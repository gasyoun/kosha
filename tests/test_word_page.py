"""P5 word-page template + parity tests (app/word_page.py, H537).

Two contracts, split by what they need:

  * NO DB — always run. The template renders a committed card into a crawlable
    page: every dictionary panel present in the DOM (§5), a <noscript> fallback,
    no hardcoded server host (R1/R5), correct SLP1→Devanagari, and deterministic
    output. card_token stays the exact twin of build_static_cache's.
  * DB-gated (skipif no kosha.db) — the P5-4 parity contract: the FastAPI SSR
    route GET /w/{slp1} emits byte-identical HTML to render_word_page() over the
    same lemma card the /api/v1/lemma endpoint returns. Mirrors
    test_static_cache.py's card==API check, one layer up.
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

from app.word_page import render_word_page, card_token  # noqa: E402

CARDS_DIR = ROOT / "docs" / "cards"
ATTESTED = ROOT / "docs" / "js" / "data" / "attested_keys.json"
DB_PATH = ROOT / "data" / "db" / "kosha.db"

pytestmark = pytest.mark.skipif(
    not CARDS_DIR.exists() or not ATTESTED.exists(),
    reason="committed static card set (docs/cards + attested_keys.json) not present",
)


def _sample_tokens(n=6):
    tokens = json.loads(ATTESTED.read_text(encoding="utf-8"))["tokens"]
    out = []
    # spread across the token space so we hit multi-dict and single-dict lemmas
    for i in range(0, len(tokens), max(1, len(tokens) // (n * 3))):
        tok = tokens[i]
        if (CARDS_DIR / f"{tok}.json").exists():
            out.append(tok)
        if len(out) >= n:
            break
    return out


def _load(tok):
    return json.loads((CARDS_DIR / f"{tok}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("tok", _sample_tokens())
def test_all_dict_panels_in_dom(tok):
    """§5 crawlability: every dict with an entry has its panel present in the
    rendered DOM (the active one shown, the rest hidden) — never lazy-fetched."""
    card = _load(tok)
    html = render_word_page(card, token=tok)
    dicts_with_entries = {r["dict"] for r in card["results"]}
    for d in dicts_with_entries:
        assert f'id="panel-{d}"' in html, f"{d} panel missing from DOM for {tok}"
    # exactly one active tab; the rest of the panels carry `hidden`
    assert html.count('role="tabpanel"') == len(dicts_with_entries)
    n_hidden = len(re.findall(r'class="dict-panel"[^>]*\shidden', html))
    assert n_hidden == max(0, len(dicts_with_entries) - 1)


@pytest.mark.parametrize("tok", _sample_tokens())
def test_crawlable_noscript_and_host_independent(tok):
    html = render_word_page(_load(tok), token=tok)
    assert "<noscript>" in html                     # no-JS reader gets stacked panels
    assert "samskrtam" not in html                  # R1/R5: never hardcode the host
    assert html.startswith("<!doctype html>")       # full crawlable document
    # every entry's rendered_html is inlined, not deferred
    assert 'class="dict-entry"' in html


def test_devanagari_is_correct_not_broken_iast_path():
    # bhū = भू. from_slp1_out(...,'deva') goes through the broken iast_to_devanagari
    # (see kosha commit 5004f4a); the template must use slp1_to_devanagari instead.
    card = {"query": {"key": "BU"}, "results":
            [{"dict": "mw", "headword": "bhū", "rendered_html": "to become",
              "scan_url": None, "evidence": {"band": 1, "band_label": "core"}}]}
    html = render_word_page(card, token="_42_55")
    assert "भू" in html


def test_deterministic():
    tok = _sample_tokens(1)[0]
    card = _load(tok)
    assert render_word_page(card, token=tok) == render_word_page(card, token=tok)


def test_card_token_twin_of_build_static_cache():
    import build_static_cache as bsc  # noqa: E402
    for key in ["ka", "Ka", "BU", "kf", "a_b", "rAma", "agni"]:
        assert card_token(key) == bsc.card_token(key)


# --------------------------------------------------------------------------- #
# P5-4 parity: SSR route == shared template over the same card (needs the DB)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not DB_PATH.exists(),
                    reason="data/db/kosha.db not built (scripts/build_db.py) — SSR parity is DB-gated")
@pytest.mark.parametrize("slp1", ["ca", "agni", "indra", "BU"])
def test_ssr_route_byte_parity_with_template(slp1):
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    api = client.get(f"/api/v1/lemma/{slp1}", params={"in": "slp1"}).json()
    expected = render_word_page(api, token=card_token(slp1),
                                data_version=api.get("data_version"))
    ssr = client.get(f"/w/{slp1}")
    assert ssr.status_code == 200
    assert ssr.text == expected
