#!/usr/bin/env python
"""H4534 — DCS upasarga praefixus: prefixed-verb decomposition (MG 2014 workbook).

Source: yadisk `Sanskrityatina/05_Sanskrit-Lexicon/upasarga-stat/DCS-upasarga-analysis.xlsx`
(Dr. Mārcis Gasūns' own working workbook, file dated 28-09-2014), sheet `praefixus`,
6,425 data rows × 6 columns (dims confirmed by the H4477 yadisk census §5). The sheet
records, per prefixed verb form found in DCS, MG's decomposition into prefix + dhātu
and the match number into the Palsule root list (cross-validated against the
workbook's own `dhatu` sheet numbering).

Two prefix columns exist in the source and BOTH are kept, because they mean different
things: `prefix_guess` («Praefixus вообще какие бывают») is the naive allomorph-inventory
match — filled for only 38 rows and demonstrably wrong where it disagrees with the
resolved parse (e.g. `abhigā` → guess `prati`, resolved `abhi`); `prefix` («Praefixus»)
is the working parse, filled for 5,059 rows. 1,350 rows carry no prefix resolution at
all. `dhatu_check` duplicates `dhatu` in the source itself and agrees exactly in 100%
of rows — kept as MG's own integrity column.

The `dhatu` / `replace` / `Лист2` sheets (Palsule root lists, sandhi-normalization
pairs, prefix frequency tally) are NOT derived here — documented in the dataset note.

Derived-only: the xlsx stays on yadisk and is never committed. Fetch it read-only:

    rclone copy "yadisk:Sanskrityatina/05_Sanskrit-Lexicon/upasarga-stat/" \
        /tmp/h4534/ --include "DCS-upasarga-analysis.xlsx"

Usage: python scripts/extract_dcs_upasarga_prefixus.py --xlsx <path-to-xlsx>

Licence as sibling `sanskrit-upasarga-semantics`: CC BY-SA 4.0, credit Dr. Mārcis Gasūns.
"""
import argparse
import csv
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "upasarga" / "dcs_upasarga_prefixus.tsv"
GITA = ROOT / "data" / "gita" / "upasarga_semantics.tsv"

HEADER = ["in_form", "prefix_guess", "dhatu", "palsule_no", "prefix", "dhatu_check"]


def s(v):
    return "" if v is None else str(v).strip().replace("\t", " ").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True,
                    help="path to DCS-upasarga-analysis.xlsx (rclone copy from yadisk, see docstring)")
    ap.add_argument("--gita", default=str(GITA),
                    help="sibling Gita upasarga dataset for the join view (default: in-repo)")
    args = ap.parse_args()

    import openpyxl
    wb = openpyxl.load_workbook(args.xlsx, read_only=True, data_only=True)
    ws = wb["praefixus"]
    rows = list(ws.iter_rows(values_only=True))
    hdr, data = rows[0], rows[1:]
    if [s(h) for h in hdr[:4]] != ["IN", "Praefixus вообще какие бывают", "OUT DHATU",
                                   "Найдено соответствие с № в Palsule"]:
        sys.exit(f"FAIL: unexpected praefixus header: {[s(h) for h in hdr]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(HEADER)
        for r in data:
            cells = [s(r[i]) if len(r) > i else "" for i in range(6)]
            if not any(cells):
                continue  # fully blank source row
            w.writerow(cells)
            n += 1

    blob = OUT.read_bytes()
    sha = hashlib.sha256(blob).hexdigest()

    no_prefix = sum(1 for r in data
                    if not s(r[1] if len(r) > 1 else None)
                    and not s(r[4] if len(r) > 4 else None))
    print(f"rows written: {n}")
    print(f"rows with no prefix resolution (guess+resolved empty): {no_prefix}")
    print(f"out: {OUT}")
    print(f"sha256: {sha}")

    # Join view vs the sibling Gita compositional dataset (H4477 census §5: zero
    # SOURCE overlap — DCS dictionary dimension vs Gita.xlsm compositional dimension).
    gita = list(csv.DictReader(open(args.gita, encoding="utf-8"), delimiter="\t"))
    gk = {(r["root"].lstrip("√").strip().lower(), r["preverb"].rstrip("-").strip().lower())
          for r in gita if r.get("preverb")}
    pk = {(s(r[2]).lower(), s(r[4]).lower()) for r in data
          if len(r) > 4 and s(r[2]) and s(r[4])}
    shared = sorted(gk & pk)
    print(f"join view: praefixus resolved (dhatu,prefix) pairs: {len(pk)}; "
          f"gita (root,preverb) pairs: {len(gk)}; shared keys: {len(shared)}")
    for k in shared:
        print(f"  shared: {k[0]} + {k[1]}-")


if __name__ == "__main__":
    main()
