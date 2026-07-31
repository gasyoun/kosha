"""D10 — history/auth/stats are absent by default (H1944, W0B item 3).

"Absent", not "disabled": the router is never mounted, so the paths 404 and do
not appear in the OpenAPI schema. A public deployment that ships the handlers
behind a flag is one misconfiguration away from collecting visitor data it
promised not to collect.

These tests need no database — they assert routing, which is exactly what makes
them safe to run on the fixture CI tier.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

from app.main import app  # noqa: E402
from kosha.feature_gates import history_enabled, mount_history  # noqa: E402

client = TestClient(app)

GATED_PATHS = [
    "/api/v1/history",
    "/api/v1/stats/summary",
    "/api/v1/stats/timeseries",
    "/api/v1/stats/top",
    "/api/v1/auth/verify",
]


def test_the_test_environment_has_history_off():
    assert history_enabled() is False


@pytest.mark.parametrize("path", GATED_PATHS)
def test_gated_paths_return_404(path):
    assert client.get(path).status_code == 404


def test_gated_paths_are_absent_from_the_openapi_schema():
    documented = set(app.openapi()["paths"])
    assert not [p for p in documented if p.startswith(("/api/v1/history", "/api/v1/stats", "/api/v1/auth"))]


def test_ungated_paths_still_answer():
    assert client.get("/health").status_code == 200


def _documented_paths() -> set[str]:
    """The app's own OpenAPI paths.

    Asserted through the schema rather than `app.routes`: FastAPI changed the
    internal shape of an included router between the version this workstation
    has and the one CI installs (`_IncludedRouter`, no `.path`), while the
    schema is the stable, user-visible contract — and it is the surface the
    "absent, not merely disabled" claim is really about.
    """
    app.openapi_schema = None
    try:
        return set(app.openapi()["paths"])
    finally:
        app.openapi_schema = None


def test_mounting_history_makes_the_routes_reachable_again():
    """The gate is a mount decision, not a missing implementation."""
    with mount_history(app):
        documented = _documented_paths()
        assert "/api/v1/history" in documented
        assert "/api/v1/stats/summary" in documented
    # …and unmounting restores the default surface for every later test.
    assert "/api/v1/history" not in _documented_paths()
    assert client.get("/api/v1/history").status_code == 404


# --------------------------------------------------------------------------- #
# W0C (H1945, item 8) — absent routes are only half the promise
# --------------------------------------------------------------------------- #

def test_no_visitor_data_is_collected_while_history_is_off(fixture_client):
    """Serving a search must neither mint an identity cookie nor write a store.

    Unmounting the *read* routes while the *write* path kept logging would be
    the worst of both worlds: data collected from a public deployment that
    documents itself as collecting none, and no endpoint through which anyone
    could notice. This exercises the real search route, so it fails if the
    logging branch is ever re-enabled independently of the gate.
    """
    from kosha.settings import get_settings

    history_db = get_settings().history_db
    existed = history_db.exists()
    before = history_db.stat().st_mtime_ns if existed else None

    response = fixture_client.get("/api/v1/search", params={"q": "a"})
    assert response.status_code == 200

    # No `Set-Cookie` at all — the anon-id cookie is the collection trigger.
    assert "set-cookie" not in {k.lower() for k in response.headers}
    if existed:
        assert history_db.stat().st_mtime_ns == before, "history store was written"
    else:
        assert not history_db.exists(), "history store was created"


def test_the_search_route_still_answers_with_history_off(fixture_client):
    """The gate must not cost the public surface anything."""
    body = fixture_client.get("/api/v1/search", params={"q": "a"}).json()
    assert set(body) == {"data_version", "query", "results"}
