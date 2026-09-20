#!/usr/bin/env python
"""H5070 — render the frozen selective-risk deck as readable adjudication cards.

Presentation only: it reads the frozen deck and prints one card per group, with
the per-dictionary senses the aligner claims denote the same meaning. It never
prints the stratum, the score or the method — an adjudicator who can see the
confidence band is no longer measuring it. The canary is indistinguishable here
by construction.
"""
import argparse, csv, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "data/concordance/selective_risk/review_deck.tsv"
DICTS = [("pwg", "PWG (de)"), ("mw", "MW  (en)"), ("apte", "Apte(en)"),
         ("md", "MD  (en)"), ("skd", "SKD (sa)"), ("vcp", "VCP (sa)")]

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--deck", type=Path, default=DECK)
ap.add_argument("--start", type=int, default=1)
ap.add_argument("--end", type=int, default=999)
ap.add_argument("--width", type=int, default=260)
a = ap.parse_args()

with a.deck.open(encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh, delimiter="\t"))

for i, r in enumerate(rows, 1):
    if not (a.start <= i <= a.end):
        continue
    print("=" * 96)
    print(f"{r['card']}  lemma={r['lemma_slp1']}  shape={r['shape']}  witnesses={r['witnesses'][:70]}")
    for key, label in DICTS:
        g = (r.get(f"{key}_gloss") or "").strip()
        if g:
            print(f"  {label}  {g[:a.width]}")
