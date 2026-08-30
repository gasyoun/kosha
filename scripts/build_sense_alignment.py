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

Outputs
  data/concordance/sense_alignment.tsv           one row per MEANING GROUP (committed)
  data/concordance/sense_alignment_failures.tsv  one row per unalignable sense (committed)
  data/concordance/SENSE_ALIGNMENT_BUILD_REPORT.md
  dist/sense-align-staging/                      the staged viewer (gitignored, never docs/)

Scope fences (H3744; restated in every artifact this writes):
  IN  — PWG, MW, Apte (ap90) only.
  OUT — the Sa→Sa dictionaries (ŚKDR / Medinī / VCP / Amara): a second slice.
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

from sense_align import (  # noqa: E402
    DICTS, GLOSS_FLOOR, PREFIX_MIN, TAU, align_lemma, extract_ls, sense_gloss,
)

PILOT = ROOT / "data" / "concordance" / "sense_pilot_headwords.tsv"
DB_CANDIDATES = [
    ROOT / "data" / "db" / "kosha.db",
    ROOT.parent / "kosha" / "data" / "db" / "kosha.db",
]
OUT_TSV = ROOT / "data" / "concordance" / "sense_alignment.tsv"
OUT_FAIL = ROOT / "data" / "concordance" / "sense_alignment_failures.tsv"
OUT_REPORT = ROOT / "data" / "concordance" / "SENSE_ALIGNMENT_BUILD_REPORT.md"
STAGING = ROOT / "dist" / "sense-align-staging"

DICT_LABEL = {"pwg": "PWG", "mw": "MW", "ap90": "Apte"}
SMOKE_LEMMA = "nAgadanta"

FENCES = [
    "IN: PWG, MW, Apte (ap90) only.",
    "OUT: Sa→Sa dictionaries (ŚKDR / Medinī / VCP / Amara) — a deliberate second slice.",
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


TSV_FIELDS = [
    "lemma_slp1", "group_id", "status", "shape", "method", "score",
    "witnesses", "flags", "failure_class",
    "pwg_sense_ids", "pwg_gloss", "mw_sense_ids", "mw_gloss",
    "apte_sense_ids", "apte_gloss", "note",
]
FAIL_FIELDS = ["lemma_slp1", "dict", "sense_id", "failure_class", "n_ls", "gloss"]


def group_rows(lemma: str, res: dict):
    out = []
    for gi, g in enumerate(res["groups"], 1):
        cell = {}
        for d in DICTS:
            ms = g["by_dict"].get(d) or []
            cell[d] = ("; ".join(m["sense_id"] for m in ms),
                       " ‖ ".join(m["gloss"] for m in ms))
        out.append({
            "lemma_slp1": lemma,
            "group_id": f"{lemma}#{gi}",
            "status": g["status"],
            "shape": g["shape"],
            "method": g["method"],
            "score": f"{g['score']:.3f}",
            "witnesses": " ".join(g["witnesses"]),
            "flags": " ".join(g["flags"]),
            "failure_class": g["failure_class"],
            "pwg_sense_ids": cell["pwg"][0], "pwg_gloss": cell["pwg"][1],
            "mw_sense_ids": cell["mw"][0], "mw_gloss": cell["mw"][1],
            "apte_sense_ids": cell["ap90"][0], "apte_gloss": cell["ap90"][1],
            "note": ("shared literary witness, weighted 1/df within the lemma"
                     if g["status"] == "aligned"
                     else "no cross-dictionary evidence — see failure_class"),
        })
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
<title>kosha — aligned senses (PWG · MW · Apte) — STAGED, NOT PUBLISHED</title>
<style>
:root{--ink:#1f2328;--mut:#656d76;--line:#d8dee4;--bg:#f6f8fa;--card:#fff;
      --pwg:#0a7a2f;--mw:#1a6fb0;--apte:#a05a00;--ok:#0a7a2f;--warn:#8a6d00}
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
  <h1>Aligned senses · PWG · MW · Apte <span style="opacity:.6">— sense-reconciliation W2, slice 1</span></h1>
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
  var rows=e.groups.map(function(g){
    return '<tr class="'+esc(g.status)+'">'+
      '<td class="ev">'+evidence(g)+'<div class="w">'+esc(g.shape)+'</div></td>'+
      '<td>'+cell(g.pwg)+'</td><td>'+cell(g.mw)+'</td><td>'+cell(g.apte)+'</td></tr>';
  }).join('');
  out.innerHTML='<h2 style="font-family:Consolas,monospace;font-size:22px;margin:16px 0 0">'+esc(key)+
    '</h2><div style="font-size:12.5px;color:#656d76">dictionaries with an entry: '+
    esc(e.present.join(', ')||'none')+' · senses aligned '+esc(e.stats.n_aligned)+
    ' / groups '+esc(e.stats.n_groups)+'</div>'+
    '<table><thead><tr><th style="width:15%">evidence</th><th class="pwg" style="width:29%">PWG (de)</th>'+
    '<th class="mw" style="width:28%">MW (en)</th><th class="apte" style="width:28%">Apte (en)</th>'+
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
    (out_root / "data" / "alignment.js").write_text(
        "/* Auto-generated by scripts/build_sense_alignment.py — do not edit. */\n"
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
        "# Build report — aligned-sense table (PWG · MW · Apte)",
        "",
        f"_Created: {today} · Last updated: {today}_",
        "",
        "Generated by [scripts/build_sense_alignment.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_sense_alignment.py)",
        "(H3744, sense-reconciliation wave 2 slice 1). Algorithm and failure taxonomy:",
        "[app/sense_align.py](https://github.com/gasyoun/kosha/blob/main/app/sense_align.py).",
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
        "  lemma cannot carry an edge alone.",
        f"- `GLOSS_FLOOR = {GLOSS_FLOOR}` — Jaccard floor, MW↔Apte only.",
        f"- `PREFIX_MIN = {PREFIX_MIN}` — shortest abbreviation that may absorb a longer one",
        "  (`panc` ⊂ `pancat`). Below it, `r` would swallow `rv`.",
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
        f"| lemmas present in all three dictionaries | {stats['n_lemmas_all_three']} |",
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
    args = ap.parse_args()

    heads = ([h.strip() for h in args.heads.split(",") if h.strip()] if args.heads
             else load_pilot_heads())
    if args.limit:
        heads = heads[: args.limit]
    print(f"headwords: {len(heads)} (tau={args.tau})")

    con = sqlite3.connect(f"file:{find_db().as_posix()}?mode=ro", uri=True)
    rows, fails, payload = [], [], {}
    fail_counts, shape_counts, method_counts = Counter(), Counter(), Counter()
    n_senses = n_no_gloss = n_aligned = n_unaligned = 0
    n_lemmas_with_alignment = n_lemmas_all_three = 0
    smoke_lines: list[str] = []

    for lemma in heads:
        senses, present = load_senses(con, lemma)
        if not senses:
            continue
        res = align_lemma(senses, present_dicts=present, tau=args.tau)
        st = res["stats"]
        n_senses += st["n_senses"]
        n_no_gloss += st["n_dropped_no_gloss"]
        n_aligned += st["n_aligned"]
        n_unaligned += st["n_unaligned"]
        if st["n_aligned"]:
            n_lemmas_with_alignment += 1
        if len(present) == 3:
            n_lemmas_all_three += 1
        fail_counts["no-gloss"] += st["n_dropped_no_gloss"]

        rows.extend(group_rows(lemma, res))
        for g in res["groups"]:
            shape_counts[g["shape"]] += 1
            method_counts[g["method"]] += 1
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
            "groups": [{
                "status": g["status"], "shape": g["shape"], "method": g["method"],
                "score": g["score"], "witnesses": g["witnesses"], "flags": g["flags"],
                "failure_class": g["failure_class"],
                "pwg": [{"sense_id": m["sense_id"], "gloss": m["gloss"]} for m in g["by_dict"]["pwg"]],
                "mw": [{"sense_id": m["sense_id"], "gloss": m["gloss"]} for m in g["by_dict"]["mw"]],
                "apte": [{"sense_id": m["sense_id"], "gloss": m["gloss"]} for m in g["by_dict"]["ap90"]],
            } for g in res["groups"]],
        }
        if lemma == SMOKE_LEMMA:
            for g in res["groups"]:
                smoke_lines.append(
                    f"[{g['status']:9s} {g['shape']} {g['method']:9s} {g['score']:.2f} "
                    f"{' '.join(g['witnesses']) or '-'}] "
                    + " || ".join(
                        f"{DICT_LABEL[d]}: " + " ; ".join(m["gloss"][:70] for m in g["by_dict"][d])
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
