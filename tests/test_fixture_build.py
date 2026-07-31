"""W0B (H1944) — the from-zero fixture build, and the guards around it.

This is the executable form of [issue #210](https://github.com/gasyoun/kosha/issues/210):
a no-flag build used to skip five of its ten declared stages and still exit 0.
Here a full build runs against the committed fixture pack, from an empty file,
and the build lock is checked stage by stage — so "every declared stage ran"
is asserted, not asserted-to-have-been-asserted.

Everything runs in a **subprocess**, through the same `scripts/build_db.py`
entry point a human types. Two reasons: it exercises the real CLI rather than
an in-process shortcut, and it keeps the builders' rebound module constants out
of the rest of the pytest session.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fixture

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "tests" / "fixtures" / "pack"
MANIFEST = PACK / "sources.json"
BUILD = ROOT / "scripts" / "build_db.py"

DECLARED_STAGES = [
    "lemmas", "entries", "forms", "inflections", "hybrid",
    "pronoun", "stem_bridge", "heritage", "evidence", "layers",
]


def run_build(target: Path, *extra: str, expect_ok: bool = True):
    cmd = [sys.executable, str(BUILD), "--sources", str(MANIFEST),
           "--db", str(target), *extra]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          env=env, cwd=str(ROOT))
    if expect_ok and proc.returncode != 0:
        pytest.fail(f"build failed ({proc.returncode})\n"
                    f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
    return proc


def read_lock(target: Path) -> dict:
    lock_path = target.with_name(target.stem + ".build-lock.json")
    assert lock_path.exists(), f"no build lock beside {target}"
    return json.loads(lock_path.read_text(encoding="utf-8"))


def counts(target: Path) -> dict:
    import sqlite3

    con = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        return {
            table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("lemmas", "entries", "senses", "forms", "inflections",
                          "stem_bridge", "heritage_anchor", "sources")
        }
    finally:
        con.close()


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    target = tmp_path_factory.mktemp("fixture-build") / "kosha.db"
    run_build(target)
    return target


# --- the #210 claim ----------------------------------------------------------

def test_pack_is_present():
    assert MANIFEST.exists(), (
        "the fixture pack is committed; regenerate with scripts/build_fixture_pack.py")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["overrides"], "manifest redirects no feeds"


def test_every_declared_stage_ran(built):
    lock = read_lock(built)
    assert lock["plan"] == DECLARED_STAGES, (
        f"the no-flag plan is not the declared order: {lock['plan']}")
    for name in DECLARED_STAGES:
        record = lock["stages"].get(name)
        assert record is not None, f"stage {name!r} left no record at all"
        assert record["status"] == "ok", (
            f"stage {name!r} was {record['status']}: {record.get('reason')}")


def test_every_stage_proved_a_postcondition(built):
    lock = read_lock(built)
    for name in DECLARED_STAGES:
        posts = lock["stages"][name]["postconditions"]
        assert posts, f"stage {name!r} proved nothing"
        for post in posts:
            assert post["ok"], f"{name}: {post['label']} = {post['count']}"
            assert post["count"] >= post["minimum"]


def test_build_populated_every_core_table(built):
    for table, n in counts(built).items():
        assert n > 0, f"{table} is empty after a full build"


def test_lock_records_the_fixture_source_set(built):
    lock = read_lock(built)
    assert lock["source_set"] == "fixture-pack", (
        "a lock that does not name its feed set cannot distinguish a fixture "
        "artifact from a real one")
    for name in ("lemmas", "entries", "forms"):
        sources = lock["stages"][name]["sources"]
        assert sources, f"{name} recorded no sources"
        assert any("fixtures" in s["path"] for s in sources), (
            f"{name} recorded sources outside the pack: "
            f"{[s['path'] for s in sources]}")
        for source in sources:
            assert source["exists"] and source["digest"]


def test_stage_sources_were_actually_read(built):
    """A recorded source that the stage did not read is a provenance lie.

    Caught for real during H1944: `build_db_layers` and `build_inflections`
    bound their feed paths as *default arguments*, so redirecting the module
    constant moved the lock entry and not the read. `inflections` loaded 6.9 M
    rows from the real MWinflect tables while the lock named a 52-line fixture.
    The proxy for "actually read" is that the row counts stay fixture-scale.
    """
    n = counts(built)
    assert n["lemmas"] <= 100, f"lemmas={n['lemmas']} — that is not the fixture feed"
    assert n["inflections"] <= 50_000, (
        f"inflections={n['inflections']} — the real MWinflect tables were read "
        f"instead of the fixture slice")
    assert n["entries"] <= 5_000, f"entries={n['entries']} — not the fixture dumps"


# --- built twice: from zero, and reproducibly ---------------------------------

def test_second_from_zero_build_reproduces_the_first(built, tmp_path):
    second = tmp_path / "again" / "kosha.db"
    run_build(second)
    assert counts(second) == counts(built), (
        "two clean builds from the same pack disagree on row counts")
    lock_a, lock_b = read_lock(built), read_lock(second)
    assert lock_a["plan"] == lock_b["plan"]
    for name in DECLARED_STAGES:
        digests_a = [(s["path"], s["digest"]) for s in lock_a["stages"][name]["sources"]]
        digests_b = [(s["path"], s["digest"]) for s in lock_b["stages"][name]["sources"]]
        assert digests_a == digests_b, f"{name}: source digests moved between builds"


def test_promotion_is_atomic(built):
    leftovers = list(built.parent.glob("*.building-*"))
    assert not leftovers, f"temporary build targets left behind: {leftovers}"
    assert built.exists() and built.stat().st_size > 0


def test_data_version_and_build_id_are_stamped(built):
    import sqlite3

    con = sqlite3.connect(f"file:{built}?mode=ro", uri=True)
    try:
        meta = dict(con.execute("SELECT key, value FROM meta").fetchall())
    finally:
        con.close()
    assert meta["data_version"] == "0.1.0-dev"
    assert meta["build_id"] == read_lock(built)["build_id"]


# --- the guards --------------------------------------------------------------

def test_release_refuses_latest(tmp_path):
    proc = run_build(tmp_path / "rel.db", "--release", "latest", expect_ok=False)
    assert proc.returncode != 0
    assert "latest" in proc.stderr


def test_release_refuses_skipped_stages(tmp_path, monkeypatch):
    """A release must be able to say every declared stage ran."""
    broken = tmp_path / "manifest.json"
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["overrides"] = {
        k: (str((PACK / v).resolve()) if k != "build_forms.DCS_F2L"
            else str(tmp_path / "does-not-exist.tsv"))
        for k, v in data["overrides"].items()
    }
    broken.write_text(json.dumps(data), encoding="utf-8")
    cmd = [sys.executable, str(BUILD), "--sources", str(broken),
           "--db", str(tmp_path / "rel2.db"),
           "--allow-missing-sources", "--release", "0.0.1-test"]
    env = dict(os.environ) | {"PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          env=env, cwd=str(ROOT))
    assert proc.returncode != 0
    assert "skipped" in proc.stderr


def test_missing_source_aborts_by_default(tmp_path):
    broken = tmp_path / "manifest.json"
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["overrides"] = {
        k: (str((PACK / v).resolve()) if k != "build_db.UNION_HEADWORDS"
            else str(tmp_path / "gone.tsv"))
        for k, v in data["overrides"].items()
    }
    broken.write_text(json.dumps(data), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(BUILD), "--sources", str(broken),
         "--db", str(tmp_path / "x.db")],
        capture_output=True, text=True, encoding="utf-8",
        env=dict(os.environ) | {"PYTHONIOENCODING": "utf-8"}, cwd=str(ROOT))
    assert proc.returncode != 0
    assert "missing source" in proc.stderr
    assert not (tmp_path / "x.db").exists(), (
        "a refused build must not leave a partial artifact behind")


def test_partial_build_refuses_unverifiable_prerequisites(tmp_path):
    """`--stage forms` on a database with no lock cannot know lemmas ever ran."""
    proc = run_build(tmp_path / "partial.db", "--stage", "forms", expect_ok=False)
    assert proc.returncode != 0
    assert "prerequisite" in proc.stderr.lower()


def _build_with(manifest: Path, target: Path, *extra: str):
    cmd = [sys.executable, str(BUILD), "--sources", str(manifest),
           "--db", str(target), *extra]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          env=dict(os.environ) | {"PYTHONIOENCODING": "utf-8"},
                          cwd=str(ROOT))


def test_partial_build_detects_a_changed_prerequisite_feed(tmp_path):
    """Rebuild one stage after its prerequisite's feed changed underneath it.

    Built against a *copy* of the pack so the feed can be edited: this is the
    real-world shape — the sibling feed is refreshed, and a later `--stage x`
    would otherwise sit on lemmas derived from the older bytes.
    """
    import shutil

    pack = tmp_path / "pack"
    shutil.copytree(PACK, pack)
    manifest = pack / "sources.json"
    target = tmp_path / "copy" / "kosha.db"
    target.parent.mkdir(parents=True)

    first = _build_with(manifest, target)
    assert first.returncode == 0, first.stdout + first.stderr

    feed = pack / "union_headwords.tsv"
    lines = feed.read_text(encoding="utf-8").splitlines()
    feed.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    proc = _build_with(manifest, target, "--stage", "evidence")
    assert proc.returncode != 0, proc.stdout
    assert "stale" in proc.stderr.lower()
    assert "lemmas" in proc.stderr
    assert "source changed" in proc.stderr


def test_partial_build_detects_a_redirected_prerequisite_feed(built, tmp_path):
    """The digest check alone misses this one, so it is pinned separately.

    Redirect a prerequisite's feed at a *different* file and every recorded
    digest still matches — the old file is sitting there untouched. What
    changed is which file the stage would now read, which is exactly as stale.
    """
    import shutil

    target = tmp_path / "redirected" / "kosha.db"
    target.parent.mkdir(parents=True)
    shutil.copy2(built, target)
    shutil.copy2(built.with_name(built.stem + ".build-lock.json"),
                 target.with_name(target.stem + ".build-lock.json"))

    moved = tmp_path / "union_headwords.tsv"
    shutil.copy2(PACK / "union_headwords.tsv", moved)

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["overrides"] = {k: str((PACK / v).resolve())
                         for k, v in data["overrides"].items()}
    data["overrides"]["build_db.UNION_HEADWORDS"] = str(moved)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(data), encoding="utf-8")

    proc = _build_with(manifest, target, "--stage", "evidence")
    assert proc.returncode != 0, proc.stdout
    assert "stale" in proc.stderr.lower()
    assert "source set changed" in proc.stderr


def test_force_overrides_the_staleness_refusal(built, tmp_path):
    import shutil

    target = tmp_path / "forced" / "kosha.db"
    target.parent.mkdir(parents=True)
    shutil.copy2(built, target)
    shutil.copy2(built.with_name(built.stem + ".build-lock.json"),
                 target.with_name(target.stem + ".build-lock.json"))
    proc = run_build(target, "--stage", "evidence", "--force")
    assert proc.returncode == 0


def test_verify_reports_a_clean_build(built):
    proc = subprocess.run(
        [sys.executable, str(BUILD), "--verify", "--db", str(built)],
        capture_output=True, text=True, encoding="utf-8",
        env=dict(os.environ) | {"PYTHONIOENCODING": "utf-8"}, cwd=str(ROOT))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "artifact digest: matches the lock" in proc.stdout
    for name in DECLARED_STAGES:
        assert f"{name}: ok" in proc.stdout
