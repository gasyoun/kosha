"""W0B (H1944) — the stage registry is the single source of truth.

Issue #210 was possible because the build had *two* stage lists that could
disagree: the `--stage` argparse choices and the `if args.stage in (...)`
ladder that actually dispatched. Five stages appeared in the first and were
missing from the no-flag path of the second.

These tests pin the properties that make a second list impossible: the CLI's
choices come from the registry, every registry row resolves to a real callable
and real source constants, and the no-flag plan is the whole registry in the
documented order.
"""
from __future__ import annotations

import pytest

from kosha.build import stages as S

pytestmark = pytest.mark.fixture

DOCUMENTED_ORDER = [
    "lemmas", "entries", "forms", "inflections", "hybrid",
    "pronoun", "stem_bridge", "heritage", "evidence", "layers",
]


def test_registry_matches_the_documented_order():
    assert list(S.STAGE_NAMES) == DOCUMENTED_ORDER


def test_full_plan_is_every_stage_in_that_order():
    assert [s.name for s in S.plan()] == DOCUMENTED_ORDER


def test_plan_is_stable_across_calls():
    assert [s.name for s in S.plan()] == [s.name for s in S.plan()]


def test_dependencies_all_name_real_stages():
    for stage in S.STAGES:
        for dep in stage.depends_on:
            assert dep in S.STAGE_NAMES, f"{stage.name} depends on unknown {dep!r}"


def test_dependencies_precede_their_dependants():
    position = {name: i for i, name in enumerate(S.STAGE_NAMES)}
    for stage in S.STAGES:
        for dep in stage.depends_on:
            assert position[dep] < position[stage.name], (
                f"{stage.name} declares a dependency on {dep}, which is "
                f"declared after it — the plan order would not be the "
                f"documented one")


def test_expand_is_transitively_closed():
    for stage in S.STAGES:
        expanded = set(S.expand([stage.name]))
        for name in list(expanded):
            assert set(S.by_name(name).depends_on) <= expanded, (
                f"expand({stage.name!r}) is missing a transitive dependency")


def test_expand_of_a_leaf_pulls_the_whole_chain():
    assert set(S.expand(["hybrid"])) == {"lemmas", "inflections", "hybrid"}
    assert set(S.expand(["pronoun"])) == {"lemmas", "inflections", "hybrid", "pronoun"}
    assert set(S.expand(["layers"])) == {"lemmas", "entries", "forms", "layers"}


def test_partial_plan_does_not_expand_by_default():
    assert [s.name for s in S.plan(["forms"])] == ["forms"]
    assert [s.name for s in S.plan(["forms"], with_deps=True)] == ["lemmas", "forms"]


def test_unknown_stage_is_rejected():
    with pytest.raises(S.UnknownStage):
        S.by_name("nope")
    with pytest.raises(S.UnknownStage):
        S.plan(["nope"])


def test_every_stage_resolves_to_a_callable():
    for stage in S.STAGES:
        func = S.resolve_callable(stage)
        assert callable(func), f"{stage.name} -> {stage.call} is not callable"


def test_every_declared_source_constant_exists():
    for stage in S.STAGES:
        paths = S.resolve_sources(stage)
        assert len(paths) >= len(stage.sources), stage.name


def test_every_stage_proves_something():
    for stage in S.STAGES:
        assert stage.postconditions, (
            f"{stage.name} declares no postcondition, so it could run to "
            f"completion having done nothing and still count as a success")
        for post in stage.postconditions:
            assert post.sql.upper().startswith("SELECT COUNT(")
            assert post.minimum >= 1


def test_call_args_are_known_context_keys():
    known = {"con", "dicts"}
    for stage in S.STAGES:
        assert set(stage.call_args) <= known, stage.name
        assert stage.call_args[0] == "con"


def test_cli_stage_choices_come_from_the_registry():
    from kosha.build.cli import build_parser

    parser = build_parser()
    action = next(a for a in parser._actions if a.dest == "stage")
    assert list(action.choices) == list(S.STAGE_NAMES)


def test_source_override_rejects_an_unknown_attribute():
    with pytest.raises(AttributeError):
        S.apply_source_overrides({"build_db.NOT_A_REAL_CONSTANT": "x"})


def test_source_override_rejects_a_bare_name():
    with pytest.raises(ValueError):
        S.apply_source_overrides({"UNION_HEADWORDS": "x"})
