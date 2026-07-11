"""Derive model-facing projections of the frozen H730 sample.

Two outputs (see docs/DEFGEN_WSD_EVAL_PROTOCOL_MW.md):
  defgen_inputs_v1.jsonl — GOLD-FREE projection for Track A generation agents
      (slp1, iast, grammar, attestation texts only). Generation agents read this
      file and never the frozen sample, so the gold answer key is structurally
      out of their context.
  wsd_subsample_v1.jsonl — Track B pilot: 100 polysemous headwords (sense_count
      >= 4), seed 731, one attestation each, with the numbered MW sense
      inventory (the inventory IS the task input there, not leakage).

Usage: python scripts/derive_defgen_inputs.py
"""
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parents[1] / "data" / "eval" / "defgen"
SAMPLE = BASE / "frozen_sample_v1.jsonl"
INPUTS = BASE / "defgen_inputs_v1.jsonl"
WSD = BASE / "wsd_subsample_v1.jsonl"
WSD_SEED = 731
WSD_N = 100
WSD_MIN_SENSES = 4


def main() -> None:
    rows = []
    with open(SAMPLE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    with open(INPUTS, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps({
                "slp1": r["slp1"],
                "iast": r["iast"],
                "grammar": r["grammar"],
                "attestations": [a["text"] for a in r["attestations"]],
            }, ensure_ascii=False) + "\n")
    print(f"inputs projection: {len(rows)} rows -> {INPUTS}")

    pool = sorted((r for r in rows if r["sense_count"] >= WSD_MIN_SENSES),
                  key=lambda r: r["slp1"])
    picked = random.Random(WSD_SEED).sample(pool, min(WSD_N, len(pool)))
    picked.sort(key=lambda r: r["slp1"])
    with open(WSD, "w", encoding="utf-8", newline="\n") as f:
        for r in picked:
            a = r["attestations"][0]
            f.write(json.dumps({
                "slp1": r["slp1"],
                "iast": r["iast"],
                "form": a["form"],
                "sentence": a["text"],
                "senses": {str(i + 1): s for i, s in enumerate(r["gold_senses"])},
            }, ensure_ascii=False) + "\n")
    print(f"wsd subsample: {len(picked)} rows (pool {len(pool)}) -> {WSD}")


if __name__ == "__main__":
    main()
