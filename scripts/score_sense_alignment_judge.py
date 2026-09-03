#!/usr/bin/env python
"""H3910 — score the two LLM-judge passes over the acceptance sample.

The handoff is explicit about the order of reporting: *"run the sample twice and
report judge self-consistency before reporting anything else, because a judge
that flips on 15 % of cards cannot support a precision figure to two significant
figures."* This script therefore prints self-consistency first and refuses to
print anything that could be mistaken for the acceptance precision figure — that
number is the human vote's to produce, not the judge's.

What it does:

  1. joins verdicts_pass_a.json and verdicts_pass_b.json through packet_key.json
     on `group_id` (card ids differ between passes by design — pass B is
     reshuffled and renumbered so cards cannot be aligned by position);
  2. reports overall agreement, a same/different/unsure confusion matrix, and
     agreement restricted to the `attrib` strata — the channel being measured;
  3. lists every flipped group so the disagreements can be inspected rather
     than averaged away;
  4. reports the judge's *provisional* same-rate per stratum, labelled as a
     judge-side signal, with the population weights carried in the sample.

Two limitations are printed with the numbers, never separately:

  * no API-key judge harness exists in this repo, so both passes were run
    in-session by the same model over reordered presentations — this bounds the
    self-consistency figure OPTIMISTICALLY;
  * the pass-B `convention` string adds a referent-over-numbering clause that
    pass A's lacks, so some A/B flips are convention drift, not instability.

Reads  data/concordance/sense_alignment_acceptance_sample.tsv
       data/concordance/sense_alignment_acceptance_strata.json
       data/concordance/judge/packet_key.json
       data/concordance/judge/verdicts_pass_{a,b}.json
Writes data/concordance/judge/judge_self_consistency.json
       data/concordance/judge/JUDGE_SELF_CONSISTENCY.md
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
CONC = ROOT / "data" / "concordance"
JUDGE = CONC / "judge"
SAMPLE = CONC / "sense_alignment_acceptance_sample.tsv"
STRATA = CONC / "sense_alignment_acceptance_strata.json"
KEY = JUDGE / "packet_key.json"
VA = JUDGE / "verdicts_pass_a.json"
VB = JUDGE / "verdicts_pass_b.json"
OUT_JSON = JUDGE / "judge_self_consistency.json"
OUT_MD = JUDGE / "JUDGE_SELF_CONSISTENCY.md"

LABELS = ["same", "different", "unsure"]

LIMITS = [
    "Both passes were run in-session by the same model (Opus 5, claude-opus-5) over "
    "reordered, renumbered presentations of the same 120 cards. No independent judge "
    "harness exists in this repo. A same-model re-read is a WEAKER test than two "
    "independent judges, so the agreement figure below is an OPTIMISTIC bound on judge "
    "stability, not a neutral one.",
    "The two passes' `convention` strings are not byte-identical: pass B adds a clause "
    "instructing that a group is judged on referent rather than on the source dictionary's "
    "own sense numbering. Some A/B disagreement is therefore convention drift rather than "
    "judge instability, and the flip list below must be read with that in mind.",
    "This file contains NO acceptance precision figure. The judge is a first pass; the "
    "verdict is the human vote on the published review sheet. The `same`-rates below are "
    "judge-side signals used to size and stratify that vote.",
]


def load_verdicts(path, key_map):
    doc = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for v in doc["verdicts"]:
        gid = key_map[v["card"]]
        out[gid] = {"card": v["card"], "verdict": v["verdict"], "reason": v["reason"]}
    return doc, out


def wilson(k, n, z=1.96):
    """Wilson score interval — honest at the small n these strata carry, where a
    normal-approximation interval would run past 0/1."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def main():
    key = json.loads(KEY.read_text(encoding="utf-8"))
    doc_a, a = load_verdicts(VA, key["pass_a"])
    doc_b, b = load_verdicts(VB, key["pass_b"])

    with SAMPLE.open(encoding="utf-8") as fh:
        rows = {r["group_id"]: r for r in csv.DictReader(fh, delimiter="\t")}
    strata_meta = {m["stratum"]: m for m in json.loads(STRATA.read_text(encoding="utf-8"))["strata"]}

    gids = sorted(set(a) & set(b))
    missing = sorted((set(a) ^ set(b)) | (set(rows) - set(gids)))
    n = len(gids)

    agree = [g for g in gids if a[g]["verdict"] == b[g]["verdict"]]
    flips = [g for g in gids if a[g]["verdict"] != b[g]["verdict"]]

    matrix = Counter((a[g]["verdict"], b[g]["verdict"]) for g in gids)

    # binary view: `unsure` collapsed out, because the acceptance question is binary
    binary = [g for g in gids if a[g]["verdict"] != "unsure" and b[g]["verdict"] != "unsure"]
    binary_agree = [g for g in binary if a[g]["verdict"] == b[g]["verdict"]]

    # Cohen's kappa over the 3-way labels — raw agreement alone flatters a judge
    # whose marginals are lopsided.
    ma = Counter(a[g]["verdict"] for g in gids)
    mb = Counter(b[g]["verdict"] for g in gids)
    pe = sum(ma[l] * mb[l] for l in LABELS) / (n * n) if n else 0.0
    po = len(agree) / n if n else 0.0
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0

    # per-channel and per-stratum
    by_stratum = defaultdict(list)
    by_channel = defaultdict(list)
    for g in gids:
        by_stratum[rows[g]["stratum"]].append(g)
        m = rows[g]["method"]
        by_channel["attrib*" if m.startswith("attrib") else "western"].append(g)

    lines = []
    w = lines.append
    w("# H3910 — judge self-consistency (reported BEFORE any rate)")
    w("")
    w("_Created: 03-09-2026 · Last updated: 03-09-2026_")
    w("")
    w("Generated by [`scripts/score_sense_alignment_judge.py`]"
      "(https://github.com/gasyoun/kosha/blob/main/scripts/score_sense_alignment_judge.py). "
      "Judge: Opus 5 (claude-opus-5), two passes over the same 120-card stratified sample, "
      "pass B reshuffled and renumbered (shuffle seed "
      f"{key['shuffle_seed']}) so cards cannot be aligned by position.")
    w("")
    w("## 1. Read this before any number below")
    w("")
    for i, lim in enumerate(LIMITS, 1):
        w(f"{i}. {lim}")
    w("")
    w("## 2. Self-consistency")
    w("")
    w(f"- cards joined on `group_id`: **{n}** / {len(rows)} sampled"
      + (f" — UNJOINED: {', '.join(missing)}" if missing else ""))
    w(f"- raw agreement (3-way `same`/`different`/`unsure`): **{len(agree)}/{n} = {po:.1%}**")
    w(f"- flip rate: **{len(flips)}/{n} = {len(flips)/n:.1%}**"
      + ("  — at or under the handoff's 15 % ceiling" if n and len(flips) / n <= 0.15
         else "  — ABOVE the handoff's 15 % ceiling; a two-significant-figure precision "
              "claim is not supportable on this judge"))
    w(f"- Cohen's κ (3-way): **{kappa:.3f}**")
    if binary:
        w(f"- agreement with `unsure` excluded: "
          f"**{len(binary_agree)}/{len(binary)} = {len(binary_agree)/len(binary):.1%}**")
    w("")
    w("### Confusion matrix (rows = pass A, columns = pass B)")
    w("")
    w("| A \\ B | " + " | ".join(LABELS) + " | total |")
    w("|---|" + "---|" * (len(LABELS) + 1))
    for la in LABELS:
        cells = [matrix[(la, lb)] for lb in LABELS]
        w(f"| **{la}** | " + " | ".join(str(c) for c in cells) + f" | {sum(cells)} |")
    w("| **total** | " + " | ".join(str(mb[l]) for l in LABELS) + f" | {n} |")
    w("")
    w("### Agreement by channel — the `attrib` channel is the one being measured")
    w("")
    w("| channel | cards | agree | rate |")
    w("|---|---:|---:|---:|")
    for ch in sorted(by_channel):
        g = by_channel[ch]
        ok = [x for x in g if a[x]["verdict"] == b[x]["verdict"]]
        w(f"| `{ch}` | {len(g)} | {len(ok)} | {len(ok)/len(g):.1%} |")
    w("")
    w("### Every flip, named")
    w("")
    if not flips:
        w("None — the two passes agree on all joined cards.")
    else:
        w("| group_id | stratum | pass A | pass B | pass A reason | pass B reason |")
        w("|---|---|---|---|---|---|")
        for g in flips:
            w(f"| `{g}` | `{rows[g]['stratum']}` | {a[g]['verdict']} | {b[g]['verdict']} "
              f"| {a[g]['reason']} | {b[g]['reason']} |")
    w("")
    w("## 3. Judge-side `same`-rate per stratum — NOT the acceptance precision")
    w("")
    w("A group counts as judge-`same` only when **both** passes say `same`; a card the judge "
      "flipped on is counted as unresolved, not silently resolved in either direction. "
      "Intervals are Wilson at 95 %. These are the numbers used to size the human vote; the "
      "acceptance figure replaces them once the vote returns.")
    w("")
    w("| stratum | pop | share | n | both-`same` | rate | 95 % CI | flips |")
    w("|---|---:|---:|---:|---:|---:|---|---:|")
    strat_payload = []
    for st in sorted(by_stratum, key=lambda s: -strata_meta[s]["population"]):
        g = by_stratum[st]
        both_same = [x for x in g if a[x]["verdict"] == "same" and b[x]["verdict"] == "same"]
        fl = [x for x in g if a[x]["verdict"] != b[x]["verdict"]]
        p, lo, hi = wilson(len(both_same), len(g))
        meta = strata_meta[st]
        w(f"| `{st}` | {meta['population']} | {meta['population_share']*100:.2f}% | {len(g)} "
          f"| {len(both_same)} | {p:.0%} | {lo:.0%}–{hi:.0%} | {len(fl)} |")
        strat_payload.append({
            "stratum": st,
            "population": meta["population"],
            "population_share": meta["population_share"],
            "census": meta["census"],
            "sampled": len(g),
            "both_same": len(both_same),
            "rate": round(p, 4),
            "ci95": [round(lo, 4), round(hi, 4)],
            "flips": len(fl),
        })
    w("")
    w("## 4. What this does not say")
    w("")
    w("Nothing here authorises publication of the aligned-sense table, and no threshold "
      "below is a tuning target: `TAU` 0.30, `GLOSS_FLOOR` 0.20 and `PREFIX_MIN` 4 stay at "
      "their marked defaults. A bad figure is a finding to write down, not a knob to turn.")
    w("")
    w("_Dr. Mārcis Gasūns_")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "handoff": "H3910",
        "judge": doc_a.get("judge"),
        "harness": doc_a.get("harness"),
        "shuffle_seed": key["shuffle_seed"],
        "convention_pass_a": doc_a.get("convention"),
        "convention_pass_b": doc_b.get("convention"),
        "conventions_identical": doc_a.get("convention") == doc_b.get("convention"),
        "limitations": LIMITS,
        "cards_joined": n,
        "unjoined": missing,
        "agreement": round(po, 4),
        "flip_rate": round(len(flips) / n, 4) if n else None,
        "cohens_kappa": round(kappa, 4),
        "agreement_excluding_unsure": (
            round(len(binary_agree) / len(binary), 4) if binary else None
        ),
        "confusion": {f"{x}|{y}": c for (x, y), c in sorted(matrix.items())},
        "by_channel": {
            ch: {
                "cards": len(g),
                "agree": sum(1 for x in g if a[x]["verdict"] == b[x]["verdict"]),
            }
            for ch, g in sorted(by_channel.items())
        },
        "flips": [
            {
                "group_id": g,
                "stratum": rows[g]["stratum"],
                "pass_a": a[g]["verdict"],
                "pass_b": b[g]["verdict"],
                "pass_a_reason": a[g]["reason"],
                "pass_b_reason": b[g]["reason"],
            }
            for g in flips
        ],
        "strata": strat_payload,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("SELF-CONSISTENCY FIRST (handoff order)")
    print(f"  cards joined      {n}")
    print(f"  raw agreement     {len(agree)}/{n} = {po:.1%}")
    print(f"  flip rate         {len(flips)}/{n} = {len(flips)/n:.1%}" if n else "")
    print(f"  Cohen's kappa     {kappa:.3f}")
    if binary:
        print(f"  excl. `unsure`    {len(binary_agree)}/{len(binary)} = {len(binary_agree)/len(binary):.1%}")
    for ch in sorted(by_channel):
        g = by_channel[ch]
        ok = sum(1 for x in g if a[x]["verdict"] == b[x]["verdict"])
        print(f"  channel {ch:9s} {ok}/{len(g)} = {ok/len(g):.1%}")
    print(f"  conventions identical across passes: {payload['conventions_identical']}")
    print()
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
