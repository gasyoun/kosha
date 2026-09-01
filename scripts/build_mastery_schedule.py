#!/usr/bin/env python3
"""H3742 -- combined FSRS-style mastery schedule over kosha's five drill families.

Data-layer only: reads each family's items + its `mastery` ease weights
(data/MASTERY_WEIGHTS_SPEC.md) and writes one due-schedule artifact,
data/mastery/combined_schedule.json, that a reader surface (SanskritKaraoke,
SanskritGrammar) can draw from without caring which family an item is in.
Does not touch, export to, or duplicate Systema-Sanscriticum's Saraswati SRS.

Usage (from kosha root):
  python scripts/build_mastery_schedule.py
  python scripts/build_mastery_schedule.py --check
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "mastery"
OUT_SCHEDULE = OUT_DIR / "combined_schedule.json"

# (family, items_path, items_key, weights_path)
FAMILIES = [
    ("sandhi", "data/sandhi/sandhi_drills.json", "items", "data/sandhi/drill_weights.json"),
    ("samasa", "data/samasa/samasa_drills.json", "items", "data/samasa/drill_weights.json"),
    ("morphology", "data/morphology/drills.json", "items", "data/morphology/drill_weights.json"),
    ("vocab", "data/frequency/vocab_drills.json", "items", "data/frequency/vocab_drill_weights.json"),
    ("thematic_vocab", "data/frequency/thematic_vocab_drills.json", "items",
     "data/frequency/thematic_vocab_drill_weights.json"),
]

# New-item FSRS-style seed: higher ease -> longer initial stability (days
# until first due), same shape for every family since ease is 0..1 comparable
# by construction (data/MASTERY_WEIGHTS_SPEC.md).
MIN_STABILITY_DAYS = 1.0
MAX_STABILITY_DAYS = 6.0


def item_ease(item: dict, mastery: dict) -> float:
    field = mastery["bucket_field"]
    default = mastery["family_default_ease"]
    val = item.get(field)
    if "bucket_ease" in mastery:
        return mastery["bucket_ease"].get(val, default)
    if "ease_formula" in mastery:
        if not isinstance(val, (int, float)):
            return default
        rank_max = mastery.get("rank_max", val)
        span = max(rank_max - 1, 1)
        ease = 1.0 - (val - 1) / span * 0.6
        return max(0.4, min(1.0, ease))
    return default


def load_family(family: str, items_path: str, items_key: str, weights_path: str, epoch: datetime) -> list[dict]:
    items = json.loads((ROOT / items_path).read_text(encoding="utf-8"))[items_key]
    weights = json.loads((ROOT / weights_path).read_text(encoding="utf-8"))
    mastery = weights["mastery"]
    rows = []
    for it in items:
        ease = item_ease(it, mastery)
        stability = MIN_STABILITY_DAYS + ease * (MAX_STABILITY_DAYS - MIN_STABILITY_DAYS)
        rows.append(
            {
                "family": family,
                "id": it["id"],
                "ease": round(ease, 4),
                "stability_days": round(stability, 4),
                # new items are all due at the epoch; a real review moves an
                # item's due date forward by its (evolving) stability -- out
                # of scope here, this is the seed state only.
                "due": epoch.isoformat().replace("+00:00", "Z"),
            }
        )
    return rows


def build(epoch: datetime | None = None) -> dict:
    epoch = epoch or datetime(2026, 9, 1, tzinfo=timezone.utc)
    rows: list[dict] = []
    by_family: dict[str, int] = {}
    for family, items_path, items_key, weights_path in FAMILIES:
        family_rows = load_family(family, items_path, items_key, weights_path, epoch)
        rows.extend(family_rows)
        by_family[family] = len(family_rows)
    schedule = {
        "_doc": "H3742 combined mastery schedule -- one row per item across kosha's five drill families. See data/MASTERY_WEIGHTS_SPEC.md.",
        "epoch": epoch.isoformat().replace("+00:00", "Z"),
        "families": by_family,
        "total_items": len(rows),
        "rows": rows,
    }
    return schedule


def due_items(schedule: dict, clock: datetime, n: int, seed: int) -> list[dict]:
    """Deterministic due-item selection: earliest `due` first, ties broken by
    a seeded shuffle so repeat calls with the same (schedule, clock, n, seed)
    always return the same list, and same-`due` items don't always resolve in
    file order (which would bias toward whichever family loads first)."""
    clock_iso = clock.isoformat().replace("+00:00", "Z")
    due_now = [r for r in schedule["rows"] if r["due"] <= clock_iso]
    rng = random.Random(seed)
    keyed = [(rng.random(), r["due"], r["family"], r["id"], r) for r in due_now]
    keyed.sort(key=lambda t: (t[1], t[0]))
    return [t[4] for t in keyed[:n]]


def check(schedule: dict | None = None) -> int:
    if schedule is None:
        if not OUT_SCHEDULE.is_file():
            print("FAIL: data/mastery/combined_schedule.json missing", file=sys.stderr)
            return 1
        schedule = json.loads(OUT_SCHEDULE.read_text(encoding="utf-8"))
    ok = True
    if schedule["total_items"] != sum(schedule["families"].values()):
        print("FAIL: total_items mismatch", file=sys.stderr)
        ok = False
    for family, n in schedule["families"].items():
        if n == 0:
            print(f"FAIL: family {family} has zero items", file=sys.stderr)
            ok = False
    if ok:
        print(f"GOAL OK -- {schedule['total_items']} items across {len(schedule['families'])} families")
        return 0
    print("GOAL FAIL", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="only re-verify the committed schedule")
    args = ap.parse_args()
    if args.check:
        return check()
    schedule = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_SCHEDULE.write_text(
        json.dumps(schedule, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"wrote {OUT_SCHEDULE.relative_to(ROOT)} ({schedule['total_items']} items)")
    return check(schedule)


if __name__ == "__main__":
    raise SystemExit(main())
