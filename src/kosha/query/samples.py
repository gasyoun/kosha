"""Frozen monolith query samples for multi-DB parity (W1A, H2341).

These are the queries the storage facade must answer identically on a monolith
and on a core+inflections+layers attach layout — results only, no placement
metadata. Overlaps W0 serializer/repository cases where applicable and adds
inflections + layer probes the eventual physical split will isolate.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Callable

from kosha.api import repository

#: One sample = (name, runner). Runner returns a JSON-serialisable value.
SampleRunner = Callable[[sqlite3.Connection], Any]


def _rows_as_tuples(rows: list[sqlite3.Row] | list[tuple]) -> list[tuple]:
    out: list[tuple] = []
    for row in rows:
        if isinstance(row, sqlite3.Row):
            out.append(tuple(row))
        else:
            out.append(tuple(row))
    return out


def _data_version(con: sqlite3.Connection) -> str:
    return repository.data_version(con)


def _pick_lemma(con: sqlite3.Connection) -> str | None:
    row = con.execute(
        "SELECT slp1_key, COUNT(DISTINCT dict) AS n FROM entries "
        "GROUP BY slp1_key ORDER BY n DESC, slp1_key LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    return row[0] if not isinstance(row, sqlite3.Row) else row["slp1_key"]


def _entries_for_best_lemma(con: sqlite3.Connection) -> list[tuple]:
    lemma = _pick_lemma(con)
    if lemma is None:
        return []
    pairs = repository.entries_for_key_across_dicts(con, lemma)
    # (dict, L, slp1_key, hom_count) — drop body so placement-free + stable size
    return [
        (row["dict"], row["L"], row["slp1_key"], hom)
        for row, hom in pairs
    ]


def _sense_for_first_entry(con: sqlite3.Connection) -> list[tuple]:
    row = con.execute(
        "SELECT id FROM entries ORDER BY dict, L LIMIT 1"
    ).fetchone()
    if row is None:
        return []
    eid = row[0] if not isinstance(row, sqlite3.Row) else row["id"]
    return _rows_as_tuples(repository.sense_rows(con, eid))


def _lemma_row_best(con: sqlite3.Connection) -> tuple | None:
    lemma = _pick_lemma(con)
    if lemma is None:
        return None
    row = repository.lemma_row(con, lemma)
    if row is None:
        return None
    # lemmas may gain columns; pin to identity fields
    keys = row.keys() if isinstance(row, sqlite3.Row) else []
    if "slp1" in keys:
        return (row["slp1"], row["iast"] if "iast" in keys else None)
    return tuple(row)[:2]


def _heritage_best(con: sqlite3.Connection) -> Any:
    lemma = _pick_lemma(con)
    if lemma is None:
        return None
    row = repository.heritage_row(con, lemma)
    if row is False:
        return "no-table"
    if row is None:
        return None
    return (row["covered"], row["anchor"] if "anchor" in row.keys() else None)


def _forms_count(con: sqlite3.Connection) -> int:
    try:
        return con.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
    except sqlite3.OperationalError:
        return -1


def _inflections_for_lemma(con: sqlite3.Connection) -> list[tuple]:
    lemma = _pick_lemma(con)
    if lemma is None:
        return []
    try:
        rows = con.execute(
            "SELECT form_slp1, lemma_slp1, model, source FROM inflections "
            "WHERE lemma_slp1=? ORDER BY form_slp1, model, source LIMIT 50",
            (lemma,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return _rows_as_tuples(rows)


def _stem_bridge_sample(con: sqlite3.Connection) -> list[tuple]:
    try:
        rows = con.execute(
            "SELECT variant_slp1, canonical_slp1, rule FROM stem_bridge "
            "ORDER BY variant_slp1 LIMIT 20"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return _rows_as_tuples(rows)


def _sense_frequency_sample(con: sqlite3.Connection) -> list[tuple]:
    lemma = _pick_lemma(con)
    if lemma is None:
        return []
    try:
        rows = con.execute(
            "SELECT * FROM sense_frequency WHERE lemma_slp1=? "
            "ORDER BY 1 LIMIT 20",
            (lemma,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return _rows_as_tuples(rows)


def _coverage_sample(con: sqlite3.Connection) -> list[tuple]:
    lemma = _pick_lemma(con)
    if lemma is None:
        return []
    try:
        rows = con.execute(
            "SELECT * FROM dict_corpus_coverage WHERE slp1=? LIMIT 5",
            (lemma,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return _rows_as_tuples(rows)


def _roots_frequency_count(con: sqlite3.Connection) -> int:
    try:
        return con.execute("SELECT COUNT(*) FROM roots_frequency").fetchone()[0]
    except sqlite3.OperationalError:
        return -1


def _history_tables_visible(con: sqlite3.Connection) -> list[str]:
    """Must stay empty on the query facade (history is a separate store)."""
    found: list[str] = []
    for name in ("visitors", "search_events", "daily_rollup", "magic_links"):
        try:
            con.execute(f"SELECT 1 FROM {name} LIMIT 1")
            found.append(name)
        except sqlite3.OperationalError:
            pass
    return found


GOLDEN_SAMPLE_QUERIES: list[tuple[str, SampleRunner]] = [
    ("data_version", _data_version),
    ("entries_for_best_lemma", _entries_for_best_lemma),
    ("sense_for_first_entry", _sense_for_first_entry),
    ("lemma_row_best", _lemma_row_best),
    ("heritage_best", _heritage_best),
    ("forms_count", _forms_count),
    ("inflections_for_lemma", _inflections_for_lemma),
    ("stem_bridge_sample", _stem_bridge_sample),
    ("sense_frequency_sample", _sense_frequency_sample),
    ("coverage_sample", _coverage_sample),
    ("roots_frequency_count", _roots_frequency_count),
    ("history_tables_visible", _history_tables_visible),
]


def run_sample_queries(con: sqlite3.Connection) -> dict[str, Any]:
    """Execute every frozen sample; returns name → result."""
    return {name: runner(con) for name, runner in GOLDEN_SAMPLE_QUERIES}
