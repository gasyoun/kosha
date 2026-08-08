"""W2A — immutable sense archives + historical-resolution (H2346).

Extends W0C citation-archive coverage:

1. ``write_archive`` always freezes a sha256 identity (``release.json``).
2. Release-gate validation fails on missing/tampered checksums and on a bad
   public base — not mere existence.
3. Historical resolution covers *two* committed release identities (prior +
   current) from ``tests/fixtures/archives/``, not only tmp_path scratch.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from kosha.api.archive import (  # noqa: E402
    METADATA_NAME,
    mounted_versions,
    resolve_archived_sense,
    validate_archive,
    validate_historical_resolution,
    validate_release_archives,
    validate_version,
)
from kosha.settings import Settings  # noqa: E402
import versions  # noqa: E402

FIXTURE_ARCHIVES = ROOT / "tests" / "fixtures" / "archives"
PRIOR = "0.1.0-w2a-prior"
CURRENT = "0.2.0-w2a-current"
SENSE_ID = "mw.101.1"


def _settings(archive_dir: Path, public_base: str = "https://gasyoun.github.io/kosha") -> Settings:
    return Settings(
        core_db=archive_dir.parent / "core.db",
        inflections_db=archive_dir.parent / "infl.db",
        layers_db=archive_dir.parent / "layers.db",
        history_db=archive_dir.parent / "history.db",
        archive_dir=archive_dir,
        public_base=public_base,
    )


# --------------------------------------------------------------------------- #
# write_archive freezes identity
# --------------------------------------------------------------------------- #


def test_write_archive_emits_matching_release_json(tmp_path, monkeypatch):
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path))
    path = versions.write_archive(CURRENT, [{
        "sense_id": SENSE_ID, "dict": "mw", "L": "101", "sense_n": 1,
        "headword": "agni", "text_raw": "<H1>fire</H1>",
    }])
    meta_path = path.parent / METADATA_NAME
    assert meta_path.is_file(), "W2A requires release.json beside every freeze"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["version"] == CURRENT
    assert meta["senses"] == 1
    assert meta["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_write_archive_checksum_fails_after_tamper(tmp_path, monkeypatch):
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path))
    path = versions.write_archive("1.0.0", [{
        "sense_id": SENSE_ID, "dict": "mw", "L": "101", "sense_n": 1,
        "headword": "agni", "text_raw": "<H1>fire</H1>",
    }])
    path.write_bytes(path.read_bytes() + b"\x00")
    checks = validate_version(tmp_path, "1.0.0", require_metadata=True)
    assert any(not c.ok and "checksum" in c.name for c in checks)


# --------------------------------------------------------------------------- #
# Release gate (strict metadata + public base + resolve)
# --------------------------------------------------------------------------- #


def test_release_gate_fails_without_metadata(tmp_path):
    """Existence alone is not enough for a citable release."""
    dump = tmp_path / "9.9.9" / "senses.sqlite"
    dump.parent.mkdir(parents=True)
    # Minimal openable archive without release.json
    import sqlite3

    con = sqlite3.connect(dump)
    con.executescript(
        "CREATE TABLE archive ("
        "sense_id TEXT PRIMARY KEY, dict TEXT, L TEXT, sense_n INTEGER,"
        "headword TEXT, text_raw TEXT NOT NULL);"
        "INSERT INTO archive VALUES "
        "('mw.1.1','mw','1',1,'x','<H1>x</H1>');"
    )
    con.commit()
    con.close()

    report = validate_archive(
        _settings(tmp_path), require_metadata=True, require_versions=True
    )
    assert not report.ok
    assert any("metadata" in c.name for c in report.failures())


def test_release_gate_fails_on_deployment_public_base(tmp_path, monkeypatch):
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path))
    versions.write_archive("1.0.0", [{
        "sense_id": SENSE_ID, "dict": "mw", "L": "101", "sense_n": 1,
        "headword": "agni", "text_raw": "<H1>fire</H1>",
    }])
    report = validate_release_archives(
        _settings(tmp_path, public_base="https://samskrtam.ru"),
        sense_id=SENSE_ID,
    )
    assert not report.ok
    assert any(c.name == "public_base" for c in report.failures())


def test_release_gate_passes_healthy_mount(tmp_path, monkeypatch):
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path))
    versions.write_archive("1.0.0", [{
        "sense_id": SENSE_ID, "dict": "mw", "L": "101", "sense_n": 1,
        "headword": "agni", "text_raw": "<H1>fire</H1>",
    }])
    report = validate_release_archives(
        _settings(tmp_path), sense_id=SENSE_ID, min_versions=1
    )
    assert report.ok, report.failures()


def test_release_gate_requires_min_versions(tmp_path, monkeypatch):
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path))
    versions.write_archive("1.0.0", [{
        "sense_id": SENSE_ID, "dict": "mw", "L": "101", "sense_n": 1,
        "headword": "agni", "text_raw": "<H1>fire</H1>",
    }])
    report = validate_release_archives(
        _settings(tmp_path), sense_id=SENSE_ID, min_versions=2
    )
    assert not report.ok
    assert any(c.name == "min_versions" for c in report.failures())


# --------------------------------------------------------------------------- #
# Committed mini-archive — prior + current identities
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def mini_archive():
    assert FIXTURE_ARCHIVES.is_dir(), "committed mini-archive missing"
    assert (FIXTURE_ARCHIVES / PRIOR / "senses.sqlite").is_file()
    assert (FIXTURE_ARCHIVES / CURRENT / "senses.sqlite").is_file()
    assert (FIXTURE_ARCHIVES / PRIOR / METADATA_NAME).is_file()
    assert (FIXTURE_ARCHIVES / CURRENT / METADATA_NAME).is_file()
    return FIXTURE_ARCHIVES


def test_committed_mini_archive_has_two_identities(mini_archive):
    versions = mounted_versions(mini_archive)
    assert PRIOR in versions
    assert CURRENT in versions
    report = validate_archive(
        _settings(mini_archive),
        require_metadata=True,
        require_versions=True,
    )
    assert report.ok, report.failures()


def test_historical_resolution_prior_and_current_diverge(mini_archive):
    """Same sense_id, two release identities, two wordings — R1 promise."""
    prior = resolve_archived_sense(mini_archive, PRIOR, SENSE_ID)
    current = resolve_archived_sense(mini_archive, CURRENT, SENSE_ID)
    assert prior is not None and current is not None
    assert "PRIOR" in prior["text_raw"]
    assert "CURRENT" in current["text_raw"]
    assert prior["text_raw"] != current["text_raw"]

    checks = validate_historical_resolution(
        mini_archive, sense_id=SENSE_ID, versions=[PRIOR, CURRENT]
    )
    assert all(c.ok for c in checks), checks


def test_release_gate_on_committed_mini_archive(mini_archive):
    report = validate_release_archives(
        _settings(mini_archive),
        sense_id=SENSE_ID,
        min_versions=2,
    )
    assert report.ok, report.failures()


def test_api_historical_resolution_against_committed_fixture(
    fixture_client, mini_archive, monkeypatch
):
    """End-to-end: API serves prior wording from the committed mount."""
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(mini_archive))
    prior = fixture_client.get(f"/api/v1/sense/{SENSE_ID}@{PRIOR}")
    assert prior.status_code == 200, prior.text
    body = prior.json()["results"][0]
    assert body["resolved_from"] == "archive"
    assert "PRIOR" in body["text_raw"]

    current = fixture_client.get(f"/api/v1/sense/{SENSE_ID}@{CURRENT}")
    assert current.status_code == 200, current.text
    body = current.json()["results"][0]
    assert "CURRENT" in body["text_raw"]
