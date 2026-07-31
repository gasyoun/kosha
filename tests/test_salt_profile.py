"""W0C — conformance to the C-SALT / CSL Salt profile (H1945, items 1 & 3).

D6 makes the profile binding for `/api/v1`. These assertions read against
[SALT_API_PROFILE.md](https://github.com/sanskrit-lexicon/csl-standards/blob/main/docs/SALT_API_PROFILE.md)
§8 and are deliberately literal about the fields the profile fixes — a
compatibility claim is only worth what its checks are.

Divergences the profile itself sanctions (and this file therefore asserts
rather than flags): `xml` is null until TEI conversion ships (§8.1); the
`-L{lnum}` id form is used for un-numbered sub-records (§8.1, catalogued in the
loss report); and modes kosha has not indexed return an explicit 400 (§4),
which `tests/test_api_errors.py` covers.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from kosha.api import repository, serializer  # noqa: E402

#: Profile §8.1 — the C-SALT-compatible top level. A conforming entry has
#: exactly these, plus the namespaced extension objects.
SALT_TOP_LEVEL = {"id", "headword_slp1", "sense", "re_headwords_slp1", "created", "xml"}


def _entries(client, lemma):
    response = client.get(f"/api/v1/lemma/{lemma}", params={"in": "slp1"})
    assert response.status_code == 200, response.text
    return response.json()["results"]


def test_top_level_is_exactly_the_profile_plus_namespaced_extensions(
    fixture_client, fixture_lemma
):
    for entry in _entries(fixture_client, fixture_lemma):
        assert set(entry) == SALT_TOP_LEVEL | {"csl", "kosha"}


def test_kosha_only_data_is_namespaced(fixture_client, fixture_lemma):
    """D6's actual rule: a C-SALT client must be able to ignore the extension
    objects and lose nothing C-SALT defines. That only holds if no kosha field
    leaked to the top level."""
    kosha_only = {"rendered_html", "sense_ids", "evidence", "heritage",
                  "cite", "scan_url", "dict", "L", "raw"}
    for entry in _entries(fixture_client, fixture_lemma):
        assert not (kosha_only & set(entry)), "kosha field leaked to the top level"
        assert kosha_only <= set(entry["kosha"]), "kosha field missing from its block"


def test_profile_field_types(fixture_client, fixture_lemma):
    for entry in _entries(fixture_client, fixture_lemma):
        assert isinstance(entry["id"], str) and entry["id"].startswith("lemma-")
        assert isinstance(entry["headword_slp1"], str) and entry["headword_slp1"]
        assert isinstance(entry["sense"], list)
        assert all(isinstance(s, str) for s in entry["sense"])
        assert isinstance(entry["re_headwords_slp1"], list)


def test_xml_is_null_until_tei_ships(fixture_client, fixture_lemma):
    """§8.1: `xml` is the TEI-P5 body and MUST NOT carry CSL display-XML.
    Filling it with the Cologne markup would look like conformance and be the
    opposite — a client would parse Cologne's tagset as TEI."""
    for entry in _entries(fixture_client, fixture_lemma):
        assert entry["xml"] is None


def test_cologne_markup_is_offered_as_xmlcsl_instead(fixture_client, fixture_lemma):
    """…and the honest slot for it, §8.2 `csl.xmlCsl`, does carry it on request."""
    response = fixture_client.get(
        f"/api/v1/lemma/{fixture_lemma}", params={"in": "slp1", "raw": 1}
    )
    for entry in response.json()["results"]:
        assert entry["xml"] is None
        assert entry["csl"]["xmlCsl"]


def test_csl_block_carries_cologne_provenance(fixture_client, fixture_lemma):
    for entry in _entries(fixture_client, fixture_lemma):
        csl = entry["csl"]
        assert csl["lnum"]
        assert set(csl) >= {"lnum", "page", "column", "scanUrl", "references",
                            "accentedKey", "headwordIast", "headwordDeva"}
        # kosha does not host Cologne's own rendering; it must not claim to.
        assert csl["html"] is None and csl["text"] is None


def test_sense_glosses_are_populated(fixture_client, fixture_lemma):
    """`sense[]` was hardcoded `[]` before W0C — a profile field the old
    serializer had no access to the data for. It is real now."""
    entries = _entries(fixture_client, fixture_lemma)
    assert any(entry["sense"] for entry in entries)
    for entry in entries:
        assert len(entry["sense"]) == len(entry["kosha"]["sense_ids"])


def test_sense_ids_are_pinned_to_the_data_version(fixture_client, fixture_lemma):
    body = fixture_client.get(
        f"/api/v1/lemma/{fixture_lemma}", params={"in": "slp1"}
    ).json()
    dv = body["data_version"]
    for entry in body["results"]:
        for sense_id in entry["kosha"]["sense_ids"]:
            assert sense_id.endswith(f"@{dv}")


def test_rest_face_envelope_shape(fixture_client, fixture_lemma):
    """§3.2 / §5 — `{data: {entries: []}}` and `{data: {ids: []}}`."""
    entries = fixture_client.get(
        "/dicts/mw/restful/entries",
        params={"field": "headword_slp1", "query": fixture_lemma, "query_type": "term"},
    ).json()
    assert set(entries) == {"data"} and set(entries["data"]) == {"entries"}

    ids = fixture_client.get(
        "/dicts/mw/restful/ids", params={"ids": f"lemma-{fixture_lemma}"}
    ).json()
    assert set(ids) == {"data"} and set(ids["data"]) == {"ids"}


def test_ids_face_round_trips_a_minted_id(fixture_client, fixture_lemma):
    """The ids face must resolve exactly the id the entries face minted —
    otherwise a client cannot follow its own results."""
    listed = fixture_client.get(
        "/dicts/mw/restful/entries",
        params={"field": "headword_slp1", "query": fixture_lemma, "query_type": "term"},
    ).json()["data"]["entries"]
    if not listed:
        pytest.skip("fixture pack has no MW entry for this headword")
    for entry in listed:
        fetched = fixture_client.get(
            "/dicts/mw/restful/ids", params={"ids": entry["id"]}
        ).json()["data"]["ids"]
        assert entry["id"] in {f["id"] for f in fetched}


def test_ids_face_is_a_get_by_id_not_a_search(fixture_client):
    """§5. An unknown id yields nothing — not an error, and not a fuzzy match."""
    fetched = fixture_client.get(
        "/dicts/mw/restful/ids", params={"ids": "lemma-notaheadwordatall"}
    ).json()["data"]["ids"]
    assert fetched == []


# --------------------------------------------------------------------------- #
# id minting (§8.1) — unit-level, no database
# --------------------------------------------------------------------------- #

def test_unique_headword_gets_no_suffix():
    assert serializer.mint_salt_id("agni", "101", "<H1>…</H1>", 1) == "lemma-agni"


def test_homonyms_use_cologne_own_number_when_present():
    body = '<H1><h><key1>ka</key1></h><tail><info hui="2" lnum="1234"/></tail></H1>'
    assert serializer.mint_salt_id("ka", "1234", body, 4) == "lemma-ka-2"


def test_homonyms_fall_back_to_the_lnum_form():
    """The sanctioned Phase-1 divergence: un-numbered sub-records still need
    unique ids."""
    assert serializer.mint_salt_id("ka", "1234", "<H1>no info tag</H1>", 4) == "lemma-ka-L1234"


def test_a_hom_number_quoted_in_running_prose_is_not_a_homonym_marker():
    """MW L41336.1/.3 quote *another* headword's homonym number in
    cross-reference prose. Matching a bare `<hom>` would mint the wrong id for
    an entry that merely mentions one."""
    body = "<H1>see <hom>3</hom> of another word</H1>"
    assert serializer.mint_salt_id("x", "9", body, 2) == "lemma-x-L9"


def test_dictionary_scoped_ids_may_collide_across_dictionaries(fixture_con, fixture_lemma):
    """Documented, not accidental — see `SaltEntry`. Asserted so a future
    change to id minting cannot silently make `id` globally unique (which would
    break C-SALT parity) or silently rely on it being so."""
    minted = set()
    for dict_code in repository.ALL_DICTS:
        rows = repository.entries_for_key(fixture_con, dict_code, fixture_lemma)
        for row in rows:
            minted.add((dict_code, serializer.mint_salt_id(
                row["slp1_key"], row["L"], row["body"], len(rows))))
    ids_only = [entry_id for _dict, entry_id in minted]
    assert len(minted) == len(set(minted)), "ids collide *within* a dictionary"
    if len(ids_only) > len(set(ids_only)):
        # The expected case on a multi-dictionary headword.
        assert len({d for d, _ in minted}) > 1
