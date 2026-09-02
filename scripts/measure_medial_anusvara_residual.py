#!/usr/bin/env python
"""How many give-back rows are still spelling twins, one position inward?

The sanskrit-util 0.11.0 fix collided WORD-FINAL anusvāra with word-final `m`
(`rasaṃ == rasam`). It left the medial case alone on purpose: medial anusvāra folds
to `n`, so `saṃskṛta == sanskṛta` keeps working. But before a labial (`p b m`) a
medial anusvāra IS phonetically /m/, and there the same asymmetry survives —
`vaiśaṃpāyana` keys as `vaiśanpāyana` while `vaiśampāyana` keys as itself, so one
name spelled two ways never meets.

The load-bearing measurement is over the **slot-conflict** class, because that is the
only class whose rows are handed to a human: a slot-conflict says "corpus and generator
disagree about this cell". When the two forms are identical after re-spelling medial
anusvāra-before-labial as `m`, there is no disagreement to adjudicate — it is a spelling
difference, and the row must not reach a review sheet (MG 17-08-2026: no human vote for
machine-resolvable verdicts).

The lemma-level count is reported alongside as context: candidates whose own lemma they
collapse into once refolded, i.e. rows that would leave A¬G entirely under a fixed key.
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT.parent / "GitHub" / "sanskrit-util" / "py"))
import sanskrit_util as su  # noqa: E402

TRIAGED = ROOT / "data" / "concordance" / "morph_giveback_triaged.tsv"
MEDIAL_LABIAL = re.compile("[ṃṁ](?=[pbm])")


def refold_key(s):
    """Key the string as if medial anusvāra-before-labial were spelled `m`."""
    return su.form_key(MEDIAL_LABIAL.sub("m", s))


def main():
    rows = list(csv.DictReader(TRIAGED.open(encoding="utf-8"), delimiter="\t"))
    conflicts = [r for r in rows if r["verdict"] == "slot-conflict"]

    twins = [r for r in conflicts
             if MEDIAL_LABIAL.search(r["attested_form"])
             and refold_key(r["attested_form"]) == refold_key(r["generator_has"])]
    tw_weight = sum(int(r["evidence_count"]) for r in twins)
    sc_weight = sum(int(r["evidence_count"]) for r in conflicts)

    lemma_twins = [r for r in rows
                   if MEDIAL_LABIAL.search(r["attested_form"])
                   and refold_key(r["attested_form"]) == refold_key(r["dcs_lemma"])]

    print("triaged rows                       : %s" % f"{len(rows):,}")
    print("slot-conflicts (the human class)   : %s" % f"{len(conflicts):,}")
    print("of those, medial-labial twins      : %s (%.2f%% of the class; %.2f%% by weight)"
          % (f"{len(twins):,}", 100.0 * len(twins) / len(conflicts),
             100.0 * tw_weight / sc_weight))
    print("candidates collapsing into their own lemma once refolded: %s"
          % f"{len(lemma_twins):,}")
    print()
    print("top twins (corpus form vs what the generator already emits):")
    for r in sorted(twins, key=lambda x: -int(x["evidence_count"]))[:12]:
        print("   %-22s vs %-22s %7s×"
              % (r["attested_form"], r["generator_has"],
                 f'{int(r["evidence_count"]):,}'))


if __name__ == "__main__":
    main()
