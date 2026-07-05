"""kosha P4 Wave K1 pytest suite — the `/api/v1/forms/{form}/analyze`
endpoint over the `inflections` sidecar (scripts/build_inflections.py),
sourced verbatim from the Cologne csl-inflect tool's own generated tables
(ROADMAP_INFLECT_2026_2027.md D3).

Requires `data/db/kosha.db` built with `python scripts/build_db.py --stage
inflections` (in addition to the base D1-D3 build test_api.py requires).
Hand-verified against MWinflect/nominals/pysanskritv2/tables/calc_tables.txt
and MWinflect/nominals/pydecl/decline.py's fixed case/number `sup` order.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.main import app  # noqa: E402

client = TestClient(app)


def test_analyze_bhagavan_nom_sg():
    """bhagavAn (bare form, roadmap exit test #1) -- nom sg of the m_vat
    stem 'Bagavat', hand-verified against calc_tables.txt:
    `m_vat\tBaga-vat\t...\tBagavAn:...` (slot 0 = nom-sg)."""
    r = client.get("/api/v1/forms/BagavAn/analyze?in=slp1")
    assert r.status_code == 200
    analyses = r.json()["results"][0]["analyses"]
    assert analyses, "bhagavAn should resolve to at least one analysis"
    hit = [a for a in analyses if a["lemma_slp1"] == "Bagavat"]
    assert hit, f"expected lemma_slp1='Bagavat' among {analyses}"
    assert hit[0]["case"] == "nom"
    assert hit[0]["number"] == "sg"
    assert hit[0]["gender"] == "m"
    assert hit[0]["source"] == "cologne_mwinflect"


def test_analyze_ramena_instr_sg():
    """rAmeRa (inflected, roadmap exit test #2) -- instr sg of stem 'rAma',
    hand-verified: slot index 6 of the 24-slot m_a paradigm (nom x3, acc x3,
    then instr-sg)."""
    r = client.get("/api/v1/forms/rAmeRa/analyze?in=slp1")
    assert r.status_code == 200
    analyses = r.json()["results"][0]["analyses"]
    hit = [a for a in analyses if a["lemma_slp1"] == "rAma" and a["gender"] == "m"]
    assert hit, f"expected masculine rAma among {analyses}"
    assert hit[0]["case"] == "instr"
    assert hit[0]["number"] == "sg"


def test_analyze_dharmaksetre_sandhied_compound():
    """DarmakzetrE (sandhied compound, roadmap exit test #3) -- genuinely
    ambiguous in Sanskrit: loc-sg of both the m_a and n_a stems, plus
    nom/acc/voc-du of the n_a stem. The endpoint must surface every parse,
    not collapse to one."""
    r = client.get("/api/v1/forms/Darmakzetre/analyze?in=slp1")
    assert r.status_code == 200
    analyses = r.json()["results"][0]["analyses"]
    assert len(analyses) >= 2, "dharmakSetre is grammatically ambiguous"
    cases_seen = {(a["gender"], a["case"], a["number"]) for a in analyses}
    assert ("m", "loc", "sg") in cases_seen
    assert ("n", "loc", "sg") in cases_seen
    assert all(a["lemma_slp1"] == "Darmakzetra" for a in analyses)


def test_analyze_miss_returns_empty_not_error():
    r = client.get("/api/v1/forms/zzznonexistentformzzz/analyze?in=slp1")
    assert r.status_code == 200
    assert r.json()["results"][0]["analyses"] == []


def test_analyze_indeclinable_has_null_case_number():
    """Indeclinables (model='ind') carry no case/number/gender -- e.g.
    'akasmAt' (a-kasmAt), verified present verbatim in calc_tables.txt."""
    r = client.get("/api/v1/forms/akasmAt/analyze?in=slp1")
    assert r.status_code == 200
    analyses = r.json()["results"][0]["analyses"]
    assert analyses, "akasmAt should resolve"
    assert analyses[0]["model"] == "ind"
    assert analyses[0]["case"] is None
    assert analyses[0]["number"] is None


def test_analyze_verb_form_now_in_scope():
    """K2a (H181) ingested verbs, so Bavati (3sg pres of BU) now resolves --
    superseding K1's out-of-scope behavior. Full coverage lives in
    tests/test_reverse_lookup.py; this just guards that the K1 endpoint still
    surfaces the verb parse alongside any nominal homographs."""
    r = client.get("/api/v1/forms/Bavati/analyze?in=slp1")  # 3sg pres. of BU, a verb form
    assert r.status_code == 200
    analyses = r.json()["results"][0]["analyses"]
    assert any(a["lemma_slp1"] == "BU" and a["model"] == "v_1" for a in analyses)
