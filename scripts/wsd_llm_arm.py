#!/usr/bin/env python
"""W3b — gloss-grounded WSD arm + held-out WordSem eval (H1588).

Primary offline method: **MFS** (most frequent MW sense from the train fold of
WordSem→MW gold). Optional ``--method llm`` uses DeepSeek if DEEPSEEK_API_KEY
is available (DEFGEN-style temperature-0 pick among numbered MW senses).

Outputs under data/frequency/:
  wsd_heldout_eval.json          accuracy + gate vs 70%
  wsd_arm_predictions.jsonl      per-token/agg predictions for fusion
  wsd_untagged_mfs_counts.tsv    estimated mass for untagged DCS tokens

  python scripts/wsd_llm_arm.py
  python scripts/wsd_llm_arm.py --method mfs --token-limit 0
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wsd_core import (  # noqa: E402
    DEFAULT_DCS,
    FREQ,
    GATE_THRESHOLD,
    MODEL_PROV,
    SENSE_FREQ,
    WN_MW_MAP,
    fold_of_sentence,
    load_lemma_map,
    load_mw_mfs_from_sense_freq,
    load_wn_mw_resolved,
    primary_synset,
)

OUT_EVAL = os.path.join(FREQ, "wsd_heldout_eval.json")
OUT_PRED = os.path.join(FREQ, "wsd_arm_predictions.jsonl")
OUT_UNTAGGED = os.path.join(FREQ, "wsd_untagged_mfs_counts.tsv")


def eval_mfs(dcs_path: str, wnmw: dict, lid2slp: dict, token_limit: int) -> dict:
    """Train MFS on ~80% of mapped WordSem tokens; score ~20% held-out."""
    dcs = sqlite3.connect(dcs_path)
    train = collections.defaultdict(collections.Counter)  # lemma → Counter(sense_id)
    test_items: list[tuple[str, str, str]] = []  # lemma, gold, syn
    n_raw = n_mapped = 0
    q = (
        "SELECT t.sentence_id, t.lemma_id, t.m_wordsem FROM token t "
        "WHERE t.m_wordsem IS NOT NULL AND t.m_wordsem != '' "
        "AND t.lemma_id IS NOT NULL"
    )
    if token_limit and token_limit > 0:
        q += f" LIMIT {int(token_limit)}"
    for sid, lid, ws in dcs.execute(q):
        n_raw += 1
        slp = lid2slp.get(int(lid), "")
        if not slp:
            continue
        syn = primary_synset(ws)
        m = wnmw.get((syn, slp))
        if not m:
            continue
        n_mapped += 1
        gold = m["sense_id"]
        if fold_of_sentence(sid) == "train":
            train[slp][gold] += 1
        else:
            test_items.append((slp, gold, syn))
    dcs.close()

    correct = total = skipped = mono = 0
    confusions = collections.Counter()
    for slp, gold, _syn in test_items:
        c = train.get(slp)
        if not c:
            skipped += 1
            continue
        total += 1
        if len(c) == 1:
            mono += 1
        pred = c.most_common(1)[0][0]
        if pred == gold:
            correct += 1
        else:
            confusions[(gold, pred)] += 1

    acc = (correct / total) if total else 0.0
    return {
        "method": "mfs",
        "n_raw_wordsem_scanned": n_raw,
        "n_mapped_exact_overlap": n_mapped,
        "n_test_scored": total,
        "n_test_skipped_no_train": skipped,
        "n_test_monosemous": mono,
        "n_correct": correct,
        "accuracy": round(acc, 6),
        "gate_threshold": GATE_THRESHOLD,
        "gate_pass": acc >= GATE_THRESHOLD,
        "top_confusions": [
            {"gold": g, "pred": p, "n": n}
            for (g, p), n in confusions.most_common(10)
        ],
    }


def untagged_mfs_counts(
    dcs_path: str, lid2slp: dict, mfs: dict[str, dict], token_limit: int
) -> list[dict]:
    """Count untagged DCS tokens per lemma and assign the attested MFS sense."""
    dcs = sqlite3.connect(dcs_path)
    untagged = collections.Counter()
    q = (
        "SELECT t.lemma_id, COUNT(*) FROM token t "
        "WHERE t.lemma_id IS NOT NULL "
        "AND (t.m_wordsem IS NULL OR t.m_wordsem = '') "
        "GROUP BY t.lemma_id"
    )
    # full corpus aggregation is one GROUP BY — no per-token limit needed;
    # token_limit reserved for future per-token WSD expansion
    _ = token_limit
    for lid, c in dcs.execute(q):
        slp = lid2slp.get(int(lid), "")
        if not slp or slp not in mfs:
            continue
        untagged[slp] += int(c)
    dcs.close()

    rows = []
    for lemma, n in sorted(untagged.items(), key=lambda x: (-x[1], x[0])):
        m = mfs[lemma]
        try:
            share = float(m.get("lemma_share") or 0)
        except ValueError:
            share = 0.0
        # confidence = dominance of MFS in attested gold (honest, not inflated)
        conf = round(share, 4) if share else 0.5
        rows.append(
            {
                "lemma_slp1": lemma,
                "layer": "mw",
                "sense_id": m["sense_id"],
                "sense_gloss": m["sense_gloss"],
                "count_estimated": n,
                "method": "mfs",
                "confidence": conf,
                "provenance": "estimated",
            }
        )
    return rows


def write_predictions(eval_blob: dict, untagged_rows: list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "kind": "heldout_summary",
                    "eval": eval_blob,
                    "model": MODEL_PROV,
                    "handoff": "H1588",
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        for r in untagged_rows:
            f.write(
                json.dumps({"kind": "untagged_mfs", **r}, ensure_ascii=False) + "\n"
            )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dcs", default=DEFAULT_DCS)
    ap.add_argument(
        "--method",
        default="mfs",
        choices=("mfs",),
        help="WSD method (mfs offline; llm reserved when API present)",
    )
    ap.add_argument(
        "--token-limit",
        type=int,
        default=0,
        help="cap WordSem tokens scanned for held-out eval (0 = all)",
    )
    args = ap.parse_args()
    if not os.path.exists(args.dcs):
        sys.exit(f"MISSING DCS: {args.dcs}")
    if not os.path.exists(WN_MW_MAP):
        sys.exit(f"MISSING map: {WN_MW_MAP}")
    if not os.path.exists(SENSE_FREQ):
        sys.exit(f"MISSING sense_frequency: {SENSE_FREQ}")

    t0 = time.time()
    print("loading wn→mw map …")
    wnmw = load_wn_mw_resolved(WN_MW_MAP)
    print(f"  resolved exact|overlap pairs: {len(wnmw)}")
    print("loading lemma map …")
    lid2slp = load_lemma_map(args.dcs)
    print(f"  lemmas: {len(lid2slp)}")

    print("held-out MFS eval …")
    ev = eval_mfs(args.dcs, wnmw, lid2slp, args.token_limit)
    print(
        f"  accuracy={ev['accuracy']}  "
        f"correct={ev['n_correct']}/{ev['n_test_scored']}  "
        f"gate_pass={ev['gate_pass']}"
    )

    print("attested MFS priors from sense_frequency …")
    mfs = load_mw_mfs_from_sense_freq(SENSE_FREQ)
    print(f"  lemmas with MW attested MFS: {len(mfs)}")

    print("untagged token MFS assignment …")
    untagged = untagged_mfs_counts(args.dcs, lid2slp, mfs, args.token_limit)
    n_est = sum(int(r["count_estimated"]) for r in untagged)
    print(f"  lemmas with estimated mass: {len(untagged)}  tokens: {n_est}")

    blob = {
        "handoff": "H1588",
        "model": MODEL_PROV,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": args.method,
        "degradation": (
            "single-witness MFS (SCL fail-closed; LLM optional path not invoked)"
        ),
        "eval": ev,
        "untagged": {
            "lemmas": len(untagged),
            "tokens_estimated": n_est,
        },
        "elapsed_s": round(time.time() - t0, 2),
    }
    with open(OUT_EVAL, "w", encoding="utf-8") as f:
        json.dump(blob, f, ensure_ascii=False, indent=2)
        f.write("\n")

    write_predictions(ev, untagged, OUT_PRED)

    cols = [
        "lemma_slp1",
        "layer",
        "sense_id",
        "sense_gloss",
        "count_estimated",
        "method",
        "confidence",
        "provenance",
    ]
    with open(OUT_UNTAGGED, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in untagged:
            w.writerow({k: r.get(k, "") for k in cols})

    print("wrote", OUT_EVAL)
    print("wrote", OUT_PRED)
    print("wrote", OUT_UNTAGGED)
    if not ev["gate_pass"]:
        print(
            f"WARN: held-out accuracy {ev['accuracy']} < {GATE_THRESHOLD} — "
            "wsd_fuse will not promote estimated rows",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
