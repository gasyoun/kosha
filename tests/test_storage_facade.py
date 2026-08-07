"""W1A multi-DB storage facade (H2341).

Proves:

1. Monolith golden samples still run through the facade.
2. Split core/inflections/layers attach layout matches monolith results.
3. History is never mounted on the query path (even when history.db exists).
4. Salt entry payloads do not leak physical placement.
5. Settings still reject conflicting DATABASE_PATH / KOSHA_CORE_DB_PATH.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app", ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from kosha.api import repository, serializer  # noqa: E402
from kosha.api.models import SaltEntry  # noqa: E402
from kosha.query.connection import (  # noqa: E402
    HISTORY_ALIAS,
    STABLE_ALIASES,
    assert_no_placement_leak,
    attached_aliases,
    open_query_connection,
)
from kosha.query.samples import GOLDEN_SAMPLE_QUERIES, run_sample_queries  # noqa: E402
from kosha.query.split import split_monolith_to_facade  # noqa: E402
from kosha.settings import Settings  # noqa: E402

FIXTURE_DB = ROOT / "data" / "db" / "kosha_fixture.db"


def _require_fixture():
    if not FIXTURE_DB.is_file():
        pytest.skip(
            "fixture DB absent — build with "
            "`python scripts/build_db.py --profile fixture`"
        )
    return FIXTURE_DB


@pytest.fixture()
def monolith_path():
    return _require_fixture()


@pytest.fixture()
def split_pack(monolith_path, tmp_path):
    core = tmp_path / "core.db"
    inf = tmp_path / "inflections.db"
    layers = tmp_path / "layers.db"
    copied = split_monolith_to_facade(
        monolith_path,
        core_out=core,
        inflections_out=inf,
        layers_out=layers,
    )
    assert "meta" in copied["core"] or "entries" in copied["core"]
    return {"core": core, "inflections": inf, "layers": layers, "copied": copied}


def test_stable_aliases_are_documented():
    assert STABLE_ALIASES == ("core", "inflections", "layers")
    assert HISTORY_ALIAS == "history"


def test_monolith_facade_opens_core_only(monolith_path):
    con = open_query_connection(core_path=monolith_path)
    try:
        aliases = attached_aliases(con)
        assert "core" in aliases
        assert HISTORY_ALIAS not in aliases
        # No separate files → no inflections/layers attach
        assert "inflections" not in aliases
        assert "layers" not in aliases
        assert repository.data_version(con)
    finally:
        con.close()


def test_split_attaches_inflections_and_layers(split_pack):
    con = open_query_connection(
        core_path=split_pack["core"],
        inflections_path=split_pack["inflections"],
        layers_path=split_pack["layers"],
    )
    try:
        aliases = attached_aliases(con)
        assert "core" in aliases
        # Attach only when the file actually holds expected tables
        if split_pack["copied"]["inflections"]:
            assert "inflections" in aliases
            n = con.execute("SELECT COUNT(*) FROM inflections").fetchone()[0]
            assert n >= 0
        if split_pack["copied"]["layers"]:
            assert "layers" in aliases
        assert HISTORY_ALIAS not in aliases
        # PRAGMA database_list names never include history
        names = {row[1] for row in con.execute("PRAGMA database_list")}
        assert HISTORY_ALIAS not in names
    finally:
        con.close()


def test_history_file_is_never_attached(monolith_path, tmp_path):
    """Even a present history.db next to the core store stays unmounted."""
    history = tmp_path / "history.db"
    hcon = sqlite3.connect(str(history))
    hcon.executescript(
        "CREATE TABLE visitors (anon_id TEXT PRIMARY KEY);"
        "CREATE TABLE search_events (id INTEGER PRIMARY KEY);"
    )
    hcon.close()

    settings = Settings.from_env(
        {
            "KOSHA_CORE_DB_PATH": str(monolith_path),
            "HISTORY_DB_PATH": str(history),
            "KOSHA_HISTORY_ENABLED": "1",  # flag on — still must not attach here
        },
        root=ROOT,
    )
    con = open_query_connection(settings)
    try:
        aliases = attached_aliases(con)
        assert HISTORY_ALIAS not in aliases
        names = {row[1] for row in con.execute("PRAGMA database_list")}
        assert HISTORY_ALIAS not in names
        # Query path must not see history tables
        with pytest.raises(sqlite3.OperationalError):
            con.execute("SELECT 1 FROM visitors LIMIT 1")
    finally:
        con.close()


def test_monolith_vs_split_sample_parity(monolith_path, split_pack):
    """Frozen golden samples: multi-DB attach ≡ monolith results."""
    mono = open_query_connection(core_path=monolith_path)
    multi = open_query_connection(
        core_path=split_pack["core"],
        inflections_path=split_pack["inflections"],
        layers_path=split_pack["layers"],
    )
    try:
        left = run_sample_queries(mono)
        right = run_sample_queries(multi)
        assert set(left) == set(right) == {n for n, _ in GOLDEN_SAMPLE_QUERIES}
        for name in left:
            assert left[name] == right[name], f"parity miss on sample {name!r}"
        # History tables must stay invisible on both layouts
        assert left["history_tables_visible"] == []
        assert right["history_tables_visible"] == []
    finally:
        mono.close()
        multi.close()


def test_repository_entry_parity_and_no_placement_leak(monolith_path, split_pack):
    """Same headword → same Salt entries; payloads free of physical placement."""
    mono = open_query_connection(core_path=monolith_path)
    multi = open_query_connection(
        core_path=split_pack["core"],
        inflections_path=split_pack["inflections"],
        layers_path=split_pack["layers"],
    )
    try:
        row = mono.execute(
            "SELECT slp1_key, COUNT(DISTINCT dict) AS n FROM entries "
            "GROUP BY slp1_key ORDER BY n DESC, slp1_key LIMIT 1"
        ).fetchone()
        lemma = row["slp1_key"]
        dv_m = repository.data_version(mono)
        dv_s = repository.data_version(multi)
        assert dv_m == dv_s

        mono_entries = []
        multi_entries = []
        public_base = "http://localhost:8000"
        for con, bucket in ((mono, mono_entries), (multi, multi_entries)):
            for entry_row, hom in repository.entries_for_key_across_dicts(con, lemma):
                entry = serializer.serialize_entry(
                    con,
                    entry_row,
                    hom_count=hom,
                    data_version=dv_m,
                    public_base=public_base,
                    include_raw=False,
                )
                payload = entry.model_dump(mode="json")
                bucket.append(payload)
                SaltEntry.model_validate(payload)
                assert_no_placement_leak(payload)

        assert mono_entries == multi_entries
        assert mono_entries, "fixture pack must yield at least one entry"
    finally:
        mono.close()
        multi.close()


def test_sample_count_is_locked():
    """Regression lock: expanding/shrinking the golden list is intentional."""
    assert len(GOLDEN_SAMPLE_QUERIES) == 12


def test_conflicting_core_paths_still_fail(tmp_path):
    from kosha.settings import SettingsError

    with pytest.raises(SettingsError, match="conflicting core-DB"):
        Settings.from_env(
            {
                "KOSHA_CORE_DB_PATH": str(tmp_path / "a.db"),
                "DATABASE_PATH": str(tmp_path / "b.db"),
            }
        )
