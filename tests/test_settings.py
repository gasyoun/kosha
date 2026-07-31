"""W0B (H1944) — typed settings, and the `DATABASE_PATH` alias contract.

`.env.example` advertised `DATABASE_PATH` from the start while `app/db.py`
hardcoded its own path and never read it: setting it silently did nothing.
Rather than delete the name (which would break anyone's existing `.env`), it is
kept as a deprecated alias that now actually works — and a *disagreeing* pair is
a hard error instead of a coin flip over which one wins.
"""
import os
import warnings
from pathlib import Path

import pytest

from kosha.settings import KoshaSettings, SettingsConflict, reload_settings, repo_root

pytestmark = pytest.mark.fixture

ENV_VARS = [
    "KOSHA_CORE_DB", "KOSHA_INFLECTIONS_DB", "KOSHA_LAYERS_DB",
    "KOSHA_ARCHIVE_DIR", "KOSHA_RELEASES_DIR", "KOSHA_HISTORY_DB",
    "HISTORY_DB_PATH", "DATABASE_PATH", "KOSHA_ENABLE_HISTORY",
    "KOSHA_PUBLIC_BASE",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    yield
    # Clear again on the way out: monkeypatch's own undo runs *after* this
    # finalizer, so anything a test set is still present here — and a
    # deliberately invalid value (see the boolean test) would make the reload
    # below raise during teardown.
    for name in ENV_VARS:
        os.environ.pop(name, None)


@pytest.fixture(scope="module", autouse=True)
def restore_process_settings():
    """Leave the cached process settings consistent with the real environment
    once monkeypatch has finished undoing everything for this module."""
    yield
    reload_settings()


def test_defaults_are_repo_relative():
    s = KoshaSettings.from_env()
    root = repo_root()
    assert s.core_db == root / "data" / "db" / "kosha.db"
    assert s.archive_dir == root / "data" / "releases"
    assert s.history_db == root / "data" / "db" / "kosha_history.db"
    assert s.enable_history is False


def test_inflections_and_layers_default_to_core(monkeypatch, tmp_path):
    monkeypatch.setenv("KOSHA_CORE_DB", str(tmp_path / "core.db"))
    s = KoshaSettings.from_env()
    assert s.inflections_db == s.core_db == tmp_path / "core.db"
    assert s.layers_db == s.core_db


def test_roles_can_be_split(monkeypatch, tmp_path):
    monkeypatch.setenv("KOSHA_CORE_DB", str(tmp_path / "core.db"))
    monkeypatch.setenv("KOSHA_INFLECTIONS_DB", str(tmp_path / "infl.db"))
    monkeypatch.setenv("KOSHA_LAYERS_DB", str(tmp_path / "layers.db"))
    s = KoshaSettings.from_env()
    assert s.inflections_db == tmp_path / "infl.db"
    assert s.layers_db == tmp_path / "layers.db"
    assert s.core_db == tmp_path / "core.db"


def test_relative_paths_resolve_against_repo_root(monkeypatch):
    monkeypatch.setenv("KOSHA_CORE_DB", "data/db/other.db")
    assert KoshaSettings.from_env().core_db == repo_root() / "data" / "db" / "other.db"


# --- the DATABASE_PATH alias -------------------------------------------------

def test_database_path_alias_takes_effect(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "legacy.db"))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        s = KoshaSettings.from_env()
    assert s.core_db == tmp_path / "legacy.db"
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert any("KOSHA_CORE_DB" in str(w.message) for w in caught)


def test_conflicting_alias_and_canonical_fails(monkeypatch, tmp_path):
    monkeypatch.setenv("KOSHA_CORE_DB", str(tmp_path / "a.db"))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "b.db"))
    with pytest.raises(SettingsConflict) as exc:
        KoshaSettings.from_env()
    assert "KOSHA_CORE_DB" in str(exc.value)
    assert "DATABASE_PATH" in str(exc.value)


def test_agreeing_alias_and_canonical_is_fine(monkeypatch, tmp_path):
    same = str(tmp_path / "same.db")
    monkeypatch.setenv("KOSHA_CORE_DB", same)
    monkeypatch.setenv("DATABASE_PATH", same)
    assert KoshaSettings.from_env().core_db == Path(same)


def test_canonical_wins_without_warning(monkeypatch, tmp_path, recwarn):
    monkeypatch.setenv("KOSHA_CORE_DB", str(tmp_path / "a.db"))
    s = KoshaSettings.from_env()
    assert s.core_db == tmp_path / "a.db"
    assert not [w for w in recwarn if issubclass(w.category, DeprecationWarning)]


@pytest.mark.parametrize("canonical,alias", [
    ("KOSHA_ARCHIVE_DIR", "KOSHA_RELEASES_DIR"),
    ("KOSHA_HISTORY_DB", "HISTORY_DB_PATH"),
])
def test_other_aliases_also_conflict_loudly(monkeypatch, tmp_path, canonical, alias):
    monkeypatch.setenv(canonical, str(tmp_path / "a"))
    monkeypatch.setenv(alias, str(tmp_path / "b"))
    with pytest.raises(SettingsConflict):
        KoshaSettings.from_env()


def test_releases_dir_alias_still_honoured(monkeypatch, tmp_path):
    monkeypatch.setenv("KOSHA_RELEASES_DIR", str(tmp_path / "rel"))
    assert KoshaSettings.from_env().archive_dir == tmp_path / "rel"


# --- flags and validation ----------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("1", True), ("true", True), ("YES", True), ("on", True),
    ("0", False), ("false", False), ("no", False), ("OFF", False),
])
def test_enable_history_parses_booleans(monkeypatch, raw, expected):
    monkeypatch.setenv("KOSHA_ENABLE_HISTORY", raw)
    assert KoshaSettings.from_env().enable_history is expected


def test_enable_history_rejects_nonsense(monkeypatch):
    monkeypatch.setenv("KOSHA_ENABLE_HISTORY", "maybe")
    with pytest.raises(SettingsConflict):
        KoshaSettings.from_env()


def test_public_base_trailing_slash_stripped(monkeypatch):
    monkeypatch.setenv("KOSHA_PUBLIC_BASE", "https://example.org/")
    assert KoshaSettings.from_env().public_base == "https://example.org"


def test_settings_are_frozen():
    s = KoshaSettings.from_env()
    with pytest.raises(Exception):
        s.core_db = Path("/tmp/nope")
