#!/usr/bin/env python
"""H3910 — stratified acceptance sample over the aligned-sense table.

Wave 2's acceptance pass needs a precision figure, and a flat random sample
would spend most of its cards on the easy majority (`ls` / `gloss` clean rows)
and measure the wrong thing. This selects a *stratified* sample over three
axes that are already known to matter, writes it as a reproducible artifact
(seed + this script regenerate it byte-for-byte), and prints the population
share of every stratum so the per-stratum rates can be weighted back to a
pooled figure later.

Axes:

  method      ls · gloss · gloss+ls · attrib · attrib+ls · attrib+gloss+ls
  score band  lo <0.40 · mid 0.40-0.69 · hi >=0.70
  shape       clean (every per-dictionary count <= 1) vs m2m (any count >= 2)

Census strata (taken WHOLE, never sampled) — small enough to enumerate, and
each is a stratum whose precision is least known:

  attrib+gloss+ls (2)  · attrib+ls (9)  · every m2m row (32)

The `attrib` channel is one-directional and shipped with a *named* false-positive
class rather than a measurement (H3862), so it is deliberately over-sampled far
above its population share; that is exactly why the pooled figure must be
re-weighted rather than read off the sample directly.

Reads  data/concordance/sense_alignment.tsv   (built by build_sense_alignment.py)
Writes data/concordance/sense_alignment_acceptance_sample.tsv
       data/concordance/sense_alignment_acceptance_strata.json

This script SELECTS. It does not judge, score or repair anything.
"""
import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "concordance" / "sense_alignment.tsv"
OUT_TSV = ROOT / "data" / "concordance" / "sense_alignment_acceptance_sample.tsv"
OUT_JSON = ROOT / "data" / "concordance" / "sense_alignment_acceptance_strata.json"

SEED = 3910
TARGET = 120

# strata taken whole rather than sampled, keyed by method
CENSUS_METHODS = {"attrib+ls", "attrib+gloss+ls"}
# every many-to-many row is a census stratum too, whatever its method
CENSUS_SHAPE = "m2m"
# the one-directional channel with a named, unmeasured false-positive class
OVERSAMPLE = {"attrib": 30}


def band(score):
    s = float(score)
    if s < 0.40:
        return "lo <0.40"
    if s < 0.70:
        return "mid 0.40-0.69"
    return "hi >=0.70"


def shape_class(shape):
    return "clean" if all(int(c) <= 1 for c in shape.split("-")) else "m2m"


def stratum_key(row):
    return (row["method"], band(row["score"]), shape_class(row["shape"]))


def allocate(strata, target, seed):
    """Return {stratum: n_to_draw}. Census strata take everything; the
    oversampled `attrib` strata take their declared budget; the remainder is
    spread over the rest proportional to sqrt(N) with a floor of 3, which
    keeps the small clean strata representable without letting the 640-row
    majority stratum eat the budget."""
    take = {}
    rest = {}
    for key, rows in strata.items():
        method, _, shp = key
        if method in CENSUS_METHODS or shp == CENSUS_SHAPE:
            take[key] = len(rows)
        else:
            rest[key] = rows

    for method, budget in OVERSAMPLE.items():
        keys = [k for k in rest if k[0] == method]
        pool = sum(len(rest[k]) for k in keys)
        if not pool:
            continue
        # proportional inside the oversampled channel, floor 1, never over-draw
        for k in keys:
            n = max(1, round(budget * len(rest[k]) / pool))
            take[k] = min(n, len(rest[k]))
        for k in keys:
            del rest[k]

    remaining = target - sum(take.values())
    if remaining > 0 and rest:
        weights = {k: len(v) ** 0.5 for k, v in rest.items()}
        total = sum(weights.values())
        raw = {k: remaining * w / total for k, w in weights.items()}
        for k in rest:
            take[k] = min(len(rest[k]), max(3, int(raw[k])))
        # trim/extend deterministically to land on `remaining`
        drift = sum(take[k] for k in rest) - remaining
        order = sorted(rest, key=lambda k: (-len(rest[k]), k))
        i = 0
        while drift != 0 and i < 10_000:
            k = order[i % len(order)]
            if drift > 0 and take[k] > 3:
                take[k] -= 1
                drift -= 1
            elif drift < 0 and take[k] < len(rest[k]):
                take[k] += 1
                drift += 1
            i += 1
    else:
        for k, v in rest.items():
            take[k] = min(len(v), 3)
    return take


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--target", type=int, default=TARGET)
    ap.add_argument("--src", type=Path, default=SRC)
    args = ap.parse_args()

    with args.src.open(encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh, delimiter="\t") if r["method"] != "singleton"]
    population = len(rows)

    strata = defaultdict(list)
    for r in rows:
        strata[stratum_key(r)].append(r)
    # deterministic stratum iteration order and deterministic row order inside
    strata = {k: sorted(v, key=lambda r: r["group_id"]) for k, v in sorted(strata.items())}

    take = allocate(strata, args.target, args.seed)

    rng = random.Random(args.seed)
    picked = []
    meta = []
    for key in strata:
        pool = strata[key]
        n = take.get(key, 0)
        chosen = pool if n >= len(pool) else rng.sample(pool, n)
        chosen = sorted(chosen, key=lambda r: r["group_id"])
        census = n >= len(pool)
        for r in chosen:
            row = dict(r)
            row["stratum"] = "|".join(key)
            row["stratum_census"] = "yes" if census else "no"
            row["stratum_population"] = len(pool)
            row["population_share"] = f"{len(pool) / population:.6f}"
            row["sample_weight"] = f"{(len(pool) / population) / (len(chosen) / args.target):.4f}"
            picked.append(row)
        meta.append(
            {
                "stratum": "|".join(key),
                "method": key[0],
                "score_band": key[1],
                "shape": key[2],
                "population": len(pool),
                "population_share": round(len(pool) / population, 6),
                "sampled": len(chosen),
                "census": census,
            }
        )

    picked.sort(key=lambda r: (r["stratum"], r["group_id"]))
    fields = list(rows[0].keys()) + [
        "stratum",
        "stratum_census",
        "stratum_population",
        "population_share",
        "sample_weight",
    ]
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_TSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(picked)

    payload = {
        "seed": args.seed,
        "target": args.target,
        "population": population,
        "sampled": len(picked),
        "source": str(args.src.relative_to(ROOT)),
        "census_methods": sorted(CENSUS_METHODS),
        "census_shape": CENSUS_SHAPE,
        "oversample": OVERSAMPLE,
        "strata": meta,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"population (aligned rows): {population}")
    print(f"sampled:                   {len(picked)}  (seed {args.seed})")
    print()
    print(f"{'stratum':46s} {'pop':>5s} {'share':>7s} {'n':>4s}  census")
    for m in sorted(meta, key=lambda m: (-m["population"], m["stratum"])):
        print(
            f"{m['stratum']:46s} {m['population']:5d} {m['population_share']*100:6.2f}% "
            f"{m['sampled']:4d}  {'CENSUS' if m['census'] else ''}"
        )
    print()
    print(f"wrote {OUT_TSV.relative_to(ROOT)}")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    by_method = Counter(r["method"] for r in picked)
    print("by method:", dict(sorted(by_method.items())))


if __name__ == "__main__":
    main()
