"""kosha — data-version archive + citation resolution (RISKS.md R1).

A2 mints citations `{dict}.{L}.{senseN}@{data_version}`. For the citation to
survive Cologne corrections (R1), an *old* `@version` must keep resolving to
the sense text as it was in that release, even after a rebuild renumbers or
rewrites senses. This module is the resolution mechanism.

**Per-version archive.** Each published rebuild dumps its senses into
`{releases_dir}/{version}/senses.sqlite` (a compact, indexed
`archive(sense_id PK, dict, L, sense_n, text_raw, headword)`). `releases_dir`
defaults to `data/releases/` and is overridable via `KOSHA_RELEASES_DIR` (tests
point it at a fixture dir; builds/CI can point it at mounted release assets).
The archive is the same artifact that ships as a GitHub release asset (R1c) —
one dump, two uses: browser resolution here, and the sense_crosswalk diff
(scripts/build_crosswalk.py, Commitment 2).

`data/releases/` is bulk + regenerable → gitignored (RISKS.md R11: data ships
as release assets, not in-repo). The mechanism and its tests live in git; the
dumps do not.
"""
import os
import re
import sqlite3
from pathlib import Path

_APP = Path(__file__).resolve().parent
_ROOT = _APP.parent

# dict.L.n where L may itself contain dots (suffixed L-numbers, e.g. ap90 455.2)
# and n is the final dotted segment. The @version is split off FIRST so a
# dotted version (9.9.9) can't be mistaken for part of L/n.
_RE_SENSE_BASE = re.compile(r"^(?P<dict>[^.]+)\.(?P<L>.+)\.(?P<n>\d+)$")


def releases_dir() -> Path:
    return Path(os.getenv("KOSHA_RELEASES_DIR", str(_ROOT / "data" / "releases")))


def parse_sense_id(sense_id: str):
    """(dict, L, sense_n:int, version|None). None on malformed input."""
    base, _, version = sense_id.partition("@")
    m = _RE_SENSE_BASE.match(base)
    if not m:
        return None
    return m.group("dict"), m.group("L"), int(m.group("n")), (version or None)


def archive_db_path(version: str) -> Path:
    return releases_dir() / version / "senses.sqlite"


def has_archive(version: str) -> bool:
    return archive_db_path(version).exists()


ARCHIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS archive (
    sense_id TEXT PRIMARY KEY,
    dict TEXT NOT NULL, L TEXT NOT NULL, sense_n INTEGER NOT NULL,
    headword TEXT, text_raw TEXT NOT NULL
);
"""


def resolve_sense(version: str, sense_id: str):
    """Look up an archived sense by its full id (with or without the @version
    suffix — the suffix, if present, must match `version`). Returns a dict or
    None if the version is not archived or the id is absent from it."""
    path = archive_db_path(version)
    if not path.exists():
        return None
    # Match on the id *without* the @version suffix (archive keys are stored
    # bare so a dump is version-agnostic in its own directory).
    bare = sense_id.split("@", 1)[0]
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            "SELECT * FROM archive WHERE sense_id=?", (bare,)).fetchone()
    finally:
        con.close()
    return dict(row) if row else None


def write_archive(version: str, senses):
    """Freeze `senses` (iterable of dicts: sense_id, dict, L, sense_n,
    headword, text_raw) into the version's archive sqlite. Idempotent."""
    path = archive_db_path(version)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    try:
        con.executescript(ARCHIVE_SCHEMA)
        con.execute("DELETE FROM archive")
        con.executemany(
            "INSERT OR REPLACE INTO archive "
            "(sense_id, dict, L, sense_n, headword, text_raw) VALUES "
            "(:sense_id, :dict, :L, :sense_n, :headword, :text_raw)",
            list(senses),
        )
        con.commit()
    finally:
        con.close()
    return path
