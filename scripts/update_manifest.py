"""Keep data/manifest/datasets.json in sync with what's actually on disk.

Two independent jobs, run separately so mechanical refresh can be fully
unattended while judgment-bearing additions never auto-commit:

  refresh    Re-stat every EXISTING entry's source_path (resolved against the
             sibling repos under GitHub/) and rewrite rows/size_bytes/
             "generated" in place when they drifted. Pure mechanical sync --
             safe to run with no human in the loop (cron/hook-friendly).

  scan       Look for files matching known dataset-producing script outputs
             (data/*, HeadwordLists/*, derived-data/* etc.) that are NOT yet
             referenced by any entry's source_path, and write candidates to
             data/manifest/_candidates.json for review. Never writes to
             datasets.json -- tier (public/restricted), rights, and consumers
             are judgment calls the manifest's own agent contract requires a
             same-pass human/agent decision on, not a script guess.

Usage:
    python scripts/update_manifest.py refresh          # mutates datasets.json
    python scripts/update_manifest.py scan              # writes _candidates.json
    python scripts/update_manifest.py refresh --dry-run  # report only

Rebuild the directory page after `refresh` changes anything:
    python scripts/build_directory.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO / "data" / "manifest"
DATASETS_JSON = MANIFEST_DIR / "datasets.json"
CANDIDATES_JSON = MANIFEST_DIR / "_candidates.json"
GITHUB_ROOT = REPO.parent  # C:\Users\user\Documents\GitHub

# source_repo -> local sibling checkout, so "source_path" (repo-relative) can
# be resolved to a real file without hitting the network.
REPO_URL_TO_LOCAL = {
    "https://github.com/sanskrit-lexicon/csl-orig": GITHUB_ROOT / "csl-orig",
    "https://github.com/sanskrit-lexicon/csl-apidev": GITHUB_ROOT / "csl-apidev",
    "https://github.com/gasyoun/SanskritLexicography": GITHUB_ROOT / "SanskritLexicography",
    "https://github.com/gasyoun/kosha": REPO,
    "https://github.com/gasyoun/SanskritRussian": GITHUB_ROOT / "SanskritRussian",
    "https://github.com/gasyoun/VisualDCS": GITHUB_ROOT / "VisualDCS",
    "https://github.com/gasyoun/SamudraManthanam": GITHUB_ROOT / "SamudraManthanam",
}

# Producer globs to check for un-registered outputs during `scan`. Extend this
# as new dataset-producing scripts are added elsewhere in the org.
CANDIDATE_GLOBS = [
    (GITHUB_ROOT / "SanskritLexicography" / "HeadwordLists", "*.tsv"),
    (GITHUB_ROOT / "SanskritLexicography" / "RussianTranslation" / "src", "*.jsonl"),
    (GITHUB_ROOT / "VisualDCS" / "derived-data", "**/*.csv"),
    (REPO / "data" / "frequency", "*.tsv"),
    (REPO / "data", "*.sqlite"),
]


def local_path_for(ds: dict) -> Path | None:
    base = REPO_URL_TO_LOCAL.get(ds.get("source_repo"))
    if base is None:
        return None
    raw = ds.get("source_path") or ""
    # strip inline parenthetical annotations e.g. "(GITIGNORED — ...)"
    rel = raw.split(" (")[0].strip()
    if not rel:
        return None
    p = base / rel
    return p


def count_rows(path: Path, fmt: str | None) -> int | None:
    try:
        if fmt in ("tsv", "csv"):
            with path.open("r", encoding="utf-8", errors="replace") as f:
                n = sum(1 for _ in f) - 1  # minus header
            return max(n, 0)
        if fmt == "jsonl":
            with path.open("r", encoding="utf-8", errors="replace") as f:
                return sum(1 for _ in f)
    except OSError:
        return None
    return None  # sqlite / mixed formats: size only, row count needs a schema-aware query


def dir_size(path: Path) -> int:
    """Recursive content size of a directory bundle -- path.stat().st_size on
    a directory returns the filesystem's directory-entry size (a few KB on
    NTFS), not the size of what's inside it, so a directory-shaped
    source_path (trailing "/") must sum its files instead of being stat'd
    directly."""
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def refresh(dry_run: bool) -> int:
    manifest = json.loads(DATASETS_JSON.read_text(encoding="utf-8"))
    changed = 0
    for ds in manifest["datasets"]:
        path = local_path_for(ds)
        if path is None or not path.exists():
            continue  # gitignored/unbackuped/remote-only entries are left alone
        size = dir_size(path) if path.is_dir() else path.stat().st_size
        rows = None if path.is_dir() else count_rows(path, ds.get("format"))
        diffs = []
        if ds.get("size_bytes") != size:
            diffs.append(f"size_bytes {ds.get('size_bytes')} -> {size}")
            ds["size_bytes"] = size
        if rows is not None and ds.get("rows") != rows:
            diffs.append(f"rows {ds.get('rows')} -> {rows}")
            ds["rows"] = rows
        if diffs:
            changed += 1
            print(f"[{ds['id']}] " + "; ".join(diffs))
    if changed and not dry_run:
        manifest["generated"] = manifest.get("generated")  # left to a human/agent to bump the date deliberately
        DATASETS_JSON.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Wrote {changed} updated entr{'y' if changed == 1 else 'ies'} to {DATASETS_JSON}")
    elif changed:
        print(f"[dry-run] {changed} entr{'y' if changed == 1 else 'ies'} would change")
    else:
        print("No drift -- all registered entries match disk.")
    return changed


def scan() -> int:
    """Group unregistered files by immediate parent directory rather than
    listing each file -- a "dataset" is usually a directory bundle (one
    export per text/class/period), and flat file-level output on a tree like
    VisualDCS/derived-data drowns real candidates in hundreds of same-bundle
    siblings."""
    manifest = json.loads(DATASETS_JSON.read_text(encoding="utf-8"))
    registered_paths = set()
    registered_dirs = set()
    for ds in manifest["datasets"]:
        p = local_path_for(ds)
        if p is None:
            continue
        rp = p.resolve()
        registered_paths.add(rp)
        # a directory-shaped source_path (trailing "/" in the manifest, or an
        # existing dir on disk) registers everything under it -- not just the
        # dir's own path -- so per-file globs don't re-flag its contents.
        if ds.get("source_path", "").split(" (")[0].strip().endswith("/") or rp.is_dir():
            registered_dirs.add(rp)

    def is_registered(f: Path) -> bool:
        rf = f.resolve()
        if rf in registered_paths:
            return True
        return any(d in rf.parents for d in registered_dirs)

    by_dir: dict[Path, list[Path]] = {}
    for base, pattern in CANDIDATE_GLOBS:
        if not base.exists():
            continue
        for f in base.glob(pattern):
            if not f.is_file() or is_registered(f):
                continue
            by_dir.setdefault(f.parent.resolve(), []).append(f)

    candidates = []
    for d, files in sorted(by_dir.items()):
        candidates.append({
            "dir": str(d),
            "file_count": len(files),
            "total_size_bytes": sum(f.stat().st_size for f in files),
            "sample_files": [f.name for f in files[:3]],
            "suggested_source_repo": next(
                (url for url, local in REPO_URL_TO_LOCAL.items() if local in d.parents), None
            ),
        })

    CANDIDATES_JSON.write_text(
        json.dumps({"note": "Unregistered directories found by scripts/update_manifest.py scan -- "
                             "each row is a directory bundle, not a single file (a 'dataset' is "
                             "usually one export per text/class/period). Review each: decide "
                             "whether it's really one manifest-worthy asset (bundle several files "
                             "into one row with a glob/pattern note) or genuine noise to ignore, "
                             "then add a proper row to datasets.json by hand (or via "
                             "/findings-append) and delete its entry here. Never auto-merged.",
                    "candidates": candidates}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{len(candidates)} unregistered director{'y' if len(candidates) == 1 else 'ies'} written to {CANDIDATES_JSON}")
    return len(candidates)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["refresh", "scan"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    if args.mode == "refresh":
        refresh(args.dry_run)
    else:
        scan()
    return 0


if __name__ == "__main__":
    sys.exit(main())
