"""H1590 — D4 static-head selection for build_word_pages.py.

Locks: measure N at 95% from lemma_frequency; --head / --coverage select only
frequency-ranked lemmas that have cards; full-set mode still returns all attested.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "app"))

from build_word_pages import (  # noqa: E402
    measure_head_n,
    select_head_tokens,
    card_token,
    harvest_reading_pack_tokens,
)

LEMMA_FREQ = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
ATTESTED = ROOT / "docs" / "js" / "data" / "attested_keys.json"
CARDS = ROOT / "docs" / "cards"

pytestmark = pytest.mark.skipif(
    not LEMMA_FREQ.exists() or not ATTESTED.exists(),
    reason="lemma_frequency.tsv or attested_keys.json missing",
)


def test_measure_head_n_at_95_is_11148():
    m = measure_head_n(freq_path=LEMMA_FREQ, coverage=0.95)
    assert m["n"] == 11148
    assert m["coverage_achieved"] >= 0.95
    assert abs(m["coverage_achieved"] - 0.95) < 0.001
    assert m["tokens_total"] == 4550704
    assert m["lemmas_with_count"] == 59282


def test_select_head_coverage_only_cards_and_bounded():
    attested = json.loads(ATTESTED.read_text(encoding="utf-8"))["tokens"]
    tokens, meta = select_head_tokens(
        attested, CARDS, coverage=0.95, freq_path=LEMMA_FREQ)
    assert meta["mode"] == "d4_head"
    assert meta["head_n"] == 11148
    assert meta["head_with_card"] == len(tokens)
    assert meta["head_without_card"] >= 0
    assert meta["head_with_card"] + meta["head_without_card"] == 11148
    # Must be a proper subset of the full card set (D4 head < full 50k).
    assert len(tokens) < len(attested)
    assert len(tokens) > 1000
    # Every selected token has a card file.
    for tok in tokens[:20]:
        assert (CARDS / f"{tok}.json").exists()


def test_select_head_explicit_n():
    attested = json.loads(ATTESTED.read_text(encoding="utf-8"))["tokens"]
    tokens, meta = select_head_tokens(
        attested, CARDS, head_n=100, freq_path=LEMMA_FREQ)
    assert meta["head_n"] == 100
    assert len(tokens) <= 100
    assert meta["head_with_card"] + meta["head_without_card"] == 100
    # Top rank is ca → card token "ca"
    assert card_token("ca") in tokens or not (CARDS / "ca.json").exists()


def test_select_all_attested_when_no_head():
    attested = json.loads(ATTESTED.read_text(encoding="utf-8"))["tokens"]
    tokens, meta = select_head_tokens(attested, CARDS)
    assert meta["mode"] == "all_attested"
    assert tokens == list(attested)


def test_harvest_reading_pack_tokens_from_fixture(tmp_path):
    (tmp_path / "gita.js").write_text(
        '{"href": "../w/vac.html"}, "../w/_42_55.html"', encoding="utf-8")
    (tmp_path / "skip.bin").write_bytes(b"../w/nope.html")
    toks = harvest_reading_pack_tokens(tmp_path)
    assert toks == ["_42_55", "vac"]
