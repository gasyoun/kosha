#!/usr/bin/env python
"""Build /concordance/morphology/ — the A3 paradigm-cell attestation viewer (H3861).

CONCORDANCE_ROADMAP Q3's web deliverable, and the last one with no artefact behind it.
Spec: *paradigm cell → attested? with corpus evidence.*

What it joins
-------------
The expensive work is already done and released; this consumes it rather than re-deriving:

  data/concordance/morph_attest_infl_AG.tsv    generated form -> attested (locus, occ, tier)
  data/concordance/morph_attest_infl_AnG.tsv   attested keys the generator never produced
  kosha.db `inflections`                       the actual gender/case/number cells
  data/frequency/lemma_frequency.tsv           DCS token counts, for the static head
  dcs_full.sqlite `sentence`                   KWIC text for attested cells (optional)

A generated form absent from the AG index is, by the audit's own reconciliation, in the
G¬A bucket — so "unattested" is read off the same two files the dataset ships, and the page
cannot drift from the dataset without the dataset changing.

Static head (standing rule D4/D5)
---------------------------------
The head is chosen by **measured** DCS token coverage, never a hardcoded N: `--coverage
0.95` walks `lemma_frequency.tsv` in frequency order until that share of corpus token mass
is covered, and the resulting N is reported and written into the page's trust block. As of
02-09-2026 that is N=11,148 lemmas, of which 9,150 carry `inflections` rows — but the
number is re-measured every run, per the H1590 discipline.

Honesty carried into the UI, not just the report
------------------------------------------------
The audit's two controls decide how a red cell may be read, so they are rendered, not
buried in a footnote:

  * **Verbs.** `inflections` holds 680 verbal lemmas against 222,736 nominal. A lemma with
    no verbal cells is out of scope, not broken — verbal-tagged gaps are labelled as such.
  * **Sandhi.** Half the A¬G set is attested only as a *sandhied* surface. Every gap row
    carries its `attested_via`, and surface-only rows are visually demoted.

A red cell on this page therefore means "this generated form is unattested in DCS", which
is a statement about the corpus, not a defect claim about the generator. The page says so
where a reader will see it.

Deterministic, no network, read-only on every input.
"""
import argparse
import collections
import csv
import gzip
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _github_root(root):
    """Locate the org checkout root (worktree-safe; see build_morphology_attestation_audit_inflections.py)."""
    env = os.environ.get("GITHUB_ROOT")
    if env:
        return Path(env)
    for cand in (root.parent, root.parent / "GitHub", root.parent.parent,
                 root.parent.parent / "GitHub"):
        if (cand / "sanskrit-util").is_dir() and (cand / "VisualDCS").is_dir():
            return cand
    sys.exit("cannot locate the GitHub org root; set GITHUB_ROOT")


GH = _github_root(ROOT)
sys.path.insert(0, str(GH / "sanskrit-util" / "py"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sanskrit_util import form_key, from_slp1  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

KOSHA_DB = GH / "kosha" / "data" / "db" / "kosha.db"
DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"
CONC = ROOT / "data" / "concordance"
AG_TSV = CONC / "morph_attest_infl_AG.tsv"
ANG_TSV = CONC / "morph_attest_infl_AnG.tsv"
FREQ_TSV = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
OUT_WEB = ROOT / "concordance" / "morphology"
OUT_DATA = OUT_WEB / "data"

CASES = ["nom", "acc", "instr", "dat", "abl", "gen", "loc", "voc"]
NUMBERS = ["sg", "du", "pl"]
GENDERS = ["m", "n", "f", ""]
SENT_TRUNC = 150
MAX_KWIC_PER_LEMMA = 6      # stated cap; the page is a preview, the TSV is the data
SHARD_MAX_BYTES = 400_000   # one lookup pulls at most this much cell data


def human(n):
    return "{:,}".format(n)


def pct(a, b):
    return "0.00%" if not b else "%.2f%%" % (100.0 * a / b)


def shard_key(slp1):
    ch = (slp1 or "?")[0].lower()
    return ch if ch.isalpha() else "_"


def measure_head(coverage):
    """Static head by MEASURED corpus token coverage (D4/D5) — never a hardcoded N."""
    rows = []
    with FREQ_TSV.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            try:
                c = int(r["count_all"])
            except (ValueError, KeyError, TypeError):
                continue
            if r.get("lemma_slp1"):
                rows.append((r["lemma_slp1"], c))
    rows.sort(key=lambda x: -x[1])
    total = sum(c for _, c in rows)
    run = 0
    head = []
    for lem, c in rows:
        head.append((lem, c))
        run += c
        if total and run / total >= coverage:
            break
    return head, total, run


def load_ag():
    """form_slp1 -> attestation record. Absence == the G¬A bucket (audit reconciliation)."""
    ag = {}
    with AG_TSV.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            ag[r["anchor_id"]] = (r["attested_form"], r["target_locus"],
                                  int(r["evidence_count"]), r["match_method"],
                                  r["attested_via"], r["tense_caveat"] == "1")
    return ag


def load_ang():
    """form_key(dcs_lemma) -> [gap rows]. The generator never produced these."""
    by_lemma = collections.defaultdict(list)
    with ANG_TSV.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            lem = r["dcs_lemma"]
            if not lem:
                continue
            k = form_key(lem)
            if k:
                by_lemma[k].append(r)
    return by_lemma


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coverage", type=float, default=0.95,
                    help="share of DCS token mass the static head must cover (D4/D5)")
    ap.add_argument("--no-kwic", action="store_true",
                    help="skip sentence text (smaller shards)")
    args = ap.parse_args()

    for p in (KOSHA_DB, AG_TSV, ANG_TSV, FREQ_TSV):
        if not p.exists():
            sys.exit("missing input: %s" % p)

    t0 = time.time()
    OUT_DATA.mkdir(parents=True, exist_ok=True)

    head, tok_total, tok_head = measure_head(args.coverage)
    head_keys = {lem for lem, _ in head}
    freq = dict(head)
    print("head: N=%s lemmas covering %s of %s tokens (%.2f%%) [%.0fs]"
          % (human(len(head)), human(tok_head), human(tok_total),
             100.0 * tok_head / tok_total, time.time() - t0), file=sys.stderr)

    ag = load_ag()
    print("AG index: %s generated forms attested [%.0fs]" % (human(len(ag)), time.time() - t0),
          file=sys.stderr)
    ang = load_ang()
    print("A¬G index: %s lemma keys carry a gap [%.0fs]" % (human(len(ang)), time.time() - t0),
          file=sys.stderr)

    # ---- cells for the head lemmas -------------------------------------------------
    con = sqlite3.connect("file:%s?mode=ro" % KOSHA_DB.as_posix(), uri=True)
    cells = collections.defaultdict(list)
    n_rows = 0
    for form_slp1, lemma, model, gender, gcase, number, person, tense, voice, src in con.execute(
            "SELECT form_slp1, lemma_slp1, model, gender, gcase, number, person, tense, "
            "voice, source FROM inflections"):
        if lemma not in head_keys:
            continue
        n_rows += 1
        cells[lemma].append((form_slp1, model, gender, gcase, number, person, tense,
                             voice, src))
    con.close()
    print("cells: %s inflection rows across %s head lemmas [%.0fs]"
          % (human(n_rows), human(len(cells)), time.time() - t0), file=sys.stderr)

    # ---- KWIC sentences for the attested cells we will actually render -------------
    sents = {}
    if not args.no_kwic and DCS.exists():
        wanted = set()
        for lemma in cells:
            got = 0
            for c in cells[lemma]:
                rec = ag.get(c[0])
                if rec and got < MAX_KWIC_PER_LEMMA:
                    wanted.add(rec[1].split(":", 1)[1])
                    got += 1
        d = sqlite3.connect("file:%s?mode=ro" % DCS.as_posix(), uri=True)
        for sid, text in d.execute("SELECT sent_id, text_sandhied FROM sentence"):
            if sid in wanted and text:
                t = text.strip()
                sents[sid] = (t[:SENT_TRUNC] + "…") if len(t) > SENT_TRUNC else t
        d.close()
        print("kwic: %s sentences resolved of %s wanted [%.0fs]"
              % (human(len(sents)), human(len(wanted)), time.time() - t0), file=sys.stderr)

    # ---- build the per-lemma payload ----------------------------------------------
    shards = collections.defaultdict(dict)
    tot_cells = tot_attested = tot_gap = 0
    lemmas_all_attested = lemmas_none_attested = 0
    verbal_lemmas = 0

    for lemma, rows in cells.items():
        lk = form_key(from_slp1(lemma))
        nominal, verbal = [], []
        kwic_budget = MAX_KWIC_PER_LEMMA
        n_att = 0
        models = set()
        for form_slp1, model, gender, gcase, number, person, tense, voice, src in rows:
            rec = ag.get(form_slp1)
            # Ship only what the page renders. `model` is hoisted to a per-lemma list
            # (it is near-constant per gender block, so a per-cell copy was ~4 MB of
            # duplicate strings); `match_method` collapses to a flag set only for the
            # weaker `floor` tier, since `exact` is the default; the attested surface is
            # carried only where a KWIC sentence needs it for highlighting.
            if model:
                models.add(model)
            cell = {"f": form_slp1, "i": from_slp1(form_slp1)}
            if rec:
                n_att += 1
                surface, locus, occ, method, via, caveat = rec
                cell["a"] = 1
                cell["o"] = occ
                cell["l"] = locus
                if method == "floor":
                    cell["t"] = 1
                if caveat:
                    cell["c"] = 1
                sid = locus.split(":", 1)[1]
                if kwic_budget > 0 and sid in sents:
                    cell["k"] = sents[sid]
                    cell["s"] = surface
                    kwic_budget -= 1
            if person:
                cell.update({"p": person, "te": tense or "", "v": voice or "",
                             "n": number or ""})
                verbal.append(cell)
            else:
                cell.update({"g": gender or "", "cs": gcase or "", "n": number or ""})
                nominal.append(cell)

        gaps = []
        for g in ang.get(lk, []):
            gaps.append({"f": g["attested_form"], "u": g["dcs_upos"], "o": int(g["evidence_count"]),
                         "l": g["target_locus"], "vi": g["attested_via"],
                         "t": g["triage_class"]})
        gaps.sort(key=lambda x: -x["o"])
        gaps = gaps[:40]

        tot_cells += len(rows)
        tot_attested += n_att
        tot_gap += len(gaps)
        if n_att == len(rows):
            lemmas_all_attested += 1
        elif n_att == 0:
            lemmas_none_attested += 1
        if verbal:
            verbal_lemmas += 1

        shards[shard_key(lemma)][lemma] = {
            "iast": from_slp1(lemma),
            "freq": freq.get(lemma, 0),
            "nom": nominal,
            "vrb": verbal,
            "gap": gaps,
            "att": n_att,
            "tot": len(rows),
            "mdl": sorted(models),
        }

    # ---- write shards ---------------------------------------------------------------
    # First-letter shards, chunked when one would exceed SHARD_MAX_BYTES: a lookup pulls
    # one chunk, not a whole letter. Chunks are numbered over SORTED lemmas rather than
    # named after a second letter, because SLP1 is case-sensitive (`A` != `a`) while NTFS
    # filenames are not — a second-letter scheme would collide case twins on this box,
    # the H3597 defect class. The manifest carries each chunk's first key so the client
    # can pick by ordinary string comparison.
    for old in list(OUT_DATA.glob("kwic_*.js")) + list(OUT_DATA.glob("index_*.js")):
        old.unlink()
    total_bytes = 0
    manifest = {}
    for sk, data in sorted(shards.items()):
        keys = sorted(data)
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        n_chunks = max(1, -(-len(payload.encode("utf-8")) // SHARD_MAX_BYTES))
        n_chunks = min(n_chunks, len(keys))
        per = -(-len(keys) // n_chunks)
        chunks = []
        for ci in range(n_chunks):
            part_keys = keys[ci * per:(ci + 1) * per]
            if not part_keys:
                continue
            part = {k: data[k] for k in part_keys}
            name = "%s_%d" % (sk, ci)
            p = OUT_DATA / ("kwic_%s.js" % name)
            body = json.dumps(part, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            with p.open("w", encoding="utf-8", newline="\n") as f:
                f.write("window.MORPH_DATA = window.MORPH_DATA || {};\n")
                f.write('window.MORPH_ADD("%s", %s);\n' % (name, body))
            total_bytes += p.stat().st_size
            chunks.append([part_keys[0], name])
        manifest[sk] = chunks
        # Light per-letter index (key -> IAST + attested/total only) so incremental typing
        # and prefix listing never pull a heavy cell chunk; the chunk loads only once a
        # specific lemma is resolved. Same split the sibling /concordance/dict/ page uses.
        idx = {k: [data[k]["iast"], data[k]["att"], data[k]["tot"]] for k in keys}
        (OUT_DATA / ("index_%s.js" % sk)).write_text(
            "window.MORPH_INDEX = window.MORPH_INDEX || {};\n"
            'window.MORPH_INDEX["%s"] = %s;\n'
            % (sk, json.dumps(idx, ensure_ascii=False, separators=(",", ":"), sort_keys=True)),
            encoding="utf-8", newline="\n")
    largest = max((p.stat().st_size for p in OUT_DATA.glob("kwic_*.js")), default=0)
    n_files = len(list(OUT_DATA.glob("kwic_*.js")))
    print("shards: %d files across %d letters, %.1f MB total (largest %.0f KB) [%.0fs]"
          % (n_files, len(manifest), total_bytes / 1e6, largest / 1e3, time.time() - t0),
          file=sys.stderr)

    stats = {
        "head_n": len(head), "head_with_cells": len(cells),
        "coverage": 100.0 * tok_head / tok_total, "coverage_arg": args.coverage * 100,
        "tok_head": tok_head, "tok_total": tok_total,
        "cells": tot_cells, "attested": tot_attested,
        "gap": tot_gap, "shards": len(shards), "bytes": total_bytes,
        "all_attested": lemmas_all_attested, "none_attested": lemmas_none_attested,
        "verbal_lemmas": verbal_lemmas,
        "built": time.strftime("%d-%m-%Y"),
        "files": n_files, "largest": largest,
    }
    (OUT_DATA / "stats.js").write_text(
        "window.MORPH_STATS = %s;\nwindow.MORPH_SHARDS = %s;\n"
        % (json.dumps(stats, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
           json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True)),
        encoding="utf-8", newline="\n")

    write_page(stats)
    print("cells %s · attested %s (%s) · head %s lemmas · %.1f MB · %.0fs"
          % (human(tot_cells), human(tot_attested), pct(tot_attested, tot_cells),
             human(len(cells)), total_bytes / 1e6, time.time() - t0))


def write_page(s):
    """The viewer. Self-contained, no external deps, matching concordance/dict's shape."""
    html = PAGE.replace("__BUILT__", s["built"])
    html = html.replace("__HEADN__", human(s["head_n"]))
    html = html.replace("__HEADCELLS__", human(s["head_with_cells"]))
    html = html.replace("__COV__", "%.2f" % s["coverage"])
    html = html.replace("__CELLS__", human(s["cells"]))
    html = html.replace("__ATT__", human(s["attested"]))
    html = html.replace("__ATTPCT__", pct(s["attested"], s["cells"]))
    html = html.replace("__NONEATT__", human(s["none_attested"]))
    html = html.replace("__ALLATT__", human(s["all_attested"]))
    html = html.replace("__MAXKWIC__", str(MAX_KWIC_PER_LEMMA))
    (OUT_WEB / "index.html").write_text(html, encoding="utf-8", newline="\n")


PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>kosha — generated ↔ attested morphology concordance (A3)</title>
<style>
:root { --ink:#222; --mut:#667; --line:#ddd; --bg:#faf9f6; --card:#fff;
        --yes:#0a7a2f; --yesbg:#e8f5ec; --no:#8a8f98; --nobg:#f2f3f5;
        --gap:#a0410a; --gapbg:#fdf0e8; --warn:#8a6d00; }
* { box-sizing:border-box; }
body { margin:0; font:15px/1.5 Georgia,'Times New Roman',serif; color:var(--ink); background:var(--bg); }
header { background:#2b3a4a; color:#fff; padding:14px 20px; }
header h1 { margin:0; font-size:18px; font-weight:normal; }
header .sub { font-size:12.5px; opacity:.78; margin-top:3px; max-width:860px; }
main { max-width:940px; margin:0 auto; padding:16px 20px 60px; }
#q { width:100%; font-size:18px; padding:9px 12px; border:1px solid var(--line); border-radius:6px;
     font-family:inherit; }
#hint { font-size:12.5px; color:var(--mut); margin:6px 2px 14px; }
#matches { margin:8px 0; }
#matches a { display:inline-block; margin:2px 8px 2px 0; font-size:14.5px; }
.entry { background:var(--card); border:1px solid var(--line); border-radius:8px;
         padding:14px 18px; margin:14px 0; }
.hw { font-size:21px; }
.hw .slp { color:var(--mut); font-size:14px; margin-left:8px; font-family:Consolas,monospace; }
.hw .freq { font-size:12.5px; color:var(--mut); margin-left:10px; }
.bar { height:7px; background:var(--nobg); border-radius:4px; margin:9px 0 3px; overflow:hidden; }
.bar i { display:block; height:100%; background:var(--yes); }
.barlab { font-size:12.5px; color:var(--mut); }
h3 { font-size:13px; text-transform:uppercase; letter-spacing:.05em; color:var(--mut);
     margin:16px 0 6px; font-weight:normal; }
table.para { border-collapse:collapse; width:100%; margin:4px 0 2px; }
table.para th { font-size:11.5px; color:var(--mut); font-weight:normal; text-align:left;
                padding:3px 6px; border-bottom:1px solid var(--line); }
table.para td { border:1px solid #eceef0; padding:4px 6px; vertical-align:top; font-size:13.5px; }
td.c { cursor:default; }
td.yes { background:var(--yesbg); }
td.no  { background:var(--nobg); color:var(--no); }
td .frm { font-family:Consolas,monospace; font-size:12.5px; }
td .occ { font-size:11px; color:var(--yes); margin-left:5px; }
.cav { color:var(--warn); font-size:11px; margin-left:3px; }
.kw { font-size:13px; margin:6px 0 0 2px; color:#333; }
.kw .loc { font-family:Consolas,monospace; font-size:11px; color:#889; margin-left:5px; }
.gaps li { margin:3px 0; font-size:13.5px; }
.gaps .surf { opacity:.55; }
.gaps .u { font-size:11px; background:#eef0f3; border-radius:8px; padding:1px 6px; color:#445; margin-left:5px; }
.note { font-size:12.5px; color:var(--mut); margin:6px 0; }
.callout { border-left:3px solid var(--warn); background:#fffdf3; padding:8px 12px;
           font-size:12.5px; color:#544; margin:10px 0; }
#trust { border-top:2px solid var(--line); margin-top:34px; padding-top:12px;
         font-size:12.5px; color:var(--mut); }
#trust table { border-collapse:collapse; margin:6px 0; }
#trust td, #trust th { border:1px solid var(--line); padding:2px 9px; font-size:12px; }
.none { color:var(--mut); font-style:italic; }
a { color:#1a6fb0; }
.legend span { display:inline-block; font-size:11.5px; padding:1px 8px; border-radius:8px; margin-right:6px; }
</style>
</head>
<body>
<header>
  <h1>Generated ↔ attested morphology <span style="opacity:.6">· A3 · kosha concordance program</span></h1>
  <div class="sub">Every generated paradigm cell for a lemma, marked <b>attested</b> or
  <b>not attested</b> in the DCS corpus (5.69M tokens, 270 texts), with the corpus evidence
  behind each attestation — plus the forms DCS attests that the generator never produced.
  __CELLS__ cells over __HEADCELLS__ lemmas · __ATT__ attested (__ATTPCT__).</div>
</header>
<main>
  <input id="q" placeholder="Type a lemma — IAST (rāma, agni, gaja) or SLP1 (rAma, agni) …" autocomplete="off">
  <div id="hint">Static head: the __HEADN__ most frequent DCS lemmas, covering __COV__% of corpus
  token mass (measured at build time from <code>lemma_frequency.tsv</code>, standing rule D4/D5 —
  not a hardcoded N); __HEADCELLS__ of them carry rows in the generator. KWIC is capped at
  __MAXKWIC__ sentences per lemma — a preview, not the data; the full set is in the
  <a href="https://github.com/gasyoun/kosha/blob/main/data/concordance/morph_attest_infl_AG.tsv">dataset TSV</a>
  (per-cell <code>evidence_count</code>) and the canonical DCS SQLite.</div>
  <div class="legend">
    <span style="background:var(--yesbg);color:var(--yes)">attested — occurs in DCS</span>
    <span style="background:var(--nobg);color:var(--no)">not attested — generated, absent from DCS</span>
    <span style="background:var(--gapbg);color:var(--gap)">gap — DCS attests it, generator did not</span>
  </div>
  <div id="matches"></div>
  <div id="out"></div>

  <div id="trust">
    <b>Trust block.</b> Source datasets:
    <a href="https://github.com/gasyoun/kosha/blob/main/data/concordance/morph_attest_infl_AG.tsv">morph_attest_infl_AG.tsv</a>
    (239,443 attested generated forms) and
    <a href="https://github.com/gasyoun/kosha/blob/main/data/concordance/morph_attest_infl_AnG.tsv">morph_attest_infl_AnG.tsv</a>
    (196,378 gap keys), built 01-09-2026 by
    <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_morphology_attestation_audit_inflections.py">build_morphology_attestation_audit_inflections.py</a>
    (H3782); paradigm cells from <code>kosha.db</code> <code>inflections</code> (6,917,018 rows,
    <b>99.99% <code>source='cologne_mwinflect'</code></b>); attestation from
    <i>dcs-full-sqlite</i> (DCS 2026, CC BY 4.0). Page built __BUILT__ by
    <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_morphology_concordance_page.py">build_morphology_concordance_page.py</a>
    (H3861). A generated form absent from the AG index is in the G¬A bucket by the audit's own
    reconciliation, so "not attested" here is read off the shipped dataset, not recomputed.
    <p><b>What a red cell does and does not mean.</b> It means the form does not occur in the
    5.69M-token DCS corpus. It is <b>not</b> a claim that the form is wrong or that the
    generator is broken: most of Sanskrit's paradigm space is simply unattested in any finite
    corpus — __ATTPCT__ of the cells shown here are attested, and __NONEATT__ of the head
    lemmas have no attested cell at all. Read it as corpus coverage, not as a defect list.</p>
    <p><b>Two scope facts that bound every reading, carried from the audit.</b>
    (1) <b>Verbs.</b> The generator holds <b>680 verbal lemmas against 222,736 nominal</b>, so
    finite verbs are territory it never claimed; a verbal gap is out of scope, not a bug —
    gap rows carry their DCS <code>upos</code>. (2) <b>Sandhi.</b> A paradigm generator emits
    <i>unsandhied</i> forms while DCS records the sandhied surface, so gap rows attested only
    as a surface (<code>via: surface</code>) are shown dimmed — for those the mismatch is an
    artefact of the attested side. Of the full 196,378-key gap set, 51.06% are surface-only
    and the defensible give-back subset is
    <a href="https://github.com/gasyoun/kosha/blob/main/data/concordance/morph_giveback_candidates.tsv">5,656 rows</a>,
    method in the
    <a href="https://github.com/gasyoun/kosha/blob/main/data/concordance/MORPHOLOGY_GIVEBACK_CANDIDATES_REPORT.md">candidates report</a>.</p>
    <p><b>Homographic cells share one evidence count — read <span class="cav">≈</span> carefully.</b>
    The join key is <code>form_key()</code>, the length-preserving floor tier, which folds the
    final visarga and homorganic nasals. So <i>rāmaḥ</i> (nom. sg.) and <i>rāma</i> (voc. sg.)
    reduce to the same key and are credited with the <b>same</b> occurrence count — the corpus
    evidence says "this key occurs 3,325 times", not "3,325 of them are vocatives". Any cell
    matched below a byte-identical SLP1 key carries <span class="cav">≈</span>; where two cells
    of one paradigm show an identical count, that is this fold, not a claim that both functions
    are equally attested. Case-level disambiguation needs the DCS morphological tags, which this
    page deliberately does not infer.</p>
    <p>R-C4: DCS conflates aorist and perfect under <code>Tense=Past</code>; cells whose evidence
    carries a Past-tense token are flagged <span class="cav">▵</span> rather than excluded.
    Citable locus IDs are host-independent (<code>dcs:&lt;sent_id&gt;</code> — DCS's own stable
    sentence id, resolvable against any copy of the corpus). CSV fallback: the two dataset TSVs
    above. Full method:
    <a href="https://github.com/gasyoun/kosha/blob/main/data/concordance/MORPHOLOGY_ATTESTATION_INFLECTIONS_BUILD_REPORT.md">build report</a>.</p>
  </div>
</main>
<script src="data/stats.js"></script>
<script>
window.MORPH_DATA = {};
var I2S = [["ai","E"],["au","O"],["kh","K"],["gh","G"],["ch","C"],["jh","J"],
  ["ṭh","W"],["ḍh","Q"],["th","T"],["dh","D"],["ph","P"],["bh","B"],
  ["ā","A"],["ī","I"],["ū","U"],["ṝ","F"],["ṛ","f"],["ḹ","X"],["ḷ","x"],
  ["ṃ","M"],["ṁ","M"],["ḥ","H"],["ṅ","N"],["ñ","Y"],["ṭ","w"],["ḍ","q"],
  ["ṇ","R"],["ś","S"],["ṣ","z"]];
function toSlp1(s){ s=(s||"").trim();
  for(var i=0;i<I2S.length;i++) s=s.split(I2S[i][0]).join(I2S[i][1]); return s; }
function letterOf(k){ var c=(k||"?")[0].toLowerCase(); return /[a-z]/.test(c)?c:"_"; }
// A letter may be split into size-capped chunks over sorted keys; pick the last chunk
// whose first key still sorts at or before the query, and fall back to the first chunk
// for a query that precedes them all (a prefix search must still find its neighbours).
function chunksFor(letter){ return (window.MORPH_SHARDS||{})[letter]||[]; }
function chunkFor(key){
  var cs=chunksFor(letterOf(key));
  if(!cs.length) return null;
  var pick=cs[0][1];
  for(var i=0;i<cs.length;i++){ if(cs[i][0]<=key) pick=cs[i][1]; else break; }
  return pick;
}
var loaded={};
function ensureShard(name,cb){
  if(!name) return cb();
  if(loaded[name]) return cb();
  var s=document.createElement("script"); s.src="data/kwic_"+name+".js";
  s.onload=function(){loaded[name]=1;cb();}; s.onerror=function(){loaded[name]=1;cb();};
  document.head.appendChild(s); }
// Every chunk of a letter merges into one bucket, so prefix search sees the whole letter
// once its chunks are loaded, and a lookup never depends on which chunk happened to load.
window.MORPH_ADD=function(name,obj){
  var letter=name.split("_")[0];
  var b=window.MORPH_DATA[letter]=window.MORPH_DATA[letter]||{};
  for(var k in obj) b[k]=obj[k];
};
function esc(t){ var d=document.createElement("div"); d.textContent=t==null?"":String(t); return d.innerHTML; }
function hi(sent,form){ if(!form) return esc(sent);
  var i=sent.toLowerCase().indexOf(form.toLowerCase()); if(i<0) return esc(sent);
  return esc(sent.slice(0,i))+"<mark>"+esc(sent.slice(i,i+form.length))+"</mark>"+esc(sent.slice(i+form.length)); }
var CASES=["nom","acc","instr","dat","abl","gen","loc","voc"], NUMS=["sg","du","pl"],
    GLABEL={m:"masculine",n:"neuter",f:"feminine","":"indeclinable / uninflected"};

function paradigm(cells){
  var byG={}; cells.forEach(function(c){ (byG[c.g]=byG[c.g]||[]).push(c); });
  var h="";
  Object.keys(byG).sort().forEach(function(g){
    var grid={}, loose=[];
    byG[g].forEach(function(c){
      if(CASES.indexOf(c.cs)>=0 && NUMS.indexOf(c.n)>=0){
        (grid[c.cs+"|"+c.n]=grid[c.cs+"|"+c.n]||[]).push(c);
      } else loose.push(c);
    });
    h+="<h3>"+esc(GLABEL[g]||g)+"</h3>";
    if(Object.keys(grid).length){
      h+='<table class="para"><tr><th></th>'+NUMS.map(function(n){return "<th>"+n+"</th>";}).join("")+"</tr>";
      CASES.forEach(function(cs){
        var any=NUMS.some(function(n){return grid[cs+"|"+n];});
        if(!any) return;
        h+="<tr><th>"+cs+"</th>";
        NUMS.forEach(function(n){
          var cc=grid[cs+"|"+n];
          if(!cc){ h+='<td class="c no">—</td>'; return; }
          var att=cc.some(function(c){return c.a;});
          h+='<td class="c '+(att?"yes":"no")+'" title="'+esc(cc.map(function(c){return c.f;}).join(" "))+'">'+cc.map(function(c){
            return '<span class="frm">'+esc(c.i)+"</span>"+
              (c.a?'<span class="occ">'+c.o+"×</span>":"")+
              (c.t?'<span class="cav" title="floor tier — matched on the length-preserving form_key, not a byte-identical SLP1 key">≈</span>':"")+
              (c.c?'<span class="cav" title="DCS Tense=Past conflates aorist and perfect">▵</span>':"");
          }).join("<br>")+"</td>";
        });
        h+="</tr>";
      });
      h+="</table>";
    }
    if(loose.length){
      h+='<div class="note">'+loose.map(function(c){
        return '<span class="frm">'+esc(c.i)+"</span>"+(c.a?'<span class="occ">'+c.o+"×</span>":"");
      }).join(" · ")+"</div>";
    }
  });
  return h;
}

function verbs(cells){
  if(!cells.length) return "";
  var h="<h3>verbal cells</h3><table class=\"para\"><tr><th>form</th><th>person</th><th>tense</th><th>voice</th><th>number</th><th>attested</th></tr>";
  cells.slice(0,60).forEach(function(c){
    h+="<tr><td"+(c.a?' class="yes"':' class="no"')+'><span class="frm">'+esc(c.i)+"</span></td><td>"+
      esc(c.p)+"</td><td>"+esc(c.te)+"</td><td>"+esc(c.v)+"</td><td>"+esc(c.n)+"</td><td>"+
      (c.a?c.o+"×":"—")+"</td></tr>";
  });
  return h+"</table>";
}

function kwics(cells){
  var out=cells.filter(function(c){return c.k;}).slice(0,8);
  if(!out.length) return "";
  return "<h3>corpus evidence</h3>"+out.map(function(c){
    return '<div class="kw">'+hi(c.k,c.s)+'<span class="loc">'+esc(c.l)+"</span></div>";
  }).join("");
}

function gaps(g){
  if(!g.length) return '<h3>gaps — attested, never generated</h3><div class="note">None for this lemma: every DCS-attested form of it is produced by the generator.</div>';
  var verbal=g.filter(function(x){return x.u==="VERB";}).length,
      surf=g.filter(function(x){return x.vi==="surface";}).length;
  var h="<h3>gaps — attested, never generated</h3>";
  if(verbal||surf){
    h+='<div class="callout">Of '+g.length+" shown, "+verbal+
      " carry DCS <code>upos=VERB</code> (the generator holds 680 verbal lemmas against 222,736 nominal — out of scope, not a defect) and "+
      surf+" are attested only as a <i>sandhied surface</i> (an artefact of the attested side, since a generator emits unsandhied forms). Neither class is an engine gap.</div>";
  }
  h+='<ul class="gaps">'+g.map(function(x){
    var dim=(x.vi==="surface"||x.u==="VERB")?' class="surf"':"";
    return "<li"+dim+'><span class="frm">'+esc(x.f)+"</span>"+
      '<span class="u">'+esc(x.u||"—")+"</span>"+
      '<span class="occ" style="color:var(--gap)">'+x.o+"×</span>"+
      '<span class="loc" style="font-family:Consolas,monospace;font-size:11px;color:#889"> '+esc(x.l)+"</span>"+
      '<span class="note" style="display:inline;margin-left:6px">'+esc(x.t.replace(/_/g," "))+
      (x.vi==="surface"?", sandhied surface only":"")+"</span></li>";
  }).join("")+"</ul>";
  return h;
}

function renderEntry(key,e){
  var p=e.tot?Math.round(100*e.att/e.tot):0;
  var h='<div class="entry"><div class="hw">'+esc(e.iast)+
    '<span class="slp">'+esc(key)+'</span>'+
    (e.freq?'<span class="freq">'+e.freq.toLocaleString()+" corpus tokens</span>":"")+"</div>"+
    '<div class="bar"><i style="width:'+p+'%"></i></div>'+
    '<div class="barlab">'+e.att+" of "+e.tot+" generated cells attested in DCS ("+p+"%)"+
    (e.att===0?" — nothing this generator produces for this lemma occurs in the corpus":"")+
    ((e.mdl&&e.mdl.length)?' · declension model '+e.mdl.map(esc).join(", "):"")+"</div>";
  h+=paradigm(e.nom||[]);
  h+=verbs(e.vrb||[]);
  h+=kwics((e.nom||[]).concat(e.vrb||[]));
  h+=gaps(e.gap||[]);
  return h+"</div>";
}

var q=document.getElementById("q"), out=document.getElementById("out"),
    matches=document.getElementById("matches");
function ensureIndex(letter,cb){
  if(window.MORPH_INDEX && window.MORPH_INDEX[letter]) return cb();
  var s=document.createElement("script"); s.src="data/index_"+letter+".js";
  s.onload=cb; s.onerror=cb; document.head.appendChild(s);
}
function show(key){
  ensureShard(chunkFor(key),function(){
    var b=window.MORPH_DATA[letterOf(key)]||{};
    if(b[key]) out.innerHTML=renderEntry(key,b[key]);
    else out.innerHTML='<p class="none">Entry for “'+esc(key)+'” could not be loaded.</p>';
  });
}
function lookup(){
  var raw=q.value.trim(); matches.innerHTML=""; out.innerHTML="";
  if(!raw) return;
  var key=toSlp1(raw), letter=letterOf(key);
  ensureIndex(letter,function(){
    var idx=(window.MORPH_INDEX||{})[letter]||{};
    if(idx[key]){ show(key); return; }
    var pref=Object.keys(idx).filter(function(k){return k.indexOf(key)===0;}).sort().slice(0,60);
    if(!pref.length){ out.innerHTML='<p class="none">No head lemma starts with “'+esc(raw)+
      '”. The page carries the '+(window.MORPH_STATS?window.MORPH_STATS.head_n.toLocaleString():"")+
      ' most frequent DCS lemmas (covering '+(window.MORPH_STATS?window.MORPH_STATS.coverage.toFixed(2):"")+
      '% of corpus tokens); a rarer lemma is in the dataset TSVs but not in this static head.</p>'; return; }
    matches.innerHTML=pref.map(function(k){
      return '<a href="#'+encodeURIComponent(k)+'" data-k="'+esc(k)+'">'+esc(idx[k][0])+
        ' <span style="font-size:11px;color:#889">'+idx[k][1]+"/"+idx[k][2]+"</span></a>";
    }).join("");
    matches.querySelectorAll("a").forEach(function(a){
      a.onclick=function(ev){ ev.preventDefault(); q.value=a.dataset.k; lookup();
        history.replaceState(null,"","#"+encodeURIComponent(a.dataset.k)); };
    });
  });
}
q.addEventListener("input",lookup);
if(location.hash.length>1){ q.value=decodeURIComponent(location.hash.slice(1)); lookup(); }
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
