#!/usr/bin/env python3
"""Build the pilot cross-dictionary sense view (next-programme W2 / H1587).

Joins, for each of the 500 H1455 pilot headwords:
  - PWG sense rows (from sense_corpus_concordance.tsv — already sense-split)
  - MW sense glosses (from kosha.db entries+senses, read-only)
  - Apte (ap90) sense glosses if the entry exists; else honest null

Outputs:
  data/concordance/sense_crossdict_pilot.tsv
  concordance/senses/data/crossdict_pilot.js
  concordance/senses/crossdict.html  (side-by-side viewer)

Fence: never writes MW/PWG/Apte source senses; this is a sidecar only.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "concordance" / "sense_pilot_headwords.tsv"
PWG_CONC = ROOT / "data" / "concordance" / "sense_corpus_concordance.tsv"
# DB may live only on the shared main checkout (gitignored). Prefer local, fall back.
DB_CANDIDATES = [
    ROOT / "data" / "db" / "kosha.db",
    ROOT.parent / "kosha" / "data" / "db" / "kosha.db",
]
OUT_TSV = ROOT / "data" / "concordance" / "sense_crossdict_pilot.tsv"
OUT_JS = ROOT / "concordance" / "senses" / "data" / "crossdict_pilot.js"
OUT_HTML = ROOT / "concordance" / "senses" / "crossdict.html"

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def strip_markup(s: str, limit: int = 220) -> str:
    t = TAG_RE.sub(" ", s or "")
    t = WS_RE.sub(" ", t).strip()
    if len(t) > limit:
        t = t[: limit - 1] + "…"
    return t


def load_pilot() -> list[dict]:
    with PILOT.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def load_pwg_senses(pilot_keys: set[str]) -> dict[str, list[dict]]:
    """slp1 -> list of {sense_id, gloss, loci:[…], conf_max}."""
    by: dict[str, dict[str, dict]] = defaultdict(dict)
    with PWG_CONC.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            slp = (row.get("slp1") or "").strip()
            if slp not in pilot_keys:
                continue
            sid = (row.get("sense_id") or "").strip()
            if not sid:
                continue
            bucket = by[slp].setdefault(
                sid,
                {
                    "sense_id": sid,
                    "gloss": strip_markup(row.get("gloss") or "", 280),
                    "loci": [],
                    "conf_max": 0.0,
                },
            )
            try:
                conf = float(row.get("conf") or 0)
            except ValueError:
                conf = 0.0
            bucket["conf_max"] = max(bucket["conf_max"], conf)
            locus = (row.get("locus") or "").strip()
            cite = (row.get("cite") or "").strip()
            method = (row.get("method") or "").strip()
            if locus and len(bucket["loci"]) < 3:
                bucket["loci"].append(
                    {"locus": locus, "cite": cite, "method": method}
                )
    return {
        k: sorted(v.values(), key=lambda x: x["sense_id"]) for k, v in by.items()
    }


def find_db() -> Path:
    for p in DB_CANDIDATES:
        if p.is_file():
            return p
    raise SystemExit(
        "kosha.db not found (gitignored). Place it under data/db/ or the main clone."
    )


def load_dict_senses(
    con: sqlite3.Connection, dict_code: str, pilot_keys: set[str]
) -> dict[str, list[dict]]:
    """slp1 -> [{sense_n, gloss, L}] from kosha.db (read-only)."""
    out: dict[str, list[dict]] = defaultdict(list)
    # Match pilot keys case-sensitively on slp1_key
    q = (
        "SELECT e.id, e.L, e.slp1_key, e.body, s.sense_n, s.span_start, s.span_end "
        "FROM entries e JOIN senses s ON s.entry_id = e.id "
        "WHERE e.dict = ? AND e.slp1_key = ? ORDER BY s.sense_n"
    )
    for key in pilot_keys:
        rows = con.execute(q, (dict_code, key)).fetchall()
        if not rows:
            continue
        for _id, L, slp, body, sn, s0, s1 in rows:
            gloss = strip_markup(body[s0:s1] if body else "")
            out[slp].append(
                {
                    "sense_id": f"{dict_code}:{L}:{sn}",
                    "sense_n": sn,
                    "L": L,
                    "gloss": gloss,
                }
            )
    return out


def write_tsv(rows: list[dict]) -> None:
    fields = [
        "lemma_slp1",
        "hom",
        "pwg_sense_id",
        "pwg_gloss",
        "pwg_loci",
        "mw_sense_id",
        "mw_gloss",
        "apte_sense_id",
        "apte_gloss",
        "confidence",
        "note",
    ]
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_TSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_js(pilot: list[dict], payload: dict) -> None:
    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    stats = {
        "n_pilot": len(pilot),
        "n_lemmas_emitted": len(payload),
        "build_date": date.today().isoformat(),
        "source_pilot": "data/concordance/sense_pilot_headwords.tsv",
        "source_pwg": "data/concordance/sense_corpus_concordance.tsv",
        "source_mw_apte": "kosha.db entries+senses (read-only)",
        "scope": "pilot 500 only — not full inventory",
    }
    body = (
        "/* Auto-generated by scripts/build_sense_crossdict_pilot.py — do not edit. */\n"
        "window.CROSSDICT_STATS = "
        + json.dumps(stats, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
        "window.CROSSDICT = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
    )
    OUT_JS.write_text(body, encoding="utf-8")


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>kosha — pilot cross-dict sense view (PWG · MW · Apte)</title>
<style>
:root { --ink:#222; --mut:#667; --line:#ddd; --bg:#faf9f6; --card:#fff;
        --pwg:#0a7a2f; --mw:#1a6fb0; --apte:#a05a00; }
* { box-sizing:border-box; }
body { margin:0; font:15px/1.5 Georgia,'Times New Roman',serif; color:var(--ink); background:var(--bg); }
header { background:#2b3a4a; color:#fff; padding:14px 20px; }
header h1 { margin:0; font-size:18px; font-weight:normal; }
header .sub { font-size:12.5px; opacity:.78; margin-top:3px; }
main { max-width:1100px; margin:0 auto; padding:16px 20px 60px; }
#q { width:100%; font-size:18px; padding:9px 12px; border:1px solid var(--line); border-radius:6px; font-family:inherit; }
#hint { font-size:12.5px; color:var(--mut); margin:6px 2px 14px; }
#matches a { display:inline-block; margin:2px 8px 2px 0; font-size:14px; font-family:Consolas,monospace; }
.entry { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:14px 16px; margin:14px 0; }
.hw { font-size:22px; font-family:Consolas,monospace; }
.cols { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-top:12px; }
@media (max-width:800px){ .cols { grid-template-columns:1fr; } }
.col { border:1px solid var(--line); border-radius:8px; padding:10px 12px; background:#fff; }
.col h3 { margin:0 0 8px; font-size:13px; text-transform:uppercase; letter-spacing:.04em; color:#fff;
  border-radius:6px; padding:3px 8px; display:inline-block; font-weight:normal; }
.col.pwg h3 { background:var(--pwg); }
.col.mw h3 { background:var(--mw); }
.col.apte h3 { background:var(--apte); }
.sense { border-top:1px solid #eee; margin-top:8px; padding-top:7px; font-size:13.5px; }
.sid { font-family:Consolas,monospace; font-size:11.5px; color:var(--mut); margin-right:6px; }
.null { color:var(--mut); font-style:italic; font-size:13px; }
.loci { font-size:12px; color:var(--mut); margin-top:3px; }
#trust { border-top:2px solid var(--line); margin-top:34px; padding-top:12px; font-size:12.5px; color:var(--mut); }
.none { color:var(--mut); font-style:italic; }
a { color:#1a6fb0; }
.banner { background:#fff6e0; border:1px solid #e8d5a0; border-radius:8px; padding:8px 12px;
  font-size:13px; margin:0 0 14px; }
</style>
</head>
<body>
<header>
  <h1>Pilot cross-dict sense view <span style="opacity:.6">· W2 · kosha</span></h1>
  <div class="sub">Side-by-side PWG · MW · Apte sense columns for the <b>500-headword pilot only</b>
  (sense-reconciliation wave-2). Not a full inventory; MW order is never rewritten.</div>
</header>
<main>
  <div class="banner"><b>Pilot scope.</b> Full-inventory reconciliation is deferred. Human sample / review-sheet
  remains ~6 months out. Null Apte/MW columns are honest gaps, not errors.</div>
  <input id="q" placeholder="Type a pilot headword (SLP1), e.g. nAgadanta …" autocomplete="off">
  <div id="hint">Source: H1455 pilot list · PWG from sense_corpus_concordance · MW/Apte glosses from kosha.db (read-only).</div>
  <div id="matches"></div>
  <div id="out"></div>
  <div id="trust">
    <b>Trust block.</b> Pilot n = <span id="n">?</span> · build <span id="bd">?</span>.
    Artefacts:
    <a href="https://github.com/gasyoun/kosha/blob/main/data/concordance/sense_crossdict_pilot.tsv">sense_crossdict_pilot.tsv</a>
    (CSV download) ·
    <a href="https://github.com/gasyoun/kosha/blob/main/data/concordance/sense_pilot_headwords.tsv">sense_pilot_headwords.tsv</a> ·
    <a href="https://github.com/gasyoun/kosha/blob/main/data/concordance/sense_corpus_concordance.tsv">sense_corpus_concordance.tsv</a>.
    Sibling PWG-only KWIC: <a href="./">concordance/senses/</a>. Fence: MW/kosha <code>senses</code> bytes unchanged.
  </div>
</main>
<script src="data/crossdict_pilot.js"></script>
<script>
function esc(t){ var d=document.createElement('div'); d.textContent=t||''; return d.innerHTML; }
function renderSenses(list, kind){
  if(!list || !list.length) return '<p class="null">null — no '+esc(kind)+' senses for this pilot lemma in the joined store</p>';
  return list.map(function(s){
    var h = '<div class="sense"><span class="sid">'+esc(s.sense_id||s.sense_n||'')+'</span>'+esc(s.gloss||'');
    if(s.loci && s.loci.length){
      h += '<div class="loci">'+s.loci.map(function(L){
        return esc(L.method||'')+': '+esc(L.locus||'')+(L.cite?' ('+esc(L.cite)+')':'');
      }).join(' · ')+'</div>';
    }
    return h+'</div>';
  }).join('');
}
function show(key){
  var e = (window.CROSSDICT||{})[key];
  var out = document.getElementById('out');
  if(!e){ out.innerHTML = '<p class="none">Not in pilot: '+esc(key)+'</p>'; return; }
  out.innerHTML = '<div class="entry"><div class="hw">'+esc(key)+
    (e.hom?' <span style="color:var(--mut);font-size:14px">hom '+esc(e.hom)+'</span>':'')+
    '</div><div class="cols">'+
    '<div class="col pwg"><h3>PWG</h3>'+renderSenses(e.pwg,'PWG')+'</div>'+
    '<div class="col mw"><h3>MW</h3>'+renderSenses(e.mw,'MW')+'</div>'+
    '<div class="col apte"><h3>Apte (ap90)</h3>'+renderSenses(e.apte,'Apte')+'</div>'+
    '</div></div>';
  history.replaceState(null,'','#'+encodeURIComponent(key));
}
function browse(prefix){
  var keys = Object.keys(window.CROSSDICT||{}).filter(function(k){
    return !prefix || k.indexOf(prefix)===0;
  }).sort();
  var m = document.getElementById('matches');
  m.innerHTML = keys.slice(0,80).map(function(k){
    return '<a href="#'+esc(k)+'" data-k="'+esc(k)+'">'+esc(k)+'</a>';
  }).join(' ');
  m.querySelectorAll('a').forEach(function(a){
    a.onclick=function(ev){ ev.preventDefault(); show(a.dataset.k); };
  });
  if(keys.length) show(keys[0]);
  else document.getElementById('out').innerHTML='<p class="none">No pilot match for prefix.</p>';
}
var q = document.getElementById('q');
q.addEventListener('change', function(){ browse(q.value.trim()); });
q.addEventListener('keydown', function(ev){ if(ev.key==='Enter') browse(q.value.trim()); });
if(window.CROSSDICT_STATS){
  document.getElementById('n').textContent = window.CROSSDICT_STATS.n_pilot;
  document.getElementById('bd').textContent = window.CROSSDICT_STATS.build_date;
}
if(location.hash.length>1){
  var h = decodeURIComponent(location.hash.slice(1));
  q.value = h; show(h);
} else {
  browse('nAga'); // includes nAgadanta smoke
}
</script>
</body>
</html>
"""


def main() -> None:
    pilot = load_pilot()
    pilot_keys = {(r.get("slp1") or "").strip() for r in pilot if r.get("slp1")}
    print(f"pilot headwords: {len(pilot_keys)}")
    pwg = load_pwg_senses(pilot_keys)
    print(f"pilot with ≥1 PWG sense row: {len(pwg)}")

    db = find_db()
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    mw = load_dict_senses(con, "mw", pilot_keys)
    apte = load_dict_senses(con, "ap90", pilot_keys)
    print(f"pilot with MW senses: {len(mw)}  · Apte: {len(apte)}")

    tsv_rows: list[dict] = []
    payload: dict[str, dict] = {}
    for r in pilot:
        key = (r.get("slp1") or "").strip()
        if not key:
            continue
        hom = (r.get("hom") or "").strip()
        pwg_s = pwg.get(key, [])
        mw_s = mw.get(key, [])
        ap_s = apte.get(key, [])
        payload[key] = {
            "hom": hom,
            "pwg": pwg_s,
            "mw": mw_s,
            "apte": ap_s,
        }
        # Flatten: one TSV row per PWG sense if any, else one null-PWG row
        if pwg_s:
            for i, ps in enumerate(pwg_s):
                mw0 = mw_s[i] if i < len(mw_s) else (mw_s[0] if mw_s and i == 0 else {})
                ap0 = ap_s[i] if i < len(ap_s) else (ap_s[0] if ap_s and i == 0 else {})
                # Only attach MW/Apte on first row to avoid implying sense-alignment
                if i > 0:
                    mw0, ap0 = {}, {}
                tsv_rows.append(
                    {
                        "lemma_slp1": key,
                        "hom": hom,
                        "pwg_sense_id": ps.get("sense_id", ""),
                        "pwg_gloss": ps.get("gloss", ""),
                        "pwg_loci": "; ".join(
                            x.get("locus", "") for x in ps.get("loci") or []
                        ),
                        "mw_sense_id": mw0.get("sense_id", "") if i == 0 else "",
                        "mw_gloss": (
                            " | ".join(m.get("gloss", "") for m in mw_s) if i == 0 else ""
                        ),
                        "apte_sense_id": ap0.get("sense_id", "") if i == 0 else "",
                        "apte_gloss": (
                            " | ".join(a.get("gloss", "") for a in ap_s) if i == 0 else ""
                        ),
                        "confidence": f"{ps.get('conf_max', 0):.2f}",
                        "note": "pilot; MW/Apte columns are inventory not sense-aligned",
                    }
                )
        else:
            tsv_rows.append(
                {
                    "lemma_slp1": key,
                    "hom": hom,
                    "pwg_sense_id": "",
                    "pwg_gloss": "",
                    "pwg_loci": "",
                    "mw_sense_id": mw_s[0]["sense_id"] if mw_s else "",
                    "mw_gloss": " | ".join(m.get("gloss", "") for m in mw_s),
                    "apte_sense_id": ap_s[0]["sense_id"] if ap_s else "",
                    "apte_gloss": " | ".join(a.get("gloss", "") for a in ap_s),
                    "confidence": "",
                    "note": "no PWG sense rows in concordance for this pilot key",
                }
            )

    write_tsv(tsv_rows)
    write_js(pilot, payload)
    OUT_HTML.write_text(HTML, encoding="utf-8")

    # Smoke: nAgadanta must have distinct PWG a/b if present
    nag = payload.get("nAgadanta", {})
    pwg_ids = [s.get("sense_id") for s in nag.get("pwg") or []]
    print(f"nAgadanta PWG sense_ids: {pwg_ids}")
    print(
        f"wrote {OUT_TSV.relative_to(ROOT)} rows={len(tsv_rows)}  "
        f"js={OUT_JS.stat().st_size}B  html={OUT_HTML.stat().st_size}B"
    )


if __name__ == "__main__":
    main()
