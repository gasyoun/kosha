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

H3975 (06-09-2026) moved that fold into the library (sanskrit-util 0.12.0) and rebuilt the
A3 chain, so this script flipped role: on a fixed library over freshly rebuilt artifacts the
answer must be ZERO, and it is now the standing REGRESSION CHECK for that. A non-zero count
under >=0.12.0 means the artifacts predate the fix — the baselines below are what the last
pre-fix run measured, kept so the check reports a delta rather than a bare number.
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")
# The sibling checkout is ROOT's *parent* (…/GitHub/kosha -> …/GitHub/sanskrit-util), the same
# hop concordance_core.py makes. This line used to append an extra "GitHub" segment, so the path
# never existed and the import fell through to whatever `sanskrit_util` happened to be installed
# — which is exactly how a measurement can silently be taken against a different key era than
# the one the repo checkout carries (H3975).
sys.path.insert(0, str(ROOT.parent / "sanskrit-util" / "py"))
import sanskrit_util as su  # noqa: E402

TRIAGED = ROOT / "data" / "concordance" / "morph_giveback_triaged.tsv"
MEDIAL_LABIAL = re.compile("[ṃṁ](?=[pbm])")
# Probed, never read off __version__: a consumer can import an installed copy that differs
# from the sibling checkout, which is precisely how a stale key era hides.
LIBRARY_HAS_LABIAL_FOLD = su.form_key("saṃbhavaḥ") == su.form_key("sambhavaḥ")
# What the last pre-fix run measured (02-09-2026 artifacts, sanskrit-util 0.11.0).
BASELINE = {"rows": 5588, "conflicts": 2521, "twins": 278, "lemma_twins": 90}


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

    def delta(now, was):
        return "%s (baseline %s, %+d)" % (f"{now:,}", f"{was:,}", now - was)

    print("library                            : sanskrit_util %s at %s"
          % (getattr(su, "__version__", "?"), su.__file__))
    print("  medial anusvara before a labial  : %s"
          % ("folds to m (>=0.12.0) — this run is a REGRESSION CHECK, expect 0 twins"
             if LIBRARY_HAS_LABIAL_FOLD else
             "still folds to n (<0.12.0) — this run is the original MEASUREMENT"))
    print()
    print("triaged rows                       : %s" % delta(len(rows), BASELINE["rows"]))
    print("slot-conflicts (the human class)   : %s"
          % delta(len(conflicts), BASELINE["conflicts"]))
    print("of those, medial-labial twins      : %s%s"
          % (delta(len(twins), BASELINE["twins"]),
             "" if not conflicts else
             " — %.2f%% of the class; %.2f%% by weight"
             % (100.0 * len(twins) / len(conflicts), 100.0 * tw_weight / sc_weight)))
    print("candidates collapsing into their own lemma once refolded: %s"
          % delta(len(lemma_twins), BASELINE["lemma_twins"]))
    print()
    if LIBRARY_HAS_LABIAL_FOLD and twins:
        print("FAIL: the library carries the fold but the artifacts still contain twins —")
        print("      morph_giveback_triaged.tsv predates the fix. Re-run "
              "scripts/rebuild_a3_chain.py.")
    elif LIBRARY_HAS_LABIAL_FOLD:
        print("PASS: no medial-labial twin survives in the human class.")
    if twins:
        print()
        print("top twins (corpus form vs what the generator already emits):")
        for r in sorted(twins, key=lambda x: -int(x["evidence_count"]))[:12]:
            print("   %-22s vs %-22s %7s×"
                  % (r["attested_form"], r["generator_has"],
                     f'{int(r["evidence_count"]):,}'))


if __name__ == "__main__":
    main()
