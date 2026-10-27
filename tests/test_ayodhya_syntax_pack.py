"""Ayodhyā 1 syntax reader contract (26-10-2026 grill D0–D7)."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "reading" / "data" / "ayodhya-1.json"
HTML = ROOT / "reading" / "index.html"

pytestmark = pytest.mark.skipif(not PACK.exists(), reason="Ayodhyā syntax pack not built")


@pytest.fixture(scope="module")
def payload():
    return json.loads(PACK.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tokens(payload):
    return [t for s in payload["sentences"] for t in s["tokens"]]


def test_headline_counts(payload, tokens):
    st = payload["stats"]
    assert len(payload["sentences"]) == st["sentences"] == 46
    assert len(tokens) == st["tokens"] == 476
    assert sum(t["head"] is not None for t in tokens) == st["dependency_tokens"] == 468
    assert sum(s["has_dependencies"] for s in payload["sentences"]) == st["dependency_sentences"] == 44
    assert sum(t["head"] is None for t in tokens) == st["unannotated_tokens"] == 8


def test_surface_projection_and_ud_are_reversible(payload, tokens):
    for t in tokens:
        expected = {"root": "predicate", "nsubj": "subject", "obj": "object", "iobj": "object",
                    "cop": "predicate_support", "aux": "predicate_support"}.get(t["deprel"])
        assert t["surface_role"] == expected
        if t["head"] is not None:
            assert isinstance(t["head"], int)
    assert sum(t["surface_role"] == "predicate" for t in tokens) == 44
    assert sum(t["surface_role"] == "subject" for t in tokens) == 26
    assert sum(t["surface_role"] == "object" for t in tokens) == 34


def test_cpd_is_not_a_ninth_case(payload, tokens):
    real_cases = {"Nom", "Acc", "Ins", "Dat", "Abl", "Gen", "Loc", "Voc"}
    assert real_cases <= set(payload["syntax"]["case_labels"])
    assert payload["syntax"]["case_labels"]["Cpd"] == "Член композита"
    assert all(t["case_label"] == "Член композита" for t in tokens if t["case"] == "Cpd")


def test_gloss_provenance(payload, tokens):
    assert sum(t["gloss_source"] == "WordSem" for t in tokens) == 217
    assert sum(t["gloss_source"] == "lemma-fallback" for t in tokens) == 259
    assert all(t["wordsem"] for t in tokens if t["gloss_source"] == "WordSem")
    assert all("wordsem" not in t for t in tokens if t["gloss_source"] == "lemma-fallback")


def test_grincer_is_validated_link_only(payload):
    linked = [s for s in payload["sentences"] if "parallel" in s]
    assert len(linked) == 26
    assert all(s["parallel"]["mode"] == "link-only" for s in linked)
    assert all(s["parallel"]["match_score"] >= 0.45 for s in linked)
    assert all("text" not in s["parallel"] for s in linked)
    assert all("ru" not in s for s in payload["sentences"])
    passages = [int(s["parallel"]["passage"].split(".")[1]) for s in linked]
    assert passages == sorted(passages)
    by_dcs = {s["dcs"]: s["parallel"]["passage"] for s in linked}
    assert by_dcs["dcs:116062_1"] == "1.2"
    assert by_dcs["dcs:116065_1"] == "1.3"
    assert by_dcs["dcs:116126_1"] == "1.50"
    for sent_id in ("dcs:116053_1", "dcs:116054_1", "dcs:116055_1", "dcs:116057_1",
                    "dcs:116059_1", "dcs:116061_1", "dcs:116061_2"):
        assert sent_id not in by_dcs


def test_no_grincer_translation_text_in_payload():
    raw = PACK.read_text(encoding="utf-8")
    assert "За Бхаратой" not in raw
    assert "Верный братской дружбе" not in raw


def test_renderer_hooks_are_additive():
    text = HTML.read_text(encoding="utf-8")
    for needle in ('src="data/ayodhya-1.js"', 'id="syntaxtoggle"', 'id="mode-surface"',
                   'id="mode-ud"', 'id="tokdetail"', 'case-cpd', 'related-head',
                   'related-dependent', 'setSyntaxMode'):
        assert needle in text
    assert 'data/nala-1.js' in text
    assert 'data/gita-18.js' in text
