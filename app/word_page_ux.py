"""kosha word-page UX layer — study badge · favorites · print-scan anchors (H3457).

STAGING ONLY (25-08-2026). Nothing here is on the public word page until a human
flips it: `render_word_page(card, ux=None)` (the default) is byte-identical to the
pre-H3457 output, and `scripts/build_word_pages.py --ux-staging` refuses to write
into the Pages tree (`docs/`). Marker: docs/NOT_PUBLISHED_H3457_WPAGE_UX.md.

Three organs, all DB-free and a pure function of committed files, so the static
prerender and the FastAPI SSR route stay byte-comparable when `ux` is on:

1. **Study badge** — `core_rank` + `coverage_pct` from
   data/frequency/lemma_frequency.tsv (Leonchenko learn-these-first ordering,
   7,120 lemmas carry it, max rank 7,532). Wording is ours: three rungs, cut on
   the rank alone, never on invented data. A lemma outside the ordering gets NO
   badge (an honest miss, not a "rare" claim).
2. **Favorites** — a `<button data-fav>` hydrated by JS, state in
   `localStorage['kosha_favorites']` (`{slp1: {t, ia, dv, ts}}`), plus a static
   favorites page (`favorites.html`) that renders that store client-side with
   TSV / Anki export. Static-site friendly: no backend, no cookies.
3. **Print-scan anchors** — every entry gets a stable `id="e-{dict}-{L}"` and
   its scan link says *where* in the print it lands. For PWG the committed
   data/pwg_scan/pwg_L_pc.tsv (from csl-orig `<pc>`, scripts/build_pwg_scan_anchors.py)
   supplies (vol, col) and the URL is rebuilt through kosha.scan_resolver's
   H839 `{vol}-{col:04d}` key — the bare-page links in the pre-H839 cards
   default to volume 1 on Cologne's side. MW / AP90 keep their column link
   (single-volume), labelled. MW-side print anchors (the Cologne
   scan-index campaign) are a later wave.

Variants (design directions, one axis: WHERE the study affordances live relative
to the reading column) — see mockups/h3457-wpage-ux/:
  a  "inline strip"   badge + heart in the headword strip, anchors in entry heads
  b  "study rail"     a separate rail (right column ≥ 900 px, stacked card below)
                      with the badge explained, the heart, and a print-sources list
  c  "margin marks"   editorial: rank line under the headword, text-link save,
                      column marks right-aligned like a critical edition
"""
import csv
import html
import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
LEMMA_FREQ = _REPO / "data" / "frequency" / "lemma_frequency.tsv"
PWG_PC = _REPO / "data" / "pwg_scan" / "pwg_L_pc.tsv"

VARIANTS = ("a", "b", "c")
DEFAULT_VARIANT = "a"

# Rungs on core_rank (1 = learn first). Cut points are design wording over the
# committed ordering; the number shown is always the raw rank.
RUNGS = (
    (500, "core-500", "core · learn first"),
    (2000, "core-2000", "core · second circle"),
    (10**9, "core-vocab", "core vocabulary"),
)

_SCAN_PAGE_RE = re.compile(r"[?&]page=(?:(\d+)-)?(\d+)")


def _load_core_rank():
    """{lemma_slp1: (core_rank:int, coverage_pct:str-as-in-file)} — the raw
    string of coverage_pct is kept so the badge byte-matches the TSV."""
    d = {}
    if not LEMMA_FREQ.exists():
        return d
    with LEMMA_FREQ.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            cr = (r.get("core_rank") or "").strip()
            if not cr:
                continue
            d[r["lemma_slp1"]] = (int(cr), (r.get("coverage_pct") or "").strip())
    return d


def _load_pwg_pc():
    """{L:str: (vol:int, col:int)} from the committed PWG print-anchor table."""
    d = {}
    if not PWG_PC.exists():
        return d
    with PWG_PC.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            d[r["L"]] = (int(r["vol"]), int(r["col"]))
    return d


_CORE = None
_PC = None


def slp1_from_token(tok):
    """Inverse of word_page.card_token — the exact SLP1 key of a card. Cards
    case-fold `query.key` ("darma" for Darma), the token does not."""
    out, j = [], 0
    while j < len(tok):
        if tok[j] == "_":
            out.append(chr(int(tok[j + 1:j + 3], 16)))
            j += 3
        else:
            out.append(tok[j])
            j += 1
    return "".join(out)


def core_rank_of(slp1):
    global _CORE
    if _CORE is None:
        _CORE = _load_core_rank()
    return _CORE.get(slp1)


def pwg_pc_of(L):
    global _PC
    if _PC is None:
        _PC = _load_pwg_pc()
    return _PC.get(str(L))


def core_total():
    global _CORE
    if _CORE is None:
        _CORE = _load_core_rank()
    return len(_CORE)


def rung_of(rank):
    for cut, cls, label in RUNGS:
        if rank <= cut:
            return cls, label
    return RUNGS[-1][1], RUNGS[-1][2]


# ---------------------------------------------------------------- organs

def study_badge(slp1, variant=DEFAULT_VARIANT):
    """HTML for the study badge, or "" when the lemma is outside the core
    ordering. data-core-rank / data-coverage carry the raw TSV strings."""
    hit = core_rank_of(slp1)
    if hit is None:
        return ""
    rank, cov = hit
    cls, label = rung_of(rank)
    esc = html.escape
    total = core_total()
    title = (f"Learn-these-first rank {rank} of {total} core lemmas "
             f"(coverage weight {cov}); source: lemma_frequency.tsv core_rank")
    if variant == "c":
        return (
            f'<p class="study-line {cls}" data-core-rank="{rank}" data-coverage="{esc(cov)}" '
            f'title="{esc(title)}"><span class="study-rung">{esc(label)}</span>'
            f' · rank <b>{rank}</b> of {total}</p>'
        )
    return (
        f'<span class="study-badge {cls}" data-core-rank="{rank}" data-coverage="{esc(cov)}" '
        f'title="{esc(title)}"><span class="study-rung">{esc(label)}</span>'
        f'<span class="study-rank">#{rank}</span></span>'
    )


def study_explainer(slp1):
    """Variant b: one sentence under the badge, in the rail."""
    hit = core_rank_of(slp1)
    if hit is None:
        return ('<p class="study-x">Not in the core learn-first ordering — '
                'study it when your reading needs it.</p>')
    rank, cov = hit
    total = core_total()
    return (f'<p class="study-x">Rank <b>{rank}</b> of {total} in the learn-these-first '
            f'ordering; coverage weight {html.escape(cov)}.</p>')


def fav_button(slp1, deva, iast, token, variant=DEFAULT_VARIANT):
    esc = html.escape
    text = "☆ save" if variant == "c" else "♡"
    return (
        f'<button type="button" class="fav" data-fav data-slp1="{esc(slp1)}" '
        f'data-token="{esc(token)}" data-deva="{esc(deva)}" data-iast="{esc(iast)}" '
        f'aria-pressed="false" aria-label="Save {esc(iast)} to favorites" hidden>'
        f'<span class="fav-ico">{text}</span></button>'
    )


def scan_anchor(fields, variant=DEFAULT_VARIANT):
    """(anchor_html, resolved_url, label) for one entry. Rebuilds the PWG URL
    through the H839 vol-col key when the committed pc table knows the L;
    otherwise keeps the card's URL and says so in the label."""
    esc = html.escape
    url = fields.get("scan_url")
    if not url:
        return "", None, None
    d = (fields.get("dict") or "").lower()
    L = fields.get("L")
    label, cls = "scan", "scan"
    if d == "pwg":
        pc = pwg_pc_of(L) if L is not None else None
        if pc:
            from kosha.scan_resolver import scan_url as _resolve
            vol, col = pc
            url = _resolve("pwg", col, vol) or url
            label = f"PWG {vol}, {col}"
        else:
            m = _SCAN_PAGE_RE.search(url)
            label = f"PWG col. {m.group(2)} (volume unresolved)" if m else "PWG scan"
            cls = "scan scan-unresolved"
    elif d in ("mw", "ap90"):
        m = _SCAN_PAGE_RE.search(url)
        name = "MW" if d == "mw" else "Apte"
        label = f"{name} p. {m.group(2)}" if m else f"{name} scan"
    if variant == "c":
        inner = f"[{esc(label)}]"
    else:
        inner = f"{esc(label)} ↗"
    a = (f'<a class="{cls}" href="{esc(url)}" target="_blank" rel="noopener" '
         f'title="Open the printed page in the Cologne scan viewer">{inner}</a>')
    return a, url, label


def entry_id(fields):
    d = (fields.get("dict") or "").lower()
    L = fields.get("L")
    return f"e-{html.escape(d)}-{html.escape(str(L))}" if d and L is not None else ""


def print_sources_list(groups):
    """Variant b: every entry's print anchor in one rail list."""
    from word_page import entry_fields, DICT_FULL  # late import: word_page imports us
    items = []
    for d, entries in groups:
        for e in entries:
            f = entry_fields(e)
            a, _url, label = scan_anchor(f, variant="b")
            if not a:
                continue
            eid = entry_id(f)
            items.append(f'<li><a class="rail-e" href="#{eid}">{html.escape(f.get("headword", ""))}</a> '
                         f'<span class="rail-d">{html.escape(DICT_FULL.get(d, d))}</span> {a}</li>')
    if not items:
        return '<p class="study-x">No print scans for this lemma.</p>'
    return f'<ul class="print-sources">{"".join(items)}</ul>'


def study_rail(slp1, deva, iast, token, groups):
    return (
        '<aside class="study-rail" aria-label="Study">'
        '<div class="rail-sec"><h3>Study</h3>'
        + (study_badge(slp1, "b") or '<span class="study-badge none">not in core ordering</span>')
        + study_explainer(slp1)
        + fav_button(slp1, deva, iast, token, "b")
        + '<a class="rail-fav-link" href="../favorites.html">my favorites →</a></div>'
        '<div class="rail-sec"><h3>In print</h3>'
        + print_sources_list(groups)
        + "</div></aside>"
    )


# ---------------------------------------------------------------- CSS / JS

UX_CSS_COMMON = """
.study-badge{display:inline-flex;align-items:baseline;gap:.35rem;font-size:.68rem;
font-weight:700;letter-spacing:.03em;text-transform:uppercase;padding:.14rem .5rem;
border-radius:4px;border:1px solid var(--accent);color:var(--accent);background:transparent}
.study-badge .study-rank{font-family:monospace;font-weight:600;letter-spacing:0;text-transform:none;
opacity:.85}
.study-badge.core-500{background:var(--accent);color:#fff}
.study-badge.core-2000{background:var(--hit-bg)}
.study-badge.none{border-style:dashed;color:var(--muted);border-color:var(--border)}
.fav{border:1px solid var(--border);background:var(--page-bg);color:var(--muted);
border-radius:999px;cursor:pointer;font-size:1rem;line-height:1;padding:.2rem .55rem;
margin-left:auto}
.fav:hover{color:var(--accent);border-color:var(--accent)}
.fav[aria-pressed=true]{color:#fff;background:var(--accent);border-color:var(--accent)}
.fav[aria-pressed=true] .fav-ico::before{content:"♥ "}
.fav[aria-pressed=true] .fav-ico{font-size:0}
.fav[aria-pressed=true] .fav-ico::before{font-size:1rem}
.scan-unresolved{color:var(--muted);text-decoration:underline dotted}
.dict-entry:target{background:var(--hit-bg);outline:2px solid var(--accent);outline-offset:.2rem}
.entry-head .eid{font-size:.75rem;color:var(--muted);text-decoration:none;margin-left:auto}
.entry-head .eid:hover{color:var(--accent)}
.wp-foot .fav-count{margin-left:.3rem;font-family:monospace}
""".strip()

UX_CSS_VARIANT = {
    "a": """
.hw-strip .study-badge{margin-left:.2rem}
""".strip(),
    "b": """
.word-page{display:grid;grid-template-columns:minmax(0,1fr)}
.word-page>*{grid-column:1;min-width:0}
.word-page>.hw-strip,.word-page>.wp-foot{grid-column:1/-1}
@media(min-width:900px){.word-page{grid-template-columns:minmax(0,1fr) 15rem;column-gap:1.4rem}
.word-page>.study-rail{grid-column:2;grid-row:2/span 400;position:sticky;top:1rem;align-self:start}}
.study-rail{border:1px solid var(--border);border-radius:10px;background:var(--card-bg);
padding:.8rem 1rem;font-size:.88rem;margin-top:.8rem}
.study-rail h3{margin:0 0 .45rem;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;
color:var(--muted)}
.rail-sec+.rail-sec{margin-top:1rem;padding-top:.9rem;border-top:1px solid var(--border)}
.study-x{margin:.5rem 0;color:var(--muted);line-height:1.4}
.study-rail .fav{margin:0 .5rem 0 0}
.rail-fav-link{font-size:.8rem;color:var(--accent)}
.print-sources{list-style:none;margin:0;padding:0}
.print-sources li{padding:.25rem 0;border-top:1px dashed var(--border);line-height:1.35}
.print-sources li:first-child{border-top:none}
.rail-e{font-weight:600;color:var(--fg);text-decoration:none}
.rail-d{font-size:.72rem;color:var(--muted)}
.print-sources .scan{display:block;font-size:.8rem}
""".strip(),
    "c": """
.study-line{margin:.35rem 0 0;font-size:.78rem;letter-spacing:.04em;color:var(--muted);
font-variant:small-caps}
.study-line .study-rung{color:var(--accent);font-weight:700}
.study-line b{color:var(--fg)}
.hw-strip .fav{border:none;background:none;border-radius:0;padding:0;font-size:.8rem;
font-variant:small-caps;letter-spacing:.05em;color:var(--accent);margin-left:auto}
.hw-strip .fav[aria-pressed=true]{background:none;color:var(--accent);font-weight:700}
.hw-strip .fav[aria-pressed=true] .fav-ico::before{content:"★ saved";font-size:.8rem}
.entry-head{justify-content:space-between}
.entry-head .scan{font-family:monospace;font-size:.75rem;color:var(--muted);text-decoration:none;
margin-left:auto;white-space:nowrap}
.entry-head .scan:hover{color:var(--accent)}
""".strip(),
}

UX_JS = """
(function(){
 var K='kosha_favorites';
 function load(){try{var s=localStorage.getItem(K);return s?JSON.parse(s):{}}catch(e){return {}}}
 function save(f){try{localStorage.setItem(K,JSON.stringify(f))}catch(e){}}
 var favs=load();
 var n=document.querySelector('[data-fav-count]');
 function count(){var c=Object.keys(favs).length;if(n)n.textContent=c?'('+c+')':''}
 document.querySelectorAll('[data-fav]').forEach(function(b){
  var k=b.getAttribute('data-slp1');b.hidden=false;
  function paint(){b.setAttribute('aria-pressed',favs[k]?'true':'false')}
  paint();
  b.addEventListener('click',function(){
   if(favs[k]){delete favs[k]}else{favs[k]={t:b.getAttribute('data-token'),
    ia:b.getAttribute('data-iast'),dv:b.getAttribute('data-deva'),ts:Date.now()}}
   save(favs);paint();count()})});
 count();
 document.querySelectorAll('.dict-entry[id]').forEach(function(a){
  var h=a.querySelector('.entry-head');if(!h||h.querySelector('.eid'))return;
  var l=document.createElement('a');l.className='eid';l.href='#'+a.id;l.title='Link to this entry';
  l.textContent='#';h.appendChild(l)});
})();
""".strip()


def ux_css(variant):
    return UX_CSS_COMMON + "\n" + UX_CSS_VARIANT.get(variant, UX_CSS_VARIANT["a"])


def footer_fav_link(base):
    return (f'<a href="{html.escape(base)}favorites.html">favorites'
            f'<span class="fav-count" data-fav-count></span></a> · ')


# ---------------------------------------------------------------- favorites page

FAV_CSS = """
:root{--fg:#1a1a1a;--muted:#6b7280;--border:#d7d7db;--accent:#7b2d26;--card-bg:#fafafa;
--hit-bg:#fdf3e7;--page-bg:#fff}
@media(prefers-color-scheme:dark){:root{--fg:#e8e8ea;--muted:#9aa0a6;--border:#3a3a40;
--accent:#e0a44a;--card-bg:#202024;--hit-bg:#3a3020;--page-bg:#161618}}
*{box-sizing:border-box}
body{margin:0;background:var(--page-bg);color:var(--fg);
font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}
main{max-width:52rem;margin:0 auto;padding:1.2rem 1rem 4rem}
h1{font-size:1.5rem;margin:.2rem 0 .3rem}
.lead{color:var(--muted);margin:0 0 1rem;font-size:.9rem}
.tools{display:flex;gap:.5rem;flex-wrap:wrap;margin:0 0 1rem}
.tools button{border:1px solid var(--border);background:var(--card-bg);color:var(--fg);
padding:.35rem .8rem;border-radius:6px;cursor:pointer;font-size:.85rem}
.tools button:hover{border-color:var(--accent);color:var(--accent)}
.fav-list{list-style:none;margin:0;padding:0}
.fav-list li{display:flex;gap:.8rem;align-items:baseline;padding:.5rem 0;
border-top:1px solid var(--border)}
.fav-list li:first-child{border-top:none}
.fav-list .dv{font-size:1.4rem}
.fav-list .ia{color:var(--muted)}
.fav-list a{color:var(--fg);text-decoration:none}
.fav-list a:hover{color:var(--accent)}
.fav-list .rm{margin-left:auto;border:none;background:none;color:var(--muted);cursor:pointer}
.fav-list .rm:hover{color:var(--accent)}
.empty{padding:1.5rem;border:1px dashed var(--border);border-radius:8px;color:var(--muted)}
.study-badge{display:inline-flex;gap:.3rem;font-size:.62rem;font-weight:700;letter-spacing:.03em;
text-transform:uppercase;padding:.1rem .4rem;border-radius:4px;border:1px solid var(--accent);
color:var(--accent)}
.study-badge.core-500{background:var(--accent);color:#fff}
.study-badge.core-2000{background:var(--hit-bg)}
footer{margin-top:2.5rem;padding-top:1rem;border-top:1px solid var(--border);font-size:.78rem;
color:var(--muted)}footer a{color:var(--accent)}
""".strip()

FAV_JS = """
(function(){
 var K='kosha_favorites',RUNG=window.KOSHA_CORE||{};
 function load(){try{var s=localStorage.getItem(K);return s?JSON.parse(s):{}}catch(e){return {}}}
 function save(f){try{localStorage.setItem(K,JSON.stringify(f))}catch(e){}}
 var list=document.getElementById('fav-list'),empty=document.getElementById('fav-empty'),
     cnt=document.getElementById('fav-n');
 function rows(){var f=load();return Object.keys(f).map(function(k){var v=f[k];v.k=k;return v})
  .sort(function(a,b){return (b.ts||0)-(a.ts||0)})}
 function badge(k){var r=RUNG[k];if(!r)return '';var c=r<=500?'core-500':r<=2000?'core-2000':'core-vocab';
  return '<span class="study-badge '+c+'">#'+r+'</span>'}
 function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
 function render(){var r=rows();cnt.textContent=r.length;
  empty.hidden=r.length>0;list.innerHTML=r.map(function(v){
   return '<li data-k="'+esc(v.k)+'"><a href="w/'+esc(v.t)+'.html"><span class="dv" lang="sa">'+esc(v.dv)+
   '</span> <span class="ia">'+esc(v.ia)+'</span></a> '+badge(v.k)+
   '<button type="button" class="rm" title="Remove">✕</button></li>'}).join('')}
 list.addEventListener('click',function(e){var b=e.target.closest('.rm');if(!b)return;
  var li=b.closest('li'),f=load();delete f[li.getAttribute('data-k')];save(f);render()});
 function dl(name,text){var a=document.createElement('a');
  a.href='data:text/plain;charset=utf-8,'+encodeURIComponent(text);a.download=name;
  document.body.appendChild(a);a.click();a.remove()}
 document.getElementById('x-tsv').addEventListener('click',function(){
  dl('kosha_favorites.tsv','slp1\\tiast\\tdevanagari\\tcore_rank\\n'+rows().map(function(v){
   return [v.k,v.ia,v.dv,RUNG[v.k]||''].join('\\t')}).join('\\n')+'\\n')});
 document.getElementById('x-anki').addEventListener('click',function(){
  dl('kosha_favorites_anki.txt',rows().map(function(v){
   return v.dv+' ('+v.ia+')\\t'+location.href.replace(/favorites\\.html.*$/,'')+'w/'+v.t+'.html'}).join('\\n')+'\\n')});
 document.getElementById('x-clear').addEventListener('click',function(){
  if(confirm('Remove all favorites on this device?')){save({});render()}});
 render();
})();
""".strip()


def favorites_page_html(core_ranks_json="{}"):
    """The static favorites index. `core_ranks_json` is a {slp1: core_rank}
    JSON string inlined so the list can show the study badge without a
    network call; the build passes the subset for the pages it wrote."""
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>My favorites — Sanskrit dictionary | kosha</title>"
        '<meta name="robots" content="noindex">'
        f"<style>{FAV_CSS}</style></head><body><main>"
        '<p class="crumb"><a href="browse/">← browse</a></p>'
        '<h1>My favorites <span id="fav-n">0</span></h1>'
        '<p class="lead">Saved on this device only (browser storage) — nothing is sent anywhere. '
        "Export to keep them.</p>"
        '<div class="tools"><button type="button" id="x-tsv">Export TSV</button>'
        '<button type="button" id="x-anki">Export for Anki</button>'
        '<button type="button" id="x-clear">Clear all</button></div>'
        '<p class="empty" id="fav-empty">No favorites yet — open a word page and press ♡.</p>'
        '<ul class="fav-list" id="fav-list"></ul>'
        '<footer>Gasuns Sanskrit Dictionary · <a href="browse/">browse</a> · '
        '<a href="inflect/">inflection lookup</a></footer>'
        "</main>"
        f"<script>window.KOSHA_CORE={core_ranks_json};</script>"
        f"<script>{FAV_JS}</script></body></html>\n"
    )


def core_ranks_json(slp1_list):
    d = {}
    for s in slp1_list:
        hit = core_rank_of(s)
        if hit:
            d[s] = hit[0]
    return json.dumps(d, ensure_ascii=False, separators=(",", ":"))
