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

sys.path.insert(0, str(ROOT / "app"))
from segment import segment  # noqa: E402

RE_PC = re.compile(r"<pc>([^<]*)</pc>")
RE_KEY2 = re.compile(r"<key2>(.*?)</key2>", re.S)
RE_L = re.compile(r"<L>([^<]*)</L>")

# csl-orig commit is not embedded in the csl-sqlite release. It is resolved
# (D5) by CROSS-DATING: the latest csl-orig commit touching this dict's source
# file at or before the csl-sqlite release timestamp, read from a local csl-orig
# sibling checkout via `git log` (offline — RISKS.md R12: no live services).
# This is an UPPER BOUND (commit <= release cut time), not a build-exact mapping
# — csl-sqlite may have been built from a slightly earlier snapshot — and is
# labelled as such in the stored value. Falls back to the release tag alone when
# no csl-orig checkout is present. See D5_MEASUREMENTS.md and data/SOURCES.md.
CSL_ORIG_SIBLING = ROOT.parent / "csl-orig"
CSL_ORIG_TXT = {"mw": "v02/mw/mw.txt", "pwg": "v02/pwg/pwg.txt", "ap90": "v02/ap90/ap90.txt"}


def _release_tag_to_datetime(tag):
    """csl-sqlite tags are 'YYYY-MM-DD-HH-MM-SS'. -> 'YYYY-MM-DD HH:MM:SS' for git,
    or None if the tag isn't in that shape."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})$", tag or "")
    if not m:
        return None
    y, mo, d, h, mi, s = m.groups()
    return f"{y}-{mo}-{d} {h}:{mi}:{s}"


def cross_date_csl_orig_commit(dict_code, release_tag, csl_orig=CSL_ORIG_SIBLING):
    """Resolve sources.csl_orig_commit by cross-dating against a local csl-orig
    checkout. Returns a labelled provenance string. Offline; graceful fallback."""
    base = f"csl-sqlite release {release_tag}"
    when = _release_tag_to_datetime(release_tag)
    relpath = CSL_ORIG_TXT.get(dict_code)
    if when is None or relpath is None or not (csl_orig / ".git").exists():
        return f"{base} (csl-orig commit not resolved: no local csl-orig checkout)"
    try:
        out = subprocess.run(
            ["git", "-C", str(csl_orig), "log", "-1", "--format=%H %cs",
             "--before", when, "--", relpath],
            capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return f"{base} (csl-orig commit not resolved: git unavailable)"
    if not out:
        return f"{base} (no csl-orig commit for {dict_code} before release)"
    commit, cdate = out.split(" ", 1)
    return (f"{base}; csl-orig<={commit} ({cdate}, cross-dated upper bound, "
            f"latest commit to {relpath} at/before release)")


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


def build_entries(con, dict_codes, release_tag="latest", batch_size=2000):
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
        src_cur = src.execute(f"SELECT key, lnum, data FROM {dict_code}")

        # Streamed in fetchmany batches (H4407): the source dict (up to ~86MB)
        # is never materialized as a Python list, and sense segmentation runs
        # in the SAME pass off the row just inserted (segment() takes the body
        # we already have in hand) rather than a second full SELECT over
        # entries. `cur.lastrowid` is safe here because `entries.id` is a
        # plain `INTEGER PRIMARY KEY` rowid alias and each insert below is a
        # single-row `execute` (not `executemany`, whose lastrowid is not
        # per-row reliable).
        cur = con.cursor()
        n_total = 0
        n_pc = 0
        n_senses = 0
        n_multi = 0
        while True:
            batch = src_cur.fetchmany(batch_size)
            if not batch:
                break
            for key, lnum, data in batch:
                n_total += 1
                pc_m = RE_PC.search(data)
                pc_raw = pc_m.group(1) if pc_m else None
                if pc_raw:
                    n_pc += 1
                vol, page, col = parse_pc(dict_code, pc_raw)
                k2_m = RE_KEY2.search(data)
                k2 = k2_m.group(1) if k2_m else None
                l_m = RE_L.search(data)
                L = l_m.group(1) if l_m else str(lnum)

                # A duplicate (dict, L) triggers the UNIQUE-constraint REPLACE
                # below, which deletes-then-reinserts under a NEW rowid — any
                # senses already inserted against the old rowid this pass
                # would otherwise dangle. Clear them first (cheap: (dict, L)
                # is UNIQUE-indexed, so this is a point lookup, almost always
                # zero rows).
                cur.execute(
                    "DELETE FROM senses WHERE entry_id IN "
                    "(SELECT id FROM entries WHERE dict=? AND L=?)",
                    (dict_code, L),
                )
                cur.execute(
                    "INSERT OR REPLACE INTO entries (dict, L, slp1_key, k2, pc_raw, vol, page, col, body) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (dict_code, L, key, k2, pc_raw, vol, page, col, data),
                )
                eid = cur.lastrowid

                # D2 per-dict sense segmentation (app/segment.py): split each
                # body at its <div> division markers — the same boundaries
                # basicdisplay.php renders — into byte-anchored senseN spans
                # (A2). Entries with no <div> keep the single-sense fallback
                # ("always mintable", ARCHITECTURE.md).
                spans = segment(dict_code, data)
                if len(spans) > 1:
                    n_multi += 1
                for sense_n, (s0, s1) in enumerate(spans, start=1):
                    cur.execute(
                        "INSERT INTO senses (entry_id, sense_n, span_start, span_end) VALUES (?,?,?,?)",
                        (eid, sense_n, s0, s1),
                    )
                    n_senses += 1
            con.commit()
        src.close()

        coverage = round(n_pc / n_total * 100, 2) if n_total else 0.0
        meta = DICT_META[dict_code]
        con.execute(
            "INSERT INTO sources (dict, title, edition, csl_orig_commit, source_path, "
            "pc_format, pc_coverage, entry_count) VALUES (?,?,?,?,?,?,?,?)",
            (dict_code, meta["title"], None,
             cross_date_csl_orig_commit(dict_code, resolved_tag),
             f"csl-sqlite/{dict_code}.zip", meta["pc_format"], coverage, n_total),
        )
        con.commit()
        print(f"[D2] {dict_code}: {n_total} entries, pc coverage {coverage}% "
              f"({meta['pc_format']}); {n_senses} senses "
              f"({n_multi} multi-sense entries)")


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
