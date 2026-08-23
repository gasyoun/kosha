#!/usr/bin/env python
"""H3167 evidence: 15-row hand spot-check of the subhashita-beginner pack's
gloss_ru triples. Read-only — samples tokens with a populated gloss_ru and
prints (surface, lemma_slp1, gloss_ru) for human/agent review against the
token's actual sense. Not part of the build chain."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
pack = json.loads((ROOT / "data" / "subhashita" / "subhashita_beginner_pack.json").read_text(encoding="utf-8"))

rows = []
for s in pack["sayings"]:
    for ln in s["lines"]:
        for ch in ln["chunks"]:
            for tok, lem, rg in zip(ch["t"], ch["lemma_slp1"], ch["gloss_ru"]):
                if rg:
                    rows.append((s["num"], tok, lem, rg))

# evenly spaced sample across the pack for spread, not just the first N
step = max(1, len(rows) // 15)
sample = rows[::step][:15]

for num, tok, lem, rg in sample:
    print(f"saying#{num}\tsurface={tok}\tlemma={lem}\tgloss_ru={json.dumps(rg, ensure_ascii=False)}")
