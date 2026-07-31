"""kosha build stages — the declared graph (W0B item 4, H1944).

This registry is the fix for
[integrity issue #210](https://github.com/gasyoun/kosha/issues/210): the old
`scripts/build_db.py` dispatched on `if args.stage in (None, "x")`, so a
no-flag "full" build silently ran four of the ten stages and skipped
`entries`, `forms`, `inflections`, `hybrid`, and `stem_bridge` without a word.
Anything reading the resulting database saw a plausible-looking store that was
missing most of its content.

Here every stage declares:

- **`requires`** — the stages whose output it reads. The default build is the
  topological expansion of the whole registry, never a hand-maintained `if`
  chain, so a stage cannot be forgotten by omission.
- **`sources`** — its external inputs, resolved and digested before any write.
- **`postcondition`** — what must be true of the database afterwards. A stage
  that runs and produces nothing fails the build instead of passing quietly.

Declared order (the plan's required expansion):

    lemmas → entries → forms → inflections → hybrid → pronoun
           → stem_bridge → heritage → evidence → layers
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Postcondition:
    """What the database must show once a stage has run."""

    #: `SELECT COUNT(*)` fragment, e.g. `"lemmas"` or `"inflections WHERE …"`.
    count_from: str
    min_rows: int = 1
    label: str = ""

    def check(self, con: sqlite3.Connection) -> tuple[bool, int]:
        rows = con.execute(f"SELECT COUNT(*) FROM {self.count_from}").fetchone()[0]
        return rows >= self.min_rows, rows


@dataclass(frozen=True)
class Stage:
    name: str
    summary: str
    run: Callable[[sqlite3.Connection, "StageContext"], object]
    requires: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    postconditions: tuple[Postcondition, ...] = ()
    #: A stage whose required sources are absent is skipped with a logged
    #: reason instead of failing the build (D19/D20: log and skip isolated
    #: noncritical gaps; the *declared* graph still records that it was
    #: skipped, which is the difference from #210).
    optional: bool = False
    #: Extra runtime precondition beyond the declared sources — an importable
    #: local library, say. Returns `(available, reason)`; a false verdict
    #: skips an optional stage and fails a required one, both loudly.
    available: Callable[[], tuple[bool, str]] | None = None


@dataclass
class StageContext:
    """Everything a stage body needs that is not the connection."""

    #: name -> resolved source (see `kosha.build.sources`).
    resolved: dict
    #: Imported builder modules, keyed by module name.
    modules: dict
    dicts: tuple[str, ...] = ("mw", "pwg", "ap90")
    #: csl-sqlite release tag. `"latest"` is a mutable alias and is refused
    #: for release builds by `dag.plan_build`.
    release_tag: str = "latest"
    profile: str = "full"
    #: Where a stage's *side artifacts* go — the TSVs some builders write next
    #: to the database. `None` means the canonical in-repo locations. Any
    #: non-canonical build (fixture profile, custom `--target`) gets a scratch
    #: directory instead, because a seven-lemma fixture run must never
    #: overwrite a 38,595-row committed derived file.
    artifacts_dir: "Path | None" = None
    notes: list[str] = field(default_factory=list)

    def path(self, name: str) -> Path:
        return self.resolved[name].path

    def present(self, name: str) -> bool:
        return bool(self.resolved.get(name) and self.resolved[name].exists)


# --- stage bodies ---------------------------------------------------------
#
# Each body calls the existing builder in `scripts/`. W0B deliberately does not
# move that code: D11 keeps `scripts/` working as a compatibility entry point,
# and moving ten builders in the same PR that introduces the DAG would make
# the diff unreviewable. What changes is *who decides the order*.


def _lemmas(con, ctx):
    return ctx.modules["build_db"].build_lemmas(con)


def _entries(con, ctx):
    return ctx.modules["build_entries"].build_entries(
        con, list(ctx.dicts), release_tag=ctx.release_tag
    )


def _forms(con, ctx):
    return ctx.modules["build_forms"].build_forms(con)


def _inflections(con, ctx):
    # Explicit paths, not module constants: `build_inflections` binds its
    # table paths as *default arguments*, which are evaluated at import time
    # and so ignore any later attribute rewrite.
    return ctx.modules["build_inflections"].build_inflections(
        con,
        calc_tables_path=ctx.path("mwinflect_nominals"),
        verb_tables_path=ctx.path("mwinflect_verbs"),
    )


def _hybrid(con, ctx):
    module = ctx.modules["build_hybrid_forms"]
    if ctx.artifacts_dir is None:
        return module.build_hybrid_forms(con)
    return module.build_hybrid_forms(con, out_dir=ctx.artifacts_dir)


def _pronoun(con, ctx):
    module = ctx.modules["build_pronoun_corrections"]
    if ctx.artifacts_dir is None:
        return module.apply_pronoun_corrections(con)
    with _rebound(module, {"OUT": ctx.artifacts_dir / "pronoun_corrections.tsv"}, {}):
        return module.apply_pronoun_corrections(con)


def _stem_bridge(con, ctx):
    return ctx.modules["build_stem_bridge"].build_stem_bridge(con)


def _heritage(con, ctx):
    return ctx.modules["build_db"].build_heritage(con)


def _evidence(con, ctx):
    module = ctx.modules["build_evidence"]
    if ctx.artifacts_dir is None:
        return module.build_evidence(con)
    constants = {
        "EVIDENCE_DIR": ctx.artifacts_dir,
        "EXAMPLES_TSV": ctx.artifacts_dir / "lemma_examples.tsv",
    }
    with _rebound(module, constants, {}):
        return module.build_evidence(con)


def _layers(con, ctx):
    layers = ctx.modules["build_db_layers"]
    # `build_db_layers` binds every feed path as a *default argument*, which is
    # evaluated at import time, so rewriting the module constant alone is not
    # enough — `build_layers` calls each loader with no `path`. Rebind the
    # defaults for the duration of the stage and put them back afterwards.
    bindings = {
        layers.load_sense_frequency: ctx.path("sense_frequency"),
        layers.load_roots_frequency: ctx.path("roots_frequency"),
        layers.load_dict_corpus_coverage: ctx.path("dict_corpus_coverage"),
        layers.load_mw_roots: ctx.path("mw_roots"),
        layers.load_mw_etymology: ctx.path("mw_etymology"),
    }
    constants = {
        "SENSE_FREQ_TSV": ctx.path("sense_frequency"),
        "ROOTS_FREQ_TSV": ctx.path("roots_frequency"),
        "DICT_COVERAGE_TSV": ctx.path("dict_corpus_coverage"),
        "MW_ROOTS_TSV": ctx.path("mw_roots"),
        "MW_ETYMOLOGY_TSV": ctx.path("mw_etymology"),
    }
    with _rebound(layers, constants, bindings):
        return layers.build_layers(con)


@contextmanager
def _rebound(module, constants: dict, bindings: dict):
    """Point a legacy builder at resolved paths, then restore it exactly.

    Restoration is not cosmetic: these modules are imported once per process,
    so a permanent rewrite would leak the fixture pack into every later caller
    — including the rest of the test session.
    """
    saved_constants = {name: getattr(module, name) for name in constants}
    saved_defaults = {func: func.__defaults__ for func in bindings}
    try:
        for name, value in constants.items():
            setattr(module, name, value)
        for func, path in bindings.items():
            _rebind_defaults(func, {"path": path})
        yield
    finally:
        for name, value in saved_constants.items():
            setattr(module, name, value)
        for func, defaults in saved_defaults.items():
            func.__defaults__ = defaults


def _rebind_defaults(func, replacements: dict) -> None:
    """Rewrite a function's keyword defaults in place.

    Only used for the legacy builders that bind feed paths as default
    arguments. Narrow and explicit beats a wholesale rewrite of those builders
    in the same PR as the DAG. Always paired with `_rebound`, which restores.
    """
    names = func.__code__.co_varnames[: func.__code__.co_argcount]
    defaults = list(func.__defaults__ or ())
    if not defaults:
        return
    offset = len(names) - len(defaults)
    for index, name in enumerate(names[offset:]):
        if name in replacements:
            defaults[index] = replacements[name]
    func.__defaults__ = tuple(defaults)


def _importable(module: str, note: str):
    """Precondition factory: is a local library importable in this interpreter?"""

    def check() -> tuple[bool, str]:
        import importlib.util

        try:
            found = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            found = False
        return found, "" if found else f"{module} not importable ({note})"

    return check


def _sanskrit_util_available() -> tuple[bool, str]:
    """`build_pronoun_corrections` imports `sanskrit_util` from a sibling repo
    at module import time, so probe the checkout rather than the import path."""
    from pathlib import Path as _Path

    for candidate in (ROOT.parent, ROOT.parent.parent):
        if (_Path(candidate) / "sanskrit-util" / "py" / "sanskrit_util").exists():
            return True, ""
    return False, "sibling sanskrit-util checkout absent"


#: The declared graph. Order in this dict is the declared order; the DAG still
#: topologically sorts it so a wrong hand-edit here cannot produce a build that
#: runs a stage before its prerequisite.
STAGES: dict[str, Stage] = {
    "lemmas": Stage(
        "lemmas",
        "D1 — vendor the union headword spine, join the frequency sidecar",
        _lemmas,
        sources=("union_headwords", "lemma_frequency"),
        postconditions=(Postcondition("lemmas"),),
    ),
    "entries": Stage(
        "entries",
        "D2 — load per-dict entries from the csl-sqlite release, segment senses",
        _entries,
        requires=("lemmas",),
        sources=("csl_sqlite_cache",),
        postconditions=(
            Postcondition("entries"),
            Postcondition("senses"),
            Postcondition("sources"),
        ),
    ),
    "forms": Stage(
        "forms",
        "D3 — inflected form→lemma index (DCS + vidyut + Heritage)",
        _forms,
        requires=("lemmas",),
        sources=("dcs_form2lemma", "vidyut_form2lemma", "heritage_forms"),
        postconditions=(Postcondition("forms"),),
    ),
    "inflections": Stage(
        "inflections",
        "K1 — MWinflect nominal + verb paradigm tables",
        _inflections,
        requires=("lemmas",),
        sources=("mwinflect_nominals", "mwinflect_verbs"),
        postconditions=(Postcondition("inflections"),),
        optional=True,
    ),
    "hybrid": Stage(
        "hybrid",
        "E1 — layer vidyut-prakriya over the Cologne inflections base",
        _hybrid,
        requires=("inflections",),
        postconditions=(
            # The base must survive the overlay — hybrid appends, it must never
            # leave the paradigm table empty.
            Postcondition("inflections", label="inflections after overlay"),
            # Correction count is *recorded*, not required: a corpus with no
            # ṇatva bug and no vidyut-only gap legitimately yields zero rows
            # (the fixture pack is exactly that case).
            Postcondition(
                "inflections WHERE source IN ('hybrid-natva-fix','vidyut-gap-fill')",
                min_rows=0,
                label="hybrid corrections",
            ),
        ),
        optional=True,
        available=_importable("vidyut", "pip install vidyut, E1 hybridize input"),
    ),
    "pronoun": Stage(
        "pronoun",
        "W4 QA — curated Gītā pronoun paradigm corrections",
        _pronoun,
        requires=("inflections",),
        sources=("gita_morphology_gold",),
        postconditions=(
            Postcondition(
                "inflections WHERE source='curated-gita-pronoun'",
                label="curated pronoun rows",
            ),
        ),
        optional=True,
        available=_sanskrit_util_available,
    ),
    "stem_bridge": Stage(
        "stem_bridge",
        "K2a — stem-normalization crosswalk between inflections and forms",
        _stem_bridge,
        requires=("inflections", "forms"),
        postconditions=(Postcondition("stem_bridge"),),
        optional=True,
    ),
    "heritage": Stage(
        "heritage",
        "H345 — Heritage coverage witness",
        _heritage,
        requires=("entries",),
        sources=("heritage_crosswalk",),
        postconditions=(Postcondition("heritage_anchor"),),
    ),
    "evidence": Stage(
        "evidence",
        "P3 — frequency bands, first era, corpus examples",
        _evidence,
        requires=("lemmas", "forms"),
        sources=("corpus_lexicon",),
        postconditions=(
            Postcondition("lemmas WHERE band IS NOT NULL", label="banded lemmas"),
        ),
    ),
    "layers": Stage(
        "layers",
        "P-D5 — additive public join layers",
        _layers,
        requires=("entries",),
        sources=(
            "sense_frequency", "roots_frequency", "dict_corpus_coverage",
            "mw_roots", "mw_etymology",
        ),
        postconditions=(),
        optional=True,
    ),
}

#: The declared full order, for documentation and for the truth test that
#: pins it. `dag.expand` must reproduce this when asked for everything.
DECLARED_ORDER = (
    "lemmas", "entries", "forms", "inflections", "hybrid", "pronoun",
    "stem_bridge", "heritage", "evidence", "layers",
)
