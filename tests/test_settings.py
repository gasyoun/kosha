"""Typed settings and the deprecated `DATABASE_PATH` alias (H1944, W0B item 2)."""

import warnings

import pytest

from kosha.settings import Settings, SettingsError


def test_defaults_land_inside_the_repo():
    settings = Settings.from_env({})
    assert settings.core_db.name == "kosha.db"
    assert settings.core_db.parent.name == "db"
    assert settings.inflections_db.name == "kosha_inflections.db"
    assert settings.layers_db.name == "kosha_layers.db"
    assert settings.archive_dir.name == "archive"
    assert settings.public_base == "http://localhost:8000"


def test_history_is_off_unless_explicitly_enabled():
    """D10 — the public-v1 default, asserted rather than assumed."""
    assert Settings.from_env({}).enable_history is False
    assert Settings.from_env({"KOSHA_HISTORY_ENABLED": "false"}).enable_history is False
    assert Settings.from_env({"KOSHA_HISTORY_ENABLED": "0"}).enable_history is False
    assert Settings.from_env({"KOSHA_HISTORY_ENABLED": "1"}).enable_history is True
    assert Settings.from_env({"KOSHA_HISTORY_ENABLED": "TRUE"}).enable_history is True


def test_unparseable_flag_is_an_error_not_a_silent_false():
    with pytest.raises(SettingsError, match="not a boolean"):
        Settings.from_env({"KOSHA_HISTORY_ENABLED": "maybe"})


def test_deprecated_alias_still_selects_the_core_db(tmp_path):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        settings = Settings.from_env({"DATABASE_PATH": str(tmp_path / "legacy.db")})
    assert settings.core_db == tmp_path / "legacy.db"
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


def test_conflicting_alias_and_typed_name_fail_loudly(tmp_path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        with pytest.raises(SettingsError, match="conflicting core-DB configuration"):
            Settings.from_env({
                "KOSHA_CORE_DB_PATH": str(tmp_path / "a.db"),
                "DATABASE_PATH": str(tmp_path / "b.db"),
            })


def test_agreeing_alias_and_typed_name_are_accepted(tmp_path):
    same = str(tmp_path / "same.db")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        settings = Settings.from_env({"KOSHA_CORE_DB_PATH": same, "DATABASE_PATH": same})
    assert settings.core_db == tmp_path / "same.db"


def test_relative_paths_resolve_against_the_repo_root(tmp_path):
    settings = Settings.from_env({"KOSHA_CORE_DB_PATH": "data/db/other.db"}, root=tmp_path)
    assert settings.core_db == tmp_path / "data" / "db" / "other.db"


def test_public_base_loses_its_trailing_slash():
    """Citation URLs are built by concatenation; a trailing slash doubles it."""
    settings = Settings.from_env({"KOSHA_PUBLIC_BASE": "https://example.org/"})
    assert settings.public_base == "https://example.org"


def test_settings_are_frozen():
    settings = Settings.from_env({})
    with pytest.raises(Exception):
        settings.enable_history = True
