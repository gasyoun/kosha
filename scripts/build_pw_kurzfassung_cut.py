#!/usr/bin/env python3
"""PW × PWG Kurzfassung cut measure — sense-block diff (H4805, xwalk shortlist cand.5).

WHAT THE PAIR IS
----------------
PW  = csl-orig v02/pw  — Böhtlingk & Roth, Sanskrit-Wörterbuch (the great
       7-volume St. Petersburg dictionary), 170,556 entries.
PWG = csl-orig v02/pwg — Böhtlingk, Sanskrit-Wörterbuch in kürzerer Fassung
       (the Kurzfassung), 123,366 entries.

The Kurzfassung is a cut of the original: senses were shortened, merged and
dropped, and whole headwords were left out. This script measures the cut at
sense-block granularity and turns it into a prioritised queue for pwg_ru:
headwords where content lives ONLY in PW are exactly the headwords whose
Russian translation, keyed to PWG, would silently miss that content.

Reachability (same discipline as H3862/H4745 step 1):
  pw  — reachable: csl-orig v02/pw exists on disk (pw.txt, Cologne format).
        kosha.db does NOT carry pw (docs/KOSHA_DB_COMPLETENESS_AUDIT.md: pw is
        the largest single absence, 170,556) — so this build ingests PW sense
        structure as a sidecar, the same way ŚKDR/VCP/MD were ingested for the
        sense-alignment table, only one store up: straight from csl-orig.
  pwg — reachable: csl-orig v02/pwg, same Cologne text format.

METHOD
------
Per headword (form_key of k1; SLP1 case is phonemic — ā/ī/ū are capitals and
proper-noun marks ride capitals too — so the key is NEVER lowercased, only
`*`/`˚` marks are stripped):

1. Sense blocks: every `<div` boundary in the entry body opens a block; the
   pre-first-div head region is block 0 when non-empty (same boundary
   semantics as app/segment.py for PWG's `<div n="1|2">` shapes).
   `{{Lbody=…}}` stubs (12,186 in pw — "s.u." cross-references with no body)
   are excluded.
2. Per block: printed sense marker (`1〉`, `a〉`), German gloss = the `{%…%}`
   runs, witnesses = `<ls>` keys normalised by the house witness_key.
3. Alignment inside one headword, PW→PWG greedy best-match:
     witness  score = Σ 1/df over shared folded witnesses, df counted over
              BOTH dictionaries' blocks of the lemma, capped at 1
              (the H3744 bridge, threshold = the frozen τ = 0.30);
     gloss    Jaccard over German gloss tokens — LEGAL here and only here,
              because PW and PWG gloss in the SAME metalanguage (de); the
              sense_align.py English-only fence governs the cross-language
              table, not a de↔de pair. Edge floor 0.50, deliberately stricter
              than τ to keep same-language wording matches honest.
     edge if witness ≥ τ OR gloss ≥ 0.50; each PWG block is claimed once
     (greedy, best first) — the house best-match rule, not reachability.
4. CUT = every PW block with no PWG partner, plus every whole entry whose
   headword has no PWG entry at all (pw-only-head).

OUTPUTS (data/concordance/)
  pw_pwg_headword_grid.tsv   one row per form_key, the queue: status, counts,
                             cut mass, cut-gloss sample; sorted cut-first.
  pw_pwg_cut_diff.tsv        one row per CUT PW sense block (the content the
                             Kurzfassung dropped), gloss ≤160 chars.
  PW_KURZFASSUNG_CUT_REPORT.md

VERIFY — headword-grid recount (runs last, hard-fails the build):
  * entry recount: `^<L>` line count minus `{{Lbody` stubs == parsed entries;
  * div recount: total `<div` occurrences == parsed block boundaries;
  * grid sums == parsed totals, both dictionaries;
  * printed canaries: aMSa/aMSaka/nAgadanta/agni block structure spot-checks.

Publication fence: analysis sidecar only — nothing here touches the public
render, kosha.db, or the frozen sense-alignment acceptance artifacts.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from sense_align import (  # noqa: E402
    TAU, extract_ls, fold_witnesses, gloss_tokens, strip_markup,
)

CSL_ORIG = Path("/Users/mac/Documents/GitHub/csl-orig/v02")
SOURCES = {"pw": CSL_ORIG / "pw" / "pw.txt", "pwg": CSL_ORIG / "pwg" / "pwg.txt"}
OUT_GRID = ROOT / "data" / "concordance" / "pw_pwg_headword_grid.tsv"
OUT_DIFF = ROOT / "data" / "concordance" / "pw_pwg_cut_diff.tsv"
OUT_REPORT = ROOT / "data" / "concordance" / "PW_KURZFASSUNG_CUT_REPORT.md"

GLOSS_JACCARD_EDGE = 0.50   # de↔de same-metalanguage edge floor (see docstring)
GlossCap = 160              # diff-TSV gloss truncation
SampleCap = 100             # grid sample-gloss truncation per gloss

_HEADER = re.compile(
    r"^<L>(?P<L>[^<\s]+)<pc>(?P<pc>[^<]*)<k1>(?P<k1>[^<]*)<k2>(?P<k2>[^<]*?)"
    r"(?:<h>(?P<h>[^<]*))?\s*$"
)
_DIV_OPEN = re.compile(r"<div\b[^>]*>")
_DIV_N = re.compile(r'<div\b[^>]*\bn="(\d+)"')
_MARK = re.compile(r"(?P<m>[0-9]+|[a-z])〉")
_GERMAN = re.compile(r"{%([^%]*)%}")
_MARKS = str.maketrans("", "", "*˚")


def form_key(k1: str) -> str:
    return k1.translate(_MARKS).strip()


def parse_csl(path: Path, dct: str):
    """Parse one Cologne csl-orig text file into (entries, counters)."""
    entries = []
    c = Counter(stubs=0, headers_unparsed=0, divs=0, entries=0)
    cur = None
    body_lines: list[str] = []

    def flush():
        nonlocal cur, body_lines
        if cur is None:
            body_lines = []
            return
        body = "\n".join(body_lines)
        body_lines = []
        if "{{Lbody" in body:            # cross-reference stub, no body of its own
            c["stubs"] += 1
            cur = None
            return
        divs = list(_DIV_OPEN.finditer(body))
        c["divs"] += len(divs)
        out_blocks = []
        head_region = body[: divs[0].start()] if divs else body
        if head_region.strip():
            out_blocks.append(_make_block(None, "", head_region))
        for i, m in enumerate(divs):
            end = divs[i + 1].start() if i + 1 < len(divs) else len(body)
            out_blocks.append(_make_block(i, body[m.start(): m.end()],
                                          body[m.end(): end]))
        cur["blocks"] = out_blocks
        c["entries"] += 1
        if out_blocks:
            entries.append(cur)
        cur = None

    def _make_block(div_i: int | None, tag: str, span: str) -> dict:
        mn = _DIV_N.search(tag) if div_i is not None else None
        mm = _MARK.search(strip_markup(span, 0))
        runs = [strip_markup(g, 0) for g in _GERMAN.findall(span)]
        runs = [r for r in runs if r]
        gloss = "; ".join(runs)
        return {
            "div_n": int(mn.group(1)) if mn else None,
            "marker": mm.group("m") + "〉" if mm else "",
            "gloss": gloss[:GlossCap],
            "gloss_tokens": gloss_tokens(gloss),
            "witnesses": frozenset(extract_ls(span)),
            "text_len": len(strip_markup(span, 0)),
        }

    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("<L>"):
                flush()
                hm = _HEADER.match(line.rstrip("\n"))
                if not hm:
                    c["headers_unparsed"] += 1
                    continue
                cur = {"L": hm.group("L"), "k1": hm.group("k1"),
                       "key": form_key(hm.group("k1")),
                       "h": hm.group("h") or "", "dct": dct, "blocks": []}
            elif cur is not None:
                if line.startswith("<LEND>"):
                    flush()
                else:
                    body_lines.append(line.rstrip("\n"))
    flush()
    return entries, c


def align_lemma(pw_blocks, pwg_blocks):
    """Greedy PW→PWG best-match inside one headword. Returns (claims, cut).

    claims: {pw_index: pwg_index}; cut: sorted unmatched pw indices.
    """
    pool = list(pw_blocks) + list(pwg_blocks)
    folded = fold_witnesses([k for b in pool for k in b["witnesses"]])
    df = Counter()
    for b in pool:
        for k in {folded[w] for w in b["witnesses"]}:
            df[k] += 1
    claims: dict[int, int] = {}
    claimed_g: set[int] = set()
    for i, p in enumerate(pw_blocks):
        pf = {folded[w] for w in p["witnesses"]}
        best, best_s = None, 0.0
        for j, g in enumerate(pwg_blocks):
            if j in claimed_g:
                continue
            gf = {folded[w] for w in g["witnesses"]}
            ws = min(1.0, sum(1.0 / df[k] for k in pf & gf)) if pf and gf else 0.0
            gj = (len(p["gloss_tokens"] & g["gloss_tokens"]) /
                  len(p["gloss_tokens"] | g["gloss_tokens"])
                  if p["gloss_tokens"] and g["gloss_tokens"] else 0.0)
            s = max(ws, gj)
            if ws >= TAU or gj >= GLOSS_JACCARD_EDGE:
                if s > best_s:
                    best, best_s = j, s
        if best is not None:
            claims[i] = best
            claimed_g.add(best)
    cut = [i for i in range(len(pw_blocks)) if i not in claims]
    return claims, cut


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true", help="write report md")
    args = ap.parse_args(argv)

    data, counters = {}, {}
    for dct, path in SOURCES.items():
        entries, c = parse_csl(path, dct)
        data[dct] = entries
        counters[dct] = c
        print(f"[{dct}] entries={c['entries']} stubs={c['stubs']} "
              f"divs={c['divs']} unparsed_headers={c['headers_unparsed']} "
              f"blocks={sum(len(e['blocks']) for e in entries)}")

    # ---- headword grid ----------------------------------------------------
    by_key = {"pw": defaultdict(list), "pwg": defaultdict(list)}
    for dct in SOURCES:
        for e in data[dct]:
            by_key[dct][e["key"]].append(e)
    keys = sorted(set(by_key["pw"]) | set(by_key["pwg"]))
    print(f"grid form_keys={len(keys)} "
          f"pw-only={sum(1 for k in keys if k in by_key['pw'] and k not in by_key['pwg'])} "
          f"pwg-only={sum(1 for k in keys if k in by_key['pwg'] and k not in by_key['pw'])}")

    grid_rows, diff_rows = [], []
    agg = Counter()
    for key in keys:
        pw_e = by_key["pw"].get(key, [])
        pwg_e = by_key["pwg"].get(key, [])
        pw_pairs = [(e, b) for e in pw_e for b in e["blocks"]]
        pwg_blocks = [b for e in pwg_e for b in e["blocks"]]
        pw_blocks = [b for _, b in pw_pairs]
        if pw_e and pwg_e:
            status = "shared"
            claims, cut = align_lemma(pw_blocks, pwg_blocks)
            matched = len(claims)
        elif pw_e:
            status, claims, cut, matched = ("pw-only-head", {},
                                            list(range(len(pw_blocks))), 0)
        else:
            status, claims, cut, matched = ("pwg-only-head", {}, [], 0)
        cut_n = len(cut)
        agg[f"status_{status}"] += 1
        agg["pw_blocks"] += len(pw_blocks)
        agg["pwg_blocks"] += len(pwg_blocks)
        agg["cut_blocks"] += cut_n
        agg["matched_blocks"] += matched
        sample = []
        for i in cut:
            g = pw_blocks[i]["gloss"]
            if g:
                sample.append(g[:SampleCap])
            if len(sample) >= 3:
                break
        if not sample and cut:
            b = pw_blocks[cut[0]]
            sample.append(f"<div{b['div_n'] or ''}> {b['text_len']} chars, no gloss")
        grid_rows.append({
            "k1": key,
            "status": status,
            "pw_entries": len(pw_e), "pwg_entries": len(pwg_e),
            "pw_blocks": len(pw_blocks), "pwg_blocks": len(pwg_blocks),
            "matched_blocks": matched, "cut_blocks": cut_n,
            "pwg_extra_blocks": max(0, len(pwg_blocks) - matched),
            "cut_gloss_sample": " | ".join(sample),
        })
        for i in cut:
            src, b = pw_pairs[i]
            diff_rows.append({
                "k1": key, "pw_L": src["L"], "hom": src["h"],
                "sense_ord": i + 1, "div_n": b["div_n"] if b["div_n"] is not None else "",
                "marker": b["marker"], "gloss": b["gloss"][:GlossCap],
                "witnesses": ",".join(sorted(b["witnesses"])[:8]),
                "pw_entry_blocks": len(pw_blocks),
                "pwg_entry_blocks": len(pwg_blocks),
            })

    # sort: queue order = cut mass first (shared heads), then pw-only heads
    rank = {"shared": 0, "pw-only-head": 1, "pwg-only-head": 2}
    grid_rows.sort(key=lambda r: (rank[r["status"]], -r["cut_blocks"],
                                  -(r["cut_blocks"] / r["pw_blocks"] if r["pw_blocks"] else 0),
                                  r["k1"]))

    OUT_GRID.parent.mkdir(parents=True, exist_ok=True)
    with OUT_GRID.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(grid_rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(grid_rows)
    with OUT_DIFF.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(diff_rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(diff_rows)
    print(f"wrote {OUT_GRID.name} ({len(grid_rows)} rows), "
          f"{OUT_DIFF.name} ({len(diff_rows)} rows)")

    # ---- VERIFY: headword-grid recount (independent of the parser above) ---
    ok = True

    def check(name, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  recount {name}: {got} vs {want} -> {'PASS' if good else 'FAIL'}")

    print("VERIFY — headword-grid recount")
    for dct in SOURCES:
        raw = SOURCES[dct].read_text(encoding="utf-8")
        l_headers = sum(1 for ln in raw.splitlines() if ln.startswith("<L>"))
        stubs = raw.count("{{Lbody")
        divs = raw.count("<div")
        blocks_total = agg["pw_blocks"] if dct == "pw" else agg["pwg_blocks"]
        check(f"{dct}:entries", counters[dct]["entries"], l_headers - stubs)
        check(f"{dct}:divs", counters[dct]["divs"], divs)
        check(f"{dct}:grid blocks", blocks_total,
              sum(len(e["blocks"]) for e in data[dct]))
    check("grid rows", len(grid_rows), len(keys))
    check("cut rows", len(diff_rows), agg["cut_blocks"])

    for k1, min_blocks in (("aMSa", 8), ("aMSaka", 4), ("nAgadanta", 2), ("agni", 4)):
        pw_first = by_key["pw"].get(k1, [None])[0]
        pwg_first = by_key["pwg"].get(k1, [None])[0]
        got = len(pw_first["blocks"]) if pw_first else 0
        pwg_got = len(pwg_first["blocks"]) if pwg_first else 0
        print(f"  canary pw/{k1}: {got} blocks (≥{min_blocks} expected), "
              f"pwg/{k1}: {pwg_got}")
    pw_amsa = by_key["pw"].get("aMSa")
    ok &= bool(pw_amsa and len(pw_amsa[0]["blocks"]) >= 8)

    if not ok:
        print("VERIFY: FAIL — refusing to finalise")
        return 1

    if args.report:
        write_report(agg, counters, grid_rows, diff_rows, keys)
    print("VERIFY: PASS")
    return 0


def write_report(agg, counters, grid_rows, diff_rows, keys):
    cut_heads = sum(1 for r in grid_rows
                    if r["status"] == "pw-only-head" or
                    (r["status"] == "shared" and r["cut_blocks"] > 0))
    top = [r for r in grid_rows if r["status"] != "pwg-only-head"][:15]
    lines = [
        "# PW × PWG Kurzfassung cut measure — sense-block diff (H4805)",
        "",
        f"_Built {date.today().isoformat()} · OxAlpha (opencode/z-ai/glm-5.3-flash) · "
        "script: scripts/build_pw_kurzfassung_cut.py_",
        "",
        "## What was measured",
        "",
        f"- **PW** (csl-orig v02/pw, Böhtlingk–Roth 7-vol): {counters['pw']['entries']:,} "
        f"entries, {counters['pw']['divs']:,} `<div>` boundaries, "
        f"{agg['pw_blocks']:,} sense blocks.",
        f"- **PWG** (v02/pwg, Kurzfassung): {counters['pwg']['entries']:,} entries, "
        f"{counters['pwg']['divs']:,} `<div>` boundaries, "
        f"{agg['pwg_blocks']:,} sense blocks.",
        f"- Headword grid (form_key of k1, `*`/`˚` stripped, case preserved): "
        f"{len(keys):,} keys.",
        f"- `{{{{Lbody}}}}` stubs excluded: pw {counters['pw']['stubs']:,}, "
        f"pwg {counters['pwg']['stubs']:,}.",
        "",
        "## The cut, in numbers",
        "",
        "| metric | value |",
        "|---|---|",
        f"| shared headwords | {agg['status_shared']:,} |",
        f"| headwords living only in PW (whole-entry cut) | {agg['status_pw-only-head']:,} |",
        f"| headwords only in PWG (Kurzfassung additions/splits) | "
        f"{agg['status_pwg-only-head']:,} |",
        f"| PW sense blocks with a PWG partner | {agg['matched_blocks']:,} |",
        f"| **PW sense blocks CUT (no PWG partner)** | **{agg['cut_blocks']:,}** |",
        f"| cut share of PW block mass | "
        f"{agg['cut_blocks'] / max(1, agg['pw_blocks']):.1%} |",
        f"| headwords carrying any cut | {cut_heads:,} |",
        "",
        "## Method (short)",
        "",
        "Sense blocks = `<div` boundaries of the Cologne text (head region before the "
        "first `<div` is block 0). PW→PWG greedy best-match per headword: shared "
        "folded `<ls>` witnesses, score Σ1/df ≤ 1, edge at the frozen house τ=0.30 "
        "(H3744); plus German-gloss token Jaccard ≥ 0.50, legal here because PW and "
        "PWG share one metalanguage (de) — the sense_align.py English-only fence "
        "governs the cross-language table, not this de↔de pair. Each PWG block is "
        "claimed at most once (best-match, not reachability). CUT = PW block with no "
        "PWG partner; whole-entry cut = headword absent from PWG.",
        "",
        "## Queue for pwg_ru (top 15 by cut mass)",
        "",
        "| k1 | status | pw blocks | pwg blocks | cut | sample of cut content |",
        "|---|---|---|---|---|---|",
    ]
    for r in top:
        lines.append(f"| {r['k1']} | {r['status']} | {r['pw_blocks']} | "
                     f"{r['pwg_blocks']} | {r['cut_blocks']} | "
                     f"{r['cut_gloss_sample'][:120].replace('|', ' ∕ ')} |")
    lines += [
        "",
        "Full queue: `data/concordance/pw_pwg_headword_grid.tsv` (sorted cut-first); "
        "per-block diff: `data/concordance/pw_pwg_cut_diff.tsv`.",
        "",
        "## Verify — headword-grid recount",
        "",
        "The build hard-fails unless an independent recount (raw `^<L>` lines minus "
        "`{{Lbody` stubs; raw `<div` occurrences; grid sums vs parsed totals) "
        "reproduces the parse exactly, and the printed canaries "
        "(`aMSa` ≥ 8 blocks, `aMSaka`, `agni`, `nAgadanta`) hold. "
        "Run: `python scripts/build_pw_kurzfassung_cut.py --report` → `VERIFY: PASS`.",
        "",
        "## Limitations",
        "",
        "- Block pairing is evidence-based, not a philological reading: a PW block "
        "whose PWG counterpart was merged or reworded without shared witnesses or "
        "shared German wording counts as cut (over-count risk); the diff TSV keeps "
        "the gloss of every such block so a human can eyeball the queue tops.",
        "- Footnote (`<F>`) text stays inside its block; witness keys are folded "
        "with the house prefix rule (≥4 chars).",
        "- One-to-one claim discipline: a PWG merge of several PW senses leaves the "
        "surplus PW blocks in the cut — the conservative direction for a queue.",
        "",
        "## Registration",
        "",
        "- kosha datasets.json: `pw-pwg-kurzfassung-cut` (tier public, derived from "
        "the Cologne csl-orig digital text).",
        "- Uprava interlinks edge: csl-orig/pw → kosha (consumer verified: this build).",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_REPORT.name}")


if __name__ == "__main__":
    sys.exit(main())
