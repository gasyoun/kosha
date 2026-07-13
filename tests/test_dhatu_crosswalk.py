"""P4 Wave E1 verb follow-on tests — the H855 Cologne-root -> vidyut
aupadeśika-dhātu crosswalk (scripts/build_dhatu_crosswalk.py) and its use in
scripts/compare_vidyut_verbs.py.

Two layers:
  * the committed `data/e1/dhatu_crosswalk.json` is validated unconditionally
    (structure, resolution rate, known mappings) — no DB, no vidyut-data;
  * the vidyut-derivation checks (that the crosswalk's aupadeśika actually fixes
    the bare-root mapping gap) are skipped when vidyut isn't importable.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

CROSSWALK = ROOT / "data" / "e1" / "dhatu_crosswalk.json"
_VIA = {"3sg", "direct", "bare", "unresolved"}

try:
    import vidyut  # noqa: F401
    _HAVE_VIDYUT = True
except Exception:
    _HAVE_VIDYUT = False


@pytest.fixture(scope="module")
def cw():
    assert CROSSWALK.exists(), f"committed crosswalk missing: {CROSSWALK}"
    return json.loads(CROSSWALK.read_text(encoding="utf-8"))


def test_crosswalk_committed_and_wellformed(cw):
    assert "crosswalk" in cw and cw["crosswalk"], "empty crosswalk"
    for key, e in cw["crosswalk"].items():
        assert "|" in key, f"key not 'model|root': {key}"
        assert e["via"] in _VIA, f"bad via {e['via']} for {key}"
        # resolved <=> aupadeśika present; unresolved <=> null
        if e["via"] == "unresolved":
            assert e["aupadeshika"] is None
        else:
            assert e["aupadeshika"], f"resolved {key} has no aupadeśika"


def test_resolution_rate_is_high(cw):
    total = cw["cologne_root_models"]
    resolved = cw["resolved"]
    assert total == len(cw["crosswalk"])
    # H855 goal: >=90% of the gaṇa-1/4/6/10 Cologne root-models resolve.
    assert resolved / total >= 0.90, f"resolution regressed: {resolved}/{total}"
    # the recomputed pct matches the stored one
    assert abs(cw["resolved_pct"] - 100 * resolved / total) < 0.05


def test_via_counts_sum_to_total(cw):
    vc = cw["via_counts"]
    assert sum(vc.values()) == cw["cologne_root_models"]
    assert vc.get("unresolved", 0) == cw["cologne_root_models"] - cw["resolved"]


def test_known_mapping_as_div_to_asu(cw):
    """The report's worked example: bare `as` in div (v_4) mis-mapped to `Ayati`;
    the crosswalk pins it to the aupadeśika `asu~` (dhātupāṭha 04.0106)."""
    e = cw["crosswalk"].get("v_4|as")
    assert e is not None, "v_4|as missing from crosswalk"
    assert e["aupadeshika"] == "asu~"
    assert e["code"] == "04.0106"
    assert e["via"] == "3sg"


def test_load_crosswalk_and_upadesha_fallback():
    """The comparison's helpers: load only resolved entries; unknown roots fall
    back to their bare root (the pre-H855 behaviour)."""
    from compare_vidyut_verbs import load_crosswalk, upadesha
    cross = load_crosswalk(CROSSWALK)
    assert cross.get("v_4|as") == "asu~"
    # unresolved / unknown keys -> bare-root fallback
    assert upadesha(cross, "nonexistent_root", "v_1") == "nonexistent_root"
    assert upadesha({}, "BU", "v_1") == "BU"


@pytest.mark.skipif(not _HAVE_VIDYUT, reason="vidyut not installed")
def test_crosswalk_aupadeshika_fixes_the_mapping():
    """End-to-end: the bare root `as`+div derives the WRONG lexeme, but the
    crosswalk's `asu~`+div derives Cologne's `asyati` (present-3sg-active)."""
    from vidyut.prakriya import (Vyakarana, Dhatu, Gana, Lakara, Prayoga,
                                 Purusha, Vacana, DhatuPada, Pada)
    v = Vyakarana()

    def p3sg(upadesha):
        d = Dhatu.mula(upadesha, Gana.Divadi)
        return {f.text for f in v.derive(Pada.Tinanta(
            dhatu=d, prayoga=Prayoga.Kartari, lakara=Lakara.Lat,
            purusha=Purusha.Prathama, vacana=Vacana.Eka,
            dhatu_pada=DhatuPada.Parasmaipada))}

    assert "asyati" in p3sg("asu~"), "crosswalk aupadeśika should yield asyati"
    assert "asyati" not in p3sg("as"), "bare root should NOT yield asyati (the bug)"
