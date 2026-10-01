#!/usr/bin/env python
"""Route the Q3 morph give-back payload as the kosha-side queued port (A3 residual).

`triage_morph_giveback_candidates.py` (H3863, rebuilt H3975) resolved the
5,224-row candidate set mechanically: 4,900 rows are OWED to the csl-inflect
give-back (slot-conflict 2,212 — the generator fills the paradigm cell with a
different form; coverage-hole 2,688 — the cell is absent entirely), 323 are not
owed, 1 needs judgment. The triage report's hard stop says those 4,900 go to
the dual-engine give-back (H185) "as a queued port — a GTD row and a pointer,
never an in-pass edit to csl-inflect".

This builder IS that queued port, kosha-side. It writes, under
`data/concordance/giveback_port/`:

  csl_inflect_slot_conflicts.tsv   2,212 rows — every disagreement names BOTH
                                   forms (attested vs generator_has), so an
                                   upstream ruling is a comparison of two
                                   concrete forms, not a data dump;
  csl_inflect_coverage_holes.tsv   2,688 rows — generator_has is empty by
                                   construction (missing paradigm cell);
  ROUTING.json                     sha256-pinned provenance + counts + the
                                   diplomacy gate state.

Deliberately NOT done here: any write outside kosha. The upstream post is
human-gated (RELATIONS.md §2/§7 — humans send, agents draft); the drafted,
ready-to-post text lives beside the payloads as DRAFT_POST.md.

Deterministic: fixed sort (evidence_count desc, then form/cell), LF newlines,
no database, no network. Runtime is seconds — the expensive join is a
different script (analyze_morph_giveback_set.py).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "concordance"
TRIAGED = SRC / "morph_giveback_triaged.tsv"
SUMMARY = SRC / "morph_giveback_triage_summary.json"
OUT = SRC / "giveback_port"

OWED_VERDICTS = ("slot-conflict", "coverage-hole")
# Uniform payload schema — same columns in both files so a consumer diffs them
# without a remap. generator_has is "" for every coverage-hole row.
PAYLOAD_COLUMNS = [
    "attested_form",
    "dcs_lemma",
    "dcs_upos",
    "cell",
    "generator_has",
    "evidence_count",
    "target_locus",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def read_rows() -> list[dict]:
    with TRIAGED.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def write_payload(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=PAYLOAD_COLUMNS, delimiter="\t",
            lineterminator="\n", extrasaction="ignore",
        )
        w.writeheader()
        for r in rows:
            w.writerow({c: r[c] for c in PAYLOAD_COLUMNS})


def sort_key(r: dict):
    # Highest corpus weight first (how the report presents the set), then a
    # stable tiebreak so two runs agree byte-for-byte.
    return (-int(r["evidence_count"]), r["attested_form"], r["cell"])


def validate(rows: list[dict], summary: dict) -> list[dict]:
    verdicts = {}
    for r in rows:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    if verdicts != summary["verdicts"]:
        sys.exit(
            f"triage drift: file verdicts {verdicts} != summary {summary['verdicts']}"
        )
    owed = [r for r in rows if r["verdict"] in OWED_VERDICTS]
    expected_owed = summary["owed"]
    if len(owed) != expected_owed:
        sys.exit(f"owed mismatch: {len(owed)} != {expected_owed}")
    for r in owed:
        if not r["attested_form"] or not r["cell"]:
            sys.exit(f"owed row without form/cell: {r}")
        if r["verdict"] == "slot-conflict" and not r["generator_has"]:
            sys.exit(f"slot-conflict without the generator's competing form: {r}")
        if r["verdict"] == "coverage-hole" and r["generator_has"]:
            sys.exit(f"coverage-hole carrying a generator form: {r}")
    return sorted(owed, key=sort_key)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    rows = read_rows()
    if len(rows) != summary["total"]:
        sys.exit(f"row-count drift: file has {len(rows)}, summary says {summary['total']}")

    owed = validate(rows, summary)
    slots = [r for r in owed if r["verdict"] == "slot-conflict"]
    holes = [r for r in owed if r["verdict"] == "coverage-hole"]
    if len(slots) != summary["verdicts"]["slot-conflict"] or len(holes) != summary["verdicts"]["coverage-hole"]:
        sys.exit("payload split does not match the triage summary")

    OUT.mkdir(parents=True, exist_ok=True)
    slot_path = OUT / "csl_inflect_slot_conflicts.tsv"
    hole_path = OUT / "csl_inflect_coverage_holes.tsv"
    write_payload(slot_path, slots)
    write_payload(hole_path, holes)

    routing = {
        "built": date.today().strftime("%d-%m-%Y"),
        "builder": "scripts/build_giveback_port.py",
        "unit": "roadmap drain A02 (kosha CONCORDANCE_ROADMAP.md — give-back routing)",
        "source": {
            "triaged": {
                "path": "data/concordance/morph_giveback_triaged.tsv",
                "sha256": sha256_file(TRIAGED),
                "rows": len(rows),
            },
            "triage_summary": {
                "path": "data/concordance/morph_giveback_triage_summary.json",
                "sha256": sha256_file(SUMMARY),
            },
            "method": "data/concordance/MORPHOLOGY_GIVEBACK_TRIAGE_REPORT.md",
        },
        "owed_total": len(owed),
        "payloads": {
            "slot-conflicts": {
                "path": "data/concordance/giveback_port/csl_inflect_slot_conflicts.tsv",
                "rows": len(slots),
                "sha256": sha256_file(slot_path),
                "meaning": "generator fills the cell with a different form — both forms named (generator_has)",
            },
            "coverage-holes": {
                "path": "data/concordance/giveback_port/csl_inflect_coverage_holes.tsv",
                "rows": len(holes),
                "sha256": sha256_file(hole_path),
                "meaning": "paradigm cell absent from the generator entirely (generator_has empty)",
            },
        },
        "not_routed": {
            "not_owed": summary["not_owed"],
            "untagged_residue": summary["residue"],
            "note": "excluded classes are a dictionary-coverage/scope question, not an inflection bug; the single untagged row stays out until judged",
        },
        "destination": {
            "target": "csl-inflect (sanskrit-lexicon/csl-inflect), dual-engine give-back",
            "pattern": "H185 Task B — one on-its-merits message, never a batch",
            "gate": {
                "upstream_post": "HUMAN-GATED (RELATIONS.md §2/§7 — humans send, agents draft; no agent posts outward)",
                "draft": "data/concordance/giveback_port/DRAFT_POST.md",
            },
        },
        "licence": "CC BY-SA 4.0 (inherits the dataset's DCS-derived terms; DCS attribution carried by target_locus)",
        "join_back": "target_locus (dcs:<sent_id>) joins every payload row to morph_giveback_candidates.tsv and the KWIC evidence",
    }
    routing_path = OUT / "ROUTING.json"
    # newline="\n" pins LF bytes on every host — otherwise text-mode writes
    # smudge CRLF on Windows and a rebuild is not byte-reproducible.
    with routing_path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(routing, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    print(f"routed {len(owed)} owed rows: {len(slots)} slot-conflicts, {len(holes)} coverage-holes")
    print(f"excluded: {summary['not_owed']} not-owed, {summary['residue']} untagged")
    print(f"wrote {slot_path.name}, {hole_path.name}, ROUTING.json under {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
