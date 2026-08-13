"""build_word_pages.py — P5 static word-page prerender (H537 / H1590).

The crawlable half of P5-4: for a frequency-ranked **static head** of attested
lemmas (cards from scripts/build_static_cache.py), render one `/w/<token>.html`
per lemma with EVERY dictionary panel present in the DOM (§5), a `<noscript>`
all-stacked fallback, and progressive JS on top. Plus a `#`-browse spine:
`/browse/<letter>.html` alphabetic (Devanagari varṇa order) index pages.

D4 standing rule (ARCHITECTURE.md, Concordance-Q3 / H1586):
  * Head size N is **measured at build time** from `lemma_frequency.tsv` at the
    target corpus token coverage (default 95%) — never carried as a silent
    constant. Today's re-measure is N=11,148 at 95.00%; that is the *expected*
    answer, not an input to hardcode without re-measuring.
  * Only head lemmas that have a static card are prerendered; missing cards
    inside the head and every lemma beyond the head are the **SSR long tail**
    (`GET /w/{slp1}`).

Source of truth for card HTML is the committed static tier, NOT the DB:
  * cards      -> <out-dir>/cards/<token>.json
  * attested   -> <out-dir>/js/data/attested_keys.json
  * frequency  -> data/frequency/lemma_frequency.tsv  (rank_all / count_all)

The page template is app/word_page.py::render_word_page — the exact same function
the FastAPI SSR route calls, so static ∥ SSR are byte-comparable (P5-4 parity).

No-silent-caps: the run logs measured N, coverage, pages written, total bytes /
mean page size, Pages-budget headroom, head-without-card drops, and the SSR tail.

Usage:
    python scripts/build_word_pages.py --coverage 0.95   # D4 default head (H1590)
    python scripts/build_word_pages.py --head 11148      # explicit head after measure
    python scripts/build_word_pages.py                   # all attested (legacy full set)
    python scripts/build_word_pages.py --limit 200       # smoke: first 200 of selection
    python scripts/build_word_pages.py --reading-packs   # pack href tokens → repo-root w/
    python scripts/build_word_pages.py --no-browse
    python scripts/build_word_pages.py --force
"""
import argparse
import csv
import html
import json
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

from word_page import render_word_page, from_slp1, card_token  # noqa: E402

LEMMA_FREQ = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
PAGES_SOFT_CAP_MB = 1024.0

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


PACK_HREF_RE = re.compile(r"\.\./w/([A-Za-z0-9_]+)\.html")


def harvest_reading_pack_tokens(reading_dir=None):
    """Unique card tokens named by reading-pack ``../w/{token}.html`` hrefs.

    Pack pages live at ``/reading/``; those relative hrefs resolve on Pages
    as ``/w/{token}.html`` (site root), not ``/docs/w/``.
    """
    root = Path(reading_dir) if reading_dir is not None else ROOT / "reading"
    tokens = set()
    if not root.exists():
        return []
    for p in root.rglob("*"):
        if p.suffix.lower() not in {".js", ".html", ".json", ".md"}:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        tokens.update(PACK_HREF_RE.findall(text))
    return sorted(tokens)


def measure_head_n(freq_path=LEMMA_FREQ, coverage=0.95):
    """D4: measure static-head N from lemma_frequency at target token coverage.

    Returns dict: n, coverage_achieved, tokens_total, lemmas_with_count.
    N is the smallest prefix of rank_all-sorted lemmas whose cumulative
    count_all / total reaches ``coverage``.
    """
    rows = []
    with open(freq_path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            c = (r.get("count_all") or "").strip()
            rank = (r.get("rank_all") or "").strip()
            lem = (r.get("lemma_slp1") or "").strip()
            if not c or not rank or not lem:
                continue
            rows.append((int(rank), lem, int(c)))
    if not rows:
        sys.exit(f"error: no countable rows in {freq_path}")
    rows.sort(key=lambda t: t[0])
    total = sum(c for _, _, c in rows)
    cum = 0
    n = len(rows)
    cov_achieved = 1.0
    for i, (_, _, c) in enumerate(rows, 1):
        cum += c
        if cum / total >= coverage:
            n = i
            cov_achieved = cum / total
            break
    else:
        cov_achieved = cum / total
    return {
        "n": n,
        "coverage_target": coverage,
        "coverage_achieved": cov_achieved,
        "tokens_total": total,
        "lemmas_with_count": len(rows),
        "ranked": [(lem, c) for _, lem, c in rows],
    }


def select_head_tokens(attested_tokens, cards_dir, head_n=None, coverage=None,
                       freq_path=LEMMA_FREQ):
    """Select card tokens for the static head (frequency-ranked).

    When ``coverage`` is set (and head_n is None), measure N at that coverage.
    When ``head_n`` is set, use that N after optionally logging a measure.
    When both are None, return the full attested list (legacy full-set mode).

    Returns (tokens, meta) where tokens is a list of card tokens in rank order
    for lemmas that have cards, and meta is a logging dict.
    """
    att_set = set(attested_tokens)
    meta = {
        "mode": "all_attested",
        "head_n": None,
        "coverage_achieved": None,
        "head_with_card": 0,
        "head_without_card": 0,
        "ssr_tail_beyond_head": None,
    }

    if head_n is None and coverage is None:
        # Legacy: every attested card token, original order.
        return list(attested_tokens), meta

    measured = measure_head_n(freq_path=freq_path,
                              coverage=coverage if coverage is not None else 0.95)
    n = int(head_n) if head_n is not None else measured["n"]
    ranked = measured["ranked"]
    if n > len(ranked):
        n = len(ranked)

    tokens = []
    without = 0
    for lem, _c in ranked[:n]:
        tok = card_token(lem)
        card_ok = tok in att_set or (cards_dir / f"{tok}.json").exists()
        if card_ok:
            tokens.append(tok)
        else:
            without += 1

    meta.update({
        "mode": "d4_head",
        "head_n": n,
        "coverage_target": measured["coverage_target"] if coverage is not None
                           else None,
        "coverage_achieved": measured["coverage_achieved"]
                            if head_n is None or coverage is not None
                            else None,
        "measured_n_at_95": measured["n"] if abs(measured["coverage_target"] - 0.95) < 1e-9
                           else None,
        "tokens_total": measured["tokens_total"],
        "lemmas_with_count": measured["lemmas_with_count"],
        "head_with_card": len(tokens),
        "head_without_card": without,
        "ssr_tail_beyond_head": max(0, measured["lemmas_with_count"] - n),
        "attested_full": len(attested_tokens),
    })
    return tokens, meta


def build_word_pages(out_dir, limit=None, force=False, head_n=None, coverage=None,
                     tokens=None, w_dir=None, cards_dir=None):
    cards_dir = Path(cards_dir) if cards_dir is not None else out_dir / "cards"
    w_dir = Path(w_dir) if w_dir is not None else out_dir / "w"
    if tokens is not None:
        tokens = list(tokens)
        meta = {
            "mode": "reading_packs",
            "head_n": None,
            "coverage_achieved": None,
            "head_with_card": 0,
            "head_without_card": 0,
            "ssr_tail_beyond_head": None,
            "pack_tokens": len(tokens),
        }
    else:
        att_path = out_dir / "js" / "data" / "attested_keys.json"
        if not att_path.exists():
            sys.exit(f"error: {att_path} not found — run scripts/build_static_cache.py first "
                     "(it emits the card set + attested_keys.json this consumes).")
        attested = _read_json(att_path)["tokens"]
        tokens, meta = select_head_tokens(
            attested, cards_dir, head_n=head_n, coverage=coverage)
    if limit:
        tokens = tokens[:limit]
    w_dir.mkdir(parents=True, exist_ok=True)
    total = len(tokens)
    print(f"[word-pages] mode={meta['mode']} selection={total} -> {w_dir}")
    if meta["mode"] == "d4_head":
        cov = meta.get("coverage_achieved")
        cov_s = f"{cov * 100:.2f}%" if cov is not None else "n/a (explicit --head)"
        print(f"[word-pages] D4 head N={meta['head_n']} coverage={cov_s} "
              f"head_with_card={meta['head_with_card']} "
              f"head_without_card={meta['head_without_card']} "
              f"freq_lemmas={meta['lemmas_with_count']} "
              f"ssr_tail_beyond_head≈{meta['ssr_tail_beyond_head']}")

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
    share = (mb / PAGES_SOFT_CAP_MB) * 100
    print(f"[word-pages] done: {written} written, {skipped} skipped, "
          f"{missing} tokens had no card.")
    print(f"[word-pages] pages={n} total={mb:.1f} MB mean={mean_kb:.1f} KB/page "
          f"Pages_share={share:.1f}% of {PAGES_SOFT_CAP_MB:.0f} MB soft cap.")
    # No-silent-caps: name the Pages budget headroom + the dropped tail explicitly.
    head_label = meta.get("head_n") if meta["mode"] == "d4_head" else n
    print(f"[word-pages] Static head pages={n} (D4 N={head_label}); "
          f"SSR route /w/{{slp1}} covers head-without-card "
          f"({meta.get('head_without_card', 0)}) + long tail beyond head "
          f"({meta.get('ssr_tail_beyond_head', 'all non-selected')}).")
    meta["pages_built"] = n
    meta["total_mb"] = mb
    meta["mean_kb"] = mean_kb
    meta["pages_share_pct"] = share
    return rendered_slp1, meta


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
                    help="only the first N of the selected head (smoke / partial)")
    ap.add_argument("--head", type=int, default=None, dest="head_n",
                    help="D4 static head: top N lemmas by lemma_frequency rank_all "
                         "(only those with cards are prerendered)")
    ap.add_argument("--coverage", type=float, default=None,
                    help="D4: measure N at this corpus token coverage "
                         "(e.g. 0.95). Mutually exclusive with a pure full-set run; "
                         "combine with --head only if you want an explicit N after "
                         "still logging the measure.")
    ap.add_argument("--no-browse", dest="browse", action="store_false", default=True,
                    help="skip the /browse spine")
    ap.add_argument("--reading-packs", action="store_true",
                    help="prerender tokens named by reading/ ../w/{token}.html "
                         "hrefs into repo-root w/ (Pages site-root /w/)")
    ap.add_argument("--force", action="store_true", help="re-emit existing pages")
    args = ap.parse_args()

    if args.head_n is not None and args.head_n < 1:
        sys.exit("error: --head must be >= 1")
    if args.coverage is not None and not (0.0 < args.coverage <= 1.0):
        sys.exit("error: --coverage must be in (0, 1]")

    extra = {}
    browse = args.browse
    if args.reading_packs:
        extra = {
            "tokens": harvest_reading_pack_tokens(),
            "w_dir": ROOT / "w",
            "cards_dir": ROOT / "docs" / "cards",
        }
        browse = False
        if not extra["tokens"]:
            sys.exit("error: --reading-packs found no ../w/{token}.html hrefs")

    rendered, meta = build_word_pages(
        args.out_dir,
        limit=args.limit,
        force=args.force,
        head_n=args.head_n,
        coverage=args.coverage,
        **extra,
    )
    if browse:
        build_browse(args.out_dir, rendered, force=args.force)
    print("[word-pages] complete.")
    # Machine-readable one-liner for exit packets / CI logs.
    print("[word-pages] META "
          + json.dumps({k: v for k, v in meta.items() if k != "ranked"},
                       ensure_ascii=False))


if __name__ == "__main__":
    main()
