"""
Restricted-tier backup deploy: uploads the local-only census giants to
samskrtam.ru/guhya via FTP (private path, not linked from any public page).

Reads credentials from .env.deploy in the repo root (gitignored) — same
FTP account as ORS-FAQ/SamudraManthanam, different FTP_PATH.

Covers all H235 primary targets: corpus_lexicon.jsonl, kosha.db, dcs_full.sqlite,
corpus.db, the Sa-Ru glossary bulk layer, and the 25 production Renou-layer
card-set files (dev/test artifact variants excluded — see MANIFEST comment).
archive_stopword.sqlite (11 GB, exceeds no per-file limit here but is huge) is
NOT included — see the GTD @DECIDE row before adding it.

Usage:
    python scripts/deploy_guhya.py                # upload the standard manifest
    python scripts/deploy_guhya.py --file PATH --remote-name NAME   # one extra file
    python scripts/deploy_guhya.py --verify-only   # only recompute/check sha256, no upload
"""

import argparse
import ftplib
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).parent.parent
GITHUB_ROOT = REPO_ROOT.parent

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
        for chunk in iter(lambda: f.read(1024 * 1024 * 8), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_remote_dir(ftp: ftplib.FTP, remote_path: str) -> None:
    parts = [p for p in remote_path.replace("\\", "/").split("/") if p]
    ftp.cwd("/")
    for part in parts:
        try:
            ftp.mkd(part)
        except ftplib.error_perm:
            pass
        ftp.cwd(part)


def remote_size(ftp: ftplib.FTP, remote_dir: str, name: str) -> int:
    ftp.cwd("/")
    ensure_remote_dir(ftp, remote_dir)
    try:
        return ftp.size(name)
    except ftplib.all_errors:
        return -1


def upload_file(ftp: ftplib.FTP, local: Path, remote_dir: str, name: str) -> None:
    size = local.stat().st_size
    existing = remote_size(ftp, remote_dir, name)
    if existing == size:
        print(f"  SKIP  {name} (already {size} bytes on server)")
        return

    rest = existing if 0 < existing < size else None
    mode = "ab" if rest else "wb"
    print(f"  {'RESUME' if rest else 'UPLOAD'} {name} ({size:,} bytes){' from ' + str(rest) if rest else ''}")

    ftp.cwd("/")
    ensure_remote_dir(ftp, remote_dir)
    with open(local, "rb") as f:
        if rest:
            f.seek(rest)
        sent = [rest or 0]

        def progress(_block):
            sent[0] += len(_block)
            if sent[0] % (256 * 1024 * 1024) < 8 * 1024 * 1024:
                print(f"    ... {sent[0]:,}/{size:,} bytes ({100 * sent[0] / size:.1f}%)")

        try:
            ftp.storbinary(f"STOR {name}", f, blocksize=8 * 1024 * 1024, callback=progress, rest=rest)
        except ftplib.all_errors as e:
            print(f"  ERROR {name}: {e}", file=sys.stderr)
            raise


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="extra local file (absolute or relative to GitHub/) to upload")
    ap.add_argument("--remote-name", help="remote filename for --file")
    ap.add_argument("--verify-only", action="store_true", help="only compute/write sha256 sidecars, no FTP")
    args = ap.parse_args()

    manifest = list(MANIFEST)
    if args.file:
        remote_name = args.remote_name or Path(args.file).name
        manifest.append((args.file, remote_name))

    results = {}
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
        results[remote_name] = {"sha256": digest, "bytes": local.stat().st_size, "local": str(local)}
        print(f"  {digest}")

    print(json.dumps(results, indent=2))

    if args.verify_only:
        return

    env_file = REPO_ROOT / ".env.deploy"
    if not env_file.exists():
        sys.exit(
            f"Missing {env_file}\n"
            "Copy .env.deploy.example to .env.deploy and fill in your FTP credentials."
        )
    cfg = load_env(env_file)
    host = cfg.get("FTP_HOST", "")
    user = cfg.get("FTP_USER", "")
    passwd = cfg.get("FTP_PASS", "")
    remote_dir = cfg.get("FTP_PATH", "guhya").strip("/")
    port = int(cfg.get("FTP_PORT", "21"))

    if not all([host, user, passwd]):
        sys.exit("Incomplete credentials in .env.deploy (need FTP_HOST, FTP_USER, FTP_PASS).")

    print(f"\nConnecting to {host}:{port} ...")
    with ftplib.FTP() as ftp:
        ftp.connect(host, port, timeout=60)
        ftp.login(user, passwd)
        ftp.set_pasv(True)
        for rel, remote_name in manifest:
            local = Path(rel)
            if not local.is_absolute():
                local = GITHUB_ROOT / rel
            if not local.exists():
                continue
            upload_file(ftp, local, remote_dir, remote_name)
            sidecar_name = remote_name + ".sha256"
            sidecar_local = local.with_suffix(local.suffix + ".sha256")
            upload_file(ftp, sidecar_local, remote_dir, sidecar_name)

    print("\nDone.")


if __name__ == "__main__":
    main()
