#!/usr/bin/env python
"""SandhiKosh splitter bake-off — H6841 / WHEEL9 item (a).

Reuses the WHEEL6/H6456 comparison-harness pattern
(SanskritGrammar scripts/pilot_process_sanskrit_vs_rules.py) — no new splitter,
no new scorer. Two arms on the committed SandhiKosh TSV
(data/sandhi/sandhikosh/*.tsv):

  upstream  — Process-Sanskrit (pip, vendored sanskrit_parser splitter, DCS
              word2vec scoring bundled as w2v.npz): parser.split(joined,
              limit=5), top-ranked split; the split runtime ADOPTED as the
              house splitter by WHEEL6/H6456.
  ours      — H6456 rule-lookup arm over the kosha induced/hand sandhi rule
              tables (data/sandhi/*.tsv, IAST `X Y → Z`): each surface form Z
              yields a candidate split, ranked by frequency mass. Audit-layer
              rules without a lexicon — expected near-zero here (H6456 showed
              the structural limit; replicated per-category below).

Inputs are Devanagari; both gold and predictions are transliterated to IAST
with indic_transliteration before canonicalization (NFC + anusvāra ṃ/ṁ → m),
exactly the H6456 comparison convention. Items whose joined form contains a
space (surface shows no single sandhi; e.g. `śabda iva`) are EXCLUDED from the
junction bench and counted per source — SandhiKosh includes such no-change
spans, which the H6456-style junction protocol (single sandhied form → split)
does not measure.

Neuro arm (ByT5-Sanskrit / CharSS): NOT run — the harness does not host HF
checkpoints; hosting would be rework (H6841 step 3 "IF ... without rework").
Recorded as declined in the dated report.

Usage:
  pip install process-sanskrit indic-transliteration
  python tools/sandhikosh_bakeoff.py [--n-per-source N] [--out reports/sandhikosh_bakeoff_metrics.json]
"""
import argparse
import csv
import json
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH_DIR = ROOT / "data" / "sandhi" / "sandhikosh"
RULE_TABLES = [ROOT / "data" / "sandhi" / f for f in
               ("gita_sandhi_rules.tsv",)]  # fallback; real tables resolved at load


def canon(s: str) -> str:
    """H6456 comparison canonical: NFC + anusvāra variants (ṃ/ṁ) unified to m."""
    s = unicodedata.normalize("NFC", s or "")
    return s.replace("ṃ", "m").replace("ṁ", "m")


def load_bench():
    rows = []
    for tsv in sorted(BENCH_DIR.glob("*.tsv")):
        if tsv.name == "convert_summary.json" or not tsv.suffix == ".tsv":
            continue
        with open(tsv, encoding="utf-8") as fh:
            rd = csv.DictReader(fh, delimiter="\t")
            for r in rd:
                r["_source_file"] = tsv.stem
                rows.append(r)
    return rows


def load_rules():
    """H6456 ours-arm rule inventory: IAST `rule<TAB>category<TAB>count<TAB>...`
    rows; keys = sandhied surface Z → list of (parts, freq)."""
    rules = defaultdict(list)
    n_files = 0
    sandhi_dir = ROOT / "data" / "sandhi"
    for tsv in sorted(sandhi_dir.glob("*_sandhi.tsv")):
        if tsv.name in ("corpus_sandhi.tsv",):
            continue
        with open(tsv, encoding="utf-8", errors="replace") as fh:
            rd = csv.reader(fh, delimiter="\t")
            try:
                header = next(rd)
            except StopIteration:
                continue
            for row in rd:
                if len(row) < 3 or not row[0] or "→" not in row[0]:
                    continue
                lhs, rhs = row[0].split("→", 1)
                parts = lhs.strip().split()
                z = rhs.strip()
                if len(parts) != 2:
                    continue
                try:
                    freq = int(float(row[2]))
                except (ValueError, TypeError):
                    freq = 1
                rules[canon(z)].append((parts, freq))
        n_files += 1
    return rules, n_files


def _pausa_normalize(iast_word):
    """House convention from scripts/compare_sandhi_methods.py: a word-final
    underlying -s/-r (Pāṇinian pausa citation form, e.g. `vacanas`) becomes
    visarga `ḥ` in isolation — matching SandhiKosh's citation gold (`vacanaḥ`).
    Applied as a SEPARATE arm (upstream+pausa), not to the primary arm, so the
    pausa-vs-visarga mismatch itself stays visible in the numbers (H6456
    symmetric-comparison discipline)."""
    return (iast_word[:-1] + "ḥ") if iast_word and iast_word[-1] in ("s", "r") else iast_word


def ours_split(joined, rules):
    """Rule-lookup splitter (H6456 ours arm): surface-occurrence + freq rank."""
    cands = rules.get(canon(joined), [])
    if not cands:
        return None
    cands = sorted(cands, key=lambda t: -t[1])
    return cands[0][0]


def upstream_split(parser, joined_iast):
    from indic_transliteration import sanscript
    splits = parser.split(joined_iast, limit=5)
    if not splits:
        return None
    top = splits[0].split
    return [sanscript.transliterate(o.canonical(), sanscript.SLP1, sanscript.IAST)
            for o in top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-per-source", type=int, default=0,
                    help="cap items per source (0 = full run)")
    ap.add_argument("--out", default=str(ROOT / "reports" / "sandhikosh_bakeoff_metrics.json"))
    a = ap.parse_args()

    from indic_transliteration import sanscript

    def dev_to_iast(s):
        return sanscript.transliterate((s or "").replace("+", " "), sanscript.DEVANAGARI, sanscript.IAST)

    bench = load_bench()
    rules, n_rule_files = load_rules()
    print(f"bench items: {len(bench)}; rule files: {n_rule_files}; rule surface keys: {len(rules)}")

    arms = ["upstream", "upstream+pausa", "ours"]
    agg = {k: {"exact": 0, "first": 0, "scored": 0, "null": 0, "errs": 0}
           for k in arms}
    by_cat = defaultdict(lambda: {k: {"exact": 0, "scored": 0, "null": 0} for k in arms})
    by_src = defaultdict(lambda: {**{k + "_exact": 0 for k in arms},
                                  **{k + "_first": 0 for k in arms},
                                  "scored": 0, "excluded_space": 0})
    examples = []
    parser = None
    if "--skip-upstream" not in sys.argv:
        from process_sanskrit.splitter import Parser
        parser = Parser()

    t_start = time.perf_counter()
    per_source_tally = defaultdict(int)
    for item in bench:
        src = item["_source_file"]
        n_per = per_source_tally[src]
        if a.n_per_source and n_per >= a.n_per_source:
            continue
        per_source_tally[src] += 1
        gold_iast = canon(dev_to_iast(item["split"]))
        gold_parts = [canon(p) for p in gold_iast.split() if p]
        joined_raw = item["word"] or ""
        joined_iast = canon(dev_to_iast(joined_raw).replace(" ", ""))
        # exclusion protocol: space in the ORIGINAAL surface = no single junction
        if " " in joined_raw.strip():
            by_src[src]["excluded_space"] += 1
            continue
        if len(gold_parts) < 2:
            by_src[src]["excluded_space"] += 1  # same bucket: no junction (counted per source)
            continue
        by_src[src]["scored"] += 1
        cat = (item.get("type") or "").strip() or "unlabeled"
        for arm in arms:
            try:
                if arm == "ours":
                    pred = ours_split(joined_iast, rules)
                    if pred is not None:
                        pred = [canon(p) for p in pred]
                else:
                    if parser is None:
                        continue
                    pred = upstream_split(parser, joined_iast)
                    if arm.startswith("upstream") and pred is not None:
                        pred = [canon(p) for p in pred]
                        if arm == "upstream+pausa":
                            pred = [_pausa_normalize(p) for p in pred]
            except Exception:
                pred = None
                agg[arm]["errs"] += 1
            if pred is None:
                agg[arm]["null"] += 1
                by_cat[cat][arm]["null"] += 1
                continue
            pred = [canon(p) for p in pred]
            ok = pred == gold_parts
            okf = bool(pred) and pred[0] == gold_parts[0]
            agg[arm]["scored"] += 1
            agg[arm]["exact"] += ok
            agg[arm]["first"] += okf
            by_cat[cat][arm]["scored"] += 1
            by_cat[cat][arm]["exact"] += ok
            by_src[src][arm + "_exact"] += ok
            by_src[src][arm + "_first"] += okf
            if not ok and len(examples) < 25:
                examples.append({"source": src, "type": cat, "word_iast": joined_iast,
                                 "gold": gold_parts, f"pred_{arm}": pred, "arm": arm})

    out = {
        "when": "2026-10-27",
        "handoff": "H6841 (WHEEL9 item a)",
        "pattern": "WHEEL6/H6456 pilot_process_sanskrit_vs_rules.py — arms reused, no new splitter/scorer",
        "bench": {"dir": str(BENCH_DIR), "items_total": len(bench),
                  "items_scored": agg["upstream"]["scored"],
                  "excluded_no_single_junction": sum(v["excluded_space"] for v in by_src.values())},
        "rule_inventory_files": n_rule_files,
        "arms": {k: {**v, "exact_pct": round(100.0 * v["exact"] / v["scored"], 2) if v["scored"] else None,
                     "first_pct": round(100.0 * v["first"] / v["scored"], 2) if v["scored"] else None}
                 for k, v in agg.items()},
        "neuro_arm": "NOT RUN — ByT5-Sanskrit/CharSS HF checkpoints not hosted by harness; hosting = rework (declined per H6841 step-3 IF clause)",
        "runtime_seconds": round(time.perf_counter() - t_start, 1),
        "by_category": {k: {**v, **{f"exact_pct_{arm}": round(100.0 * v[arm]["exact"] / v[arm]["scored"], 2) if v[arm]["scored"] else None
                                     for arm in arms}}
                        for k, v in sorted(by_cat.items())},
        "by_source": {k: {**v, "exact_pct_upstream": round(100.0 * v["upstream_exact"] / v["scored"], 2) if v["scored"] else None}
                      for k, v in sorted(by_src.items())},
        "examples": examples,
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out["arms"], indent=2))
    print(f"written: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())