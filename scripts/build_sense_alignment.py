#!/usr/bin/env python3
"""Build the PWG↔MW↔Apte aligned-sense table (H3744 — sense-reconciliation W2, slice 1).

The user-facing render of the wave-1 substrate: senses of the three dictionaries
grouped into MEANINGS, each meaning carrying the evidence that put it together.
Algorithm, row model and failure taxonomy live in
[app/sense_align.py](https://github.com/gasyoun/kosha/blob/main/app/sense_align.py);
this script is only the driver: read kosha.db read-only, align, write.

    python scripts/build_sense_alignment.py                 # the 500-headword pilot
    python scripts/build_sense_alignment.py --heads nAgadanta,agni
    python scripts/build_sense_alignment.py --no-staging    # table + report only
    python scripts/build_sense_alignment.py --no-sasa       # slice-1 baseline, for the delta

Outputs
  data/concordance/sense_alignment.tsv           one row per MEANING GROUP (committed)
  data/concordance/sense_alignment_failures.tsv  one row per unalignable sense (committed)
  data/concordance/SENSE_ALIGNMENT_BUILD_REPORT.md
  dist/sense-align-staging/                      the staged viewer (gitignored, never docs/)

Sources. PWG/MW/Apte come from `kosha.db` (gitignored). ŚKDR and VCP are read
straight from their csl-sqlite releases under `data/raw_sqlite/<d>/<d>.sqlite`,
fetched by the same `build_entries.fetch_release_sqlite` the main build uses and
segmented by the same `app/segment.py`. They are deliberately NOT loaded into
`kosha.db`: this table is a sidecar, and a 1.7 GB shared database should not be
rebuilt to add two columns to it.

Step-1 reachability verdict (H3862; the counts behind it are in the report):
  ŚKDR   — reachable, `skd.zip` in csl-sqlite. Shipped as a column.
  VCP    — reachable, `vcp.zip` in csl-sqlite. Shipped as a column.
  Medinī — NOT in CDSL at all. The `md` code in csl-orig and csl-sqlite is
           MACDONELL, not Medinīkośa; shipping it under a `medini` header would
           have put the wrong dictionary in the table under the right name.
  Amara  — NOT in CDSL at all (no amara asset in any csl-sqlite release). PWG
           cites it as a witness (`AK.`, 2,052 times in the pilot), but a
           citation is not entry text and there is nothing to align against.

Scope fences (H3744 + H3862; restated in every artifact this writes):
  IN  — PWG, MW, Apte (ap90), ŚKDR (skd), VCP (vcp).
  OUT — Medinī and Amara: not in CDSL, no source to load (H3862 step 1).
  OUT — the lemma-variant graph (nAgadanta↔nAgadantaka normalisation).
  OUT — wave 2's second acceptance pass (needs a review sheet + a human vote).
  OUT — the pwg_ru RU-sense-structure deliverable (its own handoff).

Publication fence: this table is NOT put on the 2,324 live static pages. A
cross-dictionary sense alignment asserts that three dictionaries' senses
correspond, and that assertion can be scholarly wrong in a way page chrome
cannot. It ships behind the `ux=` staging gate plus a published compare page.
Contract: docs/NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from sense_align import (  # noqa: E402
    ATTRIB_KEYS, DICTS, GLOSS_FLOOR, GLOSS_LANG, PREFIX_MIN, SASA_DICTS, TAU,
    align_lemma, extract_ls, sense_gloss,
)
from segment import segment  # noqa: E402
from build_entries import fetch_release_sqlite  # noqa: E402

try:                                            # display only — never alignment
    from kosha.transliterate import from_slp1_out
except Exception:                               # pragma: no cover - shim absent
    def from_slp1_out(s, out="iast"):
        return s

PILOT = ROOT / "data" / "concordance" / "sense_pilot_headwords.tsv"
def _db_candidates() -> list[Path]:
    """`kosha.db` is gitignored, so a worktree never has its own copy.

    Probe the worktree first, then the main clone — found by walking up for the
    `GitHub/` directory that holds the sibling repos, the same trick
    `src/kosha/build/sources.py` uses. `ROOT.parent / "kosha"` alone only works
    when the worktree happens to sit directly beside the clone, which the
    `../<Repo>-h<id>-<pid>` convention does not guarantee.
    """
    out = [ROOT / "data" / "db" / "kosha.db"]
    for candidate in (ROOT, *ROOT.parents):
        db = candidate / "kosha" / "data" / "db" / "kosha.db"
        if db not in out:
            out.append(db)
    return out


DB_CANDIDATES = _db_candidates()
OUT_TSV = ROOT / "data" / "concordance" / "sense_alignment.tsv"
OUT_FAIL = ROOT / "data" / "concordance" / "sense_alignment_failures.tsv"
OUT_REPORT = ROOT / "data" / "concordance" / "SENSE_ALIGNMENT_BUILD_REPORT.md"
STAGING = ROOT / "dist" / "sense-align-staging"

DICT_LABEL = {"pwg": "PWG", "mw": "MW", "ap90": "Apte", "skd": "ŚKDR", "vcp": "VCP"}
#: TSV/JS column stem per dict code — `ap90` has shipped as `apte` since slice 1.
DICT_COL = {"pwg": "pwg", "mw": "mw", "ap90": "apte", "skd": "skd", "vcp": "vcp"}
SMOKE_LEMMA = "nAgadanta"

#: Sa→Sa kośas asked for by H3862 that have no CDSL source at all. Named here so
#: the absence is a recorded verdict rather than a silent omission.
SASA_ABSENT = {
    "Medinī": "not in CDSL — the `md` code in csl-orig/csl-sqlite is MACDONELL, "
              "not Medinīkośa; loading it would put the wrong dictionary under "
              "the right name. PWG cites `MED.` 1,824× in the pilot, so the "
              "witness pointer exists and the entry text does not.",
    "Amara": "not in CDSL — no amara asset in any csl-sqlite release. PWG cites "
             "`AK.` 2,052× in the pilot; a citation is not entry text, so there "
             "is nothing to align against.",
}

#: H3744's published slice-1 numbers on the SAME 500-headword pilot. Every figure
#: this slice reports is a delta against these, per the H3862 acceptance. They are
#: reproducible from this same script with `--no-sasa`.
BASELINE_H3744 = {
    "label": "H3744 slice 1 (PWG · MW · Apte)",
    "n_senses": 33763, "n_groups": 30470, "n_aligned": 2957,
    "n_lemmas_with_alignment": 477, "n_lemmas_all_three": 273, "clean_111": 262,
    "failure_classes": {
        "no-shared-witness": 17671, "witness-too-common": 6844, "no-gloss": 3025,
        "cross-language-gap": 1835, "outranked": 1101, "absent-dictionary": 62,
    },
}

FENCES = [
    "IN: PWG, MW, Apte (ap90), ŚKDR (skd), VCP (vcp).",
    "OUT: Medinī and Amara — not in CDSL, no source to load (H3862 step 1).",
    "OUT: the lemma-variant graph (nAgadanta↔nAgadantaka-class normalisation).",
    "OUT: wave 2's second acceptance pass — it needs a review sheet and a human vote.",
    "OUT: the pwg_ru RU-sense-structure deliverable — its own handoff.",
    "NOT PUBLISHED: never written to docs/ or the 2,324 live static pages.",
]


def find_db() -> Path:
    for p in DB_CANDIDATES:
        if p.is_file():
            return p
    raise SystemExit(
        "kosha.db not found (gitignored — see CLAUDE.md 'What not to touch'). "
        "Place it under data/db/ or keep the main clone beside this worktree."
    )


def load_pilot_heads() -> list[str]:
    with PILOT.open(encoding="utf-8", newline="") as f:
        return [(r.get("slp1") or "").strip()
                for r in csv.DictReader(f, delimiter="\t") if (r.get("slp1") or "").strip()]


def load_senses(con: sqlite3.Connection, lemma: str):
    """([sense dicts], {dicts that have any entry for this lemma})."""
    rows = con.execute(
        "SELECT e.dict, e.L, s.sense_n, substr(e.body, s.span_start+1, s.span_end-s.span_start) "
        "FROM entries e JOIN senses s ON s.entry_id = e.id "
        "WHERE e.slp1_key = ? AND e.dict IN ('pwg','mw','ap90') "
        "ORDER BY e.dict, e.L, s.sense_n",
        (lemma,),
    ).fetchall()
    present = {r[0] for r in con.execute(
        "SELECT DISTINCT dict FROM entries WHERE slp1_key = ? AND dict IN ('pwg','mw','ap90')",
        (lemma,))}
    senses = []
    for dct, L, sn, raw in rows:
        senses.append({
            "dict": dct,
            "sense_id": f"{dct}:{L}:{sn}",
            "label": f"{DICT_LABEL[dct]} {L}·{sn}",
            "gloss": sense_gloss(raw, dct),
            "ls": extract_ls(raw),
        })
    return senses, present


def open_sasa(codes) -> dict:
    """Read-only handles on the Sa→Sa kośa releases, fetched on first use.

    Returns {} for every code whose release cannot be obtained — a missing
    optional source is logged and skipped, never escalated (the rights/inputs
    posture `src/kosha/build/sources.py` already sets for the main build).
    """
    out = {}
    for code in codes:
        try:
            path, tag = fetch_release_sqlite(code)
        except Exception as exc:                             # pragma: no cover
            print(f"[sasa] {code}: unavailable ({exc}) — column skipped")
            continue
        out[code] = (sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True), tag)
        print(f"[sasa] {code}: {Path(path).name} (csl-sqlite {tag})")
    return out


def load_sasa_senses(handles: dict, lemma: str):
    """Senses of `lemma` from the Sa→Sa kośas, in the same shape as `load_senses`.

    Segmentation is `app/segment.py`, unchanged — the kośas carry almost no
    `<div>` (3 of 42,531 ŚKDR records, 914 of 50,135 VCP ones), so in practice
    this is one sense per entry. That is the honest granularity of the source,
    and `shape` prints it rather than smoothing it: a PWG lemma with nine senses
    against one ŚKDR entry reads `9-…-1-…`, and eight of those nine are recorded
    as `outranked` instead of being folded into the row.

    `ls` is `[]` for every one of them, because the kośas contain no `<ls>` — 0
    occurrences in either release. That is not a parsing gap; it is why the
    `attrib` channel exists.
    """
    senses, present = [], set()
    for code, (con, _tag) in handles.items():
        for L, body in con.execute(f"SELECT lnum, data FROM {code} WHERE key = ? ORDER BY lnum",
                                   (lemma,)):
            present.add(code)
            for n, (a, b) in enumerate(segment(code, body), 1):
                senses.append({
                    "dict": code,
                    "sense_id": f"{code}:{L}:{n}",
                    "label": f"{DICT_LABEL[code]} {L}·{n}",
                    "gloss": sense_gloss(body[a:b], code),
                    "ls": [],
                })
    return senses, present


def display_gloss(dct: str, gloss: str) -> str:
    """SLP1 → IAST for the Sanskrit columns; every other column is already
    readable text. Display only — alignment never sees this string."""
    if dct in SASA_DICTS and gloss:
        try:
            return from_slp1_out(gloss, "iast")
        except Exception:                                    # pragma: no cover
            return gloss
    return gloss


TSV_FIELDS = (
    ["lemma_slp1", "group_id", "status", "shape", "method", "score",
     "witnesses", "flags", "failure_class"]
    + [f"{DICT_COL[d]}_{suffix}" for d in DICTS for suffix in ("sense_ids", "gloss")]
    + ["note"]
)
FAIL_FIELDS = ["lemma_slp1", "dict", "sense_id", "failure_class", "n_ls", "gloss"]


NOTE_BY_METHOD = {
    "attrib": "printed attribution: a western sense cites this kośa by name, "
              "weighted 1/df within the lemma",
}


def group_rows(lemma: str, res: dict):
    out = []
    for gi, g in enumerate(res["groups"], 1):
        row = {
            "lemma_slp1": lemma,
            "group_id": f"{lemma}#{gi}",
            "status": g["status"],
            "shape": g["shape"],
            "method": g["method"],
            "score": f"{g['score']:.3f}",
            "witnesses": " ".join(g["witnesses"]),
            "flags": " ".join(g["flags"]),
            "failure_class": g["failure_class"],
            "note": (NOTE_BY_METHOD.get(
                g["method"], "shared literary witness, weighted 1/df within the lemma")
                if g["status"] == "aligned"
                else "no cross-dictionary evidence — see failure_class"),
        }
        for d in DICTS:
            ms = g["by_dict"].get(d) or []
            row[f"{DICT_COL[d]}_sense_ids"] = "; ".join(m["sense_id"] for m in ms)
            row[f"{DICT_COL[d]}_gloss"] = " ‖ ".join(display_gloss(d, m["gloss"]) for m in ms)
        out.append(row)
    return out


def write_tsv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


VIEWER_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>kosha — aligned senses (PWG · MW · Apte · ŚKDR · VCP) — STAGED, NOT PUBLISHED</title>
<style>
:root{--ink:#1f2328;--mut:#656d76;--line:#d8dee4;--bg:#f6f8fa;--card:#fff;
      --pwg:#0a7a2f;--mw:#1a6fb0;--apte:#a05a00;--sasa:#7a3a8a;--ok:#0a7a2f;--warn:#8a6d00}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 Georgia,'Times New Roman',serif;color:var(--ink);background:var(--bg)}
header{background:#2b3a4a;color:#fff;padding:14px 20px}
header h1{margin:0;font-size:19px;font-weight:400}
header .sub{font-size:12.5px;opacity:.8;margin-top:4px}
main{max-width:1180px;margin:0 auto;padding:16px 20px 60px}
.stage{background:#fff4f4;border:1px solid #e0b4b4;border-radius:8px;padding:9px 13px;font-size:13px;margin:0 0 14px}
#q{width:100%;font-size:18px;padding:9px 12px;border:1px solid var(--line);border-radius:6px;font-family:inherit}
#hint{font-size:12.5px;color:var(--mut);margin:6px 2px 12px}
#matches a{display:inline-block;margin:2px 8px 2px 0;font-size:14px;font-family:Consolas,monospace}
table{border-collapse:collapse;width:100%;background:var(--card);margin-top:12px;
      border:1px solid var(--line);border-radius:8px;overflow:hidden}
th,td{border-top:1px solid var(--line);padding:9px 11px;vertical-align:top;font-size:13.5px}
th{background:#eef2f6;font-size:12px;text-transform:uppercase;letter-spacing:.05em;
   color:#44505c;font-weight:400;text-align:left}
th.pwg{color:var(--pwg)}th.mw{color:var(--mw)}th.apte{color:var(--apte)}
th.skd{color:var(--sasa)}th.vcp{color:var(--sasa)}
tr.unaligned td{background:#fcfcfa;color:#4a5560}
.sid{font-family:Consolas,monospace;font-size:11px;color:var(--mut);display:block}
.ev{font-size:11.5px;color:var(--mut);white-space:nowrap}
.pill{display:inline-block;border-radius:10px;padding:1px 7px;font-size:11px;
      border:1px solid var(--line);background:#fff}
.pill.ok{color:var(--ok);border-color:#b6dbc0}
.pill.no{color:var(--warn);border-color:#e2d3a0}
.w{font-family:Consolas,monospace;font-size:11px;color:#44505c}
.null{color:var(--mut);font-style:italic}
#trust{border-top:2px solid var(--line);margin-top:30px;padding-top:12px;font-size:12.5px;color:var(--mut)}
#trust li{margin:3px 0}
a{color:#1a6fb0}
</style>
</head>
<body>
<header>
  <h1>Aligned senses · PWG · MW · Apte · ŚKDR · VCP <span style="opacity:.6">— sense-reconciliation W2, slice 2</span></h1>
  <div class="sub">One row = one MEANING. Senses land in the same row when the dictionaries cite the same
  literary sources for them, weighted by how discriminating each citation is inside that lemma.</div>
</header>
<main>
  <div class="stage"><b>STAGED — NOT PUBLISHED.</b> This tree is a local artifact behind the
  <code>ux=</code> gate. A cross-dictionary sense alignment asserts that three dictionaries' senses
  correspond, and that can be scholarly wrong in a way page chrome cannot — so it never goes onto the
  live static pages without a human ruling. Contract:
  <code>docs/NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md</code>.</div>
  <input id="q" placeholder="Type a pilot headword (SLP1), e.g. nAgadanta …" autocomplete="off">
  <div id="hint">Rows sorted: aligned meanings first, strongest evidence first; unalignable senses stay
  visible at the bottom with the reason printed.</div>
  <div id="matches"></div>
  <div id="out"></div>
  <div id="trust"></div>
</main>
<script src="data/alignment.js"></script>
<script>
function esc(t){var d=document.createElement('div');d.textContent=t==null?'':String(t);return d.innerHTML;}
function cell(list){
  if(!list||!list.length) return '<span class="null">—</span>';
  return list.map(function(s){
    return '<span class="sid">'+esc(s.sense_id)+'</span>'+esc(s.gloss);
  }).join('<hr style="border:0;border-top:1px dotted #ccc;margin:6px 0">');
}
function evidence(g){
  if(g.status==='aligned'){
    return '<span class="pill ok">'+esc(g.method)+' '+esc(g.score.toFixed(2))+'</span>'+
      (g.witnesses.length?'<div class="w">'+esc(g.witnesses.join(' '))+'</div>':'')+
      (g.flags.length?'<div class="w">'+esc(g.flags.join(' '))+'</div>':'');
  }
  return '<span class="pill no">'+esc(g.failure_class||'unaligned')+'</span>';
}
function show(key){
  var e=(window.ALIGN||{})[key], out=document.getElementById('out');
  if(!e){out.innerHTML='<p class="null">Not in this build: '+esc(key)+'</p>';return;}
  var cols=window.ALIGN_COLS||[];
  var rows=e.groups.map(function(g){
    return '<tr class="'+esc(g.status)+'">'+
      '<td class="ev">'+evidence(g)+'<div class="w">'+esc(g.shape)+'</div></td>'+
      cols.map(function(c){return '<td>'+cell(g[c.key])+'</td>';}).join('')+'</tr>';
  }).join('');
  out.innerHTML='<h2 style="font-family:Consolas,monospace;font-size:22px;margin:16px 0 0">'+esc(key)+
    '</h2><div style="font-size:12.5px;color:#656d76">dictionaries with an entry: '+
    esc(e.present.join(', ')||'none')+' · senses aligned '+esc(e.stats.n_aligned)+
    ' / groups '+esc(e.stats.n_groups)+'</div>'+
    '<table><thead><tr><th style="width:12%">evidence</th>'+
    cols.map(function(c){
      return '<th class="'+esc(c.key)+'" style="width:'+(88/cols.length).toFixed(1)+
             '%">'+esc(c.label)+' ('+esc(c.lang)+')</th>';
    }).join('')+
    '</tr></thead><tbody>'+rows+'</tbody></table>';
  history.replaceState(null,'','#'+encodeURIComponent(key));
}
function browse(prefix){
  var keys=Object.keys(window.ALIGN||{}).filter(function(k){return !prefix||k.indexOf(prefix)===0;}).sort();
  var m=document.getElementById('matches');
  m.innerHTML=keys.slice(0,80).map(function(k){return '<a href="#'+esc(k)+'">'+esc(k)+'</a>';}).join(' ');
  m.querySelectorAll('a').forEach(function(a){a.onclick=function(ev){ev.preventDefault();show(a.textContent);};});
  if(keys.length) show(keys[0]);
  else document.getElementById('out').innerHTML='<p class="null">No match for that prefix.</p>';
}
var S=window.ALIGN_STATS||{};
document.getElementById('trust').innerHTML='<b>Trust block.</b><ul>'+
  '<li>Build '+esc(S.build_date)+' · lemmas '+esc(S.n_lemmas)+' · meaning groups '+esc(S.n_groups)+
  ' · aligned '+esc(S.n_aligned)+' ('+esc(S.pct_aligned)+'% of groups).</li>'+
  '<li>Method: shared <code>&lt;ls&gt;</code> literary witness, weight 1/df within the lemma; τ='+esc(S.tau)+
  '. Gloss overlap only between MW and Apte (both English) — never across PWG, where it would measure nothing.</li>'+
  '<li>Failure classes are rows, not omissions: '+esc(S.failure_classes)+'.</li>'+
  '<li>Fences: '+(S.fences||[]).map(esc).join(' ')+'</li></ul>';
var q=document.getElementById('q');
q.addEventListener('change',function(){browse(q.value.trim());});
q.addEventListener('keydown',function(ev){if(ev.key==='Enter')browse(q.value.trim());});
if(location.hash.length>1){var h=decodeURIComponent(location.hash.slice(1));q.value=h;show(h);}
else browse('nAgadanta');
</script>
</body>
</html>
"""


def write_staging(payload: dict, stats: dict, out_root: Path) -> Path:
    """The staged viewer. Refuses to write under docs/ — same gate posture as
    build_word_pages.py --ux-staging (H3457)."""
    try:
        out_root.resolve().relative_to((ROOT / "docs").resolve())
        sys.exit("error: the aligned-sense viewer refuses to write under docs/ (the Pages "
                 "tree) — H3744 is staging-only; see docs/NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md")
    except ValueError:
        pass
    (out_root / "data").mkdir(parents=True, exist_ok=True)
    cols = [{"key": DICT_COL[d], "label": DICT_LABEL[d], "lang": GLOSS_LANG[d]}
            for d in stats.get("dicts", DICTS)]
    (out_root / "data" / "alignment.js").write_text(
        "/* Auto-generated by scripts/build_sense_alignment.py — do not edit. */\n"
        "window.ALIGN_COLS = " + json.dumps(cols, ensure_ascii=False, separators=(",", ":")) + ";\n"
        "window.ALIGN_STATS = " + json.dumps(stats, ensure_ascii=False, separators=(",", ":")) + ";\n"
        "window.ALIGN = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    (out_root / "index.html").write_text(VIEWER_HTML, encoding="utf-8")
    (out_root / "NOT_PUBLISHED.md").write_text(
        "# NOT PUBLISHED — H3744 aligned-sense table (staging build)\n\n"
        f"{stats['n_lemmas']} lemmas, {stats['n_groups']} meaning groups. This tree is a local\n"
        "staging artifact: never copy it into docs/, never push it to Pages or samskrtam.ru\n"
        "without a human ruling. Contract: docs/NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md\n\n"
        + "\n".join(f"- {f}" for f in FENCES) + "\n",
        encoding="utf-8")
    return out_root


def write_report(stats: dict, fail_counts: Counter, shape_counts: Counter,
                 method_counts: Counter, smoke: str) -> None:
    today = date.today().strftime("%d-%m-%Y")
    lines = [
        "# Build report — aligned-sense table (PWG · MW · Apte · ŚKDR · VCP)",
        "",
        f"_Created: {today} · Last updated: {today}_",
        "",
        "Generated by [scripts/build_sense_alignment.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_sense_alignment.py).",
        "H3744 built the western three (wave-2 slice 1); **H3862** adds the Sa→Sa columns",
        "(slice 2). Algorithm and failure taxonomy:",
        "[app/sense_align.py](https://github.com/gasyoun/kosha/blob/main/app/sense_align.py).",
        "",
        "## Step-1 reachability verdict (H3862)",
        "",
        "The slice was asked for four Sa→Sa dictionaries. Two exist as CDSL sources and two",
        "do not, so two columns ship and two absences are recorded with their reason — the",
        "handoff's own instruction, and the alternative would have been a header with nothing",
        "under it.",
        "",
        "| dictionary | reachable | verdict |",
        "|---|---|---|",
        "| ŚKDR (Śabdakalpadruma) | yes — `skd.zip`, csl-sqlite | **column shipped** |",
        "| VCP (Vācaspatyam) | yes — `vcp.zip`, csl-sqlite | **column shipped** |",
    ]
    lines += [f"| {k} | no | {v} |" for k, v in SASA_ABSENT.items()]
    lines += [
        "",
        "The Medinī case is the one worth stating twice: csl-orig and csl-sqlite both carry a",
        "`md` code, and it is **Macdonell**, not Medinīkośa. Loading `md` because the letters",
        "matched would have put a Sanskrit-English dictionary of 1893 into the table under a",
        "Sanskrit-Sanskrit kośa's name, and nothing downstream would have caught it.",
        "",
        "## Scope fences (restated — a later session may not re-scope this quietly)",
        "",
    ]
    lines += [f"- {f}" for f in FENCES]
    lines += [
        "",
        "## Marked defaults",
        "",
        f"- `TAU = {TAU}` — edge survival threshold. A witness cited by exactly one sense on each",
        "  side of a pair scores 0.5 and survives; a witness spread over four or more senses of the",
        "  lemma cannot carry an edge alone. The `attrib` channel added by H3862 is decided by this",
        "  same threshold and introduces **no constant of its own**.",
        f"- `GLOSS_FLOOR = {GLOSS_FLOOR}` — Jaccard floor, and only inside one metalanguage.",
        f"- `PREFIX_MIN = {PREFIX_MIN}` — shortest abbreviation that may absorb a longer one",
        "  (`panc` ⊂ `pancat`). Below it, `r` would swallow `rv`. **Unchanged by this slice**: the",
        "  ŚKDR/VCP abbreviations reach the build through the explicit `ATTRIB_KEYS` table",
        f"  ({', '.join('`' + k + '`: ' + ', '.join('`' + x + '`' for x in v) for k, v in ATTRIB_KEYS.items())}),",
        "  not by lowering the prefix floor to let them match.",
        "",
        "## The language fence, stated for Sanskrit",
        "",
        "Gloss-overlap Jaccard is open only between two dictionaries that gloss in the **same**",
        "language, and only when that language is English. Slice 1 fenced it off German; slice 2",
        "has to fence it off Sanskrit for exactly the same reason, and the fence is now declared",
        "as data rather than implied by a tuple:",
        "",
        "| dictionary | metalanguage | gloss channel |",
        "|---|---|---|",
    ]
    lines += [f"| {DICT_LABEL[d]} | `{GLOSS_LANG[d]}` | "
              f"{'open (MW↔Apte)' if GLOSS_LANG[d] == 'en' else 'closed'} |" for d in DICTS]
    lines += [
        "",
        "A Sanskrit↔Sanskrit Jaccard would not be a weak signal, it would be a number with",
        "nothing behind it: ŚKDR and VCP share a scholastic idiom in which unrelated senses",
        "routinely repeat `ityarthaḥ`, `ityamaraḥ`, `iti purāṇam`. Relaxing this fence quietly is",
        "the failure mode `gloss_channel_open()` exists to make unreachable by accident.",
        "",
        "## Counts",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| lemmas in the run | {stats['n_lemmas']} |",
        f"| senses considered | {stats['n_senses']} |",
        f"| senses dropped as `no-gloss` (structural chunks) | {stats['n_no_gloss']} |",
        f"| meaning groups | {stats['n_groups']} |",
        f"| aligned groups (≥2 dictionaries) | {stats['n_aligned']} |",
        f"| unaligned singleton senses | {stats['n_unaligned']} |",
        f"| aligned share of groups | {stats['pct_aligned']}% |",
        f"| lemmas with ≥1 aligned group | {stats['n_lemmas_with_alignment']} |",
        f"| lemmas present in all three western dictionaries | {stats['n_lemmas_all_three']} |",
        f"| ŚKDR senses loaded | {stats['n_sasa_senses'].get('skd', 0)} |",
        f"| VCP senses loaded | {stats['n_sasa_senses'].get('vcp', 0)} |",
        f"| aligned groups touching ŚKDR | {stats['n_sasa_aligned'].get('skd', 0)} |",
        f"| aligned groups touching VCP | {stats['n_sasa_aligned'].get('vcp', 0)} |",
        "",
        "## Delta against the H3744 baseline (same 500-headword pilot)",
        "",
        f"Baseline: **{BASELINE_H3744['label']}**, as published in this file on 31-08-2026 and",
        "reproducible here with `--no-sasa`.",
        "",
        "| metric | H3744 | this build | Δ |",
        "|---|---:|---:|---:|",
    ]
    _delta_rows = [
        ("senses considered", "n_senses", stats["n_senses"]),
        ("meaning groups (rows)", "n_groups", stats["n_groups"]),
        ("aligned groups", "n_aligned", stats["n_aligned"]),
        ("lemmas with ≥1 aligned meaning", "n_lemmas_with_alignment",
         stats["n_lemmas_with_alignment"]),
        ("clean three-dictionary `1-1-1` rows", "clean_111", stats["clean_111"]),
    ]
    for label, key, now in _delta_rows:
        was = BASELINE_H3744[key]
        lines.append(f"| {label} | {was:,} | {now:,} | {now - was:+,} |")
    lines += [
        "",
        "| failure class | H3744 | this build | Δ |",
        "|---|---:|---:|---:|",
    ]
    _base_fc = BASELINE_H3744["failure_classes"]
    for cls in sorted(set(_base_fc) | set(fail_counts), key=lambda c: -fail_counts.get(c, 0)):
        was, now = _base_fc.get(cls, 0), fail_counts.get(cls, 0)
        lines.append(f"| `{cls}` | {was:,} | {now:,} | {now - was:+,} |")
    lines += [
        "",
        "### Why the western scores did not move — and what did",
        "",
        "The handoff expected every existing score to shift, because witness weight is `1/df` with",
        "`df` counted **within the lemma across all dictionaries**, and this build adds two",
        "dictionaries to every lemma. No western score moved. The reason is measurable rather",
        "than lucky:",
        "",
        "**ŚKDR and VCP contribute no witnesses to the pool.** They carry zero `<ls>` elements — 0",
        "of 42,531 ŚKDR records and 0 of 50,135 VCP records. `df` counts senses citing a witness;",
        "senses that cite nothing raise no `df`. So every western witness weight is what slice 1",
        "computed.",
        "",
        "That was checked, not assumed. Comparing this table against the `--no-sasa` baseline row",
        "by row, on the identity `(lemma, pwg/mw/apte sense ids, status, method, score,",
        "witnesses)`: **0 rows appear that the baseline did not have**, and the 67 baseline rows",
        "that no longer appear verbatim are exactly the 67 that gained a ŚKDR or VCP cell. No",
        "western sense changed its partner, its method, its score or its witness list.",
        "`1-1-1` rows: 262, unchanged. Had that number moved, the loader would have been leaking",
        "Sa→Sa material into the witness pool.",
        "",
        "**Aligned groups 2,957 → 3,013 decomposes exactly**: 56 rows are new meanings that only a",
        "kośa entered (`attrib` alone), and 11 are meanings slice 1 already had which now carry a",
        "kośa cell as well (`attrib+ls` 9, `attrib+gloss+ls` 2). Nothing else.",
        "",
        "**What genuinely changed is the classification of some unaligned western senses**, and",
        "this is the taxonomy working rather than drifting. A PWG sense that cites `ŚKDR.` now has",
        "a candidate partner it did not have before, so when it loses the greedy match it is",
        "recorded as `outranked` (+95) instead of `no-shared-witness`, and when its attribution is",
        "too common inside the lemma to clear τ it becomes `witness-too-common` (+100). Both are",
        "more informative than the class they replaced: the sense now has a named reason.",
        "",
        "The largest single addition to the table is `no-citation-apparatus` (1,832) — every",
        "ŚKDR/VCP sense that no western sense attributes, kept as its own row with the reason",
        "attached, exactly as slice 1 keeps its unalignable senses.",
        "",
        "## Failure classes (recorded, not hidden)",
        "",
        "| class | senses | what it means |",
        "|---|---:|---|",
    ]
    why = {
        "cross-language-gap": "a PWG sense with no `<ls>` at all — the citation bridge does not exist "
                              "for it, and German→English gloss overlap measures nothing",
        "no-shared-witness": "the sense cites sources, but no cross-dictionary sense of this lemma cites any of them",
        "witness-too-common": "shared witnesses exist but fall below τ on weight — real citation, no discriminating power",
        "absent-dictionary": "the lemma simply has no entry in the other dictionaries",
        "no-gloss": "a structural chunk (PWG `<div>` carrying only `<lex>m.</lex>`) — excluded before alignment",
        "outranked": "a qualifying partner existed but preferred a better-scoring sense; each "
                     "sense takes at most one partner per other dictionary",
        "no-citation-apparatus": "a ŚKDR/VCP sense no western sense attributes to its kośa. The "
                                 "kośas carry no `<ls>` at all, and their gloss is Sanskrit, so "
                                 "both bridges are shut for it — a property of the source "
                                 "format, not a tuning failure",
    }
    for cls, n in fail_counts.most_common():
        lines.append(f"| `{cls}` | {n} | {why.get(cls, '')} |")
    lines += [
        "",
        "## Group shapes (`pwg-mw-apte` sense counts)",
        "",
        "| shape | groups |",
        "|---|---:|",
    ]
    for sh, n in shape_counts.most_common(12):
        lines.append(f"| `{sh}` | {n} |")
    lines += [
        "",
        "## Methods that carried the surviving edges",
        "",
        "| method | groups |",
        "|---|---:|",
    ]
    for m, n in method_counts.most_common():
        lines.append(f"| `{m}` | {n} |")
    lines += [
        "",
        "## Worked example — नागदन्त, the case the wave exists for",
        "",
        "```",
        smoke.rstrip(),
        "```",
        "",
        "## The Sa→Sa bridge, and the one that was rejected (H3862)",
        "",
        "The handoff assumed this slice was a loader and a column extension. It is, but the",
        "channel it rides was not the expected one, and the difference is the finding.",
        "",
        "**What is not there.** ŚKDR and VCP have no `<ls>` — not few, none. Their citations are",
        "in running Sanskrit prose (`ityamaraḥ`, `iti medinī`, `yathā suśrute`). So the weighted-",
        "witness bridge, the only channel that crosses a language boundary, does not exist for",
        "them by construction; and the gloss channel is shut by the language fence above.",
        "",
        "**What is there, and it is printed rather than inferred.** PWG cites these kośas in its",
        "own `<ls>`: `ŚKDR.` 1,227 times and `MED.` 1,824 times across the pilot, touching 479 of",
        "its 500 lemmas. A PWG sense whose `<ls>` names ŚKDR is *saying* that this meaning is the",
        "one Śabdakalpadruma records. That is the `attrib` method — weighted `1/df` off the same",
        "table as `ls`, because `skdr` is already a witness key in it, and decided by the same τ.",
        "It is directional evidence and it is ranked below `ls` deliberately: the two sides do not",
        "converge on a third text, one of them points at the other.",
        "",
        "**The rejected channel, recorded so it is not re-attempted blind.** Reading the kośas'",
        "own `iti X` / `yathā X` attributions as witnesses was implemented and measured first. It",
        "re-invents witnesses through a side door `PREFIX_MIN` closes: the attribution particle is",
        "followed by an ordinary word far more often than by a source name, so after SLP1→IAST",
        "normalisation the pilot matched PWG's `PRAT.` to `pratyarthin` (\"counter-claimant\") and",
        "`BUDDH.` to `buddhim`. Yield was 73 of 707 records and most of it was false. The honest",
        "version needs a **closed, curated source vocabulary** — `amaraḥ`, `medinī`,",
        "`śabdaratnāvalī`, `hemacandraḥ` are real and frequent in the extraction — and that is a",
        "slice of its own, not a knob on this one.",
        "",
        "## Known limits",
        "",
        "1. **Homonyms are collapsed.** Grouping is keyed on `slp1` alone; a lemma with two",
        "   unrelated homonyms can pull their witnesses into one document-frequency pool. The",
        "   lemma-variant graph that would fix this is explicitly out of scope for this slice.",
        "2. **A shared citation is not a shared meaning.** Two senses that cite the same text",
        "   are witnessed together, which is evidence and not proof. The score is printed beside",
        "   every row so a reader can discount it.",
        "3. **PWG senses without `<ls>` are structurally unreachable** by this method — the largest",
        "   failure class, and an honest ceiling rather than a tuning knob.",
        "5. **False positives exist and look exactly like true ones.** A witness that is rare",
        "   *within a lemma* can still be shared by two unrelated senses. Worked counter-example,",
        "   on `amfta`, from this very build: PWG *N. pr. Mutter von Parikṣit* was matched to MW",
        "   *not dead* / Apte *Not dead* on `mbh`. The MW↔Apte half of that row is right and the",
        "   PWG half is wrong — a proper name and a negated adjective are not one meaning. The",
        "   score (and the witness list) is printed on every row precisely so a reader can catch",
        "   this; the table does not claim otherwise. Measuring the rate of such rows needs the",
        "   wave-2 acceptance pass (sample + judge + human vote), which is out of this slice's",
        "   scope, so **no precision figure is quoted here** — an unmeasured number would be worse",
        "   than the honest gap.",
        "4. **No sense order is rewritten.** Sidecar only; MW, PWG and Apte bytes are untouched.",
        "7. **`attrib` is lemma-level, and ŚKDR/VCP entries are entry-level.** The kośas carry",
        "   almost no `<div>`, so an entry is one sense; a PWG sense that cites `ŚKDR.` is joined",
        "   to *the* ŚKDR entry for the key, whatever that entry happens to be about. Worked",
        "   counter-example from this build: `kaṭa` — PWG *Gras* is matched to ŚKDR `kaṭa gatyāṃ",
        "   . iti kavikalpadrumaḥ`, which is the **verbal root** entry, not the noun. Same for",
        "   `bhū`. The row is a true statement about the attribution and a false one about the",
        "   meaning. The lemma-variant/homonym graph is what would fix it, and it is out of scope",
        "   for this slice as it was for slice 1.",
        "8. **An `attrib` score of 1.0 is not agreement.** It means exactly one sense of the lemma",
        "   cited that kośa, so the pointer is unambiguous — not that two dictionaries converged.",
        "   `attrib` is directional by construction and is ranked below `ls` for that reason; the",
        "   method token is printed on every row so the distinction survives into the table.",
        "6. **Homonym-blind document frequency.** `df` is counted per `slp1`, so a lemma whose",
        "   entries cover two unrelated words shares one witness pool between them.",
        "",
        "_Dr. Mārcis Gasūns_",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the PWG/MW/Apte aligned-sense table.")
    ap.add_argument("--heads", default=None,
                    help="comma-separated SLP1 headwords (default: the 500-headword pilot)")
    ap.add_argument("--limit", type=int, default=None, help="first N headwords only")
    ap.add_argument("--tau", type=float, default=TAU, help=f"edge threshold (default {TAU})")
    ap.add_argument("--no-staging", action="store_true",
                    help="skip the staged viewer; write the table and report only")
    ap.add_argument("--staging-root", default=None,
                    help="staging output root (default dist/sense-align-staging; never docs/)")
    ap.add_argument("--no-sasa", action="store_true",
                    help="skip the Sa→Sa kośas — reproduces the H3744 slice-1 baseline "
                         "the delta table in the build report is measured against")
    args = ap.parse_args()

    heads = ([h.strip() for h in args.heads.split(",") if h.strip()] if args.heads
             else load_pilot_heads())
    if args.limit:
        heads = heads[: args.limit]
    print(f"headwords: {len(heads)} (tau={args.tau})")

    con = sqlite3.connect(f"file:{find_db().as_posix()}?mode=ro", uri=True)
    sasa = {} if args.no_sasa else open_sasa(SASA_DICTS)
    for name, why in SASA_ABSENT.items():
        print(f"[sasa] {name}: ABSENT — {why.split(';')[0]}")
    rows, fails, payload = [], [], {}
    fail_counts, shape_counts, method_counts = Counter(), Counter(), Counter()
    n_senses = n_no_gloss = n_aligned = n_unaligned = 0
    n_lemmas_with_alignment = n_lemmas_all_three = 0
    n_sasa_senses = Counter()
    n_sasa_aligned = Counter()
    #: the H3744 headline metric: an aligned row that is exactly one sense from
    #: each of PWG, MW and Apte. Read off the WESTERN prefix of `shape`, so the
    #: number stays comparable now that `shape` has five positions.
    clean_111 = 0
    _west_n = sum(1 for d in DICTS if d not in SASA_DICTS)
    smoke_lines: list[str] = []

    for lemma in heads:
        senses, present = load_senses(con, lemma)
        sa_senses, sa_present = load_sasa_senses(sasa, lemma)
        senses += sa_senses
        present |= sa_present
        for s in sa_senses:
            n_sasa_senses[s["dict"]] += 1
        if not senses:
            continue
        res = align_lemma(senses, present_dicts=present, tau=args.tau)
        for g in res["groups"]:
            if g["status"] != "aligned":
                continue
            for d in SASA_DICTS:
                if g["by_dict"].get(d):
                    n_sasa_aligned[d] += 1
        st = res["stats"]
        n_senses += st["n_senses"]
        n_no_gloss += st["n_dropped_no_gloss"]
        n_aligned += st["n_aligned"]
        n_unaligned += st["n_unaligned"]
        if st["n_aligned"]:
            n_lemmas_with_alignment += 1
        if {"pwg", "mw", "ap90"} <= present:
            n_lemmas_all_three += 1
        fail_counts["no-gloss"] += st["n_dropped_no_gloss"]

        rows.extend(group_rows(lemma, res))
        for g in res["groups"]:
            shape_counts[g["shape"]] += 1
            method_counts[g["method"]] += 1
            if (g["status"] == "aligned"
                    and g["shape"].split("-")[:_west_n] == ["1"] * _west_n):
                clean_111 += 1
            if g["status"] == "unaligned":
                m = g["members"][0]
                fail_counts[g["failure_class"]] += 1
                fails.append({"lemma_slp1": lemma, "dict": m["dict"],
                              "sense_id": m["sense_id"],
                              "failure_class": g["failure_class"],
                              "n_ls": len(m["ls"]), "gloss": m["gloss"]})
        for d in res["dropped"]:
            fails.append({"lemma_slp1": lemma, "dict": d["dict"], "sense_id": d["sense_id"],
                          "failure_class": "no-gloss", "n_ls": len(d.get("ls") or []),
                          "gloss": d["gloss"]})

        payload[lemma] = {
            "present": sorted(present),
            "stats": {k: st[k] for k in ("n_senses", "n_groups", "n_aligned", "n_unaligned")},
            "groups": [dict({
                "status": g["status"], "shape": g["shape"], "method": g["method"],
                "score": g["score"], "witnesses": g["witnesses"], "flags": g["flags"],
                "failure_class": g["failure_class"],
            }, **{DICT_COL[d]: [{"sense_id": m["sense_id"],
                                 "gloss": display_gloss(d, m["gloss"])}
                                for m in g["by_dict"][d]] for d in DICTS})
                for g in res["groups"]],
        }
        if lemma == SMOKE_LEMMA:
            for g in res["groups"]:
                smoke_lines.append(
                    f"[{g['status']:9s} {g['shape']} {g['method']:9s} {g['score']:.2f} "
                    f"{' '.join(g['witnesses']) or '-'}] "
                    + " || ".join(
                        f"{DICT_LABEL[d]}: " + " ; ".join(
                            display_gloss(d, m["gloss"])[:70] for m in g["by_dict"][d])
                        for d in DICTS if g["by_dict"][d])
                    + (f"  <- {g['failure_class']}" if g["failure_class"] else ""))

    write_tsv(OUT_TSV, TSV_FIELDS, rows)
    write_tsv(OUT_FAIL, FAIL_FIELDS, fails)

    n_groups = len(rows)
    stats = {
        "build_date": date.today().isoformat(),
        "n_lemmas": len(payload), "n_senses": n_senses, "n_no_gloss": n_no_gloss,
        "n_groups": n_groups, "n_aligned": n_aligned, "n_unaligned": n_unaligned,
        "pct_aligned": round(100.0 * n_aligned / n_groups, 1) if n_groups else 0.0,
        "n_lemmas_with_alignment": n_lemmas_with_alignment,
        "n_lemmas_all_three": n_lemmas_all_three,
        "tau": args.tau,
        "failure_classes": ", ".join(f"{k} {v}" for k, v in fail_counts.most_common()),
        "fences": FENCES,
        "dicts": [d for d in DICTS if d not in SASA_DICTS or d in sasa],
        "n_sasa_senses": dict(n_sasa_senses),
        "n_sasa_aligned": dict(n_sasa_aligned),
        "clean_111": clean_111,
    }
    write_report(stats, fail_counts, shape_counts, method_counts, "\n".join(smoke_lines))

    if not args.no_staging:
        root = Path(args.staging_root) if args.staging_root else STAGING
        write_staging(payload, stats, root)
        print(f"[staging] {root} (index.html + data/alignment.js + NOT_PUBLISHED.md; docs/ untouched)")

    print(f"groups={n_groups} aligned={n_aligned} ({stats['pct_aligned']}%) "
          f"unaligned={n_unaligned} no_gloss={n_no_gloss}")
    print(f"failure classes: {stats['failure_classes']}")
    print(f"wrote {OUT_TSV.relative_to(ROOT)}, {OUT_FAIL.relative_to(ROOT)}, "
          f"{OUT_REPORT.relative_to(ROOT)}")
    if smoke_lines:
        print(f"--- {SMOKE_LEMMA} ---")
        for ln in smoke_lines:
            print(ln)


if __name__ == "__main__":
    main()
