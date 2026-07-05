"""kosha P4 Wave K2a (H181) -- reverse-lookup query pipeline pytest suite.

Covers the /api/v1/forms/{form}/analyze cascade: `inflections` -> `forms` ->
vidyut-cheda segmentation, the stem-normalization bridge, and verb-form ingest.

Requires `data/db/kosha.db` built with `--stage inflections` (nominals+verbs)
and `--stage stem_bridge`. The segmentation-fallback tests self-skip when the
vidyut data (data/vidyut/, KOSHA_VIDYUT_DATA) has not been vendored on this
machine -- the pipeline is designed to degrade gracefully there (RISKS.md R12),
so its absence is a skip, not a failure.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from app.main import app  # noqa: E402
import segmenter  # noqa: E402

client = TestClient(app)

SEG_AVAILABLE = segmenter.available()


def _result(form, scheme="slp1"):
    r = client.get(f"/api/v1/forms/{form}/analyze?in={scheme}")
    assert r.status_code == 200
    return r.json()["results"][0]


# --- roadmap exit tests: all three must resolve to dictionary entries -------

def test_exit_bhagavan_resolves_to_entry():
    """bhagavAn (bare form) -> inflections -> the m_vat stem, canonicalized to
    one lemma `Bagavat` that IS a dictionary headword."""
    res = _result("BagavAn")
    assert res["resolved_by"] == "inflections"
    lemmas = [l for l in res["lemmas"] if l["has_entry"]]
    assert any(l["lemma_slp1"] == "Bagavat" for l in lemmas)


def test_exit_ramena_resolves_to_entry():
    """rAmeRa (inflected) -> instr-sg of rAma, a dictionary headword."""
    res = _result("rAmeRa")
    assert res["resolved_by"] == "inflections"
    assert any(l["lemma_slp1"] == "rAma" and l["has_entry"] for l in res["lemmas"])


def test_exit_dharmaksetre_resolves_to_entry():
    """dharmakSetre (sandhied compound). NB (documented deviation from the
    H181 brief's assumption): the compound `Darmakzetra` is itself a Cologne
    inflection stem WITH dictionary entries, so it resolves at stage 1 rather
    than falling through to the vidyut segmentation fallback. The roadmap exit
    bar is "resolve to entries" -- which it does. The segmentation path is
    exercised by test_segmentation_* below on a form that genuinely misses
    both tables."""
    res = _result("Darmakzetre")
    assert res["resolved_by"] == "inflections"
    assert any(l["lemma_slp1"] == "Darmakzetra" and l["has_entry"] for l in res["lemmas"])


# --- verb-form ingest (K2a) --------------------------------------------------

def test_verb_form_now_resolves():
    """Bavati = 3sg present active of BU -- verbs are ingested in K2a, so this
    now resolves (it was an out-of-scope miss in K1)."""
    res = _result("Bavati")
    verb = [a for a in res["analyses"] if a["lemma_slp1"] == "BU"]
    assert verb, f"BU verb parse expected among {res['analyses']}"
    a = verb[0]
    assert a["model"] == "v_1"
    assert a["person"] == "3"
    assert a["number"] == "sg"
    assert a["tense"] == "pre"
    assert a["voice"] == "active"
    assert a["case"] is None and a["gender"] is None


def test_verb_imperfect_augment():
    """aBavat = 3sg imperfect of BU (the augment a- + Bavat)."""
    res = _result("aBavat")
    a = [x for x in res["analyses"] if x["lemma_slp1"] == "BU"]
    assert a and a[0]["tense"] == "ipf"


def test_every_analysis_has_resolved_by_provenance():
    res = _result("rAmeRa")
    assert res["analyses"]
    assert all(a["resolved_by"] == "inflections" for a in res["analyses"])


# --- stem-normalization bridge (K2a deliverable 2) ---------------------------

def test_stem_bridge_unifies_bhagavat_bhagavant():
    """The named exit example: `Bagavant` (the DCS/forms spelling) and
    `Bagavat` (the Cologne/inflections spelling) are ONE lexeme. The bridge
    canonicalizes the strong stem to the weak one; every analysis of BagavAn
    carries canonical_slp1 == 'Bagavat', so the unified answer is a single
    lemma, never a Bagavat/Bagavant split."""
    res = _result("BagavAn")
    assert all(a["canonical_slp1"] == "Bagavat" for a in res["analyses"])
    assert [l["lemma_slp1"] for l in res["lemmas"]].count("Bagavat") == 1
    assert "Bagavant" not in [l["lemma_slp1"] for l in res["lemmas"]]


# --- segmentation fallback (K2a deliverable 1.3, vidyut-cheda) ---------------

@pytest.mark.skipif(not SEG_AVAILABLE, reason="vidyut data not vendored (data/vidyut/)")
def test_segmentation_splits_sandhied_string():
    """tattvamasi genuinely misses both tables -> vidyut-cheda splits it into
    tattvam + asi, each re-resolved to a dictionary lemma."""
    res = _result("tattvamasi")
    assert res["resolved_by"] == "segmentation"
    assert res["segments"], "expected sandhi segments"
    seg_texts = {s["text"] for s in res["segments"]}
    assert "tattvam" in seg_texts
    # tattva is a real headword surfaced through the split.
    assert any(l["lemma_slp1"] == "tattva" and l["has_entry"] for l in res["lemmas"])


@pytest.mark.skipif(not SEG_AVAILABLE, reason="vidyut data not vendored (data/vidyut/)")
def test_segmentation_records_provenance():
    res = _result("tattvamasi")
    all_lemmas = [l for s in res["segments"] for l in s["lemmas"]]
    assert all_lemmas
    assert all("segmentation" in l["resolved_by"] for l in all_lemmas)


def test_segmentation_unavailable_degrades_gracefully(monkeypatch):
    """When vidyut data is absent, a both-tables miss is an honest miss with
    resolved_by null -- never a crash and never a fabricated answer (R12)."""
    monkeypatch.setattr(segmenter, "available", lambda: False)
    res = _result("qwxzqwxzqwxz")  # misses inflections + forms
    assert res["resolved_by"] is None
    assert res["lemmas"] == []


# --- honest miss -------------------------------------------------------------

def test_pure_miss_returns_null_resolved_by():
    res = _result("zzznonexistentzzz")
    assert res["resolved_by"] is None
    assert res["lemmas"] == []
