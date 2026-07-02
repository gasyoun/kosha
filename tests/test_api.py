"""kosha D4 pytest suite — the four kosha API v1 endpoints + /health, and
Salt facade parity for agni/indra/ka (PHASE1_PLAN.md D4's required check).

Requires data/db/kosha.db built (scripts/build_db.py, D1-D3). Local-only
(A3: local-first) — no CI wiring implied.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_meta():
    r = client.get("/api/v1/meta")
    assert r.status_code == 200
    body = r.json()
    assert body["counts"]["lemmas"] == 323425
    assert {s["dict"] for s in body["sources"]} == {"mw", "pwg", "ap90"}


def test_lemma_found():
    r = client.get("/api/v1/lemma/agni")
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) > 0
    assert all(e["dict"] in ("mw", "pwg", "ap90") for e in body["results"])
    assert all(e["sense_ids"] for e in body["results"])


def test_lemma_not_found():
    r = client.get("/api/v1/lemma/zzznonexistentzzz")
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "lemma_not_found"


def test_lemma_encoding_auto_detect():
    # deva, iast, slp1 for the same word all resolve to the same entry set
    slp1 = client.get("/api/v1/lemma/agni?in=slp1").json()["results"]
    iast = client.get("/api/v1/lemma/agni?in=iast").json()["results"]  # agni has no diacritics but scheme still explicit
    assert len(slp1) == len(iast) > 0


def test_form_bhagavan_resolves():
    r = client.get("/api/v1/form/BagavAn?in=slp1")
    assert r.status_code == 200
    lemmas = {l_["lemma_slp1"] for l_ in r.json()["results"][0]["lemmas"]}
    assert "Bagavant" in lemmas


def test_form_miss_returns_empty_not_error():
    r = client.get("/api/v1/form/zzznonexistentformzzz?in=slp1")
    assert r.status_code == 200
    assert r.json()["results"][0]["lemmas"] == []


def test_search_prefix_and_pagination():
    r = client.get("/api/v1/search?q=agn&mode=prefix&limit=5&offset=0")
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) == 5
    assert body["query"]["total"] > 5


def test_search_limit_over_200_rejected():
    r = client.get("/api/v1/search?q=a&limit=500")
    assert r.status_code == 400


def test_sense_roundtrip_from_lemma():
    lemma_r = client.get("/api/v1/lemma/agni")
    sense_id = lemma_r.json()["results"][0]["sense_ids"][0]
    r = client.get(f"/api/v1/sense/{sense_id}")
    assert r.status_code == 200
    result = r.json()["results"][0]
    assert result["sense_id"] == sense_id
    assert result["cite"]["text"] == sense_id


def test_sense_not_found():
    r = client.get("/api/v1/sense/mw.999999999.1@0.1.0-dev")
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "sense_not_found"


def test_sense_bad_id_format():
    r = client.get("/api/v1/sense/not-a-valid-id")
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Salt facade parity (PHASE1_PLAN.md D4 check): agni, indra, ka against real
# MW data. Ground truth: csl-apidev api1/salt_common.php id-minting logic
# (no live csl-apidev instance exists to hit — see data/SOURCES.md D4 note)
# plus doc/salt_api_handoff.md's documented counts/examples.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("headword,expected_count", [("agni", 10), ("indra", 17), ("ka", 31)])
def test_salt_entries_record_counts(headword, expected_count):
    r = client.get(f"/dicts/mw/restful/entries?query={headword}")
    assert r.status_code == 200
    entries = r.json()["data"]["entries"]
    assert len(entries) == expected_count
    ids = [e["id"] for e in entries]
    assert len(set(ids)) == len(ids), "Salt ids must be unique within a homonym group"


def test_salt_ka_homonym_ids_match_documented_subset():
    # doc/salt_api_handoff.md's illustrative example for 'ka': the 4
    # <info hui="N"/>-marked primary homonyms mint bare -N suffixes.
    r = client.get("/dicts/mw/restful/entries?query=ka")
    ids = {e["id"] for e in r.json()["data"]["entries"]}
    assert {"lemma-ka-1", "lemma-ka-2", "lemma-ka-3", "lemma-ka-4"} <= ids
    assert "lemma-ka-L41336.05" in ids  # doc-cited decimal-lnum fallback example


def test_salt_agni_l890_matches_documented_shape():
    r = client.get("/dicts/mw/restful/entries?query=agni")
    e890 = next(e for e in r.json()["data"]["entries"] if e["id"] == "lemma-agni-L890")
    assert e890["csl"]["page"] == "5"
    assert e890["csl"]["column"] == "1"
    assert e890["csl"]["accentedKey"] == "agni/"
    assert "Uṇ." in e890["csl"]["references"]


def test_salt_ids_roundtrip():
    r = client.get("/dicts/mw/restful/ids?ids=lemma-agni-L890&ids=lemma-agni-L891")
    assert r.status_code == 200
    ids = {e["id"] for e in r.json()["data"]["ids"]}
    assert ids == {"lemma-agni-L890", "lemma-agni-L891"}


def test_salt_ids_bare_lemma_returns_all_homonyms():
    r = client.get("/dicts/mw/restful/ids?ids=lemma-ka")
    assert r.status_code == 200
    assert len(r.json()["data"]["ids"]) == 31


def test_salt_unknown_dict():
    r = client.get("/dicts/zzz/restful/entries?query=agni")
    assert "error" in r.json()
