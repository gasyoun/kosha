"""kosha — build kosha.db from source feeds.

Phase 1 (PHASE1_PLAN.md D1-D3): vendor the lemma spine, load per-dict
entries, import the forms layer. Run stages independently via --stage,
or all in order with no flag. Idempotent: re-running drops and rebuilds
each stage's tables.

    python scripts/build_db.py --stage lemmas
    python scripts/build_db.py --stage entries --dicts mw,pwg,ap90
    python scripts/build_db.py --stage forms
    python scripts/build_db.py            # all stages, in order
"""
import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "db" / "kosha.db"

# SanskritLexicography is a sibling repo (org convention: all repos under
# the same GitHub/ root). Consume, don't rebuild (SHARED_CODE.md).
SIBLING = ROOT.parent
UNION_HEADWORDS = SIBLING / "SanskritLexicography" / "HeadwordLists" / "union" / "union_headwords.tsv"
FREQ_TSV = ROOT / "data" / "frequency" / "lemma_frequency.tsv"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE IF NOT EXISTS sources (
    dict TEXT PRIMARY KEY,
    title TEXT, edition TEXT,
    csl_orig_commit TEXT NOT NULL,
    source_path TEXT,
    pc_format TEXT NOT NULL,
    pc_coverage REAL,
    entry_count INTEGER
);

CREATE TABLE IF NOT EXISTS lemmas (
    slp1 TEXT PRIMARY KEY,
    iast TEXT NOT NULL,
    n_dicts INTEGER, dicts TEXT, gender TEXT,
    count_all INTEGER, grammar_all TEXT, rank_all INTEGER,
    periods TEXT, periods_sum INTEGER, coverage_pct REAL, core_rank INTEGER
);

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    dict TEXT NOT NULL REFERENCES sources(dict),
    L TEXT NOT NULL,
    slp1_key TEXT NOT NULL,
    k2 TEXT,
    pc_raw TEXT,
    vol INTEGER, page INTEGER, col TEXT,
    body TEXT NOT NULL,
    UNIQUE(dict, L)
);
-- Lemma lookups filter (dict, slp1_key) and ORDER BY L. A covering
-- (dict, slp1_key, L) index serves BOTH the equality seek and the ordering, so
-- the planner never falls back to scanning the whole dict via the UNIQUE(dict,L)
-- autoindex (measured D5: that scan cost ~240 ms/lookup; this index: ~0.3 ms —
-- a plain slp1_key-only index was NOT chosen because ORDER BY L made the planner
-- prefer the ordered autoindex-scan). See D5_MEASUREMENTS.md §3.
CREATE INDEX IF NOT EXISTS entries_dict_key ON entries(dict, slp1_key, L);

CREATE TABLE IF NOT EXISTS senses (
    entry_id INTEGER NOT NULL REFERENCES entries(id),
    sense_n INTEGER NOT NULL,
    span_start INTEGER NOT NULL, span_end INTEGER NOT NULL,
    PRIMARY KEY (entry_id, sense_n)
);

CREATE TABLE IF NOT EXISTS forms (
    form_slp1 TEXT NOT NULL,
    lemma_slp1 TEXT NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (form_slp1, lemma_slp1, source)
);
CREATE INDEX IF NOT EXISTS forms_lemma ON forms(lemma_slp1);
"""


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    return con


def build_lemmas(con):
    """D1 — vendor union_headwords.tsv, LEFT-JOIN the frequency sidecar."""
    if not UNION_HEADWORDS.exists():
        raise SystemExit(f"missing sibling feed: {UNION_HEADWORDS}")
    if not FREQ_TSV.exists():
        raise SystemExit(f"missing frequency sidecar: {FREQ_TSV}")

    freq = {}
    with open(FREQ_TSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            freq[row["lemma_slp1"]] = row

    con.execute("DELETE FROM lemmas")
    n = 0
    with open(UNION_HEADWORDS, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = []
        for r in reader:
            slp1 = r["slp1"]
            fr = freq.get(slp1)
            rows.append((
                slp1, r["iast"], int(r["n_dicts"]) if r["n_dicts"] else None,
                r["dicts"], r["gender"] or None,
                int(fr["count_all"]) if fr and fr["count_all"] else None,
                fr["grammar_all"] if fr else None,
                int(fr["rank_all"]) if fr and fr["rank_all"] else None,
                fr["periods"] if fr else None,
                int(fr["periods_sum"]) if fr and fr["periods_sum"] else None,
                float(fr["coverage_pct"]) if fr and fr.get("coverage_pct") else None,
                int(fr["core_rank"]) if fr and fr.get("core_rank") else None,
            ))
            n += 1
        con.executemany(
            "INSERT INTO lemmas (slp1, iast, n_dicts, dicts, gender, "
            "count_all, grammar_all, rank_all, periods, periods_sum, "
            "coverage_pct, core_rank) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
    con.commit()
    count = con.execute("SELECT COUNT(*) FROM lemmas").fetchone()[0]
    joined = con.execute("SELECT COUNT(*) FROM lemmas WHERE count_all IS NOT NULL").fetchone()[0]
    print(f"[D1] lemmas: {count} rows loaded, {joined} carry a frequency signal")
    return count, joined


STAGES = {"lemmas": build_lemmas}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=list(STAGES) + ["entries", "forms"], default=None)
    ap.add_argument("--dicts", default="mw,pwg,ap90")
    args = ap.parse_args()

    con = connect()
    if args.stage in (None, "lemmas"):
        build_lemmas(con)
    if args.stage == "entries":
        from build_entries import build_entries  # noqa: E402
        build_entries(con, args.dicts.split(","))
    if args.stage == "forms":
        from build_forms import build_forms  # noqa: E402
        build_forms(con)
    # data_version (A2): NOT a citable release yet — Phase 1 D1-D4 local dev
    # build. First real data_version bump happens at the first GitHub release
    # per ARCHITECTURE.md (P2, D5-gated). "0.1.0-dev" marks this explicitly.
    con.execute(
        "INSERT INTO meta (key, value) VALUES ('data_version','0.1.0-dev') "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value"
    )
    con.commit()
    # Refresh planner statistics so index selectivity is known (cheap ~5 s;
    # the entries_dict_key covering index is chosen even without stats, but
    # ANALYZE keeps the search/forms plans optimal too). D5.
    con.execute("ANALYZE")
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
