#!/usr/bin/env python3
"""CLI gate for the generated-surface registry (W1B / H2342).

Usage:
    python scripts/validate_surfaces.py
    python scripts/validate_surfaces.py --path data/manifest/surfaces.json
    python scripts/validate_surfaces.py --list

Exit 0 when every surface row is valid; non-zero otherwise. Wired into the
required Python CI job so auto-merge cannot bypass a broken registry.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Installable package is the source of truth; keep the script runnable from a
# bare checkout before `pip install -e .` by adding src/ when needed.
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kosha.surfaces import (  # noqa: E402
    default_registry_path,
    load_registry,
    validate_registry,
)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--path",
        type=Path,
        default=None,
        help="registry JSON path (default: data/manifest/surfaces.json)",
    )
    ap.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="repository root for builder path ownership checks",
    )
    ap.add_argument(
        "--list",
        action="store_true",
        help="print surface ids and exit 0 without validating beyond load",
    )
    args = ap.parse_args(argv)

    path = args.path if args.path is not None else default_registry_path(args.repo_root)

    if args.list:
        data = load_registry(path)
        for surface in data.get("surfaces", []):
            print(f"{surface.get('id')}\t{surface.get('output_class')}\t{surface.get('builder')}")
        print(f"# {len(data.get('surfaces', []))} surfaces", file=sys.stderr)
        return 0

    report = validate_registry(path=path, repo_root=args.repo_root)
    if report.ok:
        print(f"OK: {report.surface_count} surfaces validated ({path})")
        return 0

    print(f"FAIL: {len(report.errors)} error(s) in {path}", file=sys.stderr)
    for err in report.errors:
        print(f"  - {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
