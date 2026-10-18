#!/usr/bin/env python3
"""Compare sanskritabhyas.in conjugation tables against our present-system verbs.

The site publishes ten lakāras per root at `/<slug>-Conjugation`; our generator
(MWinflect `verbs/pysanskritv2/tables/calc_tables.txt`, ingested into kosha's
`inflections` as `v_<gana>`/`v_p`) covers only the present system —
pre/ipf/ipv/opt — and only gaṇas 1, 4, 6, 10. So this comparator does two
different jobs and never mixes them:

  VERIFICATION  roots in gaṇas 1/4/6/10: cell-by-cell diff on the four shared
                lakāras (लट् / लङ् / लोट् / विधिलिङ्), classified AGREE / DIFF /
                SITE_EMPTY, with every DIFF printed for triage.
  COVERAGE      everything else: a census of what the site has and we do not
                (other six lakāras, other six gaṇas). Never counted as a defect.

Input is the JSONL produced by the console grabber in
docs/SANSKRITABHYAS_VERB_VERIFICATION_2026-10-18.md (one record per root).

Usage:
    python scripts/sanskritabhyas_compare.py ~/Downloads/sa_conj_part*.jsonl
    python scripts/sanskritabhyas_compare.py --mw ../MWinflect/verbs/pysanskritv2/tables/calc_tables.txt --json-out data/e1/sa_agreement.json

The site's forms are Devanagari with optional variants separated by " / "
(e.g. `वृणीतात् / वृणीताद् / वृणातु`); a cell AGREES if our form is one of them.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

try:                                    # kosha's own converter (src tree or installed)
    from kosha.transliterate import to_slp1_auto
except Exception:                       # legacy app/ shim fallback
    sys.path.insert(0, str(ROOT / "app"))
    from transliterate import to_slp1_auto  # type: ignore

GANAS = {"भ्वादिः": "1", "अदादिः": "2", "जुहोत्यादिः": "3", "दिवादिः": "4",
         "स्वादिः": "5", "तुदादिः": "6", "रुधादिः": "7", "तनादिः": "8",
         "क्र्यादिः": "9", "चुरादिः": "10"}
TENSE = {"Present Tense": "pre", "Imperfect Past Tense": "ipf",
         "Imperative Mood": "ipv", "Potential Mood": "opt"}
PADA = {"parasmai": "a", "atmane": "m"}
ORDER = {"Third Person": 0, "Second Person": 1, "First Person": 2}
DEFAULT_MW = (Path.home() / "Documents" / "GitHub" / "MWinflect" /
              "verbs" / "pysanskritv2" / "tables" / "calc_tables.txt")


def load_reference(path: Path) -> dict[tuple[str, str, str, str], list[str]]:
    ref = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            head, root, _cls, _base, forms = line.rstrip("\n").split("\t")
            gana, pada, tense = head.split(",")
            ref[(root, pada, tense, gana)] = forms.split(":")
    return ref


def records(paths: list[str]):
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--mw", default=os.environ.get("SA_MW", str(DEFAULT_MW)))
    ap.add_argument("--max-diffs", type=int, default=25)
    ap.add_argument("--json-out")
    args = ap.parse_args()

    paths = args.paths or glob.glob(str(Path.home() / "Downloads" / "sa_conj_part*.jsonl"))
    if not paths:
        print("no sa_conj_part*.jsonl found", file=sys.stderr)
        return 2
    ref = load_reference(Path(args.mw))

    stats = collections.Counter()
    by_tense, by_pada, by_gana = collections.Counter(), collections.Counter(), collections.Counter()
    diffs, comparable_roots = [], set()
    gana_roots = collections.Counter()
    missing_root = collections.Counter()

    for rec in records(paths):
        if rec.get("error") or not rec.get("sections"):
            stats["record_error"] += 1
            continue
        parts = rec["slug"].split("-")
        gana = GANAS.get(parts[1] if len(parts) > 1 else "", "?")
        try:
            root = to_slp1_auto(parts[0])
        except Exception:
            stats["root_unconvertible"] += 1
            continue
        pada = PADA.get(rec.get("pada", ""), "?")
        gana_roots[gana] += 1
        has_ref = False

        for sec in rec["sections"]:
            tense = TENSE.get(sec.get("name", ""))
            if not tense:
                continue                                    # coverage only
            grid = {ORDER[p["person"]]: p["forms"] for p in sec["persons"] if p["person"] in ORDER}
            if len(grid) != 3:
                stats["bad_grid"] += 1
                continue
            cells = [grid[i][j] for i in (0, 1, 2) for j in (0, 1, 2)]
            key = (root, pada, tense, gana)
            ours = ref.get(key)
            if ours is None:
                missing_root[(pada, tense, gana)] += 1
                continue
            has_ref = True
            if len(cells) != len(ours):
                stats["length_mismatch"] += 1
                continue
            for n, (cell, mine) in enumerate(zip(cells, ours)):
                stats["cell_total"] += 1
                by_tense[tense] += 1
                by_pada[pada] += 1
                by_gana[gana] += 1
                variants = {to_slp1_auto(v.strip()) for v in cell.split("/") if v.strip()}
                if mine in variants:
                    stats["agree"] += 1
                elif not variants:
                    stats["site_empty"] += 1
                else:
                    stats["diff"] += 1
                    if len(diffs) < args.max_diffs:
                        diffs.append({"root": root, "gana": gana, "pada": pada,
                                      "tense": tense, "cell": n, "ours": mine, "site": cell})
        if has_ref:
            comparable_roots.add(root)

    total = stats["cell_total"]
    print(f"records read: {sum(gana_roots.values())} · roots by gaṇa: {dict(sorted(gana_roots.items()))}")
    print(f"comparable roots: {len(comparable_roots)} · comparable cells: {total}")
    if total:
        print(f"AGREE {stats['agree']} ({100 * stats['agree'] / total:.1f} %) · "
              f"DIFF {stats['diff']} · site_empty {stats['site_empty']}")
    print("by tense:", dict(by_tense))
    print("by pada:", dict(by_pada))
    if missing_root:
        print("no counterpart in our tables:", dict(missing_root.most_common(8)))
    for d in diffs:
        print("DIFF", d)

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "records": sum(gana_roots.values()),
            "roots_by_gana": dict(gana_roots),
            "comparable_roots": sorted(comparable_roots),
            "cells": total, "stats": dict(stats),
            "by_tense": dict(by_tense), "by_pada": dict(by_pada), "by_gana": dict(by_gana),
            "diffs": diffs,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
