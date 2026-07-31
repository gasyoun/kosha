"""W0C — citation archive and resolution (H1945, item 7).

R1's promise is that a sense id minted today still resolves in a browser years
from now, against the release it names. Everything that promise rests on is
configuration — where the archive is mounted, whether its bytes are the
released bytes, and what host the citation URL points at — and before W0C none
of it was checked: a misconfigured mount and an unarchived version gave the
identical answer, "not archived on this instance".

These tests cover the validator that closed that gap
(`kosha.api.archive`), the settings contradiction it uncovered, and the two
resolution paths — current build and historical release — end to end.
"""

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from kosha.api.archive import (  # noqa: E402
    DUMP_NAME,
    METADATA_NAME,
    mounted_versions,
    validate_archive,
    validate_public_base,
    validate_release_asset,
    validate_version,
)
from kosha.cite import cite_object, release_asset_url  # noqa: E402
from kosha.settings import Settings, SettingsError  # noqa: E402

ARCHIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS archive (
    sense_id TEXT PRIMARY KEY,
    dict TEXT NOT NULL, L TEXT NOT NULL, sense_n INTEGER NOT NULL,
    headword TEXT, text_raw TEXT NOT NULL
);
"""


def _write_archive(root: Path, version: str, senses, metadata=True) -> Path:
    directory = root / version
    directory.mkdir(parents=True, exist_ok=True)
    dump = directory / DUMP_NAME
    con = sqlite3.connect(dump)
    try:
        con.executescript(ARCHIVE_SCHEMA)
        con.executemany(
            "INSERT OR REPLACE INTO archive "
            "(sense_id, dict, L, sense_n, headword, text_raw) "
            "VALUES (:sense_id, :dict, :L, :sense_n, :headword, :text_raw)",
            list(senses),
        )
        con.commit()
    finally:
        con.close()
    if metadata:
        (directory / METADATA_NAME).write_text(
            json.dumps({
                "version": version,
                "sha256": hashlib.sha256(dump.read_bytes()).hexdigest(),
                "senses": len(list(senses)),
            }),
            encoding="utf-8",
        )
    return dump


SENSE = {
    "sense_id": "mw.101.1", "dict": "mw", "L": "101", "sense_n": 1,
    "headword": "agni", "text_raw": "<H1>fire</H1>",
}


def _settings(tmp_path: Path, **overrides) -> Settings:
    base = dict(
        core_db=tmp_path / "core.db",
        inflections_db=tmp_path / "infl.db",
        layers_db=tmp_path / "layers.db",
        history_db=tmp_path / "history.db",
        archive_dir=tmp_path / "releases",
        public_base="https://gasyoun.github.io/kosha",
    )
    base.update(overrides)
    return Settings(**base)


# --------------------------------------------------------------------------- #
# The configuration contradiction W0C removed
# --------------------------------------------------------------------------- #

def test_archive_dir_defaults_to_the_directory_the_mechanism_reads():
    """W0B gave `archive_dir` the default `data/archive` while
    `app/versions.py` went on reading `KOSHA_RELEASES_DIR`, default
    `data/releases`. Two settings, one directory, two different defaults —
    so pointing the documented knob at a mounted release archive moved
    nothing and every citation kept resolving against the old path."""
    settings = Settings.from_env(env={}, root=Path("/repo"))
    assert settings.archive_dir.name == "releases"


def test_the_deprecated_name_still_works():
    settings = Settings.from_env(
        env={"KOSHA_RELEASES_DIR": "/mnt/archive"}, root=Path("/repo")
    )
    assert settings.archive_dir == Path("/mnt/archive")


def test_contradicting_archive_names_are_a_hard_error():
    """Same contract as `DATABASE_PATH`: a conflict is refused rather than
    silently resolved. A deployment mounting release assets at one path and
    resolving citations from another answers "not archived" for citations it is
    in fact serving, and nothing says why."""
    with pytest.raises(SettingsError, match="conflicting citation-archive"):
        Settings.from_env(
            env={"KOSHA_ARCHIVE_DIR": "/mnt/a", "KOSHA_RELEASES_DIR": "/mnt/b"},
            root=Path("/repo"),
        )


def test_agreeing_archive_names_are_accepted():
    settings = Settings.from_env(
        env={"KOSHA_ARCHIVE_DIR": "/mnt/a", "KOSHA_RELEASES_DIR": "/mnt/a"},
        root=Path("/repo"),
    )
    assert settings.archive_dir == Path("/mnt/a")


def test_versions_module_reads_the_unified_setting(tmp_path, monkeypatch):
    """The knob has to move the mechanism, not just the settings object."""
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path))
    import versions

    assert versions.releases_dir() == tmp_path


# --------------------------------------------------------------------------- #
# Public base (R1/R5)
# --------------------------------------------------------------------------- #

def test_public_base_must_be_absolute():
    assert not validate_public_base("/api").ok
    assert not validate_public_base("localhost:8000").ok
    assert validate_public_base("https://gasyoun.github.io/kosha").ok


@pytest.mark.parametrize("base", ["https://samskrtam.ru",
                                  "https://www.samskrtam.ru/kosha",
                                  "http://samskrtam.ru:8080"])
def test_public_base_may_not_be_the_deployment_host(base):
    """R5 — citations must resolve independently of where the live server
    runs. The rule was a comment in three files; it is a check now."""
    check = validate_public_base(base)
    assert not check.ok
    assert "R5" in check.detail or "deployment host" in check.detail


# --------------------------------------------------------------------------- #
# Release metadata, checksums, asset URLs
# --------------------------------------------------------------------------- #

def test_release_asset_url_is_durable_for_a_citable_version():
    check = validate_release_asset("1.2.0")
    assert check.ok
    assert release_asset_url("1.2.0").startswith("https://github.com/gasyoun/kosha/releases/download/")


def test_dev_builds_mint_no_asset_url():
    """A `-dev` build ships no release; advertising a download for it would
    promise a file that will never exist."""
    assert release_asset_url("0.0.0-dev") is None
    assert validate_release_asset("0.0.0-dev").ok


def test_a_healthy_archive_validates(tmp_path):
    _write_archive(tmp_path / "releases", "1.2.0", [SENSE])
    report = validate_archive(_settings(tmp_path))
    assert report.ok, report.failures()
    assert report.versions == ["1.2.0"]


def test_a_tampered_dump_fails_its_checksum(tmp_path):
    """The check that distinguishes "the released bytes" from "some bytes"."""
    dump = _write_archive(tmp_path / "releases", "1.2.0", [SENSE])
    con = sqlite3.connect(dump)
    try:
        con.execute(
            "INSERT INTO archive VALUES ('mw.999.1','mw','999',1,'x','<H1>x</H1>')"
        )
        con.commit()
    finally:
        con.close()
    report = validate_archive(_settings(tmp_path))
    assert not report.ok
    assert any("checksum" in check.name for check in report.failures())


def test_metadata_naming_the_wrong_version_fails(tmp_path):
    root = tmp_path / "releases"
    dump = _write_archive(root, "1.2.0", [SENSE])
    (root / "1.2.0" / METADATA_NAME).write_text(
        json.dumps({"version": "9.9.9",
                    "sha256": hashlib.sha256(dump.read_bytes()).hexdigest()}),
        encoding="utf-8",
    )
    report = validate_archive(_settings(tmp_path))
    assert not report.ok


def test_missing_metadata_is_unverified_not_failed(tmp_path):
    """Most local archives never had a `release.json`; treating that as
    corruption would make the validator useless in development."""
    _write_archive(tmp_path / "releases", "1.2.0", [SENSE], metadata=False)
    report = validate_archive(_settings(tmp_path))
    assert report.ok
    assert any("unverified" in check.detail for check in report.checks)


def test_a_truncated_dump_is_caught(tmp_path):
    """`is_file()` passes for a corrupt file; every citation reaching it fails."""
    root = tmp_path / "releases" / "1.2.0"
    root.mkdir(parents=True)
    (root / DUMP_NAME).write_bytes(b"not a database")
    report = validate_archive(_settings(tmp_path))
    assert not report.ok
    assert any("readable" in check.name for check in report.failures())


def test_an_empty_archive_dir_is_reported_not_failed(tmp_path):
    report = validate_archive(_settings(tmp_path))
    assert report.ok
    assert report.versions == []


def test_mounted_versions_ignores_stray_directories(tmp_path):
    root = tmp_path / "releases"
    _write_archive(root, "1.2.0", [SENSE])
    (root / "scratch").mkdir()
    assert mounted_versions(root) == ["1.2.0"]


def test_validate_version_reports_a_missing_dump(tmp_path):
    (tmp_path / "1.2.0").mkdir(parents=True)
    checks = validate_version(tmp_path, "1.2.0")
    assert not all(check.ok for check in checks)


# --------------------------------------------------------------------------- #
# Resolution — current build and historical release
# --------------------------------------------------------------------------- #

def test_current_version_resolves_against_the_live_db(fixture_client, fixture_lemma):
    """The current-citation smoke: mint an id from a lemma card, resolve it."""
    body = fixture_client.get(
        f"/api/v1/lemma/{fixture_lemma}", params={"in": "slp1"}
    ).json()
    sense_ids = [sid for e in body["results"] for sid in e["kosha"]["sense_ids"]]
    assert sense_ids, "fixture entry has no senses to cite"

    response = fixture_client.get(f"/api/v1/sense/{sense_ids[0]}")
    assert response.status_code == 200, response.text
    result = response.json()["results"][0]
    assert result["resolved_from"] == "live"
    assert result["sense_id"] == sense_ids[0]
    assert result["cite"]["resolution_url"].endswith(f"/api/v1/sense/{sense_ids[0]}")


def test_historical_version_resolves_against_the_mounted_archive(
    fixture_client, tmp_path, monkeypatch
):
    """The R1 path that matters: an id naming an *older* release must resolve
    to that release's text, not to today's rebuild."""
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path))
    _write_archive(tmp_path, "0.0.1", [{
        "sense_id": "mw.101.1", "dict": "mw", "L": "101", "sense_n": 1,
        "headword": "agni", "text_raw": "<H1>the archived wording</H1>",
    }])

    response = fixture_client.get("/api/v1/sense/mw.101.1@0.0.1")
    assert response.status_code == 200, response.text
    result = response.json()["results"][0]
    assert result["resolved_from"] == "archive"
    assert "archived wording" in result["text_raw"]
    assert "archived wording" in result["text_rendered"]


def test_an_unarchived_version_says_so_and_points_at_the_release_asset(
    fixture_client, tmp_path, monkeypatch
):
    """The honest miss: not a 500, and it names where the bytes can be had."""
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path))
    response = fixture_client.get("/api/v1/sense/mw.101.1@9.9.9")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "version_not_archived"
    assert any("releases/download" in s for s in error["suggestions"])


def test_archived_sense_html_is_sanitized_too(fixture_client, tmp_path, monkeypatch):
    """The archive is a second source of rendered HTML, and it must cross the
    same boundary — an archived body predates the sanitizer entirely."""
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path))
    _write_archive(tmp_path, "0.0.2", [{
        "sense_id": "mw.101.1", "dict": "mw", "L": "101", "sense_n": 1,
        "headword": "agni",
        "text_raw": "<H1>fire<script>alert(1)</script></H1>",
    }])
    result = fixture_client.get("/api/v1/sense/mw.101.1@0.0.2").json()["results"][0]
    assert "<script" not in result["text_rendered"].lower()
    assert "alert(1)" not in result["text_rendered"]
    # …while the raw archived bytes stay untouched, as stored.
    assert "<script>" in result["text_raw"]


def test_cite_object_pins_the_version_everywhere():
    cite = cite_object("mw", "101", 1, "1.2.0", "https://example.org", "agni")
    assert cite["text"] == "mw.101.1@1.2.0"
    assert cite["resolution_url"].endswith("/api/v1/sense/mw.101.1@1.2.0")
    assert "1.2.0" in cite["bibtex"]
    assert cite["csl_json"]["version"] == "1.2.0"
    assert cite["release_asset"].endswith("data-1.2.0/senses.sqlite")
