"""kosha — writable search-history/analytics store. Kept as a SEPARATE SQLite
file from the read-only `kosha.db` (app/db.py) on purpose: the monthly
dictionary-rebuild pipeline (scripts/build_db.py) must never touch it, and the
existing read-only `get_db()` dependency must stay untouched. Still local-first
(A3): one file, no server process, no external service.
"""
import os
import sqlite3
from pathlib import Path

HISTORY_DB_PATH = Path(
    os.getenv("HISTORY_DB_PATH", str(Path(__file__).resolve().parent.parent / "data" / "db" / "kosha_history.db"))
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS visitors (
  anon_id TEXT PRIMARY KEY,
  email TEXT,
  email_verified INTEGER NOT NULL DEFAULT 0,
  newsletter_opt_in INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS search_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  anon_id TEXT NOT NULL,
  query_raw TEXT NOT NULL,
  query_slp1 TEXT NOT NULL,
  mode TEXT NOT NULL,
  results_total INTEGER,
  ip_hash TEXT
);
CREATE INDEX IF NOT EXISTS idx_search_events_anon_ts ON search_events(anon_id, ts DESC);
CREATE TABLE IF NOT EXISTS daily_rollup (
  day TEXT NOT NULL,
  query_slp1 TEXT NOT NULL,
  count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, query_slp1)
);
CREATE TABLE IF NOT EXISTS magic_links (
  token TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  anon_id TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  used INTEGER NOT NULL DEFAULT 0
);
"""


def open_connection() -> sqlite3.Connection:
    # Reads the module attribute (not a captured local) so tests can
    # monkeypatch `history_db.HISTORY_DB_PATH` and have it take effect
    # immediately, without needing a separate init call.
    path = HISTORY_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(_SCHEMA)
    return con


def get_history_db():
    con = open_connection()
    try:
        yield con
    finally:
        con.close()


def upsert_visitor(con, anon_id: str, ts: str):
    con.execute(
        "INSERT INTO visitors (anon_id, created_at) VALUES (?, ?) "
        "ON CONFLICT(anon_id) DO NOTHING",
        (anon_id, ts),
    )
    con.commit()


def log_search_event(con, anon_id: str, ts: str, query_raw: str, query_slp1: str,
                      mode: str, results_total: int, ip_hash: str | None):
    con.execute(
        "INSERT INTO search_events (ts, anon_id, query_raw, query_slp1, mode, results_total, ip_hash) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ts, anon_id, query_raw, query_slp1, mode, results_total, ip_hash),
    )
    day = ts[:10]
    con.execute(
        "INSERT INTO daily_rollup (day, query_slp1, count) VALUES (?, ?, 1) "
        "ON CONFLICT(day, query_slp1) DO UPDATE SET count = count + 1",
        (day, query_slp1),
    )
    con.commit()


def get_visitor_history(con, anon_id: str, limit: int = 50, offset: int = 0):
    rows = con.execute(
        "SELECT ts, query_raw, query_slp1, mode, results_total FROM search_events "
        "WHERE anon_id = ? ORDER BY ts DESC, id DESC LIMIT ? OFFSET ?",
        (anon_id, limit, offset),
    ).fetchall()
    total = con.execute(
        "SELECT COUNT(*) FROM search_events WHERE anon_id = ?", (anon_id,)
    ).fetchone()[0]
    return rows, total


def clear_visitor_history(con, anon_id: str) -> int:
    cur = con.execute("DELETE FROM search_events WHERE anon_id = ?", (anon_id,))
    con.commit()
    return cur.rowcount


def purge_old_search_events(con, cutoff_ts: str) -> int:
    """Delete raw search_events rows older than cutoff_ts (ISO ts string,
    compared lexicographically like the rest of this module). daily_rollup
    is untouched — it is the permanent aggregate the /api/v1/stats/* charts
    read from, and has no per-visitor identifying data to retain-limit."""
    cur = con.execute("DELETE FROM search_events WHERE ts < ?", (cutoff_ts,))
    con.commit()
    return cur.rowcount
