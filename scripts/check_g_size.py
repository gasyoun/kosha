"""G-SIZE tripwire (D5-4 / H1367) — fail CI before an upload does.

R11 corrected: kosha.db grew to 84% of the 2 GB release-asset ceiling.
Gate any single uncompressed asset that would be shipped:

  WARN  size >= 1.5 GB  (print warning, exit 0)
  FAIL  size >  1.8 GB  (exit 1)

Default target is data/db/kosha.db (gitignored). Pass extra paths to check
release assets. Soft-skips when the file is absent (fresh clone / worktree).

Usage:
    python scripts/check_g_size.py
    python scripts/check_g_size.py data/db/kosha.db path/to/asset.db
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "db" / "kosha.db"

# Binary GiB for the real GitHub per-asset limit context; thresholds follow
# D5-4 which quotes decimal-ish 1.5 / 1.8 GB against the 2 GB ceiling.
WARN_BYTES = int(1.5 * 1000**3)  # 1.5 GB decimal
FAIL_BYTES = int(1.8 * 1000**3)  # 1.8 GB decimal


def check_path(path: Path) -> str:
    """Return 'ok' | 'warn' | 'fail' | 'missing'."""
    if not path.exists():
        print(f"[G-SIZE] SKIP missing: {path}")
        return "missing"
    size = path.stat().st_size
    mb = size / 1e6
    gb = size / 1e9
    label = f"{path} = {size:,} B ({mb:.1f} MB / {gb:.3f} GB)"
    if size > FAIL_BYTES:
        print(f"[G-SIZE] FAIL >1.8 GB: {label}")
        return "fail"
    if size >= WARN_BYTES:
        print(f"[G-SIZE] WARN >=1.5 GB: {label}")
        return "warn"
    print(f"[G-SIZE] OK: {label}")
    return "ok"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[DEFAULT_DB],
        help="files to size-check (default: data/db/kosha.db)",
    )
    args = ap.parse_args(argv)
    statuses = [check_path(p) for p in args.paths]
    if "fail" in statuses:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
