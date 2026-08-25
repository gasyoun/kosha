"""measure_passive_bare_root.py — how much of the "genuine conflict" is still bare-root.

The probe (`probe_passive_conflict.py`) showed the malformed passives survive
whether vidyut is seeded with the H855 crosswalk's aupadeśika or with Cologne's
bare root - because for most roots the crosswalk *chose* the bare root (its
`direct` and `bare` resolution paths).  That is safe for the active lane, which
is what H855 was tuned on, and unsafe for the passive, where vidyut consumes the
unmarked final consonant.

This script measures the consequence over the population: of the surviving
`DIFF_conflict` cells, what share belongs to a root whose seed is still the bare
root, split by voice.  A high passive share means the 11,056 "true divergence"
figure is, in part, the same class of artifact H855 diagnosed one level up.

Usage:
    python scripts/compare_vidyut_verbs.py --examples 20000 --out <dir>
    python scripts/measure_passive_bare_root.py --in <dir>/e1_verbs_divergence.json
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

from compare_vidyut_verbs import load_crosswalk  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--crosswalk",
                    default=os.path.join(REPO, "data", "e1", "dhatu_crosswalk.json"))
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    cross = load_crosswalk(args.crosswalk)
    with open(args.crosswalk, encoding="utf-8") as fh:
        raw = json.load(fh).get("crosswalk", {})

    via = collections.Counter(e.get("via", "?") for e in raw.values())
    seed_is_bare = sum(1 for k, e in raw.items()
                       if (e.get("aupadeshika") or "") == k.split("|", 1)[-1])
    print(f"crosswalk entries: {len(raw)}  resolution paths: {dict(via)}")
    print(f"entries whose seed IS the bare Cologne root: {seed_is_bare} "
          f"({100.0 * seed_is_bare / len(raw):.1f} %)")

    with open(args.src, encoding="utf-8") as fh:
        conflicts = json.load(fh)["examples"]["DIFF_conflict"]

    def bare_seeded(row: dict) -> bool:
        model = row["model"]
        # a v_p row is seeded from the root's active model; the comparison script
        # borrows it, so test every active model this root could have supplied
        keys = ([f"{model}|{row['root']}"] if model != "v_p"
                else [f"v_{g}|{row['root']}" for g in (1, 4, 6, 10)])
        seeds = [cross.get(k) for k in keys if k in cross]
        if not seeds:
            return True  # unresolved -> the script falls back to the bare root
        return any(s == row["root"] for s in seeds)

    by_voice: dict = collections.defaultdict(lambda: [0, 0])
    for row in conflicts:
        voice = row["cell"].split(".")[0]
        by_voice[voice][0] += 1
        if bare_seeded(row):
            by_voice[voice][1] += 1

    total = sum(v[0] for v in by_voice.values())
    bare = sum(v[1] for v in by_voice.values())
    print(f"\nDIFF_conflict cells: {total}; still bare-root-seeded: {bare} "
          f"({100.0 * bare / total:.1f} %)")
    report = {"crosswalk_entries": len(raw), "via": dict(via),
              "seed_is_bare_root": seed_is_bare,
              "conflict_cells": total, "conflict_bare_seeded": bare,
              "by_voice": {}}
    for voice, (n, b) in sorted(by_voice.items(), key=lambda kv: -kv[1][0]):
        print(f"  {voice:8} {n:6} cells · {b:6} bare-seeded ({100.0 * b / n:.1f} %)")
        report["by_voice"][voice] = {"cells": n, "bare_seeded": b}

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
