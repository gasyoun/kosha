#!/usr/bin/env python3
"""Assemble a versioned local deployment bundle (W1D / H2344).

Dry packaging only — digests + payload copy. Never uploads, never reads
``.env.deploy``, never touches production hosts.

Usage:
    python scripts/assemble_deploy_bundle.py --profile fixture
    python scripts/assemble_deploy_bundle.py --profile fixture --out /tmp/kosha-bundle
    python scripts/assemble_deploy_bundle.py --validate-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from kosha.deploy.bundle import (  # noqa: E402
    assemble_bundle,
    default_recipe_path,
    load_recipe,
    validate_recipe,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--profile",
        choices=("fixture", "staged"),
        default="fixture",
        help="fixture rewrites core DB path to kosha_fixture.db (default)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output directory (default: data/deploy_bundles/<id>-<stamp>)",
    )
    ap.add_argument(
        "--recipe",
        type=Path,
        default=None,
        help="path to deploy_bundle.json (default: data/manifest/deploy_bundle.json)",
    )
    ap.add_argument(
        "--validate-only",
        action="store_true",
        help="validate recipe structure only; do not copy files",
    )
    args = ap.parse_args()

    recipe_path = args.recipe or default_recipe_path(REPO_ROOT)
    data = load_recipe(recipe_path)
    report = validate_recipe(data, recipe_path=recipe_path)
    if not report.ok:
        for err in report.errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 2

    print(f"recipe ok: {recipe_path} ({report.component_count} components)")
    if args.validate_only:
        return 0

    report = assemble_bundle(
        repo_root=REPO_ROOT,
        recipe_path=recipe_path,
        out_dir=args.out,
        profile=args.profile,
    )
    for w in report.warnings:
        print(f"WARN: {w}", file=sys.stderr)
    if not report.ok:
        for err in report.errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print(f"assembled: {report.out_dir}")
    print(f"files_hashed: {report.files_hashed}")
    print(f"identity: {report.out_dir / 'BUNDLE_IDENTITY.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
