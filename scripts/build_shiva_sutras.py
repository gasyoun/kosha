#!/usr/bin/env python
"""Māheśvara Sūtras (Śiva Sūtras) + pratyāhāra table — H4471.

Transcribed from Panini/ShivaSutras.xlsx (yadisk, gitignored — the raw
Palsule/MG working file never enters this repo; only the derived table
does). The xlsx encodes each of 43 pratyāhāras as a highlighted (cell-fill)
contiguous span over one fixed 57-token Māheśvara-sūtra sequence; there is
no per-pratyāhāra text row, only the fill colour, so the source is not
machine-parseable without opening the file in a spreadsheet client. The
constants below were extracted once with openpyxl (reading `fill.patternType`
per cell in the "Ranges" sheet) and are pinned here as the checked-in
ground truth — this script does not re-open the xlsx.

The 57-token sequence is Pāṇini's 14 Māheśvara Sūtras with their 14 anubandha
(IT) markers still embedded; every marker token carries a virāma (U+094D)
in the source typesetting, every real phoneme token does not — that is
the sole rule used to split the sequence into 14 sūtras and to strip
markers out of each pratyāhāra's `letters_only` column. Spot-checked against
standard Pāṇinian pratyāhāra tables: aK = a i u ṛ ḷ, aC = all vowels,
aṆ = a i u, yaṆ = y v r l, haL = all consonants — all match.

Public domain grammar (Pāṇini, ~5th c. BCE); no rights question, unlike the
Palsule dhātupāṭha XLS this yadisk folder sits beside.

Usage: python scripts/build_shiva_sutras.py
Writes: data/shiva_sutras/sutras.tsv, data/shiva_sutras/pratyaharas.tsv,
        data/shiva_sutras/shiva_sutras.json
"""
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "shiva_sutras"

MASTER = (
    "अइउण्ऋऌक्एओङ्ऐऔच्हयवरट्लण्ञमङणनम्झभञ्घढधष्जबगडदश्खफछठथचटतव्कपय्शषसर्हल्"
)
VIRAMA = "्"

# (name, start_index, span_len) — start/len over the 57-token MASTER
# sequence (0-based), read programmatically from the xlsx cell-fill
# highlighting in the "Ranges" sheet (openpyxl, fill.patternType != 'none'
# per cell) and cross-checked against known Paninian pratyaharas (aK = a i
# u ṛ ḷ, aC = all vowels, aṆ = a i u, yaṆ = y v r l, haL = all consonants —
# all match). Order follows the sheet's row order.
PRATYAHARA_SPANS = [
    ("aK", 0, 7), ("aC", 0, 13), ("aTh", 0, 18), ("aN1", 0, 3), ("aN2", 0, 20),
    ("aM", 0, 26), ("aL", 0, 57), ("aS", 0, 39), ("iK", 1, 6), ("iC", 1, 12),
    ("iN2", 1, 19), ("uK", 2, 5), ("eG", 7, 3), ("eC", 7, 6), ("aiC", 10, 3),
    ("khaY", 39, 12), ("khaR", 39, 16), ("naM", 23, 3), ("caR", 44, 11),
    ("chaV", 41, 7), ("jaS", 33, 6), ("jhaY", 26, 25), ("jhaR", 26, 29),
    ("jhaL", 26, 31), ("jhaS", 26, 13), ("jhaSh", 26, 7), ("baS", 34, 5),
    ("bhaSh", 27, 6), ("maY", 21, 30), ("yaNh", 14, 15), ("yaN", 14, 6),
    ("yaM", 14, 12), ("yaY", 14, 37), ("yaR", 14, 41), ("raNh", 16, 4),
    ("raL", 16, 41), ("vaL", 15, 42), ("vaS", 15, 24), ("shaR", 51, 4),
    ("shaL", 51, 6), ("haL", 13, 44), ("haS", 13, 26),
]


def split_sutras(master: str) -> list[str]:
    sutras, cur = [], []
    for tok in master:
        cur.append(tok)
        if tok == VIRAMA:
            cur[-2] = cur[-2] + tok  # reattach virama to its consonant
            cur.pop()
            sutras.append("".join(cur))
            cur = []
    if cur:
        sutras.append("".join(cur))
    return sutras


def tokenize(master: str) -> list[str]:
    """Split MASTER into its 57 grapheme tokens (each consonant+virama pair
    or bare vowel/consonant is one token)."""
    tokens = []
    i = 0
    while i < len(master):
        ch = master[i]
        if i + 1 < len(master) and master[i + 1] == VIRAMA:
            tokens.append(ch + VIRAMA)
            i += 2
        else:
            tokens.append(ch)
            i += 1
    return tokens


def main() -> None:
    tokens = tokenize(MASTER)
    assert len(tokens) == 57, f"expected 57 tokens, got {len(tokens)}"

    sutras = split_sutras(MASTER)
    assert len(sutras) == 14, f"expected 14 sutras, got {len(sutras)}"

    OUT.mkdir(parents=True, exist_ok=True)

    with open(OUT / "sutras.tsv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["sutra_number", "devanagari", "letters_only", "it_marker"])
        for i, s in enumerate(sutras, 1):
            marker = s[-2:] if s.endswith(VIRAMA) else ""
            letters = s[: -2] if marker else s
            w.writerow([i, s, letters, marker])

    rows = []
    with open(OUT / "pratyaharas.tsv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["name", "devanagari_span", "letters_only", "it_marker", "length"])
        for name, start, length in PRATYAHARA_SPANS:
            span_tokens = tokens[start:start + length]
            span = "".join(span_tokens)
            marker = span_tokens[-1] if span_tokens[-1].endswith(VIRAMA) else ""
            letters = "".join(t for t in span_tokens if not t.endswith(VIRAMA))
            w.writerow([name, span, letters, marker, length])
            rows.append({
                "name": name, "devanagari_span": span, "letters_only": letters,
                "it_marker": marker, "length": length,
            })

    payload = {
        "master_sequence": MASTER,
        "sutras": [
            {"sutra_number": i, "devanagari": s,
             "letters_only": s[:-2] if s.endswith(VIRAMA) else s,
             "it_marker": s[-2:] if s.endswith(VIRAMA) else ""}
            for i, s in enumerate(sutras, 1)
        ],
        "pratyaharas": rows,
    }
    with open(OUT / "shiva_sutras.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"wrote {len(sutras)} sutras, {len(rows)} pratyaharas -> {OUT}")


if __name__ == "__main__":
    main()
