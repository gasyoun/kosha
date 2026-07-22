#!/usr/bin/env python
"""Resolve PWG Mahābhārata <ls> loci (Böhtlingk-Roth continuous per-parvan
verse numbering, e.g. `MBH. 12,3630`) to a Nīlakaṇṭha-vulgate address
(parvan.adhyāya.śloka) — REUSING the csl-atlas f8 fitted-index crosswalk.

This is the prior art the H1455 wave-1 spike WRONGLY concluded didn't exist.
The org solved PWG-continuous → vulgate for all 18 parvans (csl-atlas
`scripts/forensic/f8_mbh_resolve.py`, H610/H761 — held-out MW gate 55.2% within
±3, DEAD_ENDS §8b retracted). We consume its committed crosswalk
`data/forensic/mbh_vulgate_concordance.csv` (numbers only, publish-safe); the
vulgate verse TEXT stays gitignored in CommentaryStrategies.

Crosswalk columns: parvan, adhyaya, shloka, continuous_C, **calibrated_N**,
adhyaya_offset, adhyaya_n_anchors. `calibrated_N` is the per-parvan continuous
verse count fitted onto the PWG/MW CITATION space — so PWG `MBH. P,V` resolves
by finding the row with parvan=P and calibrated_N nearest V.

Honest limit (kept explicit downstream): this resolves PWG → **vulgate**. DCS's
Mahābhārata is the **BORI critical edition**, a different recension whose
adhyāya/śloka numbering drifts from the vulgate (~±1 adhyāya) — so a DCS
attestation match through this crosswalk is an adhyāya-level *corroboration*,
never an exact-verse identity (the residual the wave-1 report should have named
instead of calling the whole thing infeasible).
"""
import bisect
import csv
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
LOCAL = ROOT / "data" / "concordance" / "mbh_vulgate_concordance.csv"
CSL_ATLAS = GH / "csl-atlas" / "data" / "forensic" / "mbh_vulgate_concordance.csv"

FIT_TOLERANCE = 3   # csl-atlas held-out gate is "within ±3" verses — beyond that, drop.


class MBhVulgate:
    """Per-parvan resolver PWG (parvan, verse) -> vulgate (adhyaya, shloka)."""

    def __init__(self, path=None):
        if path is None:
            path = LOCAL if LOCAL.exists() else CSL_ATLAS
        self.ok = Path(path).exists()
        # parvan -> (sorted calibrated_N list, parallel [(adhyaya, shloka, delta)])
        self._by_parvan = {}
        if not self.ok:
            return
        rows = {}
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    p = int(r["parvan"]); n = int(r["calibrated_N"])
                    a = int(r["adhyaya"]); s = int(r["shloka"])
                except (ValueError, KeyError):
                    continue
                rows.setdefault(p, []).append((n, a, s))
        for p, lst in rows.items():
            lst.sort()
            self._by_parvan[p] = ([x[0] for x in lst], [(x[1], x[2]) for x in lst])

    def resolve(self, parvan, verse):
        """-> dict(adhyaya, shloka, delta, exact) or None.
        Finds the vulgate row whose calibrated_N is nearest `verse` within
        ±FIT_TOLERANCE for that parvan."""
        pk = self._by_parvan.get(parvan)
        if not pk:
            return None
        keys, vals = pk
        i = bisect.bisect_left(keys, verse)
        best = None
        for j in (i - 1, i, i + 1):
            if 0 <= j < len(keys):
                d = abs(keys[j] - verse)
                if best is None or d < best[0]:
                    best = (d, vals[j])
        if best is None or best[0] > FIT_TOLERANCE:
            return None
        (a, s) = best[1]
        return {"adhyaya": a, "shloka": s, "delta": best[0], "exact": best[0] == 0,
                "vulgate": "%d.%d.%d" % (parvan, a, s)}


if __name__ == "__main__":
    # smoke: resolve the nAgadanta tusk-sense locus MBH 12,3630
    mv = MBhVulgate()
    print("crosswalk loaded:", mv.ok, "parvans:", len(mv._by_parvan))
    for pv in ((12, 3630), (7, 9283), (1, 4405)):
        print("PWG MBH %d,%d ->" % pv, mv.resolve(*pv))
