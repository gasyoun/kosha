"""H3457 — word-page UX staging layer (study badge · favorites · print-scan anchors).

Locks:
  * `render_word_page(card)` with no `ux` is byte-identical to the pre-H3457
    template (the public page does not move until a human flips it);
  * the badge byte-matches lemma_frequency.tsv core_rank / coverage_pct and is
    absent for a lemma outside the core ordering;
  * a PWG entry's print anchor is rebuilt through the H839 "{vol}-{col:04d}"
    key from data/pwg_scan/pwg_L_pc.tsv (the committed cards are bare-page);
  * every entry gets a stable id, the favorites button + footer link exist;
  * `build_ux_staging` refuses to write under docs/.
"""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from word_page import render_word_page, card_token  # noqa: E402
import word_page_ux as ux  # noqa: E402

CARDS = ROOT / "docs" / "cards"
LEMMA_FREQ = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
PC = ROOT / "data" / "pwg_scan" / "pwg_L_pc.tsv"

pytestmark = pytest.mark.skipif(
    not (CARDS / "gam.json").exists() or not LEMMA_FREQ.exists() or not PC.exists(),
    reason="docs/cards/gam.json, lemma_frequency.tsv or pwg_L_pc.tsv missing",
)


def _card(tok):
    return json.loads((CARDS / f"{tok}.json").read_text(encoding="utf-8"))


def _tsv_row(slp1):
    with LEMMA_FREQ.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["lemma_slp1"] == slp1:
                return r
    return None


def test_default_render_is_unchanged_by_the_ux_layer():
    card = _card("gam")
    base = render_word_page(card, token="gam")
    assert base == render_word_page(card, token="gam", ux=None)
    assert "study-badge" not in base and "data-fav" not in base and 'id="e-pwg-' not in base
    for v in ux.VARIANTS:
        assert render_word_page(card, token="gam", ux=v) != base


@pytest.mark.parametrize("tok", ["gam", "kf", "vac"])
def test_badge_byte_matches_lemma_frequency(tok):
    slp1 = ux._load_core_rank and tok  # tokens here are plain slp1
    row = _tsv_row(slp1)
    assert row and row["core_rank"], "fixture lemma must carry a core_rank"
    html = render_word_page(_card(tok), token=tok, ux="a")
    needle = (f'data-core-rank="{row["core_rank"].strip()}" '
              f'data-coverage="{row["coverage_pct"].strip()}"')
    assert needle in html


def test_no_badge_outside_core_ordering(tmp_path):
    # A synthetic lemma key with no frequency row: badge must be absent, not invented.
    card = _card("gam")
    card = json.loads(json.dumps(card))
    card["query"]["key"] = "zzzzzzzz"
    html = render_word_page(card, token=card_token("zzzzzzzz"), ux="a", ru_overlay={}, sr_strip={})
    assert "data-core-rank=" not in html  # the CSS still names .study-badge; the element must not exist
    assert ux.core_rank_of("zzzzzzzz") is None


def test_pwg_anchor_uses_h839_vol_col_key():
    html = render_word_page(_card("gam"), token="gam", ux="a")
    # csl-orig: <L>119742<pc>7-1737 — the committed card says page=1737 (bare).
    assert 'id="e-pwg-119742"' in html
    assert "servepdf.php?page=7-1737" in html
    assert "PWG 7, 1737" in html
    # The MW anchor keeps its single-volume page, labelled.
    assert "MW p. " in html


def test_rungs_are_cut_on_rank_only():
    assert ux.rung_of(1)[0] == "core-500"
    assert ux.rung_of(500)[0] == "core-500"
    assert ux.rung_of(501)[0] == "core-2000"
    assert ux.rung_of(2000)[0] == "core-2000"
    assert ux.rung_of(2001)[0] == "core-vocab"
    assert ux.rung_of(7532)[0] == "core-vocab"


def test_favorites_markup_and_footer_link():
    html = render_word_page(_card("gam"), token="gam", ux="a")
    assert 'data-fav data-slp1="gam" data-token="gam"' in html
    assert "kosha_favorites" in html  # the JS store key
    assert 'href="../favorites.html"' in html
    fav = ux.favorites_page_html(ux.core_ranks_json(["gam"]))
    assert '"gam":7' in fav and 'id="fav-list"' in fav and "noindex" in fav


def test_variant_b_rail_is_a_direct_child_of_main():
    html = render_word_page(_card("gam"), token="gam", ux="b")
    assert '<aside class="study-rail"' in html
    assert "wp-grid" not in html  # the wrapper approach was dropped (Cologne markup may close it early)
    assert "In print" in html and "print-sources" in html


def test_staging_build_refuses_docs(tmp_path):
    from build_word_pages import build_ux_staging
    with pytest.raises(SystemExit):
        build_ux_staging("a", tokens=["gam"], out_root=ROOT / "docs" / "w-staging")
    rendered, meta = build_ux_staging("a", tokens=["gam"], out_root=tmp_path)
    assert meta["ux_variant"] == "a" and len(rendered) == 1
    assert (tmp_path / "a" / "w" / "gam.html").exists()
    assert (tmp_path / "a" / "favorites.html").exists()
    assert (tmp_path / "a" / "NOT_PUBLISHED.md").exists()
