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
import history_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_history_db(tmp_path, monkeypatch):
    monkeypatch.setattr(history_db, "HISTORY_DB_PATH", tmp_path / "test_history.db")
    yield


@pytest.fixture()
def client():
    return TestClient(app)


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


def test_magic_link_request_and_verify(client, capsys):
    r = client.post("/api/v1/auth/request-link?email=test@example.com")
    assert r.status_code == 200
    captured = capsys.readouterr()
    token = captured.out.strip().rsplit("token=", 1)[1]

    v = client.get(f"/api/v1/auth/verify?token={token}")
    assert v.status_code == 200
    assert v.json() == {"linked": True, "email": "test@example.com"}


def test_magic_link_invalid_token_rejected(client):
    r = client.get("/api/v1/auth/verify?token=not-a-real-token")
    assert r.status_code == 404


def test_magic_link_cannot_be_reused(client, capsys):
    client.post("/api/v1/auth/request-link?email=test@example.com")
    token = capsys.readouterr().out.strip().rsplit("token=", 1)[1]
    client.get(f"/api/v1/auth/verify?token={token}")
    r = client.get(f"/api/v1/auth/verify?token={token}")
    assert r.status_code == 404


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
