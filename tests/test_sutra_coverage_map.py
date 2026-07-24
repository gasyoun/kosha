"""W3a sūtra-coverage map invariants (H1468) — structural, no re-harvest."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "data" / "concordance" / "sutra_coverage_map.tsv"
REPORT = ROOT / "data" / "concordance" / "SUTRA_COVERAGE_BUILD_REPORT.md"
FIRE = ROOT / "data" / "concordance" / "sutra_fire_set.tsv"

STATUSES = {
    "lit",
    "dark-unattested",
    "dark-out-of-scope",
    "dark-engine-gap",
}
ENUM_N = 3983  # vidyut-0.4.0 Ashtadhyayi load_sutras enumeration


def _rows():
    assert MAP.is_file(), f"missing {MAP}"
    with open(MAP, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def test_map_row_count_equals_named_enumeration():
    """3a-1 / 3a-2: every sūtra in the named enumeration has exactly one row."""
    rows = _rows()
    assert len(rows) == ENUM_N
    ids = [r["sutra_id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate sutra_id in map"


def test_four_statuses_never_collapsed_dark():
    """3a-3: four named statuses; no bare 'dark' bucket."""
    rows = _rows()
    dist = Counter(r["status"] for r in rows)
    assert set(dist) <= STATUSES
    assert "dark" not in dist
    # all four keys appear in the contract even if engine-gap is 0
    assert dist["lit"] > 0
    assert dist["dark-unattested"] > 0
    assert dist["dark-out-of-scope"] > 0
    assert dist.get("dark-engine-gap", 0) == 0
    assert sum(dist.values()) == ENUM_N


def test_dark_engine_gap_is_smallest():
    """3a-5: engine-gap is the smallest dark class (here 0)."""
    dist = Counter(r["status"] for r in _rows())
    de = dist.get("dark-engine-gap", 0)
    assert de <= dist["dark-unattested"]
    assert de <= dist["dark-out-of-scope"]


def test_percentages_in_report_cite_denominator():
    """3a-6 / 3a-8: report cites n/3983, not bare percentages only."""
    text = REPORT.read_text(encoding="utf-8")
    assert f"/{ENUM_N}" in text
    assert "221 : 55 : 3707 : 0" in text or "lit : dark-unattested" in text
    assert "dark-engine-gap" in text
    assert "never one" in text.lower() or "four statuses" in text.lower()


def test_out_of_scope_has_per_sutra_justification():
    """3a-4: scope_justification non-empty for every dark-out-of-scope row."""
    for r in _rows():
        if r["status"] == "dark-out-of-scope":
            assert r["scope_justification"].strip()
            assert "never-fires" in r["scope_justification"]


def test_lit_has_exemplars_dark_does_not():
    rows = _rows()
    for r in rows:
        forms = int(r["exemplar_forms"] or 0)
        if r["status"] == "lit":
            assert forms >= 1
        else:
            assert forms == 0


def test_fire_set_cache_present_and_matches_fire_classes():
    """Fire-set cache underpins --skip-harvest reproducibility (3a-7)."""
    assert FIRE.is_file()
    with open(FIRE, encoding="utf-8") as f:
        fire = {row["sutra_code"] for row in csv.DictReader(f, delimiter="\t")}
    rows = _rows()
    lit = {r["sutra_id"] for r in rows if r["status"] == "lit"}
    unatt = {r["sutra_id"] for r in rows if r["status"] == "dark-unattested"}
    assert lit | unatt == fire
    assert lit.isdisjoint(unatt)
