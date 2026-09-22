#!/usr/bin/env python
"""H5070 — freeze a selective-risk review deck over the scaled alignment table.

H4751 scaled the aligned-sense population (3,013 -> 7,009 rows) and H4745 then
extended it again with the MD channel (-> 7,087). The recorded coverage increase
and the reproduced judge kappa are NOT an error-versus-coverage curve for the
enlarged population: kappa measures whether a judge agrees with itself, not
whether an alignment is right, and both figures predate the current table.

This script SELECTS and FREEZES; it does not judge, score or repair anything.

What it freezes, before any card is read:

  1. the population identity  — sha256 of the source table, row count, the
     aligned/unaligned split and the failure taxonomy (the abstention side);
  2. the selection           — seed, per-stratum allocation, chosen group_ids;
  3. the gold separation     — every group_id already carried by the frozen
     H3910 (120-card) or H4751 W2 (153-card) acceptance artifacts is EXCLUDED,
     so newly adjudicated records can never be pooled with reused ones;
  4. one blind positive control — a synthetic high-score pair built from two
     unrelated lemmas, shuffled into the deck at a seeded position with its
     identity written to a separate key file the adjudicator does not open
     until the verdicts are recorded (a seeded confident wrong match).
     It carries the stratum metadata of the stratum it imitates. The deck TSV is
     still NOT a blind surface — its group_id can be looked up in the population —
     so adjudicators work from `render_selective_risk_deck.py` output only.
     The 20-09-2026 frozen deck predates this and reproduces only with
     --legacy-canary-metadata (its canary carried zero stratum metadata).

H5252 channel-stratified mode (additive; the default path is unchanged).
`--stratify-channel skd` replaces the method channel with "carries a skd gloss"
vs "does not", keeps the score band, and gives the named channel a fixed budget
(`--channel-budget`) spread across bands in proportion to stratum size. The rest
of the target goes to the complement, also proportionally. `--exclude-deck`
removes the group_ids of an earlier deck (the H5070 60) so no card is judged
twice. A small channel falls out of a general draw; this mode sizes it.

Strata: score band (lo <0.40 / mid 0.40-0.69 / hi >=0.70) x channel
(attrib* / gloss+ls / gloss / ls). Allocation is EQUAL across the three score
bands rather than proportional: a risk-coverage curve is read at its high end,
and a proportional draw would spend the budget on the low band. Population
shares are carried on every card so the pooled figure is re-weighted at scoring
time rather than read off the deck.

Reads  data/concordance/sense_alignment.tsv
       data/concordance/sense_alignment_acceptance_sample.tsv      (gold, excluded)
       data/concordance/sense_alignment_acceptance_sample_w2.tsv   (gold, excluded)
Writes data/concordance/selective_risk/review_deck.tsv
       data/concordance/selective_risk/population_freeze.json
       data/concordance/selective_risk/canary_key.json
"""
import argparse
import csv
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
CONC = ROOT / "data" / "concordance"
SRC = CONC / "sense_alignment.tsv"
GOLD = [CONC / "sense_alignment_acceptance_sample.tsv",
        CONC / "sense_alignment_acceptance_sample_w2.tsv"]
OUT = CONC / "selective_risk"

SEED = 5070
TARGET = 60           # the handoff's hard ceiling on newly adjudicated pairs
BANDS = ["lo <0.40", "mid 0.40-0.69", "hi >=0.70"]
DICTS = ["pwg", "mw", "apte", "md", "skd", "vcp"]


def band(score):
    s = float(score)
    return BANDS[0] if s < 0.40 else BANDS[1] if s < 0.70 else BANDS[2]


def channel(method):
    return "attrib*" if method.startswith("attrib") else method


def dict_channel(row, name):
    """H5252: the stratification channel is whether the row carries `name`."""
    return name if (row.get(f"{name}_gloss") or "").strip() else f"non-{name}"


def proportional(strata, keys, budget):
    """Spread `budget` over `keys` in proportion to stratum size, floor 1,
    capped by the stratum size, then correct rounding drift largest-first."""
    pool = sum(len(strata[k]) for k in keys)
    take = {}
    if not pool or budget <= 0:
        return take
    for k in keys:
        take[k] = min(len(strata[k]), max(1, round(budget * len(strata[k]) / pool)))
    drift = sum(take.values()) - min(budget, pool)
    order = sorted(keys, key=lambda k: (-len(strata[k]), k))
    i = 0
    while drift != 0 and i < 10_000:
        k = order[i % len(order)]
        if drift > 0 and take[k] > 1:
            take[k] -= 1; drift -= 1
        elif drift < 0 and take[k] < len(strata[k]):
            take[k] += 1; drift += 1
        i += 1
    return take


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def make_canary(rows, rng, fields):
    """One synthetic confident wrong match: the PWG sense of one lemma paired
    with the MW/Apte senses of an unrelated lemma, dressed at a high score.
    Its identity goes to the key file, never to the deck."""
    pool = [r for r in rows if r["pwg_gloss"].strip() and r["mw_gloss"].strip()]
    a, b = rng.sample(pool, 2)
    while a["lemma_slp1"] == b["lemma_slp1"]:
        a, b = rng.sample(pool, 2)
    card = {k: "" for k in fields}
    card.update({
        "lemma_slp1": a["lemma_slp1"],
        "group_id": f"{a['lemma_slp1']}#9",
        "status": "aligned",
        "shape": "1-1-0-0-0-0",
        "method": "gloss+ls",
        "score": "0.930",
        "witnesses": a["witnesses"],
        "flags": "",
        "failure_class": "",
        "pwg_sense_ids": a["pwg_sense_ids"], "pwg_gloss": a["pwg_gloss"],
        "mw_sense_ids": b["mw_sense_ids"], "mw_gloss": b["mw_gloss"],
        "apte_sense_ids": b["apte_sense_ids"], "apte_gloss": b["apte_gloss"],
        "note": "shared literary witness, weighted 1/df within the lemma",
    })
    key = {
        "canary_group_id": card["group_id"],
        "construction": "PWG sense of one lemma paired with MW/Apte senses of an unrelated lemma",
        "pwg_from_lemma": a["lemma_slp1"], "mw_apte_from_lemma": b["lemma_slp1"],
        "declared_score": card["score"], "expected_verdict": "different",
        "blinding": ("the adjudicator never sees which card is synthetic: this file is "
                     "written separately and is not opened until the verdicts are recorded"),
    }
    return card, key


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--target", type=int, default=TARGET)
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--no-canary", action="store_true", help="omit the positive control")
    ap.add_argument("--legacy-canary-metadata", action="store_true",
                    help=("reproduce the 20-09-2026 frozen deck, whose canary carried "
                          "stratum_eligible=0 / population_share=0 — a tell the H5070 "
                          "verifier caught; the default now copies its stratum's values"))
    ap.add_argument("--stratify-channel", choices=DICTS, default=None,
                    help="H5252: strata = score band x (carries this dictionary / does not)")
    ap.add_argument("--channel-budget", type=int, default=None,
                    help="cards for the named channel (rest of --target to its complement)")
    ap.add_argument("--exclude-deck", type=Path, action="append", default=[],
                    help="exclude every group_id of an earlier deck TSV (repeatable)")
    ap.add_argument("--handoff", default="H5070", help="handoff id written to the freeze")
    args = ap.parse_args()
    if args.channel_budget is not None and not args.stratify_channel:
        ap.error("--channel-budget needs --stratify-channel")
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    all_rows = load(args.src)
    fields = list(all_rows[0].keys())
    aligned = [r for r in all_rows if r["method"] != "singleton"]
    unaligned = [r for r in all_rows if r["method"] == "singleton"]

    excluded = set()
    gold_files = {}
    for g in GOLD:
        ids = {r["group_id"] for r in load(g)}
        gold_files[g.name] = {"cards": len(ids), "sha256": sha256(g)}
        excluded |= ids

    gold_ids = len(excluded)
    gold_eligible = len([r for r in aligned if r["group_id"] not in excluded])
    prior_decks = {}
    for deck_path in args.exclude_deck:
        ids = {r["group_id"] for r in load(deck_path)}
        # an earlier deck's synthetic control is not a judged row; its id may even
        # name a real row (H5070's `rajas#9` does), which must stay eligible
        key_path = deck_path.parent / "canary_key.json"
        prior_canary = (json.loads(key_path.read_text(encoding="utf-8"))["canary_group_id"]
                        if key_path.exists() else None)
        ids.discard(prior_canary)
        rel = deck_path.resolve()
        rel = str(rel.relative_to(ROOT)) if rel.is_relative_to(ROOT) else str(deck_path)
        fresh = ids - excluded
        prior_decks[rel] = {"cards_excluded": len(ids), "canary_skipped": prior_canary,
                            "sha256": sha256(deck_path),
                            "aligned_rows_removed": sum(1 for r in aligned if r["group_id"] in fresh),
                            "note": "exclusion is by group_id, like the gold fence; group_id is not "
                                    "unique, so sibling rows sharing a judged id leave too"}
        excluded |= ids

    eligible = [r for r in aligned if r["group_id"] not in excluded]

    chan = ((lambda r: dict_channel(r, args.stratify_channel)) if args.stratify_channel
            else (lambda r: channel(r["method"])))
    strata = defaultdict(list)
    for r in eligible:
        strata[(band(r["score"]), chan(r))].append(r)
    strata = {k: sorted(v, key=lambda r: r["group_id"]) for k, v in sorted(strata.items())}

    # equal budget per score band; inside a band, proportional to stratum size, floor 1
    per_band = args.target // len(BANDS)
    take = {}
    for b in ([] if args.stratify_channel else BANDS):
        keys = [k for k in strata if k[0] == b]
        pool = sum(len(strata[k]) for k in keys)
        if not pool:
            continue
        for k in keys:
            take[k] = min(len(strata[k]), max(1, round(per_band * len(strata[k]) / pool)))
        drift = sum(take[k] for k in keys) - per_band
        order = sorted(keys, key=lambda k: (-len(strata[k]), k))
        i = 0
        while drift != 0 and i < 10_000:
            k = order[i % len(order)]
            if drift > 0 and take[k] > 1:
                take[k] -= 1; drift -= 1
            elif drift < 0 and take[k] < len(strata[k]):
                take[k] += 1; drift += 1
            i += 1
    if args.stratify_channel:
        # H5252: the named channel gets its own budget, spread over bands by size
        name = args.stratify_channel
        own = [k for k in strata if k[1] == name]
        rest = [k for k in strata if k[1] != name]
        budget = args.channel_budget if args.channel_budget is not None else args.target // 2
        take.update(proportional(strata, own, budget))
        take.update(proportional(strata, rest, args.target - sum(take.values())))

    rng = random.Random(args.seed)
    picked, meta = [], []
    population = len(aligned)
    for key in strata:
        n = take.get(key, 0)
        if not n:
            continue
        pool = strata[key]
        chosen = sorted(rng.sample(pool, n), key=lambda r: r["group_id"])
        for r in chosen:
            row = dict(r)
            row["stratum"] = "|".join(key)
            row["stratum_eligible"] = len(pool)
            row["population_share"] = f"{len(pool) / len(eligible):.6f}"
            row["synthetic"] = "no"
            picked.append(row)
        meta.append({"stratum": "|".join(key), "score_band": key[0], "channel": key[1],
                     "eligible": len(pool), "eligible_share": round(len(pool) / len(eligible), 6),
                     "sampled": len(chosen)})

    canary_key = None
    if not args.no_canary:
        card, canary_key = make_canary(aligned, rng, fields)
        if args.stratify_channel:
            # H5252: never let the synthetic id name a real row (H5070's did)
            taken = {r["group_id"] for r in all_rows}
            n, lemma = 9, card["lemma_slp1"]
            while f"{lemma}#{n}" in taken:
                n += 1
            card["group_id"] = canary_key["canary_group_id"] = f"{lemma}#{n}"
        skey = (band(card["score"]), chan(card))
        if args.legacy_canary_metadata:
            elig, share = 0, "0.000000"
        else:
            # dress the control in the metadata of the stratum it imitates, so no
            # deck column tells it apart from the real cards drawn from that stratum
            n = len(strata.get(skey, []))
            elig, share = n, f"{n / len(eligible):.6f}"
        card.update({"stratum": "|".join(skey), "stratum_eligible": elig,
                     "population_share": share, "synthetic": "no"})
        picked.append(card)

    # seeded shuffle so the control does not sit in a predictable place
    rng.shuffle(picked)
    for i, r in enumerate(picked, 1):
        r["card"] = f"C{i:03d}"

    fields_out = ["card"] + fields + ["stratum", "stratum_eligible", "population_share", "synthetic"]
    deck = out / "review_deck.tsv"
    with deck.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields_out, delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(picked)

    fail = Counter(r["failure_class"] for r in unaligned)
    freeze = {
        "handoff": args.handoff,
        "source": str(args.src.relative_to(ROOT)) if args.src.is_relative_to(ROOT) else str(args.src),
        "source_sha256": sha256(args.src),
        "source_rows": len(all_rows),
        "seed": args.seed,
        "target": args.target,
        "population_aligned": population,
        "population_unaligned": len(unaligned),
        "coverage": round(population / len(all_rows), 6),
        "abstention": round(len(unaligned) / len(all_rows), 6),
        "abstention_taxonomy": dict(fail.most_common()),
        "unreachable_pairs_absent_dictionary": fail.get("absent-dictionary", 0),
        "gold_excluded_cards": gold_ids,
        "gold_files": gold_files,
        "eligible_after_gold_exclusion": len(eligible),
        **({"stratify_channel": args.stratify_channel,
            "channel_budget": sum(v for k, v in take.items() if k[1] == args.stratify_channel),
            "eligible_after_gold_only": gold_eligible,
            "prior_decks_excluded": prior_decks,
            "allocation": "named channel: fixed budget, proportional over bands; "
                          "complement: remainder, proportional over bands"}
           if args.stratify_channel else {}),
        "deck_cards": len(picked),
        "canary_included": canary_key is not None,
        "dictionary_reachability": {
            d: sum(1 for r in aligned if r.get(f"{d}_gloss", "").strip()) for d in DICTS
            if f"{d}_gloss" in fields
        },
        "strata": meta,
    }
    (out / "population_freeze.json").write_text(
        json.dumps(freeze, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if canary_key:
        (out / "canary_key.json").write_text(
            json.dumps(canary_key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"source sha256        {freeze['source_sha256']}")
    print(f"aligned population   {population}   unaligned {len(unaligned)}   coverage {freeze['coverage']*100:.2f}%")
    print(f"gold excluded        {len(excluded)} cards -> eligible {len(eligible)}")
    print(f"deck                 {len(picked)} cards (canary {'in' if canary_key else 'omitted'})")
    print()
    print(f"{'stratum':34s} {'elig':>6s} {'share':>7s} {'n':>3s}")
    for m in sorted(meta, key=lambda m: (BANDS.index(m['score_band']), -m['eligible'])):
        print(f"{m['stratum']:34s} {m['eligible']:6d} {m['eligible_share']*100:6.2f}% {m['sampled']:3d}")
    print(f"\nwrote {deck.relative_to(ROOT) if deck.is_relative_to(ROOT) else deck}")


if __name__ == "__main__":
    main()
