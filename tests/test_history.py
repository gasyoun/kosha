"""kosha search-history + analytics pytest suite (Phases A/B/C of the
search-history plan). Uses an isolated per-test SQLite file (monkeypatched
`history_db.HISTORY_DB_PATH`) so these tests never touch a real
`data/db/kosha_history.db`. Requires `data/db/kosha.db` built (same
prerequisite as tests/test_api.py) since `/api/v1/search` is exercised too.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import history_db
from app.main import app
from kosha.feature_gates import mount_history
from kosha.settings import get_settings


@pytest.fixture(autouse=True)
def history_surface(tmp_path, monkeypatch):
    """Exercise the history/auth/stats surface the documented way.

    D10 mounts these routers only when `KOSHA_HISTORY_ENABLED` is truthy, and
    `/api/v1/search` consults the same gate before logging — so the surface
    needs both the runtime mount (`mount_history`, because `app/main.py` built
    its FastAPI app at import time) and the flag visible through
    `get_settings()`. The per-test settings-cache reset in `conftest` restores
    the default (off) state afterwards; `mount_history` restores the exact
    route list, including the cached OpenAPI schema.
    """
    monkeypatch.setattr(history_db, "HISTORY_DB_PATH", tmp_path / "test_history.db")
    monkeypatch.setenv("KOSHA_HISTORY_ENABLED", "1")
    # H6909 (BH-K4): history-enabled settings refuse without a salt — the same
    # fail-closed gate production startup now has.
    monkeypatch.setenv("HISTORY_IP_SALT", "test-history-salt")
    get_settings(refresh=True)
    with mount_history(app):
        yield


@pytest.fixture()
def client():
    # https testserver: the anon cookie is Secure-only outside the documented
    # KOSHA_COOKIE_INSECURE_DEV override (H6909, BH-K5) — production history
    # only ever runs behind TLS, so the exercises replay cookies under https.
    return TestClient(app, base_url="https://testserver")


def test_search_logs_to_history(client):
    r = client.get("/api/v1/search?q=agn&mode=prefix&limit=5")
    assert r.status_code == 200
    assert "kosha_anon_id" in r.cookies

    h = client.get("/api/v1/history")
    assert h.status_code == 200
    body = h.json()
    assert body["query"]["total"] == 1
    assert body["results"][0]["query_raw"] == "agn"
    assert body["results"][0]["mode"] == "prefix"


def test_history_is_per_visitor(client):
    client.get("/api/v1/search?q=agni")
    other = TestClient(app)  # fresh cookie jar = a different anonymous visitor
    r = other.get("/api/v1/history")
    assert r.json()["query"]["total"] == 0


def test_history_accumulates_across_requests(client):
    client.get("/api/v1/search?q=agni")
    client.get("/api/v1/search?q=indra")
    h = client.get("/api/v1/history").json()
    assert h["query"]["total"] == 2
    assert {r["query_raw"] for r in h["results"]} == {"agni", "indra"}


def test_clear_history(client):
    client.get("/api/v1/search?q=agni")
    d = client.delete("/api/v1/history")
    assert d.status_code == 200
    assert d.json()["deleted"] == 1
    h = client.get("/api/v1/history").json()
    assert h["query"]["total"] == 0


def test_history_limit_over_200_rejected(client):
    r = client.get("/api/v1/history?limit=500")
    assert r.status_code == 400


def test_stats_summary_reflects_searches(client):
    client.get("/api/v1/search?q=agni")
    TestClient(app).get("/api/v1/search?q=agni")  # a second, distinct visitor
    s = client.get("/api/v1/stats/summary").json()
    assert s["total_searches"] == 2
    assert s["unique_visitors"] == 2
    assert s["top_terms"][0]["count"] == 2


def test_stats_timeseries_buckets_by_day(client):
    client.get("/api/v1/search?q=agni")
    ts = client.get("/api/v1/stats/timeseries?interval=day&days=7").json()
    assert ts["interval"] == "day"
    assert sum(p["count"] for p in ts["points"]) == 1


def test_stats_timeseries_bad_interval_rejected(client):
    r = client.get("/api/v1/stats/timeseries?interval=month")
    assert r.status_code == 400


def test_stats_top_terms(client):
    client.get("/api/v1/search?q=agni")
    client.get("/api/v1/search?q=agni")
    client.get("/api/v1/search?q=indra")
    top = client.get("/api/v1/stats/top?limit=2").json()["results"]
    assert top[0]["query_slp1"] == "agni"
    assert top[0]["count"] == 2


def _latest_link_token() -> str:
    # H6909 (BH-K6): the token is no longer printed anywhere — read it from
    # the store the endpoint wrote it to, like a real mail-out would deliver it.
    con = history_db.open_connection()
    try:
        row = con.execute(
            "SELECT token FROM magic_links ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        return row["token"]
    finally:
        con.close()


def test_magic_link_request_and_verify(client):
    r = client.post("/api/v1/auth/request-link?email=test@example.com")
    assert r.status_code == 200
    token = _latest_link_token()

    v = client.get(f"/api/v1/auth/verify?token={token}")
    assert v.status_code == 200
    assert v.json() == {"linked": True, "email": "test@example.com"}


def test_magic_link_invalid_token_rejected(client):
    r = client.get("/api/v1/auth/verify?token=not-a-real-token")
    assert r.status_code == 404


def test_magic_link_cannot_be_reused(client):
    client.post("/api/v1/auth/request-link?email=test@example.com")
    token = _latest_link_token()
    client.get(f"/api/v1/auth/verify?token={token}")
    r = client.get(f"/api/v1/auth/verify?token={token}")
    assert r.status_code == 404


def test_request_link_logs_neither_token_nor_address(client, caplog):
    """H6909 (BH-K6): `request-link` logging carries no token, no `token=`
    marker, and no raw address — only a non-redeemable token id."""
    import logging

    address = "secret-user@example.com"
    with caplog.at_level(logging.INFO, logger="kosha.magic_link"):
        r = client.post(f"/api/v1/auth/request-link?email={address}")
    assert r.status_code == 200
    token = _latest_link_token()

    captured = caplog.text
    assert token not in captured
    assert "token=" not in captured
    assert address not in captured


def test_anon_cookie_flags_on_history_route(client):
    """H6909 (BH-K5): the resolve_anon_id call site — hardening flags present."""
    r = client.get("/api/v1/history")
    lines = r.headers.get_list("set-cookie")
    anon = [ln for ln in lines if ln.startswith("kosha_anon_id=")]
    assert anon, f"no kosha_anon_id set-cookie in {lines}"
    line = anon[0]
    assert "Secure" in line
    assert "HttpOnly" in line
    assert "SameSite=lax" in line


def test_anon_cookie_flags_on_verify_route(client):
    """H6909 (BH-K5): the verify-link re-issue call site — same flags, one place."""
    r = client.post("/api/v1/auth/request-link?email=flags@example.com")
    assert r.status_code == 200
    token = _latest_link_token()
    v = client.get(f"/api/v1/auth/verify?token={token}")
    assert v.status_code == 200
    lines = v.headers.get_list("set-cookie")
    anon = [ln for ln in lines if ln.startswith("kosha_anon_id=")]
    assert anon, f"no kosha_anon_id set-cookie in {lines}"
    line = anon[0]
    assert "Secure" in line
    assert "HttpOnly" in line
    assert "SameSite=lax" in line


def test_cookie_dev_override_flips_secure_only_when_explicit(client, monkeypatch):
    # default remains prod-safe: Secure on
    assert "Secure" in client.get("/api/v1/history").headers.get_list("set-cookie")[0]
    # the documented override, off by default: explicitly requested → Secure
    # off — a fresh jar so resolve_anon_id mints rather than reuses
    monkeypatch.setenv("KOSHA_COOKIE_INSECURE_DEV", "1")
    lines = TestClient(app, base_url="https://testserver").get(
        "/api/v1/history"
    ).headers.get_list("set-cookie")
    anon = [ln for ln in lines if ln.startswith("kosha_anon_id=")][0]
    assert "Secure" not in anon
    assert "HttpOnly" in anon


def test_purge_old_search_events_deletes_only_past_cutoff():
    con = history_db.open_connection()
    history_db.upsert_visitor(con, "v1", "2026-01-01T00:00:00+00:00")
    history_db.log_search_event(con, "v1", "2026-01-01T00:00:00+00:00", "old", "old", "prefix", 1, None)
    history_db.log_search_event(con, "v1", "2026-07-01T00:00:00+00:00", "new", "new", "prefix", 1, None)

    deleted = history_db.purge_old_search_events(con, "2026-06-01T00:00:00+00:00")
    assert deleted == 1

    remaining = con.execute("SELECT query_raw FROM search_events").fetchall()
    assert [r["query_raw"] for r in remaining] == ["new"]

    # daily_rollup is a permanent aggregate — purge must never touch it.
    rollup_days = {r["day"] for r in con.execute("SELECT day FROM daily_rollup").fetchall()}
    assert rollup_days == {"2026-01-01", "2026-07-01"}
    con.close()


def test_purge_old_search_events_no_op_when_nothing_past_cutoff():
    con = history_db.open_connection()
    history_db.upsert_visitor(con, "v1", "2026-07-01T00:00:00+00:00")
    history_db.log_search_event(con, "v1", "2026-07-01T00:00:00+00:00", "agni", "agni", "prefix", 1, None)
    deleted = history_db.purge_old_search_events(con, "2020-01-01T00:00:00+00:00")
    assert deleted == 0
    con.close()
