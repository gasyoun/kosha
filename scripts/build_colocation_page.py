#!/usr/bin/env python
"""Generate the kosha static print-co-location browser (GitHub Pages tier).

"Which words were originally printed together on the same page/column?" — the
static, public-web counterpart of the /api/v1/page + /api/v1/neighbors endpoints
(app/neighbors.py, H434). Renders from kosha.db only (RISKS.md R12: the static
tier never calls a live service), into a self-contained page under
`colocation/` served at gasyoun.github.io/kosha/colocation/.

v2 (H441): a PAGED, two-column view of the printed leaf (points 2+3):
  * the printed book sets TWO columns per page; the browser shows a whole leaf
    (left + right column) at once and lets you page ← / → through leaves and
    jump to any column/page.
  * per-dict printed unit (entries.parse_pc stores different shapes):
      pwg  -> (vol, page)  page = Böhtlingk-Roth column/Spalte; leaf = cols
              2P-1 (LEFT) + 2P (RIGHT), P = ceil(col/2)
      mw   -> (page, col)  page = physical page, col numeric -> cited "page,col"
      ap90 -> (page, col)  col alphabetic -> cited "page+letter"
    For mw/ap90 the physical page IS given, so a leaf = all columns of that page.
  * HONEST caveat surfaced in the UI: the source stores COLUMN numbers, not the
    book's printed page number, so we can label left/right COLUMN (derivable) but
    NOT recto/verso of the physical leaf.
  * deep-linkable: `#<dict>/<colkey>` opens that leaf; `?w=<slp1>` highlights a
    word (the RU article site links in here per neighbour head-word).

Output:
  colocation/index.html        self-contained paged browser
  colocation/data/<dict>.js    window.COLOC_DATA['<dict>'] = {leaves:[...], index:{colkey->leafIdx}}
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


def col_of(dict_code, row):
    """(col_label, page_index, side, scan_page, sort_key) for one entry's column.

    side is 'L'/'R' for PWG (derivable from the column's parity within its leaf),
    '' for mw/ap90 (their column is a within-page label, not a leaf half)."""
    vol, page, col = row["vol"], row["page"], row["col"]
    if dict_code == "pwg":
        leaf = (page + 1) // 2               # physical leaf within the volume
        side = "L" if page % 2 == 1 else "R"  # odd column = left, even = right
        return (f"{vol}-{page:04d}", (vol, leaf), side, page, (vol, page))
    c = (col or "").strip()
    if not c:
        label = str(page)
    elif c.isalpha():
        label = f"{page}{c}"       # Apte: 45a
    else:
        label = f"{page},{c}"      # MW: 741,3
    return (label, page, "", page, (page, c))


def build_dict(con, dict_code):
    rows = con.execute(
        "SELECT L, slp1_key, vol, page, col FROM entries "
        "WHERE dict=? AND page IS NOT NULL "
        "ORDER BY COALESCE(vol,0), page, col, CAST(L AS REAL), L",
        (dict_code,),
    ).fetchall()
    # 1) gather columns
    cols = collections.OrderedDict()   # col_label -> {label, leaf, side, scan, words}
    leaves = collections.OrderedDict()  # leaf_key  -> [col_label, ...]
    for r in rows:
        label, leaf_key, side, scan_page, _sort = col_of(dict_code, r)
        c = cols.get(label)
        if c is None:
            c = cols[label] = {"c": label, "side": side,
                               "scan": scan_url(dict_code, scan_page) or "",
                               "words": []}
            leaves.setdefault(leaf_key, [])
            if label not in leaves[leaf_key]:
                leaves[leaf_key].append(label)
        c["words"].append({"iast": from_slp1_out(r["slp1_key"], "iast"),
                           "slp1": r["slp1_key"]})
    # 2) assemble ordered leaves; for PWG fill the missing half so every leaf
    #    shows both L and R even when one column had no entry starting in it.
    out_leaves = []
    index = {}
    for leaf_key in sorted(leaves):
        labels = leaves[leaf_key]
        if dict_code == "pwg":
            vol, leaf = leaf_key
            left_col, right_col = 2 * leaf - 1, 2 * leaf
            leaf_cols = []
            for cc, side in ((left_col, "L"), (right_col, "R")):
                lab = f"{vol}-{cc:04d}"
                if lab in cols:
                    leaf_cols.append(cols[lab])
                else:
                    leaf_cols.append({"c": lab, "side": side,
                                      "scan": scan_url(dict_code, cc) or "", "words": []})
            plabel = f"{vol}·leaf {leaf}"
        else:
            leaf_cols = [cols[l] for l in labels]
            plabel = str(leaf_key)
        li = len(out_leaves)
        out_leaves.append({"p": plabel, "cols": leaf_cols})
        for lc in leaf_cols:
            index[lc["c"]] = li
    return {"leaves": out_leaves, "index": index}


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
:root{--bg:#fff;--fg:#1a1a1a;--mut:#6a6a6a;--line:#e4e4e4;--accent:#7a1f1f;--card:#fafafa;--hl:#ffe27a}
@media(prefers-color-scheme:dark){:root{--bg:#161616;--fg:#e8e8e8;--mut:#9a9a9a;--line:#333;--accent:#e6928a;--card:#1e1e1e;--hl:#6b5a00}}
:root[data-theme=dark]{--bg:#161616;--fg:#e8e8e8;--mut:#9a9a9a;--line:#333;--accent:#e6928a;--card:#1e1e1e;--hl:#6b5a00}
:root[data-theme=light]{--bg:#fff;--fg:#1a1a1a;--mut:#6a6a6a;--line:#e4e4e4;--accent:#7a1f1f;--card:#fafafa;--hl:#ffe27a}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:var(--fg);background:var(--bg)}
header{padding:16px 24px 10px;border-bottom:1px solid var(--line)}
h1{font-size:20px;margin:0 0 4px}.sub{color:var(--mut);font-size:13px;max-width:70ch}
#bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:10px 24px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:2}
.tabs{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.tabs button{border:0;border-right:1px solid var(--line);background:var(--bg);color:var(--fg);padding:6px 14px;cursor:pointer;font-size:14px}
.tabs button:last-child{border-right:0}.tabs button.on{background:var(--accent);color:#fff}
.pager{display:inline-flex;gap:4px;align-items:center}
.pager button{border:1px solid var(--line);background:var(--bg);color:var(--fg);border-radius:7px;padding:6px 11px;cursor:pointer;font-size:15px}
.pager button:disabled{opacity:.4;cursor:default}
#jump,#q{padding:7px 10px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:var(--fg)}
#jump{width:120px}#q{flex:1;min-width:150px}
#where{color:var(--mut);font-size:13px;white-space:nowrap}
#leaf{padding:16px 24px;max-width:1100px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:680px){.cols{grid-template-columns:1fr}}
.colbox{padding:12px 14px;background:var(--card);border:1px solid var(--line);border-radius:10px}
.colbox .top{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:8px}
.colbox .clab{font-size:13px;font-family:ui-monospace,monospace}
.colbox .side{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#fff;background:var(--mut);border-radius:4px;padding:1px 6px}
.colbox a.scan{color:var(--accent);font-size:12px;text-decoration:none;border-bottom:1px dotted var(--accent)}
.colbox a.scan:hover{border-bottom-color:transparent}
.words{display:flex;flex-wrap:wrap;gap:5px}
.w{font-style:italic;font-size:13px;padding:1px 8px;border:1px solid var(--line);border-radius:11px;color:var(--fg);white-space:nowrap;cursor:pointer;text-decoration:none}
.w:hover{background:var(--accent);color:#fff;border-color:var(--accent)}
.w.hl{background:var(--hl);border-color:var(--accent);font-weight:600}
.empty{color:var(--mut);font-style:italic;font-size:13px}
.na{color:var(--mut);font-style:italic;padding:20px 0}
.results{margin-bottom:14px;padding:10px 12px;border:1px dashed var(--line);border-radius:8px}
.results a{display:inline-block;margin:2px 6px 2px 0;font-size:13px}
footer{padding:14px 24px;color:var(--mut);font-size:12px;border-top:1px solid var(--line);max-width:80ch}
a{color:var(--accent)}
</style></head><body>
<header><h1>kosha — print co-location</h1>
<div class="sub">Which head-words were originally printed together on the same leaf of the scanned dictionary. The book sets <b>two columns per page</b>; each leaf is shown as its left + right column. Static snapshot of <code>/api/v1/page</code> — rendered from <code>kosha.db</code>, no live server.</div></header>
<div id="bar">
<div class="tabs" id="tabs"></div>
<span class="pager"><button id="prev" title="previous leaf">←</button><button id="next" title="next leaf">→</button></span>
<input id="jump" placeholder="go to column, e.g. 1-0004 / 741,3 / 45a">
<input id="q" placeholder="search a head-word (IAST or SLP1) across the whole dictionary…">
<span id="where"></span>
</div>
<div id="leaf"><p class="na">Loading…</p></div>
<footer>PWG column = Böhtlingk-Roth Spalte; a leaf = columns 2P−1 (LEFT) + 2P (RIGHT). MW/Apte show the columns of one physical page. <b>Caveat:</b> the source records column numbers, not the book's printed page number, so left/right <i>column</i> is exact but recto/verso of the physical leaf is not derivable here. Every head-word links to its kosha entry; 🖼 opens the Cologne scan. Built by <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_colocation_page.py">build_colocation_page.py</a> (H441).</footer>
<script>
var DICTS=__DICTS__, LABELS=__LABELS__, cur='pwg', idx=0;
// kosha lemma link — the live lemma UI is deploy-gated; until it is up we point
// head-words back into this browser at their own column (deep link), which IS live.
function lemmaHref(dict,slp1,col){return '#'+dict+'/'+encodeURIComponent(col)+'?w='+encodeURIComponent(slp1);}
var tabs=document.getElementById('tabs'),prev=document.getElementById('prev'),next=document.getElementById('next'),
    jump=document.getElementById('jump'),q=document.getElementById('q'),
    leafEl=document.getElementById('leaf'),whereEl=document.getElementById('where');
window.COLOC_DATA=window.COLOC_DATA||{};
DICTS.forEach(function(d){var b=document.createElement('button');b.textContent=LABELS[d];b.setAttribute('data-d',d);
 b.onclick=function(){go(d,0);};tabs.appendChild(b);});
function syncTabs(){var bs=tabs.querySelectorAll('button');for(var i=0;i<bs.length;i++)bs[i].classList.toggle('on',bs[i].getAttribute('data-d')===cur);}
function esc(x){return (''+(x==null?'':x)).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function data(){return window.COLOC_DATA[cur]||{leaves:[],index:{}};}
function renderLeaf(hlWord){
 var D=data(),lv=D.leaves[idx];if(!lv){leafEl.innerHTML='<p class="na">—</p>';return;}
 whereEl.textContent='leaf '+(idx+1)+' / '+D.leaves.length+'  ·  '+lv.p;
 prev.disabled=idx<=0;next.disabled=idx>=D.leaves.length-1;
 var h='<div class="cols">';
 lv.cols.forEach(function(c){
  h+='<div class="colbox"><div class="top"><span class="clab">'+esc(c.c)
    +(c.side?' <span class="side">'+(c.side==='L'?'left col':'right col')+'</span>':'')+'</span>'
    +(c.scan?'<a class="scan" href="'+esc(c.scan)+'" target="_blank" rel="noopener">🖼 scan</a>':'')+'</div>';
  if(!c.words.length){h+='<div class="empty">— no entry starts here —</div>';}
  else{h+='<div class="words">';c.words.forEach(function(w){
   var hl=hlWord&&w.slp1===hlWord;
   h+='<a class="w'+(hl?' hl':'')+'" href="'+lemmaHref(cur,w.slp1,c.c)+'" title="'+esc(w.slp1)+'">'+esc(w.iast)+'</a>';
  });h+='</div>';}
  h+='</div>';
 });
 leafEl.innerHTML=h+'</div>';
 if(hlWord){var e=leafEl.querySelector('.w.hl');if(e)e.scrollIntoView({block:'center'});}
}
function ensure(cb){if(window.COLOC_DATA[cur]){cb();return;}
 leafEl.innerHTML='<p class="na">Loading '+LABELS[cur]+'…</p>';
 var sc=document.createElement('script');sc.src='data/'+cur+'.js';
 sc.onload=cb;sc.onerror=function(){leafEl.innerHTML='<p class="na">Failed to load '+cur+' data.</p>';};
 document.head.appendChild(sc);}
function go(dict,leafIdx,hlWord){cur=dict;syncTabs();ensure(function(){
 var D=data();idx=Math.max(0,Math.min(leafIdx,D.leaves.length-1));renderLeaf(hlWord);
 writeHash();});}
function writeHash(){var D=data(),lv=D.leaves[idx];if(!lv||!lv.cols.length)return;
 var col=lv.cols[0].c;history.replaceState(null,'','#'+cur+'/'+encodeURIComponent(col));}
prev.onclick=function(){if(idx>0){idx--;renderLeaf();writeHash();}};
next.onclick=function(){if(idx<data().leaves.length-1){idx++;renderLeaf();writeHash();}};
document.addEventListener('keydown',function(e){if(e.target.tagName==='INPUT')return;
 if(e.key==='ArrowLeft')prev.click();else if(e.key==='ArrowRight')next.click();});
jump.onchange=function(){var k=jump.value.trim();var D=data();
 if(k in D.index){go(cur,D.index[k]);}else{whereEl.textContent='no column '+k;}};
// global search across the loaded dict's words
q.oninput=function(){var f=q.value.trim().toLowerCase();
 var old=document.querySelector('.results');if(old)old.remove();
 if(f.length<2)return;var D=data(),hits=[],seen={};
 for(var i=0;i<D.leaves.length&&hits.length<60;i++){var lv=D.leaves[i];
  for(var j=0;j<lv.cols.length;j++){var c=lv.cols[j];
   for(var k=0;k<c.words.length;k++){var w=c.words[k];
    if((w.iast.toLowerCase().indexOf(f)>=0||w.slp1.toLowerCase().indexOf(f)>=0)&&!seen[w.slp1+'@'+c.c]){
     seen[w.slp1+'@'+c.c]=1;hits.push({w:w,col:c.c,leaf:i});}}}}
 var box=document.createElement('div');box.className='results';
 box.innerHTML='<b>'+hits.length+(hits.length>=60?'+':'')+'</b> matches — click to open its leaf: ';
 hits.forEach(function(hit){var a=document.createElement('a');a.href='#';a.className='';a.style.fontStyle='italic';
  a.textContent=hit.w.iast+' ('+hit.col+')';a.onclick=function(ev){ev.preventDefault();go(cur,hit.leaf,hit.w.slp1);};box.appendChild(a);});
 leafEl.parentNode.insertBefore(box,leafEl);
};
function fromHash(){var m=/^#([a-z0-9]+)\/([^?]+)(?:\?w=(.*))?$/.exec(location.hash||'');
 if(!m)return false;var d=m[1];if(DICTS.indexOf(d)<0)return false;
 var col=decodeURIComponent(m[2]),w=m[3]?decodeURIComponent(m[3]):null;
 cur=d;syncTabs();ensure(function(){var D=data();var li=(col in D.index)?D.index[col]:0;idx=li;renderLeaf(w);});return true;}
window.addEventListener('hashchange',fromHash);
syncTabs();if(!fromHash())go('pwg',0);
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
        if not data["leaves"]:
            sys.stderr.write(f"  [coloc] {d}: no located entries, skipping\n")
            continue
        size = write_data(args.out, d, data)
        present.append(d)
        nwords = sum(len(c["words"]) for lf in data["leaves"] for c in lf["cols"])
        print(f"  {d}: {len(data['leaves'])} leaves, {nwords} entries "
              f"-> data/{d}.js ({size // 1024} KB)")
    write_index(args.out, present)
    print(f"wrote {args.out}/index.html  (dicts: {', '.join(present)})")


if __name__ == "__main__":
    main()
