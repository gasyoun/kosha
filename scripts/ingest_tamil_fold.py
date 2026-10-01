"""kosha — ingest the csl-santam Tamil/Capeller/MW corpus fold (Wave 4, H4178).

csl-santam ships ONE combined sqlite table ``tamil(id, st, en)`` where ``id``
is the lexicon number (1=mwd Cologne Digital Sanskrit Lexicon, 2=cap Capeller,
3=otl Cologne Online Tamil Lexicon, 4=cpd Pahlavi — excluded from csl-santam's
own "all" searches). This is the estate's only copy of the Cologne Tamil
Lexicon and Capeller breadth (321,620 entries across mwd+cap+otl at the
08-07-2026 edge snapshot).

Wave 4 of docs/ROADMAP_2026_2027.md says this corpus lands permanently in
kosha. This script performs the FOLD (first consumer-side artifact): it reads
the sibling checkout read-only and builds a lexicon-tagged, provenance-pinned
kosha-side fold. It never mutates the sibling, never re-derives the corpus,
and keeps the source transliteration verbatim (mwd/cap are HK; otl is an
HK-like scheme that csl-santam itself does NOT auto-convert — hk-input.js
lines 14-17; any scheme normalization is a later wave, not this fold's job).

Outputs
-------
* ``data/raw_sqlite/tamil_fold.sqlite`` — the fold (gitignored, regenerable):
  ``tamil_fold(id, lexicon, st, en)`` + ``fold_meta(key, value)`` provenance.
* ``data/tamil/fold_stats.json`` — committed stats + provenance pin
  (source commit, sha256, per-lexicon counts).

Usage:
    python scripts/ingest_tamil_fold.py          # fold + stats
    python scripts/ingest_tamil_fold.py --check  # verify existing fold only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT_DB = ROOT / "data" / "raw_sqlite" / "tamil_fold.sqlite"
STATS_PATH = ROOT / "data" / "tamil" / "fold_stats.json"

# Edge snapshot (interlinks_edges.tsv 08-07-2026): mwd+cap+otl = 321,620 entries.
EDGE_MWD_CAP_OTL = 321_620
LEXICON_BY_ID = {1: "mwd", 2: "cap", 3: "otl", 4: "cpd"}
FOLD_SCHEMA_VERSION = "1.0.0"
SCHEME_NOTES = (
    "st/en kept verbatim from the source fold: mwd/cap use Kyoto-Harvard (HK); "
    "otl uses an HK-like scheme csl-santam itself does not auto-convert "
    "(php/js/hk-input.js lines 14-17) - scheme normalization is a later Wave-4 step."
)


def find_sibling_root() -> Path:
    """Locate the GitHub/ root holding the csl-santam sibling (worktree-safe)."""
    for candidate in (ROOT, *ROOT.parents):
        if (candidate / "csl-santam").is_dir():
            return candidate
    raise SystemExit("csl-santam sibling checkout not found above " + str(ROOT))


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sibling_commit(sibling_repo: Path, file_path: str | None = None) -> str | None:
    """Last commit touching the repo (or just the source file when given)."""
    cmd = ["git", "log", "-1", "--format=%H"]
    if file_path:
        cmd += ["--", file_path]
    try:
        return subprocess.run(
            cmd, cwd=sibling_repo, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return None


def read_source(src: Path) -> tuple[list[tuple[int, str, str]], dict, int]:
    """Read the combined source table, normalizing encoding at fold time.

    The source corpus is Windows-1252-encoded (csl-santam's PHP layer runs a
    per-request ``iconv("Windows-1252","UTF-8")`` workaround — the roadmap's
    Wave-3 flag). The fold retires that workaround: each cell is decoded as
    UTF-8 when it already is, else cp1252; the fallback rate is reported.
    """
    cp1252_fallbacks = 0
    latin1_fallbacks = 0

    def _decode(b: bytes) -> str:
        nonlocal cp1252_fallbacks, latin1_fallbacks
        try:
            return b.decode("utf-8")
        except UnicodeDecodeError:
            pass
        try:
            return b.decode("cp1252")
        except UnicodeDecodeError:
            # stray bytes undefined in cp1252 (e.g. 0x81); latin-1 maps all 256
            latin1_fallbacks += 1
            return b.decode("latin-1")
        finally:
            cp1252_fallbacks += 1

    con = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    con.text_factory = _decode
    try:
        rows = con.execute("SELECT id, st, en FROM tamil ORDER BY id, rowid").fetchall()
        meta = {
            "tables": [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")],
        }
    finally:
        con.close()
    return rows, meta, cp1252_fallbacks, latin1_fallbacks


def build_fold(src: Path) -> dict:
    rows, src_meta, cp1252_fallbacks, latin1_fallbacks = read_source(src)
    total_cells = 2 * len(rows)  # st + en per row
    counts: dict[str, int] = {lex: 0 for lex in LEXICON_BY_ID.values()}
    unknown_ids: set[int] = set()
    for row_id, _, _ in rows:
        lex = LEXICON_BY_ID.get(row_id)
        if lex is None:
            unknown_ids.add(row_id)
        else:
            counts[lex] += 1
    if unknown_ids:
        raise SystemExit(f"unknown lexicon ids in source tamil table: {sorted(unknown_ids)}")

    OUT_DB.parent.mkdir(parents=True, exist_ok=True)
    if OUT_DB.exists():
        OUT_DB.unlink()
    out = sqlite3.connect(OUT_DB)
    try:
        out.executescript(
            """
            PRAGMA journal_mode=OFF;
            CREATE TABLE fold_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE tamil_fold (
                id INTEGER NOT NULL,
                lexicon TEXT NOT NULL CHECK (lexicon IN ('mwd','cap','otl','cpd')),
                st TEXT NOT NULL,
                en TEXT NOT NULL
            );
            """
        )
        tagged = ((row_id, LEXICON_BY_ID[row_id], st, en) for row_id, st, en in rows)
        out.executemany("INSERT INTO tamil_fold(id, lexicon, st, en) VALUES (?,?,?,?)", tagged)
        out.executescript(
            """
            CREATE INDEX idx_tamil_fold_lexicon ON tamil_fold(lexicon);
            CREATE INDEX idx_tamil_fold_st ON tamil_fold(st COLLATE NOCASE);
            """
        )
        mwd_cap_otl = counts["mwd"] + counts["cap"] + counts["otl"]
        meta = {
            "fold_schema_version": FOLD_SCHEMA_VERSION,
            "source_repo": "https://github.com/gasyoun/csl-santam",
            "source_path": "sqlite/tamil.sqlite",
            "source_commit": sibling_commit(src.parent.parent, "sqlite/tamil.sqlite"),
            "source_sha256": sha256_of(src),
            "source_size_bytes": str(src.stat().st_size),
            "source_tables": ",".join(src_meta["tables"]),
            "encoding_normalization": (
                "per-cell UTF-8 with cp1252 fallback (latin-1 for stray "
                "cp1252-undefined bytes). H1513/92d1670 normalized the TEXT export "
                "(sqlite/ganz_utf8.txt) but the shipped sqlite still carries "
                "Windows-1252 cells behind the PHP runtime iconv workaround - this "
                "fold normalizes the sqlite itself, retiring that workaround"
            ),
            "encoding_fallback_cells": str(cp1252_fallbacks),
            "encoding_latin1_stray_cells": str(latin1_fallbacks),
            "scheme_notes": SCHEME_NOTES,
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "builder": "scripts/ingest_tamil_fold.py",
            "handoff": "H4178 flip 2 (csl-santam -> kosha Wave-4 fold, queued -> live)",
            "row_total": str(len(rows)),
            "row_mwd_cap_otl": str(mwd_cap_otl),
            "edge_snapshot_mwd_cap_otl_08_07_2026": str(EDGE_MWD_CAP_OTL),
        }
        out.executemany("INSERT INTO fold_meta(key, value) VALUES (?,?)", meta.items())
        out.commit()
    finally:
        out.close()

    return {
        "counts": counts,
        "total": len(rows),
        "mwd_cap_otl": mwd_cap_otl,
        "source_commit": meta["source_commit"],
        "source_sha256": meta["source_sha256"],
        "source_size_bytes": int(meta["source_size_bytes"]),
        "fold_size_bytes": OUT_DB.stat().st_size,
        "built_at": meta["built_at"],
        "scheme_notes": SCHEME_NOTES,
        "encoding_normalization": meta["encoding_normalization"],
        "encoding_fallback_cells": cp1252_fallbacks,
        "encoding_latin1_stray_cells": latin1_fallbacks,
        "encoding_total_cells": total_cells,
    }


def verify_fold(stats: dict) -> None:
    out = sqlite3.connect(f"file:{OUT_DB}?mode=ro", uri=True)
    try:
        total = out.execute("SELECT COUNT(*) FROM tamil_fold").fetchone()[0]
        by_lex = dict(
            out.execute("SELECT lexicon, COUNT(*) FROM tamil_fold GROUP BY lexicon")
        )
        for lex in ("mwd", "cap", "otl", "cpd"):
            assert by_lex.get(lex) == stats["counts"][lex], f"{lex} count drifted"
        assert total == stats["total"], "fold total drifted"
        # one smoke query per Sanskrit/Tamil lexicon: rows actually retrievable
        for lex in ("mwd", "cap", "otl"):
            hit = out.execute(
                "SELECT 1 FROM tamil_fold WHERE lexicon=? LIMIT 1", (lex,)
            ).fetchone()
            assert hit, f"smoke query returned nothing for {lex}"
    finally:
        out.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the existing fold against the committed stats, build nothing",
    )
    args = parser.parse_args()

    sibling = find_sibling_root() / "csl-santam"
    src = sibling / "sqlite" / "tamil.sqlite"
    if not src.is_file():
        raise SystemExit(f"source corpus not found: {src}")

    if args.check:
        if not OUT_DB.is_file() or not STATS_PATH.is_file():
            raise SystemExit("no existing fold/stats to check; run without --check first")
        stats = json.loads(STATS_PATH.read_text(encoding="utf-8"))
        verify_fold(stats)
        print(f"fold check OK: {stats['total']} rows "
              f"({stats['counts']['mwd']} mwd / {stats['counts']['cap']} cap / "
              f"{stats['counts']['otl']} otl / {stats['counts']['cpd']} cpd)")
        return

    stats = build_fold(src)
    verify_fold(stats)
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset": "tamil-fold",
        **stats,
        "counts_mwd_cap_otl": stats["mwd_cap_otl"],
        "edge_snapshot_mwd_cap_otl_08_07_2026": EDGE_MWD_CAP_OTL,
    }
    STATS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"folded {stats['total']} rows "
        f"(mwd {stats['counts']['mwd']} / cap {stats['counts']['cap']} / "
        f"otl {stats['counts']['otl']} / cpd {stats['counts']['cpd']}) -> {OUT_DB}"
    )
    print(f"mwd+cap+otl = {stats['mwd_cap_otl']} (edge snapshot 08-07-2026: {EDGE_MWD_CAP_OTL})")
    print(f"stats: {STATS_PATH}")


if __name__ == "__main__":
    main()
