"""Command-line front end for the build DAG.

Reachable two ways, deliberately: `python scripts/build_db.py ...` (what every
runbook, README and CLAUDE.md says) and the installed `kosha-build-db` console
script. Both call `main()` here, so there is one argument parser and one set of
defaults rather than a script and a package that drift.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .digest import digest_path
from .lock import BuildLock, lock_path_for
from .runner import BuildError, BuildOptions, run_build
from .stages import STAGE_NAMES, by_name, expand, plan

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = ["main", "build_parser"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="kosha-build-db",
        description="Build kosha.db from the declared stage DAG.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "With no --stage the full declared build runs, in this order:\n  "
            + " -> ".join(STAGE_NAMES)
            + "\n\nEvery stage must satisfy a postcondition; a stage that runs and\n"
              "produces nothing fails the build rather than passing quietly."
        ),
    )
    ap.add_argument(
        "--stage", action="append", choices=list(STAGE_NAMES), metavar="NAME",
        help="run only this stage (repeatable). Default: the full build.",
    )
    ap.add_argument("--dicts", default="mw,pwg,ap90",
                    help="dictionaries for the entries stage (default: mw,pwg,ap90)")
    ap.add_argument("--db", type=Path, default=None,
                    help="target database (default: KOSHA_CORE_DB)")
    ap.add_argument("--release", default=None, metavar="VERSION",
                    help="stamp this data_version; refuses 'latest' and refuses "
                         "to release a build with skipped stages")
    ap.add_argument("--with-deps", action="store_true",
                    help="expand each --stage to its prerequisites and run them too")
    ap.add_argument("--allow-missing-sources", action="store_true",
                    help="record an explicit skip instead of failing when a "
                         "source feed is absent")
    ap.add_argument("--force", action="store_true",
                    help="build even on stale or unverifiable prerequisites")
    ap.add_argument("--sources", type=Path, default=None, metavar="MANIFEST",
                    help="JSON manifest redirecting builder feed constants "
                         "(e.g. tests/fixtures/pack/sources.json)")
    ap.add_argument("--atomic", dest="in_place", action="store_false", default=None,
                    help="build into a temporary target and promote (default for "
                         "full builds)")
    ap.add_argument("--in-place", dest="in_place", action="store_true",
                    help="edit the target database directly (default for --stage runs)")
    ap.add_argument("--no-analyze", dest="analyze", action="store_false",
                    help="skip the closing ANALYZE")
    ap.add_argument("--plan", action="store_true",
                    help="print the resolved plan and exit without building")
    ap.add_argument("--verify", action="store_true",
                    help="check the target against its build lock and exit")
    return ap


def _print_plan(args) -> int:
    if args.sources is not None:
        from .runner import _apply_manifest

        _apply_manifest(args.sources)
    stages = args.stage
    ordered = plan(stages, with_deps=args.with_deps or stages is None)
    print("plan: " + " -> ".join(s.name for s in ordered))
    if stages:
        prerequisites = [n for n in expand(stages) if n not in {s.name for s in ordered}]
        if prerequisites:
            print("assumed already built: " + ", ".join(prerequisites))
    for stage in ordered:
        print(f"\n{stage.name} — {stage.summary}")
        if stage.depends_on:
            print(f"  depends on: {', '.join(stage.depends_on)}")
        for module, attr in stage.sources:
            print(f"  source: {module}.{attr}")
        for post in stage.postconditions:
            print(f"  proves: {post.label} (>= {post.minimum})")
        if stage.notes:
            print(f"  note: {stage.notes}")
    return 0


def _verify(target: Path) -> int:
    lock = BuildLock.read(lock_path_for(target))
    if lock is None:
        print(f"no build lock beside {target}", file=sys.stderr)
        return 2
    print(f"build {lock.build_id} — data_version {lock.data_version} "
          f"({'release' if lock.release else 'dev'})")
    problems = 0
    for name in lock.plan:
        record = lock.stages.get(name)
        if record is None:
            print(f"  {name}: NO RECORD")
            problems += 1
            continue
        line = f"  {name}: {record.status}"
        if record.reason:
            line += f" — {record.reason}"
        print(line)
        if record.status != "ok":
            problems += 1
    if lock.artifact and target.exists():
        current = digest_path(target)
        same = (current.digest == lock.artifact.get("digest")
                and current.algorithm == lock.artifact.get("algorithm"))
        print(f"  artifact digest: {'matches' if same else 'DOES NOT MATCH'} the lock")
        if not same:
            problems += 1
    return 1 if problems else 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.stage:
        for name in args.stage:
            by_name(name)

    if args.plan:
        return _print_plan(args)

    options = BuildOptions(
        stages=tuple(args.stage) if args.stage else None,
        dicts=tuple(d.strip() for d in args.dicts.split(",") if d.strip()),
        target=args.db,
        release=args.release,
        allow_missing_sources=args.allow_missing_sources,
        in_place=args.in_place,
        analyze=args.analyze,
        with_deps=args.with_deps,
        force=args.force,
        sources_manifest=args.sources,
    )

    if args.verify:
        return _verify(options.resolved_target())

    try:
        run_build(options)
    except BuildError as exc:
        print(f"\nbuild refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
