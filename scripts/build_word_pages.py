"""build_word_pages.py — P5 static word-page prerender (H537, P5_ADVANCED_UI_DESIGN.md §5).

The crawlable half of P5-4: for the attested card set (the SAME frequency-ranked
lemmas scripts/build_static_cache.py already emits — reuse, do NOT recompute N),
render one `/w/<token>.html` per lemma with EVERY dictionary panel present in the
DOM (§5), a `<noscript>` all-stacked fallback, and progressive JS on top. Plus a
`#`-browse spine: `/browse/<letter>.html` alphabetic (Devanagari varṇa order)
index pages that internally link every word page (SEO internal-linking).

Source of truth is the committed static tier, NOT the DB:
  * cards      -> <out-dir>/cards/<token>.json   (per-lemma /api/v1/lemma parity payload)
  * attested   -> <out-dir>/js/data/attested_keys.json  (the N tokens that have a card)
so this runs with no kosha.db (the card set already IS the DB's rendered output;
build_static_cache.py owns the card==API parity, tests/test_static_cache.py locks it).

The page template is app/word_page.py::render_word_page — the exact same function
the FastAPI SSR route calls, so static ∥ SSR are byte-comparable (P5-4 parity).

No-silent-caps (IMPLEMENTATION_PLAN.md cross-cutting rule): the run logs the
actual N rendered, total bytes / mean page size, the Pages-budget headroom, and
the dropped tail (entry-bearing lemmas with no static card — the SSR long tail
covers them).

Usage:
    python scripts/build_word_pages.py                 # all attested word pages + browse
    python scripts/build_word_pages.py --limit 200     # smoke: first 200 tokens
    python scripts/build_word_pages.py --no-browse     # word pages only
    python scripts/build_word_pages.py --force         # re-emit existing pages
"""
import argparse
import html
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from word_page import render_word_page, from_slp1  # noqa: E402

# Devanagari varṇa (alphabetic) order — the browse spine buckets. One bucket per
# initial phoneme; the SLP1 first byte identifies the initial (SLP1 is one token
# per phoneme, aspirates included). A fixed map keeps the Devanagari labels exact
# rather than relying on transcoder edge cases for a bare initial.
VARNA = [
    ("a", "अ"), ("A", "आ"), ("i", "इ"), ("I", "ई"), ("u", "उ"), ("U", "ऊ"),
    ("f", "ऋ"), ("F", "ॠ"), ("x", "ऌ"), ("X", "ॡ"), ("e", "ए"), ("E", "ऐ"),
    ("o", "ओ"), ("O", "औ"),
    ("k", "क"), ("K", "ख"), ("g", "ग"), ("G", "घ"), ("N", "ङ"),
    ("c", "च"), ("C", "छ"), ("j", "ज"), ("J", "झ"), ("Y", "ञ"),
    ("w", "ट"), ("W", "ठ"), ("q", "ड"), ("Q", "ढ"), ("R", "ण"),
    ("t", "त"), ("T", "थ"), ("d", "द"), ("D", "ध"), ("n", "न"),
    ("p", "प"), ("P", "फ"), ("b", "ब"), ("B", "भ"), ("m", "म"),
    ("y", "य"), ("r", "र"), ("l", "ल"), ("v", "व"),
    ("S", "श"), ("z", "ष"), ("s", "स"), ("h", "ह"), ("L", "ळ"),
]
VARNA_INDEX = {slp1: i for i, (slp1, _deva) in enumerate(VARNA)}
VARNA_LABEL = {slp1: deva for slp1, deva in VARNA}


def bucket_of(slp1):
    """(order, slp1_initial) for the browse spine; None if the initial phoneme is
    not a browsable varṇa (e.g. a leading anusvāra — vanishingly rare, dropped
    from browse but still gets a word page)."""
    if not slp1:
        return None
    c = slp1[0]
    if c in VARNA_INDEX:
        return (VARNA_INDEX[c], c)
    return None


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _decode_token(tok):
    """Inverse of card_token — recover the SLP1 key from a card token."""
    out, j = [], 0
    while j < len(tok):
        if tok[j] == "_":
            out.append(chr(int(tok[j + 1:j + 3], 16)))
            j += 3
        else:
            out.append(tok[j])
            j += 1
    return "".join(out)


def build_word_pages(out_dir, limit=None, force=False):
    cards_dir = out_dir / "cards"
    att_path = out_dir / "js" / "data" / "attested_keys.json"
    if not att_path.exists():
        sys.exit(f"error: {att_path} not found — run scripts/build_static_cache.py first "
                 "(it emits the card set + attested_keys.json this consumes).")
    tokens = _read_json(att_path)["tokens"]
    if limit:
        tokens = tokens[:limit]
    w_dir = out_dir / "w"
    w_dir.mkdir(parents=True, exist_ok=True)
    total = len(tokens)
    print(f"[word-pages] {total} attested tokens -> {w_dir}")

    written = skipped = missing = 0
    total_bytes = 0
    rendered_slp1 = []  # (slp1, token) for the browse spine, only pages that exist
    t0 = time.time()
    for i, tok in enumerate(tokens, 1):
        page_path = w_dir / f"{tok}.html"
        card_path = cards_dir / f"{tok}.json"
        if not card_path.exists():
            missing += 1
            continue
        slp1 = _decode_token(tok)
        rendered_slp1.append((slp1, tok))
        if page_path.exists() and not force:
            skipped += 1
            total_bytes += page_path.stat().st_size
            continue
        card = _read_json(card_path)
        html_str = render_word_page(card, token=tok)
        page_path.write_text(html_str, encoding="utf-8")
        total_bytes += len(html_str.encode("utf-8"))
        written += 1
        if i % 5000 == 0 or i == total:
            rate = i / max(time.time() - t0, 1e-6)
            print(f"[word-pages] {i}/{total}  written={written} skipped={skipped} "
                  f"missing={missing}  {rate:.0f}/s")

    n = written + skipped
    mb = total_bytes / 1e6
    mean_kb = (total_bytes / n / 1024) if n else 0
    print(f"[word-pages] done: {written} written, {skipped} skipped, "
          f"{missing} tokens had no card.")
    print(f"[word-pages] N={n} pages, {mb:.1f} MB total, {mean_kb:.1f} KB/page mean.")
    # No-silent-caps: name the Pages budget headroom + the dropped tail explicitly.
    print(f"[word-pages] Pages budget: ~1 GB soft cap; word pages use {mb:.1f} MB "
          f"({mb/1000*100:.1f}% of 1 GB). Static head N={n}; the SSR route "
          f"(/w/{{slp1}}) covers every entry-bearing lemma beyond this attested "
          f"head (the dropped tail).")
    return rendered_slp1


def build_browse(out_dir, rendered_slp1, force=False):
    """/browse/index.html + /browse/<slp1initial>.html — the crawlable varṇa spine
    linking every prerendered word page."""
    b_dir = out_dir / "browse"
    b_dir.mkdir(parents=True, exist_ok=True)
    buckets = {}  # slp1_initial -> [(iast, slp1, token)]
    dropped = 0
    for slp1, tok in rendered_slp1:
        b = bucket_of(slp1)
        if b is None:
            dropped += 1
            continue
        buckets.setdefault(b[1], []).append((from_slp1(slp1), slp1, tok))

    present = [(VARNA_INDEX[k], k) for k in buckets]
    present.sort()

    # index of letters
    links = []
    for _idx, k in present:
        deva = VARNA_LABEL[k]
        links.append(f'<li><a href="{html.escape(k)}.html">{html.escape(deva)}</a> '
                     f'<span class="n">{len(buckets[k])}</span></li>')
    (b_dir / "index.html").write_text(
        _browse_doc("Browse — Sanskrit dictionary | kosha",
                    '<h1>Browse by initial letter</h1>'
                    f'<ul class="varna">{"".join(links)}</ul>'),
        encoding="utf-8")

    for _idx, k in present:
        deva = VARNA_LABEL[k]
        items = sorted(buckets[k], key=lambda t: t[1])  # by slp1
        rows = "".join(
            f'<li><a href="../w/{html.escape(tok)}.html">{html.escape(iast)}</a> '
            f'<span class="key">{html.escape(slp1)}</span></li>'
            for iast, slp1, tok in items
        )
        body = (f'<p class="crumb"><a href="index.html">← all letters</a></p>'
                f'<h1>{html.escape(deva)} <span class="n">{len(items)} headwords</span></h1>'
                f'<ul class="hw-index">{rows}</ul>')
        (b_dir / f"{k}.html").write_text(
            _browse_doc(f"{deva} — browse | kosha", body), encoding="utf-8")

    print(f"[browse] {len(present)} letter pages + index -> {b_dir} "
          f"({dropped} non-varṇa initials dropped from browse).")


BROWSE_CSS = (
    "body{margin:0;font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;"
    "background:#fff;color:#1a1a1a;line-height:1.5}"
    "@media(prefers-color-scheme:dark){body{background:#161618;color:#e8e8ea}}"
    "main{max-width:52rem;margin:0 auto;padding:1.2rem 1rem 4rem}"
    "a{color:#7b2d26;text-decoration:none}a:hover{text-decoration:underline}"
    "@media(prefers-color-scheme:dark){a{color:#e0a44a}}"
    ".varna{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:.6rem}"
    ".varna li{font-size:1.4rem}.varna .n,.n{font-size:.7rem;color:#6b7280}"
    ".hw-index{list-style:none;padding:0;columns:2 14rem;gap:1.5rem}"
    ".hw-index li{break-inside:avoid;padding:.15rem 0}"
    ".key{font-family:monospace;font-size:.75rem;color:#6b7280}"
    ".crumb{font-size:.85rem}"
)


def _browse_doc(title, body):
    return (
        "<!doctype html>\n"
        '<html lang="sa"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html.escape(title)}</title>"
        f"<style>{BROWSE_CSS}</style></head><body><main>{body}"
        '<footer style="margin-top:2rem;font-size:.78rem;color:#6b7280">'
        'Gasuns Sanskrit Dictionary · <a href="../inflect/">inflection lookup</a></footer>'
        "</main></body></html>\n"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "docs",
                    help="Pages output root (default: docs/)")
    ap.add_argument("--limit", type=int, default=None,
                    help="only the first N attested tokens (smoke / partial)")
    ap.add_argument("--no-browse", dest="browse", action="store_false", default=True,
                    help="skip the /browse spine")
    ap.add_argument("--force", action="store_true", help="re-emit existing pages")
    args = ap.parse_args()

    rendered = build_word_pages(args.out_dir, limit=args.limit, force=args.force)
    if args.browse:
        build_browse(args.out_dir, rendered, force=args.force)
    print("[word-pages] complete.")


if __name__ == "__main__":
    main()
