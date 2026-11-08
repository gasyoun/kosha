"""H6906 — the bounded-limit dependency: the LIMIT -1 class dies at the type layer.

Three gates, mirroring the handoff acceptance:

1. **Introspection** — every route parameter named `limit`, `size`, `offset`
   or `ids` declares its bounds in machine-readable form, so a new unbounded
   one fails this suite, not production SQLite (`LIMIT -1` = no limit).
2. **OpenAPI** — the bounds stay visible to clients in `/openapi.json`.
3. **Probes** — the handoff's parameterised attack values (`limit=-1`,
   `size=-1`, `limit=0`, `limit=1000000000`, `offset=-1`, 101 ids) all answer
   400 with the house error body, and legitimate values still answer 200.

Before-evidence (handoff H6906, measured on the full local DB 13-10-2026):
`SELECT COUNT(DISTINCT slp1_key) FROM entries WHERE dict='mw' LIMIT -1` →
194,083 keys — that is what `/dicts/mw/restful/entries?size=-1` serialised
whole before this dependency existed.
"""
import sys
from pathlib import Path

import pytest
from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from app.main import app
from kosha.api.models import ErrorResponse
from kosha.feature_gates import mount_history

#: The four parameter names the handoff fences.
FENCED = {"limit", "size", "offset", "ids"}

#: Documented caps (keep in sync with app/params.py — asserted, not trusted).
LIMIT_BOUNDS = (1, 200)
OFFSET_BOUNDS = (0, 10_000_000)
IDS_CAP = 100


def _walk_query_params(dependant):
    """All query params of `dependant` and its sub-dependencies.

    Hand-rolled instead of `fastapi.dependencies.utils.get_flat_dependant`
    (removed in current FastAPI): a `Depends(...)` boundary must not hide the
    param from the introspection gate — that is the point of walking.
    """
    yield from dependant.query_params
    for sub in dependant.dependencies:
        yield from _walk_query_params(sub)

def _fenced_params(routes):
    """Yield (route, field) for every fenced query param on `routes`.

    Walks the dependant tree so params contributed by a `Depends(...)`
    boundary (the shared bounded-int dependency) are seen exactly like inline
    params — an inline `limit: int = 50` and a dependency-provided one must
    both be checkable.
    """
    for route in routes:
        if not isinstance(route, APIRoute):
            continue
        for field in _walk_query_params(route.dependant):
            if field.alias in FENCED:
                yield route, field


def _declared_int_bounds(field):
    extra = field.field_info.json_schema_extra or {}
    return extra.get("minimum"), extra.get("maximum")


def test_every_fenced_param_declares_bounds():
    """The introspection gate: no fenced param may reach a route unbounded."""
    with mount_history(app):
        found = list(_fenced_params(app.routes))
    assert found, "introspection saw no limit/size/offset/ids params — it is checking nothing"
    unbounded = []
    for route, field in found:
        if field.alias == "ids":
            extra = field.field_info.json_schema_extra or {}
            if "maxItems" not in extra:
                unbounded.append(f"{route.path} {field.alias}: no maxItems")
        else:
            minimum, maximum = _declared_int_bounds(field)
            if minimum is None or maximum is None:
                unbounded.append(f"{route.path} {field.alias}: bounds {minimum}..{maximum}")
    assert not unbounded, f"unbounded fenced params: {unbounded}"


def test_introspection_reds_on_a_deliberately_unbounded_param():
    """The verifier's negative: a new unbounded `limit` param must be caught.

    Adds a throwaway route with a plain `limit: int = 10` (the exact shape a
    careless new endpoint would have) and asserts the same scanner that gates
    the real routes flags it. The route is removed again before yield returns.
    """
    def _rogue(limit: int = 10):
        return {"limit": limit}

    rogue = APIRoute("/api/v1/_h6906_rogue", _rogue, methods=["GET"])
    app.router.routes.append(rogue)
    try:
        flagged = [
            f"{route.path} {field.alias}"
            for route, field in _fenced_params([rogue])
            if _declared_int_bounds(field) == (None, None)
        ]
    finally:
        app.router.routes.remove(rogue)
    assert flagged == ["/api/v1/_h6906_rogue limit"], flagged


def test_openapi_documents_the_bounds():
    schema = app.openapi()
    params = {}

    def _collect(node):
        for param in node.get("parameters", []):
            params[(param.get("in"), param.get("name"))] = param

    for path_item in schema["paths"].values():
        _collect(path_item)
        for method in ("get", "post"):
            op = path_item.get(method)
            if op:
                _collect(op)

    limit = params[("query", "limit")]["schema"]
    assert limit["minimum"] == LIMIT_BOUNDS[0] and limit["maximum"] == LIMIT_BOUNDS[1]
    offset = params[("query", "offset")]["schema"]
    assert offset["minimum"] == OFFSET_BOUNDS[0] and offset["maximum"] == OFFSET_BOUNDS[1]
    size = params[("query", "size")]["schema"]
    assert size["minimum"] == LIMIT_BOUNDS[0] and size["maximum"] == LIMIT_BOUNDS[1]
    ids = params[("query", "ids")]["schema"]
    assert ids["maxItems"] == IDS_CAP


# --------------------------------------------------------------------------- #
# Probes: the handoff's attack values answer 400 + house error body
# --------------------------------------------------------------------------- #

def _assert_kosha_400(response):
    assert response.status_code == 400, response.text
    body = response.json()
    parsed = ErrorResponse.model_validate(body)
    assert "detail" not in body
    assert parsed.error.code == "bad_request"
    assert parsed.error.message
    return parsed


def _assert_salt_400(response):
    assert response.status_code == 400, response.text
    body = response.json()
    assert set(body) == {"error"}
    assert isinstance(body["error"], str) and body["error"]
    return body["error"]


@pytest.mark.parametrize("params", [
    {"limit": -1},
    {"limit": 0},
    {"limit": 1_000_000_000},
    {"offset": -1},
    {"offset": 10_000_001},
])
def test_search_rejects_unbounded_values_with_house_body(fixture_client, params):
    response = fixture_client.get("/api/v1/search", params={"q": "a", **params})
    parsed = _assert_kosha_400(response)
    name = next(iter(params))
    assert name in parsed.error.message


def test_history_rejects_unbounded_values_with_house_body():
    """History routes are gate-mounted; the dependency must bound them too."""
    from fastapi.testclient import TestClient

    with mount_history(app):
        client = TestClient(app)
        for url, params in [
            ("/api/v1/history", {"limit": -1}),
            ("/api/v1/history", {"limit": 0}),
            ("/api/v1/history", {"offset": -1}),
            ("/api/v1/stats/top", {"limit": -1}),
            ("/api/v1/stats/top", {"limit": 0}),
        ]:
            _assert_kosha_400(client.get(url, params=params))


@pytest.mark.parametrize("size", [-1, 0, 1_000_000_000])
def test_salt_entries_rejects_unbounded_size_with_salt_body(fixture_client, size):
    """BH-K3's live exposure: `size=-1` serialised the whole MW face
    (194,083 keys on the full DB). The Salt face keeps C-SALT's bare-string
    error form — still 400, still one documented shape."""
    _assert_salt_400(
        fixture_client.get(
            "/dicts/mw/restful/entries",
            params={"field": "headword_slp1", "query": "agni", "size": size},
        )
    )


def test_salt_ids_rejects_more_than_100_ids_with_salt_body(fixture_client):
    _assert_salt_400(
        fixture_client.get(
            "/dicts/mw/restful/ids",
            params={"ids": ["lemma-x"] * (IDS_CAP + 1)},
        )
    )


# --------------------------------------------------------------------------- #
# Legitimate values still answer 200
# --------------------------------------------------------------------------- #

def test_legitimate_limits_still_answer_200(fixture_client, fixture_lemma):
    assert fixture_client.get(
        "/api/v1/search", params={"q": "a", "limit": 50, "offset": 0}
    ).status_code == 200
    assert fixture_client.get(
        "/api/v1/search", params={"q": "a", "limit": 200}
    ).status_code == 200
    assert fixture_client.get(
        "/dicts/mw/restful/entries",
        params={"field": "headword_slp1", "query": fixture_lemma,
                "query_type": "term", "size": 25},
    ).status_code == 200
    assert fixture_client.get(
        "/dicts/mw/restful/ids", params={"ids": [f"lemma-{fixture_lemma}"]}
    ).status_code == 200

    from fastapi.testclient import TestClient

    with mount_history(app):
        client = TestClient(app)
        assert client.get("/api/v1/history", params={"limit": 50}).status_code == 200
        assert client.get("/api/v1/history", params={"limit": 200}).status_code == 200
        assert client.get(
            "/api/v1/history", params={"limit": 50, "offset": 100}
        ).status_code == 200
        assert client.get("/api/v1/stats/top", params={"limit": 50}).status_code == 200
