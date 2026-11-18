#!/usr/bin/env python3
"""Convert H8433 blind-sheet decisions.json -> H6253 canary mg_labels.tsv.

Only MG's explicit approve/reject decisions become 1/0. A defer/null decision
leaves that cell unlabeled and the converter REFUSES to write the file until
all 15 decisions are present — a partial sheet must never masquerade as a
completed human reproduction check.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
DATA = REPO / "data" / "eval" / "articlegen"
TEMPLATE = DATA / "canary" / "mg_labels_template.tsv"
LABELS = DATA / "canary" / "mg_labels.tsv"
SHEET_ID = "kosha-h6253-mg-canary-blind_18-11-26"
PREFIX = "h6253-canary-"
CRITERIA = ("gloss", "examples", "citations")
MATCH_FIELD = {c: c + "_match" for c in CRITERIA}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("decisions", help="decisions.json exported by the blind sheet")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing mg_labels.tsv")
    args = ap.parse_args()

    payload = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
    if payload.get("sheet_id") != SHEET_ID:
        print("REFUSE: decisions.json sheet_id %r != %r"
              % (payload.get("sheet_id"), SHEET_ID), file=sys.stderr)
        return 2

    values = {}
    for item in payload.get("items", []):
        did = item.get("id", "")
        if not did.startswith(PREFIX):
            print("REFUSE: unexpected card id %r" % did, file=sys.stderr)
            return 2
        slp1, sep, criterion = did[len(PREFIX):].rpartition("-")
        if not sep or criterion not in CRITERIA:
            print("REFUSE: cannot parse criterion from %r" % did, file=sys.stderr)
            return 2
        decision = item.get("decision")
        if decision == "approve":
            value = "1"
        elif decision == "reject":
            value = "0"
        elif decision in ("defer", None, ""):
            value = ""          # unlabeled
        else:
            print("REFUSE: unknown decision %r on %s" % (decision, did), file=sys.stderr)
            return 2
        values[(slp1, criterion)] = value

    with open(TEMPLATE, encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    missing = ["%s.%s" % (r["slp1"], c)
               for r in rows for c in CRITERIA
               if not values.get((r["slp1"], c))]
    if missing:
        print("REFUSE: %d of 15 decisions unlabeled: %s"
              % (len(missing), ", ".join(missing)), file=sys.stderr)
        return 2
    if LABELS.exists() and not args.force:
        print("REFUSE: %s exists (use --force only with MG's explicit ruling)"
              % LABELS.relative_to(REPO), file=sys.stderr)
        return 2

    LABELS.parent.mkdir(parents=True, exist_ok=True)
    provenance = "MG/%s@%s" % (SHEET_ID, payload.get("reviewedAt", "unknown"))
    with open(LABELS, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            for criterion in CRITERIA:
                out[MATCH_FIELD[criterion]] = values[(row["slp1"], criterion)]
            out["notes"] = provenance
            writer.writerow(out)

    print("wrote %s (5 rows x 3 criteria, all MG-decided)" % LABELS.relative_to(REPO))
    print("next: python3 scripts/articlegen_score.py --canary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
