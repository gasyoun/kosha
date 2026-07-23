"""W1b vocabulary-curriculum tests (H947).

Locks the acceptance bar from docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md
§W1b: monotone cumulative coverage, every curriculum lemma resolves to a
real committed dictionary card (no dead /w/ links), and lesson sizes match
the builder's --lesson-size contract.

Local-only-ish: requires data/frequency/vocab_curriculum.tsv +
data/frequency/vocab_drills.json to already be built
(scripts/build_vocab_curriculum.py) — both are committed release assets,
so this is a pure output-file check, no DB / no DCS dependency.
"""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_vocab_curriculum as bvc  # noqa: E402

TSV = ROOT / "data" / "frequency" / "vocab_curriculum.tsv"
DRILLS = ROOT / "data" / "frequency" / "vocab_drills.json"
APKG = ROOT / "data" / "frequency" / "vocab_curriculum.apkg"
CARDS_DIR = ROOT / "docs" / "cards"

pytestmark = pytest.mark.skipif(not TSV.exists(), reason="vocab_curriculum.tsv not built")


def _rows():
    return list(csv.DictReader(open(TSV, encoding="utf-8"), delimiter="\t"))


def test_nonempty():
    rows = _rows()
    assert len(rows) > 1000


def test_cumulative_coverage_is_monotone():
    rows = _rows()
    prev = -1.0
    for r in rows:
        cur = float(r["cumulative_pct"])
        assert cur >= prev, "cumulative_pct decreased at rank %s" % r["rank"]
        prev = cur


def test_every_lemma_resolves_to_a_real_card():
    rows = _rows()
    for r in rows:
        tok = bvc.card_token(r["lemma_slp1"])
        assert (CARDS_DIR / (tok + ".json")).exists(), \
            "no committed card for lemma %r (token %r) — dead /w/ link" % (r["lemma_slp1"], tok)
        assert r["card_href"].endswith(tok + ".html")


def test_lesson_sizes_correct():
    rows = _rows()
    lesson_size = 50
    by_lesson = {}
    for r in rows:
        by_lesson.setdefault(int(r["lesson"]), []).append(r)
    last_lesson = max(by_lesson)
    for lk, items in by_lesson.items():
        if lk == last_lesson:
            assert 1 <= len(items) <= lesson_size
        else:
            assert len(items) == lesson_size


def test_ranks_are_sequential_and_core_rank_is_sorted():
    rows = _rows()
    for i, r in enumerate(rows, 1):
        assert int(r["rank"]) == i
    core_ranks = [int(r["core_rank"]) for r in rows]
    assert core_ranks == sorted(core_ranks)


def test_card_token_roundtrip_matches_shared_convention():
    # exact twin of app/word_page.py::card_token — locks the encoding so a
    # future drift there doesn't silently break every card_href in this file
    assert bvc.card_token("BU") == "_42_55"
    assert bvc.card_token("kf") == "kf"


def test_drills_every_item_has_answer_and_evidence():
    data = json.loads(DRILLS.read_text(encoding="utf-8"))
    assert len(data["items"]) > 0
    for it in data["items"]:
        assert it["answer"], "item %s has no answer" % it["id"]
        assert it["evidence"], "item %s has no evidence" % it["id"]
        assert it["aspect"] == "vocabulary"
        assert it["type"] in ("recognition", "recall")


def test_apkg_written():
    assert APKG.exists()
    assert APKG.stat().st_size > 0


DRILLS_HTML = ROOT / "reading" / "vocabulary" / "drills" / "index.html"

pytestmark_drills_page = pytest.mark.skipif(
    not DRILLS_HTML.exists(), reason="vocabulary drills page not built")


@pytestmark_drills_page
def test_drills_page_built_and_sized():
    assert DRILLS_HTML.stat().st_size > 4 * 1024 * 1024


@pytestmark_drills_page
def test_drills_page_contains_all_items():
    html = DRILLS_HTML.read_text(encoding="utf-8")
    assert "VC-00001" in html
    assert "13334" in html or "VC-13334" in html


def test_mcq_choices_includes_answer_and_no_empty_choice():
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    import build_vocab_drills_page as bvdp
    import random

    rng = random.Random(20260714)
    choices = bvdp.mcq_choices(rng, "answer", ["a", "", "b", "answer", None])
    assert "answer" in choices
    assert "" not in choices
    assert None not in choices
    assert choices.count("answer") == 1


def test_build_payload_choices_always_include_answer():
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    import build_vocab_drills_page as bvdp

    data = json.loads(DRILLS.read_text(encoding="utf-8"))
    payload = bvdp.build_payload(data["items"], seed=20260714)
    assert len(payload) == len(data["items"])
    for it in payload:
        assert it["answer"] in it["choices"]
        assert "" not in it["choices"]
