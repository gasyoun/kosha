"""kosha word-page UX layer — literary-source `<ls>` citation links (H3479, wave
2 of H3457's print-scan anchors).

STAGING ONLY (25-08-2026), same contract as app/word_page_ux.py: only reached
when `ux` is truthy, so the default `render_word_page(card)` path is untouched.

PWG only (MW-side literary-source scans are a later wave — the resolver below
is a PWG-scoped port and this module never calls it for other dicts).

**Never a new resolver.** This hydrates the ALREADY-RENDERED
`<span class='ls' title='N'>TEXT</span>` markup app/render.py emits for a
Cologne `<ls>` element (see its "DB-backed tooltips and external `<ls>`
hyperlinks are not resolved here" deferral) by calling the two things that
already exist:

1. [`ls_resolver.generate_href`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/ls_resolver.py)
   (SanskritLexicography sibling checkout) — the faithful Python port of
   Cologne's own csl-app Dart pattern engine, already production-proven on the
   pwg_ru pipeline (83.6% coverage over 41,115 real `<ls>` citations, H2827).
2. [`pwg_scan_index.tsv`](https://github.com/sanskrit-lexicon/csl-observatory/blob/main/data/pwg_scan_index_tracker/pwg_scan_index.tsv)
   (csl-observatory sibling checkout, kosha manifest row
   `pwg-scan-index-campaign`) — which literary sources the volunteer
   print-scan campaign has actually wired live (`scan_wired == "yes"`), plus
   each source's full title for the link tooltip.

Both are optional sibling checkouts (same DB-free, pure-function-of-committed-
files posture as word_page_ux.py's PWG print anchors): when either is absent,
`hydrate_pwg_ls` returns the input unchanged — an honest miss, never a crash
and never an invented link.

Two link classes, because they answer different questions:

* `ls-scan`  — the citation resolves to a host the campaign registry marks
  `scan_wired` (a volunteer-scanned page image of the printed source; title
  = the registry's full source name).
* `ls-etext` — the resolver returns a live URL that is NOT in the campaign
  registry: canonical Ashtadhyayi.com sutra pages, the sanskrit-lexicon.github.io
  RV/AV hymn-line anchors, or a sanskrit-lexicon-scans.github.io host the
  82-row PWG-specific tracker doesn't happen to carry (Mahābhārata, Rāmāyaṇa,
  Manu, Śatapatha Brāhmaṇa, ...). Still a real, resolvable target — just not
  the volunteer print-scan campaign's own inventory.

A citation with a real locus but no resolver pattern (`MINTABLE`) or a bare
abbreviation with nothing to point at (`NO_LOCUS`) is left as the plain
`<span class='ls'>` text app/render.py already emits — unresolvable, untouched.
"""
import csv
import html
import os
import re
from collections import Counter
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_GH = _REPO.parent
_SANSKRIT_LEXICOGRAPHY_SRC = _GH / "SanskritLexicography" / "RussianTranslation" / "src"
_SCAN_INDEX_TSV = (_GH / "csl-observatory" / "data" / "pwg_scan_index_tracker"
                   / "pwg_scan_index.tsv")

# Matches app/render.py's `<ls>` emission exactly: `class='ls'` first, then an
# optional `title='N'` (the `n` attribute of the source `<ls n="N">`; absent
# when the citation carries its own abbreviation inline). Deliberately does
# NOT match `<span style='color:blue;' class='ls'>` (the `<lshead>` emission —
# different attribute order, no title), which is not an `<ls>` citation.
_LS_SPAN_RE = re.compile(r"<span class='ls'(?: title='([^']*)')?>(.*?)</span>", re.S)
_HAS_LOCUS = re.compile(r"\d")
_STRIP_TAGS = re.compile(r"<[^>]+>")

HIT_SCAN = "hit_scan"        # resolved, campaign-registry scan_wired
HIT_ETEXT = "hit_etext"      # resolved, not in the campaign registry
MINTABLE = "mintable"        # real locus, no resolver pattern
NO_LOCUS = "no_locus"        # bare abbreviation, nothing to point at

_lsr = None
_lsr_load_failed = False


def _resolver():
    """The SanskritLexicography sibling's ls_resolver module, or None."""
    global _lsr, _lsr_load_failed
    if _lsr is not None or _lsr_load_failed:
        return _lsr
    if not (_SANSKRIT_LEXICOGRAPHY_SRC / "ls_resolver.py").exists():
        _lsr_load_failed = True
        return None
    import sys
    os.environ.setdefault("LS_RESOLVER_QUIET", "1")
    sys.path.insert(0, str(_SANSKRIT_LEXICOGRAPHY_SRC))
    try:
        import ls_resolver as lsr
    except ImportError:
        _lsr_load_failed = True
        return None
    _lsr = lsr
    return _lsr


_wired_titles = None


def _wired():
    """{scan_dir: full_title} for every campaign-registry row with
    scan_wired == "yes", or {} when the csl-observatory sibling is absent."""
    global _wired_titles
    if _wired_titles is not None:
        return _wired_titles
    d = {}
    if _SCAN_INDEX_TSV.exists():
        with _SCAN_INDEX_TSV.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                if row.get("scan_wired") != "yes":
                    continue
                title = row.get("title") or row.get("ls_code") or ""
                for key in (row.get("scan_dir"), row.get("scan_dir_canonical")):
                    if key:
                        d[key] = title
    _wired_titles = d
    return _wired_titles


def _classify_href(href):
    """(status, title_or_None) for a resolver href, or (status, None) unresolved."""
    from urllib.parse import urlparse
    seg = urlparse(href).path.strip("/").split("/")[0]
    title = _wired().get(seg)
    if title is not None:
        return HIT_SCAN, title
    return HIT_ETEXT, None


def resolve_one(n_attr, visible):
    """(status, href_or_None, title_or_None) for one `<ls>` citation, PWG only."""
    lsr = _resolver()
    href = None
    if lsr is not None:
        try:
            href = lsr.generate_href("pwg", n_attr, visible) or None
        except Exception:
            href = None
    if href:
        status, title = _classify_href(href)
        return status, href, title
    return (MINTABLE if _HAS_LOCUS.search(visible or "") else NO_LOCUS), None, None


def hydrate_pwg_ls(rendered_html):
    """(new_html, Counter) — every resolvable `<span class='ls'>` in a PWG
    entry's rendered_html rewritten to a link; unresolvable ones untouched.

    Only meaningful for dict == 'pwg' bodies; callers gate on that (see
    app/word_page.py::_entry_html). Idempotent no-op (Counter all zero) when
    neither sibling checkout is present."""
    esc = html.escape
    stats = Counter()
    out, pos = [], 0
    text = rendered_html or ""
    for m in _LS_SPAN_RE.finditer(text):
        out.append(text[pos:m.start()])
        pos = m.end()
        n_attr, inner = m.group(1), m.group(2)
        visible = _STRIP_TAGS.sub("", inner)
        status, href, title = resolve_one(n_attr, visible)
        stats[status] += 1
        if status == HIT_SCAN:
            out.append(f"<a class=\"ls ls-scan\" href=\"{esc(href, quote=True)}\" "
                       f"target=\"_blank\" rel=\"noopener\" "
                       f"title=\"Cologne print scan: {esc(title)}\">{inner}</a>")
        elif status == HIT_ETEXT:
            out.append(f"<a class=\"ls ls-etext\" href=\"{esc(href, quote=True)}\" "
                       f"target=\"_blank\" rel=\"noopener\" "
                       f"title=\"Resolved literary-source link\">{inner}</a>")
        else:
            out.append(m.group(0))
    out.append(text[pos:])
    return "".join(out), stats


def census_pwg_ls(rendered_html):
    """Counter only — same classification as hydrate_pwg_ls, no HTML built."""
    _, stats = hydrate_pwg_ls(rendered_html)
    return stats
