# H5296 — blind-packet metadata-leak gate tests.
# Gate contract: the rendered reviewer packet must not identify the planted
# control; every mutation class must be caught; the frozen SKD deck's TSV
# residual stays disclosed (never silently suppressed).
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts" / "check_blind_packet_leak.py"
RENDERER = ROOT / "scripts" / "render_selective_risk_deck.py"
SKD = ROOT / "data" / "concordance" / "selective_risk_skd"
SKD_DECK = SKD / "review_deck.tsv"
SKD_KEY = SKD / "canary_key.json"
FROZEN_H5070 = ROOT / "data" / "concordance" / "selective_risk"
SURFACE_MUTATIONS = ["unique_metadata", "ordering", "missing_gloss", "formatting"]


def run_gate(*extra, check=True):
    return subprocess.run(
        [sys.executable, str(GATE), "--deck", str(SKD_DECK), "--key", str(SKD_KEY), *extra],
        capture_output=True, text=True, encoding="utf-8", check=check)


def deck_rows(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def test_gate_green_on_the_active_skd_deck():
    """The committed SKD packet renders blind: no check fires, exit 0."""
    out = run_gate()
    assert "GREEN" in out.stdout
    assert "FAIL" not in out.stdout


def test_gate_reuse_green_on_frozen_h5070_deck_read_only():
    """The gate is reusable: the H5070 packet (untouched) also renders blind."""
    returncode = subprocess.run(
        [sys.executable, str(GATE), "--deck", str(FROZEN_H5070 / "review_deck.tsv"),
         "--key", str(FROZEN_H5070 / "canary_key.json")],
        capture_output=True, text=True, encoding="utf-8").returncode
    assert returncode == 0


@pytest.mark.parametrize("mutation", SURFACE_MUTATIONS)
def test_every_surface_mutation_is_caught_red(mutation):
    """Each leak class (metadata/missingness/ordering/formatting) trips the gate."""
    out = run_gate("--mutate", mutation)
    assert f"RED    mutation={mutation}" in out.stdout
    assert "GATE DEFECT" not in out.stdout


def test_legacy_hidden_metadata_specimen_is_caught_by_strict_layer():
    """The literal PR #631 arithmetic (stratum_eligible=0, share=0.000000)."""
    out = run_gate("--mutate", "legacy_hidden_metadata")
    assert "caught by field_tell,joint_tell" in out.stdout


def test_frozen_deck_tsv_residual_is_disclosed_not_hidden():
    """Strict layer reports the frozen deck's unique canary score; the default
    rendered-packet verdict stays GREEN — disclosed limitation, not a cover-up."""
    out = run_gate("--strict-deck-metadata")
    assert "field_tell" in out.stdout and "'score'" in out.stdout
    assert "GREEN" in out.stdout


def test_rendered_packet_never_carries_hidden_metadata():
    """#631 mechanism: labels/scores must stay outside the blind packet."""
    from importlib import util
    spec = util.spec_from_file_location("gate", GATE)
    gate = util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    cards = gate.render_deck(SKD_DECK, RENDERER)
    text = "\n".join(line for card in cards for line in card["lines"])
    for label in gate.HIDDEN_LABELS:
        assert label not in text


def test_deck_never_flags_the_control_and_key_stays_separate():
    """synthetic must read 'no' on every rendered row; the key carries the truth."""
    rows = deck_rows(SKD_DECK)
    key = json.loads(SKD_KEY.read_text(encoding="utf-8"))
    assert all((r.get("synthetic") or "").strip() == "no" for r in rows)
    canary = [r for r in rows if r["group_id"] == key["canary_group_id"]]
    assert len(canary) == 1
    assert canary[0]["card"] == "C025"


def test_expect_deck_sha256_binding():
    """The isolated re-test binds to the exact packet bytes."""
    import hashlib
    digest = hashlib.sha256(SKD_DECK.read_bytes()).hexdigest()
    out = run_gate("--expect-deck-sha256", digest)
    assert "GREEN" in out.stdout
    with pytest.raises(subprocess.CalledProcessError) as err:
        run_gate("--expect-deck-sha256", "0" * 64)
    assert err.value.returncode == 1
