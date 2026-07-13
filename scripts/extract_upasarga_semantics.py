#!/usr/bin/env python
"""H876 / roadmap W6 — Sanskrit root × preverb (upasarga) semantics.

The `verbs` sheet of SanskritGrammar/Concordance/Gita.xlsm records, per root, its
base sense and how PREVERBS shift it (√vac 'speak' → pra-√vac 'declare'; √as
'be' → sam-ni-√as 'renounce', vi-ud-√as 'reject'). Sanskrit dictionaries are thin
on this compositional upasarga semantics; this extracts it into a flat dataset.

Sheet layout (0-indexed): col C(2)=corpus count · D(3)=root(√X) · E(4)=base sense;
then repeating (preverb, sense) pairs from col F(5): (5,6), (7,8), (9,10)…

Public/MIT, credit Dr. Mārcis Gasūns.
Usage: python scripts/extract_upasarga_semantics.py --xlsm <path>
"""
import argparse
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSM = ROOT.parent / "SanskritGrammar" / "Concordance" / "Gita.xlsm"
OUT = ROOT / "data" / "gita" / "upasarga_semantics.tsv"


def s(v):
    return "" if v is None else str(v).strip().replace("\t", " ").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsm", default=str(DEFAULT_XLSM))
    args = ap.parse_args()
    import openpyxl
    ws = openpyxl.load_workbook(args.xlsm, read_only=True, data_only=True)["verbs"]

    # A preverb cell ends in '-' (pra-, sam-ni-, vi-ud-); a sense cell does not.
    # The sheet's column alignment is irregular, so classify by that signal and
    # pair each preverb with the next following sense; a sense with no pending
    # preverb (and none yet recorded) is the root's base sense.
    def is_preverb(x):
        return bool(x) and x.rstrip().endswith("-")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    n_roots = n_rows = 0
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["root", "preverb", "combined", "sense", "count"])
        for r in ws.iter_rows(min_row=1, values_only=True):
            root = s(r[3]) if len(r) > 3 else ""
            if not root.startswith("√"):
                continue
            count = s(r[2]) if len(r) > 2 else ""
            n_roots += 1
            cells = [s(r[i]) for i in range(4, len(r)) if s(r[i])]
            base_written = False
            pending = None
            for cell in cells:
                if is_preverb(cell):
                    pending = cell
                    continue
                # a sense cell
                if pending:
                    combined = pending + root.lstrip("√")
                    w.writerow([root, pending, combined, cell, ""]); n_rows += 1
                    pending = None
                elif not base_written:
                    w.writerow([root, "", root, cell, count]); n_rows += 1
                    base_written = True
    print(f"wrote {OUT} — {n_roots} roots, {n_rows} sense rows")


if __name__ == "__main__":
    main()
