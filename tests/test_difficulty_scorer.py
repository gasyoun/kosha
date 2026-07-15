"""W2a difficulty-scorer tests (H949).

Locks the acceptance bar from docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md R5 +
the global contract: the scorer is a documented, tunable, honest ONE-estimator
that orders reading packs by difficulty. These are pure output-file + pure-function
checks (no DCS, no kosha.db) — the committed release assets
(data/difficulty/reading_pack_difficulty.tsv + the pure scoring functions) are all
that is exercised.

What is pinned:
  * every scored pack's composite and all four axes are in [0,1];
  * the composite equals the weighted sum of the axes (no drift between the number
    shown and the formula documented);
  * the ordering is by ascending difficulty (a graded sequence, easiest first);
  * scoring is deterministic (same pack in → same score out);
  * a non-UD pack (empty upos/morph) is SKIPPED, never fabricated into a score
    (the 'no fabricated signal' rule that made the Gītā packs mis-score at 1.0);
  * the known-hard kāvya (Kirātārjunīya) outranks the epic-narrative packs — a
    sanity anchor that the axes measure something real.
"""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_difficulty_scorer as bds  # noqa: E402

TSV = ROOT / "data" / "difficulty" / "reading_pack_difficulty.tsv"
JSONF = ROOT / "data" / "difficulty" / "reading_pack_difficulty.json"
WEIGHTS = ROOT / "data" / "difficulty" / "difficulty_weights.json"
METHODS = ROOT / "data" / "difficulty" / "METHODS.md"
MORPH = ROOT / "data" / "difficulty" / "morph_signature_freq.tsv"

pytestmark = pytest.mark.skipif(
    not TSV.exists(), reason="reading_pack_difficulty.tsv not built")

AXES = ("vocab", "sandhi", "morphology", "compound")


def _rows():
    with open(TSV, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def test_assets_present():
    for p in (TSV, JSONF, WEIGHTS, METHODS, MORPH):
        assert p.exists(), f"missing release asset {p.name}"


def test_axes_and_composite_in_range():
    for r in _rows():
        for a in AXES + ("difficulty",):
            v = float(r[a])
            assert 0.0 <= v <= 1.0, f"{r['slug']} {a}={v} out of [0,1]"


def test_composite_matches_weighted_sum():
    """The number in the table must equal the documented formula applied to the
    axes — otherwise the score is not the thing the methods note claims it is."""
    w, _raw = bds.load_weights()
    for r in _rows():
        sub = {a: float(r[a]) for a in AXES}
        expect = bds.composite(sub, w)
        assert abs(expect - float(r["difficulty"])) <= 1e-4, (
            f"{r['slug']}: table {r['difficulty']} != recomputed {expect}")


def test_ordering_is_ascending_difficulty():
    rows = _rows()
    diffs = [float(r["difficulty"]) for r in rows]
    assert diffs == sorted(diffs), "packs not ordered easiest→hardest"
    orders = [int(r["order"]) for r in rows]
    assert orders == list(range(1, len(rows) + 1)), "order column not 1..N contiguous"


def test_at_least_three_new_packs_scored():
    """The handoff bar: ≥3 new packs beyond Nala 1, ordered by the scorer."""
    slugs = {r["slug"] for r in _rows()}
    new = slugs - {"nala-1"}
    assert len(new) >= 3, f"need ≥3 packs beyond nala-1, scored {sorted(slugs)}"


def test_weights_tunable_and_normalise():
    doc = json.loads(WEIGHTS.read_text(encoding="utf-8"))
    assert set(doc["weights"]) == set(AXES)
    w, raw = bds.load_weights()
    assert abs(sum(w.values()) - 1.0) <= 1e-9, "normalised weights must sum to 1"
    assert all(v >= 0 for v in raw.values())


def test_scoring_is_deterministic():
    vr, mx = bds.load_vocab_ranks()
    ms, mn = bds.load_morph_shares()
    pack = {"sentences": [
        {"text": "bṛhadaśva uvāca", "tokens": [
            {"form": "bṛhadaśva", "lemma": "bṛhadaśva", "upos": "NOUN", "morph": "Nom Sing Masc"},
            {"form": "uvāca", "lemma": "vac", "upos": "VERB", "morph": "Sing p3 Past Ind"},
        ]}]}
    a = bds.score_pack(pack, vr, mx, ms, mn)
    b = bds.score_pack(pack, vr, mx, ms, mn)
    assert a == b
    for ax in AXES:
        assert 0.0 <= a[ax] <= 1.0


def test_non_ud_pack_is_skipped_not_fabricated():
    """A pack whose tokens carry no UD upos/morph (the Gītā-builder schema) must be
    detected as unscorable, not silently scored with morph=1.0 / compound=0."""
    non_ud = {"sentences": [{"text": "dharmakṣetre kurukṣetre", "tokens": [
        {"form": "dharma-kṣetre", "lemma": "dharma-kṣetra", "upos": "", "morph": ""},
        {"form": "kuru-kṣetre", "lemma": "kuru-kṣetra", "upos": "", "morph": ""},
    ]}]}
    assert bds.ud_coverage(non_ud) < 0.5
    ud = {"sentences": [{"text": "x", "tokens": [
        {"form": "x", "lemma": "x", "upos": "NOUN", "morph": "Nom Sing Masc"}]}]}
    assert bds.ud_coverage(ud) >= 0.5


def test_kavya_harder_than_epic_narrative():
    """Sanity anchor: Bhāravi's Kirātārjunīya (dense kāvya) must score harder than
    the Nala epic-narrative chapters. If this flips, an axis has broken."""
    d = {r["slug"]: float(r["difficulty"]) for r in _rows()}
    if "kiratarjuniya-1" in d and "nala-1" in d:
        assert d["kiratarjuniya-1"] > d["nala-1"], (
            f"kāvya {d['kiratarjuniya-1']} not > epic {d['nala-1']}")
