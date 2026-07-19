#!/usr/bin/env python
"""Regression test for the W-RU-b subhāṣita difficulty grading (H1279).

Pins 10 HAND-CHECKED sayings — 7 verified-easy band members (each read in
full during the curation pass: canonical beginner anthology pieces) and 3
verified-hard contrasts (alliterative compound chains, dense āryās) — and
asserts:

  1. re-scoring each of the 10 live (same code path as the builder)
     reproduces the committed TSV row exactly (difficulty, vocab, fusion,
     metre) — the byte-stability of the grading step, per
     VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md § W-RU-b;
  2. the 7 easy ones sit in the committed beginner band, the 3 hard ones
     score far above the band ceiling — band membership matches the hand
     verdicts;
  3. every band member's TSV row carries a resolved metre (curation gate C4);
  4. the built pack contains exactly the band, ordered by difficulty, every
     saying with metre + split lines.

Run:  python scripts/test_subhashita_difficulty.py     (offline, ~10 s)
"""
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_subhashita_difficulty as bd  # noqa: E402

DIFF_TSV = ROOT / "data" / "subhashita" / "subhashita_difficulty.tsv"
BAND_TSV = ROOT / "data" / "subhashita" / "beginner_band.tsv"
PACK_JSON = ROOT / "data" / "subhashita" / "subhashita_beginner_pack.json"

# hand-checked during the H1279 curation pass (Fable 5, claude-fable-5):
# read in full; verdicts are human, the numbers pin the scorer against drift.
EASY = {
    3128: 0.2841,  # dharmeṇa hanyate vyādhir…      — anaphora drill, upagīti
    1249: 0.2893,  # udyamena hi sidhyanti…          — THE beginner classic
    133: 0.3125,   # atithirbālakaścaiva…            — dehi dehi humour
    7583: 0.3686,  # paṭha putra…                    — learn-my-son meta-saying
    2763: 0.3982,  # dānena pāṇir na tu kaṅkaṇena…   — indravajrā gem
    4897: 0.4051,  # muṇḍe muṇḍe matir bhinnā…       — proverb of proverbs
    954: 0.4063,   # āpatsu mitraṃ jānīyād…          — test-the-friend list
}
HARD = {
    792: 0.7689,   # astamastakaparyasta…            — alliterative compound chain
    5748: 0.7499,  # rājasevā… asidhārāvalehanam     — sword-edge licking, rare vocab
    470: 0.7366,   # apriyavacanadaridraiḥ…          — dense āryā compounds
}
BAND_CEILING = 0.4063  # the curated pool's max (250-lowest cut)

fails = []


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails.append(msg)


def main():
    tsv = {int(r["num"]): r for r in
           csv.DictReader(DIFF_TSV.open(encoding="utf-8"), delimiter="\t")}
    band = {int(r["num"]) for r in
            csv.DictReader(BAND_TSV.open(encoding="utf-8"), delimiter="\t")}
    pack = json.loads(PACK_JSON.read_text(encoding="utf-8"))

    recs = {}
    wanted = set(EASY) | set(HARD)
    with bd.SPRUECHE.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["num"] in wanted:
                recs[r["num"]] = r

    w_vocab, w_fusion = bd.load_weights()
    ranks, grammar, maxrank = bd.load_ranks()
    w1b = bd.load_w1b()
    seg = bd.Segmenter()
    from vidyut.chandas import Chandas
    chandas = Chandas(str(bd.METERS_TSV))

    print("1) live re-score == committed TSV row (10 hand-checked sayings)")
    for num, expected in sorted({**EASY, **HARD}.items()):
        vocab, fusion, *_rest, slp = bd.score_saying(
            recs[num]["iast"], seg, ranks, grammar, maxrank, w1b)
        d = round(w_vocab * vocab + w_fusion * fusion, 4)
        row = tsv[num]
        check(d == expected == float(row["difficulty"]),
              f"{num}: live {d} == pinned {expected} == TSV {row['difficulty']}")
        metre, _method, _syl = bd.classify_metre(chandas, slp)
        check(metre == row["metre"], f"{num}: metre live '{metre}' == TSV '{row['metre']}'")

    print("2) band membership matches the hand verdicts")
    for num in EASY:
        check(num in band, f"{num} (hand-checked easy) is in beginner_band.tsv")
    for num in HARD:
        check(num not in band, f"{num} (hand-checked hard) is NOT in the band")
        check(float(tsv[num]["difficulty"]) > BAND_CEILING + 0.25,
              f"{num} scores far above the band ceiling")

    print("3) every band member carries a resolved metre (curation gate C4)")
    no_metre = [n for n in band if not tsv[n]["metre"]]
    check(not no_metre, f"band members without metre: {no_metre or 'none'}")

    print("4) the built pack is exactly the band, difficulty-ordered, complete")
    nums = [s["num"] for s in pack["sayings"]]
    check(set(nums) == band, f"pack sayings == band ({len(nums)} == {len(band)})")
    diffs = [s["difficulty"] for s in pack["sayings"]]
    check(diffs == sorted(diffs), "pack ordered by difficulty ascending")
    bad = [s["num"] for s in pack["sayings"]
           if not s["metre"] or not s["lines"] or
           not all(ch["t"] for ln in s["lines"] for ch in ln["chunks"])]
    check(not bad, f"every pack saying has metre + split lines (bad: {bad or 'none'})")

    print()
    if fails:
        sys.exit(f"{len(fails)} check(s) FAILED")
    print("all checks green")


if __name__ == "__main__":
    main()
