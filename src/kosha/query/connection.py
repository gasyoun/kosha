"""Multi-DB read-only connection facade (W1A, H2341).

Opens the core store and ATTACHes `inflections` / `layers` with the architecture's
stable aliases when those files exist and differ from core. TEMP VIEWs project
moved tables into the unqualified namespace so existing SQL (`FROM inflections`,
`FROM sense_frequency`, …) keeps working without rewriting every call site.

**History is never attached on this path.** Writable history stays on
`app/history_db.py` and only when `KOSHA_HISTORY_ENABLED` is true. Even if
`history.db` sits next to the core file, the query facade refuses to mount it.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from kosha.settings import Settings, get_settings

#: Architecture § Storage facade — tables that belong on the core file.
CORE_TABLES: frozenset[str] = frozenset(
    {
        "meta",
        "sources",
        "lemmas",
        "entries",
        "senses",
        "forms",
        "stem_bridge",
        "heritage_anchor",
    }
)

#: Paradigm / inflection inventory (separate file after the physical split).
INFLECTIONS_TABLES: frozenset[str] = frozenset({"inflections"})

#: Public query layers (frequency, coverage, roots, etymology, …).
LAYERS_TABLES: frozenset[str] = frozenset(
    {
        "sense_frequency",
        "roots_frequency",
        "dict_corpus_coverage",
        "mw_roots",
        "mw_etymology",
    }
)

#: Stable ATTACH schema names from ARCHITECTURE_KOSHA_PLATFORM.md § Storage facade.
STABLE_ALIASES: tuple[str, ...] = ("core", "inflections", "layers")

#: History alias is documented but deliberately unused by the query path.
HISTORY_ALIAS = "history"


class StorageFacadeError(RuntimeError):
    """Raised when the multi-DB facade cannot be opened safely."""


def _ro_uri(path: Path) -> str:
    """SQLite URI for a read-only file open (Windows-safe)."""
    resolved = path.resolve().as_posix()
    # Windows drive letters need a leading slash: file:///C:/...
    if len(resolved) >= 2 and resolved[1] == ":":
        resolved = "/" + resolved
    return f"file:{resolved}?mode=ro"


def _tables_in_schema(con: sqlite3.Connection, schema: str) -> set[str]:
    rows = con.execute(
        f"SELECT name FROM {schema}.sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row[0] for row in rows}


def _main_has_table(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM main.sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _safe_alias(alias: str) -> str:
    """Only allow the documented stable aliases as schema identifiers."""
    if alias not in STABLE_ALIASES and alias != HISTORY_ALIAS:
        raise StorageFacadeError(f"refusing non-stable attach alias {alias!r}")
    # Aliases are fixed identifiers, never user input, but still refuse quotes.
    if not alias.isidentifier():
        raise StorageFacadeError(f"invalid attach alias {alias!r}")
    return alias


def _attach_ro(
    con: sqlite3.Connection,
    *,
    alias: str,
    path: Path,
    tables: Iterable[str],
) -> bool:
    """ATTACH `path` as `alias` and project missing tables via TEMP VIEWs.

    Returns True when the attach was performed. Skips when the file is missing,
    is the same path as main, or contains none of the expected tables.
    """
    alias = _safe_alias(alias)
    if not path.is_file():
        return False
    main_path = Path(
        con.execute("PRAGMA database_list").fetchone()[2]  # (seq, name, file)
    ).resolve()
    if path.resolve() == main_path:
        return False

    # Probe without permanently attaching: open a throwaway connection.
    probe = sqlite3.connect(str(path.resolve()))
    try:
        present = {
            row[0]
            for row in probe.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
    finally:
        probe.close()

    wanted = set(tables) & present
    if not wanted:
        return False

    # Plain path ATTACH (URI mode=ro is flaky on Windows for ATTACH). The
    # connection-wide PRAGMA query_only = ON after setup freezes writes on
    # main and every attached schema.
    con.execute(f"ATTACH DATABASE ? AS {alias}", (str(path.resolve()),))

    for table in sorted(wanted):
        # Monolith residual: table still lives on main → leave it; the physical
        # split has not moved this table yet. Facade still works; parity tests
        # use a true split where main no longer has these tables.
        if _main_has_table(con, table):
            continue
        # TEMP lives in the connection-local temp store; unqualified names hit
        # temp first, so existing `FROM {table}` SQL keeps working.
        con.execute(
            f'CREATE TEMP VIEW "{table}" AS SELECT * FROM "{alias}"."{table}"'
        )
    return True


def open_query_connection(
    settings: Settings | None = None,
    *,
    core_path: Path | None = None,
    inflections_path: Path | None = None,
    layers_path: Path | None = None,
) -> sqlite3.Connection:
    """Open the read-only multi-DB query facade.

    Parameters override settings paths (tests inject a split pack without
    mutating process-wide settings). History is never attached.
    """
    settings = settings or get_settings()
    core = Path(core_path) if core_path is not None else settings.core_db
    inflections = (
        Path(inflections_path)
        if inflections_path is not None
        else settings.inflections_db
    )
    layers = Path(layers_path) if layers_path is not None else settings.layers_db

    if not core.is_file():
        raise StorageFacadeError(
            f"core DB missing at {core} — set KOSHA_CORE_DB_PATH or build the store"
        )

    # Open without URI mode=ro: TEMP VIEWs that project attached tables into the
    # unqualified namespace require a writable temp store, and SQLite refuses
    # CREATE TEMP VIEW on a mode=ro connection. Read-only is enforced after
    # setup via PRAGMA query_only (covers main + attached).
    con = sqlite3.connect(str(core.resolve()))
    con.row_factory = sqlite3.Row

    _attach_ro(
        con, alias="inflections", path=inflections, tables=INFLECTIONS_TABLES
    )
    _attach_ro(con, alias="layers", path=layers, tables=LAYERS_TABLES)

    # Hard guard: history must never appear on the dictionary query path.
    aliases = {row[1] for row in con.execute("PRAGMA database_list")}
    if HISTORY_ALIAS in aliases:
        con.close()
        raise StorageFacadeError(
            "history alias mounted on the query facade — this is a bug; "
            "history is a separate writable store gated by KOSHA_HISTORY_ENABLED"
        )

    # Lock writes after TEMP VIEW setup. query_only applies to the whole
    # connection, including attached schemas.
    con.execute("PRAGMA query_only = ON")
    return con


def attached_aliases(con: sqlite3.Connection) -> dict[str, str]:
    """Map attach alias → absolute file path for diagnostics and tests.

    `main` is reported as `core` so callers can key on the architecture name.
    History is never present; if it were, tests would fail the hard guard above.
    """
    out: dict[str, str] = {}
    for _seq, name, file in con.execute("PRAGMA database_list"):
        if not file:
            continue  # temp
        key = "core" if name == "main" else name
        out[key] = str(Path(file).resolve())
    return out


def assert_no_placement_leak(payload: object) -> None:
    """Fail if a response-shaped object mentions physical DB placement.

    Response models must stay free of path / ATTACH-alias / file names (D7).
    Walks dict/list/str leaves only — enough for Salt JSON and sample rows.
    """
    banned_substrings = (
        "kosha.db",
        "kosha_fixture",
        "kosha_inflections",
        "kosha_layers",
        "kosha_history",
        "core.db",
        "inflections.db",
        "layers.db",
        "history.db",
        "KOSHA_CORE_DB",
        "KOSHA_INFLECTIONS",
        "KOSHA_LAYERS",
        "ATTACH ",
        "database_list",
    )
    # Schema aliases as standalone placement leaks when they appear as values.
    banned_exact = {"core", "inflections", "layers", "history", "main", "temp"}

    def walk(node: object, path: str = "$") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                key_l = str(key).lower()
                if any(b.lower() in key_l for b in ("db_path", "database_path", "attach_alias", "sqlite_path")):
                    raise AssertionError(
                        f"placement leak at {path}.{key}: response key names a physical store"
                    )
                walk(value, f"{path}.{key}")
            return
        if isinstance(node, (list, tuple)):
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")
            return
        if isinstance(node, str):
            low = node.lower()
            for banned in banned_substrings:
                if banned.lower() in low:
                    raise AssertionError(
                        f"placement leak at {path}: {node!r} mentions {banned!r}"
                    )
            if node in banned_exact and path.endswith(
                (".db", ".database", ".alias", ".schema")
            ):
                raise AssertionError(f"placement leak at {path}: {node!r}")
            return
        # numbers / None / bool — fine

    walk(payload)
