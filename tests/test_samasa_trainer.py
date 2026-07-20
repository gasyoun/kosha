"""Samasa (compound) trainer tests (H948) — VERIFICATION §W1c acceptance:
gold agreement, evidence on every item, type balance reported, curriculum
monotone, page cross-links to the hosted csl-guides quiz.
"""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

CURRICULUM = ROOT / "data" / "samasa" / "samasa_curriculum.tsv"
REFERENCE = ROOT / "data" / "samasa" / "reference.tsv"
DRILLS = ROOT / "data" / "samasa" / "samasa_drills.json"
GOLD = ROOT / "data" / "gita" / "gita_morphology_gold.tsv"
HTML_CURRICULUM = ROOT / "reading" / "samasa" / "curriculum" / "index.html"

pytestmark = pytest.mark.skipif(
    not DRILLS.exists(), reason="run scripts/build_samasa_trainer.py first")


def _load_json():
    return json.loads(DRILLS.read_text(encoding="utf-8"))


def _load_gold_gold_types():
    """verse|form -> raw compound tag, straight from the source TSV."""
    rows = csv.DictReader(open(GOLD, encoding="utf-8"), delimiter="\t")
    return {(r["verse"], r["form"]): r["compound"] for r in rows if r["compound"]}


def test_every_item_has_evidence():
    items = _load_json()["items"]
    assert items
    for it in items:
        assert it.get("evidence"), it["id"]


def test_gold_identify_matches_source_compound_column():
    from build_samasa_trainer import TYPE_MAP
    gold_types = _load_gold_gold_types()
    items = [i for i in _load_json()["items"] if i["type"] == "identify"]
    assert items
    checked = 0
    for it in items:
        # evidence = 'Bhagavadgītā <verse> (“<form>”), gold-tagged'
        verse = it["evidence"].split()[1]
        form = it["evidence"].split("“")[1].split("”")[0]
        raw = gold_types.get((verse, form))
        assert raw is not None, it
        assert TYPE_MAP[raw] == it["answer"], (it, raw)
        checked += 1
    assert checked == len(items)


def test_ambiguous_dual_tag_rows_excluded_from_identify():
    gold_types = _load_gold_gold_types()
    ambiguous_forms = {k for k, v in gold_types.items() if "/" in v}
    assert ambiguous_forms  # sanity: the source really does have dual-tag rows
    items = [i for i in _load_json()["items"] if i["type"] == "identify"]
    for it in items:
        verse = it["evidence"].split()[1]
        form = it["evidence"].split("“")[1].split("”")[0]
        assert (verse, form) not in ambiguous_forms


def test_type_balance_all_four_represented():
    from build_samasa_trainer import TYPE_NAME
    items = [i for i in _load_json()["items"] if i["type"] == "identify"]
    seen = {i["answer"] for i in items}
    missing = set(TYPE_NAME) - seen
    assert not missing, "compound classes with zero gold examples: %s" % missing


def test_curriculum_type_order_transparent_first():
    rows = list(csv.DictReader(open(CURRICULUM, encoding="utf-8"), delimiter="\t"))
    assert rows
    lessons_seen = []
    for r in rows:
        lesson = int(r["lesson"])
        if lesson not in lessons_seen:
            lessons_seen.append(lesson)
    types_in_lesson_order = []
    seen_types = set()
    for r in rows:
        if r["type"] not in seen_types:
            types_in_lesson_order.append(r["type"])
            seen_types.add(r["type"])
    assert types_in_lesson_order == ["KD", "TP", "BV", "DV"]


def test_curriculum_rank_monotone_and_dense():
    rows = list(csv.DictReader(open(CURRICULUM, encoding="utf-8"), delimiter="\t"))
    ranks = [int(r["rank"]) for r in rows]
    assert ranks == list(range(1, len(ranks) + 1))


def test_curriculum_cumulative_freq_pct_monotone_within_lesson():
    rows = list(csv.DictReader(open(CURRICULUM, encoding="utf-8"), delimiter="\t"))
    prev = -1
    for r in rows:
        cur = float(r["cumulative_freq_pct"])
        assert cur >= prev - 1e-9
        prev = cur


def test_every_split_item_answer_has_at_least_two_members():
    items = [i for i in _load_json()["items"] if i["type"] == "split"]
    assert items
    for it in items:
        members = it["answer"].split(" + ")
        assert len(members) >= 2, it


def test_reference_grouped_by_type_ranked():
    rows = list(csv.DictReader(open(REFERENCE, encoding="utf-8"), delimiter="\t"))
    by_type = {}
    for r in rows:
        by_type.setdefault(r["type"], []).append(int(r["rank_in_type"]))
    for t, ranks in by_type.items():
        assert ranks == list(range(1, len(ranks) + 1)), t


def test_curriculum_page_crosslinks_hosted_quiz():
    html = HTML_CURRICULUM.read_text(encoding="utf-8")
    assert "sanskrit-lexicon.github.io/csl-guides" in html
    assert "samasa-quiz" in html


def test_provenance_flag_present_and_split_from_correct_source():
    # NOTE: "dictionary" (MW uttarapada member_side/member_recall items,
    # PR #144) was added to this three-way split without updating this
    # assertion -- fixed here as a drive-by (H1398) rather than left red.
    items = _load_json()["items"]
    for it in items:
        assert it["provenance"] in ("gold", "corpus", "dictionary")
        if it["provenance"] == "corpus":
            assert it["type"] == "split"  # corpus items never carry a verified type
            assert it["source_dataset"] == "dcs-compound-dictionary"
        elif it["provenance"] == "dictionary":
            assert it["type"] in ("member_side", "member_recall")
            assert it["source_dataset"] in ("mw-derivations-uttarapada", "uttarapada-dict-vs-corpus")
        else:
            assert it["source_dataset"] == "gita-morphology-gold"


def test_member_drill_ranked_by_corpus_tokens():
    """H1398: member_side/member_recall drills rank compound final members
    (uttarapadas) by real DCS corpus attestation (corpus_tokens), not MW
    dictionary type-count -- H1328's report measured median Jaccard 0.00
    between the two rankings' first-member sets. The H1328-report-mandated
    junk stoplist (data/samasa/drill_weights.json member_stoplist) must keep
    particles/pronoun-stems/bare-roots/-tva/-tā out of the drilled pool,
    since ranking by corpus_tokens alone does not reliably drop them.
    """
    items = _load_json()["items"]
    member_recall = [i for i in items if i["type"] == "member_recall"]
    assert member_recall

    # every member_recall item's evidence embeds the corpus_tokens figure
    # it was ranked by -- extract and check the pool is sorted descending.
    import re
    tokens = []
    for it in member_recall:
        m = re.search(r"corpus-attested (\d+) tokens", it["evidence"])
        assert m, it["evidence"]
        tokens.append(int(m.group(1)))
    assert tokens == sorted(tokens, reverse=True), "member drill pool is not ranked by corpus_tokens"

    answers = {it["answer"] for it in member_recall}
    junk = {"ca", "eva", "vā", "tu", "hi", "api", "iva",
            "idam", "tad", "etad", "yad", "kim", "adas", "sva",
            "kṛ", "as", "bhū", "gam", "i", "dā", "dhā", "sthā", "han", "nī", "pā", "yā",
            "tva", "tā"}
    assert not (answers & junk), "stoplisted junk leaked into the drill pool: %s" % (answers & junk)

    # corpus-dominant, MW-dictionary-thin heads (H1328 report) should be
    # drillable now that the dictionary type-count floor no longer gates them.
    expected_corpus_dominant = {"ādi", "indra", "ātman", "ṛṣi"}
    missing = expected_corpus_dominant - answers
    assert not missing, "expected corpus-dominant heads missing from the ranked pool: %s" % missing
