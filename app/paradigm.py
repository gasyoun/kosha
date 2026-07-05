"""kosha P4 Wave K2b (H183) -- forward stem->paradigm assembly.

Reads the `inflections` table (Cologne csl-inflect, engine=Cologne verbatim per
D3) and groups every parse for a lemma into paradigm grids. This is the SINGLE
source of the paradigm JSON shape: the live API endpoint
(`GET /api/v1/paradigm/{lemma}` in app/main.py) and the static-tier generator
(scripts/build_paradigms.py) both call `build_paradigm()`, so a static shard is
byte-identical to the API response for the same lemma (locked by
tests/test_paradigms.py, the K2a/P2 parity discipline).

Cells carry forms as SLP1 keys; the frontend renders them into
Devanagari/IAST/SLP1 client-side. Cells are surfaced VERBATIM -- the m_a ṇatva
bug inherited from Cologne (MWinflect#6, e.g. nfpena for attested nfpeRa) is NOT
silently corrected here (D3 / RISKS.md guardrail in H183 §7).
"""
import sqlite3

from transliterate import from_slp1_out

# Standard grammatical presentation order. Anything the data uses that is not
# listed here is appended after, so an unexpected label never silently vanishes.
CASE_ORDER = ["nom", "acc", "instr", "dat", "abl", "gen", "loc", "voc"]
NUMBER_ORDER = ["sg", "du", "pl"]
PERSON_ORDER = ["3", "2", "1"]  # Sanskrit prathama/madhyama/uttama order


def _has_entry(con, lemma_slp1):
    return con.execute(
        "SELECT 1 FROM entries WHERE slp1_key=? LIMIT 1", (lemma_slp1,)
    ).fetchone() is not None


def _ordered(keys, order):
    known = [k for k in order if k in keys]
    extra = sorted(k for k in keys if k not in order)
    return known + extra


def build_paradigm(con: sqlite3.Connection, lemma_slp1: str) -> dict | None:
    """Return the full paradigm block for a stem, or None if the lemma has no
    inflection rows. Groups by model; nominal models get a case x number grid,
    verb models (person/tense/voice non-null) a voice/tense/person x number
    grid."""
    rows = con.execute(
        "SELECT form_slp1, model, gender, gcase, number, person, tense, voice, refs "
        "FROM inflections WHERE lemma_slp1=? "
        "ORDER BY model, gcase, number, person, tense, voice, form_slp1",
        (lemma_slp1,),
    ).fetchall()
    if not rows:
        return None

    models: dict[str, dict] = {}
    for r in rows:
        m = models.get(r["model"])
        if m is None:
            m = models[r["model"]] = {
                "model": r["model"],
                "gender": r["gender"],
                "refs": r["refs"],
                "is_verb": r["person"] is not None,
                "_cells": {},   # nominal: case -> number -> [forms]
                "_vcells": {},  # verb: voice -> tense -> person -> number -> [forms]
            }
        if r["person"] is not None:
            voice = r["voice"] or "?"
            tense = r["tense"] or "?"
            person = r["person"]
            number = r["number"] or "?"
            (m["_vcells"].setdefault(voice, {}).setdefault(tense, {})
             .setdefault(person, {}).setdefault(number, []))
            m["_vcells"][voice][tense][person][number].append(r["form_slp1"])
        else:
            gcase = r["gcase"] or "?"
            number = r["number"] or "?"
            m["_cells"].setdefault(gcase, {}).setdefault(number, []).append(r["form_slp1"])

    out_models = []
    for model_key in sorted(models):
        m = models[model_key]
        if m["is_verb"]:
            vcells = {}
            for voice in sorted(m["_vcells"]):
                vcells[voice] = {}
                for tense in sorted(m["_vcells"][voice]):
                    vcells[voice][tense] = {}
                    persons = m["_vcells"][voice][tense]
                    for person in _ordered(persons.keys(), PERSON_ORDER):
                        vcells[voice][tense][person] = {
                            num: persons[person][num]
                            for num in _ordered(persons[person].keys(), NUMBER_ORDER)
                        }
            out_models.append({
                "model": m["model"], "type": "verb", "gender": m["gender"],
                "refs": m["refs"], "vcells": vcells,
                "numbers": _ordered({n for p in
                                     (persons for v in m["_vcells"].values()
                                      for persons in v.values())
                                     for pn in p.values() for n in pn.keys()}, NUMBER_ORDER),
            })
        else:
            cells = {}
            for gcase in _ordered(m["_cells"].keys(), CASE_ORDER):
                cells[gcase] = {
                    num: m["_cells"][gcase][num]
                    for num in _ordered(m["_cells"][gcase].keys(), NUMBER_ORDER)
                }
            numbers = _ordered(
                {n for byc in m["_cells"].values() for n in byc.keys()}, NUMBER_ORDER)
            out_models.append({
                "model": m["model"], "type": "nominal", "gender": m["gender"],
                "refs": m["refs"], "cases": _ordered(m["_cells"].keys(), CASE_ORDER),
                "numbers": numbers, "cells": cells,
            })

    # Note: no `lemma_deva` is emitted. Cells and lemma keys are SLP1; the
    # frontend renders Devanagari client-side via sanskrit-util's
    # slp1_to_devanagari (the Python iast_to_devanagari is a naive char-map that
    # does not compose vowel matras — रआमअ for rāma — so a Python-side deva
    # field would be wrong, and shipping SLP1 keeps the shard script-neutral).
    return {
        "lemma_slp1": lemma_slp1,
        "lemma_iast": from_slp1_out(lemma_slp1, "iast"),
        "has_entry": _has_entry(con, lemma_slp1),
        "models": out_models,
    }
