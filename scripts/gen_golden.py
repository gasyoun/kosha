"""kosha D4/A1 — generate frozen golden render snapshots.

ARCHITECTURE.md A1 merge bar: "≥10 sample entries per dictionary with committed
HTML snapshots; the renderer cannot merge without them." EVAL_PLAN.md §0
anti-gaming: golden artifacts are **frozen, checksummed, and NOT hand-picked**.

Selection is a seeded-deterministic sample of the stable Cologne L-numbers per
dict (`random.Random(SEED)` over the sorted L list) — auditably reproducible,
never cherry-picked for easy markup. The two known-good fixtures the plan names
(MW banD = L142512, akṣa = L523) are pinned in addition, as regression anchors.

Snapshots lock render()'s output against regression. They are the frozen
expected output of THIS port (basicdisplay.php mw/pwg/ap90 path); they are NOT
diffed against the live PHP web stack (which needs dal DBs + servers kosha
never calls — RISKS.md R12). That boundary is stated in app/render.py.

    python scripts/gen_golden.py          # (re)generate + freeze
Run only to (re)freeze intentionally; the committed snapshots are the contract.
"""
import hashlib
import json
import random
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from render import render  # noqa: E402

DB_PATH = ROOT / "data" / "db" / "kosha.db"
GOLDEN_DIR = ROOT / "tests" / "golden"
SEED = 20260702  # frozen; changing it re-selects the sample (an intentional act)
N_PER_DICT = 12
PINNED = {"mw": ["142512", "523"]}  # named fixtures (banD, akza)


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def select(con, dict_code):
    ls = [r[0] for r in con.execute(
        "SELECT L FROM entries WHERE dict=? ORDER BY L", (dict_code,)).fetchall()]
    rng = random.Random(f"{SEED}:{dict_code}")
    sample = rng.sample(ls, min(N_PER_DICT, len(ls)))
    picked = list(dict.fromkeys(PINNED.get(dict_code, []) + sorted(sample)))
    return picked


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"missing {DB_PATH}; build it with scripts/build_db.py first")
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"seed": SEED, "n_per_dict": N_PER_DICT, "entries": []}
    for dict_code in ("mw", "pwg", "ap90"):
        d_dir = GOLDEN_DIR / dict_code
        d_dir.mkdir(exist_ok=True)
        for L in select(con, dict_code):
            row = con.execute(
                "SELECT body FROM entries WHERE dict=? AND L=?", (dict_code, L)).fetchone()
            if row is None:
                continue
            html = render(dict_code, row["body"])
            fname = f"{dict_code}/{L.replace('/', '_')}.html"
            (GOLDEN_DIR / fname).write_text(html, encoding="utf-8")
            manifest["entries"].append(
                {"dict": dict_code, "L": L, "file": fname, "sha256": sha256(html)})
    (GOLDEN_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    by = {}
    for e in manifest["entries"]:
        by[e["dict"]] = by.get(e["dict"], 0) + 1
    print(f"[golden] froze {len(manifest['entries'])} snapshots: {by}")


if __name__ == "__main__":
    main()
