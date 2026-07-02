"""kosha D2 — entry loader + per-dict <pc> dispatcher.

Primary source (max Salt reuse, PHASE1_PLAN.md D2): csl-sqlite releases
(https://github.com/sanskrit-lexicon/csl-sqlite/releases), the same data
layer csl-apidev's Salt implementation reads via Dal. Each {dict}.zip
contains a {dict}.sqlite with columns (key, lnum, data) where `data` is
the raw csl-orig <H1>...</H1> record (A1: stored verbatim).

Usage: called by build_db.py --stage entries --dicts mw,pwg,ap90.
Standalone:
    python scripts/build_entries.py --dicts mw,pwg,ap90 --release latest
"""
import argparse
import re
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DL_DIR = ROOT / "data" / "raw_sqlite"

RE_PC = re.compile(r"<pc>([^<]*)</pc>")
RE_KEY2 = re.compile(r"<key2>(.*?)</key2>", re.S)
RE_L = re.compile(r"<L>([^<]*)</L>")

# csl-orig commit is not embedded in the csl-sqlite release; recorded as
# "csl-sqlite release tag" per ARCHITECTURE §Maximum-reuse-rules point 3
# (sources records BOTH the csl-sqlite release tag and the underlying
# csl-orig commit — the latter is not exposed by this release format and
# is left for a future D2 refinement to resolve via the csl-orig repo's
# own commit log for the matching data snapshot).
DICT_META = {
    "mw": {"title": "Monier-Williams Sanskrit-English Dictionary", "pc_format": "page,col"},
    "pwg": {"title": "Petersburger Wörterbuch (large)", "pc_format": "vol-page"},
    "ap90": {"title": "Apte Sanskrit-English Dictionary of 1890", "pc_format": "page-col"},
}


def parse_pc(dict_code, pc_raw):
    """Dispatch by per-dict <pc> shape. Returns (vol, page, col) — any may be None."""
    if not pc_raw:
        return None, None, None
    if dict_code == "mw":
        # 'page,col' — col occasionally carries a trailing letter suffix (e.g. '741,3x')
        m = re.match(r"^(\d+),(\d+)([a-zA-Z]?)$", pc_raw)
        if not m:
            return None, None, None
        page, col, suffix = m.groups()
        return None, int(page), col + suffix if suffix else col
    if dict_code == "pwg":
        # 'vol-page', 7 volumes
        m = re.match(r"^(\d+)-(\d+)$", pc_raw)
        if not m:
            return None, None, None
        vol, page = m.groups()
        return int(vol), int(page), None
    if dict_code == "ap90":
        # 'page-col' where col is usually a letter (a/b/c), rarely numeric
        m = re.match(r"^(\d+)-(\w+)$", pc_raw)
        if not m:
            return None, None, None
        page, col = m.groups()
        return None, int(page), col
    return None, None, None


def fetch_release_sqlite(dict_code, release_tag="latest"):
    """Download+extract {dict}.zip from the csl-sqlite release via gh CLI. Cached under
    data/raw_sqlite/ (gitignored — regenerable, not a committed asset)."""
    out_dir = DL_DIR / dict_code
    sqlite_path = out_dir / f"{dict_code}.sqlite"
    tag_file = out_dir / "RELEASE_TAG.txt"
    if sqlite_path.exists():
        cached_tag = tag_file.read_text(encoding="utf-8").strip() if tag_file.exists() else "unknown (pre-existing cache, no RELEASE_TAG.txt)"
        return sqlite_path, cached_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{dict_code}.zip"
    if release_tag == "latest":
        release_tag = subprocess.run(
            ["gh", "release", "list", "--repo", "sanskrit-lexicon/csl-sqlite",
             "--limit", "1", "--json", "tagName", "--jq", ".[0].tagName"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    subprocess.run(
        ["gh", "release", "download", release_tag, "--repo", "sanskrit-lexicon/csl-sqlite",
         "-p", f"{dict_code}.zip", "-D", str(out_dir), "--clobber"],
        check=True,
    )
    with zipfile.ZipFile(zip_path) as zf:
        zf.extract(f"{dict_code}.sqlite", out_dir)
    tag_file.write_text(release_tag, encoding="utf-8")
    return sqlite_path, release_tag


def build_entries(con, dict_codes, release_tag="latest"):
    con.execute("DELETE FROM entries WHERE dict IN ({})".format(
        ",".join("?" * len(dict_codes))), dict_codes)
    con.execute("DELETE FROM sources WHERE dict IN ({})".format(
        ",".join("?" * len(dict_codes))), dict_codes)

    for dict_code in dict_codes:
        if dict_code not in DICT_META:
            print(f"[D2] skip {dict_code}: no DICT_META entry (only mw/pwg/ap90 wired)")
            continue
        sqlite_path, resolved_tag = fetch_release_sqlite(dict_code, release_tag)
        src = sqlite3.connect(sqlite_path)
        rows = src.execute(f"SELECT key, lnum, data FROM {dict_code}").fetchall()
        src.close()

        n_total = len(rows)
        n_pc = 0
        insert_rows = []
        for key, lnum, data in rows:
            pc_m = RE_PC.search(data)
            pc_raw = pc_m.group(1) if pc_m else None
            if pc_raw:
                n_pc += 1
            vol, page, col = parse_pc(dict_code, pc_raw)
            k2_m = RE_KEY2.search(data)
            k2 = k2_m.group(1) if k2_m else None
            l_m = RE_L.search(data)
            L = l_m.group(1) if l_m else str(lnum)
            insert_rows.append((dict_code, L, key, k2, pc_raw, vol, page, col, data))

        con.executemany(
            "INSERT OR REPLACE INTO entries (dict, L, slp1_key, k2, pc_raw, vol, page, col, body) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            insert_rows,
        )
        # D2 fallback sense rule: single sense spanning the whole body (ARCHITECTURE.md
        # senses table doc — "always mintable" fallback). Per-dict sense-marker
        # segmentation is flagged as follow-on refinement, not blocking D2/D4.
        entry_ids = con.execute(
            "SELECT id, LENGTH(body) FROM entries WHERE dict=?", (dict_code,)
        ).fetchall()
        con.execute("DELETE FROM senses WHERE entry_id IN (SELECT id FROM entries WHERE dict=?)", (dict_code,))
        con.executemany(
            "INSERT INTO senses (entry_id, sense_n, span_start, span_end) VALUES (?,1,0,?)",
            entry_ids,
        )

        coverage = round(n_pc / n_total * 100, 2) if n_total else 0.0
        meta = DICT_META[dict_code]
        con.execute(
            "INSERT INTO sources (dict, title, edition, csl_orig_commit, source_path, "
            "pc_format, pc_coverage, entry_count) VALUES (?,?,?,?,?,?,?,?)",
            (dict_code, meta["title"], None,
             f"csl-sqlite release {resolved_tag} (csl-orig commit not exposed by this release format)",
             f"csl-sqlite/{dict_code}.zip", meta["pc_format"], coverage, n_total),
        )
        con.commit()
        print(f"[D2] {dict_code}: {n_total} entries, pc coverage {coverage}% ({meta['pc_format']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dicts", default="mw,pwg,ap90")
    ap.add_argument("--release", default="latest")
    ap.add_argument("--db", default=str(ROOT / "data" / "db" / "kosha.db"))
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    build_entries(con, args.dicts.split(","), args.release)
    con.close()


if __name__ == "__main__":
    main()
