"""W-RU-a inline Sa->Ru gloss-layer tests (H1278).

Locks the acceptance bar from docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md § W-RU-a:
the joiner attaches a Russian gloss triple (surface/lemma/root) to reading-pack tokens
from the SanskritRussian **public site-tier** subset, additively (the English gloss is
never touched), with honest coverage.

What is pinned:
  * gloss() returns the 4-key contract; a garbage form resolves to layer_hit "none";
  * the avagraha/apostrophe join-strip works on both sides ('gam == gam);
  * inline_token_ru is ADDITIVE (leaves `gloss`), attaches `gloss_ru` iff a layer hit,
    and is idempotent (a re-run is byte-stable);
  * real-glossary anchors: a known verb/noun hit (Cyrillic), a proper name misses;
  * a 50-token fixture drawn from the committed nala-1 pack clears the coverage bar
    (>=45/50 carry a lemma-layer RU gloss -- the 97.5% measured coverage, locked);
  * the committed artifacts (ru_gloss_layer.tsv, RU_GLOSS_COVERAGE.md) exist and are
    well-formed, and every emitted layer_hit is from the valid vocabulary.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_ru_gloss_layer as rg  # noqa: E402

TSV = ROOT / "data" / "ru_gloss" / "ru_gloss_layer.tsv"
COVERAGE = ROOT / "reading" / "RU_GLOSS_COVERAGE.md"
NALA1 = ROOT / "reading" / "data" / "nala-1.json"
VALID_HITS = {"surface", "lemma", "root", "surface+lemma", "surface+root", "lemma+root",
              "surface+lemma+root", "none"}
CYRILLIC = set("абвгдежзийклмнопрстуфхцчшщъыьэюяё")

# SanskritRussian public layers are needed; skip cleanly if the sibling repo is absent.
pytestmark = pytest.mark.skipif(
    not rg.SURFACE_TSV.exists(), reason="SanskritRussian public glossary not present")


@pytest.fixture(scope="module")
def glosser():
    return rg.RuGlosser()


def _is_cyrillic(s):
    return bool(s) and any(c in CYRILLIC for c in s.lower())


def test_gloss_contract_and_garbage(glosser):
    out = glosser.gloss("gacchati", "gam", "gam")
    assert set(out) == {"surface_ru", "lemma_ru", "root_ru", "layer_hit"}
    miss = glosser.gloss("zzqxwvpqx", "zzqxwvpqx", "zzqxwvpqx")
    assert miss["layer_hit"] == "none"
    assert miss["lemma_ru"] is None and miss["surface_ru"] is None


def test_avagraha_strip_both_sides(glosser):
    # A leading avagraha/apostrophe must not change the surface join (README discipline).
    with_av = glosser.gloss("'gacchati", "gam", "gam")["surface_ru"]
    without = glosser.gloss("gacchati", "gam", "gam")["surface_ru"]
    assert with_av == without


def test_layer_hit_matches_values(glosser):
    out = glosser.gloss("uvāca", "vac", "vac")
    hits = [n for n in ("surface", "lemma", "root")
            if out[{"surface": "surface_ru", "lemma": "lemma_ru", "root": "root_ru"}[n]]]
    assert out["layer_hit"] == ("+".join(hits) if hits else "none")


def test_real_anchors(glosser):
    # A common verb resolves and its gloss is Russian (Cyrillic).
    vac = glosser.gloss("uvāca", "vac", "vac")
    assert vac["lemma_ru"] and _is_cyrillic(vac["lemma_ru"])
    assert vac["layer_hit"] != "none"
    # A proper name (Naiṣadha = "of Niṣadha/Nala") is in the uncovered long tail.
    naisadha = glosser.gloss("naiṣadhaḥ", "naiṣadha", "nEzaDa")
    assert naisadha["lemma_ru"] is None


def test_inline_is_additive_and_idempotent(glosser):
    tok = {"form": "uvāca", "lemma": "vac", "slp1": "vac", "gloss": "to speak; to say"}
    hit = rg.inline_token_ru(tok, glosser)
    assert hit is True
    assert tok["gloss"] == "to speak; to say"          # English layer untouched
    assert "gloss_ru" in tok and isinstance(tok["gloss_ru"], dict)
    assert _is_cyrillic(tok["gloss_ru"].get("lemma", ""))
    snapshot = json.dumps(tok, ensure_ascii=False, sort_keys=True)
    rg.inline_token_ru(tok, glosser)                    # idempotent
    assert json.dumps(tok, ensure_ascii=False, sort_keys=True) == snapshot
    # A pure miss attaches nothing and reports False.
    miss = {"form": "zzqxwv", "lemma": "zzqxwv", "slp1": "zzqxwv", "gloss": "x"}
    assert rg.inline_token_ru(miss, glosser) is False
    assert "gloss_ru" not in miss


@pytest.mark.skipif(not NALA1.exists(), reason="nala-1 pack not built")
def test_50_token_fixture_coverage(glosser):
    pack = json.loads(NALA1.read_text(encoding="utf-8"))
    toks = [t for s in pack["sentences"] for t in s["tokens"]][:50]
    assert len(toks) == 50
    hits = sum(1 for t in toks
               if glosser.gloss(t.get("form", ""), t.get("lemma"), t.get("slp1"))["lemma_ru"])
    # 97.5% measured coverage on nala-1; lock a conservative 45/50 bar.
    assert hits >= 45, "lemma-layer RU coverage regressed on the nala-1 fixture: %d/50" % hits


@pytest.mark.skipif(not TSV.exists(), reason="ru_gloss_layer.tsv not built")
def test_committed_tsv_wellformed():
    lines = TSV.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    assert header == ["pack", "sent_n", "sent_sub", "tok_idx", "form_slp1",
                      "surface_ru", "lemma_ru", "root_ru", "layer_hit"]
    assert len(lines) - 1 >= 2900
    for ln in lines[1:]:
        cols = ln.split("\t")
        assert len(cols) == 9
        assert cols[8] in VALID_HITS


def test_coverage_report_exists():
    assert COVERAGE.exists()
    txt = COVERAGE.read_text(encoding="utf-8")
    assert "public site-tier" in txt and "Top-20 uncovered lemmas" in txt


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
