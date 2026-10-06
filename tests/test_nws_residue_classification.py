"""Offline tests for the NWS residue classifier (H6050).

No network, no tar, no csl-orig: the classification cascade, the
Levenshtein-1 machinery and the stem-feature histogram are exercised on
synthetic sets. The pinned full-corpus numbers live in the script's
--selftest and need the private inputs (skipped here).
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import nws_residue_classification as nrc  # noqa: E402


UNION = {"ASana", "sUrya", "vargIya", "karma", "raTya"}


def test_c1_translit_exact() -> None:
    klass, ev = nrc.classify("_a_sana", "ASana", 0, UNION)
    assert klass == "c1_translit_exact"
    assert ev == "ASana"


def test_c1_wins_even_with_content() -> None:
    # first-match cascade: a key1 union match is C1 regardless of content
    klass, _ = nrc.classify("x", "karma", 500, UNION)
    assert klass == "c1_translit_exact"


def test_c2_content_uncollected() -> None:
    klass, ev = nrc.classify("br_ahm_istha", "brAhmISTa", 120, UNION)
    assert klass == "c2_content_uncollected"
    assert ev == "brAhmISTa"


def test_c3_errata_near() -> None:
    # śūrya encoded as SUrya: one substitution away from sUrya
    klass, ev = nrc.classify("_s_urya", "SUrya", 0, UNION)
    assert klass == "c3_errata_near"
    assert "sUrya" in ev


def test_c3_requires_len4() -> None:
    # 'jau' is within distance 1 of 'karma'-shaped short keys but len<4 → C4
    klass, _ = nrc.classify("jau", "jau", 0, UNION | {"jYu"})
    assert klass == "c4_orphan_empty"


def test_c4_orphans() -> None:
    assert nrc.classify("_watch_state", "", 0, UNION)[0] == "c4_orphan_empty"
    assert nrc.classify("pravoar", "pravoar", 0, UNION)[0] == "c4_orphan_empty"


def test_near_targets_subs_del_ins() -> None:
    # substitution
    assert "sUrya" in nrc.near_targets("SUrya", UNION)
    # substitution: vargIyi ~ vargIya
    assert "vargIya" in nrc.near_targets("vargIyi", UNION)
    # deletion: 'karama' minus one 'a' → 'karma'
    assert "karma" in nrc.near_targets("karama", UNION)
    # insertion: one letter inserted into a union key is recovered by deletion
    assert "ASana" in nrc.near_targets("ASaSna", UNION)  # delete S → ASana
    # no self, no phantom
    assert nrc.near_targets("zzzzzz", UNION) == []


def test_stem_features() -> None:
    assert nrc.stem_features("_a_b_a_raka") == ["_a", "_b", "_a", "_r"]
    assert nrc.stem_features("karma") == []


def test_pinned_sums_to_residue() -> None:
    p = nrc.PINNED
    assert p["c1_translit_exact"] + p["c2_content_uncollected"] \
        + p["c3_errata_near"] + p["c4_orphan_empty"] == p["residue"]
    assert p["residue"] == 138976  # the reproduced H5932 baseline


@pytest.mark.skipif(
    not nrc.DEF_TAR.is_file() or not (nrc.DEF_CSL_ORIG / "v02").is_dir(),
    reason="private NWS tar / csl-orig checkout not present",
)
def test_selftest_on_real_inputs() -> None:
    import subprocess
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "nws_residue_classification.py"),
         "--selftest"],
        capture_output=True, text=True, timeout=600,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "SELFTEST PASS" in r.stdout
