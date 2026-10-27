#!/usr/bin/env python
"""SandhiKosh (LREC-2018 benchmark) xls workbooks → committed TSV — H6841 / WHEEL9 item (a).

Source: github.com/sanskrit-sandhi/SandhiKosh — first (and only) public Sanskrit
sandhi benchmark, upstream static since 2020-01-30 (commit b4938f82982a3217899fb554bbc093fab3a6b85b),
NO license file (README: "provided ... free of cost for research purposes only").
License-gated-ingest discipline (H6841): raw xls mirror stays OUT of git; the
derived TSV layer is what gets committed, with full provenance in
data/sandhi/sandhikosh/README.md.

Sheets → TSV (id, word, split, rule, type, source):
  UoH_Corpus.xls / Sheet1                                  → uoh.tsv
  Astaadhyaayii Corpus.xls / Sheet1                         → astadhyayii.tsv
  Bhagvad_Gita Corpus.xls / Sheet1                          → bhagvad_gita.tsv
  Rule-based Corpus and Literature Corpus.xls / Internal   → rule_internal.tsv
  Rule-based Corpus and Literature Corpus.xls / External   → rule_external.tsv
  Rule-based Corpus and Literature Corpus.xls / Literature → rule_literature.tsv

Deterministic and idempotent: same workbooks → byte-identical TSVs.
Usage:
  pip install xlrd
  python tools/sandhikosh_xls_to_tsv.py --src <dir-with-xls> [--out data/sandhi/sandhikosh]
"""
import argparse
import json
import sys
import unicodedata
from pathlib import Path

import xlrd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "sandhi" / "sandhikosh"

HEADER = ["id", "word", "split", "rule", "type", "source"]

# (workbook, sheet, header-row index, default type when sheet lacks a Type col)
SOURCES = [
    ("UoH_Corpus.xls", "uoh", 0),
    ("Astaadhyaayii Corpus.xls", "astaadhyayii", 0),
    ("Bhagvad_Gita Corpus.xls", "bhagvad_gita", 0),
    ("Rule-based Corpus and Literature Corpus.xls", "rule_internal", 1),
    ("Rule-based Corpus and Literature Corpus.xls", "rule_external", 1),
    ("Rule-based Corpus and Literature Corpus.xls", "rule_literature", 0),
]


def norm_cell(v):
    """Normalize one cell: NFC + collapse whitespace; None for empty."""
    s = unicodedata.normalize("NFC", str(v)).strip()
    return s if s else None


def num_rule(v):
    """Rule column: numeric 1.0 → '1'; text ('11001.0' in S.No vs '11001.0') stays."""
    s = norm_cell(v)
    if s is None:
        return s
    try:
        f = float(s)
        return str(int(f))
    except ValueError:
        return s


def convert(src_dir: Path, out_dir: Path):
    src_dir = Path(src_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for wb_name, out_stem, hdr_row in SOURCES:
        wb = xlrd.open_workbook(src_dir / wb_name)
        sheet_map = {sh.name: sh for sh in wb.sheets()
                     if len(wb.sheets()) == 1 or sh.name.startswith(("Internal", "External", "Literature"))}
        sh = list(sheet_map.values())[0]
        if out_stem == "rule_internal":
            sh = next(s for s in wb.sheets() if s.name == "Internal")
        elif out_stem == "rule_external":
            sh = next(s for s in wb.sheets() if s.name == "External")
        elif out_stem == "rule_literature":
            sh = next(s for s in wb.sheets() if s.name == "Literature")
        # locate columns from the header row
        names = [norm_cell(sh.cell_value(hdr_row, c)) for c in range(sh.ncols)]
        names = [(n or "").lower() for n in names]
        col = {k.lower(): i for i, k in enumerate(names) if k}
        idc = next(i for i, n in enumerate(names) if n in ("s.no", "s. no."))
        wc = next(i for i, n in enumerate(names) if n == "word")
        sc = next(i for i, n in enumerate(names) if n == "split")
        rc = names.index("rule") if "rule" in names else None
        tc = names.index("type") if "type" in names else None
        rows = []
        skipped = 0
        for r in range(hdr_row + 1, sh.nrows):
            wid = norm_cell(sh.cell_value(r, idc))
            word = norm_cell(sh.cell_value(r, wc))
            split = norm_cell(sh.cell_value(r, sc))
            if not word or not split:
                if any(norm_cell(sh.cell_value(r, c)) for c in range(sh.ncols)):
                    skipped += 1
                continue
            rule = num_rule(sh.cell_value(r, rc)) if rc is not None else None
            typ = norm_cell(sh.cell_value(r, tc)) if tc is not None else None
            rows.append([wid or "", word, split, rule or "", typ or "", out_stem])
        out = out_dir / f"{out_stem}.tsv"
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\t".join(HEADER) + "\n")
            for row in rows:
                fh.write("\t".join(row) + "\n")
        summary[out_stem] = {"rows": len(rows), "skipped": skipped, "file": out.name}
    with open(out_dir / "convert_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default=str(OUT_DIR))
    a = ap.parse_args()
    summary = convert(Path(a.src), Path(a.out))
    print("OK", json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())