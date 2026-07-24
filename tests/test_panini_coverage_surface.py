"""W4a / H1585 — panini coverage surface honesty checks.

Acceptance (VERIFICATION next-programme 1c-1…1c-3 + ARCHITECTURE §9):
- coverage shard (or HTML) names all four statuses distinctly
- dark classes are never collapsed into one bucket string
- trust-facing artefacts (report link, enumeration n, CSV path) present
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "concordance" / "panini" / "index.html"
COV_JS = ROOT / "concordance" / "panini" / "data" / "coverage.js"
TSV = ROOT / "data" / "concordance" / "sutra_coverage_map.tsv"

FOUR = (
    "lit",
    "dark-unattested",
    "dark-out-of-scope",
    "dark-engine-gap",
)


@pytest.mark.skipif(not HTML.is_file(), reason="panini index.html missing")
def test_html_names_all_four_coverage_statuses():
    text = HTML.read_text(encoding="utf-8")
    for s in FOUR:
        assert s in text, f"HTML must surface status {s!r} distinctly"
    # Forbidden collapse patterns that would merge dark classes
    assert "dark-only" not in text
    assert re.search(r"status\s*===\s*[\"']dark[\"']", text) is None


@pytest.mark.skipif(not HTML.is_file(), reason="panini index.html missing")
def test_html_trust_block_has_source_n_and_report():
    text = HTML.read_text(encoding="utf-8")
    assert "sutra_coverage_map.tsv" in text
    assert "SUTRA_COVERAGE_BUILD_REPORT.md" in text
    assert "3983" in text
    # CSV download affordance (house /viz-page)
    assert "sutra_coverage_map.tsv" in text and (
        "download" in text.lower() or "CSV" in text or "csv" in text
    )


@pytest.mark.skipif(not COV_JS.is_file(), reason="coverage.js not built yet")
def test_coverage_js_contains_four_statuses_and_stats():
    text = COV_JS.read_text(encoding="utf-8")
    assert "window.COVERAGE_MAP" in text
    assert "window.COVERAGE_STATS" in text
    for s in FOUR:
        assert f'"{s}"' in text or f"'{s}'" in text, f"coverage.js missing {s}"
    # Standing enumeration denominator
    assert "3983" in text or '"n":3983' in text.replace(" ", "")


@pytest.mark.skipif(not TSV.is_file(), reason="coverage TSV missing")
def test_coverage_tsv_four_statuses_never_collapsed():
    statuses = set()
    with TSV.open(encoding="utf-8") as f:
        header = f.readline()
        assert "status" in header
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 7:
                continue
            statuses.add(parts[6])
    for s in FOUR:
        # dark-engine-gap may be absent (0 rows) — still required as a named
        # class in the UI/shard, not necessarily present as a data row.
        if s == "dark-engine-gap":
            continue
        assert s in statuses, f"TSV missing expected status {s}"
    # No collapsed single "dark" class
    assert "dark" not in statuses
