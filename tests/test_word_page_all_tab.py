"""All-dictionaries tab on the word page (H2653).

No static card set required — uses a synthetic 3-dict envelope.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

from app.word_page import render_word_page  # noqa: E402


def _card():
    return {
        "query": {"key": "BU"},
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
                "rendered_html": "<p>pwg-body</p>",
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


def test_all_tab_present_for_multi_dict():
    html = render_word_page(_card(), token="_42_55")
    assert 'id="tab-all"' in html
    assert 'data-dict="all"' in html
    assert "mw-body" in html and "pwg-body" in html and "ap90-body" in html
    # Five headings: MW + PWG + AP90 + pwg_ru + mw_ru (H2670 / R15).
    assert html.count('class="dict-label"') == 5
    assert "all-dicts" in html  # JS class toggle
    assert 'id="panel-mw"' in html
    assert 'id="panel-pwg"' in html
    assert 'id="panel-ap90"' in html
    assert 'id="panel-pwg_ru"' in html
    assert 'id="panel-mw_ru"' in html


def test_all_tab_present_for_single_dict():
    """All is a top-level language control (R15), even for one Cologne dict."""
    card = _card()
    card["results"] = card["results"][:1]
    html = render_word_page(card, token="_42_55")
    assert 'id="tab-all"' in html
    assert 'id="panel-mw"' in html
    assert 'id="panel-pwg_ru"' in html
