"""Language-group chrome + pwg_ru/mw_ru join (H2670).

No DB required. Uses the committed fixture at tests/fixtures/ru_join/.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

from kosha.api.ru_join import (  # noqa: E402
    clear_caches,
    join_ru,
    locale_from_accept_language,
)
from app.word_page import render_word_page  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "ru_join"


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


def _panel(html: str, dict_id: str) -> str:
    start = html.find(f'id="panel-{dict_id}"')
    assert start != -1, f"missing panel {dict_id}"
    end = html.find('class="dict-panel"', start + 1)
    return html[start:] if end == -1 else html[start:end]


def test_chrome_en_de_ru_all():
    html = render_word_page(_card(), token="_42_55")
    assert 'id="tab-lang-en"' in html
    assert 'id="tab-lang-de"' in html
    assert 'id="tab-lang-ru"' in html
    assert 'id="tab-all"' in html
    assert ">EN<" in html and ">DE<" in html and ">RU<" in html
    assert 'data-dict="mw"' in html
    assert 'data-dict="ap90"' in html
    assert 'data-dict="pwg"' in html
    assert 'data-dict="pwg_ru"' in html
    assert 'data-dict="mw_ru"' in html
    assert 'data-lang="en"' in html
    assert 'navigator.language' in html


def test_ru_panels_render_fixture_russian():
    html = render_word_page(_card(), token="_42_55")
    ru_pwg = _panel(html, "pwg_ru")
    ru_mw = _panel(html, "mw_ru")
    assert "становиться" in ru_pwg
    assert "существовать" in ru_mw
    # Fail = German PWG dumped under RU.
    assert "pwg-body-werden" not in ru_pwg
    assert "pwg-body-werden" not in ru_mw
    assert "Кочергина" not in html
    assert "saru-strip" not in html


def test_empty_state_is_visible():
    html = render_word_page(_card(), token="_42_55", ru_overlay={"pwg_ru": [], "mw_ru": []})
    assert 'id="panel-pwg_ru"' in html
    assert 'id="panel-mw_ru"' in html
    assert "No pwg_ru row for this lemma." in html
    assert "No mw_ru row for this lemma." in html


def test_ai_translated_badge_on_unreviewed_only():
    html = render_word_page(_card(), token="_42_55")
    assert "AI-translated" in _panel(html, "pwg_ru")
    assert "AI-translated" in _panel(html, "mw_ru")
    approved = render_word_page(
        {**_card(), "query": {"key": "banD"}},
        token="band",
    )
    assert "AI-translated" not in _panel(approved, "pwg_ru")
    assert "связывать" in _panel(approved, "pwg_ru")
    assert "AI-translated" in _panel(approved, "mw_ru")


def test_accept_language_ru_first_paint():
    html = render_word_page(_card(), token="_42_55", default_lang="ru")
    assert 'data-lang="ru"' in html
    assert 'id="tab-lang-ru"' in html
    assert 'aria-selected="true"' in html
    pwg_ru = html[html.find('id="panel-pwg_ru"'):html.find('id="panel-pwg_ru"') + 180]
    assert " hidden" not in pwg_ru
    mw = html[html.find('id="panel-mw"'):html.find('id="panel-mw"') + 180]
    assert " hidden" in mw
    assert locale_from_accept_language("ru,en;q=0.8") == "ru"
    assert locale_from_accept_language("ru-RU") == "ru"
    assert locale_from_accept_language("en-US,en;q=0.9") == "en"
    assert locale_from_accept_language(None) == "en"


DB_PATH = ROOT / "data" / "db" / "kosha.db"


@pytest.mark.skipif(not DB_PATH.exists(), reason="kosha.db not built — SSR locale is DB-gated")
def test_ssr_accept_language_ru_selects_ru():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    ru = client.get("/w/BU", headers={"Accept-Language": "ru"})
    assert ru.status_code == 200
    assert 'data-lang="ru"' in ru.text
    assert 'id="tab-lang-ru"' in ru.text
    en = client.get("/w/BU")
    assert en.status_code == 200
    assert 'data-lang="en"' in en.text


def test_all_stacks_every_dict():
    html = render_word_page(_card(), token="_42_55")
    for d in ("mw", "pwg", "ap90", "pwg_ru", "mw_ru"):
        assert f'id="panel-{d}"' in html
    assert "mw-body" in html
    assert "pwg-body-werden" in _panel(html, "pwg")
    assert "ap90-body" in html
    assert "становиться" in html
    assert html.count('role="tabpanel"') == 5


def test_join_reads_fixture_only_and_does_not_write():
    clear_caches()
    before = {}
    for name in ("pwg_ru.jsonl", "mw_ru.jsonl"):
        raw = (FIXTURE / name).read_bytes()
        before[name] = (hashlib.sha256(raw).hexdigest(), raw)
    out = join_ru("BU")
    assert out["pwg_ru"] and out["mw_ru"]
    assert out["pwg_ru"][0]["review_status"] == "ai_translated"
    assert "становиться" in out["pwg_ru"][0]["rendered_html"]
    missing = join_ru("zzqxw")
    assert missing["pwg_ru"] == [] and missing["mw_ru"] == []
    for name, (digest, raw) in before.items():
        now = (FIXTURE / name).read_bytes()
        assert now == raw
        assert hashlib.sha256(now).hexdigest() == digest
        assert b'"review_status": "ai_translated"' in now or b"approved" in now
