#!/usr/bin/env python
"""H1588 — two-witness WSD acceptance tests (Wave 3)."""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FREQ = REPO / "data" / "frequency"
SCRIPTS = REPO / "scripts"
CACHE = FREQ / ".cache"
GITIGNORE = REPO / ".gitignore"


def test_scl_cache_path_gitignored():
    """Acceptance 3-1: cache path is gitignored."""
    text = GITIGNORE.read_text(encoding="utf-8")
    assert "data/frequency/.cache/" in text
    # git check-ignore when available
    r = subprocess.run(
        ["git", "check-ignore", "-v", "data/frequency/.cache/scl_sense_labels.jsonl"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert ".cache" in (r.stdout or "")


def test_wsd_core_primary_synset():
    sys.path.insert(0, str(SCRIPTS))
    from wsd_core import primary_synset, fold_of_sentence, GATE_THRESHOLD

    assert primary_synset("100006") == "100006"
    assert primary_synset("100006,96762") == "100006"
    assert primary_synset("") == ""
    assert fold_of_sentence(1) in ("train", "test")
    assert GATE_THRESHOLD == 0.70


def test_heldout_eval_artifact_gate():
    """Acceptance 3-2: held-out eval exists and records gate ≥70% when fused."""
    p = FREQ / "wsd_heldout_eval.json"
    if not p.exists():
        pytest.skip("run wsd_llm_arm.py first")
    blob = json.loads(p.read_text(encoding="utf-8"))
    ev = blob["eval"]
    assert "accuracy" in ev
    assert ev["n_test_scored"] > 0
    # When gate_pass, accuracy must clear the threshold
    if ev.get("gate_pass"):
        assert ev["accuracy"] >= 0.70


def test_estimated_rows_only_when_gate_passes():
    """Acceptance 3-3: estimated provenance rows exist iff gate passed."""
    eval_p = FREQ / "wsd_heldout_eval.json"
    sf = FREQ / "sense_frequency.tsv"
    if not eval_p.exists() or not sf.exists():
        pytest.skip("artifacts not built")
    gate = json.loads(eval_p.read_text(encoding="utf-8"))["eval"].get("gate_pass")
    n_est = 0
    with sf.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if (r.get("provenance") or "") == "estimated":
                n_est += 1
                assert r["layer"] == "mw"
    if gate:
        assert n_est > 0
    else:
        assert n_est == 0


def test_review_queue_exists():
    """Acceptance 3-5: review queue TSV present (non-empty or empty-with-reason in report)."""
    q = FREQ / "wsd_review_queue.tsv"
    report = FREQ / "wsd_fusion_report.md"
    if not q.exists():
        pytest.skip("run wsd_fuse.py first")
    with q.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    # file always has header; body may be empty
    assert q.stat().st_size > 0
    if len(rows) == 0:
        assert report.exists()
        body = report.read_text(encoding="utf-8")
        assert "empty" in body.lower() or "Review queue" in body


def test_cards_estimated_chip_not_blended():
    """Acceptance 3-4: estimated chip is separate from attested in word_page HTML."""
    sys.path.insert(0, str(REPO))
    from app import word_page as wp

    # synthetic: inject a lemma with both tiers into the already-loaded map
    wp._SENSE_FREQ["__h1588_test__"] = [
        {
            "sense_id": "x#1",
            "gloss": "test sense",
            "count": 10,
            "share": 1.0,
            "top_genre": "",
            "top_share": 0.0,
            "nonsastra": 1,
            "est_count": 42,
        }
    ]
    html = wp._sense_frequency_block("__h1588_test__")
    assert 'class="chip att"' in html
    assert "<b>10</b> in this sense" in html
    assert 'class="chip est"' in html
    assert "<b>42</b> estimated" in html
    # never a single blended total like 52 in this sense
    assert "52" not in html
    del wp._SENSE_FREQ["__h1588_test__"]


def test_no_scl_body_in_tree():
    """Acceptance 3-1 residual: no accidental SCL HTML dumps under frequency/."""
    if not FREQ.exists():
        return
    for p in FREQ.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".html", ".htm"}:
            pytest.fail(f"unexpected HTML under frequency/: {p}")
