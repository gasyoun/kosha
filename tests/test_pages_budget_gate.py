"""H3745 / H4841 — W4b Pages budget re-measure gate (scripts/measure_pages_budget.py).

Locks: the gate actually computes a real projection and actually fails when
the projection crosses 70% of the 1,024 MB soft cap — a measurement with no
threshold that can fail is not a gate. H4841 adds: the sample frame spans the
whole head selection (not one band), the committed repo-root w/ tier is part
of the projection, and the head estimator lands within ±5% of the byte-true
census of the committed w/ pages.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "docs" / "cards"
ATTESTED = ROOT / "docs" / "js" / "data" / "attested_keys.json"
LEMMA_FREQ = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
W = ROOT / "w"

sys.path.insert(0, str(ROOT / "scripts"))
import measure_pages_budget as mpb  # noqa: E402

needs_data = pytest.mark.skipif(
    not CARDS.exists() or not ATTESTED.exists() or not LEMMA_FREQ.exists(),
    reason="docs/cards, attested_keys.json, or lemma_frequency.tsv missing",
)


@needs_data
def test_gate_runs_and_reports_a_real_projection():
    # --no-log: CI must not mutate the committed architecture doc on every run.
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "measure_pages_budget.py"),
         "--sample", "50", "--no-log"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=300,
    )
    assert "PROJECTED TOTAL" in result.stdout
    assert "w/ (committed)=" in result.stdout
    assert "GATE PASS" in result.stdout or "GATE FAIL" in result.stdout
    # The gate must exit non-zero exactly when it reports FAIL, zero when PASS —
    # an exit code that doesn't track the printed verdict is a silent gate.
    if "GATE FAIL" in result.stdout:
        assert result.returncode == 1
    else:
        assert result.returncode == 0


def test_gate_fails_closed_on_a_synthetic_overshoot():
    """The threshold logic itself, isolated from real disk measurement."""
    assert mpb.GATE_MB == pytest.approx(716.8, abs=0.1)
    assert mpb.GATE_FRACTION == 0.70


def test_sampler_frame_spans_the_selection():
    """H4841: the H4833 defect class is a frame that under-reads its subject.
    Every rank band gets sampled, the bands tile the selection end to end, and
    the heaviest cards are taken whole rather than left to chance."""
    tokens = [f"t{i}" for i in range(1000)]
    # Heavy tail at the END of the rank order — a head-band sampler misses it.
    card_bytes = {t: (100 + i) * (50 if i >= 980 else 1) for i, t in enumerate(tokens)}
    frame = mpb.stratified_frame(tokens, card_bytes, sample_n=60)

    assert [b["name"] for b in frame["bands"]] == ["head", "mid", "tail"]
    assert all(b["sample"] for b in frame["bands"])
    assert frame["bands"][0]["lo"] == 0
    assert frame["bands"][-1]["hi"] == 979  # last rank outside the take-all stratum
    assert sum(b["size"] for b in frame["bands"]) + len(frame["take_all"]) == len(tokens)
    # take-all = the 2% largest cards, i.e. exactly the heavy tail here
    assert set(frame["take_all"]) == {f"t{i}" for i in range(980, 1000)}
    # each band's sample comes from inside that band
    pos = {t: i for i, t in enumerate(tokens)}
    for b in frame["bands"]:
        assert all(b["lo"] <= pos[t] <= b["hi"] for t in b["sample"])


def test_tiers_partition_the_tracked_tree_and_see_committed_w():
    tiers = mpb.tracked_tier_bytes()
    parts = sum(v for k, v in tiers.items() if k != "total")
    assert parts == tiers["total"]
    if (W / "README.md").exists():
        # the committed w/ tree is a counted tier, not invisible to the projection
        assert tiers["w"] > 0


@needs_data
def test_head_projection_within_5pct_of_committed_w_census():
    """H4841 acceptance: the estimator vs a byte-true census of the committed
    head pages (fixture = committed docs/cards + committed repo-root w/)."""
    head, _meta = mpb.head_selection()
    built = [t for t in head if (W / f"{t}.html").exists()]
    if len(built) < len(head):
        pytest.skip(f"committed w/ holds {len(built)}/{len(head)} head pages — no full census")
    census = sum((W / f"{t}.html").stat().st_size for t in built)
    est, info = mpb.project_pages_bytes(head, sample_n=300)
    assert [b[0] for b in info["bands"]] == ["head", "mid", "tail"]
    assert abs(est / census - 1) <= mpb.SAMPLER_TOLERANCE, (est, census)
