#!/usr/bin/env python
"""Extract the GOLD word-by-word Bhagavadgītā adhyāya 1 from the hand-curated
SanskritGrammar/Concordance/Gita.xlsm 'Grammar' sheet into a vendored TSV
(reading/data/sources/gita-1_gold_sanskritgrammar.tsv).

The xlsm is a local-only artifact (not committed in SanskritGrammar), so we
vendor the small chapter-1 slice into kosha for a reproducible build. Run once
(or when the workbook updates); the reading-pack builder consumes the TSV.

'Grammar' sheet columns (0-indexed): A=0 verse Devanagari (verse-initial only),
B=1 verse IAST (verse-initial only), C=2 pada Devanagari, D=3 pada IAST,
G=6 Russian gloss, H=7 chapter, I=8 verse-ref (e.g. '1.01'), J=9 word index,
K=10 English gloss, N=13 lemma (√root / compound-with-hyphens), O=14 root,
AB=27 morphology (e.g. '1n.1 m.', 'Perf. P 1v.1').

Usage: python scripts/extract_gita_gold.py --xlsm <path to Gita.xlsm>
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSM = ROOT.parent / "SanskritGrammar" / "Concordance" / "Gita.xlsm"
OUT = ROOT / "reading" / "data" / "sources" / "gita-1_gold_sanskritgrammar.tsv"

COLS = {"deva_v": 0, "iast_v": 1, "deva": 2, "form": 3, "gloss_ru": 6,
        "chapter": 7, "vref": 8, "widx": 9, "gloss_en": 10,
        "lemma": 13, "root": 14, "morph": 27}


def cell(r, key):
    v = r[COLS[key]]
    return "" if v is None else str(v).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsm", default=str(DEFAULT_XLSM))
    ap.add_argument("--chapter", default="1")
    args = ap.parse_args()

    import openpyxl
    wb = openpyxl.load_workbook(args.xlsm, read_only=True, data_only=True)
    ws = wb["Grammar"]

    header = [
        "# Bhagavadgītā adhyāya 1 — GOLD word-by-word analysis, 47 verses",
        "# Source: SanskritGrammar/Concordance/Gita.xlsm 'Grammar' sheet (hand-curated:",
        "#   lemma, root, morphology, English + Russian gloss per word). Vendored 13-07-2026 (H848).",
        "# Cols: vref\\twidx\\tform_iast\\tdeva\\tlemma_raw\\troot\\tmorph\\tgloss_en\\tgloss_ru\\tverse_iast\\tverse_deva",
        "# verse_iast/verse_deva populated only on each verse's first word-row.",
    ]
    lines = list(header)
    n = 0
    for r in ws.iter_rows(min_row=2, values_only=True):
        vref = cell(r, "vref")
        if not vref.startswith(args.chapter + "."):
            continue
        form = cell(r, "form")
        if not form and not cell(r, "lemma"):
            continue
        widx = cell(r, "widx")
        # col A/B carry the verse text only on the verse's FIRST word-row; on
        # later rows col A holds a Russian transcription (garbage here) — gate it.
        verse_iast = cell(r, "iast_v") if widx == "1" else ""
        verse_deva = cell(r, "deva_v") if widx == "1" else ""
        fields = [vref, widx, form, cell(r, "deva"),
                  cell(r, "lemma"), cell(r, "root"), cell(r, "morph"),
                  cell(r, "gloss_en"), cell(r, "gloss_ru"),
                  verse_iast, verse_deva]
        lines.append("\t".join(f.replace("\t", " ").replace("\n", " ") for f in fields))
        n += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT} — {n} word rows for chapter {args.chapter}")


if __name__ == "__main__":
    main()
