#!/usr/bin/env python
"""Corpus-wide sandhi sweep — roadmap Phase 2 (H899).

Runs the validated DCS sandhi inducer (method A, 96.3 % Gītā-gold frequency-mass
coverage — see scripts/score_gita_gold.py) across a curated pedagogical text set,
in learner-difficulty order, and builds:

  * per-text  data/sandhi/<id>_sandhi.tsv     (== gita_sandhi.tsv schema)
  * merged    data/sandhi/corpus_sandhi.tsv   global frequency ranks across texts
      columns: rule · category · global_count · global_pct · n_texts ·
               top_texts · examples

The merged table is the pedagogy backbone: "learn these N junctions to read X %
of the corpus." Rules are ranked by total attestation; `top_texts` shows where
each is most frequent.

The Bhagavadgītā is not a standalone DCS text — it lives inside the Mahābhārata
as book-6 chapters relabelled `MBh, 6, BhaGī 1…18` — so texts are specified by an
explicit file glob, not just a directory.

Public/MIT, credit Dr. Mārcis Gasūns. Usage: python scripts/build_corpus_sandhi.py
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import dcs_sandhi_induce as ind  # noqa: E402

DCS = Path("C:/Users/user/Documents/GitHub/dcs-conllu/files")
OUT = ROOT / "data" / "sandhi"

# curated pedagogical set, learner-difficulty order (dir, glob, id, label)
TEXTS = [
    ("Hitopadeśa", "*.conllu", "hitopadesa", "Hitopadeśa"),
    ("Vetālapañcaviṃśatikā", "*.conllu", "vetalapancavimsatika", "Vetālapañcaviṃśatikā"),
    ("Śukasaptati", "*.conllu", "sukasaptati", "Śukasaptati"),
    ("Amaruśataka", "*.conllu", "amarusataka", "Amaruśataka"),
    ("Aṣṭāvakragīta", "*.conllu", "astavakragita", "Aṣṭāvakragīta"),
    ("Mahābhārata", "*BhaGī*.conllu", "bhagavadgita", "Bhagavadgītā"),
    ("Gītagovinda", "*.conllu", "gitagovinda", "Gītagovinda"),
    ("Kathāsaritsāgara", "*.conllu", "kathasaritsagara", "Kathāsaritsāgara"),
]


def write_per_text(tsv, counts, examples):
    total = sum(counts.values())
    with open(tsv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["rule", "category", "count", "pct", "examples"])
        for rule, n in counts.most_common():
            w.writerow([rule, ind.categorise(rule), n,
                        round(100.0 * n / total, 2) if total else 0,
                        " · ".join(examples[rule])])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    global_count = Counter()
    per_text_count = defaultdict(dict)   # rule -> {text_id: n}
    global_ex = defaultdict(list)
    summary = []

    for d, glob, tid, label in TEXTS:
        files = sorted((DCS / d).glob(glob))
        if not files:
            print("skip (no files): %s" % label)
            continue
        counts, examples, st, _fl, _dbg = ind.induce_from_files(files)
        write_per_text(OUT / ("%s_sandhi.tsv" % tid), counts, examples)
        total = sum(counts.values())
        summary.append((label, len(files), total, len(counts)))
        for rule, n in counts.items():
            global_count[rule] += n
            per_text_count[rule][label] = n
            if len(global_ex[rule]) < 4 and examples.get(rule):
                global_ex[rule].append(examples[rule][0])
        print("  %-24s %3d files · %5d events · %4d rules" % (label, len(files), total, len(counts)))

    gtotal = sum(global_count.values())
    merged = OUT / "corpus_sandhi.tsv"
    with open(merged, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["rule", "category", "global_count", "global_pct", "n_texts",
                    "top_texts", "examples"])
        for rule, n in global_count.most_common():
            tops = sorted(per_text_count[rule].items(), key=lambda kv: -kv[1])[:3]
            top_texts = ", ".join("%s(%d)" % (t, c) for t, c in tops)
            w.writerow([rule, ind.categorise(rule), n,
                        round(100.0 * n / gtotal, 2) if gtotal else 0,
                        len(per_text_count[rule]), top_texts,
                        " · ".join(global_ex[rule])])

    cat = Counter()
    for rule, n in global_count.items():
        cat[ind.categorise(rule)] += n
    cum = 0
    top_for_80 = 0
    for _rule, n in global_count.most_common():
        cum += n
        top_for_80 += 1
        if cum >= 0.8 * gtotal:
            break

    print("\n=== corpus sandhi merged ===")
    print("texts swept:   %d" % len(summary))
    print("total events:  %d" % gtotal)
    print("distinct rules: %d" % len(global_count))
    print("categories:", dict(cat.most_common()))
    print("pedagogy: the top %d rules cover 80%% of all corpus sandhi occurrences" % top_for_80)
    print("wrote", merged)
    print("\ntop 15 corpus rules:")
    for rule, n in global_count.most_common(15):
        print("  %-16s %-18s %5d  %5.1f%%  (%d texts)"
              % (rule, ind.categorise(rule), n, 100.0 * n / gtotal, len(per_text_count[rule])))


if __name__ == "__main__":
    main()
