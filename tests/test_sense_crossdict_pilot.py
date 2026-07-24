"""W2 / H1587 — pilot cross-dict sense view acceptance."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "concordance" / "sense_pilot_headwords.tsv"
TSV = ROOT / "data" / "concordance" / "sense_crossdict_pilot.tsv"
HTML = ROOT / "concordance" / "senses" / "crossdict.html"
JS = ROOT / "concordance" / "senses" / "data" / "crossdict_pilot.js"


@pytest.mark.skipif(not TSV.is_file(), reason="crossdict pilot TSV not built")
def test_pilot_row_count_covers_all_headwords():
    with PILOT.open(encoding="utf-8", newline="") as f:
        pilot = {(r["slp1"] or "").strip() for r in csv.DictReader(f, delimiter="\t")}
    with TSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    lemmas = {(r["lemma_slp1"] or "").strip() for r in rows}
    missing = pilot - lemmas
    assert not missing, f"pilot lemmas missing from crossdict TSV: {sorted(missing)[:10]}"
    # TSV may have >1 row per lemma (per PWG sense); lower bound = pilot size
    assert len(rows) >= len(pilot)


@pytest.mark.skipif(not TSV.is_file(), reason="crossdict pilot TSV not built")
def test_nagadanta_has_distinct_pwg_ab():
    with TSV.open(encoding="utf-8", newline="") as f:
        rows = [
            r
            for r in csv.DictReader(f, delimiter="\t")
            if r.get("lemma_slp1") == "nAgadanta"
        ]
    assert rows, "nAgadanta must be in pilot output"
    sids = {r["pwg_sense_id"] for r in rows if r.get("pwg_sense_id")}
    assert "1a" in sids and "1b" in sids, f"expected PWG 1a/1b, got {sids}"


@pytest.mark.skipif(not HTML.is_file(), reason="crossdict HTML missing")
def test_viewer_declares_pilot_only_and_three_columns():
    text = HTML.read_text(encoding="utf-8")
    assert "pilot" in text.lower()
    assert "PWG" in text and "MW" in text and "Apte" in text
    assert "500" in text


@pytest.mark.skipif(not JS.is_file(), reason="crossdict JS missing")
def test_js_payload_has_nagadanta():
    text = JS.read_text(encoding="utf-8")
    assert "nAgadanta" in text
    assert "CROSSDICT" in text
