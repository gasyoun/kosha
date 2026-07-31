"""W0B (H1944) — the visitor-data surface is off unless explicitly enabled.

Three separable claims, each pinned here:

1. The personal-history, magic-link auth and aggregate-stats routes are not
   merely guarded — they are **absent from the route table**, so they 404 like
   any unknown path and leak nothing about the feature's existence.
2. A search served by a history-disabled app writes **nothing** to the history
   store. A disabled feature that keeps accumulating visitor rows is still
   collecting visitor data.
3. Flipping `KOSHA_ENABLE_HISTORY` on brings all of it back, so the gate is a
   deployment setting rather than a removal.

Claim 1 needs no dictionary DB and is marked `fixture` (CI runs it). Claims
about `/api/v1/search` need real data and are skipped without it.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import history_db  # noqa: E402
from app.main import build_app  # noqa: E402
from app.db import core_db_path  # noqa: E402
from kosha.settings import reload_settings  # noqa: E402

GATED_PATHS = [
    "/api/v1/history",
    "/api/v1/stats/summary",
    "/api/v1/stats/timeseries",
    "/api/v1/stats/top",
    "/api/v1/auth/verify?token=x",
]


@pytest.fixture()
def off_client():
    return TestClient(build_app(enable_history=False))


# --- claim 1: routes absent, not just guarded ---------------------------------

@pytest.mark.fixture
@pytest.mark.parametrize("path", GATED_PATHS)
def test_gated_routes_404_when_disabled(off_client, path):
    assert off_client.get(path).status_code == 404


@pytest.mark.fixture
def test_gated_routes_absent_from_route_table():
    disabled = {r.path for r in build_app(enable_history=False).routes}
    enabled = {r.path for r in build_app(enable_history=True).routes}
    only_when_enabled = enabled - disabled
    assert "/api/v1/history" in only_when_enabled
    assert "/api/v1/auth/request-link" in only_when_enabled
    assert {p for p in only_when_enabled if p.startswith("/api/v1/stats/")}
    # The dictionary surface is identical either way — the gate must not
    # accidentally take a lookup route with it.
    assert not disabled - enabled
    for public in ("/api/v1/lemma/{key}", "/api/v1/search", "/health"):
        assert public in disabled, public


@pytest.mark.fixture
def test_delete_history_also_absent_when_disabled(off_client):
    # DELETE /api/v1/history is a separate method on the same path; a gate that
    # only dropped the GET would still expose a destructive endpoint.
    assert off_client.delete("/api/v1/history").status_code == 404


@pytest.mark.fixture
def test_magic_link_post_absent_when_disabled(off_client):
    assert off_client.post("/api/v1/auth/request-link?email=a@b.c").status_code == 404


# --- claim 3: the flag, not the code, is what turns it on ---------------------

@pytest.mark.fixture
def test_env_flag_enables_the_surface(monkeypatch):
    monkeypatch.setenv("KOSHA_ENABLE_HISTORY", "1")
    reload_settings()
    try:
        paths = {r.path for r in build_app().routes}
        assert "/api/v1/history" in paths
    finally:
        monkeypatch.delenv("KOSHA_ENABLE_HISTORY", raising=False)
        reload_settings()


@pytest.mark.fixture
def test_default_is_off(monkeypatch):
    monkeypatch.delenv("KOSHA_ENABLE_HISTORY", raising=False)
    reload_settings()
    assert "/api/v1/history" not in {r.path for r in build_app().routes}


# --- claim 2: no visitor rows written while disabled --------------------------

@pytest.mark.skipif(not core_db_path().exists(),
                    reason="needs a built data/db/kosha.db for /api/v1/search")
def test_search_writes_no_history_when_disabled(tmp_path, monkeypatch, off_client):
    store = tmp_path / "history.db"
    monkeypatch.setattr(history_db, "HISTORY_DB_PATH", store)
    r = off_client.get("/api/v1/search?q=agni&mode=prefix&limit=5")
    assert r.status_code == 200
    # Not even an empty store should be created — nothing opened it.
    assert not store.exists(), "history store was written while the feature was off"
    assert "kosha_anon_id" not in r.cookies, "visitor cookie minted while history was off"
