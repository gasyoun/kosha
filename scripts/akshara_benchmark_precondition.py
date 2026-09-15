#!/usr/bin/env python3
"""H3743 - self-checking precondition gate for the full-corpus benchmark.

Verifies the akshara FULL crawl (H3597) has actually drained before any
benchmark scoring starts. Three checks, all required:

  1. both crawl passes report DONE: every census head has an http==200 row
     in data/akshara_full/crawl_manifest.jsonl (pass 1, originals) and in
     data/akshara_full/crawl_manifest_ru.jsonl for each of mw_ru/apte_ru/
     pwg_ru (pass 2, MT).
  2. the case-twin repair pass is applied: crawl_manifest_repair.jsonl
     exists and covers the twin keys listed in
     data/akshara_full/parity/casefold_twins.tsv.
  3. the PARSED row count matches the frozen census of 51,663 heads:
     data/akshara_full/parsed_corpus.jsonl (pass 1) and
     data/akshara_full/parsed_corpus_ru.jsonl (pass 2, x3 dicts) - these are
     gitignored/RESTRICTED and only exist once scripts/akshara_full_parse.py
     has actually run against locally-present raw HTML.

If any check fails: print NOT YET DRAINED with the measured numbers and
exit 0 (this is the designed early-exit, not an error).

Usage:
  python scripts/akshara_benchmark_precondition.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AF = ROOT / "data" / "akshara_full"
CENSUS = AF / "census.json"
CRAWL_ALL = AF / "crawl_manifest.jsonl"
CRAWL_RU = AF / "crawl_manifest_ru.jsonl"
REPAIR = AF / "crawl_manifest_repair.jsonl"
TWINS = AF / "parity" / "casefold_twins.tsv"
PARSED_ALL = AF / "parsed_corpus.jsonl"
PARSED_RU = AF / "parsed_corpus_ru.jsonl"

MT_DICTS = ("mw_ru", "apte_ru", "pwg_ru")


def ok_keys(path: Path, key_field: str = "slp1") -> set[str]:
    keys: set[str] = set()
    if not path.exists():
        return keys
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("http") == 200:
                keys.add(r[key_field])
    return keys


def parsed_count(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    if not CENSUS.exists():
        print("NOT YET DRAINED: census.json missing - crawl never froze its head list")
        return 0
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    target = census["heads"]

    reasons = []

    # 1. pass 1 (originals) coverage
    ok_all = ok_keys(CRAWL_ALL)
    if len(ok_all) < target:
        reasons.append(
            f"pass 1 (originals) crawl incomplete: {len(ok_all)}/{target} http==200 "
            f"in {CRAWL_ALL.relative_to(ROOT)}"
        )

    # 1b. pass 2 (ru/MT) coverage per dict
    ok_ru = ok_keys(CRAWL_RU)
    ru_by_dict: dict[str, int] = {d: 0 for d in MT_DICTS}
    for key in ok_ru:
        _, _, d = key.partition("|")
        if d in ru_by_dict:
            ru_by_dict[d] += 1
    for d in MT_DICTS:
        if ru_by_dict[d] < target:
            reasons.append(
                f"pass 2 ({d}) crawl incomplete: {ru_by_dict[d]}/{target} http==200 "
                f"in {CRAWL_RU.relative_to(ROOT)}"
            )

    # 2. repair pass applied
    if not REPAIR.exists():
        reasons.append(f"case-twin repair pass missing: {REPAIR.relative_to(ROOT)} absent")
    elif TWINS.exists():
        twin_keys = set()
        with open(TWINS, encoding="utf-8") as f:
            next(f, None)  # header
            for line in f:
                line = line.rstrip("\n")
                if line:
                    twin_keys.add(line.split("\t")[0])
        repaired = ok_keys(REPAIR)
        missing_twins = twin_keys - repaired
        if missing_twins:
            reasons.append(
                f"case-twin repair incomplete: {len(missing_twins)}/{len(twin_keys)} "
                f"twin keys not yet in {REPAIR.relative_to(ROOT)}"
            )

    # 3. parsed row counts (the actual benchmark input)
    n_parsed_all = parsed_count(PARSED_ALL)
    if n_parsed_all < target:
        reasons.append(
            f"pass 1 PARSED corpus incomplete: {n_parsed_all}/{target} rows "
            f"in {PARSED_ALL.relative_to(ROOT)} "
            f"({'file absent' if not PARSED_ALL.exists() else 'partial'})"
        )
    n_parsed_ru = parsed_count(PARSED_RU)
    target_ru = target * len(MT_DICTS)
    if n_parsed_ru < target_ru:
        reasons.append(
            f"pass 2 PARSED corpus incomplete: {n_parsed_ru}/{target_ru} rows "
            f"in {PARSED_RU.relative_to(ROOT)} "
            f"({'file absent' if not PARSED_RU.exists() else 'partial'})"
        )

    if reasons:
        print("NOT YET DRAINED")
        print(f"census target: {target} heads (frozen {census.get('frozen_ts')})")
        for r in reasons:
            print(f"  - {r}")
        return 0

    print(f"DRAINED: {target} heads, all passes + repair + parse complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
