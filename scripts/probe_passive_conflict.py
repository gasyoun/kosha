"""probe_passive_conflict.py — is the passive conflict vidyut's, or the harness's?

`profile_verb_divergence.py` shows 55.8 % of the surviving `DIFF_conflict` cells
are passive and 66.9 % have vidyut's form shorter than Cologne's, with some of
the short forms plainly malformed (`yyante` where the passive of `yat` is
`yatyate`).  Two explanations survive that observation and they call for
opposite follow-ups:

  A. **vidyut derives it that way** from the correct aupadeśika dhātu - a real
     engine divergence to report upstream;
  B. **the harness hands vidyut a dhātu that is right for the active and wrong
     for the passive** - `compare_vidyut_verbs.py` gives a `v_p` row the dhātu
     resolved for the root's *active* model, because a passive row carries no
     gaṇa of its own.

This probe discriminates, reusing the comparison script's own helpers rather
than restating them: for each root it prints the crosswalk's aupadeśika, the
passive cell vidyut derives from it, and the passive vidyut derives from the
bare root (the pre-H855 fallback).  Where the bare root reproduces Cologne and
the crosswalk's aupadeśika does not, the cause is B - the crosswalk optimised
for the active and cost the passive.

Usage:
    python scripts/probe_passive_conflict.py --roots yat kam paR ruc pA
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from compare_vidyut_verbs import (GANA_OF_MODEL, load_crosswalk,  # noqa: E402
                                  upadesha, vidyut_verb_cell)
from vidyut.prakriya import Dhatu, Vyakarana  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+",
                    default=["yat", "kam", "paR", "ruc", "pA", "kzam"])
    ap.add_argument("--model", default="v_1", help="the active model whose gaṇa the passive borrows")
    ap.add_argument("--cell", default="pre.3.sg")
    args = ap.parse_args()

    cross = load_crosswalk(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "data", "e1", "dhatu_crosswalk.json"))
    v = Vyakarana()
    tense, person, number = args.cell.split(".")

    print(f"passive {args.cell}, gaṇa borrowed from {args.model}\n")
    print(f"{'root':10} {'aupadeśika':14} {'from crosswalk':28} {'from bare root':28}")
    for root in args.roots:
        up = upadesha(cross, root, args.model)
        gana = GANA_OF_MODEL[args.model]
        out = {}
        for label, seed in (("crosswalk", up), ("bare", root)):
            try:
                d = Dhatu.mula(seed, gana)
                out[label] = sorted(vidyut_verb_cell(v, d, "passive", tense, person, number))
            except Exception as exc:  # noqa: BLE001 - showing the failure IS the result
                out[label] = [f"<{type(exc).__name__}>"]
        same = " (same)" if out["crosswalk"] == out["bare"] else ""
        print(f"{root:10} {up:14} {','.join(out['crosswalk']) or '-':28} "
              f"{','.join(out['bare']) or '-':28}{same}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
