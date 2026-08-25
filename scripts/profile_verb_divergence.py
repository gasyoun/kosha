"""profile_verb_divergence.py — where the E1 verb divergence actually concentrates.

The hand-adjudication sample (`sample_verb_divergence.py`, seed 3166) showed the
surviving `DIFF_conflict` cells are not spread evenly across the paradigm: they
pile up in one model and one shape.  This script turns that impression into
population numbers, over every cell the comparison emitted - not the sample.

It reads the divergence JSON from
[`compare_vidyut_verbs.py`](compare_vidyut_verbs.py) run with a high
`--examples` (so the per-class lists are the full population, not the first 50),
and reports, per class: the model split, the voice split, and - for the conflict
class - whether vidyut's form is shorter than Cologne's, which is the signature
of the two engines resolving the root differently rather than inflecting it
differently.

Usage:
    python scripts/compare_vidyut_verbs.py --examples 20000 --out <dir>
    python scripts/profile_verb_divergence.py --in <dir>/e1_verbs_divergence.json
"""
from __future__ import annotations

import argparse
import collections
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")


def pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:.1f} %" if d else "n/a"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    with open(args.src, encoding="utf-8") as fh:
        examples = json.load(fh)["examples"]

    report: dict = {}
    for klass, rows in sorted(examples.items()):
        n = len(rows)
        models = collections.Counter(r["model"] for r in rows)
        voices = collections.Counter(r["cell"].split(".")[0] for r in rows)
        roots = collections.Counter(r["root"] for r in rows)
        entry = {
            "cells": n,
            "distinct_roots": len(roots),
            "top_models": models.most_common(4),
            "voices": voices.most_common(),
        }
        if klass == "DIFF_conflict":
            shorter = same = longer = 0
            for r in rows:
                cw = max((len(x) for x in r.get("cologne") or []), default=0)
                vw = max((len(x) for x in r.get("vidyut") or []), default=0)
                if vw < cw:
                    shorter += 1
                elif vw > cw:
                    longer += 1
                else:
                    same += 1
            entry["vidyut_form_vs_cologne"] = {
                "shorter": shorter, "equal_length": same, "longer": longer,
                "shorter_pct": round(100.0 * shorter / n, 1) if n else 0.0,
            }
        report[klass] = entry

        print(f"\n{klass}: {n} cells over {len(roots)} roots")
        print("  models:", ", ".join(f"{m} {c} ({pct(c, n)})" for m, c in models.most_common(4)))
        print("  voices:", ", ".join(f"{v} {c} ({pct(c, n)})" for v, c in voices.most_common()))
        if "vidyut_form_vs_cologne" in entry:
            s = entry["vidyut_form_vs_cologne"]
            print(f"  vidyut form shorter than Cologne: {s['shorter']} ({s['shorter_pct']} %)"
                  f" · equal {s['equal_length']} · longer {s['longer']}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
