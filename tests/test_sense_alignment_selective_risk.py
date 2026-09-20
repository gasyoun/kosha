"""H5070 — selective risk and abstention over the scaled aligned-sense table.

What can go wrong here is quiet, so these are the checks that catch it:

1. the deck must be REPRODUCIBLE — a seeded selection that drifts is not a
   frozen population, and every figure downstream would describe a deck nobody
   can rebuild;
2. reused gold must stay OUT — pooling newly adjudicated records with the frozen
   H3910/W2 cards would double-count the same evidence;
3. the synthetic positive control must never reach a rate — a canary counted as
   a real error inflates the very number it exists to validate;
4. the estimator must re-weight — the deck is allocated equally per score band,
   so a raw deck fraction is not a population rate and must not be reported.

Checks that need the committed table degrade to a skip when it is absent, so the
fixture-tier CI stays green.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "data" / "concordance" / "sense_alignment.tsv"
SR = ROOT / "data" / "concordance" / "selective_risk"
SAMPLER = ROOT / "scripts" / "sample_sense_alignment_selective_risk.py"
SCORER = ROOT / "scripts" / "score_sense_alignment_selective_risk.py"

needs_table = pytest.mark.skipif(not TABLE.exists(), reason="sense_alignment.tsv absent")
needs_deck = pytest.mark.skipif(not (SR / "review_deck.tsv").exists(), reason="H5070 deck absent")


def _read_tsv(path):
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


# ------------------------------------------------------------------ reproducible

@needs_table
@needs_deck
def test_deck_reproduces_byte_for_byte(tmp_path):
    out = tmp_path / "redraw"
    subprocess.run([sys.executable, str(SAMPLER), "--out-dir", str(out)],
                   check=True, capture_output=True, encoding="utf-8")
    assert (out / "review_deck.tsv").read_bytes() == (SR / "review_deck.tsv").read_bytes()
    assert (out / "canary_key.json").read_bytes() == (SR / "canary_key.json").read_bytes()


@needs_deck
def test_population_freeze_pins_the_source_hash():
    freeze = json.loads((SR / "population_freeze.json").read_text(encoding="utf-8"))
    assert len(freeze["source_sha256"]) == 64
    assert freeze["population_aligned"] + freeze["population_unaligned"] == freeze["source_rows"]
    # abstention and coverage are the two halves of the same split
    assert abs(freeze["coverage"] + freeze["abstention"] - 1.0) < 1e-6


# ------------------------------------------------------------------- gold fence

@needs_deck
def test_reused_gold_is_excluded_from_the_new_deck():
    deck = {r["group_id"] for r in _read_tsv(SR / "review_deck.tsv")}
    for name in ("sense_alignment_acceptance_sample.tsv",
                 "sense_alignment_acceptance_sample_w2.tsv"):
        gold = ROOT / "data" / "concordance" / name
        if not gold.exists():
            pytest.skip(f"{name} absent")
        assert deck.isdisjoint({r["group_id"] for r in _read_tsv(gold)}), (
            f"newly adjudicated deck overlaps reused gold in {name}")


# -------------------------------------------------------------- positive control

@needs_deck
def test_canary_is_blind_in_the_deck_and_absent_from_every_rate():
    key = json.loads((SR / "canary_key.json").read_text(encoding="utf-8"))
    deck = _read_tsv(SR / "review_deck.tsv")
    canary = [r for r in deck if r["group_id"] == key["canary_group_id"]]
    assert len(canary) == 1, "the canary must be in the deck exactly once"
    # blind: it carries no marker distinguishing it from a real card
    assert canary[0]["synthetic"] == "no"

    scored = json.loads((SR / "selective_risk.json").read_text(encoding="utf-8"))
    assert scored["positive_control"]["verdict"] == "PASS"
    assert scored["newly_adjudicated_cards"] == len(deck) - 1, (
        "the synthetic control must be excluded from the adjudicated population")


@needs_deck
def test_canary_is_a_confident_wrong_match():
    key = json.loads((SR / "canary_key.json").read_text(encoding="utf-8"))
    assert float(key["declared_score"]) >= 0.70, "a control for confident error must sit in the high band"
    assert key["expected_verdict"] == "different"
    assert key["pwg_from_lemma"] != key["mw_apte_from_lemma"], "the two sides must be unrelated lemmas"


# ----------------------------------------------------------------- the estimator

@needs_deck
def test_rates_are_reweighted_not_raw_deck_fractions():
    scored = json.loads((SR / "selective_risk.json").read_text(encoding="utf-8"))
    rows = _read_tsv(SR / "adjudication_h5070.tsv")
    key = json.loads((SR / "canary_key.json").read_text(encoding="utf-8"))
    real = [r for r in rows if r["group_id"] != key["canary_group_id"]]
    raw = sum(1 for r in real if r["verdict"] == "different") / len(real)
    pooled = scored["risk_coverage"][0]["strict_wrong_rate"]
    # equal-per-band allocation over unequal strata: the weighted figure must not
    # coincide with the raw fraction, or the weighting was silently skipped
    assert abs(pooled - raw) > 1e-9, "pooled rate equals the raw deck fraction — weighting lost"


@needs_deck
def test_strict_rate_never_below_lenient_and_intervals_bracket_the_point():
    scored = json.loads((SR / "selective_risk.json").read_text(encoding="utf-8"))
    for scope in scored["risk_coverage"]:
        assert scope["strict_wrong_rate"] >= scope["lenient_wrong_rate"], scope["scope"]
        for kind in ("strict", "lenient"):
            lo, hi = scope[f"{kind}_ci95"]
            assert lo <= scope[f"{kind}_wrong_rate"] <= hi, f"{scope['scope']} {kind}"
            assert 0.0 <= lo <= hi <= 1.0


@needs_deck
def test_unreachable_pairs_are_split_out_of_the_error_rate():
    scored = json.loads((SR / "selective_risk.json").read_text(encoding="utf-8"))
    tax = scored["abstention_taxonomy"]
    assert "absent-dictionary" in tax, "the unreachable-pair class must be reported"
    assert scored["unreachable_pairs_absent_dictionary"] == tax["absent-dictionary"]
    # unreachable pairs live on the abstention side, never among aligned rows
    assert scored["unreachable_pairs_absent_dictionary"] <= scored["population_unaligned"]


@needs_deck
def test_every_deck_card_carries_a_verdict():
    deck = {r["card"] for r in _read_tsv(SR / "review_deck.tsv")}
    adj = _read_tsv(SR / "adjudication_h5070.tsv")
    assert {r["card"] for r in adj} == deck
    assert all(r["verdict"] in {"same", "different", "unsure"} for r in adj)
