"""W1C readiness checks (H2343).

Proves:

1. Healthy mini-core + empty archive → ready, history disabled.
2. Missing core → not ready (HTTP 503), not 500.
3. Expected data_version mismatch → not ready.
4. History flag off → status ``disabled`` (never looks ready while unmounted).
5. History flag on + missing history.db → fail.
6. Corrupt mounted citation archive → fail closed.
7. Thin `/ready` route maps report ready → 200 / 503.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from kosha.api.archive import DUMP_NAME, METADATA_NAME  # noqa: E402
from kosha.api.readiness import (  # noqa: E402
    assess_readiness,
    readiness_payload,
)
from kosha.settings import Settings  # noqa: E402

CORE_SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE lemmas (slp1 TEXT PRIMARY KEY);
CREATE TABLE entries (
    id INTEGER PRIMARY KEY, dict TEXT, L TEXT, slp1_key TEXT,
    k2 TEXT, pc_raw TEXT, vol TEXT, page TEXT, col TEXT, body TEXT
);
CREATE TABLE senses (
    id INTEGER PRIMARY KEY, entry_id INTEGER, sense_n INTEGER, text_raw TEXT
);
"""

ARCHIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS archive (
    sense_id TEXT PRIMARY KEY,
    dict TEXT NOT NULL, L TEXT NOT NULL, sense_n INTEGER NOT NULL,
    headword TEXT, text_raw TEXT NOT NULL
);
"""


def _settings(tmp_path: Path, **overrides) -> Settings:
    base = dict(
        core_db=tmp_path / "core.db",
        inflections_db=tmp_path / "infl.db",
        layers_db=tmp_path / "layers.db",
        history_db=tmp_path / "history.db",
        archive_dir=tmp_path / "releases",
        public_base="https://gasyoun.github.io/kosha",
        enable_history=False,
        expected_data_version=None,
    )
    base.update(overrides)
    return Settings(**base)


def _write_core(path: Path, *, version: str = "0.1.0-test") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    try:
        con.executescript(CORE_SCHEMA)
        con.execute(
            "INSERT INTO meta (key, value) VALUES ('data_version', ?)", (version,)
        )
        con.commit()
    finally:
        con.close()
    return path


def _write_archive(root: Path, version: str, *, corrupt_checksum: bool = False) -> Path:
    directory = root / version
    directory.mkdir(parents=True, exist_ok=True)
    dump = directory / DUMP_NAME
    con = sqlite3.connect(str(dump))
    try:
        con.executescript(ARCHIVE_SCHEMA)
        con.execute(
            "INSERT INTO archive (sense_id, dict, L, sense_n, headword, text_raw) "
            "VALUES ('mw.1.1', 'mw', '1', 1, 'agni', '<H1>fire</H1>')"
        )
        con.commit()
    finally:
        con.close()
    digest = hashlib.sha256(dump.read_bytes()).hexdigest()
    if corrupt_checksum:
        digest = "0" * 64
    (directory / METADATA_NAME).write_text(
        json.dumps({"version": version, "sha256": digest, "senses": 1}),
        encoding="utf-8",
    )
    return dump


def _by_name(report, name: str):
    for check in report.checks:
        if check.name == name:
            return check
    raise AssertionError(f"no check named {name!r}: {[c.name for c in report.checks]}")


# --------------------------------------------------------------------------- #
# Unit: assess_readiness
# --------------------------------------------------------------------------- #


def test_healthy_core_is_ready(tmp_path):
    _write_core(tmp_path / "core.db")
    report = assess_readiness(_settings(tmp_path))
    assert report.ready is True
    assert report.http_status() == 200
    assert report.data_version == "0.1.0-test"
    assert _by_name(report, "core_db").status == "ok"
    assert _by_name(report, "history").status == "disabled"
    assert _by_name(report, "citation_archives").status == "unconfigured"
    assert _by_name(report, "inflections_db").status == "absent"
    assert _by_name(report, "layers_db").status == "absent"
    # History must never look ready while unmounted.
    assert _by_name(report, "history").status != "ok"


def test_missing_core_is_not_ready(tmp_path):
    report = assess_readiness(_settings(tmp_path))
    assert report.ready is False
    assert report.http_status() == 503
    assert _by_name(report, "core_db").status == "fail"
    assert _by_name(report, "history").status == "disabled"


def test_version_mismatch_fails_closed(tmp_path):
    _write_core(tmp_path / "core.db", version="0.1.0-test")
    settings = _settings(tmp_path, expected_data_version="9.9.9")
    report = assess_readiness(settings)
    assert report.ready is False
    assert report.http_status() == 503
    assert _by_name(report, "data_version_match").status == "fail"


def test_version_match_when_expected_set(tmp_path):
    _write_core(tmp_path / "core.db", version="0.1.0-test")
    settings = _settings(tmp_path, expected_data_version="0.1.0-test")
    report = assess_readiness(settings)
    assert report.ready is True
    assert _by_name(report, "data_version_match").status == "ok"


def test_history_enabled_without_file_fails(tmp_path):
    _write_core(tmp_path / "core.db")
    settings = _settings(tmp_path, enable_history=True)
    report = assess_readiness(settings)
    assert report.ready is False
    assert _by_name(report, "history").status == "fail"


def test_history_enabled_with_file_ok(tmp_path):
    _write_core(tmp_path / "core.db")
    history = tmp_path / "history.db"
    hcon = sqlite3.connect(str(history))
    hcon.execute("CREATE TABLE visitors (id INTEGER PRIMARY KEY)")
    hcon.commit()
    hcon.close()
    settings = _settings(tmp_path, enable_history=True, history_db=history)
    report = assess_readiness(settings)
    assert report.ready is True
    assert _by_name(report, "history").status == "ok"


def test_corrupt_archive_fails_closed(tmp_path):
    _write_core(tmp_path / "core.db")
    archive_dir = tmp_path / "releases"
    _write_archive(archive_dir, "1.0.0", corrupt_checksum=True)
    settings = _settings(tmp_path, archive_dir=archive_dir)
    report = assess_readiness(settings)
    assert report.ready is False
    assert _by_name(report, "citation_archives").status == "fail"


def test_healthy_archive_is_ok(tmp_path):
    _write_core(tmp_path / "core.db")
    archive_dir = tmp_path / "releases"
    _write_archive(archive_dir, "1.0.0")
    settings = _settings(tmp_path, archive_dir=archive_dir)
    report = assess_readiness(settings)
    assert report.ready is True
    assert _by_name(report, "citation_archives").status == "ok"


def test_payload_shape_has_no_placement_keys(tmp_path):
    _write_core(tmp_path / "core.db")
    body, status = readiness_payload(_settings(tmp_path))
    assert status == 200
    assert set(body) >= {"ready", "status", "data_version", "checks"}
    text = json.dumps(body)
    for banned in ("kosha.db", "ATTACH ", "KOSHA_CORE_DB", "database_list"):
        assert banned not in text


# --------------------------------------------------------------------------- #
# HTTP route
# --------------------------------------------------------------------------- #


def test_ready_route_200_on_healthy_store(tmp_path, monkeypatch):
    core = tmp_path / "core.db"
    _write_core(core)
    monkeypatch.setenv("KOSHA_CORE_DB_PATH", str(core))
    monkeypatch.setenv("KOSHA_HISTORY_ENABLED", "0")
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path / "releases"))
    monkeypatch.delenv("KOSHA_EXPECTED_DATA_VERSION", raising=False)

    from kosha import settings as settings_mod

    settings_mod._cached = None
    # Force refresh so the route reads the patched env.
    from kosha.settings import get_settings

    get_settings(refresh=True)

    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["status"] == "ready"
    history = next(c for c in body["checks"] if c["name"] == "history")
    assert history["status"] == "disabled"


def test_ready_route_503_on_missing_core(tmp_path, monkeypatch):
    missing = tmp_path / "no-such-core.db"
    monkeypatch.setenv("KOSHA_CORE_DB_PATH", str(missing))
    monkeypatch.setenv("KOSHA_HISTORY_ENABLED", "0")
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path / "releases"))

    from kosha.settings import get_settings

    get_settings(refresh=True)

    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["ready"] is False
    assert body["status"] == "not_ready"
    core = next(c for c in body["checks"] if c["name"] == "core_db")
    assert core["status"] == "fail"


def test_health_stays_liveness_only(tmp_path, monkeypatch):
    """`/health` must not start failing when dependencies are down."""
    missing = tmp_path / "no-such-core.db"
    monkeypatch.setenv("KOSHA_CORE_DB_PATH", str(missing))
    from kosha.settings import get_settings

    get_settings(refresh=True)
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/health").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}
