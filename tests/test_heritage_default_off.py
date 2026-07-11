"""H696 -- R7 ruling enforcement: Heritage surplus forms are default-off.

The 10-07-2026 R7 ruling (Uprava docs/DECISIONS_roadmap_forks_2026H2.md)
ingests the ~928k Heritage-only surplus forms provenance-flagged
(`source='heritage'`, done by H111) and requires them OFF by default for
every visitor, surfaced only on explicit opt-in (`?heritage=1`).

Requires `data/db/kosha.db` built with `--stage forms` (incl. the heritage
feed). Test forms (stable in the DB):

  ABABis -- heritage-only witness (lemma ABA), no inflections row
  ABAhi  -- dcs witness (lemma ABA), no inflections row
"""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from app.main import app  # noqa: E402
from app.db import DB_PATH  # noqa: E402
import segmenter  # noqa: E402

client = TestClient(app)

HERITAGE_ONLY_FORM = "ABABis"
DCS_FORM = "ABAhi"


def _form_lemmas(form, heritage=None):
    url = f"/api/v1/form/{form}?in=slp1"
    if heritage is not None:
        url += f"&heritage={int(heritage)}"
    r = client.get(url)
    assert r.status_code == 200
    return r.json()["results"][0]["lemmas"]


def _analyze(form, heritage=None):
    url = f"/api/v1/forms/{form}/analyze?in=slp1"
    if heritage is not None:
        url += f"&heritage={int(heritage)}"
    r = client.get(url)
    assert r.status_code == 200
    return r.json()["results"][0]


# --- /api/v1/form ------------------------------------------------------------

def test_form_heritage_absent_by_default():
    lemmas = _form_lemmas(HERITAGE_ONLY_FORM)
    assert lemmas == [], f"heritage-only form leaked by default: {lemmas}"


def test_form_heritage_present_with_flag():
    lemmas = _form_lemmas(HERITAGE_ONLY_FORM, heritage=True)
    assert any(l["lemma_slp1"] == "ABA" and l["source"] == "heritage"
               for l in lemmas), lemmas


def test_form_native_sources_unaffected_by_flag():
    for flag in (None, True):
        lemmas = _form_lemmas(DCS_FORM, heritage=flag)
        assert any(l["lemma_slp1"] == "ABA" and l["source"] == "dcs"
                   for l in lemmas), (flag, lemmas)


# --- /api/v1/forms/{form}/analyze --------------------------------------------

def test_analyze_heritage_absent_by_default(monkeypatch):
    # segmentation off so the heritage-only form is a deterministic pure miss
    # (with vidyut vendored, stage 3 may otherwise attempt a compound split).
    monkeypatch.setattr(segmenter, "available", lambda: False)
    res = _analyze(HERITAGE_ONLY_FORM)
    assert res["resolved_by"] is None
    assert res["lemmas"] == []


def test_analyze_heritage_present_with_flag():
    res = _analyze(HERITAGE_ONLY_FORM, heritage=True)
    assert res["resolved_by"] == "forms"
    assert any(w["lemma_slp1"] == "ABA" and w["source"] == "heritage"
               for w in res["forms_witnesses"])


def test_analyze_never_serves_heritage_source_by_default():
    res = _analyze(HERITAGE_ONLY_FORM)
    for lemma in res.get("lemmas", []):
        assert "heritage" not in lemma.get("sources", []), res
    for w in res.get("forms_witnesses", []):
        assert w["source"] != "heritage", res


def test_analyze_native_witness_unaffected_by_flag():
    for flag in (None, True):
        res = _analyze(DCS_FORM, heritage=flag)
        assert res["resolved_by"] == "forms", (flag, res)
        assert any(w["lemma_slp1"] == "ABA" and w["source"] == "dcs"
                   for w in res["forms_witnesses"]), (flag, res)


# --- ingest verification (ruling count) ---------------------------------------

def test_heritage_surplus_ingested_at_ruled_count():
    """The R7 fork's surplus set (heritage_forms_oracle: heritage_only_forms
    = 928,262 distinct forms) is what sits behind source='heritage'."""
    import sqlite3
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        n = con.execute(
            "SELECT COUNT(DISTINCT form_slp1) FROM forms WHERE source='heritage'"
        ).fetchone()[0]
    finally:
        con.close()
    assert n == 928_262, f"expected the ruled ~928k surplus, got {n}"
