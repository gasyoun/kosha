"""Invariants for the Hitopadeśa per-text concordance surface (H4038).

The claims the surface makes that could silently rot: that the rendered viewer
payload still equals the committed concordance.tsv (parity of input vs render),
that every row's occurrence refs stay in document order (order-invariance of
the underlying text), that the H4026 badge/caveat/legend machinery is what
renders (never a second render system), that the page is wired into the
existing Hitopadeśa reading pack, and that unlinked forms stay honestly absent.

Skips cleanly when the H4034 fold has not been built in this checkout.
"""
import csv
import importlib.util
import io
import json
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
FOLD = REPO / "data" / "concordance" / "text_hitopadesa"
READER = REPO / "reading" / "index.html"

pytestmark = pytest.mark.skipif(
    not (FOLD / "concordance.tsv").exists(),
    reason="Hitopadeśa text-concordance fold not built in this checkout",
)


def _builder():
    spec = importlib.util.spec_from_file_location(
        "build_text_concordance_hitopadesa",
        REPO / "scripts" / "build_text_concordance_hitopadesa.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def builder():
    return _builder()


@pytest.fixture(scope="module")
def payload(builder):
    return builder.payload_from_tsv(FOLD / "concordance.tsv")


@pytest.fixture(scope="module")
def page():
    return (FOLD / "index.html").read_text(encoding="utf-8")


# --- gate 1: parity of concordance input vs rendered counts -----------------

def test_check_gates_pass(builder):
    """The full gate pair (parity + order-invariance) on the committed fold."""
    info = builder.check_gates(FOLD / "concordance.tsv", FOLD / "text_hitopadesa.js",
                               FOLD / "index.html", FOLD / "MANIFEST.json")
    assert info["rows"] == 7857
    assert info["occurrences"] == 25040
    assert info["era"] == "early-medieval"


def test_payload_reconstruction_is_order_invariant(builder):
    """Re-deriving the payload from rows read in a SHUFFLED order yields the
    same byte-exact JSON — the rendered artifact depends on the declared
    deterministic row order, never on traversal order."""
    with open(FOLD / "concordance.tsv", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        fields = reader.fieldnames
        rows = list(reader)
    forward = builder.payload_from_tsv(FOLD / "concordance.tsv")
    shuffled = rows[::3] + rows[1::3] + rows[2::3]
    with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False,
                                     encoding="utf-8", newline="") as tmp:
        w = csv.DictWriter(tmp, fieldnames=fields, delimiter="\t",
                           lineterminator="\n")
        w.writeheader()
        w.writerows(shuffled)
        tmp_path = Path(tmp.name)
    try:
        reshuffled = builder.payload_from_tsv(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
    assert json.dumps(reshuffled, ensure_ascii=False) == \
        json.dumps(forward, ensure_ascii=False)


def test_refs_are_in_document_order(builder, payload):
    checked = 0
    for r in payload["rows"]:
        keys = [builder._locus_key(x) for x in r["refs"].split("; ")]
        assert all(k is not None for k in keys), r["surface"]
        assert keys == sorted(keys), "refs out of document order: %s" % r["surface"]
        assert len(keys) == r["n_occ"]
        checked += 1
    assert checked == 7857


# --- H4026 machinery on the surface (never a second render system) ----------

def test_page_badge_is_house_badge_html_output(builder, page, payload):
    import sys
    if str(REPO / "app") not in sys.path:
        sys.path.insert(0, str(REPO / "app"))
    from dating_hydrate import badge_html
    assert payload["era"] == "early-medieval"
    assert badge_html(payload["era"], payload["era_via"]) in page, \
        "page badge is not the house badge_html output"


def test_page_carries_h4026_caveat_and_legend(builder, page):
    import sys
    if str(REPO / "app") not in sys.path:
        sys.path.insert(0, str(REPO / "app"))
    from word_page import _dating_caveat_block
    assert _dating_caveat_block() in page, \
        "page caveat+legend is not the house _dating_caveat_block output"
    for era in ("vedic", "epic-sutra", "classical", "early-medieval",
                "late-medieval"):
        assert 'ls-era-demo" data-era="%s"' % era in page


# --- wiring: the pack page hooks the concordance (H1448 surface) ------------

def test_reading_pack_page_wires_concordance():
    html_text = READER.read_text(encoding="utf-8")
    assert 'id="conclink"' in html_text
    assert 'href="../data/concordance/text_hitopadesa/index.html"' in html_text
    assert 'slug.indexOf("hitopadesa") !== 0' in html_text, \
        "affordance must stay hidden for non-hitopadesa packs"
    assert (FOLD / "index.html").exists()


# --- honest absence ---------------------------------------------------------

def test_unlinked_forms_stay_present_and_absent(payload):
    """Unlinked (-ay residue) rows: no card href, no sense ids — but the
    occurrences ARE listed (the concordance never drops rows it can't join)."""
    unlinked = [r for r in payload["rows"] if not r["headword_slp1"]]
    assert unlinked, "expected an honest unlinked residue"
    for r in unlinked:
        assert r["card_href"] == "" and r["sense_ids"] == ""
        assert r["n_occ"] >= 1 and r["refs"]
    assert [r for r in unlinked if r["lemma_iast"] == "avalokay"], \
        "the evidence proof word must stay unlinked"


def test_badge_absent_when_no_bucket(builder):
    """A work without an era bucket must render no badge and no caveat —
    the H4026 refusal contract at page scale."""
    no_era = {
        "text_name": "T", "work_key": "t", "era": "", "era_date_range": "",
        "era_via": "", "era_reason": "", "license": "L",
        "stats": {"tokens": 1, "distinct_surface_lemma_pairs": 1,
                  "distinct_lemmas": 1, "sense_linked_share_pct": 0.0},
        "rows": [],
    }
    out = builder.render_page(no_era)
    body = out.split("</style>")[1]
    assert "class='ls-era'" not in out, "a badge element rendered without a bucket"
    assert "ls-era-demo" not in body and "dating-note" not in body, \
        "legend/caveat rendered without a bucket"
