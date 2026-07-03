"""kosha D4/A1 — golden render snapshot tests (ARCHITECTURE.md merge bar).

Re-renders every entry pinned in tests/golden/manifest.json and asserts the
HTML is byte-identical to the frozen snapshot AND matches its committed sha256.
These are frozen artifacts (EVAL_PLAN.md §0): a diff here means render() changed
output for a real entry — regenerate deliberately with scripts/gen_golden.py and
review the diff, never edit a snapshot by hand to make the test pass.

Local-only (A3): if data/db/kosha.db is absent, the DB-backed tests skip; the
snapshot-integrity checks (checksum of committed files) still run.
"""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from render import render  # noqa: E402

GOLDEN_DIR = ROOT / "tests" / "golden"
DB_PATH = ROOT / "data" / "db" / "kosha.db"
MANIFEST = json.loads((GOLDEN_DIR / "manifest.json").read_text(encoding="utf-8"))


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def test_manifest_covers_min_10_per_dict():
    by = {}
    for e in MANIFEST["entries"]:
        by[e["dict"]] = by.get(e["dict"], 0) + 1
    assert set(by) == {"mw", "pwg", "ap90"}
    for d, n in by.items():
        assert n >= 10, f"{d} has only {n} golden snapshots (merge bar: >=10)"


@pytest.mark.parametrize("e", MANIFEST["entries"], ids=lambda e: f"{e['dict']}.{e['L']}")
def test_snapshot_file_matches_committed_checksum(e):
    html = (GOLDEN_DIR / e["file"]).read_text(encoding="utf-8")
    assert _sha256(html) == e["sha256"], f"{e['file']} content drifted from manifest sha256"


_have_db = DB_PATH.exists()


@pytest.mark.skipif(not _have_db, reason="kosha.db not built (A3 local-only)")
@pytest.mark.parametrize("e", MANIFEST["entries"], ids=lambda e: f"{e['dict']}.{e['L']}")
def test_render_reproduces_golden(e):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            "SELECT body FROM entries WHERE dict=? AND L=?", (e["dict"], e["L"])).fetchone()
    finally:
        con.close()
    assert row is not None, f"golden entry {e['dict']}.{e['L']} missing from DB"
    html = render(e["dict"], row["body"])
    expected = (GOLDEN_DIR / e["file"]).read_text(encoding="utf-8")
    assert html == expected, f"render() output changed for {e['dict']}.{e['L']}"
    assert _sha256(html) == e["sha256"]
