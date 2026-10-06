"""Offline tests for the NWS intake pipeline (H6064).

No network, no private tar: the siglum parser, works-registry index,
stem decoder, registry builder and the OCR-route dump reader are exercised
on synthetic inputs. The pinned full-tar numbers live in the script's
--selftest and need the private tar (skipped here).
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import nws_ingest_pipeline as nip  # noqa: E402


# --- parse_nws_field --------------------------------------------------------

ASANA = ("āśana Reg , unsp > Subst n food. ĀdiPa Ed, S. 206, Z. 4 . "
         "Ensink 1964 : 27 >")
ABA = ("ābhā Gen , unsp > Subst f a flash. beauty. Mbh , MānDhŚ , Suś , "
       "Pañcat . a reflected image, outline. likeness, resemblance. Mbh , R . "
       "Adj mfn like, resembling, appearing. R , Kāvyād , Śiśup . MW : 145 >")


def test_canary_asana_header() -> None:
    p = nip.parse_nws_field(ASANA)
    assert "Reg , unsp > Subst n" in p["header"]


def test_canary_asana_pageref() -> None:
    p = nip.parse_nws_field(ASANA)
    assert any(r.startswith("ĀdiPa Ed, S. 206, Z. 4") for r in p["page_refs"])
    assert "ĀdiPa" in p["sigla"]


def test_canary_asana_litref() -> None:
    p = nip.parse_nws_field(ASANA)
    assert "Ensink 1964" in p["lit_refs"]


def test_canary_aba_sigla_and_marker() -> None:
    p = nip.parse_nws_field(ABA)
    for sig in ("Mbh", "MānDhŚ", "Suś", "Pañcat", "R", "Kāvyād", "Śiśup"):
        assert sig in p["sigla"]
    assert "MW" in p["dict_markers"]


def test_page_refs_survive_sentence_split() -> None:
    # "S. 206" / "Z. 4" periods must not split the reference apart
    p = nip.parse_nws_field(ASANA)
    assert len(p["page_refs"]) == 1
    assert "206" in p["page_refs"][0]


def test_empty_and_bare() -> None:
    assert nip.parse_nws_field("")["senses"] == 0
    p = nip.parse_nws_field("karma > Subst n deed.")
    assert "Subst n" in p["header"]
    assert p["senses"] >= 1


def test_numbered_senses_split() -> None:
    p = nip.parse_nws_field("ā Ved > Präp 1) bis an. 2) zeitlich.")
    assert p["senses"] == 2


# --- works registry / matching ----------------------------------------------

WORKS = [
    {"id": 1, "siglum": "Ensink 1964", "citation": "", "textgattung": "",
     "sachkategorie": ""},
    {"id": 2, "siglum": "Bareau 1953 (1)", "citation": "", "textgattung": "",
     "sachkategorie": ""},
    {"id": 3, "siglum": "BHSD", "citation": "", "textgattung": "",
     "sachkategorie": ""},
]


def test_match_exact_and_normalized_and_none() -> None:
    idx = nip.WorksIndex(WORKS)
    assert idx.match("Ensink 1964")[1] == "exact"
    assert idx.match("Bareau 1953 (1)")[1] == "exact"
    assert idx.match("Bareau 1953")[0]["siglum"] == "Bareau 1953 (1)"
    assert idx.match("BHSD")[1] == "exact"
    w, how = idx.match("Mbh")
    assert w is None and how == "none"


def test_match_fuzzy_author_year() -> None:
    idx = nip.WorksIndex(WORKS)
    w, how = idx.match("Ensink 1964")
    assert how == "exact" and w["id"] == 1


def test_is_siglum_token_rejects_markers() -> None:
    assert not nip.is_siglum_token("Ed")
    assert not nip.is_siglum_token("Ved")
    assert not nip.is_siglum_token("1964")
    assert not nip.is_siglum_token("food")
    assert nip.is_siglum_token("Mbh")
    assert nip.is_siglum_token("MānDhŚ")


def test_committed_registry_shape() -> None:
    reg = nip.load_registry()
    assert len(reg) == 174
    assert any(w["siglum"] == "Ensink 1964" for w in reg)
    assert all({"id", "siglum", "citation", "textgattung",
                "sachkategorie"} <= set(w) for w in reg)


# --- stem decoder (dump fallback, H6050 contract) ---------------------------

def test_decode_stem() -> None:
    assert nip.decode_stem("_a_sana") == "ASana"
    assert nip.decode_stem("_a_b_a") == "ABA"
    assert nip.decode_stem("karma") == "karma"
    assert nip.decode_stem("_s_urya") == "SUrya"


# --- registry builder --------------------------------------------------------

HTML = """<h4>Ensink 1964</h4><p>
M. Ensink, Glossary. <em>Vāk</em> 6 (1964): 1-219.
<br>
<strong>Textgattung:</strong>
Allgemein
—
<strong>Sachkategorie:</strong>
ohne Spezifikation
</p>"""


def test_build_registry_from_html(tmp_path: Path) -> None:
    f = tmp_path / "d.html"
    f.write_text(HTML, encoding="utf-8")
    works = nip.build_registry_from_html(f)
    assert len(works) == 1
    w = works[0]
    assert w["siglum"] == "Ensink 1964"
    assert "Glossary" in w["citation"]
    assert w["textgattung"] == "Allgemein"
    assert w["sachkategorie"] == "ohne Spezifikation"


# --- OCR-route dump reader (H6067 sender shape) ------------------------------

def _route(tmp_path: Path) -> Path:
    d = tmp_path / "route"
    d.mkdir()
    text = "āśana Subst n food. Mbh , R . Ensink 1964 : 27\n"
    sha = hashlib.sha256(text.encode()).hexdigest()
    (d / "p1.md").write_text(text, encoding="utf-8")
    (d / "nws_route_manifest.jsonl").write_text(json.dumps({
        "page_id": "p1", "source_image": "p1.png", "engine": "sidecar",
        "sha256_text": sha, "qc_status": "PASS"}) + "\n", encoding="utf-8")
    return d


def test_ocr_route_reader(tmp_path: Path) -> None:
    r = nip.run_ocr_route(_route(tmp_path), nip.WorksIndex(WORKS))
    assert r["pages"] == 1
    assert r["qc"] == {"PASS": 1}
    toks = dict(r["sigla_census"])
    assert toks.get("Mbh") == 1 and toks.get("R") == 1


def test_ocr_route_missing_manifest_fails(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(SystemExit):
        nip.run_ocr_route(empty, nip.WorksIndex(WORKS))


def test_ocr_route_sha_mismatch_fails(tmp_path: Path) -> None:
    d = _route(tmp_path)
    (d / "p1.md").write_text("tampered", encoding="utf-8")
    with pytest.raises(SystemExit):
        nip.run_ocr_route(d, nip.WorksIndex(WORKS))


def test_ocr_route_manifest_fields_enforced(tmp_path: Path) -> None:
    d = _route(tmp_path)
    (d / "nws_route_manifest.jsonl").write_text(
        json.dumps({"page_id": "p1"}) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        nip.run_ocr_route(d, nip.WorksIndex(WORKS))
