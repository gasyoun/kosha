"""R3 fallback exercise — parse csl-orig text directly (RISKS.md R3, D2).

The primary entry source is the csl-sqlite releases (ARCHITECTURE.md max-reuse
rule 3). RISKS.md R3 requires the documented fallback — "parse csl-orig text
directly" when a dict is absent from csl-sqlite or a release lags a needed
correction — to be **a tested path, not a comment**. This script exercises it
once, on ap90 (the smallest dict), against a local csl-orig sibling checkout,
and proves it recovers the same entry inventory the csl-sqlite path loaded.

What it demonstrates and what it honestly does NOT:
- RECOVERS, byte-for-byte where comparable: the entry inventory — the set of
  <L> records, each record's <k1> SLP1 key, and its <pc> page/column token —
  which are the fields kosha keys, pages, and cites on.
- DOES NOT produce a body identical to the csl-sqlite `data` column: csl-orig
  `.txt` is the UPSTREAM display-markup stage (`{#slp1#}`, `¦`, bare `<ls>`),
  whereas csl-sqlite ships the DOWNSTREAM `make_xml`-converted record
  (`<H1><h><key1>…`, `<s>…</s>`, `<div n=…/>`). So a production fallback that
  needs render()-able bodies must also run the csl-orig->XML `make_xml` step;
  the raw parse below is the inventory-level fallback. This boundary is the
  real finding, stated rather than glossed.

Usage:
    python scripts/fallback_csl_orig.py --dict ap90 \
        --csl-orig ../../csl-orig/v02/ap90/ap90.txt
(defaults resolve the sibling csl-orig checkout next to the GitHub/ root.)
"""
import argparse
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
# GitHub/ root is three parents up from kosha/scripts/ when kosha sits directly
# under GitHub/; the worktree case is handled by --csl-orig override.
DEFAULT_CSL_ORIG_ROOT = ROOT.parent  # sibling repos live beside kosha/

RE_L = re.compile(r"<L>([^<]*)")
RE_PC = re.compile(r"<pc>([^<]*)")
RE_K1 = re.compile(r"<k1>([^<]*)")
RE_K2 = re.compile(r"<k2>([^\n<]*)")


def parse_csl_orig(text: str):
    """Split a csl-orig dict .txt into records at each line-initial <L>, and
    parse (L, pc, k1, k2, body) from each. Returns a list of dicts in file
    order. The record body is everything after the header token run — kept raw
    (upstream display markup)."""
    records = []
    # Records begin at a line-start <L>. Split keeping the delimiter.
    parts = re.split(r"(?m)(?=^<L>)", text)
    for part in parts:
        if not part.startswith("<L>"):
            continue
        L = RE_L.search(part)
        pc = RE_PC.search(part)
        k1 = RE_K1.search(part)
        k2 = RE_K2.search(part)
        # Body = text after the header line's last recognised head tag.
        head_end = 0
        for m in (L, pc, k1, k2):
            if m:
                head_end = max(head_end, m.end())
        body = part[head_end:]
        records.append({
            "L": L.group(1) if L else None,
            "pc": pc.group(1) if pc else None,
            "k1": k1.group(1) if k1 else None,
            "k2": k2.group(1).strip() if k2 else None,
            "body_len": len(body.strip()),
        })
    return records


def resolve_csl_orig_path(dict_code, override):
    if override:
        return Path(override)
    # try common layouts under the sibling root
    for cand in (
        DEFAULT_CSL_ORIG_ROOT / "csl-orig" / "v02" / dict_code / f"{dict_code}.txt",
        DEFAULT_CSL_ORIG_ROOT.parent / "csl-orig" / "v02" / dict_code / f"{dict_code}.txt",
    ):
        if cand.exists():
            return cand
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dict", default="ap90")
    ap.add_argument("--csl-orig", default=None,
                    help="path to the dict's csl-orig .txt (overrides auto-resolve)")
    ap.add_argument("--db", default=str(ROOT / "data" / "db" / "kosha.db"))
    args = ap.parse_args()

    src = resolve_csl_orig_path(args.dict, args.csl_orig)
    if src is None or not src.exists():
        print(f"[R3] csl-orig source for {args.dict} not found "
              f"(pass --csl-orig PATH). Looked under {DEFAULT_CSL_ORIG_ROOT}")
        sys.exit(2)
    print(f"[R3] fallback parse: {src}")
    text = src.read_text(encoding="utf-8")
    recs = parse_csl_orig(text)
    print(f"[R3] parsed {len(recs):,} csl-orig records "
          f"(fields present: L={sum(r['L'] is not None for r in recs):,} "
          f"pc={sum(r['pc'] is not None for r in recs):,} "
          f"k1={sum(r['k1'] is not None for r in recs):,})")

    # Compare against the csl-sqlite-built DB inventory for the same dict.
    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    db_rows = con.execute(
        "SELECT L, slp1_key, pc_raw FROM entries WHERE dict=?", (args.dict,)).fetchall()
    con.close()
    db = {r["L"]: (r["slp1_key"], r["pc_raw"]) for r in db_rows}
    fb = {r["L"]: (r["k1"], r["pc"]) for r in recs if r["L"] is not None}

    print(f"\n[R3] inventory comparison (csl-orig fallback vs csl-sqlite DB, {args.dict}):")
    print(f"  records: fallback={len(fb):,}  db={len(db):,}")
    common = set(fb) & set(db)
    only_fb = set(fb) - set(db)
    only_db = set(db) - set(fb)
    key_match = sum(1 for L in common if fb[L][0] == db[L][0])
    pc_match = sum(1 for L in common if (fb[L][1] or "") == (db[L][1] or ""))
    print(f"  L-numbers in both: {len(common):,}   only-in-fallback: {len(only_fb):,}   "
          f"only-in-db: {len(only_db):,}")
    print(f"  <k1> SLP1 key matches DB slp1_key: {key_match:,}/{len(common):,} "
          f"({key_match/len(common)*100:.2f}%)")
    print(f"  <pc> token matches DB pc_raw:      {pc_match:,}/{len(common):,} "
          f"({pc_match/len(common)*100:.2f}%)")

    # Show a few concrete recovered records + any key mismatches for honesty.
    print("\n  sample recovered records (fallback):")
    for r in recs[:3]:
        print(f"    L={r['L']:>6} k1={r['k1']!r} pc={r['pc']!r} body_chars={r['body_len']}")
    mism = [L for L in common if fb[L][0] != db[L][0]][:5]
    if mism:
        print("  sample <k1> mismatches (fallback vs db):")
        for L in mism:
            print(f"    L={L}: fallback={fb[L][0]!r} db={db[L][0]!r}")
    else:
        print("  no <k1> key mismatches on common L-numbers.")

    verdict = (len(common) / max(len(db), 1) >= 0.99 and key_match / max(len(common), 1) >= 0.99)
    print(f"\n[R3] VERDICT: fallback recovers the entry inventory "
          f"{'YES (>=99% L + key parity)' if verdict else 'PARTIAL — see above'}.")
    print("[R3] NOTE: bodies are the upstream display-markup stage; a render()-able "
          "fallback additionally needs the csl-orig->XML make_xml step (documented).")


if __name__ == "__main__":
    main()
