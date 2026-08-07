"""Split a monolith kosha.db into the D7 multi-file layout (W1A, H2341).

This is a **test / parity** tool, not the production bulk move. W1A builds the
repository facade *before* any production data migration: freeze monolith
query samples, split a copy into core/inflections/layers, and prove parity.

Tables land on files per ARCHITECTURE_KOSHA_PLATFORM.md § Storage facade.
Indexes and sqlite_sequence rows travel with their tables. The source file is
never modified.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .connection import CORE_TABLES, INFLECTIONS_TABLES, LAYERS_TABLES, _ro_uri


def _copy_tables(
    src: sqlite3.Connection,
    dest_path: Path,
    tables: set[str],
    *,
    present: set[str],
) -> list[str]:
    """Create `dest_path` with a subset of `src` tables. Returns copied names."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists():
        dest_path.unlink()
    dest = sqlite3.connect(str(dest_path))
    try:
        dest.execute("PRAGMA journal_mode=OFF")
        dest.execute("PRAGMA synchronous=OFF")
        copied: list[str] = []
        for table in sorted(tables & present):
            # Schema including indexes is recreated via sqlite_master sql.
            row = src.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if not row or not row[0]:
                continue
            dest.execute(row[0])
            cols = [
                r[1]
                for r in src.execute(f"PRAGMA table_info({table})").fetchall()
            ]
            col_list = ", ".join(f'"{c}"' for c in cols)
            rows = src.execute(f'SELECT {col_list} FROM "{table}"').fetchall()
            if rows:
                placeholders = ", ".join("?" for _ in cols)
                dest.executemany(
                    f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})',
                    rows,
                )
            # Indexes defined on this table (skip autoindexes).
            for idx_sql, in src.execute(
                "SELECT sql FROM sqlite_master WHERE type='index' "
                "AND tbl_name=? AND sql IS NOT NULL",
                (table,),
            ):
                dest.execute(idx_sql)
            copied.append(table)
        dest.commit()
        return copied
    finally:
        dest.close()


def split_monolith_to_facade(
    monolith: Path,
    *,
    core_out: Path,
    inflections_out: Path,
    layers_out: Path,
) -> dict[str, list[str]]:
    """Write three RO-ready files from a monolith. Source is read-only.

    Returns `{alias: [copied_table, …]}` for the three targets. Raises if the
    monolith has none of the expected core tables (not a kosha store).
    """
    monolith = Path(monolith)
    if not monolith.is_file():
        raise FileNotFoundError(monolith)

    try:
        src = sqlite3.connect(_ro_uri(monolith), uri=True)
    except sqlite3.OperationalError:
        # Fallback for odd path shapes; still never write the source.
        src = sqlite3.connect(str(monolith))
    present = {
        r[0]
        for r in src.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }

    try:
        if not (CORE_TABLES & present):
            raise ValueError(
                f"{monolith} has no core tables {sorted(CORE_TABLES)}; "
                f"present={sorted(present)}"
            )
        result = {
            "core": _copy_tables(src, Path(core_out), set(CORE_TABLES), present=present),
            "inflections": _copy_tables(
                src, Path(inflections_out), set(INFLECTIONS_TABLES), present=present
            ),
            "layers": _copy_tables(
                src, Path(layers_out), set(LAYERS_TABLES), present=present
            ),
        }
        return result
    finally:
        src.close()
