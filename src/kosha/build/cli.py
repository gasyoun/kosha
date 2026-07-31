"""kosha build CLI — `python scripts/build_db.py` and `kosha-build` (H1944).

Flags kept from the pre-W0B script so existing muscle memory and docs still
work: `--stage`, `--dicts`. Everything else is new surface the DAG needs.

    python scripts/build_db.py                     # full declared DAG
    python scripts/build_db.py --plan              # print the order, build nothing
    python scripts/build_db.py --stage forms       # forms + everything it reads
    python scripts/build_db.py --profile fixture   # compact public fixture build
    python scripts/build_db.py --release --release-tag 2026-05-01-00-00-00
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..settings import get_settings
from . import dag
from .stages import DECLARED_ORDER, STAGES

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kosha-build", description="Build the kosha SQLite store."
    )
    parser.add_argument(
        "--stage",
        action="append",
        choices=list(DECLARED_ORDER),
        help="build this stage and its prerequisites (repeatable); "
             "omitted means every declared stage",
    )
    parser.add_argument("--dicts", default="mw,pwg,ap90")
    parser.add_argument(
        "--target", type=Path, default=None,
        help="output database (default: the configured core DB)",
    )
    parser.add_argument(
        "--profile", default="full", choices=("full", "fixture"),
        help="'fixture' points every source at the committed public pack",
    )
    parser.add_argument(
        "--release", action="store_true",
        help="release build: refuses the mutable 'latest' csl-sqlite alias",
    )
    parser.add_argument("--release-tag", default="latest")
    parser.add_argument(
        "--relock", action="store_true",
        help="accept source digests that differ from the recorded lock",
    )
    parser.add_argument(
        "--plan", action="store_true",
        help="print the expanded stage order and resolved sources, build nothing",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable --plan")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    env = None
    release_tag = args.release_tag
    if args.profile == "fixture":
        from . import fixtures

        env = fixtures.fixture_env(fixtures.materialize())
        if release_tag == "latest":
            # The pack digest is the fixture profile's immutable tag, so even a
            # fixture build never records the mutable `latest` alias.
            release_tag = fixtures.release_tag()

    settings = get_settings(refresh=True)
    target = args.target or (
        settings.core_db if args.profile == "full"
        else settings.core_db.parent / "kosha_fixture.db"
    )

    try:
        plan = dag.plan_build(
            target,
            args.stage,
            release=args.release,
            release_tag=release_tag,
            dicts=tuple(args.dicts.split(",")),
            profile=args.profile,
            env=env,
        )
    except dag.BuildError as error:
        print(f"[dag] ERROR {error}", file=sys.stderr)
        return 2

    if args.plan:
        document = {
            "target": str(plan.target),
            "profile": plan.profile,
            "release_tag": plan.release_tag,
            "stages": plan.stages,
            "skipped": plan.skipped,
            "sources": {
                name: {"path": str(source.path), "exists": source.exists}
                for name, source in sorted(plan.resolved.items())
            },
        }
        if args.json:
            print(json.dumps(document, indent=2, ensure_ascii=False))
        else:
            print(f"target : {plan.target}")
            print(f"profile: {plan.profile}  release_tag: {plan.release_tag}")
            print("stages : " + " -> ".join(plan.stages))
            for name, reason in plan.skipped.items():
                print(f"  SKIP {name}: {reason}")
            for name, source in sorted(plan.resolved.items()):
                mark = "ok " if source.exists else "MISS"
                print(f"  [{mark}] {name}: {source.path}")
        return 0

    try:
        dag.execute(plan, relock=args.relock)
    except dag.BuildError as error:
        print(f"[dag] ERROR {error}", file=sys.stderr)
        return 1
    return 0


def describe() -> str:
    """Human-readable dump of the declared graph, used by the docs test."""
    lines = []
    for name in DECLARED_ORDER:
        stage = STAGES[name]
        requires = ", ".join(stage.requires) or "—"
        lines.append(f"{name}: requires {requires}; {stage.summary}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
