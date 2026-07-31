"""The declarative kosha build DAG.

Every stage the build claims to have is a row in `STAGES`. There is no other
list — `scripts/build_db.py --stage` choices, the no-flag full build, the CI
fixture build and the build lock all read this one registry, so a stage cannot
exist in the help text and be missing from the run (issue #210's exact shape).

Each row declares:

* `depends_on` — what must be materialised first. The runner topologically
  sorts these; the tie-break is the declaration order below, which is why the
  no-flag plan comes out as the documented sequence
  `lemmas → entries → forms → inflections → hybrid → pronoun → stem_bridge →
  heritage → evidence → layers`.
* `sources` — the external feeds it reads, as `(module, attribute)` pairs
  resolved lazily against the builder scripts. Pointing at the builder's own
  constant rather than repeating a path here keeps one source of truth, and
  `tests/test_build_stages.py` fails if a named attribute disappears.
* `call` — `module:function` plus the context keys to pass, so the registry
  stays importable without dragging in sqlite, vidyut or the sibling repos.
* `postconditions` — what must be true of the database *after* the stage.
  A stage that runs to completion and leaves its table empty is a failure, not
  a success; this is what converts "silently omitted" into "loudly refused".
"""
from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path

from kosha.settings import repo_root

__all__ = [
    "Stage",
    "Postcondition",
    "STAGES",
    "STAGE_NAMES",
    "by_name",
    "expand",
    "plan",
    "apply_source_overrides",
    "resolve_sources",
    "resolve_callable",
    "UnknownStage",
]

def _scripts_dir() -> Path:
    return repo_root() / "scripts"


class UnknownStage(KeyError):
    """A stage name that is not in the registry."""


@dataclass(frozen=True)
class Postcondition:
    """A claim about the database that must hold once the stage has run."""

    label: str
    sql: str
    minimum: int = 1


@dataclass(frozen=True)
class Stage:
    name: str
    summary: str
    depends_on: tuple[str, ...]
    call: str
    call_args: tuple[str, ...]
    postconditions: tuple[Postcondition, ...]
    sources: tuple[tuple[str, str], ...] = ()
    # True when the feed legitimately may be absent on a working checkout (a
    # sibling repo nobody clones for API work). A missing REQUIRED feed aborts
    # the build; a missing optional feed still aborts unless the operator
    # passes --allow-missing-sources, which records an explicit skip.
    sources_optional: bool = False
    notes: str = ""


def _row_count(table: str, where: str = "") -> str:
    return f"SELECT COUNT(*) FROM {table}" + (f" WHERE {where}" if where else "")


STAGES: tuple[Stage, ...] = (
    Stage(
        name="lemmas",
        summary="vendor union_headwords.tsv, LEFT-JOIN the DCS frequency sidecar",
        depends_on=(),
        call="build_db:build_lemmas",
        call_args=("con",),
        sources=(("build_db", "UNION_HEADWORDS"), ("build_db", "FREQ_TSV")),
        postconditions=(Postcondition("lemmas loaded", _row_count("lemmas")),),
    ),
    Stage(
        name="entries",
        summary="load per-dict entries from the csl-sqlite releases",
        depends_on=("lemmas",),
        call="build_entries:build_entries",
        call_args=("con", "dicts"),
        sources=(("build_entries", "DL_DIR"),),
        postconditions=(
            Postcondition("entries loaded", _row_count("entries")),
            Postcondition("sources registered", _row_count("sources")),
        ),
    ),
    Stage(
        name="forms",
        summary="form -> lemma index (dcs, vidyut, heritage)",
        depends_on=("lemmas",),
        call="build_forms:build_forms",
        call_args=("con",),
        sources=(
            ("build_forms", "DCS_F2L"),
            ("build_forms", "VIDYUT_F2L"),
            ("build_forms", "HERITAGE_F2L"),
        ),
        postconditions=(Postcondition("forms loaded", _row_count("forms")),),
    ),
    Stage(
        name="inflections",
        summary="Cologne csl-inflect nominal + verb tables",
        depends_on=("lemmas",),
        call="build_inflections:build_inflections",
        call_args=("con",),
        sources=(
            ("build_inflections", "DEFAULT_CALC_TABLES"),
            ("build_inflections", "DEFAULT_VERB_TABLES"),
        ),
        sources_optional=True,
        notes="needs the generated MWinflect sibling tables, absent on most checkouts",
        postconditions=(Postcondition("inflections loaded", _row_count("inflections")),),
    ),
    Stage(
        name="hybrid",
        summary="layer vidyut-prakriya fixes/gap-fills over the Cologne base",
        # Must follow `inflections`, which DELETEs and repopulates the table and
        # would otherwise wipe the hybrid rows written before it.
        depends_on=("inflections",),
        call="build_hybrid_forms:build_hybrid_forms",
        call_args=("con",),
        postconditions=(
            Postcondition(
                "hybrid rows present",
                _row_count("inflections", "source IN ('hybrid-natva-fix','vidyut-gap-fill')"),
            ),
        ),
    ),
    Stage(
        name="pronoun",
        summary="curated Gita pronoun-paradigm corrections",
        depends_on=("inflections", "hybrid"),
        call="build_pronoun_corrections:apply_pronoun_corrections",
        call_args=("con",),
        sources=(("build_pronoun_corrections", "GOLD"),),
        postconditions=(
            Postcondition(
                "pronoun corrections applied",
                _row_count("inflections", "source = 'curated-gita-pronoun'"),
            ),
        ),
    ),
    Stage(
        name="stem_bridge",
        summary="stem-normalisation crosswalk between inflections and forms",
        depends_on=("inflections", "forms"),
        call="build_stem_bridge:build_stem_bridge",
        call_args=("con",),
        postconditions=(Postcondition("bridge built", _row_count("stem_bridge")),),
    ),
    Stage(
        name="heritage",
        summary="MW<->Heritage coverage witness (consumed verbatim)",
        # Loads standalone, but its own summary counts the entries it joins, so
        # it is ordered after them rather than reporting a meaningless zero.
        depends_on=("entries",),
        call="build_db:build_heritage",
        call_args=("con",),
        sources=(("build_db", "HERITAGE_CROSSWALK"),),
        postconditions=(
            Postcondition("heritage anchors loaded", _row_count("heritage_anchor")),
            Postcondition(
                "heritage coverage non-empty",
                _row_count("heritage_anchor", "covered = 1"),
            ),
        ),
    ),
    Stage(
        name="evidence",
        summary="P3 evidence layer: band, first era, corpus example",
        depends_on=("lemmas", "forms"),
        call="build_evidence:build_evidence",
        call_args=("con",),
        sources=(("build_evidence", "CORPUS_LEXICON"),),
        sources_optional=True,
        notes="corpus_lexicon.jsonl lives in the RussianTranslation sibling",
        postconditions=(
            Postcondition("evidence bands stamped", _row_count("lemmas", "band IS NOT NULL")),
        ),
    ),
    Stage(
        name="layers",
        summary="P-D5 public join layers (additive, never mutates core tables)",
        depends_on=("lemmas", "entries", "forms"),
        call="build_db_layers:build_layers",
        call_args=("con",),
        sources=(
            ("build_db_layers", "SENSE_FREQ_TSV"),
            ("build_db_layers", "ROOTS_FREQ_TSV"),
            ("build_db_layers", "DICT_COVERAGE_TSV"),
        ),
        sources_optional=True,
        postconditions=(
            Postcondition(
                "layer version stamped",
                "SELECT COUNT(*) FROM meta WHERE key = 'pd5_layers'",
            ),
        ),
    ),
)

STAGE_NAMES: tuple[str, ...] = tuple(s.name for s in STAGES)
_BY_NAME = {s.name: s for s in STAGES}
_ORDER = {s.name: i for i, s in enumerate(STAGES)}


def by_name(name: str) -> Stage:
    try:
        return _BY_NAME[name]
    except KeyError:
        raise UnknownStage(
            f"unknown stage {name!r}; known stages: {', '.join(STAGE_NAMES)}"
        ) from None


def expand(names) -> list[str]:
    """Every stage in `names` plus everything they transitively depend on."""
    wanted: set[str] = set()
    stack = list(names)
    while stack:
        current = stack.pop()
        if current in wanted:
            continue
        stage = by_name(current)
        wanted.add(current)
        stack.extend(stage.depends_on)
    return sorted(wanted, key=lambda n: _ORDER[n])


def plan(names=None, *, with_deps: bool = False) -> list[Stage]:
    """Topologically ordered stages to run.

    `names=None` means the full build. `with_deps` expands each requested stage
    to its prerequisites; it is off by default so `--stage forms` still runs
    *forms* and nothing else, exactly as the runbooks document. The runner
    checks those unexpanded prerequisites against the build lock instead, which
    catches staleness without silently rebuilding gigabytes the operator did not
    ask for.

    The tie-break between stages ready at the same moment is the registry's
    declaration order, which is what makes the full plan reproducible run to run
    — and equal to the sequence the docs promise.
    """
    requested = list(names) if names is not None else list(STAGE_NAMES)
    for name in requested:
        by_name(name)
    wanted = set(expand(requested) if with_deps else requested)
    remaining = {n: set(by_name(n).depends_on) & wanted for n in wanted}
    ordered: list[Stage] = []
    done: set[str] = set()
    while remaining:
        ready = sorted((n for n, deps in remaining.items() if deps <= done),
                       key=lambda n: _ORDER[n])
        if not ready:
            raise ValueError(f"cycle in stage graph among {sorted(remaining)}")
        nxt = ready[0]
        ordered.append(by_name(nxt))
        done.add(nxt)
        del remaining[nxt]
    return ordered


def _import_builder(module: str):
    """Import a `scripts/` builder module by name.

    The builders are scripts, not a package: they import each other flat
    (`from build_evidence import ensure_columns`), so `scripts/` has to be on
    `sys.path` rather than them being imported as `scripts.build_x`.
    """
    scripts = str(_scripts_dir())
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return importlib.import_module(module)


def resolve_callable(stage: Stage):
    module_name, _, func_name = stage.call.partition(":")
    module = _import_builder(module_name)
    try:
        return getattr(module, func_name)
    except AttributeError as exc:
        raise AttributeError(
            f"stage {stage.name!r} names {stage.call!r}, but {func_name!r} is "
            f"not defined in {module_name!r}"
        ) from exc


def apply_source_overrides(overrides: dict[str, Path]) -> dict[str, Path]:
    """Point builder modules at a different set of feed files.

    Keys are `module.ATTRIBUTE` — the same coordinates the registry already
    uses to name a stage's sources, so a fixture pack cannot redirect a feed
    the registry does not know about. Returns what was actually rebound, for
    the build lock.

    This is how the committed fixture pack drives a real build: the builders
    are untouched and read their own constants as always; only the constants
    move. Nothing here is test-only scaffolding inside production code paths.
    """
    applied: dict[str, Path] = {}
    for key, value in overrides.items():
        module_name, _, attr = key.rpartition(".")
        if not module_name:
            raise ValueError(f"source override key must be 'module.ATTR', got {key!r}")
        module = _import_builder(module_name)
        if not hasattr(module, attr):
            raise AttributeError(
                f"source override {key!r} names an attribute that does not exist"
            )
        path = Path(value)
        setattr(module, attr, path)
        applied[key] = path
    return applied


def resolve_sources(stage: Stage) -> list[Path]:
    """The concrete feed paths this stage reads, in declaration order."""
    paths: list[Path] = []
    for module_name, attr in stage.sources:
        module = _import_builder(module_name)
        try:
            value = getattr(module, attr)
        except AttributeError as exc:
            raise AttributeError(
                f"stage {stage.name!r} declares source {module_name}.{attr}, "
                f"which no longer exists"
            ) from exc
        if isinstance(value, (str, Path)):
            paths.append(Path(value))
        else:  # a tuple/list of paths
            paths.extend(Path(v) for v in value)
    return paths
