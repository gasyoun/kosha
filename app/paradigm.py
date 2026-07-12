"""kosha P4 Wave K2b (H183) -- forward stem->paradigm assembly.

Reads the `inflections` table (Cologne csl-inflect, engine=Cologne verbatim per
D3) and groups every parse for a lemma into paradigm grids. This is the SINGLE
source of the paradigm JSON shape: the live API endpoint
(`GET /api/v1/paradigm/{lemma}` in app/main.py) and the static-tier generator
(scripts/build_paradigms.py) both call `build_paradigm()`, so a static shard is
byte-identical to the API response for the same lemma (locked by
tests/test_paradigms.py, the K2a/P2 parity discipline).

Cells carry forms as SLP1 keys; the frontend renders them into
Devanagari/IAST/SLP1 client-side.

E1 hybridize (H185, MG ruling HYBRIDIZE): the `inflections` table now carries,
besides the Cologne base (`source='cologne_mwinflect'`), vidyut-layered rows —
`hybrid-natva-fix` (a corrected form for a ṇatva-bug cell, MWinflect#6) and
`vidyut-gap-fill` (a form for a cell Cologne left empty) — plus a `disputed`
flag on the pronominal/feminine forks. This builder resolves each cell to ONE
authoritative display form-set: where a `hybrid-natva-fix` exists it SUPERSEDES
the buggy Cologne form for display (the Cologne row is not deleted — it stays
resolvable in reverse lookup, and the superseded form is preserved in
`cell_notes` for the K2b UI). A sparse per-model `cell_notes` map records which
cells were fixed, gap-filled, or flagged `disputed`, so the UI can surface an
editorial-review affordance. Cells NOT touched by the hybrid pass stay verbatim
Cologne (the pre-E1 D3 behaviour), rAma's ṇ-correct paradigm included.
"""
import sqlite3

from transliterate import from_slp1_out

# Standard grammatical presentation order. Anything the data uses that is not
# listed here is appended after, so an unexpected label never silently vanishes.
CASE_ORDER = ["nom", "acc", "instr", "dat", "abl", "gen", "loc", "voc"]
NUMBER_ORDER = ["sg", "du", "pl"]
PERSON_ORDER = ["3", "2", "1"]  # Sanskrit prathama/madhyama/uttama order


def _resolve_nominal_cell(rows):
    """Given the (form, source, disputed) rows for one case x number cell,
    return (display_forms, note). `display_forms` is the deduped, form-sorted
    list the UI shows; a `hybrid-natva-fix` supersedes the Cologne form. `note`
    is None for an untouched Cologne cell, else a sparse dict describing the
    hybrid provenance / disputed flag (recorded per-cell in `cell_notes`)."""
    by_src = {}
    disputed = False
    for form, source, dsp in rows:
        by_src.setdefault(source or "cologne_mwinflect", set()).add(form)
        disputed = disputed or bool(dsp)
    cologne = sorted(by_src.get("cologne_mwinflect", set()))
    fixed = sorted(by_src.get("hybrid-natva-fix", set()))
    gap = sorted(by_src.get("vidyut-gap-fill", set()))
    note = None
    if fixed:
        display = fixed
        note = {"provenance": "hybrid-natva-fix"}
        if cologne:
            note["superseded"] = cologne  # the ṇatva-buggy Cologne form, kept for the UI
    elif gap and not cologne:
        display = gap
        note = {"provenance": "vidyut-gap-fill"}
    else:
        # untouched Cologne (plus any additive forms that aren't a supersede)
        display = sorted(set(cologne) | set(gap) | set(fixed))
    if disputed:
        note = dict(note or {})
        note["disputed"] = True
    return display, note


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
        "SELECT form_slp1, model, gender, gcase, number, person, tense, voice, refs, "
        "source, disputed "
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
                "_cells": {},   # nominal: case -> number -> [(form, source, disputed)]
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
            m["_cells"].setdefault(gcase, {}).setdefault(number, []).append(
                (r["form_slp1"], r["source"], r["disputed"]))

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
            cell_notes = {}  # sparse: "case.number" -> hybrid/disputed provenance
            for gcase in _ordered(m["_cells"].keys(), CASE_ORDER):
                cells[gcase] = {}
                for num in _ordered(m["_cells"][gcase].keys(), NUMBER_ORDER):
                    display, note = _resolve_nominal_cell(m["_cells"][gcase][num])
                    cells[gcase][num] = display
                    if note is not None:
                        cell_notes[f"{gcase}.{num}"] = note
            numbers = _ordered(
                {n for byc in m["_cells"].values() for n in byc.keys()}, NUMBER_ORDER)
            out_models.append({
                "model": m["model"], "type": "nominal", "gender": m["gender"],
                "refs": m["refs"], "cases": _ordered(m["_cells"].keys(), CASE_ORDER),
                "numbers": numbers, "cells": cells,
                # E1 hybridize (H185): empty {} for an all-Cologne paradigm, so
                # the field is stable but adds no noise to untouched stems.
                "cell_notes": cell_notes,
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
