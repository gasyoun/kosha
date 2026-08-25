"""H3480 — word-page header rethink (MG rulings R1–R5, 25-08-2026).

R1  three header rows in variant d: strip · SanskritRussian · one flat tab row
R2  a single Gloss/Full switch in the strip; no three-way toggle
R3  RU overlay renders `{#slp1#}` / `{%gloss%}` (public path, not staging-gated)
R4/R5 no language row, no per-language rows, no RU sub-row; zero-count dicts dropped
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "src"))

from word_page import render_word_page  # noqa: E402
from kosha.api.ru_join import ru_markup_prepass  # noqa: E402

CARDS = ROOT / "docs" / "cards"
pytestmark = pytest.mark.skipif(not (CARDS / "gam.json").exists(), reason="docs/cards/gam.json missing")


def _card(tok):
    return json.loads((CARDS / f"{tok}.json").read_text(encoding="utf-8"))


def test_r3_ru_prepass_maps_to_cologne_markup():
    assert ru_markup_prepass("{#gam#} (vgl. {#gA#}) {%идти%}") == "<s>gam</s> (vgl. <s>gA</s>) <i>идти</i>"
    assert ru_markup_prepass("plain") == "plain"


def test_r3_ru_tab_has_no_raw_wrappers_public_path():
    # The default (public) render — no ux flag — must not leak {# or {% from the RU overlay.
    html = render_word_page(_card("gam"), token="gam")
    panel = html.split('id="panel-pwg_ru"', 1)[1].split("</section>", 1)[0]
    if "No pwg_ru row" in panel:
        pytest.skip("RU store not present in this checkout")
    assert "{#" not in panel and "{%" not in panel
    assert 'class="sdata"' in panel


def test_r1_r2_r4_r5_variant_d_header_is_three_rows():
    html = render_word_page(_card("gam"), token="gam", ux="d")
    assert 'class="lang-tabs"' not in html and 'class="dict-tabs"' not in html
    assert 'class="view-toggle"' not in html
    assert html.count('class="flat-tabs"') == 1
    assert 'data-vswitch' in html and html.index("data-vswitch") < html.index("data-fav")
    assert html.index('class="hw-strip"') < html.index('<p class="saru-strip') < html.index('class="flat-tabs"')
    # zero-count dictionaries are dropped from the flat row; All keeps the total
    assert 'data-dict="mw_ru"' not in html.split('class="flat-tabs"', 1)[1].split("</nav>", 1)[0]
    assert 'id="tab-all"' in html


def test_variant_d_does_not_touch_default_output():
    card = _card("gam")
    assert render_word_page(card, token="gam") == render_word_page(card, token="gam", ux=None)
