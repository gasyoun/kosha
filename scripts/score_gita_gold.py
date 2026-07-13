#!/usr/bin/env python
"""Gītā gold scoring — sandhi roadmap item 5 (H894 follow-on).

The truest test of the DCS sandhi inducer (method A): run it on the **actual
Bhagavadgītā** — not a small pilot proxy — and score against the hand-annotated
`data/gita/gita_sandhi.tsv` (161 rules the human wrote from the same text). Small
pilots (Aṣṭāvakragīta) under-attest the rare rules, so their coverage (~61 %)
understates the inducer; on the Gītā itself every gold rule is actually present.

DCS stores the Gītā inside the Mahābhārata as book-6 chapters relabelled
`MBh, 6, BhaGī 1…18` (the numeric MBh-6 sequence skips 23–40) — 18 `.conllu`
files, one per adhyāya, found by `*BhaGī*.conllu`.

Reports, against the 161 gold rules:
  * rule-string coverage  |shared| / |gold|
  * **frequency-mass coverage** — Σ gold_count over shared rules / Σ gold_count
    (the roadmap exit metric: "≥90 % of the Gītā hand rules by frequency mass")
  * precision / recall / F1 on rule strings
  * the top gold rules method A still misses, by frequency mass

Usage: python scripts/score_gita_gold.py
"""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import dcs_sandhi_induce as ind  # noqa: E402

GITA_GOLD = ROOT / "data" / "gita" / "gita_sandhi.tsv"
MBH = Path("C:/Users/user/Documents/GitHub/dcs-conllu/files/Mahābhārata")


def load_gold(path):
    gold = {}
    for row in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"):
        gold[row["rule"]] = int(row["count"])
    return gold


def main():
    files = sorted(MBH.glob("*BhaGī*.conllu"))
    if not files:
        sys.exit("no BhaGī files found under %s" % MBH)
    counts, _ex, st, _fl, _dbg = ind.induce_from_files(files)

    gold = load_gold(GITA_GOLD)
    gold_total = sum(gold.values())
    shared = set(gold) & set(counts)
    shared_mass = sum(gold[r] for r in shared)

    # rule-string P/R/F1
    tp = len(shared)
    prec = tp / len(counts) if counts else 0.0
    rec = tp / len(gold) if gold else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0

    print("=== Gītā gold scoring — method A on the DCS Bhagavadgītā ===")
    print("BhaGī files:            %d (adhyāyas)" % len(files))
    print("induced events:         %d  (edge %d · MWT %d · MWT-edge %d)"
          % (sum(counts.values()), st["junctions"] - st["no_sandhi"],
             st["mwt_boundaries"] - st["mwt_no_sandhi"] - st["mwt_no_gold"],
             st["mwt_edges"] - st["mwt_no_edge"]))
    print("induced distinct rules: %d" % len(counts))
    print("gold hand rules:        %d  (%d junction-attestations)" % (len(gold), gold_total))
    print()
    print("rule-string coverage:   %d / %d = %.1f%%" % (tp, len(gold), 100.0 * tp / len(gold)))
    print("FREQUENCY-MASS coverage: %d / %d = %.1f%%  (roadmap exit: ≥90%%)"
          % (shared_mass, gold_total, 100.0 * shared_mass / gold_total))
    print("precision %.3f · recall %.3f · F1 %.3f" % (prec, rec, f1))
    print()
    missing = sorted((set(gold) - set(counts)), key=lambda r: -gold[r])
    miss_mass = sum(gold[r] for r in missing)
    print("top gold rules still MISSED (by mass; %d rules = %d attest = %.1f%% of gold mass):"
          % (len(missing), miss_mass, 100.0 * miss_mass / gold_total))
    for r in missing[:15]:
        print("  %-16s gold count %4d  (%.1f%%)" % (r, gold[r], 100.0 * gold[r] / gold_total))


if __name__ == "__main__":
    main()
