#!/usr/bin/env python
"""H1493 — Gītā prose interlinear view acceptance tests."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
TSV = REPO / "data" / "gita" / "gita_prose.tsv"
JS = REPO / "reading" / "data" / "gita_prose.js"
READER = REPO / "reading" / "index.html"
MANIFEST = REPO / "data" / "manifest" / "datasets.json"
META = REPO / "docs" / "data-statements" / "gita-prose.meta.md"


def test_tsv_exists_and_has_blocks():
    assert TSV.exists(), "run scripts/extract_gita_prose.py"
    rows = list(csv.DictReader(TSV.open(encoding="utf-8"), delimiter="\t"))
    assert len(rows) >= 500, f"expected hundreds of prose blocks, got {len(rows)}"
    assert {"verse_label", "verse_keys", "n_lines", "text"} <= set(rows[0].keys())
    # first verse of the Gītā should be present
    labels = {r["verse_label"] for r in rows}
    assert any(l.startswith("1.") for l in labels)
    # every row has non-empty text
    empty = [r for r in rows if not (r.get("text") or "").strip()]
    assert not empty


def test_js_shard_parses_and_covers_1_1():
    assert JS.exists()
    text = JS.read_text(encoding="utf-8")
    assert text.startswith("window.GITA_PROSE")
    # extract JSON object
    m = re.search(r"window\.GITA_PROSE\s*=\s*(\{.*\})\s*;\s*$", text, re.S)
    assert m, "could not parse GITA_PROSE assignment"
    data = json.loads(m.group(1))
    assert "1.1" in data
    assert "Dhṛtarāṣṭra" in data["1.1"] or "dhṛtarāṣṭra" in data["1.1"].lower()
    # range expansion: 1.4-6 block should cover 1.4, 1.5, 1.6 if present in TSV
    rows = list(csv.DictReader(TSV.open(encoding="utf-8"), delimiter="\t"))
    ranged = [r for r in rows if "-" in (r.get("verse_label") or "")]
    if ranged:
        keys = ranged[0]["verse_keys"].split("|")
        for k in keys:
            assert k in data


def test_reader_has_prose_toggle_and_loads_shard():
    html = READER.read_text(encoding="utf-8")
    assert 'src="data/gita_prose.js"' in html
    assert "prose" in html.lower()
    assert "GITA_PROSE" in html
    # mode toggle buttons
    assert "mode-words" in html or "Word-by-word" in html
    assert "mode-prose" in html or "Prose" in html


def test_manifest_and_data_statement():
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ids = {r["id"] for r in man["datasets"]}
    assert "gita-prose" in ids
    row = next(r for r in man["datasets"] if r["id"] == "gita-prose")
    assert row["tier"] == "public"
    assert META.exists()
    body = META.read_text(encoding="utf-8")
    assert "Mārcis Gasūns" in body or "Gasūns" in body
    assert "MIT" in body
