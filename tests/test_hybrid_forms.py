"""P4 Wave E1 hybridize tests — scripts/build_hybrid_forms.py + the provenance
it surfaces through app/paradigm.py and app/reverse_lookup.py (H185).

Locks the invariants of MG's HYBRIDIZE ruling:
  * the ṇatva bug (MWinflect#6) is auto-fixed — a `hybrid-natva-fix` form
    supersedes the buggy Cologne cell in the paradigm grid, WITHOUT the Cologne
    row being deleted (it stays resolvable in reverse lookup);
  * VIDYUT_ONLY coverage gaps (cardinals) are gap-filled;
  * pronominal / feminine-stem forks are flagged `disputed`, NOT overwritten;
  * an untouched all-Cologne stem (rāma) is byte-for-byte unchanged.

Local-only (A3): requires data/db/kosha.db built AND `--stage hybrid` (or
scripts/build_hybrid_forms.py) already run against it. Skips otherwise — the
hybrid pass is an out-of-band deploy step, exactly like build_paradigms --all.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

import sqlite3

from paradigm import build_paradigm  # noqa: E402
from reverse_lookup import analyze  # noqa: E402

DB = ROOT / "data" / "db" / "kosha.db"


def _con():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _hybrid_ran():
    if not DB.exists():
        return False
    con = _con()
    try:
        return con.execute(
            "SELECT COUNT(*) FROM inflections WHERE source='hybrid-natva-fix'"
        ).fetchone()[0] > 0
    finally:
        con.close()


pytestmark = pytest.mark.skipif(
    not _hybrid_ran(),
    reason="hybrid pass not run on kosha.db (A3; `build_db.py --stage hybrid`)")


def _cell(para, model, gcase, number):
    m = next(mm for mm in para["models"] if mm["model"] == model)
    return m["cells"].get(gcase, {}).get(number, []), m.get("cell_notes", {})


def test_natva_fix_supersedes_buggy_cologne_cell():
    """nṛpa (nfpa) m_a instr.sg: Cologne emits nfpena (ṇatva bug); the paradigm
    now shows the vidyut-corrected nfpeRa and records the supersede."""
    con = _con()
    try:
        para = build_paradigm(con, "nfpa")
    finally:
        con.close()
    forms, notes = _cell(para, "m_a", "instr", "sg")
    assert forms == ["nfpeRa"], forms
    note = notes.get("instr.sg")
    assert note and note["provenance"] == "hybrid-natva-fix"
    assert "nfpena" in note.get("superseded", [])


def test_buggy_cologne_form_still_reverse_resolves():
    """The ṇatva-buggy form is NOT deleted — a reader who types nfpena still
    resolves it (source tells them it's the Cologne base), and nfpeRa resolves
    as the hybrid fix."""
    con = _con()
    try:
        buggy = analyze(con, "nfpena")
        fixed = analyze(con, "nfpeRa")
    finally:
        con.close()
    buggy_srcs = {a["source"] for a in buggy["analyses"]}
    assert "cologne_mwinflect" in buggy_srcs
    assert any(a["lemma_slp1"] == "nfpa" for a in buggy["analyses"])
    fixed_srcs = {a["source"] for a in fixed["analyses"]}
    assert "hybrid-natva-fix" in fixed_srcs


def test_gap_fill_is_vidyut_sourced():
    """Every gap-fill row carries source='vidyut-gap-fill' and sits in a cell
    Cologne left empty (cardinal numerals dominate — model m_card)."""
    con = _con()
    try:
        rows = con.execute(
            "SELECT lemma_slp1, model FROM inflections "
            "WHERE source='vidyut-gap-fill' LIMIT 5").fetchall()
        assert rows, "expected at least one gap-fill row after the hybrid pass"
        lem, model = rows[0]["lemma_slp1"], rows[0]["model"]
        para = build_paradigm(con, lem)
    finally:
        con.close()
    m = next(mm for mm in para["models"] if mm["model"] == model)
    assert any(n.get("provenance") == "vidyut-gap-fill" for n in m["cell_notes"].values())


def test_disputed_fork_flagged_not_overwritten():
    """bhagavat (m_vat) has feminine/consonant-fork cells flagged disputed; the
    Cologne form stays the display default (not overwritten) and the flag shows
    in both the paradigm cell_notes and the reverse analyses."""
    con = _con()
    try:
        n_disp = con.execute(
            "SELECT COUNT(*) FROM inflections WHERE lemma_slp1='Bagavat' AND disputed=1"
        ).fetchone()[0]
        para = build_paradigm(con, "Bagavat")
        # pick one disputed form and confirm reverse marks it disputed
        drow = con.execute(
            "SELECT form_slp1 FROM inflections WHERE lemma_slp1='Bagavat' AND disputed=1 LIMIT 1"
        ).fetchone()
        rev = analyze(con, drow["form_slp1"]) if drow else None
    finally:
        con.close()
    assert n_disp > 0
    disputed_notes = [n for m in para["models"] if m["type"] == "nominal"
                      for n in m.get("cell_notes", {}).values() if n.get("disputed")]
    assert disputed_notes, "expected at least one disputed cell_note on bhagavat"
    assert rev is not None
    assert any(a.get("disputed") and a["lemma_slp1"] == "Bagavat" for a in rev["analyses"])


def test_untouched_stem_has_empty_cell_notes():
    """rāma is ṇ-correct in Cologne (rāmeṇa/rāmāṇām) — the hybrid pass must not
    touch it: cells verbatim, cell_notes empty."""
    con = _con()
    try:
        para = build_paradigm(con, "rAma")
    finally:
        con.close()
    m_a = next(m for m in para["models"] if m["model"] == "m_a")
    assert m_a["cells"]["instr"]["sg"] == ["rAmeRa"]
    assert m_a["cells"]["gen"]["pl"] == ["rAmARAm"]
    assert m_a["cell_notes"] == {}


def test_no_cologne_row_deleted():
    """The hybrid pass is additive on the form axis: the Cologne base row count
    is unchanged (fixes/gap-fills are NEW rows, never replacements)."""
    con = _con()
    try:
        n_cologne = con.execute(
            "SELECT COUNT(*) FROM inflections WHERE source='cologne_mwinflect'"
        ).fetchone()[0]
    finally:
        con.close()
    # the K1+K2a ingest total (6,849,382 nominal + 67,140 verb) — all Cologne.
    assert n_cologne == 6_916_522
