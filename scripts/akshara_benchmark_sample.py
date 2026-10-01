#!/usr/bin/env python3
"""H3456 step 2 - stratified judge sample + packet files + chrF on all items.

Sampling: size-stratified (by max(chars_A, chars_B) quartiles), seed 730, n=40
LLM-judged fully; chrF computed on ALL benchmark items (objective secondary signal).
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "data" / "akshara_pilot" / "bench"
SEED = 730
N_JUDGED = 40


def chrf(reference: str, hypothesis: str, max_order: int = 6) -> float:
    """POPENCHR-style char F-score (chrF-6), 0..100."""

    def ngrams(s: str, n: int) -> Counter:
        return Counter(s[i:i + n] for i in range(len(s) - n + 1))

    ref = re.sub(r"\s+", " ", reference)
    hyp = re.sub(r"\s+", " ", hypothesis)
    prec_sum = rec_sum = 0.0
    for n in range(1, max_order + 1):
        r, h = ngrams(ref, n), ngrams(hyp, n)
        overlap = sum((r & h).values())
        nt_r, nt_h = sum(r.values()), sum(h.values())
        if nt_r == 0 or nt_h == 0:
            continue
        prec_sum += overlap / nt_h
        rec_sum += overlap / nt_r
    if prec_sum + rec_sum == 0:
        return 0.0
    # micro-averaged F (beta=2 favors recall, like sacrebleu chrF beta=2)
    p, r = prec_sum / 6, rec_sum / 6
    return 200 * p * r / (p + 2 * r)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rng = random.Random(SEED)
    items = [json.loads(l) for l in open(BENCH / "bench_items.jsonl", encoding="utf-8")]

    # chrF on all items (A vs B symmetric-ish: report both directions averaged)
    chrf_rows = []
    for it in items:
        f_ab = chrf(it["text_A"], it["text_B"])
        f_ba = chrf(it["text_B"], it["text_A"])
        chrf_rows.append({"item_id": it["item_id"], "headword": it["headword"],
                          "chrf_avg": round((f_ab + f_ba) / 2, 2)})
    (BENCH / "chrf_all.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in chrf_rows) + "\n",
        encoding="utf-8", newline="\n")

    # stratified judged sample by size quartile
    ranked = sorted(items, key=lambda x: max(x["chars_A"], x["chars_B"]))
    q = len(ranked) // 4
    buckets = [ranked[:q], ranked[q:2 * q], ranked[2 * q:3 * q], ranked[3 * q:]]
    per = N_JUDGED // 4
    sample = []
    for b in buckets:
        sample.extend(rng.sample(b, min(per, len(b))))
    sample.sort(key=lambda x: x["item_id"])

    pk_dir = BENCH / "judge_packets"
    pk_dir.mkdir(parents=True, exist_ok=True)
    per_file = 8
    for fi in range(0, len(sample), per_file):
        chunk = sample[fi:fi + per_file]
        parts = []
        for it in chunk:
            parts.append(
                f"## {it['item_id']} ({it['headword']})\n"
                f"[A {it['chars_A']} зн.{' ОБРЕЗАНО' if it['truncated_A'] else ''} | "
                f"B {it['chars_B']} зн.{' ОБРЕЗАНО' if it['truncated_B'] else ''}]\n"
                f"### ИСТОЧНИК (нем.)\n{it['source_de_cap6000']}\n"
                f"### Вариант A\n{it['text_A']}\n"
                f"### Вариант B\n{it['text_B']}\n")
        (pk_dir / f"pack_{fi // per_file + 1}.md").write_text(
            "\n".join(parts), encoding="utf-8", newline="\n")
    print(json.dumps({
        "judged_sample": [it["item_id"] for it in sample],
        "packets": sorted(p.name for p in pk_dir.glob("*.md")),
        "chrf_mean_all": round(sum(r["chrf_avg"] for r in chrf_rows) / len(chrf_rows), 2),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
