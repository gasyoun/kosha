"""kosha — shared SQLite connection helper. Local-first (A3): no pooling,
no server process; uvicorn opens one read-only connection per request-scope
dependency, closed by FastAPI's dependency teardown."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "db" / "kosha.db"


def get_db():
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


def data_version(con) -> str:
    row = con.execute("SELECT value FROM meta WHERE key='data_version'").fetchone()
    return row["value"] if row else "0.0.0-dev"
