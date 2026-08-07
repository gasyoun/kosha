"""kosha — shared SQLite connection helper. Local-first (A3): no pooling,
no server process; uvicorn opens one read-only connection per request-scope
dependency, closed by FastAPI's dependency teardown.

W0B (H1944): the location comes from typed settings instead of a hard-coded
literal, so `KOSHA_CORE_DB_PATH` — or the deprecated `DATABASE_PATH` alias that
`.env.example` has shipped since Phase 1 — selects the store. `DB_PATH` stays
a module attribute because tests and scripts import it directly.

W1A (H2341): connections go through the multi-DB storage facade
(`kosha.query.open_query_connection`), which ATTACHes read-only
`inflections` / `layers` with stable aliases when those files exist. History
is never mounted on this path.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kosha.query.connection import open_query_connection  # noqa: E402
from kosha.settings import get_settings  # noqa: E402

DB_PATH = get_settings().core_db


def get_db():
    con = open_query_connection()
    try:
        yield con
    finally:
        con.close()


def data_version(con) -> str:
    row = con.execute("SELECT value FROM meta WHERE key='data_version'").fetchone()
    return row["value"] if row else "0.0.0-dev"
