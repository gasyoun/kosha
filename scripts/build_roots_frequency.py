#!/usr/bin/env python
"""Roots frequency + attestation layer — roadmap Wave 2, W2b (H950).

REUSE/INTEGRATE, not greenfield: WhitneyRoots already owns the 935-root
explorer + quiz and already computes a per-root MW<->Whitney<->DCS
triangulation with corpus frequency and top attested forms
(WhitneyRoots/src/dcs_freq.json, built by WhitneyRoots/scripts/
root_triangulation.py from the canonical VisualDCS/src/DCS-data-2026/
dcs_full.sqlite ingest — SHARED_CODE.md's "one place this join happens").
This script does NOT re-derive that join. It adds the one thing missing
from WhitneyRoots's per-root JSON: the graded-curriculum framing (rank
order + cumulative coverage_pct) that turns "here is frequency data" into
"learn the top N roots and you can recognise X% of verb-token occurrences"
-- the same coverage-metric shape as the sandhi/vocabulary curricula
(ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md stage (2)). Stops at stage (6)
(data + export) -- no kosha roots UI; WhitneyRoots/Systema consume this.

Outputs:
  * data/roots/roots_frequency.tsv   rank . root_iast . dcs_lemma .
                                      grammar_class . dcs_status .
                                      attested_count . coverage_pct .
                                      top_attested_forms
  * data/roots/roots_frequency.json  same rows, structured, top_forms as
                                      [{form, n}, ...] (full fidelity)

Usage:
  python scripts/build_roots_frequency.py
"""
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "WhitneyRoots").exists() else ROOT.parent.parent
SOURCE = GH / "WhitneyRoots" / "src" / "dcs_freq.json"
OUT_TSV = ROOT / "data" / "roots" / "roots_frequency.tsv"
OUT_JSON = ROOT / "data" / "roots" / "roots_frequency.json"

# dcs_status values whose `total`/`top_forms` genuinely reflect attested corpus
# occurrences of THIS root (vs `unmatched`, which carries no DCS evidence at all).
ATTESTED_STATUSES = {"matched", "aliased", "homonym_shared"}


def load_source():
    if not SOURCE.exists():
        sys.exit(
            f"missing {SOURCE} -- this script reuses WhitneyRoots's canonical "
            f"MW<->Whitney<->DCS triangulation (scripts/root_triangulation.py); "
            f"regenerate it there first, do not re-derive the join here."
        )
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    return data["metadata"], data["entries"]


def group_by_lemma(entries):
    """Collapse Whitney roots onto one row per DCS lemma. Corpus tokens can't
    distinguish homonym roots that share a lemma (dcs_status=homonym_shared) --
    WhitneyRoots reports the SAME total/top_forms on every homonym sharing one
    lemma (verified: 74 groups, 162 roots, zero mismatched totals across a
    group). Summing those duplicates would inflate the coverage mass by
    however many homonyms happen to share a root string. One row per lemma,
    listing every root string that maps to it, counts the corpus mass once."""
    groups = {}
    for v in entries.values():
        if v["dcs_status"] not in ATTESTED_STATUSES or v["total"] <= 0:
            continue
        key = v["dcs_lemma"]
        g = groups.setdefault(key, {
            "roots": [], "total": v["total"], "top_forms": v["top_forms"],
            "grammar_classes": set(), "statuses": set(),
        })
        g["roots"].append(v["root"])
        g["grammar_classes"].update(v["grammar_class"])
        g["statuses"].add(v["dcs_status"])
    return groups


def build_rows(entries):
    groups = group_by_lemma(entries)
    ordered = sorted(groups.items(), key=lambda kv: (-kv[1]["total"], kv[0]))

    total_mass = sum(g["total"] for _, g in ordered)
    rows = []
    running = 0
    for i, (lemma, g) in enumerate(ordered, start=1):
        running += g["total"]
        coverage_pct = round(100.0 * running / total_mass, 4) if total_mass else 0.0
        status = "homonym_shared" if len(g["roots"]) > 1 else next(iter(g["statuses"]))
        rows.append({
            "rank": i,
            "root_iast": " / ".join(sorted(g["roots"])),
            "dcs_lemma": lemma,
            "grammar_class": ",".join(sorted(g["grammar_classes"])),
            "dcs_status": status,
            "attested_count": g["total"],
            "coverage_pct": coverage_pct,
            "top_forms": g["top_forms"],
        })
    return rows, total_mass


def write_tsv(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow([
            "rank", "root_iast", "dcs_lemma", "grammar_class", "dcs_status",
            "attested_count", "coverage_pct", "top_attested_forms",
        ])
        for r in rows:
            top_forms_str = "; ".join(f"{tf['form']}:{tf['n']}" for tf in r["top_forms"])
            w.writerow([
                r["rank"], r["root_iast"], r["dcs_lemma"], r["grammar_class"],
                r["dcs_status"], r["attested_count"], r["coverage_pct"], top_forms_str,
            ])


def write_json(rows, meta, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "source": "WhitneyRoots/src/dcs_freq.json (canonical MW<->Whitney<->DCS "
                       "triangulation, WhitneyRoots/scripts/root_triangulation.py)",
            "dcs_snapshot": meta.get("dcs_snapshot"),
            "generated_by": "kosha/scripts/build_roots_frequency.py",
            "hub_size": meta.get("total"),
            "n_ranked": len(rows),
            "excluded_unmatched": meta.get("unmatched", 0),
        },
        "roots": rows,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    meta, entries = load_source()
    rows, total_mass = build_rows(entries)
    write_tsv(rows, OUT_TSV)
    write_json(rows, meta, OUT_JSON)

    print(f"ranked {len(rows)} roots (excluded {meta.get('unmatched', 0)} DCS-unmatched, "
          f"hub size {meta.get('total')})")
    for n in (25, 50, 100, 200):
        if n <= len(rows):
            print(f"  learn top {n:>3} roots -> attested {rows[n - 1]['coverage_pct']:.1f}% "
                  f"of verb-token occurrences ({total_mass} total)")
    print(f"wrote {OUT_TSV}")
    print(f"wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
