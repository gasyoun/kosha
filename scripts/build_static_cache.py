"""build_static_cache.py — P2 Pages static-cache generator (KOSHA_DECISIONS_NEEDED.md D5-3).

Emits the GitHub-Pages static tier from the local kosha.db (never calls live
services — RISKS.md R12; renders from the DB only). Three deliverables:

  1. Sharded per-lemma cards — one JSON file per lemma, NEVER one bundle (a single
     lemmas.json crosses GitHub's 100 MB/file cap at ~33k lemmas). The ~50,355
     lemmas that have BOTH a dict entry AND a corpus attestation
     (count_all IS NOT NULL AND >=1 entry), generated in frequency-rank order so a
     partial / interrupted run always front-loads the highest-value cards
     (top-10k = 95.4% of corpus token mass). Each card is byte-identical to what
     GET /api/v1/lemma/<slp1>?in=slp1 returns. ~155 MB total, ~3 KB/file.
       -> <out-dir>/cards/<token>.json   (gitignored; MG deploys to Pages, A3)

  2. Headword autocomplete index — a single file, all 323,425 lemmas, three fields
     each (slp1, iast, dicts) for search-as-you-type. This is the artifact the
     gitignored docs/js/data/lemmas.json path holds (D5-3a: it is the INDEX, not
     the full cards). A tiny sidecar attested_keys.json lists the tokens that have
     a static card so the UI can pick static-vs-dynamic without a 404 probe.
       -> <out-dir>/js/data/lemmas.json
       -> <out-dir>/js/data/attested_keys.json

  3. Full 222,179-lemma card set (every entry-bearing lemma, not just attested) as
     a release-asset tarball for offline/mirror rebuildability (R1c/R4). Opt-in
     (--full-tarball) because it is ~682 MB; not committed in-repo.
       -> <path>.tar.gz

The card payload is produced by importing app/ directly (render, scan_resolver,
transliterate, db) so it stays in lockstep with the live /api/v1/lemma handler.

Usage:
    python scripts/build_static_cache.py                 # cards + index (default)
    python scripts/build_static_cache.py --limit 5000    # top-5k cards only (smoke / partial)
    python scripts/build_static_cache.py --no-index      # cards only
    python scripts/build_static_cache.py --cards none --index   # index only
    python scripts/build_static_cache.py --full-tarball data/releases/cards_full.tar.gz
    python scripts/build_static_cache.py --force         # re-emit existing card files

Idempotent: a card file that already exists is skipped unless --force, so a run
interrupted mid-way resumes in rank order without redoing work.
"""
import argparse
import io
import json
import sqlite3
import sys
import tarfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from render import render            # noqa: E402
from scan_resolver import scan_url   # noqa: E402
from transliterate import from_slp1_out  # noqa: E402
from evidence import build_evidence  # noqa: E402

DEFAULT_DB = ROOT / "data" / "db" / "kosha.db"
ALL_DICTS = ("mw", "pwg", "ap90")


# --------------------------------------------------------------------------- #
# Filename encoding — a pure function of the SLP1 key, reproducible in JS.
#
# SLP1 is case-SIGNIFICANT (K != k), but Windows/macOS filesystems and many
# checkouts are case-INSENSITIVE, so raw keys collide. We keep [a-z0-9] verbatim
# and escape every other UTF-8 byte (uppercase letters, punctuation, and '_'
# itself) as "_<hexbyte>". Unambiguous, filesystem- and URL-safe, ASCII-only.
#
# JS twin (put in the Pages frontend):
#   function cardToken(slp1){
#     let out='';
#     for(const b of new TextEncoder().encode(slp1)){
#       out += ((b>=97&&b<=122)||(b>=48&&b<=57)) ? String.fromCharCode(b)
#                                                 : '_'+b.toString(16).padStart(2,'0');
#     }
#     return out;                       // fetch(`cards/${out}.json`)
#   }
# --------------------------------------------------------------------------- #
def card_token(slp1: str) -> str:
    out = []
    for b in slp1.encode("utf-8"):
        if (97 <= b <= 122) or (48 <= b <= 57):
            out.append(chr(b))
        else:
            out.append("_%02x" % b)
    return "".join(out)


def open_db(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def data_version(con: sqlite3.Connection) -> str:
    row = con.execute("SELECT value FROM meta WHERE key='data_version'").fetchone()
    return row["value"] if row else "0.0.0-dev"


def entry_payload(con, row, dv, out="iast", raw=False):
    """Mirror of app/main.py::_entry_payload — keep the two in lockstep."""
    payload = {
        "dict": row["dict"], "L": row["L"], "sense_ids": [],
        "scan_url": scan_url(row["dict"], row["page"]),
        "headword": from_slp1_out(row["slp1_key"], out),
        "rendered_html": render(row["dict"], row["body"]),
    }
    if raw:
        payload["raw"] = row["body"]
    senses = con.execute(
        "SELECT sense_n FROM senses WHERE entry_id=? ORDER BY sense_n", (row["id"],)
    ).fetchall()
    payload["sense_ids"] = [f"{row['dict']}.{row['L']}.{s['sense_n']}@{dv}" for s in senses]
    # P3 evidence layer -- mirror app/main.py::_entry_payload's lemma_row join.
    lemma_row = con.execute(
        "SELECT * FROM lemmas WHERE slp1=?", (row["slp1_key"],)
    ).fetchone()
    payload["evidence"] = build_evidence(lemma_row)
    return payload


def lemma_card(con, slp1, dv, out="iast"):
    """Byte-identical to GET /api/v1/lemma/<slp1>?in=slp1&out=<out>."""
    results = []
    for d in ALL_DICTS:
        rows = con.execute(
            "SELECT * FROM entries WHERE dict=? AND slp1_key=? ORDER BY L", (d, slp1)
        ).fetchall()
        for r in rows:
            results.append(entry_payload(con, r, dv, out))
    return {
        "data_version": dv,
        "query": {"key": slp1, "in": "slp1", "out": out, "dicts": list(ALL_DICTS)},
        "results": results,
    }


def _write_json(path: Path, obj):
    # utf-8, NO BOM (CLAUDE.md BOM pitfall); compact but human-diffable.
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))


# --------------------------------------------------------------------------- #
# Deliverable 1 — sharded attested cards (frequency-rank order)
# --------------------------------------------------------------------------- #
def build_cards(con, out_dir: Path, limit=None, force=False):
    dv = data_version(con)
    cards_dir = out_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    sql = (
        "SELECT l.slp1 FROM lemmas l "
        "WHERE l.count_all IS NOT NULL "
        "  AND EXISTS (SELECT 1 FROM entries e WHERE e.slp1_key = l.slp1) "
        "ORDER BY l.rank_all ASC"
    )
    if limit:
        sql += f" LIMIT {int(limit)}"
    keys = [r["slp1"] for r in con.execute(sql).fetchall()]
    total = len(keys)
    print(f"[cards] {total} attested-with-entry lemmas (frequency-ranked) -> {cards_dir}")

    written = skipped = 0
    t0 = time.time()
    for i, slp1 in enumerate(keys, 1):
        path = cards_dir / f"{card_token(slp1)}.json"
        if path.exists() and not force:
            skipped += 1
            continue
        _write_json(path, lemma_card(con, slp1, dv))
        written += 1
        if i % 2000 == 0 or i == total:
            rate = i / max(time.time() - t0, 1e-6)
            print(f"[cards] {i}/{total}  written={written} skipped={skipped}  {rate:.0f}/s")
    print(f"[cards] done: {written} written, {skipped} skipped (already present)")
    return total


# --------------------------------------------------------------------------- #
# Deliverable 2 — autocomplete index + attested-key sidecar
# --------------------------------------------------------------------------- #
def build_index(con, out_dir: Path):
    data_dir = out_dir / "js" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Columnar {fields, rows} keeps the file small (no repeated keys per row).
    rows = con.execute(
        "SELECT slp1, iast, dicts FROM lemmas ORDER BY slp1"
    ).fetchall()
    index = {
        "data_version": data_version(con),
        "fields": ["slp1", "iast", "dicts"],
        "rows": [[r["slp1"], r["iast"], r["dicts"] or ""] for r in rows],
    }
    index_path = data_dir / "lemmas.json"
    _write_json(index_path, index)
    size_mb = index_path.stat().st_size / 1e6
    print(f"[index] {len(index['rows'])} headwords -> {index_path}  ({size_mb:.1f} MB)")

    # Sidecar: sorted card tokens for the attested set, so the UI decides
    # static-card vs dynamic-API without a 404 probe.
    attested = con.execute(
        "SELECT l.slp1 FROM lemmas l "
        "WHERE l.count_all IS NOT NULL "
        "  AND EXISTS (SELECT 1 FROM entries e WHERE e.slp1_key = l.slp1) "
        "ORDER BY l.rank_all ASC"
    ).fetchall()
    tokens = sorted(card_token(r["slp1"]) for r in attested)
    att_path = data_dir / "attested_keys.json"
    _write_json(att_path, {"count": len(tokens), "tokens": tokens})
    print(f"[index] {len(tokens)} attested card tokens -> {att_path}")


# --------------------------------------------------------------------------- #
# Deliverable 3 — full 222k card set as a release tarball (opt-in, ~682 MB)
# --------------------------------------------------------------------------- #
def build_full_tarball(con, tar_path: Path):
    dv = data_version(con)
    tar_path.parent.mkdir(parents=True, exist_ok=True)
    keys = [r["slp1_key"] for r in con.execute(
        "SELECT DISTINCT slp1_key FROM entries ORDER BY slp1_key"
    ).fetchall()]
    total = len(keys)
    print(f"[tarball] {total} entry-bearing lemmas -> {tar_path}")

    t0 = time.time()
    with tarfile.open(tar_path, "w:gz") as tar:
        for i, slp1 in enumerate(keys, 1):
            payload = json.dumps(lemma_card(con, slp1, dv),
                                 ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            info = tarfile.TarInfo(name=f"cards/{card_token(slp1)}.json")
            info.size = len(payload)
            info.mtime = 0  # deterministic archive (no Date.now dependence)
            tar.addfile(info, io.BytesIO(payload))
            if i % 5000 == 0 or i == total:
                rate = i / max(time.time() - t0, 1e-6)
                print(f"[tarball] {i}/{total}  {rate:.0f}/s")
    size_mb = tar_path.stat().st_size / 1e6
    print(f"[tarball] done: {size_mb:.1f} MB")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="path to kosha.db")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "docs",
                    help="Pages output root (default: docs/)")
    ap.add_argument("--cards", choices=["all", "none"], default="all",
                    help="generate the attested sharded cards (default: all)")
    ap.add_argument("--limit", type=int, default=None,
                    help="only the top-N frequency-ranked cards (partial / smoke run)")
    ap.add_argument("--index", dest="index", action="store_true", default=True,
                    help="generate the autocomplete index (default: on)")
    ap.add_argument("--no-index", dest="index", action="store_false",
                    help="skip the autocomplete index")
    ap.add_argument("--full-tarball", type=Path, default=None,
                    help="also emit the full 222k card set as a .tar.gz release asset")
    ap.add_argument("--force", action="store_true",
                    help="re-emit card files that already exist")
    args = ap.parse_args()

    if not args.db.exists():
        sys.exit(f"error: DB not found at {args.db} (build it via scripts/build_db.py)")

    con = open_db(args.db)
    print(f"[static-cache] db={args.db}  data_version={data_version(con)}  out={args.out_dir}")

    if args.cards == "all":
        build_cards(con, args.out_dir, limit=args.limit, force=args.force)
    if args.index:
        build_index(con, args.out_dir)
    if args.full_tarball:
        build_full_tarball(con, args.full_tarball)

    con.close()
    print("[static-cache] complete.")


if __name__ == "__main__":
    main()
