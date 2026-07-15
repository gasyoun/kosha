#!/usr/bin/env python
"""Morphology drills — Wave 1 W1a (H946).

The paradigm engine (app/paradigm.py, P4 K2b) already generates full case x
number / voice x tense x person x number tables. This build turns them into
graded, frequency-filtered, answer-keyed drills: the novel move (stage 2) is
drilling ONLY forms the corpus actually attests, in attested-frequency order
(field SS3.2 RQ1: "stop drilling forms that never appear").

Attestation join. kosha's own DB carries no per-form corpus-attestation
signal, so this script aggregates VisualDCS's dcs_full.sqlite `token` table
ONCE into an in-memory (lemma_slp1, form_slp1) -> {count, locus, tags-seen}
map, then joins every paradigm cell against it:
  * nominal cells match on (lemma, form, case, gender, number) — DCS
    feat_case/feat_gender/feat_number map directly onto Cologne's gcase/
    gender/number vocabulary (see CASE_MAP/GENDER_MAP/NUMBER_MAP).
  * verb cells match on (lemma, form, person, number, tense-bucket) — DCS's
    feat_tense x feat_mood pair collapses onto kosha's single `tense` column
    (pre/ipf/ipv/opt) via TENSE_MAP; DCS's feat_voice marks ONLY passive
    (`Pass`) and leaves active/middle (parasmaipada/atmanepada) undistinguished,
    so voice is NOT part of the verb match key — an honest limitation, not a
    silent overclaim (kosha generates no aorist/perfect cells at all, so the
    org's known "DCS Tense=Past conflates aorist/perfect" caveat never bites
    here).
  * the surface form itself is the primary evidence key. DCS's unsandhied-
    reconstructed field (`m_unsandhiedreconstructed`) is preferred (clean
    citation form) but is NULL for 100% of verb tokens and ~29% of nominal
    tokens in this DCS snapshot — for those the raw in-context `form` field
    is used instead (conservative: word-boundary sandhi can only cause a
    real attested form to be missed, never a false match, since the match
    is a literal SLP1 string equality).
  * DCS aggregates by lemma TEXT, not lemma_id — a handful of homonym-shared
    lemma spellings pool their attestation (same simplification H950 already
    accepted for roots-frequency; documented, not chased further).

Default mode drops any cell whose form has no attestation (honest residue,
mirrors the H696 heritage default-off precedent); --include-generated keeps
them, flagged `attested: false`.

Scope: lemmas carrying a `core_rank` in data/frequency/lemma_frequency.tsv
(the Leonchenko core-vocabulary layer, 7,120 lemmas — same restriction W1b
already applied) that also have kosha inflection rows and a real dictionary
entry (`has_entry`). Verb paradigms are additionally scoped to lemmas whose
inflections table actually carries verb rows (a small minority, 67,140/6.9M
inflection rows org-wide).

Outputs:
  * data/morphology/morphology_curriculum.tsv   rank * lemma * model * cell *
                                                 form * corpus_count *
                                                 cumulative_pct * lesson
  * data/morphology/drills.json                 answer-keyed fill/match items
                                                 (ARCHITECTURE SS shared item schema)
  * data/morphology/morphology_drills.apkg      Anki deck (genanki)
  * reading/morphology/curriculum/index.html    graded syllabus page
  * reading/morphology/drills/index.html        self-contained MCQ quiz

Public/MIT, credit Dr. Mārcis Gasūns. Usage:
  python scripts/build_morphology_drills.py [--include-generated] [--limit-lemmas N]
"""
import argparse
import csv
import html
import json
import random
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT.parent / "sanskrit-util" / "py"))

from paradigm import build_paradigm  # noqa: E402
from sanskrit_util import to_slp1, from_slp1, slp1_to_devanagari  # noqa: E402

KOSHA_DB = ROOT / "data" / "db" / "kosha.db"
DCS_DB = ROOT.parent / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"
FREQ_TSV = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
WEIGHTS = ROOT / "data" / "morphology" / "drill_weights.json"
OUT_CURRICULUM = ROOT / "data" / "morphology" / "morphology_curriculum.tsv"
OUT_DRILLS_JSON = ROOT / "data" / "morphology" / "drills.json"
OUT_APKG = ROOT / "data" / "morphology" / "morphology_drills.apkg"
OUT_CURR_HTML = ROOT / "reading" / "morphology" / "curriculum" / "index.html"
OUT_DRILLS_HTML = ROOT / "reading" / "morphology" / "drills" / "index.html"

# DCS UD-style tags -> Cologne/kosha vocabulary (see module docstring).
CASE_MAP = {"Nom": "nom", "Acc": "acc", "Ins": "instr", "Dat": "dat",
            "Abl": "abl", "Gen": "gen", "Loc": "loc", "Voc": "voc"}
GENDER_MAP = {"Masc": "m", "Fem": "f", "Neut": "n"}
NUMBER_MAP = {"Sing": "sg", "Dual": "du", "Plur": "pl"}
# (feat_tense, feat_mood) -> kosha `tense` column. Any DCS combination not
# listed here (Fut/Cond/Sub/Jus/Prec/Pot, aorist-ish Past outside Impf) has
# no counterpart kosha cell and is simply never looked up -- not an error.
TENSE_MOOD_MAP = {
    ("Pres", "Ind"): "pre",
    ("Impf", "Ind"): "ipf",
    ("Pres", "Imp"): "ipv",
    (None, "Imp"): "ipv",
    ("Pres", "Opt"): "opt",
    (None, "Opt"): "opt",
}

CASE_LABEL = {"nom": "Nominative", "acc": "Accusative", "instr": "Instrumental",
              "dat": "Dative", "abl": "Ablative", "gen": "Genitive",
              "loc": "Locative", "voc": "Vocative"}
NUM_LABEL = {"sg": "singular", "du": "dual", "pl": "plural"}
PERS_LABEL = {"1": "1st", "2": "2nd", "3": "3rd"}
TENSE_LABEL = {"pre": "present", "ipf": "imperfect", "opt": "optative", "ipv": "imperative"}


def load_attestation(dcs_path: Path) -> dict:
    """One-pass aggregate of dcs_full.sqlite -> {(lemma_slp1, form_slp1):
    {"count": int, "locus": str, "tags": set[tuple]}}. `tags` holds every
    distinct normalized tag-tuple seen for that (lemma, form) pair -- a cell
    lookup checks its own tag-tuple against this set, not just presence."""
    con = sqlite3.connect(f"file:{dcs_path}?mode=ro", uri=True)
    att: dict = {}

    def add(lemma_slp1, form_slp1, tag, count, locus):
        if not lemma_slp1 or not form_slp1:
            return
        key = (lemma_slp1, form_slp1)
        rec = att.setdefault(key, {"count": 0, "locus": locus, "tags": set()})
        rec["count"] += count
        rec["tags"].add(tag)

    # -- nominal: prefer the unsandhied-reconstructed citation form --
    t0 = time.time()
    n = 0
    q = ("SELECT lemma, m_unsandhiedreconstructed, feat_case, feat_gender, feat_number, "
         "COUNT(*), MIN(sent_id) FROM token "
         "WHERE upos IN ('NOUN','ADJ','PRON') AND feat_case IS NOT NULL "
         "AND m_unsandhiedreconstructed IS NOT NULL "
         "GROUP BY lemma, m_unsandhiedreconstructed, feat_case, feat_gender, feat_number")
    for lemma, form, case, gender, number, cnt, locus in con.execute(q):
        c, g, num = CASE_MAP.get(case), GENDER_MAP.get(gender), NUMBER_MAP.get(number)
        if not (c and g and num):
            continue
        add(to_slp1(lemma), to_slp1(form), (c, g, num), cnt, f"dcs:{locus}")
        n += 1

    # -- nominal fallback: raw in-context form, for tokens with no unsandhied field --
    q = ("SELECT lemma, form, feat_case, feat_gender, feat_number, COUNT(*), MIN(sent_id) "
         "FROM token WHERE upos IN ('NOUN','ADJ','PRON') AND feat_case IS NOT NULL "
         "AND m_unsandhiedreconstructed IS NULL AND form IS NOT NULL "
         "GROUP BY lemma, form, feat_case, feat_gender, feat_number")
    for lemma, form, case, gender, number, cnt, locus in con.execute(q):
        c, g, num = CASE_MAP.get(case), GENDER_MAP.get(gender), NUMBER_MAP.get(number)
        if not (c and g and num):
            continue
        add(to_slp1(lemma), to_slp1(form), (c, g, num), cnt, f"dcs:{locus}")
        n += 1

    # -- verb: raw form only (unsandhied field is 100% null for VERB tokens) --
    q = ("SELECT lemma, form, feat_person, feat_number, feat_tense, feat_mood, COUNT(*), MIN(sent_id) "
         "FROM token WHERE upos='VERB' AND feat_person IS NOT NULL AND form IS NOT NULL "
         "GROUP BY lemma, form, feat_person, feat_number, feat_tense, feat_mood")
    for lemma, form, person, number, tense, mood, cnt, locus in con.execute(q):
        t = TENSE_MOOD_MAP.get((tense, mood))
        num = NUMBER_MAP.get(number)
        if not (t and num and person in ("1", "2", "3")):
            continue
        add(to_slp1(lemma), to_slp1(form), (person, num, t), cnt, f"dcs:{locus}")
        n += 1

    con.close()
    print(f"[attestation] {len(att)} (lemma,form) pairs from {n} tag-groups in {time.time() - t0:.1f}s")
    return att


def lookup(att: dict, lemma_slp1: str, form_slp1: str, tag: tuple):
    rec = att.get((lemma_slp1, form_slp1))
    if rec is None or tag not in rec["tags"]:
        return None
    return rec


def select_lemmas(con, limit: int) -> list:
    core = []
    for row in csv.DictReader(open(FREQ_TSV, encoding="utf-8"), delimiter="\t"):
        if row["core_rank"]:
            core.append((int(row["core_rank"]), row["lemma_slp1"]))
    core.sort()
    out = []
    for rank, lem in core:
        if not con.execute("SELECT 1 FROM inflections WHERE lemma_slp1=? LIMIT 1", (lem,)).fetchone():
            continue
        if not con.execute("SELECT 1 FROM entries WHERE slp1_key=? LIMIT 1", (lem,)).fetchone():
            continue
        out.append((rank, lem))
        if limit and len(out) >= limit:
            break
    return out


def collect_items(con, att, lemmas, include_generated):
    """Walk build_paradigm() output for every selected lemma; emit one
    (rank_key, item_pair) per attested cell. rank_key = (core_rank,
    -corpus_count) so items sort by lemma frequency first, then by the
    attested form's own corpus weight within that lemma."""
    dropped_unattested = 0
    kept = []
    for core_rank, lem in lemmas:
        para = build_paradigm(con, lem)
        if para is None:
            continue
        for model in para["models"]:
            if model["type"] == "nominal":
                gender = model["gender"]
                for gcase, by_num in model["cells"].items():
                    for num, forms in by_num.items():
                        if gcase == "?" or num == "?" or not forms:
                            continue
                        for form in forms:
                            tag = (gcase, gender, num)
                            rec = lookup(att, lem, form, tag)
                            if rec is None:
                                dropped_unattested += 1
                                if not include_generated:
                                    continue
                            kept.append({
                                "aspect": "morphology", "lemma": lem, "model": model["model"],
                                "gender": gender, "form": form,
                                "cell": {"case": gcase, "number": num},
                                "cell_label": f"{CASE_LABEL.get(gcase, gcase)} {NUM_LABEL.get(num, num)}",
                                "core_rank": core_rank,
                                "corpus_count": rec["count"] if rec else 0,
                                "evidence": rec["locus"] if rec else None,
                                "attested": rec is not None,
                            })
            else:  # verb
                for voice, tenses in model["vcells"].items():
                    for tense, persons in tenses.items():
                        for person, by_num in persons.items():
                            for num, forms in by_num.items():
                                if num == "?" or not forms:
                                    continue
                                for form in forms:
                                    tag = (person, num, tense)
                                    rec = lookup(att, lem, form, tag)
                                    if rec is None:
                                        dropped_unattested += 1
                                        if not include_generated:
                                            continue
                                    kept.append({
                                        "aspect": "morphology", "lemma": lem, "model": model["model"],
                                        "voice": voice, "form": form,
                                        "cell": {"person": person, "number": num, "tense": tense},
                                        "cell_label": f"{PERS_LABEL.get(person, person)} {NUM_LABEL.get(num, num)} "
                                                      f"{TENSE_LABEL.get(tense, tense)}",
                                        "core_rank": core_rank,
                                        "corpus_count": rec["count"] if rec else 0,
                                        "evidence": rec["locus"] if rec else None,
                                        "attested": rec is not None,
                                    })
    print(f"[cells] kept {len(kept)}, dropped {dropped_unattested} unattested "
          f"({'included, flagged' if include_generated else 'default off'})")
    return kept


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=KOSHA_DB)
    ap.add_argument("--dcs-db", type=Path, default=DCS_DB)
    ap.add_argument("--include-generated", action="store_true",
                     help="keep unattested cells too, flagged attested:false (default: dropped)")
    ap.add_argument("--limit-lemmas", type=int, default=0, help="cap the core-vocab lemma set (debug)")
    ap.add_argument("--max-drill-cells", type=int, default=6000,
                     help="cap the interactive deck (drills.json/.apkg/HTML) to the top-N attested "
                          "cells by (core_rank, corpus frequency); 0 = full set. "
                          "morphology_curriculum.tsv is never scoped by this flag.")
    ap.add_argument("--seed", type=int, default=20260715)
    args = ap.parse_args()

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    att = load_attestation(args.dcs_db)
    lemmas = select_lemmas(con, args.limit_lemmas)
    print(f"[lemmas] {len(lemmas)} core-vocabulary lemmas with inflections + entry")

    cells = collect_items(con, att, lemmas, args.include_generated)

    import build_morphology_curriculum as _curr  # local helper module
    _curr.write_curriculum(cells, WEIGHTS, OUT_CURRICULUM, OUT_CURR_HTML)
    items = _curr.write_drills(cells, OUT_DRILLS_JSON, args.seed, args.max_drill_cells)
    _curr.write_apkg(items, OUT_APKG)
    _curr.write_drills_html(items, OUT_DRILLS_HTML)


if __name__ == "__main__":
    main()
