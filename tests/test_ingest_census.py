# tests/test_ingest_census.py — G89 (H5778) pytest shim over
# scripts/ingest_census_check.py. The real gate needs the built
# data/db/kosha.db (1.7 GB, never committed); on a checkout without it this
# SKIPs — the vendor-SKIP convention (goal_signal_run.py PHP lane), never a
# false FAIL. With the db present the shim runs the checker's own exit code.
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "db" / "kosha.db"


def test_ingest_census_floors_hold():
    if not DB.is_file():
        import pytest
        pytest.skip("kosha.db not built on this checkout (SKIP, not FAIL)")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ingest_census_check.py")],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.startswith("CENSUS PASS")


def test_census_file_schema():
    import json
    census = json.loads(
        (ROOT / "data" / "census" / "ingest_census.json").read_text("utf-8"))
    for key in ("heritage_anchor", "forms", "forms_heritage", "entries",
                "lemmas", "senses"):
        assert isinstance(census["floors"][key], int), key
    assert census["floors"]["heritage_anchor"] >= 100000
    assert census["floors"]["forms_heritage"] >= 900000
