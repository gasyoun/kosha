"""The declared build DAG — expansion, locking, promotion (H1944, W0B).

These are the tests that would have caught
[integrity issue #210](https://github.com/gasyoun/kosha/issues/210) on the day
it was introduced: the no-flag build must expand to *every* declared stage,
and a built database must be able to say which stages actually ran.
"""

import json
from pathlib import Path
import sqlite3

import pytest

from kosha.build import dag, fixtures
from kosha.build.stages import DECLARED_ORDER, STAGES


# --- expansion ------------------------------------------------------------


def test_no_flag_build_runs_every_declared_stage():
    """#210 in one assertion: the default build is the whole graph."""
    assert dag.expand(None) == list(DECLARED_ORDER)


def test_declared_order_is_the_documented_order():
    assert DECLARED_ORDER == (
        "lemmas", "entries", "forms", "inflections", "hybrid", "pronoun",
        "stem_bridge", "heritage", "evidence", "layers",
    )
    assert set(DECLARED_ORDER) == set(STAGES)


def test_requesting_one_stage_pulls_its_prerequisites():
    assert dag.expand(["stem_bridge"]) == [
        "lemmas", "forms", "inflections", "stem_bridge",
    ]
    assert dag.expand(["lemmas"]) == ["lemmas"]


def test_every_dependency_precedes_its_dependent():
    order = dag.expand(None)
    position = {name: index for index, name in enumerate(order)}
    for name, stage in STAGES.items():
        for dependency in stage.requires:
            assert position[dependency] < position[name], f"{dependency} after {name}"


def test_unknown_stage_is_refused():
    with pytest.raises(dag.BuildError, match="unknown stage"):
        dag.expand(["not_a_stage"])


# --- release-tag immutability --------------------------------------------


def test_release_build_refuses_the_latest_alias(tmp_path):
    with pytest.raises(dag.BuildError, match="mutable alias"):
        dag.plan_build(tmp_path / "kosha.db", release=True, release_tag="latest")


def test_release_build_accepts_a_pinned_tag(tmp_path):
    plan = dag.plan_build(
        tmp_path / "kosha.db",
        ["lemmas"],
        release=True,
        release_tag="2026-05-01-00-00-00",
        env=fixtures.fixture_env(),
    )
    assert plan.release_tag == "2026-05-01-00-00-00"


# --- prerequisites --------------------------------------------------------


def test_missing_required_source_fails_before_any_write(tmp_path):
    """A missing feed must stop the *plan*, not a half-written database."""
    target = tmp_path / "kosha.db"
    env = dict(fixtures.fixture_env())
    env["KOSHA_SRC_UNION_HEADWORDS"] = str(tmp_path / "absent.tsv")
    with pytest.raises(dag.BuildError, match="cannot run"):
        dag.plan_build(target, ["lemmas"], env=env)
    assert not target.exists()


def test_optional_stage_missing_source_is_skipped_not_fatal(tmp_path):
    env = dict(fixtures.fixture_env())
    env["KOSHA_SRC_MWINFLECT_NOMINALS"] = str(tmp_path / "absent.txt")
    plan = dag.plan_build(tmp_path / "kosha.db", ["inflections"], env=env)
    assert "inflections" in plan.skipped
    assert "mwinflect_nominals" in plan.skipped["inflections"]


def test_skipping_a_stage_skips_its_dependents(tmp_path):
    env = dict(fixtures.fixture_env())
    env["KOSHA_SRC_MWINFLECT_NOMINALS"] = str(tmp_path / "absent.txt")
    plan = dag.plan_build(tmp_path / "kosha.db", ["stem_bridge"], env=env)
    assert "stem_bridge" in plan.skipped
    assert "prerequisite skipped" in plan.skipped["stem_bridge"]


# --- fixture build end to end --------------------------------------------


@pytest.fixture(scope="module")
def fixture_build(tmp_path_factory):
    """One clean build from zero, shared by the assertions below."""
    workspace = tmp_path_factory.mktemp("fixture-build")
    cache = fixtures.materialize(workspace / "cache")
    plan = dag.plan_build(
        workspace / "kosha.db",
        env=fixtures.fixture_env(cache),
        profile="fixture",
        release_tag=fixtures.release_tag(),
    )
    dag.execute(plan, verbose=False)
    return plan


def test_fixture_build_from_zero_runs_the_core_stages(fixture_build):
    assert fixture_build.target.is_file()
    for required in ("lemmas", "entries", "forms", "heritage", "evidence"):
        assert required in fixture_build.stages


def test_fixture_build_records_its_stage_manifest(fixture_build):
    manifest = dag.stage_manifest(fixture_build.target)
    assert manifest["declared"] == list(DECLARED_ORDER)
    assert manifest["run"] == fixture_build.stages
    assert manifest["profile"] == "fixture"


def test_fixture_build_populates_every_core_table(fixture_build):
    con = sqlite3.connect(fixture_build.target)
    try:
        for table in ("lemmas", "entries", "senses", "sources", "forms", "heritage_anchor"):
            count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert count > 0, f"{table} is empty after a full fixture build"
    finally:
        con.close()


def test_fixture_build_writes_a_source_lock(fixture_build):
    lock = json.loads(fixture_build.lock_path.read_text(encoding="utf-8"))
    assert lock["schema_version"] == dag.LOCK_SCHEMA_VERSION
    assert lock["release_tag"].startswith("fixture-")
    assert lock["declared_order"] == list(DECLARED_ORDER)
    union = lock["sources"]["union_headwords"]
    assert len(union["sha256"]) == 64 and union["exists"]


def test_rebuild_is_stable_across_two_clean_runs(tmp_path):
    """Build twice from zero; the logical content must be identical."""
    cache = fixtures.materialize(tmp_path / "cache")
    env = fixtures.fixture_env(cache)
    dumps = []
    for index in (1, 2):
        target = tmp_path / f"kosha{index}.db"
        plan = dag.plan_build(
            target, env=env, profile="fixture", release_tag=fixtures.release_tag()
        )
        dag.execute(plan, verbose=False)
        con = sqlite3.connect(target)
        try:
            # Logical dump, not a file hash: SQLite pages are not byte
            # deterministic (the verification plan says so explicitly).
            # `meta` is excluded — it carries the build's own paths.
            dumps.append([
                row for row in con.iterdump()
                if "INSERT INTO \"meta\"" not in row
            ])
        finally:
            con.close()
    assert dumps[0] == dumps[1]


def test_fixture_build_never_writes_in_repo_derived_artifacts(tmp_path):
    """A seven-lemma fixture run must not touch committed derived files.

    Regression: the first fixture build overwrote
    `data/evidence/lemma_examples.tsv` (38,595 rows, committed) with its six
    fixture rows, because `build_evidence` writes that path unconditionally.
    Non-canonical builds now write side artifacts into their own scratch dir.
    """
    repo_root = Path(__file__).resolve().parent.parent
    watched = [
        repo_root / "data" / "evidence" / "lemma_examples.tsv",
        repo_root / "data" / "gita" / "pronoun_corrections.tsv",
    ]
    before = {path: path.read_bytes() for path in watched if path.is_file()}

    cache = fixtures.materialize(tmp_path / "cache")
    plan = dag.plan_build(
        tmp_path / "kosha.db",
        env=fixtures.fixture_env(cache),
        profile="fixture",
        release_tag=fixtures.release_tag(),
    )
    assert plan.artifacts_dir is not None
    dag.execute(plan, verbose=False)

    for path, payload in before.items():
        assert path.read_bytes() == payload, f"{path} was overwritten by a fixture build"


# --- source lock enforcement ---------------------------------------------


def test_changed_source_bytes_fail_the_lock(tmp_path):
    cache = fixtures.materialize(tmp_path / "cache")
    env = dict(fixtures.fixture_env(cache))
    headwords = tmp_path / "union_headwords.tsv"
    headwords.write_text(
        "slp1\tiast\tn_dicts\tdicts\tgender\nagni\tagni\t1\tmw\tm\n", encoding="utf-8"
    )
    env["KOSHA_SRC_UNION_HEADWORDS"] = str(headwords)

    target = tmp_path / "kosha.db"
    plan = dag.plan_build(target, ["lemmas"], env=env, profile="fixture")
    dag.execute(plan, verbose=False)

    headwords.write_text(
        "slp1\tiast\tn_dicts\tdicts\tgender\nindra\tindra\t1\tmw\tm\n", encoding="utf-8"
    )
    replan = dag.plan_build(target, ["lemmas"], env=env, profile="fixture")
    with pytest.raises(dag.BuildError, match="source lock mismatch"):
        dag.execute(replan, verbose=False)

    # …and --relock accepts the new bytes deliberately.
    dag.execute(replan, relock=True, verbose=False)


# --- atomic promotion -----------------------------------------------------


def test_failed_postcondition_leaves_the_target_untouched(tmp_path, monkeypatch):
    cache = fixtures.materialize(tmp_path / "cache")
    env = fixtures.fixture_env(cache)
    target = tmp_path / "kosha.db"
    target.write_bytes(b"sentinel - must survive a failed build")

    import dataclasses

    from kosha.build.stages import Postcondition

    impossible = Postcondition("lemmas", min_rows=10**9, label="impossible")
    monkeypatch.setitem(
        STAGES, "lemmas",
        dataclasses.replace(STAGES["lemmas"], postconditions=(impossible,)),
    )
    plan = dag.plan_build(target, ["lemmas"], env=env, profile="fixture")
    with pytest.raises(dag.BuildError, match="postcondition failed"):
        dag.execute(plan, verbose=False)

    assert target.read_bytes() == b"sentinel - must survive a failed build"
