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


def _mounted_paths() -> set[str]:
    """Route paths, tolerating FastAPI's `_IncludedRouter` wrapper.

    Newer FastAPI wraps an included router in an object with no `.path`, so
    introspecting `route.path` directly works on some versions and raises on
    others — the CI runner caught exactly that.
    """
    paths = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if path:
            paths.add(path)
        for nested in getattr(getattr(route, "router", None), "routes", ()):
            nested_path = getattr(nested, "path", None)
            if nested_path:
                paths.add(nested_path)
    return paths


def test_mounting_history_makes_the_routes_reachable_again():
    """The gate is a mount decision, not a missing implementation."""
    with mount_history(app):
        paths = _mounted_paths()
        assert "/api/v1/history" in paths
        assert "/api/v1/stats/summary" in paths
    # …and unmounting restores the default surface for every later test.
    assert "/api/v1/history" not in _mounted_paths()
    assert client.get("/api/v1/history").status_code == 404
