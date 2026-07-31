"""Run the declarative build DAG: plan, guard, execute, prove, promote.

Design decisions worth keeping, because each one closes a way the old
`scripts/build_db.py` could report success it had not earned:

* **A full build starts from an empty database in a temporary target** and is
  `os.replace`-promoted only after every stage passed its postcondition. A
  half-built database therefore never occupies the path the API reads, and a
  crashed build leaves the previous good artifact untouched.
* **A missing source feed aborts the build.** It used to be indistinguishable
  from "this stage was not requested". `--allow-missing-sources` downgrades it
  to a *recorded* skip, which a release build then refuses.
* **Sources are re-digested after each stage.** A feed rewritten mid-build
  means earlier and later stages read different bytes; that is a hard error,
  not a warning.
* **Single-stage runs check their prerequisites** against the previous lock and
  refuse to build on top of a stage that never ran or whose inputs have moved.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from kosha import __version__ as KOSHA_VERSION
from kosha.settings import get_settings

from .digest import digest_path
from .lock import (
    STATUS_FAILED,
    STATUS_OK,
    STATUS_SKIPPED,
    BuildLock,
    StageRecord,
    lock_path_for,
    utc_now,
)
from .stages import (
    STAGE_NAMES as STAGE_ORDER,
    Stage,
    apply_source_overrides,
    by_name,
    expand,
    plan,
    resolve_callable,
    resolve_sources,
)

if hasattr(sys.stdout, "reconfigure"):  # Windows console defaults to cp1251
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = ["BuildOptions", "BuildError", "run_build", "DEV_DATA_VERSION"]

DEV_DATA_VERSION = "0.1.0-dev"
_REJECTED_RELEASE_VERSIONS = {"latest", "LATEST", "Latest"}


class BuildError(RuntimeError):
    """The build refused to proceed, or a stage failed its postcondition."""


@dataclass
class BuildOptions:
    stages: tuple[str, ...] | None = None      # None = the full declared build
    dicts: tuple[str, ...] = ("mw", "pwg", "ap90")
    target: Path | None = None                 # defaults to settings.core_db
    release: str | None = None                 # version to stamp; None = dev build
    allow_missing_sources: bool = False
    in_place: bool | None = None               # None = atomic for full builds
    analyze: bool = True
    with_deps: bool = False                    # expand a --stage run to its deps
    force: bool = False                        # accept stale/unverifiable prereqs
    sources_manifest: Path | None = None       # fixture pack / alternate feed set

    def resolved_target(self) -> Path:
        return Path(self.target) if self.target else get_settings().core_db

    def is_full_build(self) -> bool:
        return self.stages is None

    def use_temp_target(self) -> bool:
        if self.in_place is not None:
            return not self.in_place
        # Full builds are atomic; a `--stage x` run edits the live database in
        # place, because copying a multi-gigabyte artifact per stage would make
        # the incremental path unusable. `--atomic` forces the copy.
        return self.is_full_build()


def _log(message: str) -> None:
    print(message, flush=True)


def _apply_manifest(manifest_path: Path) -> str:
    """Rebind builder feed constants from a sources manifest (the fixture pack).

    Relative paths resolve against the manifest's own directory, so a pack is
    relocatable and a committed one works from any checkout.
    """
    manifest_path = Path(manifest_path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    overrides = {
        key: (base / value).resolve() if not Path(value).is_absolute() else Path(value)
        for key, value in data.get("overrides", {}).items()
    }
    applied = apply_source_overrides(overrides)
    name = data.get("name", manifest_path.stem)
    _log(f"source set: {name} ({len(applied)} feed(s) redirected from {manifest_path})")
    return name


def _build_id() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _connect(path: Path) -> sqlite3.Connection:
    """Open (creating) a kosha database with the canonical schema applied."""
    from .stages import _import_builder  # local: needs scripts/ on sys.path

    build_db = _import_builder("build_db")
    return build_db.connect(path)


def _check_postconditions(con: sqlite3.Connection, stage: Stage) -> list[dict]:
    results = []
    for post in stage.postconditions:
        count = con.execute(post.sql).fetchone()[0]
        results.append({
            "label": post.label,
            "sql": post.sql,
            "count": count,
            "minimum": post.minimum,
            "ok": count >= post.minimum,
        })
    return results


def _missing_sources(stage: Stage) -> list[Path]:
    return [p for p in resolve_sources(stage) if not p.exists()]


def _run_stage(con, stage: Stage, options: BuildOptions, lock: BuildLock) -> StageRecord:
    sources = resolve_sources(stage)
    before = [digest_path(p) for p in sources]
    missing = [d.path for d in before if not d.exists]

    if missing:
        detail = ", ".join(missing)
        if not options.allow_missing_sources:
            raise BuildError(
                f"stage {stage.name!r} cannot run: missing source feed(s): {detail}. "
                f"{stage.notes or ''}\n"
                f"Re-run with --allow-missing-sources to record an explicit skip "
                f"instead (a release build refuses skipped stages)."
            )
        _log(f"[{stage.name}] SKIPPED — missing source(s): {detail}")
        return StageRecord(
            name=stage.name, status=STATUS_SKIPPED,
            started_at=utc_now(), finished_at=utc_now(), duration_s=0.0,
            reason=f"missing source(s): {detail}", sources=before,
        )

    context = {"con": con, "dicts": list(options.dicts)}
    func = resolve_callable(stage)
    args = [context[key] for key in stage.call_args]

    started = utc_now()
    clock = time.perf_counter()
    _log(f"[{stage.name}] {stage.summary}")
    try:
        func(*args)
    except Exception as exc:  # recorded, then re-raised — never swallowed
        lock.record(StageRecord(
            name=stage.name, status=STATUS_FAILED, started_at=started,
            finished_at=utc_now(), duration_s=time.perf_counter() - clock,
            reason=f"{type(exc).__name__}: {exc}", sources=before,
        ))
        raise
    duration = time.perf_counter() - clock

    # Immutable source lock: the bytes this stage read must be the bytes the
    # rest of the build reads. A feed replaced under a running build would
    # otherwise produce an artifact no single source state can explain.
    after = [digest_path(p) for p in sources]
    for old, new in zip(before, after):
        if not old.matches(new):
            raise BuildError(
                f"source changed while stage {stage.name!r} was running: {old.path}. "
                f"The build is not reproducible from any single source state; "
                f"re-run it against a quiescent source tree."
            )

    postconditions = _check_postconditions(con, stage)
    failed = [p for p in postconditions if not p["ok"]]
    if failed:
        reason = "; ".join(
            f"{p['label']}: got {p['count']}, need >= {p['minimum']}" for p in failed
        )
        lock.record(StageRecord(
            name=stage.name, status=STATUS_FAILED, started_at=started,
            finished_at=utc_now(), duration_s=duration, reason=reason,
            sources=before, postconditions=postconditions,
        ))
        raise BuildError(
            f"stage {stage.name!r} ran but left nothing behind — {reason}. "
            f"A stage that completes without producing rows is the failure mode "
            f"issue #210 was opened for; it is not a success."
        )

    for post in postconditions:
        _log(f"[{stage.name}]   {post['label']}: {post['count']}")
    return StageRecord(
        name=stage.name, status=STATUS_OK, started_at=started,
        finished_at=utc_now(), duration_s=duration,
        sources=before, postconditions=postconditions,
    )


def _guard_prerequisites(options: BuildOptions, target: Path, wanted: list[str]) -> None:
    """A partial build must not silently sit on stale earlier stages.

    This is the half of issue #210 that survives the DAG fix: with the full
    build repaired, the remaining way to get a wrong database is to rebuild one
    stage on top of prerequisites that were themselves built from feeds that
    have since changed — and to be told nothing about it.
    """
    if options.is_full_build() or options.force:
        return
    requested = set(wanted)
    prerequisites = [name for name in expand(wanted) if name not in requested]
    if not prerequisites:
        return

    previous = BuildLock.read(lock_path_for(target))
    if previous is None:
        raise BuildError(
            f"no build lock beside {target}: cannot prove the prerequisites "
            f"({', '.join(prerequisites)}) of {', '.join(sorted(requested))} were "
            f"ever built. Run a full build first, or pass --force to accept an "
            f"unverifiable base."
        )
    configured = {
        name: [str(p) for p in resolve_sources(by_name(name))]
        for name in prerequisites
    }
    problems = previous.stale_prerequisites(prerequisites, configured)
    if problems:
        detail = "; ".join(f"{dep}: {why}" for dep, why in problems)
        raise BuildError(
            f"refusing to build {', '.join(sorted(requested))} on stale "
            f"prerequisites — {detail}. Rebuild those stages (or the whole "
            f"database) first, or pass --force to accept the staleness."
        )


def run_build(options: BuildOptions) -> BuildLock:
    settings = get_settings()
    target = options.resolved_target()

    if options.release is not None:
        if options.release in _REJECTED_RELEASE_VERSIONS:
            raise BuildError(
                "--release 'latest' is refused: a citation minted against "
                "'latest' resolves to different text every rebuild, which is "
                "exactly what the durable sense-id contract (RISKS.md R1) "
                "forbids. Name the concrete version."
            )
        if not options.release.strip():
            raise BuildError("--release needs a version string")

    source_set = "default"
    if options.sources_manifest is not None:
        source_set = _apply_manifest(options.sources_manifest)

    ordered = plan(options.stages, with_deps=options.with_deps or options.is_full_build())
    wanted = [s.name for s in ordered]
    _guard_prerequisites(options, target, wanted)

    build_id = _build_id()
    lock = BuildLock(
        build_id=build_id,
        target=str(target),
        plan=wanted,
        release=options.release is not None,
        data_version=options.release or DEV_DATA_VERSION,
        kosha_version=KOSHA_VERSION,
        source_set=source_set,
    )

    # A partial run must not erase what the previous build recorded about the
    # stages it is not touching — the lock is the artifact's whole provenance,
    # not a log of the last command. Carried-over records keep their original
    # timestamps and source digests, so staleness stays detectable.
    if not options.is_full_build():
        previous = BuildLock.read(lock_path_for(target))
        if previous is not None:
            for name, record in previous.stages.items():
                if name not in wanted:
                    lock.record(record)
            lock.plan = [n for n in previous.plan if n not in wanted] + wanted
            lock.plan.sort(key=lambda n: list(STAGE_ORDER).index(n)
                           if n in STAGE_ORDER else len(STAGE_ORDER))

    if options.use_temp_target():
        work = target.with_name(f"{target.name}.building-{build_id}")
        if work.exists():
            work.unlink()
        work.parent.mkdir(parents=True, exist_ok=True)
        if not options.is_full_build() and target.exists():
            # A partial atomic run edits a copy of the live artifact.
            shutil.copy2(target, work)
        _log(f"building into {work} (atomic promotion to {target})")
    else:
        work = target
        _log(f"building in place: {target}")

    _log(f"plan: {' -> '.join(wanted)}")

    con = _connect(work)
    try:
        for stage in ordered:
            lock.record(_run_stage(con, stage, options, lock))

        skipped = [n for n, r in lock.stages.items() if r.status == STATUS_SKIPPED]
        if options.release is not None and skipped:
            raise BuildError(
                f"release build refuses skipped stage(s): {', '.join(sorted(skipped))}. "
                f"A release artifact must be able to say every declared stage ran."
            )

        con.execute(
            "INSERT INTO meta (key, value) VALUES ('data_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (lock.data_version,),
        )
        con.execute(
            "INSERT INTO meta (key, value) VALUES ('build_id', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (build_id,),
        )
        con.commit()
        if options.analyze:
            # Refresh planner statistics (~5 s) so index selectivity is known.
            con.execute("ANALYZE")
            con.commit()
    except BaseException:
        con.close()
        if work != target and work.exists():
            work.unlink(missing_ok=True)
            _log(f"discarded incomplete build target {work}")
        lock.finished_at = utc_now()
        raise
    con.close()

    missing = lock.missing_from_plan()
    if missing:
        raise BuildError(
            f"planned stage(s) left no record: {', '.join(missing)} — refusing to "
            f"promote a build whose own log cannot account for it."
        )

    lock.finished_at = utc_now()
    artifact = digest_path(work)
    lock.artifact = artifact.to_json() | {"path": str(target)}

    if work != target:
        os.replace(work, target)
        _log(f"promoted {work.name} -> {target}")
    lock.write(lock_path_for(target))
    _log(f"build lock: {lock_path_for(target)}")

    incomplete = lock.incomplete()
    if incomplete:
        _log(f"NOTE: {len(incomplete)} stage(s) did not complete: {', '.join(incomplete)}")
    _log(f"data_version = {lock.data_version}")
    if settings.core_db != target:
        _log(f"NOTE: built {target}, but KOSHA_CORE_DB points at {settings.core_db}")
    return lock
