"""kosha build DAG — expansion, source locking, atomic promotion (H1944).

The contract this module implements, in order:

1. **Expansion.** A requested stage set expands to its full prerequisite
   closure, topologically sorted. Asking for everything reproduces
   `stages.DECLARED_ORDER`; asking for one stage still runs what it reads.
2. **Prerequisites before writes.** Every declared source is resolved and
   digested *before* the first stage runs, so a missing feed fails a build that
   has written nothing rather than one that is half full.
3. **Temporary target + atomic promotion.** Stages write to a scratch file
   next to the destination. The destination is replaced with `os.replace`
   only after every postcondition passes, so a failed build never leaves a
   partially populated database where the API can read it.
4. **Immutable source lock.** The digests, the executed stage order, the row
   counts, and the resolved csl-sqlite release tag are written to a sidecar
   `<target>.lock.json` and mirrored into the database's `meta` table. A later
   build verifies against the recorded digests unless explicitly re-locked.
5. **`latest` is not a source.** A release build refuses the mutable
   `latest` csl-sqlite alias — an immutable tag is required, which is what
   makes the lock meaningful.

`PRAGMA foreign_key_check` runs on the finished temp target before promotion:
the release gate demands it, and running it here means a corrupt build cannot
reach the destination in the first place.
"""

from __future__ import annotations

import importlib
import json
import os
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import sources as sources_mod
from .stages import DECLARED_ORDER, STAGES, Stage, StageContext

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"

LOCK_SCHEMA_VERSION = 1
META_STAGE_KEY = "build_stage_manifest"
META_LOCK_KEY = "build_source_lock"


class BuildError(RuntimeError):
    """A build-stopping condition: missing prerequisite, failed postcondition,
    source-lock mismatch, or a mutable release alias in a release build."""


# --- expansion ------------------------------------------------------------


def expand(requested: list[str] | tuple[str, ...] | None = None) -> list[str]:
    """Expand a requested stage set to its topologically sorted closure.

    `None` (the no-flag build) means *every declared stage* — the property
    #210 was missing. Ties are broken by `DECLARED_ORDER` so the output is
    stable and reviewable rather than dependent on dict iteration.
    """
    if requested is None:
        requested = list(STAGES)
    unknown = [name for name in requested if name not in STAGES]
    if unknown:
        raise BuildError(f"unknown stage(s): {', '.join(sorted(unknown))}")

    wanted: set[str] = set()

    def pull(name: str, seen: tuple[str, ...] = ()) -> None:
        if name in seen:
            cycle = " -> ".join((*seen[seen.index(name):], name))
            raise BuildError(f"stage dependency cycle: {cycle}")
        if name in wanted:
            return
        for dependency in STAGES[name].requires:
            pull(dependency, (*seen, name))
        wanted.add(name)

    for name in requested:
        pull(name)

    rank = {name: index for index, name in enumerate(DECLARED_ORDER)}
    ordered = sorted(wanted, key=lambda name: rank.get(name, len(rank)))

    # Declared order must already satisfy every edge; assert rather than trust.
    position = {name: index for index, name in enumerate(ordered)}
    for name in ordered:
        for dependency in STAGES[name].requires:
            if dependency in position and position[dependency] > position[name]:
                raise BuildError(
                    f"declared order violates dependency {dependency} -> {name}"
                )
    return ordered


# --- planning -------------------------------------------------------------


@dataclass
class BuildPlan:
    target: Path
    temp_target: Path
    stages: list[str]
    resolved: dict
    release_tag: str
    profile: str
    dicts: tuple[str, ...]
    skipped: dict[str, str] = field(default_factory=dict)
    #: Scratch directory for stage side artifacts, or `None` for a canonical
    #: full build (which writes them to their in-repo homes).
    artifacts_dir: Path | None = None

    @property
    def lock_path(self) -> Path:
        return self.target.with_suffix(self.target.suffix + ".lock.json")


def plan_build(
    target: Path,
    requested: list[str] | None = None,
    *,
    release: bool = False,
    release_tag: str = "latest",
    dicts: tuple[str, ...] = ("mw", "pwg", "ap90"),
    profile: str = "full",
    env: dict[str, str] | None = None,
) -> BuildPlan:
    """Resolve the graph and every source; refuse a release build on `latest`."""
    if release and release_tag == "latest":
        raise BuildError(
            "release build refuses release_tag='latest': it is a mutable alias, "
            "so the recorded source lock would not identify the bytes built "
            "from. Pass an immutable csl-sqlite tag (YYYY-MM-DD-HH-MM-SS)."
        )

    ordered = expand(requested)
    resolved: dict = {}
    for name in ordered:
        for source_name in STAGES[name].sources:
            if source_name not in resolved:
                resolved[source_name] = sources_mod.resolve(source_name, env)

    skipped: dict[str, str] = {}
    runnable: list[str] = []
    for name in ordered:
        stage = STAGES[name]
        missing = [
            source_name
            for source_name in stage.sources
            if not resolved[source_name].exists
            and sources_mod.SOURCES[source_name].required
        ]
        blocked_by = [
            dependency for dependency in stage.requires if dependency in skipped
        ]
        unavailable = ""
        if stage.available is not None and not missing and not blocked_by:
            ok, why = stage.available()
            if not ok:
                unavailable = why
        if missing or blocked_by or unavailable:
            reason = (
                f"missing source(s): {', '.join(missing)}"
                if missing
                else f"prerequisite skipped: {', '.join(blocked_by)}"
                if blocked_by
                else unavailable
            )
            if not stage.optional:
                raise BuildError(f"stage '{name}' cannot run — {reason}")
            skipped[name] = reason
            continue
        runnable.append(name)

    temp = target.parent / ".build" / f"{target.name}.{os.getpid()}.tmp"
    # Side artifacts (lemma_examples.tsv, pronoun_corrections.tsv, the hybrid
    # report) go to their in-repo homes ONLY for a canonical full build. A
    # fixture run wrote seven rows over a committed 38,595-row file exactly
    # once, on 31-07-2026, before this line existed.
    canonical = profile == "full"
    artifacts = None if canonical else temp.parent / f"{target.stem}-artifacts"
    return BuildPlan(
        target=target,
        temp_target=temp,
        stages=runnable,
        resolved=resolved,
        release_tag=release_tag,
        profile=profile,
        dicts=dicts,
        skipped=skipped,
        artifacts_dir=artifacts,
    )


# --- source lock ----------------------------------------------------------


def lock_document(plan: BuildPlan, stage_results: dict) -> dict:
    return {
        "schema_version": LOCK_SCHEMA_VERSION,
        "profile": plan.profile,
        "release_tag": plan.release_tag,
        "dicts": list(plan.dicts),
        "declared_order": list(DECLARED_ORDER),
        "stages_run": list(plan.stages),
        "stages_skipped": plan.skipped,
        "postconditions": stage_results,
        "sources": {
            name: resolved.as_lock_entry() for name, resolved in sorted(plan.resolved.items())
        },
    }


def verify_against_lock(plan: BuildPlan) -> list[str]:
    """Compare resolved source digests with a previously written lock.

    Returns the list of human-readable mismatches; an empty list means the
    inputs are byte-identical to the recorded build. Missing lock ⇒ no claim,
    so no mismatch is reported.
    """
    if not plan.lock_path.is_file():
        return []
    recorded = json.loads(plan.lock_path.read_text(encoding="utf-8"))
    problems = []
    for name, entry in recorded.get("sources", {}).items():
        current = plan.resolved.get(name)
        if current is None:
            continue
        if entry.get("sha256") and current.sha256 != entry["sha256"]:
            problems.append(
                f"{name}: locked {entry['sha256'][:12]}… but resolved "
                f"{(current.sha256 or 'absent')[:12]}… at {current.path}"
            )
    return problems


# --- execution ------------------------------------------------------------


def _import_builders(names: list[str]):
    """Import the `scripts/` builder modules the planned stages need."""
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    wanted = {"build_db"}
    module_for = {
        "entries": "build_entries",
        "forms": "build_forms",
        "inflections": "build_inflections",
        "hybrid": "build_hybrid_forms",
        "pronoun": "build_pronoun_corrections",
        "stem_bridge": "build_stem_bridge",
        "evidence": "build_evidence",
        "layers": "build_db_layers",
    }
    for stage in names:
        if stage in module_for:
            wanted.add(module_for[stage])
    return {name: importlib.import_module(name) for name in sorted(wanted)}


def execute(plan: BuildPlan, *, relock: bool = False, verbose: bool = True) -> dict:
    """Run the planned stages into a temp target and promote it atomically."""
    mismatches = [] if relock else verify_against_lock(plan)
    if mismatches:
        raise BuildError(
            "source lock mismatch — the recorded build used different bytes:\n  "
            + "\n  ".join(mismatches)
            + "\nRe-run with --relock to accept the new sources."
        )

    modules = _import_builders(plan.stages)
    with sources_mod.injected(plan.resolved, modules):
        return _run(plan, modules, verbose=verbose)


def _run(plan: BuildPlan, modules: dict, *, verbose: bool) -> dict:
    plan.temp_target.parent.mkdir(parents=True, exist_ok=True)
    for stale in (plan.temp_target, Path(str(plan.temp_target) + "-journal")):
        if stale.exists():
            stale.unlink()

    build_db = modules["build_db"]
    started = time.time()
    con = build_db.connect(plan.temp_target)
    context = StageContext(
        resolved=plan.resolved,
        modules=modules,
        dicts=plan.dicts,
        release_tag=plan.release_tag,
        profile=plan.profile,
        artifacts_dir=plan.artifacts_dir,
    )
    if plan.artifacts_dir is not None:
        plan.artifacts_dir.mkdir(parents=True, exist_ok=True)

    results: dict = {}
    try:
        for name in plan.stages:
            stage: Stage = STAGES[name]
            if verbose:
                print(f"[dag] {name}: {stage.summary}")
            stage.run(con, context)
            con.commit()
            counts = {}
            for postcondition in stage.postconditions:
                ok, rows = postcondition.check(con)
                counts[postcondition.label or postcondition.count_from] = rows
                if not ok:
                    raise BuildError(
                        f"stage '{name}' postcondition failed: "
                        f"{postcondition.count_from} has {rows} row(s), "
                        f"expected at least {postcondition.min_rows}"
                    )
            results[name] = counts
            if verbose and counts:
                print(f"[dag] {name}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))

        for name, reason in plan.skipped.items():
            print(f"[dag] SKIP {name}: {reason}")

        lock = lock_document(plan, results)
        con.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (META_STAGE_KEY, json.dumps(
                {"run": plan.stages, "skipped": plan.skipped,
                 "declared": list(DECLARED_ORDER), "profile": plan.profile},
                ensure_ascii=False)),
        )
        con.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (META_LOCK_KEY, json.dumps(lock["sources"], ensure_ascii=False)),
        )
        con.execute(
            "INSERT INTO meta (key, value) VALUES ('data_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            ("0.1.0-dev" if plan.profile != "fixture" else "0.0.0-fixture",),
        )
        con.commit()

        violations = con.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise BuildError(
                f"foreign_key_check found {len(violations)} violation(s) in the "
                "temp target; refusing to promote"
            )
        con.execute("ANALYZE")
        con.commit()
    finally:
        con.close()

    plan.target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(plan.temp_target, plan.target)
    plan.lock_path.write_text(
        json.dumps(lock_document(plan, results), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if verbose:
        print(
            f"[dag] promoted {plan.target} "
            f"({len(plan.stages)} stage(s), {len(plan.skipped)} skipped, "
            f"{time.time() - started:.1f}s)"
        )
    return {"stages": results, "skipped": plan.skipped, "target": str(plan.target)}


def stage_manifest(db_path: Path) -> dict:
    """Read back what a built database says it ran. Empty dict if unrecorded."""
    if not Path(db_path).is_file():
        return {}
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        row = con.execute(
            "SELECT value FROM meta WHERE key=?", (META_STAGE_KEY,)
        ).fetchone()
    except sqlite3.OperationalError:
        return {}
    finally:
        con.close()
    return json.loads(row[0]) if row else {}
