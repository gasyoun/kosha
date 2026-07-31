"""kosha — shared SQLite connection helper. Local-first (A3): no pooling,
no server process; uvicorn opens one read-only connection per request-scope
dependency, closed by FastAPI's dependency teardown.

The path comes from the typed settings (`kosha.settings`, W0B/H1944) rather
than a hardcoded constant, so `KOSHA_CORE_DB` — or the deprecated
`DATABASE_PATH` alias, which used to be advertised in `.env.example` while
nothing read it — actually selects the database.
"""
import sqlite3
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if (_SRC / "kosha" / "__init__.py").is_file() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from kosha.settings import get_settings  # noqa: E402


def core_db_path() -> Path:
    """Current core-DB path. Read per call so a test that re-points
    `KOSHA_CORE_DB` and calls `kosha.settings.reload_settings()` takes effect
    without re-importing this module."""
    return get_settings().core_db


# Back-compat module constant: several tests and scripts import DB_PATH
# directly. It is a snapshot of the value at import time; anything that needs
# to observe a later change must call core_db_path().
DB_PATH = core_db_path()


def get_db():
    con = sqlite3.connect(f"file:{core_db_path()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


def data_version(con) -> str:
    row = con.execute("SELECT value FROM meta WHERE key='data_version'").fetchone()
    return row["value"] if row else "0.0.0-dev"
