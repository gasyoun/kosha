#!/usr/bin/env python3
"""H3455 lane A step 1 - freeze the akshara.ru benchmark sample manifest.

Stratum A: ALL distinct TM headwords (c1-lane promoted coverage census).
Stratum B: 50 random PWG headwords absent from the TM (coverage control).

Deterministic: fixed seed 730 (house convention). Length-preserving SLP1 keys,
never NFD-strip. Output: data/akshara_pilot/sample_manifest.jsonl

Usage:
  python scripts/akshara_pilot_sample.py [--selftest]
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN_CHECKOUT = Path(r"C:\Users\user\Documents\GitHub\kosha")
TM_PATH = Path(r"C:\Users\user\Documents\GitHub\pwg-ru-data\tm\pwg_ru_translated.jsonl")


def _first_existing(*cands: Path) -> Path:
    for p in cands:
        if p.exists():
            return p
    raise FileNotFoundError(f"none of {cands} exists")


PWG_SQLITE = _first_existing(
    ROOT / "data" / "raw_sqlite" / "pwg" / "pwg.sqlite",
    MAIN_CHECKOUT / "data" / "raw_sqlite" / "pwg" / "pwg.sqlite",
)
OUT = ROOT / "data" / "akshara_pilot" / "sample_manifest.jsonl"
SEED = 730
CONTROL_N = 50


def load_tm_roots(tm_path: Path):
    """Distinct TM headwords -> {key1: {statuses:set, n_subcards:int}}."""
    roots: dict[str, dict] = {}
    with open(tm_path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            k = r["key1"]
            e = roots.setdefault(k, {"statuses": collections.Counter(), "n_subcards": 0})
            e["statuses"][r.get("review_status", "?")] += 1
            e["n_subcards"] += 1
    return roots


def load_pwg_keys(db_path: Path):
    con = sqlite3.connect(str(db_path))
    try:
        return [r[0] for r in con.execute("SELECT DISTINCT key FROM pwg ORDER BY key")]
    finally:
        con.close()


def build(out_path: Path = OUT, tm_path: Path = TM_PATH, db_path: Path = PWG_SQLITE,
          control_n: int = CONTROL_N, seed: int = SEED) -> dict:
    tm = load_tm_roots(tm_path)
    keys = load_pwg_keys(db_path)
    rng = random.Random(seed)
    pool = [k for k in keys if k not in tm]
    control = sorted(rng.sample(pool, min(control_n, len(pool))))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_a = n_b = 0
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        for k in sorted(tm):
            e = tm[k]
            f.write(json.dumps({
                "slp1": k, "stratum": "tm",
                "n_subcards": e["n_subcards"],
                "review_status": dict(e["statuses"]),
                "url": f"https://akshara.ru/kosha?q={k}&dict=all&script=slp1",
            }, ensure_ascii=False) + "\n")
            n_a += 1
        for k in control:
            f.write(json.dumps({
                "slp1": k, "stratum": "control",
                "n_subcards": 0, "review_status": {},
                "url": f"https://akshara.ru/kosha?q={k}&dict=all&script=slp1",
            }, ensure_ascii=False) + "\n")
            n_b += 1
    return {"tm_roots": n_a, "control": n_b, "pool_size": len(pool), "seed": seed}


def selftest() -> None:
    tmp = Path(sys.argv[0]).parent / "_selftest_manifest.jsonl"
    stats = build(tmp)
    rows = [json.loads(l) for l in open(tmp, encoding="utf-8")]
    assert len(rows) == stats["tm_roots"] + stats["control"], "row count mismatch"
    assert all(r["slp1"] and r["url"].startswith("https://akshara.ru/kosha?q=") for r in rows)
    assert sum(r["stratum"] == "control" for r in rows) == stats["control"]
    assert any(r["stratum"] == "tm" for r in rows)
    tmp.unlink()
    print(f"selftest OK: {stats}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    else:
        print(json.dumps(build(), ensure_ascii=False))
