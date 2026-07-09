"""kosha — print co-location ("which words shared a printed page/column").

Every dictionary entry carries a `<pc>` marker that scripts/build_entries.py
parse_pc() splits into (vol, page, col) on the `entries` table. For PWG the
`<pc>` is `vol-Spalte` (e.g. `1-0004` -> vol=1, page=4), so kosha's `page`
column IS the Böhtlingk-Roth column (Spalte) — the same value scan_resolver
feeds to servepdf.php. Grouping entries by (dict, vol, page) therefore recovers
exactly the set of headwords that physically sat together on one printed
column; the book prints two columns per leaf, so `merge=2` folds column pairs
into one physical page (page P -> columns 2P-1, 2P).

MW/AP90 store vol=None (single-volume) and their own page granularity; this
module is dict-agnostic — it groups on whatever (vol, page) the entry carries.
Entries with an unparseable `<pc>` (vol/page NULL) have no location and are
simply absent from every group (the G-PC fail-closed rule, EVAL_PLAN.md §4).
"""
import sqlite3


def _loc_clause(vol):
    """SQL fragment + params for a possibly-NULL vol (mw/ap90 carry vol=None)."""
    if vol is None:
        return "vol IS NULL", []
    return "vol = ?", [int(vol)]


def entry_location(con: sqlite3.Connection, dict_code: str, L: str):
    """(dict, L) -> the entry's own location row, or None if L is unknown."""
    return con.execute(
        "SELECT id, dict, L, slp1_key, pc_raw, vol, page, col "
        "FROM entries WHERE dict = ? AND L = ?",
        (dict_code, L),
    ).fetchone()


def column_entries(con: sqlite3.Connection, dict_code: str, vol, page):
    """All entries on ONE printed column (dict, vol, page), ordered as printed (by L)."""
    where, params = _loc_clause(vol)
    return con.execute(
        f"SELECT id, dict, L, slp1_key, pc_raw, vol, page, col "
        f"FROM entries WHERE dict = ? AND {where} AND page = ? "
        f"ORDER BY CAST(L AS REAL), L",
        [dict_code, *params, int(page)],
    ).fetchall()


def physical_page_entries(con: sqlite3.Connection, dict_code: str, vol, phys_page):
    """All entries on one physical leaf = the two columns 2P-1 and 2P, ordered as printed."""
    where, params = _loc_clause(vol)
    lo, hi = 2 * int(phys_page) - 1, 2 * int(phys_page)
    return con.execute(
        f"SELECT id, dict, L, slp1_key, pc_raw, vol, page, col "
        f"FROM entries WHERE dict = ? AND {where} AND page BETWEEN ? AND ? "
        f"ORDER BY page, CAST(L AS REAL), L",
        [dict_code, *params, lo, hi],
    ).fetchall()


def group_label(dict_code: str, vol, page, *, merge: bool = False):
    """Human-facing label for a group, e.g. 'pwg 1-0004' (column) / 'pwg 1-p0002' (page)."""
    unit = f"p{page:04d}" if merge else f"{page:04d}"
    return f"{dict_code} {vol}-{unit}" if vol is not None else f"{dict_code} {unit}"
