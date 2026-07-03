"""kosha — freeze the current build's senses into a per-version archive
(RISKS.md R1 Commitments 1-2). One dump serves both:
  * `/api/v1/sense/{id}@version` resolution of an old citation (app/versions.py)
  * the old side of the sense_crosswalk diff (scripts/build_crosswalk.py)

    python scripts/archive_senses.py [--version X] [--dicts mw,pwg,ap90]

Writes `{KOSHA_RELEASES_DIR|data/releases}/{version}/senses.sqlite`. The
archive is bulk + regenerable → gitignored; it ships as a GitHub release asset
(R11). `--version` defaults to the DB's current `meta.data_version`.
"""
import argparse
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from versions import write_archive  # noqa: E402
from segment import sense_text  # noqa: E402

DB_PATH = ROOT / "data" / "db" / "kosha.db"


def iter_senses(con, dicts):
    q = ("SELECT e.dict, e.L, e.slp1_key, e.body, s.sense_n, s.span_start, s.span_end "
         "FROM senses s JOIN entries e ON e.id=s.entry_id "
         f"WHERE e.dict IN ({','.join('?' * len(dicts))}) ORDER BY e.dict, e.L, s.sense_n")
    for r in con.execute(q, dicts):
        yield {
            "sense_id": f"{r['dict']}.{r['L']}.{r['sense_n']}",
            "dict": r["dict"], "L": r["L"], "sense_n": r["sense_n"],
            "headword": r["slp1_key"],
            "text_raw": sense_text(r["body"], r["span_start"], r["span_end"]),
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=None)
    ap.add_argument("--dicts", default="mw,pwg,ap90")
    args = ap.parse_args()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    version = args.version or con.execute(
        "SELECT value FROM meta WHERE key='data_version'").fetchone()[0]
    dicts = args.dicts.split(",")
    path = write_archive(version, iter_senses(con, dicts))
    n = sqlite3.connect(path).execute("SELECT COUNT(*) FROM archive").fetchone()[0]
    con.close()
    print(f"[archive] froze {n} senses -> {path} (version {version})")


if __name__ == "__main__":
    main()
