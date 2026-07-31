"""kosha — the one entry-reading query layer (W0C item 2, H1945).

Four surfaces answer "what does the dictionary say about this headword":
`/api/v1/lemma`, the `/dicts/*` Salt faces, the prerendered static cards, and
the `/w/{slp1}` SSR page. Before W0C each of them wrote its own SQL against
`entries`/`senses`/`lemmas`/`heritage_anchor`, and the copies had already
drifted — the static builder silently omitted the `raw` branch, and the Salt
face selected a narrower column list than the API, so an entry served through
`/dicts/mw` could carry provenance the same entry served through `/api/v1`
did not.

This module is the single reader. It returns rows, not payloads: shaping is
`kosha.api.serializer`'s job, and keeping the two apart is what lets the
serializer be tested against hand-built rows with no database at all.

Local-first (A3): every function takes an already-open read-only connection.
Nothing here opens, writes, or migrates a store.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Iterable, Sequence

#: The dictionaries kosha serves. Ordered — this is the order entries appear in
#: a merged lemma card, so it is part of the response contract, not a detail.
ALL_DICTS: tuple[str, ...] = ("mw", "pwg", "ap90")

#: Every column the serializer needs. Named explicitly rather than `SELECT *`
#: so a schema change surfaces here instead of as a missing key three layers up.
_ENTRY_COLUMNS = "id, dict, L, slp1_key, k2, pc_raw, vol, page, col, body"


def data_version(con: sqlite3.Connection) -> str:
    """The build id every sense id and citation in a response is pinned to."""
    row = con.execute("SELECT value FROM meta WHERE key='data_version'").fetchone()
    return row["value"] if row else "0.0.0-dev"


def entries_for_key(
    con: sqlite3.Connection, dict_code: str, slp1_key: str
) -> list[sqlite3.Row]:
    """The homonym group for one (dict, headword) — the set Salt ids are minted
    against, so it must be the *whole* group even when the caller wants one
    row: an id's `-1`/`-2` suffix is only correct relative to the full group.
    """
    return con.execute(
        f"SELECT {_ENTRY_COLUMNS} FROM entries WHERE dict=? AND slp1_key=? ORDER BY L",
        (dict_code, slp1_key),
    ).fetchall()


def entries_for_key_across_dicts(
    con: sqlite3.Connection, slp1_key: str, dicts: Sequence[str] = ALL_DICTS
) -> list[tuple[sqlite3.Row, int]]:
    """Every entry for a headword across `dicts`, each paired with its homonym
    count. This is the lemma-card query — one call replaces the per-dict loop
    the API, the SSR route and the static builder each wrote separately.
    """
    out: list[tuple[sqlite3.Row, int]] = []
    for dict_code in dicts:
        rows = entries_for_key(con, dict_code, slp1_key)
        out.extend((row, len(rows)) for row in rows)
    return out


def entry_by_lnum(
    con: sqlite3.Connection, dict_code: str, lnum: str
) -> sqlite3.Row | None:
    return con.execute(
        f"SELECT {_ENTRY_COLUMNS} FROM entries WHERE dict=? AND L=?",
        (dict_code, lnum),
    ).fetchone()


def sense_rows(con: sqlite3.Connection, entry_id: int) -> list[sqlite3.Row]:
    """Sense spans for one entry, in printed order."""
    return con.execute(
        "SELECT sense_n, span_start, span_end FROM senses WHERE entry_id=? "
        "ORDER BY sense_n",
        (entry_id,),
    ).fetchall()


def lemma_row(con: sqlite3.Connection, slp1_key: str) -> sqlite3.Row | None:
    """The union-spine row carrying the P3 evidence columns.

    Keyed off the *entry's own* `slp1_key`, never the caller's query string:
    homonym-suffixed entries under one headword must still resolve their own
    lemma row.
    """
    return con.execute("SELECT * FROM lemmas WHERE slp1=?", (slp1_key,)).fetchone()


def heritage_row(con: sqlite3.Connection, slp1_key: str) -> sqlite3.Row | None | bool:
    """H345 Heritage coverage witness.

    Three-valued on purpose, and the third value is the point: `False` means
    *this build has no heritage_anchor table at all* (a pre-H345 or partial
    DB), which is not the same fact as "this headword is not covered". The
    serializer maps the two to `heritage: null` and `{covered: false}`
    respectively, so a missing layer can never be read as a negative finding.
    """
    try:
        return con.execute(
            "SELECT covered, anchor FROM heritage_anchor WHERE mw_key1=?",
            (slp1_key,),
        ).fetchone()
    except sqlite3.OperationalError:
        return False


def distinct_keys(
    con: sqlite3.Connection,
    dict_code: str,
    where: str,
    params: Iterable[Any],
    limit: int,
) -> list[str]:
    """Headword keys matching a Salt-face search, capped at `size`."""
    rows = con.execute(
        f"SELECT DISTINCT slp1_key FROM entries WHERE dict=? AND {where} "
        "ORDER BY slp1_key LIMIT ?",
        (dict_code, *params, limit),
    ).fetchall()
    return [row["slp1_key"] for row in rows]


def prefix_range_bound(prefix: str) -> str:
    """Exclusive upper bound for a half-open prefix seek (H838).

    `slp1 >= p AND slp1 < bound` hits the index as a seek, where
    `LIKE p||'%'` forces a scan *and* is case-insensitive by default — which
    would let the case-significant SLP1 prefix `ka` (क) wrongly match `Ka` (ख).
    """
    return prefix[:-1] + chr(ord(prefix[-1]) + 1)
