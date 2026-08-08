"""kosha — W2A release gate for immutable citation archives (H2346).

Verifies the mount that a citable release ships with:

  * durable public base (absolute https, not the deployment host)
  * ≥1 archived version (configurable via --min-versions)
  * each version has senses.sqlite + release.json with matching sha256
  * at least one sense resolves from every mounted version

Runtime readiness still treats an empty mount as unconfigured; this script
is the *release* gate and fails closed.

Usage::

    python scripts/validate_release_archives.py
    python scripts/validate_release_archives.py --archive-dir tests/fixtures/archives \\
        --public-base https://gasyoun.github.io/kosha --min-versions 2 \\
        --sense-id mw.101.1

Exit 0 on pass, 1 on any failed check.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from kosha.api.archive import validate_release_archives  # noqa: E402
from kosha.settings import Settings  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--archive-dir",
        type=Path,
        default=None,
        help="Archive mount (default: KOSHA_ARCHIVE_DIR / data/releases)",
    )
    ap.add_argument(
        "--public-base",
        default=None,
        help="Citation public base (default: KOSHA_PUBLIC_BASE / settings default)",
    )
    ap.add_argument(
        "--min-versions",
        type=int,
        default=1,
        help="Minimum archived versions required (default 1; use 2 for multi-id smoke)",
    )
    ap.add_argument(
        "--sense-id",
        default=None,
        help="Sense id to resolve across all versions (auto-picked if omitted)",
    )
    args = ap.parse_args(argv)

    base = Settings.from_env()
    settings = Settings(
        core_db=base.core_db,
        inflections_db=base.inflections_db,
        layers_db=base.layers_db,
        history_db=base.history_db,
        archive_dir=args.archive_dir or base.archive_dir,
        public_base=args.public_base or base.public_base,
        enable_history=base.enable_history,
        expected_data_version=base.expected_data_version,
    )

    report = validate_release_archives(
        settings,
        sense_id=args.sense_id,
        min_versions=args.min_versions,
    )
    for check in report.checks:
        mark = "OK  " if check.ok else "FAIL"
        print(f"[{mark}] {check.name}: {check.detail}")
    if report.ok:
        print(
            f"release archive gate PASS — {len(report.versions)} version(s) "
            f"under {report.archive_dir}"
        )
        return 0
    print(
        f"release archive gate FAIL — {len(report.failures())} check(s) failed",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
