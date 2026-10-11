"""make_word_cards.py — OG preview cards (1200x630 PNG) for kosha word pages.

Renders one og/<token>.png per requested SLP1 headword for the og:image tag
that app/word_page.py emits when pages are built with --public-base (the
canonical URL then points at <public_base>/og/<token>.png).

Card content per MG ruling 11-10-2026: Devanagari + IAST headword, dictionary
badge (MW/PWG/AP90) and the first sense line, kosha-branded.

Usage:
    python scripts/make_word_cards.py agni vac karman darma yoga mantra guru deva jYAna Atman
    CHROME_BIN=/path/to/chrome OG_AVATAR=/path/optional  (avatar skipped by default)
"""
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

from word_page import slp1_to_devanagari, from_slp1, card_token

CHROME = os.environ.get(
    "CHROME_BIN",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
CARDS_DIR = ROOT / "docs" / "cards"
OUT_DIR = ROOT / "og"
TMP_HTML = ROOT / "_word_card_tmp.html"
DICT_LABEL = {"mw": "Monier-Williams", "pwg": "PW Grammatik", "ap90": "Apte 1890"}

TEMPLATE = u"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@font-face {{ font-family:'Sanskrit 2003'; src:url('fonts/sanskrit2003.ttf'); }}
html,body {{ margin:0; padding:0; }}
#card {{ width:1200px; height:630px; background:#ffffff; box-sizing:border-box;
 padding:56px 72px 48px; border-top:10px solid #1a3e6e; display:flex; flex-direction:column;
 font-family:-apple-system,'Segoe UI',Georgia,serif; color:#1f2328; }}
.badge {{ font-size:24px; color:#59636e; }}
.badge b {{ color:#1a3e6e; }}
.hw {{ margin-top:14px; display:flex; align-items:baseline; gap:28px; }}
.deva {{ font-family:'Devanagari Sangam MN','Noto Serif Devanagari','Sanskrit 2003',serif;
 font-size:84px; color:#8b0000; line-height:1.2; }}
.iast {{ font-size:48px; font-style:italic; color:#3d444d; }}
.dict {{ font-size:24px; color:#ffffff; background:#1a3e6e; border-radius:8px;
 padding:4px 14px; margin-left:auto; }}
.sense {{ font-size:32px; line-height:1.5; color:#24292f; margin-top:34px;
 display:-webkit-box; -webkit-line-clamp:5; -webkit-box-orient:vertical; overflow:hidden; }}
.footer {{ margin-top:auto; display:flex; justify-content:space-between;
 font-size:24px; color:#59636e; border-top:2px solid #d1d9e0; padding-top:18px; }}
</style></head>
<body><div id="card">
<div class="badge"><b>kosha</b> · Gasuns Sanskrit Dictionary</div>
<div class="hw"><span class="deva">{deva}</span><span class="iast">{iast}</span><span class="dict">{dict_label}</span></div>
<div class="sense">{sense}</div>
<div class="footer"><span>samskrtam.ru/w/{token}.html</span><span>every sense anchored to the scanned print</span></div>
</div></body></html>
"""


def strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def first_sense(card):
    results = card.get("results", [])
    if not results:
        return ""
    return strip_tags(html.unescape(results[0].get("rendered_html", "")))[:220]


def render(slp1):
    token = card_token(slp1)
    card_path = CARDS_DIR / f"{token}.json"
    if not card_path.exists():
        print(f"no card at {card_path}, skipping {slp1}")
        return False
    card = json.loads(card_path.read_text(encoding="utf-8"))
    results = card.get("results", [])
    dict_key = results[0].get("dict", "mw") if results else "mw"
    page = TEMPLATE.format(
        deva=slp1_to_devanagari(slp1),
        iast=from_slp1(slp1),
        dict_label=DICT_LABEL.get(dict_key, dict_key.upper()),
        sense=html.escape(first_sense(card)),
        token=token)
    TMP_HTML.write_text(page, encoding="utf-8")
    out = OUT_DIR / f"{token}.png"
    if out.exists():
        out.unlink()
    cmd = [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
           "--allow-file-access-from-files", "--window-size=1200,630",
           "--virtual-time-budget=3000", f"--screenshot={out}",
           f"file://{TMP_HTML}"]
    subprocess.run(cmd, capture_output=True, timeout=60,
                   encoding="utf-8", errors="replace")
    if not out.exists() or out.stat().st_size == 0:
        print("CARD FAIL", token)
        return False
    print("card written:", out.relative_to(ROOT), out.stat().st_size, "bytes")
    return True


def main():
    slp1_words = sys.argv[1:]
    if not slp1_words:
        print(__doc__)
        return 1
    OUT_DIR.mkdir(exist_ok=True)
    fails = [w for w in slp1_words if not render(w)]
    if TMP_HTML.exists():
        TMP_HTML.unlink()
    if fails:
        print("FAILED:", ",".join(fails))
        return 1
    print(f"{len(slp1_words)} word cards OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
