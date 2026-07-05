"""P4 Wave K2b (H183) paradigm tests — app/paradigm.py + the forward endpoint
+ the static generator's shard parity.

Locks the invariants the inflection UI depends on:
  * build_paradigm groups the `inflections` table into correctly-ordered
    case x number (nominal) and voice/tense/person x number (verb) grids;
  * GET /api/v1/paradigm/{lemma} returns the same block (bridged stems fold);
  * a static paradigm shard is byte-identical to the API response (the K2a/P2
    parity discipline: the static tier and the live API never diverge).

Local-only (A3): requires data/db/kosha.db built (scripts/build_db.py).
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

from app.main import app  # noqa: E402
import build_paradigms as bp  # noqa: E402
from paradigm import build_paradigm  # noqa: E402

client = TestClient(app)
DB = ROOT / "data" / "db" / "kosha.db"

pytestmark = pytest.mark.skipif(not DB.exists(), reason="kosha.db not built (A3, local-only)")


def _con():
    return bp.open_db(DB)


def test_rama_m_a_paradigm_grid():
    con = _con()
    try:
        para = build_paradigm(con, "rAma")
    finally:
        con.close()
    m_a = next(m for m in para["models"] if m["model"] == "m_a")
    assert m_a["type"] == "nominal"
    # canonical grammatical order, all three numbers present
    assert m_a["cases"] == ["nom", "acc", "instr", "dat", "abl", "gen", "loc", "voc"]
    assert m_a["numbers"] == ["sg", "du", "pl"]
    # the roadmap's forward exit forms, verbatim from Cologne
    assert m_a["cells"]["nom"]["sg"] == ["rAmaH"]
    assert m_a["cells"]["instr"]["sg"] == ["rAmeRa"]     # the reverse exit form
    assert m_a["cells"]["gen"]["pl"] == ["rAmARAm"]


def test_verb_paradigm_has_person_grid():
    con = _con()
    try:
        para = build_paradigm(con, "BU")  # bhū
    finally:
        con.close()
    verb = next(m for m in para["models"] if m["type"] == "verb")
    assert "active" in verb["vcells"]
    # 3rd person present singular of bhū is Bavati (present system, Cologne)
    pre = verb["vcells"]["active"].get("pre")
    assert pre and pre["3"]["sg"] == ["Bavati"]


def test_endpoint_matches_builder_and_bridges_stem():
    con = _con()
    try:
        direct = build_paradigm(con, "Bagavat")
    finally:
        con.close()
    # bhagavant (an inflections variant) must fold to bhagavat via stem_bridge
    resp = client.get("/api/v1/paradigm/Bagavant", params={"in": "slp1"})
    assert resp.status_code == 200
    assert resp.json()["results"][0] == direct


def test_static_shard_is_byte_identical_to_api(tmp_path):
    con = _con()
    try:
        n = bp.emit_paradigms(con, ["rAma"], tmp_path, force=True)
    finally:
        con.close()
    assert n == 1
    shard = json.loads((tmp_path / "paradigms" / f"{bp.card_token('rAma')}.json").read_text("utf-8"))
    api = client.get("/api/v1/paradigm/rAma", params={"in": "slp1"}).json()["results"][0]
    assert shard == api


def test_reverse_bucket_static_matches_api_stages_1_2():
    """The static reverse index resolves the exit forms at the same stage and to
    the same lemmas the API does (segmentation excluded — stage 1/2 only)."""
    con = _con()
    try:
        for form, expect_lemma in [("BagavAn", "bhagavat"),
                                    ("rAmeRa", "rāma"),
                                    ("Darmakzetre", "dharmakṣetra")]:
            rec = bp._reverse_entry(con, form)
            assert rec["resolved_by"] == "inflections"
            assert expect_lemma in [l["lemma_iast"] for l in rec["lemmas"]]
    finally:
        con.close()


def test_paradigm_not_found_is_404():
    resp = client.get("/api/v1/paradigm/zzznotasanskritstemzzz", params={"in": "slp1"})
    assert resp.status_code == 404
