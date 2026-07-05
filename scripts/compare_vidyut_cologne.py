"""compare_vidyut_cologne.py — P4 Wave E1 (inflection roadmap) dual-engine diff.

Generates nominal paradigms with **vidyut-prakriya** (rule-based Paninian
derivation, local library — RISKS.md R12-clean, no live call) and diffs them
against the ingested Cologne **csl-inflect** tables (`inflections`), classifying
every case×number cell:

  AGREE         — both engines produce the same form set
  DIFF          — both non-empty but the sets differ (the interesting bucket)
  VIDYUT_ONLY   — Cologne has no form for the cell, vidyut does
  COLOGNE_ONLY  — Cologne has a form, vidyut produced nothing (stem vidyut can't decline)

DIFF cells are sub-classified; the headline one is the **ṇatva bug**
(MWinflect#6): Cologne emits e.g. `nfpena`/`nfpAnAm` where the attested /
vidyut-correct form is `nfpeRa`/`nfpARAm` — the Pāṇini 8.4.1-2 retroflexion
Cologne's m_a table never applied. This script flags every cell where the only
difference is n↔ṇ (R) so the report can quantify the bug's blast radius.

Nominals only (E1 v1). Verb conjugation (dhātu+gaṇa+lakāra mapping) is a larger
follow-on and is noted in the report, not attempted here.

Scope is a frequency-ranked sample of attested-with-entry stems (--limit) — the
goal is to CHARACTERISE divergence, not regenerate all 6.85M cells.

Usage:
    python scripts/compare_vidyut_cologne.py                 # top-2000 stems
    python scripts/compare_vidyut_cologne.py --limit 5000
    python scripts/compare_vidyut_cologne.py --out data/e1

Outputs (gitignored measurement, regenerable):
    <out>/e1_divergence.json   — full classified stats + example lists
    <out>/e1_summary.txt       — human-readable rollup
The narrative report (E1_DIVERGENCE_REPORT.md) is authored from these.
"""
import argparse
import json
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "db" / "kosha.db"
DEFAULT_OUT = ROOT / "data" / "e1"

from vidyut.prakriya import (  # noqa: E402
    Vyakarana, Pratipadika, Linga, Vibhakti, Vacana, Pada,
)

CASE_TO_VIBHAKTI = {
    "nom": Vibhakti.Prathama, "acc": Vibhakti.Dvitiya, "instr": Vibhakti.Trtiya,
    "dat": Vibhakti.Caturthi, "abl": Vibhakti.Panchami, "gen": Vibhakti.Sasthi,
    "loc": Vibhakti.Saptami, "voc": Vibhakti.Sambodhana,
}
NUMBER_TO_VACANA = {"sg": Vacana.Eka, "du": Vacana.Dvi, "pl": Vacana.Bahu}
GENDER_TO_LINGA = {"m": Linga.Pum, "n": Linga.Napumsaka, "f": Linga.Stri}


def open_db(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


_FINAL_STOP = {"t": "d", "d": "t", "k": "g", "g": "k", "p": "b", "b": "p"}


def is_natva_diff(cologne: set[str], vidyut: set[str]) -> bool:
    """True when the ONLY difference between the two form sets is n vs ṇ (R) —
    i.e. mapping every ṇ→n in the vidyut forms makes the sets equal, and they
    actually differ on at least one such character. Cologne wrong (MWinflect#6)."""
    if not cologne or not vidyut or cologne == vidyut:
        return False
    denatva = {f.replace("R", "n") for f in vidyut}
    cologne_dn = {f.replace("R", "n") for f in cologne}
    return denatva == cologne_dn and any("R" in f for f in vidyut)


def _final_swaps(f: str) -> set[str]:
    if f and f[-1] in _FINAL_STOP:
        return {f, f[:-1] + _FINAL_STOP[f[-1]]}
    return {f}


def is_final_stop_variant(cologne: set[str], vidyut: set[str]) -> bool:
    """True when the sets differ only by word-final stop voicing (t↔d, k↔g,
    p↔b) — e.g. vidyut {cAd,cAt} vs Cologne {cAt}. A representation choice
    (both are valid pre-sandhi citation forms), not an error on either side."""
    if cologne == vidyut:
        return False
    col_exp = set().union(*(_final_swaps(f) for f in cologne)) if cologne else set()
    vid_exp = set().union(*(_final_swaps(f) for f in vidyut)) if vidyut else set()
    return bool(cologne) and bool(vidyut) and col_exp == vid_exp


def is_pronominal_diff(vidyut: set[str]) -> bool:
    """Heuristic: vidyut declined the stem PRONOMINALLY (sarvasmai, sarvasmin,
    sarveṣām, tasya…) — the tell is an -sm- / -ṣām / -smin ending absent from a
    plain nominal. Marks the Cologne m_a/n_a row as a mis-modelled sarvanāma
    duplicate (vidyut correct; Cologne also carries the right m_pron row)."""
    return any(("sm" in f) or f.endswith("ezAm") or f.endswith("ezu") for f in vidyut)


def subclass_diff(cologne: set[str], vidyut: set[str]) -> str:
    if is_natva_diff(cologne, vidyut):
        return "natva"           # Cologne wrong
    if is_final_stop_variant(cologne, vidyut):
        return "final_stop"      # representation choice
    if is_pronominal_diff(vidyut) and not is_pronominal_diff(cologne):
        return "pronominal"      # Cologne mis-modelled (vidyut correct)
    if cologne < vidyut:
        return "vidyut_superset"
    if vidyut < cologne:
        return "cologne_superset"
    return "other"


def select_stems(con, limit: int):
    """Ranked (lemma, model, gender) nominal tuples that have a dict entry."""
    sql = (
        "SELECT DISTINCT i.lemma_slp1 AS lemma, i.model AS model, i.gender AS gender, "
        "       l.rank_all AS rank "
        "FROM inflections i "
        "JOIN entries e ON e.slp1_key = i.lemma_slp1 "
        "LEFT JOIN lemmas l ON l.slp1 = i.lemma_slp1 "
        "WHERE i.person IS NULL AND i.gender IN ('m','n','f') "
        "ORDER BY (l.rank_all IS NULL), l.rank_all ASC, i.lemma_slp1 ASC"
    )
    rows = con.execute(sql).fetchall()
    if limit:
        rows = rows[:limit]
    return rows


def cologne_cells(con, lemma, model):
    """{(case, number): set(forms)} from the Cologne table for one paradigm."""
    out = defaultdict(set)
    for r in con.execute(
        "SELECT form_slp1, gcase, number FROM inflections "
        "WHERE lemma_slp1=? AND model=? AND person IS NULL",
        (lemma, model),
    ):
        if r["gcase"] and r["number"]:
            out[(r["gcase"], r["number"])].add(r["form_slp1"])
    return out


def vidyut_cell(v, pratipadika, linga, gcase, number):
    vib = CASE_TO_VIBHAKTI[gcase]
    vac = NUMBER_TO_VACANA[number]
    try:
        pada = Pada.Subanta(pratipadika=pratipadika, linga=linga, vibhakti=vib, vacana=vac)
        return {pr.text for pr in v.derive(pada)}
    except Exception:
        return set()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=2000)
    ap.add_argument("--examples", type=int, default=60, help="max example cells kept per class")
    args = ap.parse_args()

    con = open_db(args.db)
    v = Vyakarana()
    stems = select_stems(con, args.limit)
    print(f"[E1] comparing {len(stems)} nominal paradigm(s) (vidyut-prakriya vs Cologne)")

    cls = Counter()
    per_model = defaultdict(Counter)
    examples = defaultdict(list)
    natva_cells = []
    stems_with_natva = set()
    t0 = time.time()

    for n, s in enumerate(stems, 1):
        lemma, model, gender = s["lemma"], s["model"], s["gender"]
        linga = GENDER_TO_LINGA[gender]
        try:
            prati = Pratipadika.basic(lemma)
        except Exception:
            per_model[model]["bad_stem"] += 1
            continue
        cells = cologne_cells(con, lemma, model)
        for gcase in CASE_TO_VIBHAKTI:
            for number in NUMBER_TO_VACANA:
                col = cells.get((gcase, number), set())
                vid = vidyut_cell(v, prati, linga, gcase, number)
                if not col and not vid:
                    continue
                if col == vid:
                    label = "AGREE"
                elif col and vid:
                    label = "DIFF"
                elif vid:
                    label = "VIDYUT_ONLY"
                else:
                    label = "COLOGNE_ONLY"
                cls[label] += 1
                per_model[model][label] += 1
                if label == "DIFF":
                    sub = subclass_diff(col, vid)
                    cls[f"DIFF_{sub}"] += 1
                    per_model[model][f"DIFF_{sub}"] += 1
                    ex = {"lemma": lemma, "model": model, "cell": f"{gcase}.{number}",
                          "cologne": sorted(col), "vidyut": sorted(vid)}
                    if sub == "natva":
                        stems_with_natva.add((lemma, model))
                        if len(natva_cells) < args.examples:
                            natva_cells.append(ex)
                    elif len(examples[f"DIFF_{sub}"]) < args.examples:
                        examples[f"DIFF_{sub}"].append(ex)
                elif label in ("VIDYUT_ONLY", "COLOGNE_ONLY") and len(examples[label]) < args.examples:
                    examples[label].append({"lemma": lemma, "model": model,
                                            "cell": f"{gcase}.{number}",
                                            "cologne": sorted(col), "vidyut": sorted(vid)})
        if n % 500 == 0:
            print(f"  {n}/{len(stems)}  ({time.time()-t0:.0f}s)")

    total_cells = sum(cls[k] for k in ("AGREE", "DIFF", "VIDYUT_ONLY", "COLOGNE_ONLY"))
    agree = cls["AGREE"]
    report = {
        "sample_stems": len(stems),
        "total_cells": total_cells,
        "classes": dict(cls),
        "agreement_pct": round(100 * agree / total_cells, 2) if total_cells else None,
        "natva_bug": {
            "cells": cls["DIFF_natva"],
            "stems_affected": len(stems_with_natva),
            "examples": natva_cells,
        },
        "diff_subclasses": {k[5:]: cls[k] for k in sorted(cls) if k.startswith("DIFF_")},
        "per_model": {m: dict(c) for m, c in sorted(per_model.items())},
        "examples": {k: examples[k] for k in examples},
        "elapsed_s": round(time.time() - t0, 1),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "e1_divergence.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "P4 Wave E1 — vidyut-prakriya vs Cologne csl-inflect (nominals)",
        f"sample stems      : {len(stems)}",
        f"total cells       : {total_cells}",
        f"AGREE             : {agree} ({report['agreement_pct']}%)",
        f"DIFF              : {cls['DIFF']}",
        f"  ṇatva (COL wrong)   : {cls['DIFF_natva']}  (stems: {len(stems_with_natva)})",
        f"  pronominal (COL wrong): {cls['DIFF_pronominal']}",
        f"  final-stop variant  : {cls['DIFF_final_stop']}",
        f"  vidyut superset     : {cls['DIFF_vidyut_superset']}",
        f"  cologne superset    : {cls['DIFF_cologne_superset']}",
        f"  other               : {cls['DIFF_other']}",
        f"VIDYUT_ONLY       : {cls['VIDYUT_ONLY']}",
        f"COLOGNE_ONLY      : {cls['COLOGNE_ONLY']}",
        f"elapsed           : {report['elapsed_s']}s",
    ]
    (args.out / "e1_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"[E1] wrote {args.out/'e1_divergence.json'}")


if __name__ == "__main__":
    main()
