#!/usr/bin/env python
"""Curated pronoun-paradigm correction (W4 follow-up, MG «do correction»).

The Gītā inflection QA (H874) found kosha's Cologne+vidyut hybrid `inflections`
layer mis-models Sanskrit pronouns (sarvanāman): 71% of the divergences were
pronoun forms left untagged or given a wrong cell. This uses the GOLD attested
pronoun analyses from the Gītā (data/gita/gita_morphology_gold.tsv, pos=pronoun)
as a curated correction:

  1. emits data/gita/pronoun_corrections.tsv (form_slp1·lemma_slp1·gcase·number·
     gender·source) — the committed, reproducible correction set;
  2. applies it to kosha.db `inflections` as source='curated-gita-pronoun' rows
     (idempotent: only inserts an analysis the paradigm doesn't already hold),
     so the engine now CONTAINS the attested pronoun cell. Non-destructive —
     nothing is overwritten; wrong Cologne rows remain (flagging those is a
     further step).

This is a build stage — wire into build_db.py (`--stage pronoun`) so a rebuild
re-applies it (else it regresses like the H345 heritage table did).

Usage: python scripts/build_pronoun_corrections.py [--db <kosha.db>]
"""
import argparse
import csv
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "sanskrit-util" / "py"))
from sanskrit_util import to_slp1  # noqa: E402

GOLD = ROOT / "data" / "gita" / "gita_morphology_gold.tsv"
OUT = ROOT / "data" / "gita" / "pronoun_corrections.tsv"
DB = ROOT / "data" / "db" / "kosha.db"
if not DB.exists():
    GH = ROOT.parent if (ROOT.parent / "SanskritGrammar").exists() else ROOT.parent.parent
    DB = GH / "kosha" / "data" / "db" / "kosha.db"

CASE = {"nom": "nom", "acc": "acc", "ins": "instr", "dat": "dat", "abl": "abl",
        "gen": "gen", "loc": "loc", "voc": "voc"}
SOURCE = "curated-gita-pronoun"


def corrections():
    seen, out = set(), []
    for r in csv.DictReader(open(GOLD, encoding="utf-8"), delimiter="\t"):
        if r["pos"] != "pronoun" or not r["case"]:
            continue
        form = to_slp1(r["form"].replace("-", "").strip("'’"))
        lemma = to_slp1(r["lemma"].replace("-", "").replace("√", ""))
        gc = CASE.get(r["case"], r["case"])
        key = (form, lemma, gc, r["number"], r["gender"])
        if form and lemma and key not in seen:
            seen.add(key)
            out.append((form, lemma, gc, r["number"], r["gender"]))
    return out


def write_tsv():
    corr = corrections()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["form_slp1", "lemma_slp1", "gcase", "number", "gender", "source"])
        for c in corr:
            w.writerow(list(c) + [SOURCE])
    print(f"wrote {OUT} — {len(corr)} curated pronoun analyses")
    return corr


def apply_pronoun_corrections(con):
    """build_db.py `--stage pronoun`: emit the committed correction TSV and insert
    the curated pronoun analyses into `inflections` (source-tagged, idempotent).
    Non-destructive; only inserts an analysis the paradigm doesn't already hold."""
    corr = write_tsv()
    c = con.cursor()
    c.execute("DELETE FROM inflections WHERE source=?", (SOURCE,))
    added = 0
    for form, lemma, gc, num, gen in corr:
        if c.execute(
            "SELECT 1 FROM inflections WHERE form_slp1=? AND lemma_slp1=? AND "
            "gcase=? AND number=? AND gender=? LIMIT 1", (form, lemma, gc, num, gen)).fetchone():
            continue
        # OR IGNORE: the unique index is (form,lemma,model,gcase,number) — gender
        # excluded — so a form with two attested genders keeps the first; the other
        # still gains case+number agreement (not full DIVERGE).
        added += c.execute(
            "INSERT OR IGNORE INTO inflections (form_slp1, lemma_slp1, model, gender, "
            "gcase, number, source, disputed) VALUES (?,?,?,?,?,?,?,0)",
            (form, lemma, "pronoun", gen, gc, num, SOURCE)).rowcount
    con.commit()
    total = c.execute("SELECT COUNT(*) FROM inflections WHERE source=?", (SOURCE,)).fetchone()[0]
    print(f"[pronoun] {len(corr)} curated analyses; {added} new rows inserted "
          f"({len(corr) - added} already present); {total} total curated-pronoun rows")
    return added, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--no-apply", action="store_true", help="emit the TSV only")
    args = ap.parse_args()
    if args.no_apply:
        write_tsv(); return
    con = sqlite3.connect(args.db)
    apply_pronoun_corrections(con)
    con.close()


if __name__ == "__main__":
    main()
