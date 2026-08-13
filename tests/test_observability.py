"""W2C release observability (H2348).

Proves:

1. Every response carries ``X-Request-ID`` (minted UUID or echoed token).
2. Incoming ``X-Request-ID`` / ``X-Correlation-ID`` is accepted when safe.
3. Unsafe / short tokens are rejected and replaced.
4. Structured logs carry ``request_id=`` and the route *template*, never
   the raw headword path.
5. ``GET /metrics`` is Prometheus text with the locked low-cardinality
   name list; headwords and forbidden label keys never appear.
6. Readiness failure gauges use H2343 check names; ``/ready`` 503
   increments ``kosha_ready_failures_total``; ``/metrics`` scrapes do not.
7. History/auth stay off — ``/api/v1/history`` is a real 404; ready
   reports history ``disabled``.
"""

from __future__ import annotations

import logging
import re
import sqlite3
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from kosha.api.observability import (  # noqa: E402
    ALLOWED_LABEL_KEYS,
    FORBIDDEN_LABEL_KEYS,
    METRIC_NAMES,
    LabelError,
    REGISTRY,
    record_http_request,
    reset_metrics,
    resolve_request_id,
)
from kosha.settings import get_settings  # noqa: E402

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

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.I,
)
UNIQUE_HEADWORD = "SomeVeryUniqueHeadwordXYZ"


def _write_core(path: Path, *, version: str = "0.1.0-w2c") -> Path:
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


def _client(tmp_path: Path, monkeypatch, *, missing_core: bool = False) -> TestClient:
    core = tmp_path / "core.db"
    if missing_core:
        monkeypatch.setenv("KOSHA_CORE_DB_PATH", str(tmp_path / "no-such-core.db"))
    else:
        _write_core(core)
        monkeypatch.setenv("KOSHA_CORE_DB_PATH", str(core))
    monkeypatch.setenv("KOSHA_HISTORY_ENABLED", "0")
    monkeypatch.setenv("KOSHA_ARCHIVE_DIR", str(tmp_path / "releases"))
    monkeypatch.delenv("KOSHA_EXPECTED_DATA_VERSION", raising=False)
    get_settings(refresh=True)
    reset_metrics()
    from app.main import app

    return TestClient(app, raise_server_exceptions=False)


def test_health_mints_uuid_request_id(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    rid = response.headers.get("X-Request-ID")
    assert rid, "X-Request-ID missing"
    assert UUID_RE.match(rid)


def test_incoming_request_id_is_echoed(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/health", headers={"X-Request-ID": "corr-test-01"})
    assert response.headers.get("X-Request-ID") == "corr-test-01"


def test_incoming_correlation_id_is_accepted(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/ready", headers={"X-Correlation-ID": "trace-token-99"})
    assert response.headers.get("X-Request-ID") == "trace-token-99"


def test_unsafe_incoming_token_is_replaced(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/health", headers={"X-Request-ID": "bad token"})
    rid = response.headers.get("X-Request-ID")
    assert rid != "bad token"
    assert UUID_RE.match(rid)


def test_short_incoming_token_is_replaced():
    scope = {
        "type": "http",
        "headers": [(b"x-request-id", b"short")],
    }
    minted = resolve_request_id(scope)
    assert minted != "short"
    uuid.UUID(minted)


def test_request_id_in_structured_logs(tmp_path, monkeypatch, caplog):
    client = _client(tmp_path, monkeypatch)
    caplog.set_level(logging.INFO, logger="kosha.api")
    client.get("/health", headers={"X-Request-ID": "corr-test-01"})
    assert "request_id=corr-test-01" in caplog.text
    assert "route=/health" in caplog.text


def test_logs_use_route_template_not_headword(tmp_path, monkeypatch, caplog):
    client = _client(tmp_path, monkeypatch)
    caplog.set_level(logging.INFO, logger="kosha.api")
    client.get(f"/api/v1/lemma/{UNIQUE_HEADWORD}")
    assert UNIQUE_HEADWORD not in caplog.text
    assert "route=/api/v1/lemma/{key}" in caplog.text


def test_metrics_locked_name_list(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.get("/health")
    text = client.get("/metrics").text
    for name in METRIC_NAMES:
        assert name in text, f"missing metric {name}"
    assert "kosha_http_requests_total" in text
    assert 'route="/health"' in text
    assert 'status_class="2xx"' in text


def test_metrics_omit_headword_and_forbidden_labels(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.get(f"/api/v1/lemma/{UNIQUE_HEADWORD}")
    client.get("/api/v1/search", params={"q": UNIQUE_HEADWORD})
    text = client.get("/metrics").text
    assert UNIQUE_HEADWORD not in text
    assert "/api/v1/lemma/" + UNIQUE_HEADWORD not in text
    assert 'route="/api/v1/lemma/{key}"' in text
    for banned in FORBIDDEN_LABEL_KEYS:
        assert f"{banned}=" not in text, f"forbidden label leaked: {banned}"


def test_forbidden_label_raises_before_recording():
    reset_metrics()
    try:
        record_http_request("GET", "/health", "2xx", 0.01)
        # sneak a banned key through the registry
        try:
            REGISTRY.inc("kosha_http_requests_total", {"headword": "vac"})
        except LabelError:
            return
        raise AssertionError("high-cardinality headword label was accepted")
    finally:
        reset_metrics()


def test_allowed_label_vocabulary_is_closed():
    assert FORBIDDEN_LABEL_KEYS.isdisjoint(ALLOWED_LABEL_KEYS)
    assert "route" in ALLOWED_LABEL_KEYS
    assert "headword" in FORBIDDEN_LABEL_KEYS
    assert "request_id" in FORBIDDEN_LABEL_KEYS


def test_ready_503_exports_h2343_failure(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, missing_core=True)
    ready = client.get("/ready")
    assert ready.status_code == 503
    assert ready.json()["ready"] is False
    text = client.get("/metrics").text
    assert re.search(r"^kosha_ready 0$", text, re.M)
    assert 'kosha_ready_check{name="core_db",status="fail"} 1' in text
    assert 'kosha_ready_failures_total{check="core_db"} 1' in text
    assert 'name="history"' in text
    assert 'status="disabled"' in text


def test_metrics_scrape_does_not_increment_failures(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, missing_core=True)
    client.get("/ready")
    first = client.get("/metrics").text
    second = client.get("/metrics").text
    match = re.search(
        r'kosha_ready_failures_total\{check="core_db"\} (\d+)', first
    )
    assert match is not None
    first_n = int(match.group(1))
    match2 = re.search(
        r'kosha_ready_failures_total\{check="core_db"\} (\d+)', second
    )
    assert match2 is not None
    assert int(match2.group(1)) == first_n


def test_healthy_ready_exports_ok_gauges(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    ready = client.get("/ready")
    assert ready.status_code == 200
    history = next(c for c in ready.json()["checks"] if c["name"] == "history")
    assert history["status"] == "disabled"
    text = client.get("/metrics").text
    assert re.search(r"^kosha_ready 1$", text, re.M)
    assert 'kosha_ready_check{name="core_db",status="ok"} 1' in text
    assert 'kosha_ready_check{name="history",status="disabled"} 1' in text
    assert 'kosha_data_version_info{version="0.1.0-w2c"} 1' in text


def test_history_routes_stay_absent(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/api/v1/history")
    assert response.status_code == 404
    text = client.get("/metrics").text
    # unmatched or 404 template — never a history-analytics product metric
    assert "visitor" not in text
    assert "anon_id" not in text


def test_metrics_content_type(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/metrics")
    assert response.status_code == 200
    ctype = response.headers.get("content-type", "")
    assert ctype.startswith("text/plain")
    assert response.headers.get("X-Request-ID")
