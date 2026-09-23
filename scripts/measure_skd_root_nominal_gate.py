#!/usr/bin/env python3
"""Measure the H5273 root-vs-nominal gate against a pre-gate table and the H5252 deck.

    python scripts/measure_skd_root_nominal_gate.py --before <old tsv> [--after <new tsv>]
    python scripts/measure_skd_root_nominal_gate.py --before-rev origin/main

Reads, never writes, anything under data/concordance/selective_risk_skd/: the
deck and the two frozen verdict files are only re-scored against the rebuilt
table, no new adjudication. A deck card counts as REMOVED when no aligned row
of the new table carries both its PWG sense and its ŚKDR sense any more.

Prints one JSON object: ŚKDR attachment counts before/after (rows and
PWG↔ŚKDR sense pairs), and the deck re-score split by the primary verdict,
with the blind second pass's agreement alongside.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "data" / "concordance" / "sense_alignment.tsv"
SKD = ROOT / "data" / "concordance" / "selective_risk_skd"


def read_tsv(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def skd_pairs(rows: list[dict]) -> tuple[int, set[tuple[str, str]]]:
    """(aligned rows carrying ŚKDR, {(pwg sense, skd sense)} co-grouped pairs)."""
    n, pairs = 0, set()
    for r in rows:
        if r["status"] != "aligned" or not r["skd_sense_ids"]:
            continue
        n += 1
        for s in r["skd_sense_ids"].split("; "):
            for p in (r["pwg_sense_ids"].split("; ") if r["pwg_sense_ids"] else []):
                pairs.add((p, s))
    return n, pairs


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--before", type=Path, help="pre-gate sense_alignment.tsv")
    g.add_argument("--before-rev", help="git revision holding the pre-gate table")
    ap.add_argument("--after", type=Path, default=TABLE)
    a = ap.parse_args()

    before_text = (a.before.read_text(encoding="utf-8") if a.before else subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{a.before_rev}:data/concordance/sense_alignment.tsv"],
        check=True, capture_output=True, encoding="utf-8").stdout)
    before, after = read_tsv(before_text), read_tsv(a.after.read_text(encoding="utf-8"))
    nb, pb = skd_pairs(before)
    na, pa = skd_pairs(after)

    deck = read_tsv((SKD / "review_deck.tsv").read_text(encoding="utf-8"))
    v1 = {r["card"]: r for r in read_tsv((SKD / "adjudication_h5252.tsv").read_text(encoding="utf-8"))}
    v2 = {r["card"]: r for r in read_tsv((SKD / "adjudication_h5252_blind2.tsv").read_text(encoding="utf-8"))}
    by_verdict: dict[str, dict] = {}
    for r in deck:
        if not r["skd_sense_ids"] or r.get("synthetic") == "yes" or r["card"] not in v1:
            continue
        pairs = {(p, s) for s in r["skd_sense_ids"].split("; ")
                 for p in r["pwg_sense_ids"].split("; ") if p}
        removed = not (pairs & pa)
        verdict = v1[r["card"]]["verdict"]
        b = by_verdict.setdefault(verdict, {"cards": 0, "removed": 0, "kept": [], "removed_cards": []})
        b["cards"] += 1
        b["removed"] += removed
        (b["removed_cards"] if removed else b["kept"]).append(
            f"{r['card']} {r['lemma_slp1']} (blind2: {v2.get(r['card'], {}).get('verdict', '-')})")

    print(json.dumps({
        "skd_aligned_rows": {"before": nb, "after": na, "removed": nb - na},
        "pwg_skd_pairs": {"before": len(pb), "after": len(pa),
                          "removed": len(pb - pa), "added": len(pa - pb)},
        "h5252_deck_by_primary_verdict": by_verdict,
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
