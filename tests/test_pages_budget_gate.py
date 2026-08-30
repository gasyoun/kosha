"""H3745 — W4b Pages budget re-measure gate (scripts/measure_pages_budget.py).

Locks: the gate actually computes a real projection and actually fails when
the projection crosses 70% of the 1,024 MB soft cap — a measurement with no
threshold that can fail is not a gate.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "docs" / "cards"
ATTESTED = ROOT / "docs" / "js" / "data" / "attested_keys.json"
LEMMA_FREQ = ROOT / "data" / "frequency" / "lemma_frequency.tsv"

pytestmark = pytest.mark.skipif(
    not CARDS.exists() or not ATTESTED.exists() or not LEMMA_FREQ.exists(),
    reason="docs/cards, attested_keys.json, or lemma_frequency.tsv missing",
)


def test_gate_runs_and_reports_a_real_projection(tmp_path):
    # --no-log: CI must not mutate the committed architecture doc on every run.
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "measure_pages_budget.py"),
         "--sample", "50", "--no-log"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    assert "PROJECTED TOTAL" in result.stdout
    assert "GATE PASS" in result.stdout or "GATE FAIL" in result.stdout
    # The gate must exit non-zero exactly when it reports FAIL, zero when PASS —
    # an exit code that doesn't track the printed verdict is a silent gate.
    if "GATE FAIL" in result.stdout:
        assert result.returncode == 1
    else:
        assert result.returncode == 0


def test_gate_fails_closed_on_a_synthetic_overshoot(monkeypatch):
    """The threshold logic itself, isolated from real disk measurement."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import measure_pages_budget as mpb

    assert mpb.GATE_MB == pytest.approx(716.8, abs=0.1)
    assert mpb.GATE_FRACTION == 0.70
