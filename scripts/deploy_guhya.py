"""
Restricted-tier backup deploy: mirrors the local-only census giants to
samskrtam.ru/guhya (private path, not linked from any public page).

W0B (H1944) replaced the plaintext `ftplib.FTP` path this script used to
carry. Every transfer now goes over explicit TLS, lands under a temporary
remote name, is verified against a server-computed sha256, and is only then
renamed into place — see
[`kosha.backup.transport`](https://github.com/gasyoun/kosha/blob/main/src/kosha/backup/transport.py).
If the server cannot prove a digest the upload **fails closed** and nothing is
promoted; that is the required treatment, not a bug to work around. Sources
are fail-closed too (added 01-10-2026, after the 23-08-2026 corpus.db
0-byte-stub incident): a missing or 0-byte source lands in a printed SKIP
ledger and is never uploaded, because uploading a stub would mint a false
backup artifact.

Credentials come from `.env.deploy` in the repo root (gitignored) — same FTP
account as ORS-FAQ/SamudraManthanam, different FTP_PATH. This script never
runs in CI and no test in this repo contacts a live server.

Covers all H235 primary targets: corpus_lexicon.jsonl, kosha.db,
dcs_full.sqlite, corpus.db, the Sa-Ru glossary bulk layer, and the 25
production Renou-layer card-set files (dev/test artifact variants excluded —
see MANIFEST comment). archive_stopword.sqlite (11 GB) is NOT included — the
H1989/H1998 retain/discard ruling excluded it as regenerable
(`import_archive.py stopword`; the Mac copy is covered weekly by the W4-Mac
restic lane). Do not add it back without an MG order.

Usage:
    python scripts/deploy_guhya.py                 # DRY RUN: digest + plan only
    python scripts/deploy_guhya.py --upload        # verified encrypted upload
    python scripts/deploy_guhya.py --file PATH --remote-name NAME --upload
    python scripts/deploy_guhya.py --verify-only   # write sha256 sidecars only
"""

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).parent.parent
GITHUB_ROOT = REPO_ROOT.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from kosha.backup.transport import (
    BackupError, FTPSTransport, sha256_of, upload,
)

# (local path relative to GitHub/, remote filename under FTP_PATH)
MANIFEST = [
    ("SanskritLexicography/RussianTranslation/src/corpus_lexicon.jsonl", "corpus_lexicon.jsonl"),
    ("kosha/data/db/kosha.db", "kosha.db"),
    ("VisualDCS/src/DCS-data-2026/dcs_full.sqlite", "dcs_full.sqlite"),
    ("SanskritLexicography/RussianTranslation/glossary/surface_glossary.jsonl", "renou/surface_glossary.jsonl"),
]

# Renou-layer card sets (25 production files, ~1.48 GB — dev/test artifact
# variants like *.chunk/*.perf/*.quarantine/*.smoke/*.test are excluded, they
# are regenerable pipeline fixtures, not canonical data). Verified 06-07-2026;
# see GTD dedup-ruling row before deleting any stage — sizes differ per stage
# so these are NOT byte-identical duplicates despite matching row counts.
# 03-10-2026 MG ruling (GTD 0LX, chat vote A): underscore-spelled renou variants
# dropped — no .sha256 sidecar ever marked them canonical (H3389 dot-variants
# are), sources absent on the Mac lane; corpus.db removed as a regenerable
# stub. Count note: the GTD row said 13, the disk probe found 11 underscore
# entries + corpus.db.
_RENOU_DIR = "SanskritLexicography/RussianTranslation/src"
_RENOU_FILES = [
    "ap.renou.jsonl", "ap90.renou.jsonl",
    "assembled_cards.jsonl", "assembled_cards.renou.jsonl",
    "assembled_cards.renou.bhs.jsonl", "assembled_cards.renou.bhs.wl.jsonl",
    "ben.renou.jsonl",
    "bhs.renou.jsonl",
    "mw.renou.jsonl",
    "pw.renou.jsonl", "pwg.renou.jsonl", "pwg_ru_translated.renou.jsonl",
    "sch.renou.jsonl",
]
MANIFEST += [(f"{_RENOU_DIR}/{name}", f"renou/{name}") for name in _RENOU_FILES]


def load_env(path: Path) -> dict:
    env = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def tls_verify_from_env(cfg: dict) -> bool:
    """Whether FTPS should verify the server certificate (default True).

    Shared hosting often serves a self-signed ProFTPD cert. Prefer
    ``FTP_TLS_INSECURE=1`` (encrypt without CA match) over plaintext FTP.
    """
    insecure = cfg.get("FTP_TLS_INSECURE", "").strip().lower()
    if insecure in ("1", "true", "yes", "on"):
        return False
    verify = cfg.get("FTP_SSL_VERIFY", "1").strip().lower()
    if verify in ("0", "false", "no", "off"):
        return False
    return True


def resolve(rel: str, root: Path | None = None) -> Path:
    local = Path(rel)
    base = root if root is not None else GITHUB_ROOT
    return local if local.is_absolute() else base / rel


def plan_targets(
    manifest: list[tuple[str, str]], root: Path | None = None
) -> tuple[list[tuple[str, str, Path]], list[tuple[str, str]]]:
    """Split manifest targets into (ready, skipped) — the fail-closed ledger.

    A target is SKIPPED, never uploaded, when its source is missing or is a
    0-byte stub: uploading a stub would mint a false backup artifact (the
    23-08-2026 corpus.db incident — a 0-byte local file sat where the
    registry promised 655 MB). Skips are printed, not fatal: the run stays
    green so the ledger keeps printing until MG rules the ghosts away
    (H3389 residual 3), mirroring H3389's exclusion-with-reasons pattern.
    """
    ready: list[tuple[str, str, Path]] = []
    skipped: list[tuple[str, str]] = []
    for rel, remote_name in manifest:
        local = resolve(rel, root)
        if not local.exists():
            skipped.append((remote_name, f"missing on disk: {local}"))
        elif local.stat().st_size == 0:
            skipped.append(
                (remote_name, f"0-byte stub — refusing to mint a false backup: {local}")
            )
        else:
            ready.append((rel, remote_name, local))
    return ready, skipped


def split_remote(remote_name: str, base_dir: str) -> tuple[str, str]:
    """Manifest names may carry a subdirectory (`renou/x.jsonl`)."""
    if "/" in remote_name:
        head, _, tail = remote_name.rpartition("/")
        return f"{base_dir}/{head}", tail
    return base_dir, remote_name


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", help="extra local file (absolute or relative to GitHub/) to upload")
    ap.add_argument("--remote-name", help="remote filename for --file")
    ap.add_argument("--verify-only", action="store_true",
                    help="only compute/write sha256 sidecars, no transport at all")
    ap.add_argument("--upload", action="store_true",
                    help="actually transfer (default is a dry run that uploads nothing)")
    args = ap.parse_args()

    manifest = list(MANIFEST)
    if args.file:
        manifest.append((args.file, args.remote_name or Path(args.file).name))

    ready, skipped = plan_targets(manifest)

    results = {}
    for rel, remote_name, local in ready:
        print(f"sha256 {remote_name} ...")
        digest = sha256_of(local)
        sidecar = local.with_suffix(local.suffix + ".sha256")
        sidecar.write_text(f"{digest}  {local.name}\n", encoding="utf-8")
        results[remote_name] = {
            "sha256": digest, "bytes": local.stat().st_size, "local": str(local),
        }
        print(f"  {digest}")

    if skipped:
        print(
            "\nSKIP ledger (fail-closed — nothing was uploaded for these):",
            file=sys.stderr,
        )
        for remote_name, reason in skipped:
            print(f"  SKIP  {remote_name}: {reason}", file=sys.stderr)

    print(json.dumps(results, indent=2))

    if args.verify_only:
        return
    if not args.upload:
        skip_note = f" (skip ledger: {len(skipped)})" if skipped else ""
        print(
            "\nDRY RUN — nothing was transferred. Re-run with --upload to send "
            f"{len(results)} file(s) over TLS with remote digest verification{skip_note}."
        )
        return

    env_file = REPO_ROOT / ".env.deploy"
    if not env_file.exists():
        sys.exit(
            f"Missing {env_file}\n"
            "Copy .env.deploy.example to .env.deploy and fill in your FTP credentials."
        )
    cfg = load_env(env_file)
    host, user, passwd = cfg.get("FTP_HOST", ""), cfg.get("FTP_USER", ""), cfg.get("FTP_PASS", "")
    remote_dir = cfg.get("FTP_PATH", "guhya").strip("/")
    port = int(cfg.get("FTP_PORT", "21"))
    verify_tls = tls_verify_from_env(cfg)
    if not all([host, user, passwd]):
        sys.exit("Incomplete credentials in .env.deploy (need FTP_HOST, FTP_USER, FTP_PASS).")

    tls_note = "TLS (CA verify)" if verify_tls else "TLS (insecure verify — self-signed host)"
    print(f"\nConnecting to {host}:{port} over explicit {tls_note} ...")
    failures = []
    with FTPSTransport(
        host, user, passwd, port=port, verify_tls=verify_tls
    ) as transport:
        for rel, remote_name, local in ready:
            target_dir, name = split_remote(remote_name, remote_dir)
            try:
                outcome = upload(transport, local, target_dir, name)
                print(f"  OK    {remote_name} ({outcome.bytes:,} bytes, digest verified)")
            except BackupError as error:
                print(f"  FAIL  {error}", file=sys.stderr)
                failures.append(remote_name)
                continue
            sidecar_local = local.with_suffix(local.suffix + ".sha256")
            try:
                upload(transport, sidecar_local, target_dir, name + ".sha256")
            except BackupError as error:
                print(f"  FAIL  sidecar {error}", file=sys.stderr)
                failures.append(remote_name + ".sha256")

    if failures:
        sys.exit(f"\n{len(failures)} file(s) were NOT promoted: {', '.join(failures)}")
    print("\nDone.")


if __name__ == "__main__":
    main()
