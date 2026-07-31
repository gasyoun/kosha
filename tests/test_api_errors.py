"""W0C — one documented error shape per contract (H1945, item 5).

Before this, three shapes left `/api/v1`: the deliberate errors nested one
level inside FastAPI's `detail` wrapper, FastAPI's own validation errors as a
list of `{loc, msg, type}` objects, and unhandled failures as
`{"detail": "Internal Server Error"}`. A client had to know all three to read
one API.

Now there are two, each owned by a contract and each asserted here:

* `/api/v1/*` → `{"error": {"code", "message", "suggestions"}}`, top level;
* `/dicts/*` → `{"error": "<message>"}`, the bare-string form C-SALT
  documents (profile §3.2), because those routes exist to be wire-compatible.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from kosha.api.models import ErrorResponse  # noqa: E402


def _assert_kosha_error(response, status: int, code: str | None = None):
    assert response.status_code == status, response.text
    body = response.json()
    # `extra="forbid"`: a stray key (FastAPI's `detail`, say) fails validation,
    # which is the whole point — the shape is exact, not merely present.
    parsed = ErrorResponse.model_validate(body)
    assert "detail" not in body
    if code is not None:
        assert parsed.error.code == code
    assert parsed.error.message
    return parsed


def test_deliberate_404_is_a_top_level_error_object(fixture_client):
    response = fixture_client.get(
        "/api/v1/lemma/nosuchlemmaanywhere", params={"in": "slp1"}
    )
    _assert_kosha_error(response, 404, "lemma_not_found")


def test_error_object_is_not_nested_inside_detail(fixture_client):
    """The specific regression: `error()` used to raise
    `HTTPException(detail={"error": {...}})`, so clients read
    `detail.error.code`. The object is top level now."""
    body = fixture_client.get(
        "/api/v1/lemma/nosuchlemmaanywhere", params={"in": "slp1"}
    ).json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "suggestions"}


def test_validation_failure_uses_the_same_shape(fixture_client):
    """FastAPI answers a bad query parameter with a 422 and a list of objects.
    A service whose own errors are 400 + an object cannot also answer this
    class of mistake with 422 + a list and still claim one contract."""
    response = fixture_client.get("/api/v1/search", params={"q": "a", "limit": "many"})
    parsed = _assert_kosha_error(response, 400, "bad_request")
    # The field that failed still has to be identifiable.
    assert "limit" in parsed.error.message


def test_unknown_route_uses_the_same_shape(fixture_client):
    """Starlette's own routing 404 never passed through `error()` at all."""
    _assert_kosha_error(fixture_client.get("/api/v1/no/such/route"), 404)


def test_method_not_allowed_uses_the_same_shape(fixture_client):
    _assert_kosha_error(fixture_client.post("/api/v1/meta"), 405)


def test_route_level_400_uses_the_same_shape(fixture_client):
    response = fixture_client.get("/api/v1/search", params={"q": "a", "limit": 5000})
    _assert_kosha_error(response, 400, "bad_request")


def test_malformed_sense_id_is_a_400_object(fixture_client):
    _assert_kosha_error(fixture_client.get("/api/v1/sense/not-a-sense-id"), 400)


def test_suggestions_survive_normalization(fixture_client):
    """`suggestions` carries the actionable half of an error; the handler must
    not drop it while flattening."""
    response = fixture_client.get("/api/v1/page/mw", params={"page": 999999})
    assert response.status_code == 404
    assert isinstance(response.json()["error"]["suggestions"], list)


# --------------------------------------------------------------------------- #
# The Salt faces keep C-SALT's error form — deliberately a different shape
# --------------------------------------------------------------------------- #

def _assert_salt_error(response, status: int = 400):
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"}
    # A *string*, per profile §3.2 — not kosha's object.
    assert isinstance(body["error"], str) and body["error"]
    return body["error"]


def test_salt_face_unknown_dict_is_a_400_string(fixture_client):
    """Profile §3.2 requires HTTP 400. These routes used to answer **200** with
    an error body, so a client checking the status read a failure as success."""
    _assert_salt_error(
        fixture_client.get("/dicts/nosuchdict/restful/entries",
                           params={"query": "agni"})
    )


def test_salt_face_unsupported_field_is_a_400_string(fixture_client):
    message = _assert_salt_error(
        fixture_client.get("/dicts/mw/restful/entries",
                           params={"field": "xml", "query": "agni",
                                   "query_type": "term"})
    )
    assert "field" in message


@pytest.mark.parametrize("query_type", ["wildcard", "regexp", "fuzzy", "match",
                                        "match_phrase", "nonsense"])
def test_unimplemented_query_types_400_rather_than_return_empty(
    fixture_client, query_type
):
    """Profile §4: a host MUST implement the requested mode or return an
    explicit 400. It MUST NOT silently return an empty result set — which reads
    to a client as "this dictionary has no such word"."""
    message = _assert_salt_error(
        fixture_client.get("/dicts/mw/restful/entries",
                           params={"field": "headword_slp1", "query": "agni",
                                   "query_type": query_type})
    )
    assert "query_type" in message


def test_salt_face_ids_unknown_dict_is_a_400_string(fixture_client):
    _assert_salt_error(
        fixture_client.get("/dicts/nosuchdict/restful/ids", params={"ids": "lemma-agni"})
    )


def test_implemented_modes_still_answer(fixture_client, fixture_lemma):
    for query_type in ("term", "prefix"):
        response = fixture_client.get(
            "/dicts/mw/restful/entries",
            params={"field": "headword_slp1", "query": fixture_lemma,
                    "query_type": query_type},
        )
        assert response.status_code == 200, response.text
        assert "entries" in response.json()["data"]
