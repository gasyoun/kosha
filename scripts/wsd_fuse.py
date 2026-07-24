#!/usr/bin/env python
"""W3c — two-witness fusion + sense_frequency estimated rows (H1588).

Fusion rule (ARCHITECTURE_KOSHA_NEXT_PROGRAMME §4):
  - both witnesses agree → provenance=estimated, keep
  - disagree → drop from estimated, keep in review queue TSV
  - SCL absent / fail-closed → single-witness (MFS/LLM) with logged degradation;
    still requires held-out gate ≥70%

Writes:
  data/frequency/wsd_review_queue.tsv
  data/frequency/wsd_fusion_report.md
  appends provenance=estimated rows into sense_frequency.tsv (idempotent:
  strips prior estimated rows first)

  python scripts/wsd_fuse.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wsd_core import (  # noqa: E402
    CACHE_DIR,
    FREQ,
    GATE_THRESHOLD,
    MODEL_PROV,
    SCL_CACHE,
    SENSE_FREQ,
    load_tsv,
)

OUT_REVIEW = os.path.join(FREQ, "wsd_review_queue.tsv")
OUT_REPORT = os.path.join(FREQ, "wsd_fusion_report.md")
OUT_EVAL = os.path.join(FREQ, "wsd_heldout_eval.json")
OUT_UNTAGGED = os.path.join(FREQ, "wsd_untagged_mfs_counts.tsv")
REASON_PATH = os.path.join(CACHE_DIR, "scl_witness_reason.json")


def load_scl_labels() -> dict[str, str]:
    """lemma_slp1 → scl sense label (minimal). Empty if cache missing/empty."""
    out: dict[str, str] = {}
    if not os.path.exists(SCL_CACHE):
        return out
    with open(SCL_CACHE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            lemma = o.get("lemma_slp1") or o.get("lemma")
            lab = o.get("scl_sense_id") or o.get("label") or o.get("sense_id")
            if lemma and lab:
                out[str(lemma)] = str(lab)
    return out


def strip_estimated(rows: list[dict]) -> list[dict]:
    return [r for r in rows if (r.get("provenance") or "attested") != "estimated"]


def empty_genre_fields() -> dict:
    return {
        "n_texts": "0",
        "dispersion_dp": "",
        "largest_text_share": "",
        "count_adj": "",
        "sense_rank_adj": "",
        "count_bal_uniform": "",
        "sense_rank_bal": "",
        "count_nonsastra": "",
        "sense_rank_nonsastra": "",
        "top_genre": "",
        "top_genre_share": "",
        "periods": "",
    }


def main() -> int:
    if not os.path.exists(OUT_EVAL):
        sys.exit(f"MISSING eval — run wsd_llm_arm.py first: {OUT_EVAL}")
    if not os.path.exists(OUT_UNTAGGED):
        sys.exit(f"MISSING untagged counts: {OUT_UNTAGGED}")
    if not os.path.exists(SENSE_FREQ):
        sys.exit(f"MISSING {SENSE_FREQ}")

    with open(OUT_EVAL, encoding="utf-8") as f:
        eval_blob = json.load(f)
    ev = eval_blob.get("eval") or {}
    acc = float(ev.get("accuracy") or 0)
    gate_pass = bool(ev.get("gate_pass")) and acc >= GATE_THRESHOLD

    scl = load_scl_labels()
    scl_reason = {}
    if os.path.exists(REASON_PATH):
        with open(REASON_PATH, encoding="utf-8") as f:
            scl_reason = json.load(f)
    single_witness = len(scl) == 0
    degradation = (
        "single-witness MFS (SCL cache empty / H057 rights fail-closed)"
        if single_witness
        else "two-witness SCL+MFS"
    )

    arm_rows = load_tsv(OUT_UNTAGGED)
    review: list[dict] = []
    fused: list[dict] = []

    for r in arm_rows:
        lemma = r["lemma_slp1"]
        sense = r["sense_id"]
        if not single_witness:
            scl_lab = scl.get(lemma)
            # SCL labels are free-form; require explicit equality or documented
            # absence of a per-lemma label → treat missing as non-vote (keep arm).
            if scl_lab is not None and scl_lab != sense and scl_lab != sense.split("#")[-1]:
                review.append(
                    {
                        "lemma_slp1": lemma,
                        "arm_sense_id": sense,
                        "scl_sense_id": scl_lab,
                        "count_estimated": r.get("count_estimated", ""),
                        "reason": "witness_disagree",
                    }
                )
                continue
        if not gate_pass:
            review.append(
                {
                    "lemma_slp1": lemma,
                    "arm_sense_id": sense,
                    "scl_sense_id": scl.get(lemma, ""),
                    "count_estimated": r.get("count_estimated", ""),
                    "reason": f"gate_fail_acc={acc}",
                }
            )
            continue
        fused.append(r)

    # Rebuild sense_frequency: attested rows + estimated mw rows
    existing = load_tsv(SENSE_FREQ)
    cols = list(existing[0].keys()) if existing else []
    if "provenance" not in cols:
        sys.exit("sense_frequency.tsv missing provenance column")
    base = strip_estimated(existing)

    new_rows = []
    if gate_pass:
        for r in fused:
            row = {c: "" for c in cols}
            row.update(empty_genre_fields())
            row["lemma_slp1"] = r["lemma_slp1"]
            row["layer"] = "mw"
            row["sense_id"] = r["sense_id"]
            row["sense_gloss"] = r.get("sense_gloss") or ""
            row["count_all"] = r.get("count_estimated") or "0"
            row["sense_rank"] = "1"
            row["lemma_share"] = ""  # estimated mass is not a share of gold
            row["provenance"] = "estimated"
            row["confidence"] = r.get("confidence") or ""
            new_rows.append(row)

    out_all = base + new_rows
    with open(SENSE_FREQ, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in out_all:
            w.writerow({c: r.get(c, "") for c in cols})

    rev_cols = [
        "lemma_slp1",
        "arm_sense_id",
        "scl_sense_id",
        "count_estimated",
        "reason",
    ]
    with open(OUT_REVIEW, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rev_cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in review:
            w.writerow({c: r.get(c, "") for c in rev_cols})

    # Explicit empty-with-reason when review is empty (acceptance 3-5)
    empty_reason = ""
    if not review:
        empty_reason = (
            "empty because gate_pass and single-witness MFS: no SCL labels to disagree with"
            if single_witness and gate_pass
            else "empty: no fused candidates or all promoted"
        )

    n_est_tok = sum(int(r.get("count_estimated") or 0) for r in fused)
    report = f"""# WSD fusion report (H1588)

_Created: 24-07-2026 · Last updated: 24-07-2026_

**Model:** {MODEL_PROV} · **Handoff:** H1588 (Opus-lock override)

## Gate

| Metric | Value |
|---|---|
| Method | `{ev.get("method", "mfs")}` |
| Held-out accuracy | **{acc:.4f}** (threshold {GATE_THRESHOLD}) |
| Gate pass | **{"YES" if gate_pass else "NO"}** |
| Test scored | {ev.get("n_test_scored")} |
| Correct | {ev.get("n_correct")} |
| WordSem mapped (exact\\|overlap) | {ev.get("n_mapped_exact_overlap")} |
| Degradation | {degradation} |

## SCL witness

| Field | Value |
|---|---|
| Labels in cache | {len(scl)} |
| Status | {(scl_reason or {}).get("status", "no reason file")} |
| Reason | {(scl_reason or {}).get("reason", "—")} |

## Fusion

| Outcome | N |
|---|---|
| Promoted estimated lemma-rows | {len(fused)} |
| Estimated tokens (sum count_all) | {n_est_tok} |
| Review-queue rows | {len(review)} |
| Attested rows retained | {len(base)} |
| Total sense_frequency rows | {len(out_all)} |

Review queue empty reason: {empty_reason or "n/a (queue non-empty)"}

## Honesty

- Estimated counts are **MFS mass on untagged DCS tokens** (no WordSem), not blended into attested.
- Cards must show a separate estimated chip (W3d).
- SCL body text was never written to the tree (gitignore fence).

_Dr. Mārcis Gasūns_
"""
    with open(OUT_REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write(report)

    # meta touch
    meta_path = os.path.join(FREQ, "sense_frequency.meta.json")
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        meta["wsd_wave3_h1588"] = {
            "model": MODEL_PROV,
            "gate_pass": gate_pass,
            "accuracy": acc,
            "degradation": degradation,
            "estimated_rows": len(new_rows),
            "estimated_tokens": n_est_tok,
            "review_rows": len(review),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        meta["rows"] = len(out_all)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
            f.write("\n")

    print(f"gate_pass={gate_pass} acc={acc} estimated_rows={len(new_rows)} review={len(review)}")
    print("wrote", SENSE_FREQ)
    print("wrote", OUT_REVIEW)
    print("wrote", OUT_REPORT)
    return 0 if gate_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
