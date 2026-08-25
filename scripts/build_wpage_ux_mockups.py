"""build_wpage_ux_mockups.py — H3457 design directions for the word-page UX layer.

Renders ONE real card (default: gam — a verb root with MW + PWG + AP90 entries,
core_rank 7, PWG print anchor 7-1737) through app/word_page.py with each UX
variant (a · b · c, app/word_page_ux.py) into self-contained HTML mockups under
mockups/h3457-wpage-ux/, then (with --shots) screenshots each in light + dark at
375 and 1280 px with Playwright (Chromium, file://, no network).

The mockups are the real template + the variant's CSS/markup — not a parallel
hand-drawn page — so the promotion path from a direction to the staging build
is one flag (`build_word_pages.py --ux-staging <variant>`).

Usage:
    python scripts/build_wpage_ux_mockups.py               # HTML only
    python scripts/build_wpage_ux_mockups.py --shots       # + PNGs
    python scripts/build_wpage_ux_mockups.py --token kf    # another card
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

from word_page import render_word_page  # noqa: E402
from word_page_ux import VARIANTS, favorites_page_html, core_ranks_json  # noqa: E402

OUT = ROOT / "mockups" / "h3457-wpage-ux"
AXIS = {
    "a": "inline strip — badge + heart in the headword strip; print anchors in each entry head",
    "b": "study rail — a separate sticky rail (desktop) / stacked card (mobile): badge explained, "
         "heart, list of every print source; entry heads stay light",
    "c": "margin marks — editorial: a small-caps rank line under the headword, text-link save, "
         "column marks right-aligned like a critical-edition apparatus",
}


def build(token):
    card = json.loads((ROOT / "docs" / "cards" / f"{token}.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "w").mkdir(exist_ok=True)
    paths = []
    for v in VARIANTS:
        html_str = render_word_page(card, token=token, ux=v, base="./")
        # The template links ../favorites.html from /w/; mockups sit flat, so point
        # the footer at the sibling mockup favorites page.
        html_str = html_str.replace('href="./favorites.html"', 'href="favorites.html"')
        p = OUT / f"direction-{v}-{token}.html"
        p.write_text(html_str, encoding="utf-8")
        paths.append(p)
    fav = OUT / "favorites.html"
    fav.write_text(favorites_page_html(core_ranks_json([card["query"]["key"]])), encoding="utf-8")
    paths.append(fav)
    for p in paths:
        print(f"[mockups] {p.relative_to(ROOT)}  {p.stat().st_size / 1024:.0f} KB")
    return paths


def shots(token):
    from playwright.sync_api import sync_playwright
    shots_dir = OUT / "shots"
    shots_dir.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for v in VARIANTS:
            url = (OUT / f"direction-{v}-{token}.html").resolve().as_uri()
            for scheme in ("light", "dark"):
                for width in (375, 1280):
                    ctx = browser.new_context(viewport={"width": width, "height": 900},
                                              color_scheme=scheme)
                    page = ctx.new_page()
                    errors = []
                    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    page.goto(url)
                    page.wait_for_timeout(150)
                    out = shots_dir / f"{v}-{scheme}-{width}.png"
                    page.screenshot(path=str(out), full_page=False)
                    print(f"[shots] {out.relative_to(ROOT)}  console_errors={len(errors)}")
                    if errors:
                        for e in errors:
                            print("   !", e)
                    ctx.close()
        browser.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--token", default="gam")
    ap.add_argument("--shots", action="store_true")
    args = ap.parse_args()
    build(args.token)
    if args.shots:
        shots(args.token)
    print("[mockups] axes:")
    for v, a in AXIS.items():
        print(f"  {v}: {a}")


if __name__ == "__main__":
    main()
