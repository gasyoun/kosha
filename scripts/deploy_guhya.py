"""
Restricted-tier backup deploy: uploads the local-only census giants to
samskrtam.ru/guhya over **FTPS** (private path, not linked from any public page).

Reads credentials from .env.deploy in the repo root (gitignored) — same
FTP account as ORS-FAQ/SamudraManthanam, different FTP_PATH.

Covers all H235 primary targets: corpus_lexicon.jsonl, kosha.db, dcs_full.sqlite,
corpus.db, the Sa-Ru glossary bulk layer, and the 25 production Renou-layer
card-set files (dev/test artifact variants excluded — see MANIFEST comment).
archive_stopword.sqlite (11 GB, exceeds no per-file limit here but is huge) is
NOT included — see the GTD @DECIDE row before adding it.

W0B (H1944) — what changed, and why each part matters:

* **Encrypted, always.** The transport was `ftplib.FTP`: credentials and every
  byte of the corpus in clear text. It is now `ftplib.FTP_TLS` with an explicit
  `AUTH TLS` handshake and `PROT P` on the data channel, and there is no
  plaintext code path left to fall back to. A server that cannot negotiate TLS
  is a failed deploy, not a silent downgrade.
* **Temporary remote names + atomic rename.** The old code streamed straight
  onto the final filename, so an interrupted 1.7 GB upload left a truncated
  file sitting at the name consumers fetch — and the next run's
  `existing == size` check could not tell truncated-and-resumable from
  complete. Uploads now land on `<name>.uploading-<token>` and are `RNFR`/`RNTO`
  renamed into place only once the byte count matches.
* **Digest verification.** The sha256 was computed locally and shipped in a
  sidecar; nothing ever checked the far end. The uploader now asks the server
  for a hash (`HASH` / `XSHA256`, RFC-draft but widely supported) and compares
  it; when the server offers neither, it falls back to a size check and
  **records which of the two it got** rather than reporting an unqualified
  "verified".
* No upload happens under `--dry-run` or `--verify-only`.

Usage:
    python scripts/deploy_guhya.py                # upload the standard manifest
    python scripts/deploy_guhya.py --file PATH --remote-name NAME   # one extra file
    python scripts/deploy_guhya.py --verify-only   # only recompute/check sha256, no upload
    python scripts/deploy_guhya.py --dry-run       # plan + digests, no connection
"""

import argparse
import ftplib
import hashlib
import json
import os
import ssl
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).parent.parent
GITHUB_ROOT = REPO_ROOT.parent

BLOCK_SIZE = 8 * 1024 * 1024
UPLOAD_SUFFIX = ".uploading"

# (local path relative to GitHub/, remote filename under FTP_PATH)
MANIFEST = [
    ("SanskritLexicography/RussianTranslation/src/corpus_lexicon.jsonl", "corpus_lexicon.jsonl"),
    ("kosha/data/db/kosha.db", "kosha.db"),
    ("VisualDCS/src/DCS-data-2026/dcs_full.sqlite", "dcs_full.sqlite"),
    ("SamudraManthanam/web/corpus.db", "corpus.db"),
    ("SanskritLexicography/RussianTranslation/glossary/surface_glossary.jsonl", "renou/surface_glossary.jsonl"),
]

# Renou-layer card sets (25 production files, ~1.48 GB — dev/test artifact
# variants like *.chunk/*.perf/*.quarantine/*.smoke/*.test are excluded, they
# are regenerable pipeline fixtures, not canonical data). Verified 06-07-2026;
# see GTD dedup-ruling row before deleting any stage — sizes differ per stage
# so these are NOT byte-identical duplicates despite matching row counts.
_RENOU_DIR = "SanskritLexicography/RussianTranslation/src"
_RENOU_FILES = [
    "ap.renou.jsonl", "ap90.renou.jsonl", "ap90_renou.jsonl", "ap_renou.jsonl",
    "ap_renou.bhs.jsonl", "ap_renou.bhs.wl.jsonl",
    "assembled_cards.jsonl", "assembled_cards.renou.jsonl",
    "assembled_cards.renou.bhs.jsonl", "assembled_cards.renou.bhs.wl.jsonl",
    "ben.renou.jsonl", "ben_renou.jsonl",
    "bhs.renou.jsonl", "bhs_renou.jsonl",
    "mw.renou.jsonl", "mw_renou.jsonl", "mw_renou.bhs.jsonl", "mw_renou.bhs.wl.jsonl",
    "pw.renou.jsonl", "pw_renou.jsonl", "pwg.renou.jsonl", "pwg_ru_translated.renou.jsonl",
    "sch.renou.jsonl", "sch_renou.jsonl",
]
MANIFEST += [(f"{_RENOU_DIR}/{name}", f"renou/{name}") for name in _RENOU_FILES]


class DeployError(RuntimeError):
    """The deploy refused to proceed, or could not prove what it uploaded."""


def load_env(path: Path) -> dict:
    env = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(BLOCK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def upload_token() -> str:
    """A per-run suffix for in-flight names, so two concurrent deploys cannot
    stream into each other's temporary file."""
    return f"{os.getpid()}-{hashlib.sha256(os.urandom(16)).hexdigest()[:8]}"


class SecureTransport:
    """FTPS session with atomic, digest-verified uploads.

    `connection_factory` exists so the tests can drive the whole upload
    protocol — temp name, resume, rename, hash check — against a double,
    without a server and without ever sending a byte anywhere. There is no
    plaintext branch to test, by design.
    """

    def __init__(self, host, user, passwd, port=21, timeout=60,
                 connection_factory=ftplib.FTP_TLS, token=None):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.port = int(port)
        self.timeout = timeout
        self._factory = connection_factory
        self.token = token or upload_token()
        self.ftp = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def connect(self):
        context = ssl.create_default_context()
        try:
            self.ftp = self._factory(context=context)
        except TypeError:  # a double that takes no context
            self.ftp = self._factory()
        self.ftp.connect(self.host, self.port, timeout=self.timeout)
        # AUTH TLS before LOGIN, so credentials never cross in clear text.
        self.ftp.auth()
        self.ftp.login(self.user, self.passwd)
        # PROT P — encrypt the data channel too, not just the control channel.
        self.ftp.prot_p()
        self.ftp.set_pasv(True)
        return self.ftp

    def close(self):
        if self.ftp is not None:
            try:
                self.ftp.quit()
            except Exception:
                self.ftp.close()
            self.ftp = None

    # --- remote helpers ------------------------------------------------------

    def ensure_dir(self, remote_path: str) -> None:
        parts = [p for p in remote_path.replace("\\", "/").split("/") if p]
        self.ftp.cwd("/")
        for part in parts:
            try:
                self.ftp.mkd(part)
            except ftplib.error_perm:
                pass
            self.ftp.cwd(part)

    def size(self, remote_dir: str, name: str) -> int:
        self.ensure_dir(remote_dir)
        try:
            return self.ftp.size(name) or -1
        except ftplib.all_errors:
            return -1

    def remote_sha256(self, name: str) -> str | None:
        """Ask the server to hash the file it now holds.

        `HASH` (draft-bryan-ftpext-hash) and the older `XSHA256` are both
        widely deployed but neither is guaranteed; returning None means "this
        server cannot prove it", which the caller reports rather than hides.
        """
        for command in (f"HASH {name}", f"XSHA256 {name}"):
            try:
                response = self.ftp.sendcmd(command)
            except ftplib.all_errors:
                continue
            # `HASH` answers `213 SHA-256 0-<len> <digest> <filename>`; the
            # older `XSHA256` answers `213 <digest>`. Scan left to right for
            # the first 64-hex token rather than assuming a position — taking
            # the LAST token picks the filename out of a HASH reply, which is
            # how this silently degraded to a size-only check.
            for token in response.strip().split():
                candidate = token.split("=")[-1].strip().lower()
                if len(candidate) == 64 and all(c in "0123456789abcdef" for c in candidate):
                    return candidate
        return None

    def enable_sha256_hash(self) -> None:
        """Best effort: ask for SHA-256 if the server supports OPTS HASH."""
        try:
            self.ftp.sendcmd("OPTS HASH SHA-256")
        except ftplib.all_errors:
            pass

    # --- the upload ----------------------------------------------------------

    def upload_atomic(self, local: Path, remote_dir: str, name: str,
                      digest: str, on_progress=None) -> dict:
        """Upload `local` and only then let `name` refer to it.

        Returns a record naming how the result was verified — never a bare
        boolean, because "the server agrees on the sha256" and "the byte count
        matched" are different strengths of claim.
        """
        size = local.stat().st_size
        temp_name = f"{name}{UPLOAD_SUFFIX}-{self.token}"

        final_size = self.size(remote_dir, name)
        if final_size == size:
            remote_digest = self.remote_sha256(name)
            if remote_digest is None or remote_digest == digest:
                return {
                    "action": "skipped",
                    "bytes": size,
                    "verified_by": "remote-sha256" if remote_digest else "size",
                    "remote_sha256": remote_digest,
                }
            print(f"  {name}: remote sha256 differs — re-uploading")

        # Resume only ever applies to OUR in-flight temporary file. A partial
        # object can no longer be sitting at the final name, so resuming can
        # never silently append to something a consumer already fetched.
        existing = self.size(remote_dir, temp_name)
        rest = existing if 0 < existing < size else None
        action = "resumed" if rest else "uploaded"
        print(f"  {action.upper()} {name} ({size:,} bytes)"
              + (f" from {rest:,}" if rest else ""))

        self.ftp.cwd("/")
        self.ensure_dir(remote_dir)
        sent = [rest or 0]

        def progress(block):
            sent[0] += len(block)
            if on_progress:
                on_progress(sent[0], size)

        with open(local, "rb") as fh:
            if rest:
                fh.seek(rest)
            try:
                self.ftp.storbinary(f"STOR {temp_name}", fh, blocksize=BLOCK_SIZE,
                                    callback=progress, rest=rest)
            except ftplib.all_errors as exc:
                raise DeployError(f"{name}: transfer failed ({exc}); the "
                                  f"temporary object {temp_name} was left in "
                                  f"place for a resume, and {name} is "
                                  f"untouched") from exc

        uploaded = self.size(remote_dir, temp_name)
        if uploaded != size:
            raise DeployError(
                f"{name}: uploaded {uploaded} bytes, expected {size}; refusing "
                f"to promote a short object over the live one")

        remote_digest = self.remote_sha256(temp_name)
        if remote_digest is not None and remote_digest != digest:
            raise DeployError(
                f"{name}: server-side sha256 {remote_digest} does not match "
                f"the local {digest}; refusing to promote")

        self.ftp.cwd("/")
        self.ensure_dir(remote_dir)
        try:
            self.ftp.delete(name)
        except ftplib.all_errors:
            pass  # first upload, or the server allows rename-over
        self.ftp.rename(temp_name, name)

        return {
            "action": action,
            "bytes": size,
            "verified_by": "remote-sha256" if remote_digest else "size",
            "remote_sha256": remote_digest,
        }


def plan(manifest) -> tuple[list, dict]:
    """Resolve the manifest against the local tree and compute digests."""
    resolved, results = [], {}
    for rel, remote_name in manifest:
        local = Path(rel)
        if not local.is_absolute():
            local = GITHUB_ROOT / rel
        if not local.exists():
            print(f"  MISSING {local}", file=sys.stderr)
            continue
        print(f"sha256 {remote_name} ...")
        digest = sha256_of(local)
        sidecar = local.with_suffix(local.suffix + ".sha256")
        sidecar.write_text(f"{digest}  {local.name}\n", encoding="utf-8")
        results[remote_name] = {"sha256": digest, "bytes": local.stat().st_size,
                                "local": str(local)}
        resolved.append((local, remote_name, digest, sidecar))
        print(f"  {digest}")
    return resolved, results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="extra local file (absolute or relative to GitHub/) to upload")
    ap.add_argument("--remote-name", help="remote filename for --file")
    ap.add_argument("--verify-only", action="store_true",
                    help="only compute/write sha256 sidecars, no FTPS")
    ap.add_argument("--dry-run", action="store_true",
                    help="plan and digest everything, connect to nothing")
    args = ap.parse_args(argv)

    manifest = list(MANIFEST)
    if args.file:
        remote_name = args.remote_name or Path(args.file).name
        manifest.append((args.file, remote_name))

    resolved, results = plan(manifest)
    print(json.dumps(results, indent=2))

    if args.verify_only or args.dry_run:
        print("\nNo connection attempted "
              f"({'--verify-only' if args.verify_only else '--dry-run'}).")
        return 0

    env_file = REPO_ROOT / ".env.deploy"
    if not env_file.exists():
        print(f"Missing {env_file}\n"
              "Copy .env.deploy.example to .env.deploy and fill in your FTPS "
              "credentials.", file=sys.stderr)
        return 2
    cfg = load_env(env_file)
    host = cfg.get("FTP_HOST", "")
    user = cfg.get("FTP_USER", "")
    passwd = cfg.get("FTP_PASS", "")
    remote_dir = cfg.get("FTP_PATH", "guhya").strip("/")
    port = int(cfg.get("FTP_PORT", "21"))

    if not all([host, user, passwd]):
        print("Incomplete credentials in .env.deploy (need FTP_HOST, FTP_USER, "
              "FTP_PASS).", file=sys.stderr)
        return 2

    print(f"\nConnecting to {host}:{port} over FTPS ...")
    uploaded = {}
    try:
        with SecureTransport(host, user, passwd, port) as transport:
            transport.enable_sha256_hash()
            for local, remote_name, digest, sidecar in resolved:
                def show(sent, total, name=remote_name):
                    if sent % (256 * 1024 * 1024) < BLOCK_SIZE:
                        print(f"    ... {sent:,}/{total:,} bytes "
                              f"({100 * sent / total:.1f}%)")

                record = transport.upload_atomic(local, remote_dir, remote_name,
                                                 digest, on_progress=show)
                uploaded[remote_name] = record
                sidecar_digest = sha256_of(sidecar)
                transport.upload_atomic(sidecar, remote_dir,
                                        remote_name + ".sha256", sidecar_digest)
    except DeployError as exc:
        print(f"\ndeploy refused: {exc}", file=sys.stderr)
        return 1

    weak = [n for n, r in uploaded.items() if r["verified_by"] == "size"]
    print("\nDone.")
    if weak:
        print(f"NOTE: {len(weak)} file(s) verified by byte count only — this "
              f"server answers neither HASH nor XSHA256, so the sha256 sidecar "
              f"is an assertion about the local file, not a checked property "
              f"of the remote one: {', '.join(sorted(weak))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
