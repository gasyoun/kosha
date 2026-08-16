"""W0C/H2768 — the four surfaces share one serializer and explicit projections.

`/api/v1/lemma`, the `/dicts/*` Salt faces, the prerendered static cards and
the `/w/{slp1}` SSR page all answer "what does the dictionary say about this
headword". Until W0C they did it through three separately-maintained
serializers held together by a comment. `/api/v1`, cards, and SSR retain the
full entry; `/dicts/*` projects the strict Salt §9 face. These are the
assertions that replace that comment.

Fixture tier on purpose: every test here runs against the committed pack, so
CI proves parity on each pull request instead of a workstation proving it
occasionally.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app", ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from kosha.api import repository, serializer  # noqa: E402
from kosha.api.models import SaltEntry  # noqa: E402


def _api_results(client, slp1):
    response = client.get(f"/api/v1/lemma/{slp1}", params={"in": "slp1"})
    assert response.status_code == 200, response.text
    return response.json()["results"]


def test_api_returns_salt_entries(fixture_client, fixture_lemma):
    """D6: the `/api/v1` result element IS a Salt entry, validated as one."""
    for entry in _api_results(fixture_client, fixture_lemma):
        # `model_validate` with `extra="forbid"` throughout is the real
        # assertion: an undeclared field is a contract break, not a bonus.
        SaltEntry.model_validate(entry)


def test_static_card_equals_the_api_response(fixture_con, fixture_client, fixture_lemma):
    """The static tier is a *cache* of the API, so it must be byte-equal.

    `scripts/build_static_cache.py` used to build its own copy of the payload;
    when the copy drifted, a cached card and a live lookup disagreed about the
    same entry and nothing noticed. This is the check that notices.
    """
    from build_static_cache import lemma_card

    dv = repository.data_version(fixture_con)
    card = lemma_card(fixture_con, fixture_lemma, dv)
    assert card["results"] == _api_results(fixture_client, fixture_lemma)


def test_salt_face_entry_matches_the_api_salt_projection(
    fixture_con, fixture_client, fixture_lemma
):
    """One serializer, two public contracts, shared Salt fields equal.

    Keyed by `(dict, id)`, not by `id`: a Salt id is **dictionary-scoped**
    (profile §5 fetches ids under `/dicts/{id}/…`), so MW's `agni` and Apte's
    `agni` both legitimately mint `lemma-agni`. That collision is only visible
    on kosha's merged multi-dictionary card, which is why the note lives in
    `SaltEntry` too — a client indexing a lemma card by `id` alone would lose
    entries.
    """
    contract = json.loads(
        (ROOT / "tests" / "contracts" / "salt-entry-v0.1.0.json")
        .read_text(encoding="utf-8")
    )
    salt_keys = contract["entry_top_level_keys"]
    api_by_key = {
        (e["kosha"]["dict"], e["id"]): e
        for e in _api_results(fixture_client, fixture_lemma)
    }
    seen = 0
    for dict_code in repository.ALL_DICTS:
        response = fixture_client.get(
            f"/dicts/{dict_code}/restful/entries",
            params={"field": "headword_slp1", "query": fixture_lemma,
                    "query_type": "term"},
        )
        assert response.status_code == 200, response.text
        for entry in response.json()["data"]["entries"]:
            key = (dict_code, entry["id"])
            assert key in api_by_key, f"{key} absent from /api/v1"
            assert set(entry) == set(salt_keys)
            assert entry == {field: api_by_key[key][field] for field in salt_keys}
            seen += 1
    assert seen == len(api_by_key), "a face served fewer entries than /api/v1"


def test_ssr_page_carries_the_same_rendered_html(fixture_client, fixture_lemma):
    """P5-4: static ∥ SSR parity on primary content.

    The SSR route builds its card through the same serializer, so every entry's
    sanitized HTML must appear verbatim in the served page.
    """
    page = fixture_client.get(f"/w/{fixture_lemma}")
    assert page.status_code == 200, page.text
    for entry in _api_results(fixture_client, fixture_lemma):
        html = entry["kosha"]["rendered_html"]
        if html:
            assert html in page.text


def test_one_serializer_has_no_surviving_copies():
    """The de-duplication itself, asserted.

    A future edit that reintroduces a hand-built entry dict in the static
    builder would pass every test above — they compare *outputs*, and a fresh
    copy starts out identical. This checks the structural fact those tests
    cannot: the builder delegates.
    """
    source = (ROOT / "scripts" / "build_static_cache.py").read_text(encoding="utf-8")
    assert "serializer.serialize_entry" in source or "serializer.entry_dict" in source
    # The tell-tale of the old copy: building the payload dict inline.
    assert '"rendered_html": render(' not in source


@pytest.mark.parametrize("out", ["iast", "slp1", "deva", "hk"])
def test_output_scheme_reaches_every_surface(fixture_con, fixture_client, fixture_lemma, out):
    """`out=` is a serializer argument, so it must behave identically wherever
    the serializer is called from."""
    from build_static_cache import lemma_card

    dv = repository.data_version(fixture_con)
    card = lemma_card(fixture_con, fixture_lemma, dv, out=out)
    response = fixture_client.get(
        f"/api/v1/lemma/{fixture_lemma}", params={"in": "slp1", "out": out}
    )
    assert response.status_code == 200
    assert card["results"] == response.json()["results"]


def test_raw_is_opt_in_and_unmodified(fixture_con, fixture_client, fixture_lemma):
    """"Store raw Cologne markup unchanged; sanitize only rendered output."

    The raw body must be absent unless asked for, and when asked for must be
    the stored bytes — not a sanitized, re-rendered or re-escaped copy of them.
    """
    plain = _api_results(fixture_client, fixture_lemma)
    assert all(e["kosha"]["raw"] is None for e in plain)
    assert all(e["csl"]["xmlCsl"] is None for e in plain)

    response = fixture_client.get(
        f"/api/v1/lemma/{fixture_lemma}", params={"in": "slp1", "raw": 1}
    )
    assert response.status_code == 200
    for entry in response.json()["results"]:
        stored = fixture_con.execute(
            "SELECT body FROM entries WHERE dict=? AND L=?",
            (entry["kosha"]["dict"], entry["kosha"]["L"]),
        ).fetchone()["body"]
        assert entry["kosha"]["raw"] == stored
        assert entry["csl"]["xmlCsl"] == stored


def test_envelope_is_unchanged_by_the_migration(fixture_client, fixture_lemma):
    """W0C changed `results`, not the envelope around it (item 3: "keep the
    envelope"). A client reading `data_version`/`query` keeps working."""
    body = fixture_client.get(
        f"/api/v1/lemma/{fixture_lemma}", params={"in": "slp1"}
    ).json()
    assert set(body) == {"data_version", "query", "results"}
    assert body["query"]["key"] == fixture_lemma
    assert body["data_version"]


def test_entries_are_json_serializable(fixture_con, fixture_lemma):
    """The serializer returns models; every surface ships JSON. A field whose
    type only survives in Python (a Path, a Row) would pass the model and fail
    at the wire."""
    dv = repository.data_version(fixture_con)
    entries = serializer.serialize_lemma_card(
        fixture_con, fixture_lemma, data_version=dv,
        public_base="https://example.org",
    )
    assert entries
    json.dumps([serializer.entry_dict(e) for e in entries])
