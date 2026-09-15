#!/usr/bin/env python3
"""Build the kosha dataset-disciplines packet (H4737): the join of the kosha
dataset registry through the estate's ratified meso->discipline crosswalk.

H3567 ruling F5 consumer leg (kosha half), released by ruling F5c (MG,
29-08-2026). The crosswalk is OWNED by IndologyScholars
(curation/meso_discipline_crosswalk.csv + curation/disciplines.csv) and
consumed here read-only from the sibling checkout — the discipline taxonomy is
never re-derived kosha-side, and keyword_filtering.py is never used. kosha
contributes only the dataset -> meso_code assignment layer
(data/manifest/dataset_meso_assignments.json), a reviewed seed mirroring the
csl-atlas precedent (H4178 flip 3).

Emits (committed):
  - data/disciplines/dataset_disciplines.json: per-dataset disciplines
    (confidence = assignment x crosswalk, capped at 1), per-discipline
    coverage summary, the crosswalk's deliberate NOT-MAPPED sentinel rows.
  - data/disciplines/dataset_disciplines.source.json: provenance pin.

--check: rebuild the payload and compare against the committed one (byte
determinism: the payload carries no timestamps — only the .source.json
envelope does), plus internal invariants. When the sibling checkout is
absent, --check degrades to internal-consistency-only so CI stays green
(the committed packet carries the feedCommit pin either way).

Usage: python3 scripts/build_dataset_disciplines.py [--check]
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIBLING_ROOT = ROOT.parent / "IndologyScholars"
CROSSWALK_PATH = SIBLING_ROOT / "curation" / "meso_discipline_crosswalk.csv"
DISCIPLINES_PATH = SIBLING_ROOT / "curation" / "disciplines.csv"
MANIFEST_PATH = ROOT / "data" / "manifest" / "datasets.json"
ASSIGNMENTS_PATH = ROOT / "data" / "manifest" / "dataset_meso_assignments.json"
OUT_DIR = ROOT / "data" / "disciplines"
JSON_OUT = OUT_DIR / "dataset_disciplines.json"
SOURCE_OUT = OUT_DIR / "dataset_disciplines.source.json"

SCHEMA_VERSION = "1.0.0"
GENERATED_BY = "scripts/build_dataset_disciplines.py"
FEED_REPO = "https://github.com/gasyoun/IndologyScholars"
SOURCE_FILES = [
    "IndologyScholars/curation/meso_discipline_crosswalk.csv",
    "IndologyScholars/curation/disciplines.csv",
    "data/manifest/dataset_meso_assignments.json",
    "scripts/build_dataset_disciplines.py",
]


def _git_head(cwd: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, timeout=30
        ).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def round4(value: float) -> float:
    return round(value, 4)


def build_payload() -> dict:
    crosswalk_rows = list(csv.DictReader(CROSSWALK_PATH.open(encoding="utf-8")))
    discipline_rows = list(csv.DictReader(DISCIPLINES_PATH.open(encoding="utf-8")))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assignments_doc = json.loads(ASSIGNMENTS_PATH.read_text(encoding="utf-8"))

    # meso_code -> [{discipline_code, confidence, note}] (a code may map to several);
    # rows with an empty discipline_code are the crosswalk's deliberate NOT-MAPPED sentinels.
    crosswalk: dict[str, list[dict]] = {}
    sentinel_rows: list[dict] = []
    for r in crosswalk_rows:
        meso = (r.get("meso_code") or "").strip()
        disc = (r.get("discipline_code") or "").strip()
        if not meso:
            continue
        if not disc:
            sentinel_rows.append(
                {
                    "mesoCode": meso,
                    "confidence": float(r.get("confidence") or 0),
                    "note": (r.get("note") or "").strip(),
                }
            )
            continue
        crosswalk.setdefault(meso, []).append(
            {
                "disciplineCode": disc,
                "confidence": float(r.get("confidence") or 0),
                "note": (r.get("note") or "").strip(),
            }
        )

    discipline_labels = {
        (r.get("discipline_code") or "").strip(): {
            "labelEn": (r.get("label_en") or "").strip(),
            "labelRu": (r.get("label_ru") or "").strip(),
            "parentCode": (r.get("parent_code") or "").strip() or None,
            "status": (r.get("status") or "").strip(),
        }
        for r in discipline_rows
    }

    assignment_by_id = {a["id"]: a for a in assignments_doc["assignments"]}
    dataset_ids = [d["id"] for d in manifest["datasets"]]

    missing = sorted(set(dataset_ids) - set(assignment_by_id))
    if missing:
        raise SystemExit(f"assignment layer missing rows for datasets: {missing}")
    extra = sorted(set(assignment_by_id) - set(dataset_ids))
    if extra:
        raise SystemExit(f"assignment layer references unknown datasets: {extra}")

    datasets = []
    for d in manifest["datasets"]:
        a = assignment_by_id[d["id"]]
        base = {
            "id": d["id"],
            "title": d.get("title", ""),
            "mesoCode": a.get("mesoCode"),
            "assignmentConfidence": a.get("confidence", 0),
            "rationale": a.get("rationale", ""),
        }
        if not a.get("mesoCode"):
            datasets.append({**base, "disciplines": []})
            continue
        mappings = crosswalk.get(a["mesoCode"])
        if mappings is None:
            raise SystemExit(
                f"meso code {a['mesoCode']} (dataset {d['id']}) not in sibling crosswalk"
            )
        disciplines = []
        for m in mappings:
            label = discipline_labels.get(m["disciplineCode"])
            if label is None:
                raise SystemExit(f"discipline {m['disciplineCode']} not in sibling disciplines.csv")
            disciplines.append(
                {
                    "code": m["disciplineCode"],
                    "labelEn": label["labelEn"],
                    "labelRu": label["labelRu"],
                    "parentCode": label["parentCode"],
                    "confidence": round4(min(1.0, a["confidence"] * m["confidence"])),
                    "crosswalkConfidence": m["confidence"],
                    "crosswalkNote": m["note"],
                }
            )
        disciplines.sort(key=lambda x: -x["confidence"])
        datasets.append({**base, "disciplines": disciplines})

    assigned = [d for d in datasets if d["disciplines"]]
    per_discipline: dict[str, dict] = {}
    for d in assigned:
        for disc in d["disciplines"]:
            entry = per_discipline.setdefault(
                disc["code"],
                {"code": disc["code"], "labelEn": disc["labelEn"], "labelRu": disc["labelRu"], "datasets": []},
            )
            entry["datasets"].append(d["id"])

    return {
        "schemaVersion": SCHEMA_VERSION,
        "license": "CC-BY-4.0 (IndologyScholars derived exports; archive attribution)",
        "generatedBy": GENERATED_BY,
        "sourceFiles": SOURCE_FILES,
        "method": (
            "kosha dataset-registry -> meso_code assignments joined through the sibling "
            "IndologyScholars crosswalk to the ratified discipline taxonomy; taxonomy never "
            "re-derived (H3567 F5 / F5c); csl-atlas assignment precedent mirrored (H4178)."
        ),
        "totals": {
            "datasets": len(datasets),
            "assigned": len(assigned),
            "unassigned": len(datasets) - len(assigned),
            "disciplines": len(per_discipline),
        },
        "perDiscipline": sorted(per_discipline.values(), key=lambda x: -len(x["datasets"])),
        "notMappedSentinels": sentinel_rows,
        "datasets": datasets,
    }


def check() -> int:
    failures: list[str] = []
    notes: list[str] = []
    if not JSON_OUT.exists() or not SOURCE_OUT.exists():
        print(f"FAIL: committed packet missing ({JSON_OUT.name} / {SOURCE_OUT.name})")
        return 1
    committed = json.loads(JSON_OUT.read_text(encoding="utf-8"))
    source = json.loads(SOURCE_OUT.read_text(encoding="utf-8"))

    rebuilt = build_payload()
    if rebuilt != committed:
        for key in rebuilt:
            if rebuilt[key] != committed.get(key):
                failures.append(f"payload section '{key}' does not re-derive from inputs")
    if source.get("dataset") != "dataset_disciplines":
        failures.append("source envelope dataset mismatch")
    if source.get("schemaVersion") != SCHEMA_VERSION:
        failures.append(f"source envelope schemaVersion {source.get('schemaVersion')}")
    if not source.get("feedCommit"):
        notes.append("source envelope has no feedCommit (sibling absent at build time)")
    elif SIBLING_ROOT.exists():
        head = _git_head(SIBLING_ROOT)
        if head and head != source["feedCommit"]:
            notes.append(
                f"STALE PIN: sibling HEAD {head[:12]} != pinned feedCommit "
                f"{source['feedCommit'][:12]} — re-run the build to refresh"
            )

    if failures:
        print("FAIL: dataset-disciplines packet does not re-derive:")
        for f in failures:
            print(f"  - {f}")
        return 1
    for n in notes:
        print(f"note: {n}")
    t = committed["totals"]
    print(
        f"PASS: dataset-disciplines packet re-derives byte-identical "
        f"({t['datasets']} datasets, {t['assigned']} assigned, {t['unassigned']} honest nulls, "
        f"{t['disciplines']} disciplines)"
    )
    return 0


def main() -> int:
    if "--check" in sys.argv[1:]:
        return check()

    payload = build_payload()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    source = {
        "dataset": "dataset_disciplines",
        "commit": _git_head(ROOT) or "unknown (no git)",
        "feedRepo": FEED_REPO,
        "feedCommit": _git_head(SIBLING_ROOT),
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generatedBy": GENERATED_BY,
        "sourceFiles": SOURCE_FILES,
        "schemaVersion": SCHEMA_VERSION,
    }
    SOURCE_OUT.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    t = payload["totals"]
    print(
        f"Wrote dataset-disciplines packet ({t['datasets']} datasets, {t['assigned']} assigned, "
        f"{t['unassigned']} honest nulls, {t['disciplines']} disciplines, "
        f"{len(payload['notMappedSentinels'])} NOT-MAPPED sentinels):"
    )
    print(f"- {JSON_OUT.relative_to(ROOT)}")
    print(f"- {SOURCE_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
