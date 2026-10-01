"""P4 Wave E1 verb follow-on tests — the H855 Cologne-root -> vidyut
aupadeśika-dhātu crosswalk (scripts/build_dhatu_crosswalk.py) and its use in
scripts/compare_vidyut_verbs.py.

Two layers:
  * the committed `data/e1/dhatu_crosswalk.json` is validated unconditionally
    (structure, licensed-seed rate, the A03 bare-seeded resolution invariants,
    known mappings) — no DB, no vidyut-data;
  * the vidyut-derivation checks (that the crosswalk's aupadeśika actually fixes
    the bare-root mapping gap, and that `no-dhatu` entries abstain) are skipped
    when vidyut isn't importable.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

CROSSWALK = ROOT / "data" / "e1" / "dhatu_crosswalk.json"
_VIA = {"3sg", "direct", "bare", "unresolved",
        "cells", "cells-xgana", "no-dhatu"}  # cells* = A03 stage-2
_NULL_SEED_VIA = {"unresolved", "no-dhatu"}
MODEL_GANA = {"v_1": 1, "v_4": 4, "v_6": 6, "v_10": 10}

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
        # null seed <=> vidyut abstains (unresolved / no-dhatu)
        if e["via"] in _NULL_SEED_VIA:
            assert e["aupadeshika"] is None, f"{key} abstains but carries a seed"
        else:
            assert e["aupadeshika"], f"resolved {key} has no aupadeśika"


def test_resolution_rate_is_high(cw):
    total = cw["cologne_root_models"]
    resolved = cw["resolved"]
    assert total == len(cw["crosswalk"])
    # 'resolved' = carries a licensed aupadeśika seed. H855 hit 92.7 % by
    # counting unverifiable bare-root seeds; A03 re-decided those on Cologne
    # form evidence, and the honestly-unlicensable residue (Cologne causative
    # models of roots absent from vidyut's gaṇa-1/4/6/10 dhātupāṭha) is now
    # `no-dhatu` instead of a bare seed. Floor guards against silent regression.
    assert resolved / total >= 0.80, f"licensed-seed rate regressed: {resolved}/{total}"
    # the recomputed pct matches the stored one
    assert abs(cw["resolved_pct"] - 100 * resolved / total) < 0.05


def test_via_counts_sum_to_total(cw):
    vc = cw["via_counts"]
    assert sum(vc.values()) == cw["cologne_root_models"]
    unresolved = vc.get("unresolved", 0) + vc.get("no-dhatu", 0)
    assert unresolved == cw["cologne_root_models"] - cw["resolved"]


def test_stage2_resolution_block_consistent(cw):
    s2 = cw["bare_seeded_resolution"]
    vc = cw["via_counts"]
    outcomes = sum(v for k, v in s2.items() if k != "targets")
    assert outcomes == s2["targets"] == 262  # H3166's 212 bare + 57 unresolved − 7 identity-3sg
    assert vc["cells"] == s2["cells"]
    assert vc["cells-xgana"] == s2["cells_xgana"]
    assert vc["no-dhatu"] == s2["no_dhatu"]
    # the bare-seeded artifact population H3166 measured (212) is resolved
    assert vc["direct"] < 20, "bare-root seeds crept back past verified-direct"


def test_bare_seeded_artifact_is_resolved(cw):
    """The A03 invariant: an entry whose seed is the bare Cologne root must be
    either an identity upadeśa (3sg/bare/cells — a real dhātupāṭha entry whose
    citation form happens to be the bare string) or a verified `direct` keep
    carrying its Cologne form-evidence count. Never an unverified bare seed."""
    n_direct = 0
    for key, e in cw["crosswalk"].items():
        root = key.split("|", 1)[1]
        if e.get("aupadeshika") != root:
            continue
        if e["via"] == "direct":
            n_direct += 1
            assert e.get("evidence", 0) >= 1, f"unverified bare seed kept: {key}"
        else:
            assert e["via"] in ("3sg", "bare", "cells", "cells-xgana"), \
                f"bare seed via {e['via']}: {key}"
    assert 0 < n_direct < 20


def test_cells_entries_carry_code_and_xgana_gana(cw):
    for key, e in cw["crosswalk"].items():
        if e["via"] in ("cells", "cells-xgana"):
            assert e.get("code"), f"{key} licensed pick without dhātupāṭha code"
            assert e.get("prev_via") in ("direct", "unresolved")
        if e["via"] == "cells-xgana":
            model = key.split("|", 1)[0]
            assert e["gana"] in (1, 4, 6, 10), f"{key} bad gaṇa override"
            assert e["gana"] != MODEL_GANA[model], \
                f"{key} marked xgana but gaṇa equals the model's"


def test_known_mapping_as_div_to_asu(cw):
    """The report's worked example: bare `as` in div (v_4) mis-mapped to `Ayati`;
    the crosswalk pins it to the aupadeśika `asu~` (dhātupāṭha 04.0106)."""
    e = cw["crosswalk"].get("v_4|as")
    assert e is not None, "v_4|as missing from crosswalk"
    assert e["aupadeshika"] == "asu~"
    assert e["code"] == "04.0106"
    assert e["via"] == "3sg"


def test_known_a03_resolutions(cw):
    """The H3166 poster children, resolved: `yat`'s passive malformed as `yyate`
    off the bare seed; the licensed bhvādi `yatI~\\` (01.0030) now seeds it (its
    ātmanepada `yatate` is the Cologne middle form). `kṣam` carries BOTH Cologne
    models licensed: v_1 -> `kṣamati` (01.0510), v_4 -> `kṣamyati` (04.0103)."""
    e = cw["crosswalk"].get("v_1|yat")
    assert e and e["aupadeshika"] == "yatI~\\" and e["code"] == "01.0030"
    assert e["via"] == "cells" and e["prev_via"] == "direct"
    e = cw["crosswalk"].get("v_1|kzam")
    assert e and e["aupadeshika"] == "kzamU~\\z" and e["code"] == "01.0510"
    e = cw["crosswalk"].get("v_4|kzam")
    assert e and e["aupadeshika"] == "kzamU~" and e["via"] == "3sg"
    # no-dhatu: a Cologne causative model vidyut's gaṇa-1/4/6/10 dhātupāṭha
    # cannot license — recorded honestly, never a bare-root guess
    e = cw["crosswalk"].get("v_10|Cal")
    assert e and e["aupadeshika"] is None and e["via"] == "no-dhatu"
    assert e["prev_via"] == "direct"


def test_load_crosswalk_and_upadesha_fallback():
    """The comparison's helpers: load only resolved entries; unknown roots fall
    back to their bare root (the pre-H855 behaviour)."""
    from compare_vidyut_verbs import load_crosswalk, upadesha
    cross = load_crosswalk(CROSSWALK)
    assert cross.get("v_4|as") == "asu~"
    # unresolved / unknown keys -> bare-root fallback
    assert upadesha(cross, "nonexistent_root", "v_1") == "nonexistent_root"
    assert upadesha({}, "BU", "v_1") == "BU"


def test_load_crosswalk_full_partitions(cw):
    """A03: the full loader partitions the crosswalk into licensed seeds, gaṇa
    overrides and abstaining keys with no overlap."""
    from compare_vidyut_verbs import load_crosswalk_full
    au, gana, noseed = load_crosswalk_full(CROSSWALK)
    assert not (set(au) & noseed), "a key cannot both seed and abstain"
    assert set(gana) <= set(au), "gaṇa override without a seed"
    assert all(g in (1, 4, 6, 10) for g in gana.values())
    raw = cw["crosswalk"]
    assert noseed == {k for k, e in raw.items() if e["aupadeshika"] is None}
    assert au == {k: e["aupadeshika"] for k, e in raw.items() if e["aupadeshika"]}
    assert gana == {k: e["gana"] for k, e in raw.items() if e.get("gana") is not None}


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


@pytest.mark.skipif(not _HAVE_VIDYUT, reason="vidyut not installed")
def test_a03_seed_fixes_the_poster_child_passive():
    """H3166's named artifact: bare `yat`+Karmaṇi -> `yyate` against Cologne's
    `yatyate`; the A03 seed `yatI~\\` derives `yatyate` — a strict AGREE cell."""
    from vidyut.prakriya import (Vyakarana, Dhatu, Gana, Lakara, Prayoga,
                                 Purusha, Vacana, DhatuPada, Pada)
    from compare_vidyut_verbs import vidyut_verb_cell
    v = Vyakarana()
    d_bare = Dhatu.mula("yat", Gana.Bhvadi)
    d_fixed = Dhatu.mula("yatI~\\", Gana.Bhvadi)
    kw = dict(voice="passive", tense="pre", person="3", number="sg")
    assert vidyut_verb_cell(v, d_bare, **kw) == {"yyate"}
    assert vidyut_verb_cell(v, d_fixed, **kw) == {"yatyate"}


@pytest.mark.skipif(not _HAVE_VIDYUT, reason="vidyut not installed")
def test_abstaining_seed_yields_empty_cell():
    """A03 abstain semantics: a None dhatu (no-dhatu / unresolved entry) produces
    an empty vidyut cell set — the comparison scores COLOGNE_ONLY, never a
    bare-root pseudo-derivation."""
    from compare_vidyut_verbs import vidyut_verb_cell
    from vidyut.prakriya import Vyakarana
    v = Vyakarana()
    assert vidyut_verb_cell(v, None, voice="active", tense="pre",
                            person="3", number="sg") == set()
