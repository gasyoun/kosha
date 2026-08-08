"""Build the committed W2A mini-archive under tests/fixtures/archives/.

Two release identities share sense_id mw.101.1 but carry *different* text so
historical resolution can prove the old wording is returned for the prior
version. Run once when the fixture needs regenerating; the outputs are
committed (small, public MW-shaped sample text only).

    python scripts/build_w2a_mini_archive_fixture.py
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "archives"
DUMP = "senses.sqlite"
META = "release.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS archive (
    sense_id TEXT PRIMARY KEY,
    dict TEXT NOT NULL, L TEXT NOT NULL, sense_n INTEGER NOT NULL,
    headword TEXT, text_raw TEXT NOT NULL
);
"""

# Prior vs current wording deliberately diverge — that is the point of the
# multi-version historical-resolution smoke.
VERSIONS = {
    "0.1.0-w2a-prior": {
        "sense_id": "mw.101.1",
        "dict": "mw",
        "L": "101",
        "sense_n": 1,
        "headword": "agni",
        "text_raw": "<H1>PRIOR fire (W2A fixture 0.1.0)</H1>",
    },
    "0.2.0-w2a-current": {
        "sense_id": "mw.101.1",
        "dict": "mw",
        "L": "101",
        "sense_n": 1,
        "headword": "agni",
        "text_raw": "<H1>CURRENT fire (W2A fixture 0.2.0)</H1>",
    },
}


def _write(version: str, sense: dict) -> Path:
    directory = FIXTURE / version
    directory.mkdir(parents=True, exist_ok=True)
    dump = directory / DUMP
    con = sqlite3.connect(dump)
    try:
        con.executescript(SCHEMA)
        con.execute("DELETE FROM archive")
        con.execute(
            "INSERT INTO archive "
            "(sense_id, dict, L, sense_n, headword, text_raw) "
            "VALUES (:sense_id, :dict, :L, :sense_n, :headword, :text_raw)",
            sense,
        )
        con.commit()
    finally:
        con.close()
    digest = hashlib.sha256(dump.read_bytes()).hexdigest()
    (directory / META).write_text(
        json.dumps(
            {"version": version, "sha256": digest, "senses": 1},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return dump


def main() -> int:
    FIXTURE.mkdir(parents=True, exist_ok=True)
    for version, sense in VERSIONS.items():
        path = _write(version, sense)
        print(f"wrote {path.relative_to(ROOT)}")
    readme = FIXTURE / "README.md"
    readme.write_text(
        "# W2A mini-archive fixture\n\n"
        "_Created: 08-08-2026 · Last updated: 08-08-2026_\n\n"
        "Committed sample for [H2346](https://github.com/gasyoun/Uprava/blob/"
        "main/handoffs/H2346-Grok_kosha_architecture-roadmap-w2a-immutable-"
        "sense-archives_07.08.26.md) historical-resolution tests.\n\n"
        "| Version | Sense | Text marker |\n"
        "|---|---|---|\n"
        "| `0.1.0-w2a-prior` | `mw.101.1` | PRIOR fire |\n"
        "| `0.2.0-w2a-current` | `mw.101.1` | CURRENT fire |\n\n"
        "Regenerate with `python scripts/build_w2a_mini_archive_fixture.py`.\n"
        "Each directory has `senses.sqlite` + `release.json` (sha256 identity).\n\n"
        "_Dr. Mārcis Gasūns_\n",
        encoding="utf-8",
    )
    print(f"wrote {readme.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
