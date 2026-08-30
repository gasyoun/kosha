"""H3744 — cross-dictionary sense alignment (PWG · MW · Apte).

Two things are tested, and neither needs `kosha.db` (gitignored, absent in CI):

1. the alignment ALGORITHM, on synthetic senses shaped like the real ones —
   including the नागदन्त tusk↔peg case in miniature;
2. the PUBLICATION FENCE, which is the part that can go wrong quietly: the
   organ must not appear on a render that any live build path could produce.

Checks that need the committed table degrade to a skip when it is absent, so
the fixture-tier CI stays green.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from sense_align import (  # noqa: E402
    align_lemma, extract_ls, fold_witnesses, jaccard, witness_key,
)

TABLE = ROOT / "data" / "concordance" / "sense_alignment.tsv"


# ----------------------------------------------------------------- witness keys

@pytest.mark.parametrize("raw,key", [
    ("MBH. 12,3630", "mbh"),          # PWG upper-case German style
    ("MBh.", "mbh"),                  # MW
    ("PAÑCAT. 116,19", "pancat"),
    ("Pañc.", "panc"),
    ("Kathās.", "kathas"),
    ("KATHĀS. 76,24", "kathas"),
    ("SUŚR. 1,138,12", "susr"),
    ("Suśr.", "susr"),
    ("H. an. 4,111", "h.an"),
    ("123", ""),                      # a bare locus is not a witness
])
def test_witness_key_normalises_across_traditions(raw, key):
    assert witness_key(raw) == key


def test_fold_witnesses_joins_abbreviation_lengths():
    rep = fold_witnesses(["panc", "pancat", "kathas"])
    assert rep["pancat"] == "panc"     # same text, abbreviated at two lengths
    assert rep["kathas"] == "kathas"


def test_fold_refuses_short_prefixes():
    """`r` (Rāmāyaṇa) must never absorb `rv` (Ṛgveda) — PREFIX_MIN exists for this."""
    rep = fold_witnesses(["r", "rv"])
    assert rep["rv"] == "rv"


def test_sense_gloss_drops_the_apparatus():
    """A gloss is the definition; citations and quoted Sanskrit are evidence."""
    from sense_align import sense_gloss
    pwg = ('<div n="2"> a〉 <i>Elephantenzahn, Elfenbein</i> '
           '<ls>H. an. 4,111</ls>. <ls>MBH. 12,3630</ls>. </div>')
    assert sense_gloss(pwg, "pwg") == "Elephantenzahn, Elfenbein"
    mw = "<s>nAga—danta</s> <lex>m.</lex> elephant's tusk or ivory, <ls>MBh.</ls>"
    assert sense_gloss(mw, "mw") == "m. elephant's tusk or ivory"


def test_extract_ls_reads_both_citation_forms():
    body = ('<i>Pflock</i> <ls>PAÑCAT. 116,19</ls>. <ls n="PAÑCAT.">252,10</ls>.')
    assert extract_ls(body) == ["pancat", "pancat"]


def test_jaccard_ignores_stopwords():
    from sense_align import gloss_tokens
    a = gloss_tokens("a peg in the wall to hang things upon")
    b = gloss_tokens("A peg in the wall.")
    assert jaccard(a, b) >= 0.4


# --------------------------------------------------------------- the algorithm

def _nagadanta_senses():
    """The real case, trimmed to what the aligner sees."""
    return [
        {"dict": "pwg", "sense_id": "pwg:38150:3", "label": "PWG a〉",
         "gloss": "Elephantenzahn, Elfenbein",
         "ls": ["h.an", "med.t", "mbh"]},
        {"dict": "pwg", "sense_id": "pwg:38150:4", "label": "PWG b〉",
         "gloss": "Pflock in der Wand zum Anhängen von Sachen",
         "ls": ["h", "h.an", "med", "pancat"]},
        {"dict": "mw", "sense_id": "mw:104994:1", "label": "MW 1",
         "gloss": "elephant's tusk or ivory", "ls": ["mbh"]},
        {"dict": "mw", "sense_id": "mw:104995:1", "label": "MW 2",
         "gloss": "a peg in the wall to hang things upon", "ls": ["panc", "kathas"]},
    ]


def test_nagadanta_tusk_and_peg_align_and_do_not_merge():
    res = align_lemma(_nagadanta_senses(), present_dicts={"pwg", "mw"})
    aligned = [g for g in res["groups"] if g["status"] == "aligned"]
    assert len(aligned) == 2, "the tusk and the peg are two meanings, not one"

    def gloss_of(g, d):
        return " ".join(m["gloss"] for m in g["by_dict"][d])

    tusk = [g for g in aligned if "Elephantenzahn" in gloss_of(g, "pwg")]
    peg = [g for g in aligned if "Pflock" in gloss_of(g, "pwg")]
    assert tusk and peg
    assert "tusk" in gloss_of(tusk[0], "mw")
    assert "peg in the wall" in gloss_of(peg[0], "mw")
    assert tusk[0]["witnesses"] == ["mbh"]
    assert peg[0]["witnesses"] == ["panc"]   # PAÑCAT. ≡ Pañc. after folding
    assert all(g["method"] == "ls" for g in aligned), "the bridge is the citation, not the gloss"


def test_a_witness_shared_by_everything_carries_no_edge():
    """`MBh.` on every sense of a lemma discriminates nothing — 1/df sinks below τ."""
    senses = [{"dict": "pwg", "sense_id": f"pwg:1:{i}", "label": "", "gloss": f"Bedeutung {i}",
               "ls": ["mbh"]} for i in range(4)]
    senses += [{"dict": "mw", "sense_id": f"mw:1:{i}", "label": "", "gloss": f"meaning {i}",
                "ls": ["mbh"]} for i in range(4)]
    res = align_lemma(senses, present_dicts={"pwg", "mw"})
    assert all(g["status"] == "unaligned" for g in res["groups"])
    assert {g["failure_class"] for g in res["groups"]} == {"witness-too-common"}


def test_gloss_overlap_never_crosses_the_german_boundary():
    """PWG↔MW gloss overlap would measure nothing; only `ls` may cross."""
    senses = [
        {"dict": "pwg", "sense_id": "pwg:1:1", "label": "", "gloss": "Elefant Elefant", "ls": []},
        {"dict": "mw", "sense_id": "mw:1:1", "label": "", "gloss": "Elefant Elefant", "ls": []},
    ]
    res = align_lemma(senses, present_dicts={"pwg", "mw"})
    assert all(g["status"] == "unaligned" for g in res["groups"])


def test_mw_apte_align_on_gloss_alone():
    senses = [
        {"dict": "mw", "sense_id": "mw:1:1", "label": "", "gloss": "a kind of temple", "ls": []},
        {"dict": "ap90", "sense_id": "ap90:1:1", "label": "", "gloss": "A kind of temple.",
         "ls": []},
    ]
    res = align_lemma(senses, present_dicts={"mw", "ap90"})
    aligned = [g for g in res["groups"] if g["status"] == "aligned"]
    assert len(aligned) == 1 and aligned[0]["method"] == "gloss"


def test_failure_classes_are_from_the_documented_taxonomy():
    known = {"no-shared-witness", "witness-too-common", "cross-language-gap",
             "no-gloss", "absent-dictionary", "outranked"}
    senses = [
        {"dict": "pwg", "sense_id": "pwg:1:1", "label": "", "gloss": "Bedeutung ohne Belege",
         "ls": []},                                     # cross-language-gap
        {"dict": "pwg", "sense_id": "pwg:1:2", "label": "", "gloss": "m.", "ls": []},  # no-gloss
        {"dict": "mw", "sense_id": "mw:1:1", "label": "", "gloss": "an unrelated meaning",
         "ls": ["ragh"]},                               # no-shared-witness
    ]
    res = align_lemma(senses, present_dicts={"pwg", "mw"})
    seen = {g["failure_class"] for g in res["groups"] if g["failure_class"]}
    seen |= {d["failure_class"] for d in res["dropped"]}
    assert seen <= known and seen
    assert "no-gloss" in seen, "a structural chunk is dropped and counted, never aligned"


def test_absent_dictionary_only_when_there_was_nothing_to_align_against():
    senses = [{"dict": "pwg", "sense_id": "pwg:1:1", "label": "", "gloss": "Lust",
               "ls": ["av"]}]
    res = align_lemma(senses, present_dicts={"pwg"})
    assert res["groups"][0]["failure_class"] == "absent-dictionary"


# ----------------------------------------------------------- publication fence

def _card():
    p = ROOT / "docs" / "cards" / "padma.json"
    if not p.is_file():
        pytest.skip("docs/cards/ not built in this tree")
    return json.loads(p.read_text(encoding="utf-8"))


def test_public_render_carries_no_alignment_block():
    from word_page import render_word_page
    html = render_word_page(_card(), token="padma", include_doc=False)
    assert "sense-align" not in html


def test_a_live_shaped_ux_render_carries_no_alignment_block():
    """The gate is the explicit `sense_align` key, NOT `ux` truthiness: since the
    H3457 publish (26-08-2026) every live /w/ page is rendered WITH ux."""
    from word_page import render_word_page
    html = render_word_page(_card(), token="padma", include_doc=False, ux={"variant": "a"})
    assert "sense-align" not in html


def test_staging_render_carries_the_block_when_the_table_exists():
    if not TABLE.is_file():
        pytest.skip("data/concordance/sense_alignment.tsv not built in this tree")
    from word_page import render_word_page
    html = render_word_page(_card(), token="padma", include_doc=False,
                            ux={"variant": "a", "sense_align": True})
    assert "sense-align" in html
    assert "Aligned senses across dictionaries" in html


def test_block_is_empty_for_a_lemma_outside_the_table():
    from word_page_ux import sense_alignment_block
    assert sense_alignment_block("zzz-not-a-lemma") == ""


def test_committed_table_shape():
    if not TABLE.is_file():
        pytest.skip("data/concordance/sense_alignment.tsv not built in this tree")
    import csv
    with TABLE.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    assert rows, "the table is empty"
    for r in rows:
        assert r["status"] in {"aligned", "unaligned"}
        if r["status"] == "aligned":
            # an aligned row spans at least two dictionaries, by construction
            assert sum(1 for x in r["shape"].split("-") if x != "0") >= 2
            assert r["method"] and r["score"]
        else:
            assert r["failure_class"], "an unaligned row must say why"
