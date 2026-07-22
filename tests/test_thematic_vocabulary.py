"""Thematic vocabulary axis tests (H1462).

Locks the acceptance bar: every kept lemma resolves to a real committed
H947 vocab_curriculum.tsv row (no dead /w/ links), rows are grouped into
the 20 genuinely thematic Amarakosa vargas only (the last 4 grammatical/
misc annexes are excluded), each theme is sorted by corpus core_rank
(most frequent first), and every drill item's distractors come from the
SAME theme as its answer.

Local-only-ish: requires data/frequency/thematic_vocabulary.tsv +
thematic_vocab_drills.json to already be built
(scripts/build_thematic_vocabulary.py) — pure output-file check, no
DB / no live AMAR-repo dependency at test time.
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_thematic_vocabulary as btv  # noqa: E402

TSV = ROOT / "data" / "frequency" / "thematic_vocabulary.tsv"
DRILLS = ROOT / "data" / "frequency" / "thematic_vocab_drills.json"
APKG = ROOT / "data" / "frequency" / "thematic_vocabulary.apkg"
CURRICULUM = ROOT / "data" / "frequency" / "vocab_curriculum.tsv"

pytestmark = pytest.mark.skipif(not TSV.exists(), reason="thematic_vocabulary.tsv not built")


def _rows():
    return list(csv.DictReader(open(TSV, encoding="utf-8"), delimiter="\t"))


def test_nonempty():
    rows = _rows()
    assert len(rows) > 500


def test_only_thematic_vargas_present():
    rows = _rows()
    vargas = {r["varga_id"] for r in rows}
    assert vargas <= btv.THEMATIC_VARGA_IDS
    assert len(vargas) == 20, "expected all 20 thematic vargas to contribute at least one row"


def test_every_lemma_resolves_to_a_real_curriculum_row():
    curriculum_lemmas = {r["lemma_slp1"] for r in
                          csv.DictReader(open(CURRICULUM, encoding="utf-8"), delimiter="\t")}
    for r in _rows():
        assert r["lemma_slp1"] in curriculum_lemmas, \
            "lemma %r has no H947 vocab_curriculum row -- dead /w/ link" % r["lemma_slp1"]


def test_rows_sorted_by_theme_then_rank():
    rows = _rows()
    by_theme = defaultdict(list)
    for r in rows:
        by_theme[r["varga_id"]].append(int(r["core_rank"]))
    for varga_id, ranks in by_theme.items():
        assert ranks == sorted(ranks), "ranks not ascending within varga %s" % varga_id


def test_no_duplicate_lemma_within_a_theme():
    rows = _rows()
    seen = defaultdict(set)
    for r in rows:
        assert r["lemma_slp1"] not in seen[r["varga_id"]], \
            "duplicate lemma %r within theme %r" % (r["lemma_slp1"], r["varga_id"])
        seen[r["varga_id"]].add(r["lemma_slp1"])


def test_drills_every_item_has_answer_and_evidence_and_theme_matched_distractors():
    data = json.loads(DRILLS.read_text(encoding="utf-8"))
    assert len(data["items"]) > 0
    by_theme_answers = defaultdict(set)
    for it in data["items"]:
        by_theme_answers[it["theme"]].add(it["answer"])
    for it in data["items"]:
        assert it["answer"], "item %s has no answer" % it["id"]
        assert it["evidence"], "item %s has no evidence" % it["id"]
        assert it["aspect"] == "vocabulary-thematic"
        assert it["type"] in ("recognition", "recall")
        for d in it["distractors"]:
            assert d in by_theme_answers[it["theme"]] or d == "", \
                "distractor %r in item %s is not drawn from theme %r" % (d, it["id"], it["theme"])


def test_apkg_written():
    assert APKG.exists()
    assert APKG.stat().st_size > 0


def test_parse_amar_finds_thematic_vargas():
    synsets = btv.parse_amar(btv.AMAR)
    found = {vid for vid, _eid, _lemmas in synsets}
    assert btv.THEMATIC_VARGA_IDS <= found
