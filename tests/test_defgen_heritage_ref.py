"""H2408 — guard tests for the Heritage second-reference eval harness.

The load-bearing safety property is the digest gate: the committed subset carries
SHA-256 digests instead of the (restricted, LGPLLR) Heritage gloss text, so the
scorer MUST refuse to run when the local Heritage file no longer produces the
glosses the subset was built from. Silently scoring against drifted text would
publish numbers whose reference nobody can reconstruct.

Falsification, not just happy-path: each test proves the gate FAILS on drifted
input, and the rights test proves no French gloss text leaked into the repo.
"""
import csv
import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
HERITAGE_DIR = REPO / "data" / "eval" / "defgen" / "heritage"
SUBSET = HERITAGE_DIR / "heritage_ref_subset.tsv"
META = HERITAGE_DIR / "heritage_ref_subset.meta.json"
SCORES = HERITAGE_DIR / "heritage_ref_scores.json"
ARMS = ["A0_random_floor", "A1_chat_ctx", "A2_chat_noctx", "A3_reasoner_ctx",
        "F1_fable_ctx"]


def load_module():
    """Import the harness without executing its CLI. Skips when the local
    SanskritLexicography sibling (restricted Heritage layer) is absent."""
    spec = importlib.util.spec_from_file_location(
        "defgen_heritage_ref", SCRIPTS / "defgen_heritage_ref.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec.loader.exec_module(mod)
    except FileNotFoundError as exc:  # .env / sibling missing
        pytest.skip("harness deps unavailable: %s" % exc)
    return mod


def read_subset():
    with io.open(SUBSET, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def test_subset_is_committed_and_nonempty():
    rows = read_subset()
    assert len(rows) == 333, "expected the frozen 333-item MW∩Heritage subset"
    meta = json.loads(META.read_text(encoding="utf-8"))
    assert meta["n_subset"] == len(rows)
    assert meta["n_frozen_sample"] == 500
    assert meta["n_subset"] + meta["n_skipped"] == 500


def test_no_heritage_gloss_text_is_committed():
    """Rights gate: the subset must carry digests, never the French gloss text."""
    header = SUBSET.read_text(encoding="utf-8").splitlines()[0].split("\t")
    assert "heritage_gloss_sha256" in header
    assert not any("gloss_fr" == h or h.endswith("_gloss_text") for h in header), header
    for row in read_subset():
        assert len(row["heritage_gloss_sha256"]) == 64
        assert int(row["heritage_gloss_words"]) >= 0


def test_digest_gate_accepts_the_real_join_and_refuses_a_drifted_one():
    """The gate must PASS on the committed subset and FAIL on tampered text —
    proving it is a real check, not a no-op."""
    mod = load_module()
    if not Path(mod.HERITAGE).exists():
        pytest.skip("local Heritage layer (restricted) not present")
    her = mod.load_heritage()
    subset = mod.load_subset()

    assert mod.verify_join(subset, her) == [], "committed subset must verify clean"

    victim = subset[0]["slp1"]
    drifted = dict(her)
    anchor, gloss = drifted[victim]
    drifted[victim] = (anchor, gloss + " DRIFT")
    bad = mod.verify_join(subset, drifted)
    assert victim in bad, "gate failed to notice a one-item gloss change"


def test_digest_gate_notices_a_missing_entry():
    mod = load_module()
    if not Path(mod.HERITAGE).exists():
        pytest.skip("local Heritage layer (restricted) not present")
    subset = mod.load_subset()
    her = mod.load_heritage()
    victim = subset[0]["slp1"]
    pruned = {k: v for k, v in her.items() if k != victim}
    assert victim in mod.verify_join(subset, pruned)


def test_recorded_digests_match_a_recomputation():
    """Digests in the subset must be reproducible from the local file, not stale."""
    mod = load_module()
    if not Path(mod.HERITAGE).exists():
        pytest.skip("local Heritage layer (restricted) not present")
    her = mod.load_heritage()
    for row in read_subset():
        got = hashlib.sha256(her[row["slp1"]][1].encode("utf-8")).hexdigest()
        assert got == row["heritage_gloss_sha256"], row["slp1"]


def test_scores_cover_every_arm_with_no_nulls():
    scores = json.loads(SCORES.read_text(encoding="utf-8"))
    assert scores["metrics"]["n"] == 333
    for arm in ARMS:
        assert arm in scores["metrics"]["arms"]
        assert scores["judge_fr"][arm]["n_scored"] == 333, arm
        assert scores["judge_fr"][arm]["mean_adequacy_fr"] is not None


def test_floor_gate_passes_and_ranking_is_reference_invariant():
    """The two headline claims of the report must be backed by the stored numbers."""
    scores = json.loads(SCORES.read_text(encoding="utf-8"))
    gate = scores["gates"]["floor_separation_fr"]
    assert gate["pass"] is True
    assert gate["min_system"] - gate["floor"] >= 1.0
    ranking = scores["mw_fr_judge_delta"]["_ranking"]
    assert ranking["identical"] is True
    assert ranking["by_judge_fr"][0] == "F1_fable_ctx"
    assert ranking["by_judge_fr"][-1] == "A0_random_floor"


def test_mw_premium_is_positive_for_every_system_arm_but_not_the_floor():
    """Finding 2: the premium is real for systems, not significant for the floor."""
    delta = json.loads(SCORES.read_text(encoding="utf-8"))["mw_fr_judge_delta"]
    for arm in ARMS:
        if arm == "A0_random_floor":
            assert delta[arm]["ci_excludes_zero"] is False
            continue
        assert delta[arm]["n_paired"] == 333, arm
        assert delta[arm]["mean_delta"] > 0, arm
        assert delta[arm]["ci_excludes_zero"] is True, arm
        assert delta[arm]["sign_test_p"] < 0.001, arm
