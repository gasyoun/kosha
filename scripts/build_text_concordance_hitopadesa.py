#!/usr/bin/env python
"""Build the per-TEXT concordance pilot for the Hitopadeśa (H4034).

The INVERSE VIEW of the H1455 sense-attestation layer:

    H1455: (headword) -> (numbered PWG sense) -> (DCS attestation)
    H4034: (one TEXT: Hitopadeśa) -> every word occurrence -> (kosha senses)

the Tamilex "corpus dictionary" pattern: a full concordance of every word of a
text, feeding the dictionary. REUSES, never re-derives:

  * ../VisualDCS/src/DCS-data-2026/dcs_full.sqlite  DCS 2026 (CC BY 4.0),
    text_id 189 Hitopadeśa — tokens, lemmas, chapter refs (license-gated
    ingest discipline: measurements free, redistribution gated; the manifest
    records license + provenance, output attribution required).
  * scripts/concordance_core.py :: human_locus — the house locus format.
  * app/word_page.py :: card_token — the /w/<card>.html URL key (exact twin).
  * data/concordance/dict_corpus_concordance.tsv — the H380 DCS-lemma ->
    kosha-headword join (match_method exact/xref, confidence).
  * data/concordance/sense_corpus_concordance.tsv — the H1455 per-sense layer
    (kosha headword -> numbered PWG sense ids) — frame-limited coverage, so
    the linked-vs-unlinked share is REPORTED, never faked.
  * data/dating/work_dates.json — the H4019/H4026 era bucket for the badge
    (work_key `hitopadesa`: early-medieval via Dharmamitra).

ADDITIVE: a new data/concordance/text_hitopadesa/ fold only. No printed-order
change, no existing surface touched, no MW/kosha senses mutated.

Outputs (data/concordance/text_hitopadesa/):
  concordance.tsv   one row per distinct (surface, lemma): occurrence refs,
                    kosha headword link + PWG sense ids + /w/ card href
                    (also emitted as text_hitopadesa.js for the viewer)
  index.html        the concordance page, carrying the era badge
  MANIFEST.json     license + edition + provenance + counts
  BUILD_REPORT.md   coverage memo (forms, occurrences, linked-vs-unlinked)

Run:  python3 scripts/build_text_concordance_hitopadesa.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from concordance_core import human_locus  # noqa: E402  (REUSE house locus)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from word_page import card_token  # noqa: E402  (REUSE the /w/ URL key)

ROOT = Path(__file__).resolve().parent.parent
DCS = ROOT.parent / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"
TEXT_ID = 189
TEXT_NAME = "Hitopadeśa"
WORK_KEY = "hitopadesa"

DICT_CONC = ROOT / "data" / "concordance" / "dict_corpus_concordance.tsv"
SENSE_CONC = ROOT / "data" / "concordance" / "sense_corpus_concordance.tsv"
WORK_DATES = ROOT / "data" / "dating" / "work_dates.json"
OUT = ROOT / "data" / "concordance" / "text_hitopadesa"

ERA_CSS = {  # H4026 palette (w/ cards house style)
    "vedic": ("#a66a00",), "epic-sutra": ("#7a6ea8",), "classical": ("#3d7a68",),
    "early-medieval": ("#36679b",), "late-medieval": ("#8a5a5a",),
}


def load_lemma_join():
    """DCS lemma (IAST) -> best kosha anchor (H380 join, consumed not re-derived).

    Several anchors can claim one DCS lemma; keep the highest-confidence row
    per (dcs_lemma, anchor) and then the best anchor by (method, confidence).
    """
    by_pair = {}
    with open(DICT_CONC, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            lemma = row["dcs_lemma_iast"].strip()
            anchor = row["anchor_key_slp1"].strip()
            if not lemma or not anchor:
                continue
            conf = float(row["confidence"] or 0)
            method = row["match_method"]
            rank = (1 if method == "exact" else 0, conf)
            key = (lemma, anchor)
            if key not in by_pair or rank > by_pair[key][0]:
                by_pair[key] = (rank, row)
    best = {}
    for (lemma, anchor), (_rank, row) in by_pair.items():
        cur = best.get(lemma)
        rank = (1 if row["match_method"] == "exact" else 0, float(row["confidence"] or 0))
        if cur is None or rank > cur[0]:
            best[lemma] = (rank, anchor, row["match_method"], float(row["confidence"] or 0))
    return {lemma: (anchor, method, conf) for lemma, (_r, anchor, method, conf) in best.items()}


def load_senses():
    """kosha headword slp1 -> sorted distinct PWG sense ids (H1455 layer)."""
    senses = defaultdict(set)
    with open(SENSE_CONC, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            slp1 = row["slp1"].strip()
            sid = row["sense_id"].strip()
            if slp1 and sid:
                senses[slp1].add(sid)
    return {k: sorted(v) for k, v in senses.items()}


def load_era():
    """Era bucket for the badge (H4019/H4026 layer, verbatim)."""
    data = json.loads(WORK_DATES.read_text(encoding="utf-8"))
    rows = data.values() if isinstance(data, dict) else data
    for row in rows:
        if row.get("work_key") == WORK_KEY and row.get("era"):
            return row
    return {}


def main():
    lemma_join = load_lemma_join()
    senses = load_senses()
    era = load_era()

    con = sqlite_connect()
    cur = con.cursor()
    occ = defaultdict(list)          # (surface, lemma) -> [(ref, dcs_sent_id)]
    forms_of_lemma = defaultdict(set)
    upos_of = {}
    n_tokens = 0
    q = """
        select t.m_unsandhied, t.lemma, t.upos, c.ref, s.sent_counter,
               s.sent_subcounter, s.sent_id
        from token t
        join sentence s on s.id = t.sentence_id
        join chapter c on c.chapter_id = s.chapter_id
        where c.text_id = ?
        order by c.chapter_id, cast(s.sent_counter as integer),
                 cast(s.sent_subcounter as integer), t.idx
    """
    for surface, lemma, upos, ch_ref, sc, ssc, sent_id in cur.execute(q, (TEXT_ID,)):
        surface, lemma = (surface or "").strip(), (lemma or "").strip()
        if not surface or not lemma:
            continue
        n_tokens += 1
        ref = human_locus(TEXT_NAME, ch_ref, sc, ssc)
        occ[(surface, lemma)].append((ref, str(sent_id)))
        forms_of_lemma[lemma].add(surface)
        upos_of.setdefault((surface, lemma), upos)

    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    n_sense_linked = 0
    for (surface, lemma), refs in sorted(occ.items(), key=lambda kv: (-len(kv[1]), kv[0][0], kv[0][1])):
        anchor, method, conf = lemma_join.get(lemma, ("", "none", 0.0))
        sids = senses.get(anchor, []) if anchor else []
        if sids:
            n_sense_linked += 1
        href = "../w/%s.html" % card_token(anchor) if anchor else ""
        rows.append({
            "surface": surface,
            "lemma_iast": lemma,
            "upos": upos_of.get((surface, lemma), ""),
            "n_occ": len(refs),
            "refs": "; ".join(r for r, _ in refs),
            "n_refs": len({r for r, _ in refs}),
            "headword_slp1": anchor,
            "link_method": method,
            "conf": "%.2f" % conf if anchor else "",
            "sense_ids": "|".join(sids),
            "card_href": href,
        })

    fields = ["surface", "lemma_iast", "upos", "n_occ", "n_refs", "refs",
              "headword_slp1", "link_method", "conf", "sense_ids", "card_href"]
    tsv = OUT / "concordance.tsv"
    with open(tsv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    payload = {
        "text_name": TEXT_NAME, "work_key": WORK_KEY,
        "era": era.get("era", ""), "era_date_range": era.get("date_range", ""),
        "era_via": era.get("via", ""), "era_reason": era.get("reason", ""),
        "license": "DCS 2026 — CC BY 4.0",
        "stats": stats(n_tokens, rows, n_sense_linked),
        "rows": rows,
    }
    js = OUT / "text_hitopadesa.js"
    js.write_text(
        "window.TEXT_CONCORDANCE = window.TEXT_CONCORDANCE || {};\n"
        'window.TEXT_CONCORDANCE["hitopadesa"] = %s;\n' % json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "index.html").write_text(render_page(payload), encoding="utf-8")

    manifest = {
        "dataset": "hitopadesa-text-concordance-pilot",
        "handoff": "H4034",
        "built": "2026-09-04",
        "text": {"name": TEXT_NAME, "dcs_text_id": TEXT_NAME and TEXT_ID,
                 "chapters": "Hitop, 0–4"},
        "source": {
            "corpus": "DCS (Digital Corpus of Sanskrit) 2026",
            "file": "../VisualDCS/src/DCS-data-2026/dcs_full.sqlite",
            "license": "CC BY 4.0",
            "attribution": "Digital Corpus of Sanskrit (dcs.uni-heidelberg.de), "
                           "Oliver Hellwig; lemmatized tokens consumed verbatim.",
        },
        "rights_note": "license-gated ingest: measurements derived here are free; "
                       "bulk redistribution of the underlying corpus stays gated "
                       "(DharmaMitra memo precedent).",
        "inputs": [str(DICT_CONC.relative_to(ROOT)), str(SENSE_CONC.relative_to(ROOT)),
                   str(WORK_DATES.relative_to(ROOT))],
        "outputs": ["data/concordance/text_hitopadesa/concordance.tsv",
                    "data/concordance/text_hitopadesa/text_hitopadesa.js",
                    "data/concordance/text_hitopadesa/index.html"],
        "reuse": ["scripts/concordance_core.py::human_locus",
                  "app/word_page.py::card_token",
                  "data/concordance/dict_corpus_concordance.tsv (H380 join)",
                  "data/concordance/sense_corpus_concordance.tsv (H1455 senses)",
                  "data/dating/work_dates.json (H4019/H4026 era badge)"],
        "stats": stats(n_tokens, rows, n_sense_linked),
    }
    (OUT / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(manifest["stats"], ensure_ascii=False, indent=1))
    return 0


def sqlite_connect():
    import sqlite3
    if not DCS.exists():
        sys.exit("STOP: DCS corpus not found at %s (H4034 gate: do not substitute "
                 "an unlicensed text)" % DCS)
    return sqlite3.connect(str(DCS))


def stats(n_tokens, rows, n_sense_linked):
    n_forms = len(rows)
    n_lemmas = len({r["lemma_iast"] for r in rows})
    return {
        "tokens": n_tokens,
        "distinct_surface_lemma_pairs": n_forms,
        "distinct_lemmas": n_lemmas,
        "occurrences_listed": sum(r["n_occ"] for r in rows),
        "lemma_join_linked": sum(1 for r in rows if r["headword_slp1"]),
        "lemma_join_share_pct": round(100.0 * sum(1 for r in rows if r["headword_slp1"]) / max(n_forms, 1), 1),
        "sense_linked": n_sense_linked,
        "sense_linked_share_pct": round(100.0 * n_sense_linked / max(n_forms, 1), 1),
    }


def render_page(p):
    era = p["era"]
    color = ERA_CSS.get(era, ("#666",))[0]
    s = p["stats"]
    badge = ""
    if era:
        title = "%s — first-attestation bucket via %s (not origin)" % (era, p["era_via"])
        badge = ('<span class="ls-era" data-era="%s" title="%s">%s</span>'
                 % (era, title, era))
    drange = p["era_date_range"]
    date_html = ('<span class="drange">%s</span>' % drange) if drange else ""
    return PAGE % {
        "title": p["text_name"], "badge": badge, "drange": date_html,
        "color": color, "stats": "%s tokens · %s forms · %s lemmas · %s%% sense-linked"
        % (s["tokens"], s["distinct_surface_lemma_pairs"], s["distinct_lemmas"],
           s["sense_linked_share_pct"]),
        "js": "text_hitopadesa.js",
    }


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s — text concordance | kosha</title>
<style>
 body{font:15px/1.5 -apple-system,'Segoe UI',Roboto,sans-serif;margin:0;
      color:#222;background:#fafaf8}
 header{padding:1.2rem 1.4rem;border-bottom:1px solid #e5e2da;background:#fff}
 h1{margin:0;font-size:1.35rem}
 .sub{color:#666;font-size:.85rem;margin-top:.3rem}
 .ls-era{display:inline-block;font-size:.6rem;line-height:1.4;letter-spacing:.02em;
   text-transform:uppercase;border:1px solid %(color)s;color:%(color)s;
   border-radius:3px;padding:.05rem .4rem;margin-left:.5rem;vertical-align:middle}
 .drange{color:#888;font-size:.8rem;margin-left:.6rem}
 main{padding:1rem 1.4rem;max-width:1100px}
 #stats{font-size:.85rem;color:#555;margin-bottom:.8rem}
 input{width:100%%;max-width:420px;padding:.45rem .6rem;font-size:.95rem;
       border:1px solid #ccc;border-radius:4px;margin-bottom:.8rem}
 table{border-collapse:collapse;width:100%%;font-size:.85rem}
 th,td{text-align:left;padding:.3rem .5rem;border-bottom:1px solid #eee;vertical-align:top}
 th{position:sticky;top:0;background:#fafaf8;border-bottom:2px solid #ddd}
 td.refs{color:#555;font-size:.78rem;max-width:340px}
 td.n{text-align:right;white-space:nowrap}
 a{color:#36679b;text-decoration:none} a:hover{text-decoration:underline}
 .sid{color:#7a6ea8;font-size:.75rem;margin-right:.35rem}
 tr:hover td{background:#f4f2ec}
</style></head><body>
<header>
 <h1>%(title)s — word concordance %(badge)s %(drange)s</h1>
 <div class="sub">Every word occurrence feeding the dictionary (Tamilex corpus-dictionary
 pattern) · kosha H4034 pilot · <a href="../../concordance/index.html">concordance hub</a></div>
</header>
<main>
 <div id="stats">%(stats)s</div>
 <input id="q" placeholder="Filter by form or lemma (IAST)…" autofocus>
 <table id="t"><thead><tr>
  <th>form</th><th>lemma</th><th>pos</th><th>n</th>
  <th>occurrences (Hitop, chapter, sentence)</th><th>koshasense</th>
 </tr></thead><tbody></tbody></table>
 <p style="color:#888;font-size:.78rem">Sense ids come from the H1455 per-sense layer
 (frame-limited); era badge = first-attestation bucket in the cited corpus, not the
 origin of the text. Source: DCS 2026, CC BY 4.0.</p>
</main>
<script src="%(js)s"></script>
<script>
(function(){
 var D=window.TEXT_CONCORDANCE["hitopadesa"], tb=document.querySelector("#t tbody"),
     q=document.querySelector("#q"), rows=D.rows;
 function esc(s){return s.replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;"}[c]})}
 function render(f){
  var html="", n=0;
  for(var i=0;i<rows.length&&n<500;i++){
   var r=rows[i];
   if(f && r.surface.indexOf(f)<0 && r.lemma_iast.indexOf(f)<0) continue;
   n++;
   var senses=r.sense_ids?r.sense_ids.split("|").map(function(s){
     return '<span class="sid">'+esc(s)+'</span>'}).join(""):"",
       card=r.card_href?'<a href="'+esc(r.card_href)+'">'+esc(r.headword_slp1)+'</a>'
                        :esc(r.headword_slp1);
   html+='<tr><td><b>'+esc(r.surface)+'</b></td><td>'+esc(r.lemma_iast)+'</td><td>'
        +esc(r.upos)+'</td><td class="n">'+r.n_occ+'</td><td class="refs">'
        +esc(r.refs)+'</td><td>'+(card?senses+" "+card:"—")+'</td></tr>';
  }
  tb.innerHTML=html||'<tr><td colspan="6" style="color:#999">no rows</td></tr>';
 }
 q.addEventListener("input",function(){render(q.value.trim().toLowerCase())});
 render("");
})();
</script>
</body></html>
"""

if __name__ == "__main__":
    sys.exit(main())
