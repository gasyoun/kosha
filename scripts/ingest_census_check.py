#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ingest_census_check.py — G89 (H5778): the ingest census lock.

Known signal gap 2 said kosha's H345/H111 ingests were "queued roadmap items,
not yet wired as coverage-% emitters". They shipped since (H345 heritage_anchor
re-run live per H837; H111 heritage-forms surplus delivered in PR #7 / #57) —
this locks them as LOWER-BOUND floors over data/db/kosha.db:

  - per-table row counts >= data/census/ingest_census.json floors;
  - the heritage share of forms is checked too (a rebuild that keeps `forms`
    total but loses the heritage source share still trips);
  - meta.build_stage_manifest must DECLARE the heritage stage and not list it
    in skipped — the silent-skip is exactly how H345-class damage hides.

Read-only (sqlite URI mode=ro), full count sweep < 2 s. Exit 0 = PASS with
counts printed; exit 1 = FAIL naming table / measured / floor.

Usage: python3 scripts/ingest_census_check.py [--db data/db/kosha.db]
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent.parent
CENSUS = BASE / "data" / "census" / "ingest_census.json"
TABLES = ("heritage_anchor", "forms", "entries", "lemmas", "senses")


def fail(msg):
    print(f"CENSUS FAIL: {msg}")
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(BASE / "data" / "db" / "kosha.db"))
    args = ap.parse_args()

    try:
        floors = json.loads(CENSUS.read_text(encoding="utf-8"))["floors"]
    except (OSError, ValueError, KeyError) as exc:
        fail(f"census file unreadable: {exc}")
    db_path = Path(args.db)
    if not db_path.is_file():
        fail(f"db not found: {db_path} (the lock runs on a checkout that has "
             "the built kosha.db; SKIP class, not FAIL class, for CI — see "
             "tests/test_ingest_census.py)")

    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = db.cursor()
    measured = {}
    for table in TABLES:
        try:
            measured[table] = cur.execute(
                f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except sqlite3.OperationalError as exc:
            fail(f"table {table} missing/broken: {exc}")
    try:
        measured["forms_heritage"] = cur.execute(
            "SELECT COUNT(*) FROM forms WHERE source = 'heritage'"
        ).fetchone()[0]
    except sqlite3.OperationalError as exc:
        fail(f"forms.source probe failed: {exc}")

    # heritage stage must be declared AND not skipped (meta JSON)
    meta_row = cur.execute(
        "SELECT value FROM meta WHERE key = 'build_stage_manifest'"
    ).fetchone()
    if meta_row:
        manifest = json.loads(meta_row[0])
        if "heritage" not in manifest.get("declared", []):
            fail("build_stage_manifest no longer declares the heritage stage")
        if "heritage" in manifest.get("skipped", {}):
            fail("build_stage_manifest lists heritage as SKIPPED — the silent "
                 "skip is the H345-class damage this lock exists to catch")

    drops = []
    for key, floor in floors.items():
        got = measured.get(key)
        if got is None:
            fail(f"census key {key} never measured")
        if got < floor:
            drops.append(f"{key}: {got} < floor {floor} "
                         f"(-{floor - got})")
    if drops:
        fail("; ".join(drops))

    print("CENSUS PASS: " + " · ".join(
        f"{key}={measured[key]} (floor {floor})"
        for key, floor in floors.items()))
    sys.exit(0)


if __name__ == "__main__":
    main()
