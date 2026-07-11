"""kosha — kosha.db completeness audit vs the csl-orig dictionary inventory (H687).

Answers the DATA_LAYERS_CENSUS question "is the service complete vs csl-orig?":

  * per-table row counts + index inventory (read-only, PRAGMA + COUNT)
  * dictionaries loaded (entries.dict) mapped against the live csl-orig
    v02 inventory (every ``v02/<code>/<code>.txt``)
  * per loaded dict: entry count vs the source's live ``<L>`` count,
    shortfalls >1% flagged
  * lookup-path coverage: which dicts each path (entry body, senses,
    union-headword lemmas, forms, inflections) actually covers

    python scripts/audit_db_completeness.py [--csl-orig PATH] [--json]

Read-only against the DB (opened with ``mode=ro``); no schema changes.
Markdown tables print to stdout — the committed snapshot lives in
docs/KOSHA_DB_COMPLETENESS_AUDIT.md; re-run this script to refresh it.
"""
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "db" / "kosha.db"
DEFAULT_CSL_ORIG = ROOT.parent / "csl-orig" / "v02"

# v02 subdirectories that are not dictionaries.
NON_DICT_DIRS = {"etymology_stats"}

L_LINE = re.compile(rb"^<L>")


def count_source_entries(txt: Path) -> int:
    """Count ``<L>`` entry markers in a csl-orig v02 dictionary text."""
    n = 0
    with txt.open("rb") as fh:
        for line in fh:
            if L_LINE.match(line):
                n += 1
    return n


def audit(csl_orig: Path) -> dict:
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    cur = con.cursor()

    table_names = [
        n for (n,) in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    ]
    tables = {
        n: cur.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0]
        for n in table_names
    }

    indexes = [
        {"name": n, "table": t, "sql": s}
        for n, t, s in cur.execute(
            "SELECT name, tbl_name, sql FROM sqlite_master "
            "WHERE type='index' ORDER BY tbl_name, name"
        )
    ]

    sources = [
        dict(zip([c[0] for c in cur.description], row))
        for row in cur.execute(
            "SELECT dict, title, csl_orig_commit, pc_format, pc_coverage, "
            "entry_count FROM sources ORDER BY dict"
        )
    ]

    loaded = {
        d: {"entries": n, "distinct_L": dl}
        for d, n, dl in cur.execute(
            "SELECT dict, COUNT(*), COUNT(DISTINCT L) FROM entries GROUP BY dict"
        )
    }
    for d, n in cur.execute(
        "SELECT e.dict, COUNT(*) FROM senses s JOIN entries e ON e.id = s.entry_id "
        "GROUP BY e.dict"
    ):
        loaded[d]["senses"] = n

    forms_by_source = {
        (src, cat or ""): n
        for src, cat, n in cur.execute(
            "SELECT source, category, COUNT(*) FROM forms GROUP BY source, category"
        )
    }
    inflections_by_source = dict(
        cur.execute("SELECT source, COUNT(*) FROM inflections GROUP BY source")
    )

    # Union-headword layer: which dict codes appear in lemmas.dicts (space-sep).
    lemma_dicts: dict[str, int] = {}
    for codes, n in cur.execute(
        "SELECT dicts, COUNT(*) FROM lemmas WHERE dicts IS NOT NULL AND dicts != '' "
        "GROUP BY dicts"
    ):
        for code in codes.split():
            lemma_dicts[code] = lemma_dicts.get(code, 0) + n

    meta = dict(cur.execute("SELECT key, value FROM meta"))
    con.close()

    inventory = {}
    for d in sorted(p.name for p in csl_orig.iterdir() if p.is_dir()):
        if d in NON_DICT_DIRS:
            continue
        txt = csl_orig / d / f"{d}.txt"
        inventory[d] = count_source_entries(txt) if txt.exists() else None

    comparison = []
    for d, src_n in inventory.items():
        row = {"dict": d, "source_L": src_n, "loaded": d in loaded}
        if d in loaded:
            got = loaded[d]["entries"]
            row["db_entries"] = got
            row["senses"] = loaded[d].get("senses", 0)
            if src_n:
                row["delta"] = got - src_n
                row["delta_pct"] = round(100.0 * (got - src_n) / src_n, 3)
                row["shortfall_gt_1pct"] = (src_n - got) / src_n > 0.01
        comparison.append(row)

    return {
        "db": DB.as_posix(),
        "meta": meta,
        "tables": tables,
        "indexes": indexes,
        "sources": sources,
        "loaded_dicts": loaded,
        "forms_by_source": {f"{s}/{c}" if c else s: n for (s, c), n in forms_by_source.items()},
        "inflections_by_source": inflections_by_source,
        "lemma_union_dict_codes": dict(sorted(lemma_dicts.items())),
        "csl_orig_inventory_size": len(inventory),
        "comparison": comparison,
    }


def print_markdown(a: dict) -> None:
    print(f"kosha.db = {a['db']} · data_version = {a['meta'].get('data_version')}")
    print()
    print("## Tables")
    print()
    print("| table | rows |")
    print("|---|---:|")
    for t, n in a["tables"].items():
        print(f"| {t} | {n:,} |")
    print()
    print("## Loaded dicts vs live csl-orig `<L>` counts")
    print()
    print("| dict | source `<L>` | db entries | delta | delta % | senses | status |")
    print("|---|---:|---:|---:|---:|---:|---|")
    for r in a["comparison"]:
        if r["loaded"]:
            flag = "SHORTFALL >1%" if r.get("shortfall_gt_1pct") else "OK"
            print(
                f"| {r['dict']} | {r['source_L']:,} | {r['db_entries']:,} | "
                f"{r['delta']:+,} | {r['delta_pct']:+.3f}% | {r['senses']:,} | {flag} |"
            )
    not_loaded = [r["dict"] for r in a["comparison"] if not r["loaded"]]
    print()
    print(f"Not loaded ({len(not_loaded)}/{a['csl_orig_inventory_size']}): "
          + " ".join(not_loaded))
    print()
    print("## Union-headword (lemmas.dicts) codes")
    print()
    print("| code | lemmas |")
    print("|---|---:|")
    for c, n in a["lemma_union_dict_codes"].items():
        print(f"| {c} | {n:,} |")
    print()
    print("## Forms / inflections by source")
    print()
    for k, n in a["forms_by_source"].items():
        print(f"- forms {k}: {n:,}")
    for k, n in a["inflections_by_source"].items():
        print(f"- inflections {k}: {n:,}")
    print()
    print("## Indexes")
    print()
    for ix in a["indexes"]:
        print(f"- {ix['table']}.{ix['name']}: {ix['sql'] or '(implicit unique)'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csl-orig", type=Path, default=DEFAULT_CSL_ORIG,
                    help="path to csl-orig/v02 (default: sibling clone)")
    ap.add_argument("--json", action="store_true", help="emit raw JSON instead of markdown")
    args = ap.parse_args()
    if not DB.exists():
        sys.exit(f"missing DB: {DB}")
    if not args.csl_orig.is_dir():
        sys.exit(f"missing csl-orig v02 dir: {args.csl_orig}")
    a = audit(args.csl_orig)
    if args.json:
        print(json.dumps(a, ensure_ascii=False, indent=2))
    else:
        print_markdown(a)


if __name__ == "__main__":
    main()
