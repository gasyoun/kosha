"""Tests for the H539 Type-D extension: concordance_core record shapes +
typed_link_lint.py, against TYPED_LINK_ID_GRAMMAR.md §4a/§4b fixtures."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "typed_link"

sys.path.insert(0, str(SCRIPTS))
import concordance_core as cc  # noqa: E402


def test_record_fields_renamed_not_reordered():
    # RECORD_FIELDS keeps its 8-field position order (Type-B consumers write
    # values positionally) — only corpus_locus/corpus_text_id are renamed.
    assert cc.RECORD_FIELDS == [
        "anchor_type", "anchor_id", "anchor_key_slp1", "target_locus",
        "source_dataset", "match_method", "confidence", "evidence_count",
    ]


def test_type_d_record_fields_is_superset():
    for f in cc.RECORD_FIELDS:
        assert f in cc.TYPE_D_RECORD_FIELDS
    assert "link_type" in cc.TYPE_D_RECORD_FIELDS
    assert "date" in cc.TYPE_D_RECORD_FIELDS


def test_new_tiers_above_exact_in_trust():
    assert cc.TIER_CONFIDENCE["id-link"] > cc.TIER_CONFIDENCE["exact"]
    assert cc.TIER_CONFIDENCE["curated"] > cc.TIER_CONFIDENCE["exact"]


def test_normalize_record_handles_both_shapes():
    type_b_row = {
        "anchor_type": "dict-entry", "anchor_id": "BU", "anchor_key_slp1": "BU",
        "corpus_locus": "lemma:12", "corpus_text_id": "-",
        "match_method": "exact", "confidence": "0.95", "evidence_count": "3",
    }
    view = cc.normalize_record(type_b_row)
    assert view["target_locus"] == "lemma:12"
    assert view["source_dataset"] == "-"
    assert view["link_type"] is None
    assert view["date"] is None

    type_d_row = {
        "anchor_type": "id-gra", "anchor_id": "gra:3983", "anchor_key_slp1": "tva",
        "target_locus": "vedaweb:1.1.6:668bbf5c1e18769f3d9aafc3",
        "link_type": "translation-witness",
        "source_dataset": "VisualDCS/non-derived/vedaweb/grassmann_de_1876_1877.json",
        "match_method": "id-link", "confidence": "0.99", "evidence_count": "4712",
        "date": "08-07-2026",
    }
    view = cc.normalize_record(type_d_row)
    assert view["target_locus"] == "vedaweb:1.1.6:668bbf5c1e18769f3d9aafc3"
    assert view["link_type"] == "translation-witness"


def _run_lint(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "typed_link_lint.py"), *args],
        capture_output=True, text=True,
    )


def test_lint_landed_fixtures_clean():
    r = _run_lint(str(FIXTURES / "typed_link_good.tsv"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "all clean" in r.stdout


def test_lint_negative_fixtures_fail():
    r = _run_lint(str(FIXTURES / "typed_link_bad.tsv"))
    assert r.returncode == 1
    assert "URL host" in r.stdout
    assert "no known prefix" in r.stdout
    assert "not DD-MM-YYYY" in r.stdout
