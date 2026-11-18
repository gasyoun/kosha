#!/usr/bin/env python3
"""Register the H6253 article-generation eval dataset in data/manifest/datasets.json.

Idempotent (replaces the existing row); counts and bytes measured from committed
files, never hardcoded.
"""
import io
import json
import os
import sys
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MANIFEST = os.path.join(REPO, "data", "manifest", "datasets.json")
OUT = os.path.join(REPO, "data", "eval", "articlegen")
DATASET_ID = "articlegen-cologne-gold"


def main():
    files = sorted(f for f in os.listdir(OUT) if not f.startswith("."))
    size = sum(os.path.getsize(os.path.join(OUT, f)) for f in files)
    rows = 0
    for f in files:
        if f.endswith((".jsonl", ".tsv")):
            with io.open(os.path.join(OUT, f), encoding="utf-8") as fh:
                rows += sum(1 for _ in fh)
    with io.open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    row = {
        "id": DATASET_ID,
        "title": "LLM article generation vs Cologne MW gold — 105-headword eval + hallucination taxonomy (H6253)",
        "tier": "public",
        "in_release": "not-applicable",
        "format": "tsv + jsonl + json + txt",
        "rows": rows,
        "size_bytes": size,
        "keying": ("sample.tsv: 105 A55-union keys (100 main + 5 MG canary), seed 6253, "
                   "gold examples/citations from Cologne MW v02; citation_inventory.json: "
                   "38,672 unique <ls> abbreviations; gen_<arm>.jsonl: per-arm generated "
                   "articles; scores_per_item.tsv + scores_summary.json + "
                   "hallucination_taxonomy.tsv + REPORT.md"),
        "source_repo": "https://github.com/gasyoun/kosha",
        "source_path": "data/eval/articlegen/",
        "builder": ("scripts/articlegen_build.py + articlegen_score.py + "
                    "articlegen_manifest_row.py, H6253, "
                    "Hy4 flash Free (opencode-go/hy4-flash-free), " + date.today().isoformat()),
        "consumers": [
            "docs/ARTICLEGEN_COLOGNE_EVAL_PROTOCOL.md (protocol + results of record)",
            "Uprava H6253 (originating handoff)",
        ],
        "notes": ("Canary split of 5 headwords awaits MG manual gold labels: verdict "
                  "INCONCLUSIVE until canary/mg_labels.tsv is filled and "
                  "articlegen_score.py --canary reproduces >=80% of 30 decisions. "
                  "Raw model transcripts retained under raw/ for audit; MW 1899 is "
                  "public domain, so numbers measure reproduction + grounding, not "
                  "generation from evidence alone."),
    }
    ds = manifest["datasets"]
    replaced = False
    for i, existing in enumerate(ds):
        if existing.get("id") == DATASET_ID:
            ds[i] = row
            replaced = True
            break
    if not replaced:
        ds.append(row)
    with io.open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(json.dumps({"id": DATASET_ID, "rows": rows, "size_bytes": size,
                      "operation": "replace" if replaced else "append"}, indent=2))


if __name__ == "__main__":
    main()
