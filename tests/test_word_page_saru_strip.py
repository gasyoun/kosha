"""SanskritRussian glossary strip on /w/ (H2680).

One line under the headword. Not a dictionary tab. Public site-tier
fixture only (tests/fixtures/sanskritrussian/). Known hit: BU. Known
miss: zzqxw.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

from kosha.api.sr_gloss import (  # noqa: E402
    _PUBLIC_FILES,
    clear_caches,
    join_sr_strip,
    resolve_sr_root,
)
from app.word_page import render_word_page  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "sanskritrussian"


def _card(key="BU"):
    return {
        "query": {"key": key},
        "data_version": "0.1.0-test",
        "results": [
            {
                "dict": "mw",
                "headword": "bhū",
                "rendered_html": "<p>mw-body</p>",
                "scan_url": None,
                "evidence": {"band": 1, "band_label": "core"},
            },
            {
                "dict": "pwg",
                "headword": "bhū",
                "rendered_html": "<p>pwg-body-werden</p>",
                "scan_url": None,
                "evidence": {"band": 1, "band_label": "core"},
            },
            {
                "dict": "ap90",
                "headword": "bhū",
                "rendered_html": "<p>ap90-body</p>",
                "scan_url": None,
                "evidence": {"band": 1, "band_label": "core"},
            },
        ],
    }


def test_bu_hit_is_one_line_under_headword_not_a_tab():
    html = render_word_page(_card(), token="_42_55")
    assert html.count('class="saru-strip"') == 1
    assert 'class="saru-strip saru-miss"' not in html
    assert "будет" in html
    assert "SanskritRussian" in html
    hw = html.find('class="hw-strip"')
    saru = html.find('class="saru-strip"')
    tabs = html.find('class="lang-tabs"')
    assert 0 <= hw < saru < tabs
    assert 'id="tab-saru"' not in html
    assert 'id="panel-saru"' not in html
    assert 'data-dict="saru"' not in html
    assert html.count('role="tabpanel"') == 5
    assert 'id="tab-lang-en"' in html
    assert 'id="tab-lang-de"' in html
    assert 'id="tab-lang-ru"' in html
    assert 'id="tab-all"' in html
    assert 'data-dict="pwg_ru"' in html
    assert 'data-dict="mw_ru"' in html


def test_miss_is_one_honest_line():
    html = render_word_page(_card("zzqxw"), token="zzqxw")
    assert html.count('class="saru-strip saru-miss"') == 1
    assert "No SanskritRussian gloss for this lemma." in html
    assert html.count('role="tabpanel"') == 5
    assert 'id="tab-saru"' not in html
    assert 'data-dict="saru"' not in html


def test_join_prefers_lemma_and_does_not_write():
    clear_caches()
    lemma = FIXTURE / "lemma_glossary.tsv"
    before = lemma.read_bytes()
    digest = hashlib.sha256(before).hexdigest()
    hit = join_sr_strip("BU")
    assert hit["hit"] is True
    assert hit["text"] == "будет"
    assert hit["layer"] == "lemma"
    miss = join_sr_strip("zzqxw")
    assert miss["hit"] is False
    assert miss["text"] is None
    now = lemma.read_bytes()
    assert now == before
    assert hashlib.sha256(now).hexdigest() == digest


def test_public_tier_only_never_corpus_lexicon():
    root = resolve_sr_root()
    assert root == FIXTURE
    names = {p.name for p in root.iterdir()}
    assert "corpus_lexicon.jsonl" not in names
    assert "lemma_glossary.tsv" in names
    for name in _PUBLIC_FILES:
        assert (root / name).is_file()
    from kosha.api import sr_gloss

    opened = {path.name for path, _, _ in sr_gloss.rg._layer_files(root)}
    assert opened == set(_PUBLIC_FILES)
    assert "corpus_lexicon.jsonl" not in opened
