#!/usr/bin/env python
"""Generate the kosha static print-co-location page (GitHub Pages tier).

"Which words were originally printed together on the same page/column?" — the
static, public-web counterpart of the /api/v1/page + /api/v1/neighbors endpoints
(app/neighbors.py, H434). Renders from kosha.db only (RISKS.md R12: the static
tier never calls a live service), into a self-contained page under
`colocation/` served at gasyoun.github.io/kosha/colocation/.

Per-dict co-location unit (entries.parse_pc stores different shapes per dict):
  * pwg  -> (vol, page)   page = the Böhtlingk-Roth column/Spalte (fine unit)
  * mw   -> (page, col)   page = physical page, col = column within it
  * ap90 -> (page, col)   same
Grouping on the finest available key per dict recovers the printed column.

Output:
  colocation/index.html        self-contained browser (dict tabs, search, scan links)
  colocation/data/<dict>.js    window.COLOC_DATA['<dict>'] = [{key,label,scan,words}]
                               (lazy-loaded per dict via <script src>, works on file://)

Deterministic; no network; safe to regenerate + commit to main (Pages redeploys).
"""
import argparse
import collections
import io
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
from scan_resolver import scan_url  # noqa: E402
from transliterate import from_slp1_out  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DICTS = ("pwg", "mw", "ap90")
DICT_LABEL = {"pwg": "PWG (Böhtlingk–Roth)", "mw": "Monier-Williams", "ap90": "Apte 1890"}


def group_key(dict_code, row):
    """(label, scan_page, sort_key) for one entry's printed column."""
    vol, page, col = row["vol"], row["page"], row["col"]
    if dict_code == "pwg":
        # page IS the Spalte; volume-scoped
        return (f"{vol}-{page:04d}", page, (vol, page, 0))
    # mw / ap90: physical page + column-within-page. Canonical citation is
    # "page,col" when the column is numeric (MW, e.g. 741,3) and "page+letter"
    # when it is alphabetic (Apte, e.g. 45a) — never bare-concat a numeric col
    # ("1"+"1" would read as page 11).
    c = (col or "").strip()
    if not c:
        label = str(page)
    elif c.isalpha():
        label = f"{page}{c}"
    else:
        label = f"{page},{c}"
    return (label, page, (0, page, c))


def build_dict(con, dict_code):
    rows = con.execute(
        "SELECT L, slp1_key, vol, page, col FROM entries "
        "WHERE dict=? AND page IS NOT NULL ORDER BY page, col, CAST(L AS REAL), L",
        (dict_code,),
    ).fetchall()
    groups = collections.OrderedDict()
    for r in rows:
        label, scan_page, sortk = group_key(dict_code, r)
        g = groups.get(label)
        if g is None:
            g = groups[label] = {"label": label, "scan_page": scan_page,
                                 "sort": sortk, "words": []}
        g["words"].append({"iast": from_slp1_out(r["slp1_key"], "iast"),
                           "slp1": r["slp1_key"]})
    out = []
    for g in sorted(groups.values(), key=lambda x: x["sort"]):
        out.append({"key": g["label"], "label": g["label"],
                    "scan": scan_url(dict_code, g["scan_page"]) or "",
                    "n": len(g["words"]), "words": g["words"]})
    return out


def write_data(out_dir, dict_code, data):
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, f"{dict_code}.js")
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("window.COLOC_DATA=window.COLOC_DATA||{};window.COLOC_DATA[%s]="
                % json.dumps(dict_code))
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    return os.path.getsize(path)


INDEX_HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>kosha — print co-location</title>
<style>
:root{--bg:#fff;--fg:#1a1a1a;--mut:#6a6a6a;--line:#e4e4e4;--accent:#7a1f1f;--card:#fafafa}
@media(prefers-color-scheme:dark){:root{--bg:#161616;--fg:#e8e8e8;--mut:#9a9a9a;--line:#333;--accent:#e6928a;--card:#1e1e1e}}
:root[data-theme=dark]{--bg:#161616;--fg:#e8e8e8;--mut:#9a9a9a;--line:#333;--accent:#e6928a;--card:#1e1e1e}
:root[data-theme=light]{--bg:#fff;--fg:#1a1a1a;--mut:#6a6a6a;--line:#e4e4e4;--accent:#7a1f1f;--card:#fafafa}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:var(--fg);background:var(--bg)}
header{padding:18px 24px;border-bottom:1px solid var(--line)}
h1{font-size:20px;margin:0 0 4px}.sub{color:var(--mut);font-size:13px}
#bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:12px 24px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:2}
.tabs{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.tabs button{border:0;border-right:1px solid var(--line);background:var(--bg);color:var(--fg);padding:6px 14px;cursor:pointer;font-size:14px}
.tabs button:last-child{border-right:0}.tabs button.on{background:var(--accent);color:#fff}
#q{flex:1;min-width:180px;padding:7px 10px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:var(--fg)}
#count{color:var(--mut);font-size:13px}
#list{padding:12px 24px;max-width:1000px}
.col{margin:0 0 14px;padding:12px 14px;background:var(--card);border:1px solid var(--line);border-radius:10px}
.col .clab{font-size:13px;color:var(--mut);font-family:ui-monospace,monospace}
.col a.scan{color:var(--accent);font-size:12px;text-decoration:none;border-bottom:1px dotted var(--accent);margin-left:8px}
.col a.scan:hover{border-bottom-color:transparent}
.words{margin-top:7px;display:flex;flex-wrap:wrap;gap:5px}
.w{font-style:italic;font-size:13px;padding:1px 8px;border:1px solid var(--line);border-radius:11px;color:var(--fg);white-space:nowrap}
.w.hit{background:var(--accent);color:#fff;border-color:var(--accent)}
.na{color:var(--mut);font-style:italic;padding:20px 0}
footer{padding:16px 24px;color:var(--mut);font-size:12px;border-top:1px solid var(--line)}
a{color:var(--accent)}
</style></head><body>
<header><h1>kosha — print co-location</h1>
<div class="sub">Which head-words were originally printed together on the same page/column of the scanned dictionary. Static snapshot of the <code>/api/v1/page</code> + <code>/api/v1/neighbors</code> endpoints — data rendered from <code>kosha.db</code>, no live server.</div></header>
<div id="bar">
<div class="tabs" id="tabs"></div>
<input id="q" placeholder="filter by head-word (IAST or SLP1) or column, e.g. aṃśu / 1-0004 / 649…">
<span id="count"></span>
</div>
<div id="list"><p class="na">Loading…</p></div>
<footer>PWG column = Böhtlingk-Roth Spalte; MW/Apte = page+column. Scan links open the Cologne servepdf viewer. Built by <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_colocation_page.py">build_colocation_page.py</a> (H441).</footer>
<script>
var DICTS=__DICTS__, LABELS=__LABELS__, cur='pwg', LIMIT=400;
var tabs=document.getElementById('tabs'),q=document.getElementById('q'),
    listEl=document.getElementById('list'),countEl=document.getElementById('count');
window.COLOC_DATA=window.COLOC_DATA||{};
DICTS.forEach(function(d){var b=document.createElement('button');b.textContent=LABELS[d];b.setAttribute('data-d',d);
 b.onclick=function(){cur=d;syncTabs();load();};tabs.appendChild(b);});
function syncTabs(){var bs=tabs.querySelectorAll('button');for(var i=0;i<bs.length;i++)bs[i].classList.toggle('on',bs[i].getAttribute('data-d')===cur);}
function esc(x){return (''+(x==null?'':x)).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function render(){
 var data=window.COLOC_DATA[cur]||[];var f=q.value.trim().toLowerCase();
 var rows=[];
 for(var i=0;i<data.length&&rows.length<LIMIT;i++){var g=data[i];
  if(f){var km=g.label.toLowerCase().indexOf(f)>=0;
   var wm=false;for(var j=0;j<g.words.length;j++){if(g.words[j].iast.toLowerCase().indexOf(f)>=0||g.words[j].slp1.toLowerCase().indexOf(f)>=0){wm=true;break;}}
   if(!km&&!wm)continue;}
  rows.push(g);
 }
 var total=data.length;
 countEl.textContent=rows.length+(rows.length>=LIMIT?'+':'')+' / '+total+' columns';
 if(!rows.length){listEl.innerHTML='<p class="na">No matching column.</p>';return;}
 var h='';rows.forEach(function(g){
  h+='<div class="col"><span class="clab">'+esc(g.label)+' · '+g.n+' entries</span>'
   +(g.scan?'<a class="scan" href="'+esc(g.scan)+'" target="_blank" rel="noopener">🖼 scan</a>':'')
   +'<div class="words">';
  g.words.forEach(function(w){var hit=f&&(w.iast.toLowerCase().indexOf(f)>=0||w.slp1.toLowerCase().indexOf(f)>=0);
   h+='<span class="w'+(hit?' hit':'')+'" title="'+esc(w.slp1)+'">'+esc(w.iast)+'</span>';});
  h+='</div></div>';
 });
 listEl.innerHTML=h;
}
function load(){
 if(window.COLOC_DATA[cur]){render();return;}
 listEl.innerHTML='<p class="na">Loading '+LABELS[cur]+'…</p>';
 var sc=document.createElement('script');sc.src='data/'+cur+'.js';
 sc.onload=function(){render();};sc.onerror=function(){listEl.innerHTML='<p class="na">Failed to load '+cur+' data.</p>';};
 document.head.appendChild(sc);
}
q.oninput=render;
syncTabs();load();
</script></body></html>
"""


def write_index(out_dir, dicts):
    html = (INDEX_HTML
            .replace("__DICTS__", json.dumps(list(dicts)))
            .replace("__LABELS__", json.dumps({d: DICT_LABEL[d] for d in dicts})))
    path = os.path.join(out_dir, "index.html")
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=os.path.join("data", "db", "kosha.db"))
    ap.add_argument("--out", default="colocation", help="output dir (repo-root Pages path)")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    os.makedirs(args.out, exist_ok=True)
    present = []
    for d in DICTS:
        data = build_dict(con, d)
        if not data:
            sys.stderr.write(f"  [coloc] {d}: no located entries, skipping\n")
            continue
        size = write_data(args.out, d, data)
        present.append(d)
        print(f"  {d}: {len(data)} columns, {sum(g['n'] for g in data)} entries "
              f"-> data/{d}.js ({size // 1024} KB)")
    write_index(args.out, present)
    print(f"wrote {args.out}/index.html  (dicts: {', '.join(present)})")


if __name__ == "__main__":
    main()
