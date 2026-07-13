"""kosha P5 — the word page template (H537 / P5_ADVANCED_UI_DESIGN.md §3, §5).

ONE render path shared by both P5-4 targets:

  * the static prerender (scripts/build_word_pages.py) — reads a committed
    per-lemma card (docs/cards/<token>.json) and writes /w/<token>.html;
  * the FastAPI SSR route (app/main.py GET /w/{slp1}) — builds the same card
    shape from the live DB and renders it.

Because both call `render_word_page(card, token=...)`, the two targets are
byte-comparable on primary content by construction (P5-4 parity contract) —
tests/test_word_page.py locks it with no DB, and tests/test_static_cache.py's
sibling live check locks the card==API half.

Crawlability is the whole point (§5): every dictionary's panel is present in
the DOM at render time (the active one shown, the rest `hidden`), and a
`<noscript>` block shows all panels stacked. Progressive JS then hydrates the
tabs, the view-mode toggle, and the disclosures on top — a fetcher with no JS
still reads every entry.

Host-independence (RISKS.md R1/R5, CLAUDE.md citation-durability): the template
never hardcodes `samskrtam.ru`. Self/canonical links are built from the caller-
supplied `base` (default relative), so a page is identical whether served from
gasyoun.github.io/kosha or samskrtam.ru/kosha.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "sanskrit-util" / "py"))
from sanskrit_util import from_slp1, slp1_to_devanagari, to_slp1  # noqa: E402


def _load_upasarga():
    """{root_slp1: [(combined, sense), …]} from the committed W6 dataset
    (data/gita/upasarga_semantics.tsv). Loaded once; a pure function of the
    committed file, so prerender ∥ SSR stay byte-identical."""
    import csv
    d = {}
    p = Path(__file__).resolve().parent.parent / "data" / "gita" / "upasarga_semantics.tsv"
    if not p.exists():
        return d
    with p.open(encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if not r["preverb"]:
                continue
            key = to_slp1(r["root"].replace("√", "").replace("-", "").strip())
            d.setdefault(key, []).append((r["combined"], r["sense"]))
    return d


_UPASARGA = _load_upasarga()

# Fixed presentation order (P5-1). RU is intentionally absent until the P6 gates
# (G5 review + Kochergina rights) clear — see IMPLEMENTATION_PLAN.md §P6 and
# P5_ADVANCED_UI_DESIGN.md §8; cards carry no `ru` dict, so this is also a data
# fact, not only a policy one.
DICT_ORDER = ("mw", "pwg", "ap90")
DICT_LABEL = {"mw": "MW", "pwg": "PWG", "ap90": "AP90"}
DICT_FULL = {
    "mw": "Monier-Williams",
    "pwg": "Petersburger Wörterbuch (großes)",
    "ap90": "Apte 1890",
}

BAND_CLASS = {1: "b1", 2: "b2", 3: "b3", 4: "b4", 5: "b5"}


def card_token(slp1: str) -> str:
    """Filesystem/URL-safe SLP1 encoding — exact twin of
    scripts/build_static_cache.py::card_token and ui/src/lib/cardToken.js.
    Keep [a-z0-9] verbatim, escape every other UTF-8 byte as _<hexbyte>."""
    out = []
    for b in slp1.encode("utf-8"):
        if (97 <= b <= 122) or (48 <= b <= 57):
            out.append(chr(b))
        else:
            out.append("_%02x" % b)
    return "".join(out)


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _plain(rendered_html: str, limit: int = 160) -> str:
    """Strip tags + collapse whitespace — for the <meta> description and the
    Gloss-mode teaser. Never inserted as HTML; always html.escape'd by callers."""
    text = _WS_RE.sub(" ", _TAG_RE.sub("", rendered_html or "")).strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def _group_by_dict(results):
    """{dict: [entry, ...]} in DICT_ORDER, entries in their card order (L order)."""
    grouped = {}
    for r in results:
        grouped.setdefault(r["dict"], []).append(r)
    return [(d, grouped[d]) for d in DICT_ORDER if d in grouped]


def _headword_strip(slp1, deva, iast, band, band_label, n_dicts):
    esc = html.escape
    band_cls = BAND_CLASS.get(band, "b5")
    return (
        '<header class="hw-strip">'
        f'<span class="hw-deva" lang="sa">{esc(deva)}</span>'
        f'<span class="hw-iast">{esc(iast)}</span>'
        f'<span class="hw-key" title="SLP1 key">[{esc(slp1)}]</span>'
        f'<span class="band {band_cls}" title="{esc(band_label)}">band {band}</span>'
        f'<span class="ndicts">{n_dicts} dict{"s" if n_dicts != 1 else ""}</span>'
        # JS-hydrated grammar token (P4 Zaliznyak-style, e.g. m·8n*): filled from
        # the paradigm layer client-side so the static ∥ SSR primary content stays
        # byte-comparable (the paradigm is not part of the card payload). Empty in
        # the crawlable DOM, never fabricated.
        '<span class="gram" data-gram hidden></span>'
        "</header>"
    )


def _view_toggle():
    # Hidden from no-JS readers (they get the full stacked content anyway).
    return (
        '<div class="view-toggle" role="radiogroup" aria-label="Detail level" hidden>'
        '<button type="button" data-view-set="gloss" role="radio" aria-checked="false">Gloss</button>'
        '<button type="button" data-view-set="full" role="radio" aria-checked="false">Full</button>'
        '<button type="button" data-view-set="adaptive" role="radio" aria-checked="true">Adaptive</button>'
        "</div>"
    )


def _entry_html(entry):
    esc = html.escape
    scan = ""
    if entry.get("scan_url"):
        scan = (f'<a class="scan" href="{esc(entry["scan_url"])}" '
                f'target="_blank" rel="noopener">scan ↗</a>')
    return (
        '<article class="dict-entry">'
        f'<div class="entry-head"><span class="hw">{esc(entry.get("headword", ""))}</span>{scan}</div>'
        f'<div class="rendered">{entry.get("rendered_html", "")}</div>'
        "</article>"
    )


def _dict_panels(groups):
    esc = html.escape
    tabs = []
    panels = []
    for i, (d, entries) in enumerate(groups):
        active = i == 0
        tabs.append(
            f'<button type="button" class="tab{" active" if active else ""}" '
            f'role="tab" aria-selected="{"true" if active else "false"}" '
            f'aria-controls="panel-{d}" id="tab-{d}" data-dict="{d}" '
            f'title="{esc(DICT_FULL.get(d, d))}">{esc(DICT_LABEL.get(d, d.upper()))}'
            f'<span class="tab-n">{len(entries)}</span></button>'
        )
        body = "".join(_entry_html(e) for e in entries)
        hidden = "" if active else " hidden"
        panels.append(
            f'<section class="dict-panel" id="panel-{d}" role="tabpanel" '
            f'aria-labelledby="tab-{d}" data-dict="{d}"{hidden}>{body}</section>'
        )
    tabbar = f'<nav class="dict-tabs" role="tablist" aria-label="Dictionaries">{"".join(tabs)}</nav>'
    return tabbar, "".join(panels)


def _evidence_block(ev):
    if not ev:
        return ""
    esc = html.escape
    rows = []
    band = ev.get("band", 5)
    rows.append(f'<li><b>Frequency band {band}</b> — {esc(ev.get("band_label", ""))}</li>')
    ca = ev.get("count_all")
    rows.append(f'<li>{esc(str(ca))} attestations in DCS</li>' if ca is not None
                else '<li>no attestation data</li>')
    fe = ev.get("first_era")
    if fe:
        rows.append(f'<li>first attested: {esc(str(fe))}</li>')
    ex = ev.get("example")
    ex_html = ""
    if ex and ex.get("sa"):
        work = f' — <cite>{esc(ex.get("work", "") or "")}</cite>' if ex.get("work") else ""
        ex_html = (f'<blockquote class="example" lang="sa">{esc(ex["sa"])}{work}</blockquote>')
    return (
        '<details class="disclosure evidence"><summary>Evidence</summary>'
        f'<ul class="ev-list">{"".join(rows)}</ul>{ex_html}</details>'
    )


def _paradigm_block(slp1, base):
    """Static paradigm affordance: a crawlable link into the inflection app,
    JS-hydrated to an inline "show all forms" table (P4 ParadigmTable) on top.
    No paradigm data is inlined (not in the card) so prerender ∥ SSR stay
    byte-comparable; the data-slp1 hook lets the client fetch + expand it."""
    esc = html.escape
    href = f"{base}inflect/?lemma={esc(slp1)}"
    return (
        f'<details class="disclosure paradigm" data-paradigm data-slp1="{esc(slp1)}">'
        '<summary>Paradigm (all forms)</summary>'
        f'<p class="para-fallback">Full inflection table: '
        f'<a href="{href}">open in the inflection lookup →</a></p>'
        "</details>"
    )


def _upasarga_block(slp1):
    """Root cards only: how preverbs (upasarga) shift this root's sense, from the
    W6 dataset. A pure function of slp1 + the committed TSV, so it is prerender ∥
    SSR byte-identical and crawlable (a static <details>, no host, no JS)."""
    variants = _UPASARGA.get(slp1)
    if not variants:
        return ""
    esc = html.escape
    items = "".join(
        f'<li><span class="upa-pv">{esc(c)}</span> — {esc(s)}</li>' for c, s in variants)
    return (
        '<details class="disclosure upasarga">'
        '<summary>Preverb senses (upasarga)</summary>'
        f'<ul class="upa-list">{items}</ul></details>'
    )


PAGE_CSS = """
:root{--fg:#1a1a1a;--muted:#6b7280;--border:#d7d7db;--accent:#7b2d26;
--card-bg:#fafafa;--head-bg:#f0f0f2;--hit-bg:#fdf3e7;--tag-bg:#ece7e0;
--tag-fg:#7b2d26;--page-bg:#fff;--b1:#7b2d26;--b2:#a05a2c;--b3:#4a7a3a;
--b4:#5a6b8c;--b5:#9aa0a6}
@media(prefers-color-scheme:dark){:root{--fg:#e8e8ea;--muted:#9aa0a6;
--border:#3a3a40;--accent:#e0a44a;--card-bg:#202024;--head-bg:#26262b;
--hit-bg:#3a3020;--tag-bg:#2c2c31;--tag-fg:#e0a44a;--page-bg:#161618;
--b1:#e0a44a;--b2:#d08a3a;--b3:#7bbf6a;--b4:#8fa4c8;--b5:#6b7078}}
*{box-sizing:border-box}
body{margin:0;background:var(--page-bg);color:var(--fg);
font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}
.word-page{max-width:52rem;margin:0 auto;padding:1.2rem 1rem 4rem}
.hw-strip{display:flex;gap:.7rem;align-items:baseline;flex-wrap:wrap;
border-bottom:1px solid var(--border);padding-bottom:.6rem}
.hw-deva{font-size:2rem}.hw-iast{font-size:1.2rem;color:var(--muted)}
.hw-key{font-family:monospace;font-size:.8rem;color:var(--muted)}
.band{font-size:.65rem;font-weight:700;padding:.12rem .45rem;border-radius:4px;
color:#fff;text-transform:uppercase}
.band.b1{background:var(--b1)}.band.b2{background:var(--b2)}
.band.b3{background:var(--b3)}.band.b4{background:var(--b4)}.band.b5{background:var(--b5)}
.ndicts,.gram{font-size:.72rem;color:var(--muted)}
.gram{font-family:monospace}
.view-toggle{display:inline-flex;margin:.7rem 0 0;border:1px solid var(--border);
border-radius:6px;overflow:hidden}
.view-toggle button{border:none;background:var(--page-bg);color:var(--muted);
padding:.3rem .7rem;cursor:pointer;font-size:.8rem}
.view-toggle button[aria-checked=true]{background:var(--head-bg);color:var(--fg);font-weight:600}
.dict-tabs{display:flex;gap:.35rem;flex-wrap:wrap;margin:.9rem 0 0;
border-bottom:1px solid var(--border)}
.tab{border:1px solid var(--border);border-bottom:none;background:var(--card-bg);
color:var(--fg);padding:.4rem .8rem;cursor:pointer;border-radius:6px 6px 0 0;font-size:.9rem}
.tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.tab-n{font-size:.65rem;opacity:.75;margin-left:.3rem}
.dict-panel{border:1px solid var(--border);border-top:none;padding:.4rem 1rem;
background:var(--card-bg)}
.dict-entry{border-top:1px solid var(--border);padding:.55rem 0}
.dict-entry:first-child{border-top:none}
.entry-head{display:flex;gap:.7rem;align-items:baseline;margin-bottom:.25rem}
.entry-head .hw{font-weight:600}
.scan{font-size:.8rem;color:var(--accent)}
.rendered{overflow-wrap:anywhere}
[data-view=gloss] .dict-entry:not(:first-child){display:none}
@media(max-width:640px){[data-view=adaptive] .dict-entry:not(:first-child){display:none}}
.disclosure{margin:.8rem 0 0;border:1px solid var(--border);border-radius:8px;
background:var(--card-bg);padding:.3rem .8rem}
.disclosure summary{cursor:pointer;font-weight:600;font-size:.9rem;padding:.3rem 0}
.upa-list{margin:.2rem 0 .4rem;padding-left:1.1rem;font-size:.9rem}
.upa-pv{font-weight:600}
.ev-list{margin:.2rem 0 .4rem;padding-left:1.1rem;font-size:.9rem}
.example{margin:.3rem 0;padding:.4rem .7rem;border-left:3px solid var(--accent);
background:var(--hit-bg);font-size:1.05rem}
.wp-foot{margin-top:2.5rem;padding-top:1rem;border-top:1px solid var(--border);
font-size:.78rem;color:var(--muted)}
.wp-foot a{color:var(--accent)}
""".strip()


PAGE_JS = """
(function(){
 var VM='kosha_view_mode',root=document.documentElement;
 function setView(v){root.setAttribute('data-view',v);
  try{localStorage.setItem(VM,v)}catch(e){}
  document.querySelectorAll('[data-view-set]').forEach(function(b){
   b.setAttribute('aria-checked',b.getAttribute('data-view-set')===v?'true':'false')})}
 try{var s=localStorage.getItem(VM);if(s)root.setAttribute('data-view',s)}catch(e){}
 var vt=document.querySelector('.view-toggle');if(vt){vt.hidden=false;
  setView(root.getAttribute('data-view')||'adaptive');
  vt.addEventListener('click',function(e){var b=e.target.closest('[data-view-set]');
   if(b)setView(b.getAttribute('data-view-set'))})}
 var tabs=document.querySelectorAll('.dict-tabs .tab');
 tabs.forEach(function(t){t.addEventListener('click',function(){
  tabs.forEach(function(x){x.classList.remove('active');x.setAttribute('aria-selected','false')});
  document.querySelectorAll('.dict-panel').forEach(function(p){p.hidden=true});
  t.classList.add('active');t.setAttribute('aria-selected','true');
  var p=document.getElementById('panel-'+t.getAttribute('data-dict'));if(p)p.hidden=false})})
})();
""".strip()


def render_word_page(card, *, token=None, base="../", data_version=None,
                     public_base="", include_doc=True):
    """Render one word page from a card (the /api/v1/lemma envelope shape).

    `card`      : {"query": {"key": slp1}, "results": [...], "data_version": ...}
    `token`     : card_token(slp1); computed if omitted.
    `base`      : URL prefix for in-site links to the site root that holds
                  inflect/ and browse/. Word pages always live under /w/ (both the
                  static prerender and the SSR route), so the default "../" is
                  correct everywhere; host-independent (never an absolute host).
    `public_base`: optional absolute origin for the JSON-LD/canonical (SEO only);
                  empty keeps everything relative (R1/R5 default).
    `include_doc`: wrap in <!doctype html>… (prerender). False returns just the
                  <main> fragment (SSR can embed it, tests compare the core).
    """
    esc = html.escape
    slp1 = card["query"]["key"]
    if token is None:
        token = card_token(slp1)
    results = card.get("results", [])
    deva = slp1_to_devanagari(slp1)
    iast = from_slp1(slp1)
    groups = _group_by_dict(results)
    n_dicts = len(groups)
    ev = results[0].get("evidence") if results else None
    band = (ev or {}).get("band", 5)
    band_label = (ev or {}).get("band_label", "")

    tabbar, panels = _dict_panels(groups)
    strip = _headword_strip(slp1, deva, iast, band, band_label, n_dicts)

    # <noscript>: show every panel stacked (CSS reveals them), hide the tab bar.
    noscript = ("<noscript><style>.dict-panel[hidden]{display:block!important}"
                ".dict-tabs,.view-toggle{display:none!important}</style></noscript>")

    main = (
        '<main class="word-page" data-slp1="%s">' % esc(slp1)
        + strip
        + _view_toggle()
        + noscript
        + tabbar
        + panels
        + _evidence_block(ev)
        + _paradigm_block(slp1, base)
        + _upasarga_block(slp1)
        + '<footer class="wp-foot">Gasuns Sanskrit Dictionary · '
        + '<a href="%sinflect/">inflection lookup</a> · ' % esc(base)
        + '<a href="%sbrowse/">browse</a> · ' % esc(base)
        + 'entries from MW, PWG &amp; Apte (Cologne), rendered verbatim.</footer>'
        + "</main>"
    )
    if not include_doc:
        return main

    dv = data_version or card.get("data_version", "")
    desc = esc(_plain(results[0]["rendered_html"]) if results else iast)
    title = f"{esc(deva)} {esc(iast)} — Sanskrit dictionary | kosha"
    canonical = (f'<link rel="canonical" href="{esc(public_base)}/w/{esc(token)}.html">'
                 if public_base else "")
    return (
        "<!doctype html>\n"
        f'<html lang="sa" data-view="adaptive"><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{title}</title>"
        f'<meta name="description" content="{desc}">'
        f'<meta name="data-version" content="{esc(dv)}">'
        f"{canonical}"
        f"<style>{PAGE_CSS}</style>"
        "</head><body>"
        f"{main}"
        f"<script>{PAGE_JS}</script>"
        "</body></html>\n"
    )
