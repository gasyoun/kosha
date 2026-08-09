#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""defgen_heritage_manifest_row.py — H2408: register the Heritage second-reference
eval artifacts in data/manifest/datasets.json (org rule: new derived dataset ⇒
manifest row in the same pass).

Idempotent: re-running replaces the existing row instead of appending a duplicate.
Rows/size are measured from the committed files, not hardcoded.
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MANIFEST = os.path.join(REPO, "data", "manifest", "datasets.json")
OUT = os.path.join(REPO, "data", "eval", "defgen", "heritage")
DATASET_ID = "defgen-heritage-second-reference"


def main():
    files = sorted(f for f in os.listdir(OUT) if not f.startswith("."))
    size = sum(os.path.getsize(os.path.join(OUT, f)) for f in files)
    n_rows = 0
    for f in files:
        if f.endswith(".jsonl") or f.endswith(".tsv"):
            with io.open(os.path.join(OUT, f), encoding="utf-8") as fh:
                n_rows += sum(1 for _ in fh)

    row = {
        "id": DATASET_ID,
        "title": ("Definition-generation eval: Heritage (Huet) French glosses as an "
                  "independent second reference (H2408)"),
        "tier": "public",
        "in_release": "not-applicable",
        "format": "tsv + jsonl + json",
        "rows": n_rows,
        "size_bytes": size,
        "keying": ("heritage_ref_subset.tsv (slp1 -> DICO anchor + gloss SHA-256 + word "
                   "count; NO gloss text) · judge_fr_<arm>.jsonl (slp1 -> cross-lingual "
                   "adequacy 0-5, 5 arms x 333) · heritage_ref_per_item.tsv (arm x slp1 -> "
                   "chrF vs MW/FR/multi-ref + token-F1) · heritage_ref_scores.json "
                   "(summary, gates, paired MW-FR premium with bootstrap CI)"),
        "source_repo": "https://github.com/gasyoun/kosha",
        "source_path": "data/eval/defgen/heritage/",
        "builder": ("scripts/defgen_heritage_ref.py (build/metrics/judge/report) + "
                    "defgen_heritage_delta.py + defgen_heritage_coverage.py, H2408, "
                    "Fable 5 (claude-fable-5) 09-08-2026"),
        "consumers": [
            ("docs/DEFGEN_HERITAGE_SECOND_REFERENCE_EVAL.md (report of record: "
             "reference-invariant arm ranking + MW-familiarity premium +0.13..+0.25)"),
            ("docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md next-step #4 (closed by this "
             "dataset)"),
        ],
        "notes": ("PUBLIC tier despite consuming the restricted Heritage layer (D20, "
                  "LGPLLR, heritage-dico-gloss): gloss TEXT is deliberately never copied "
                  "into kosha — the subset carries mw_key1 + DICO anchor + SHA-256 + word "
                  "count, and defgen_heritage_ref.py REFUSES to score if any digest stops "
                  "matching the local SanskritLexicography file. Reproduction therefore "
                  "requires that sibling checkout. Derived from the frozen 500-headword MW "
                  "sample (seed 730, H730) intersected with Heritage = 333 items; the "
                  "subset is high-frequency-skewed by Heritage coverage, so its numbers are "
                  "not comparable to the published 500-item table."),
        "data_statement": "docs/DEFGEN_HERITAGE_SECOND_REFERENCE_EVAL.md",
    }

    with io.open(MANIFEST, encoding="utf-8") as f:
        man = json.load(f)
    ds = man["datasets"]
    for i, existing in enumerate(ds):
        if existing.get("id") == DATASET_ID:
            ds[i] = row
            action = "replaced"
            break
    else:
        ds.append(row)
        action = "appended"
    with io.open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("%s %s: rows=%d size=%d files=%d" % (action, DATASET_ID, n_rows, size, len(files)))


if __name__ == "__main__":
    main()
