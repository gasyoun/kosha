"""W3a metre-layer annotator tests (H951).

Locks the acceptance from docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md W3a:
the reading packs carry a per-verse metre annotation, no fabrication, no UI. These
are pure output-file checks plus a few pure-function checks; the function checks need
`vidyut` and skip cleanly without it.
"""
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

METRE_TSV = ROOT / "data" / "metre" / "reading_pack_metre.tsv"
COVERAGE_TSV = ROOT / "data" / "metre" / "metre_coverage.tsv"
METERS_TSV = ROOT / "data" / "vidyut" / "chandas" / "meters.tsv"

pytestmark = pytest.mark.skipif(
    not METRE_TSV.exists(), reason="reading_pack_metre.tsv not built")

VALID_CONF = {"high", "medium", ""}
VALID_METHOD = {"vidyut-chandas", "syllable-heuristic", "unresolved"}


def _rows():
    with open(METRE_TSV, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def test_assets_present():
    for p in (METRE_TSV, COVERAGE_TSV, METERS_TSV):
        assert p.exists(), f"missing asset {p.name}"


def test_schema_and_enums():
    rows = _rows()
    assert rows, "no rows"
    for r in rows:
        assert r["confidence"] in VALID_CONF, r
        assert r["method"] in VALID_METHOD, r


def test_no_fabricated_metre():
    """Every metre-bearing row names its method + confidence; every unresolved row
    has an empty metre. No metre is ever asserted without a stated basis."""
    for r in _rows():
        if r["metre"]:
            assert r["method"] in ("vidyut-chandas", "syllable-heuristic")
            assert r["confidence"] in ("high", "medium")
        else:
            assert r["method"] == "unresolved" and r["confidence"] == ""


def test_vrtta_matches_are_never_too_short():
    """Guard: a high-confidence strict-vṛtta ID requires >=8 syllables — a shorter
    'match' is a spurious partial hit on a prose heading (the 'atha kathāmukham'
    → drutavilambitā case) and must not survive as high confidence."""
    for r in _rows():
        if r["confidence"] == "high":
            assert int(r["syllables"]) >= 8, r


def test_anustubh_heuristic_is_pada_aligned():
    """Every syllable-heuristic anuṣṭubh tag is a multiple of 8 syllables (whole
    pādas) in [8,32] — never an arbitrary fragment guessed as śloka."""
    for r in _rows():
        if r["method"] == "syllable-heuristic":
            n = int(r["syllables"])
            assert r["metre"] == "anuṣṭubh" and 8 <= n <= 32 and n % 8 == 0, r


def test_kiratarjuniya_is_all_vrtta():
    """Validation anchor: Bhāravi's Kirātārjunīya canto 1 is composed in strict
    vṛtta (predominantly vaṃśastha), so every one of its verses must carry a
    high-confidence vṛtta ID — none fall through to the anuṣṭubh heuristic."""
    kir = [r for r in _rows() if r["pack"] == "kiratarjuniya-1"]
    assert kir, "kiratarjuniya-1 not annotated"
    assert all(r["confidence"] == "high" for r in kir), "some Kirāt verses not vṛtta"
    vamsastha = sum(1 for r in kir if r["metre"] == "vaMSasTa")
    assert vamsastha >= 0.8 * len(kir), f"expected mostly vaṃśastha, got {vamsastha}/{len(kir)}"


def test_coverage_sums_match_detail():
    """The per-pack coverage summary agrees with the detail rows (no drift)."""
    detail = {}
    for r in _rows():
        detail.setdefault(r["pack"], []).append(r)
    with open(COVERAGE_TSV, encoding="utf-8") as f:
        for c in csv.DictReader(f, delimiter="\t"):
            rows = detail[c["pack"]]
            assert int(c["sentences"]) == len(rows), c["pack"]
            assert int(c["vrtta_high"]) == sum(1 for r in rows if r["confidence"] == "high")
            assert int(c["anustubh_medium"]) == sum(1 for r in rows if r["confidence"] == "medium")


# --- pure-function checks (need vidyut) ---------------------------------------

vidyut = pytest.importorskip("vidyut", reason="vidyut not installed")


def _classifier():
    import build_reading_pack_metre as m
    from vidyut.chandas import Chandas
    from vidyut.lipi import Scheme, transliterate
    return m, Chandas(str(METERS_TSV)), transliterate, Scheme


def test_classify_deterministic_and_guarded():
    m, ch, tr, Scheme = _classifier()
    # a clean vasantatilakā pāda (the vidyut doc example) -> high vṛtta
    a = m.classify_sentence(ch, tr, Scheme, "mAtaH samastajagatAM maDukEwaBAreH")
    b = m.classify_sentence(ch, tr, Scheme, "mAtaH samastajagatAM maDukEwaBAreH")
    assert a == b
    assert a[0] == "vasantatilakA" and a[3] == "high"
    # a short prose heading -> unresolved, NOT a spurious vṛtta
    metre, _t, method, conf, _n = m.classify_sentence(ch, tr, Scheme, "atha kathAmuKam")
    assert conf != "high", (metre, method, conf)


def test_non_slp1_input_does_not_crash():
    """vidyut-chandas panics on non-SLP1 bytes; the sanitiser must prevent that."""
    m, ch, tr, Scheme = _classifier()
    # punctuation, digits, an avagraha — all stripped before classify
    out = m.classify_sentence(ch, tr, Scheme, "rājā 1234 nalo 'bravīt.")
    assert out[2] in ("vidyut-chandas", "syllable-heuristic", "unresolved")
