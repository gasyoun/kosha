#!/usr/bin/env python
"""H882 / Phase 0 — sandhi split-method A/B/C comparison harness (skeleton).

The roadmap's central experiment: for a text with NO hand-annotated sandhi, three
ways to obtain the word-split that the junction-rule inducer needs, compared on
the SAME text —

  A  DCS gold splits      — read `Unsandhied=` straight from DCS CoNLL-U. The
                            ceiling: human-verified. IMPLEMENTED (dcs_sandhi_induce).
  B  Vidyut cheda         — segment raw text with the offline vidyut-cheda model
                            (vidyut-data/cheda/model.msgpack), then induce. STUB.
  C  Neural (DharmaMitra) — API segmenter, higher recall on hard junctions. STUB.

Because A uses gold splits, it is the reference; B and C are scored *against A*
on the same text (junction-level agreement + rule-inventory P/R/F1). Separately,
A's rule NOTATION is validated against the Bhagavadgītā hand table
(data/gita/gita_sandhi.tsv) — the only place where a human independently wrote
the same `X Y → Z` strings — to confirm the inducer speaks the same language.

This file wires A and the notation-validation, and lays out B/C as explicit
NotImplemented stubs with the exact assets/commands a Phase-1 pass will use.

Usage:
  python scripts/compare_sandhi_methods.py --text "Aṣṭāvakragīta"
  python scripts/compare_sandhi_methods.py --text Hitopadeśa --methods A
"""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import dcs_sandhi_induce as ind  # noqa: E402

GITA_GOLD = ROOT / "data" / "gita" / "gita_sandhi.tsv"
VIDYUT_CHEDA = Path("C:/Users/user/Documents/GitHub/vidyut-data/cheda/model.msgpack")


# --- method A: DCS gold splits (implemented) --------------------------------
def method_A(text, dcs_root):
    """Induce rules from DCS gold Unsandhied splits (mode 1 edge + mode 2 MWT
    coalescence). Returns Counter(rule -> n)."""
    files = sorted((Path(dcs_root) / text).glob("*.conllu"))
    counts, _examples, _st, _flagged, _dbg = ind.induce_from_files(files)
    return counts


# --- method B: Vidyut cheda segmenter (STUB) --------------------------------
def method_B(text, dcs_root):
    """PHASE 1. Reconstruct the raw (sandhied) text from DCS `## text:` / FORM,
    segment it with vidyut-cheda, then feed each predicted split pair through
    ind.induce_rule() exactly as method A does — so only the SPLIT source
    differs, isolating splitter quality.

    Assets on disk:  %s
    Binding options: (a) `vidyut` Python pkg if installed (`pip show vidyut`);
                     (b) shell out to a vidyut-cheda CLI; (c) PyO3/subprocess.
    The reconstructed surface string per sentence is the space-join of FORM
    tokens (already available via ind.read_sentences).
    """ % VIDYUT_CHEDA
    raise NotImplementedError(
        "method B (vidyut-cheda) is a Phase-1 task — model at %s" % VIDYUT_CHEDA)


# --- method C: neural DharmaMitra segmenter (STUB) --------------------------
def method_C(text, dcs_root):
    """PHASE 1. Segment via the DharmaMitra neural API (API-only, not vendored —
    see kosha/data/manifest/external_tools.json row `dharmamitra`). Same
    induce_rule() tail. Gate behind an explicit --allow-network flag and a
    cost/rate note; cache responses under data/sandhi/_cache/."""
    raise NotImplementedError(
        "method C (neural) is a Phase-1 task — DharmaMitra API, see external_tools.json")


# --- scoring ----------------------------------------------------------------
def load_rule_set(tsv_path):
    if not tsv_path.exists():
        return {}
    out = {}
    for row in csv.DictReader(open(tsv_path, encoding="utf-8"), delimiter="\t"):
        out[row["rule"]] = int(row["count"])
    return out


def pr_f1(ref_rules, hyp_rules):
    """Rule-inventory precision/recall/F1 (set overlap on rule strings)."""
    ref, hyp = set(ref_rules), set(hyp_rules)
    tp = len(ref & hyp)
    prec = tp / len(hyp) if hyp else 0.0
    rec = tp / len(ref) if ref else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1, tp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--dcs-root", default=str(ind.DEFAULT_DCS))
    ap.add_argument("--methods", default="A", help="subset of ABC, e.g. 'A' or 'AB'")
    args = ap.parse_args()

    results = {}
    for m in args.methods.upper():
        fn = {"A": method_A, "B": method_B, "C": method_C}[m]
        try:
            results[m] = fn(args.text, args.dcs_root)
            print("method %s: %d distinct rules over %d junctions"
                  % (m, len(results[m]), sum(results[m].values())))
        except NotImplementedError as e:
            print("method %s: SKIPPED — %s" % (m, e))

    # B/C scored against A (the gold-split ceiling) on the same text
    if "A" in results:
        for m in ("B", "C"):
            if m in results:
                p, r, f, tp = pr_f1(results["A"], results[m])
                print("  %s vs A: P=%.3f R=%.3f F1=%.3f (%d shared rules)" % (m, p, r, f, tp))

    # validate method-A notation against the Gītā hand table
    gita = load_rule_set(GITA_GOLD)
    if "A" in results and gita:
        p, r, f, tp = pr_f1(gita, results["A"])
        print("\nnotation check — method A rules vs Gītā hand table (%s):" % GITA_GOLD.name)
        print("  shared rule strings: %d   (A covers %.0f%% of Gītā's %d hand rules)"
              % (tp, 100.0 * tp / len(gita), len(gita)))
        shared = sorted(set(gita) & set(results["A"]),
                        key=lambda k: -gita[k])[:10]
        print("  top shared:", ", ".join(shared))
        only_gita = sorted(set(gita) - set(results["A"]), key=lambda k: -gita[k])[:8]
        if only_gita:
            print("  in Gītā not (yet) here:", ", ".join(only_gita))


if __name__ == "__main__":
    main()
