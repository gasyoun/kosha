"""kosha P3 pytest suite -- evidence layer (IMPLEMENTATION_PLAN.md P3,
EVAL_PLAN.md T-UC4). Requires data/db/kosha.db built through
`scripts/build_db.py --stage evidence` (needs lemmas + forms already
populated). Local-only (A3), same convention as tests/test_api.py.

Covers the P3 exit check verbatim:
    "dharma shows band + counts + >=1 attested example; ranking measurably
    changes for a 20-query sample; provenance label on every badge."
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.main import app  # noqa: E402

client = TestClient(app)


def test_dharma_evidence_band_counts_example():
    r = client.get("/api/v1/lemma/dharma?in=iast")
    assert r.status_code == 200
    entry = r.json()["results"][0]
    ev = entry["evidence"]
    assert ev["band"] == 1  # rank_all=36 <= 500, see scripts/build_evidence.py band thresholds
    assert ev["count_all"] is not None and ev["count_all"] > 0
    assert ev["rank_all"] == 36
    assert ev["example"] is not None
    assert ev["example"]["sa"]
    assert ev["example"]["source"]


def test_evidence_provenance_label_on_every_badge():
    r = client.get("/api/v1/lemma/dharma?in=iast")
    ev = r.json()["results"][0]["evidence"]
    assert len(ev["badges"]) >= 4
    for badge in ev["badges"]:
        assert badge["source"], f"badge {badge['field']} missing a provenance source"
        assert "field" in badge and "value" in badge and "label" in badge


def test_evidence_negative_no_attestation_never_fabricates():
    # ABAsaH (aabhaasah) carries no DCS frequency signal at all (band 5,
    # rank_all IS NULL in the DB) -- fail-closed per EVAL_PLAN.md rule 4:
    # "no attestation data", never a numeric 0 and never an invented example.
    r = client.get("/api/v1/lemma/ABAsaH?in=slp1")
    assert r.status_code == 200
    entry = r.json()["results"][0]
    ev = entry["evidence"]
    assert ev["band"] == 5
    assert ev["count_all"] is None  # never a fabricated 0
    assert ev["rank_all"] is None
    assert ev["example"] is None  # never an invented example
    # the badges still exist and still carry a (non-DCS) source label --
    # "no attestation data" is itself provenanced, not silently blank.
    count_badge = next(b for b in ev["badges"] if b["field"] == "count_all")
    assert count_badge["value"] is None
    assert count_badge["label"] == "no attestation data"
    assert count_badge["source"]
    genre_badge = next(b for b in ev["badges"] if b["field"] == "genre")
    assert genre_badge["value"] is None
    assert "not derivable" in genre_badge["label"]


def test_evidence_absent_lemma_still_fails_closed():
    # A lemma absent from DCS entirely but WITH a dict entry (band 5 path
    # via lemma_row not None) must not error and must not fabricate data.
    r = client.get("/api/v1/lemma/ABAsin?in=slp1")
    assert r.status_code == 200
    ev = r.json()["results"][0]["evidence"]
    assert ev["band"] == 5
    assert ev["count_all"] is None


# ---------------------------------------------------------------------------
# T-UC4 ranking check: a committed 20-headword sample spanning all 5 bands
# (selected by SQL: real dict headwords, 4 per band, sharing a common
# 3-4 char prefix within each band so /api/v1/search?mode=prefix returns
# >1 candidate per query -- see scripts/build_evidence.py band thresholds
# for how band is computed. Frozen list, not cherry-picked per run.)
# ---------------------------------------------------------------------------

SAMPLE_20 = [
    # (slp1 headword, expected band, search prefix)
    ("A", 1, "A"),
    ("AKyA", 1, "AKyA"),
    ("ASrama", 1, "ASra"),
    ("Adi", 1, "Adi"),
    ("AdA", 1, "AdA"),
    ("ABa", 2, "ABa"),
    ("ABaraRa", 2, "ABar"),
    ("ADA", 2, "ADA"),
    ("AQya", 2, "AQya"),
    ("ASA", 2, "ASA"),
    ("ABA", 3, "ABA"),
    ("ABAsa", 3, "ABAs"),
    ("ABAz", 3, "ABAz"),
    ("ABIra", 3, "ABIr"),
    ("ABU", 3, "ABU"),
    ("ABARaka", 4, "ABAR"),
    ("ABAs", 4, "ABAs"),
    ("ABAsana", 4, "ABAs"),
    ("ABAsura", 4, "ABAs"),
    ("ABAsaH", 5, "ABAs"),
]


@pytest.mark.parametrize("slp1,expected_band,_prefix", SAMPLE_20)
def test_sample_band_matches_committed_thresholds(slp1, expected_band, _prefix):
    r = client.get(f"/api/v1/lemma/{slp1}?in=slp1")
    assert r.status_code == 200
    ev = r.json()["results"][0]["evidence"]
    assert ev["band"] == expected_band, f"{slp1}: expected band {expected_band}, got {ev['band']}"


def test_search_ranking_measurably_changes_for_sample():
    """For each of the 20 sample queries' search prefix, frequency-weighted
    order (rank_all ascending, nulls last, per app/main.py search()) must
    differ from plain alphabetical order (the pre-P3 behavior) for a
    majority of queries that return >1 result -- proving the ranking change
    is real, not a no-op."""
    changed = 0
    compared = 0
    for slp1, _band, prefix in SAMPLE_20:
        r = client.get(f"/api/v1/search?q={prefix}&mode=prefix&limit=50")
        assert r.status_code == 200
        results = r.json()["results"]
        if len(results) < 2:
            continue
        compared += 1
        ranked_order = [row["slp1"] for row in results]
        alphabetical_order = sorted(ranked_order)
        if ranked_order != alphabetical_order:
            changed += 1
        # sortedness check (excluding the exact-key-match-first rule):
        # among non-exact-match rows, rank_all must be non-decreasing with
        # nulls last.
        non_exact = [row for row in results if row["slp1"] != prefix]
        keys = [(row["rank_all"] is None, row["rank_all"] or 0) for row in non_exact]
        assert keys == sorted(keys), f"prefix {prefix}: not rank-ordered: {results}"
    assert compared >= 10, "sample must yield >=10 multi-result queries to measure a change"
    assert changed / compared >= 0.5, (
        f"ranking should measurably differ from alphabetical for most of the "
        f"sample: only {changed}/{compared} queries changed"
    )


def test_search_exact_key_match_always_sorts_first():
    r = client.get("/api/v1/search?q=Darma&mode=prefix&limit=10")
    results = r.json()["results"]
    assert results[0]["slp1"] == "Darma"
