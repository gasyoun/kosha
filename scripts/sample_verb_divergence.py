"""sample_verb_divergence.py — draw the hand-adjudication sample from the E1 verb diff.

H185-C measured the Cologne-vs-vidyut verb agreement and H855 made it
interpretable with the dhātu-identity crosswalk (12.68 % → 70.24 %).  What
neither pass produced is the thing that turns the surviving 11,056 `DIFF_conflict`
cells from a number into a finding: a **hand-adjudicated, class-weighted sample**
saying *what kind* of disagreement each one is.  This script draws that sample.

It reads the divergence JSON that
[`compare_vidyut_verbs.py`](compare_vidyut_verbs.py) already writes — run that
with a high `--examples` so the per-class lists are not truncated — and emits a
seeded, stratified TSV for adjudication.  It computes nothing itself: any number
in the sample came from the comparison script, not from a second implementation.

Usage:
    python scripts/compare_vidyut_verbs.py --examples 20000 --out <dir>
    python scripts/sample_verb_divergence.py --in <dir>/e1_verbs_divergence.json
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Weighted toward DIFF_conflict: that is the class the report calls "true
# divergence", and the only one whose content is still unknown.  The cosmetic
# and superset classes get a few rows each purely as a control - if they turn
# out NOT to be cosmetic, the classification above them is wrong.
QUOTA = {
    "DIFF_conflict": 30,
    "COLOGNE_ONLY": 8,
    "DIFF_vidyut_superset": 4,
    "DIFF_final_stop": 3,
    "DIFF_cologne_superset": 3,
    "VIDYUT_ONLY": 4,
}
COLS = ["klass", "root", "model", "cell", "cologne", "vidyut"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", default=os.path.join("data", "e1",
                                                  "verb_divergence_adjudication.tsv"))
    ap.add_argument("--seed", type=int, default=3166)
    args = ap.parse_args()

    with open(args.src, encoding="utf-8") as fh:
        payload = json.load(fh)
    examples = payload["examples"]

    rng = random.Random(args.seed)
    rows = []
    drawn = collections.Counter()
    for klass, n in QUOTA.items():
        pool = examples.get(klass, [])
        take = pool if len(pool) <= n else rng.sample(pool, n)
        drawn[klass] = len(take)
        for r in sorted(take, key=lambda x: (x["root"], x["cell"])):
            rows.append({
                "klass": klass, "root": r["root"], "model": r["model"],
                "cell": r["cell"],
                "cologne": ",".join(r.get("cologne") or []),
                "vidyut": ",".join(r.get("vidyut") or []),
            })

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(COLS) + "\n")
        for r in rows:
            fh.write("\t".join(r[c] for c in COLS) + "\n")

    print(f"sampled {len(rows)} rows (seed {args.seed}) -> {args.out}")
    for klass, n in QUOTA.items():
        print(f"  {klass}: drew {drawn[klass]} of {len(examples.get(klass, []))} available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
