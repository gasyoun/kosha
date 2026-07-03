"""kosha P3 -- evidence layer payload builder.

Reads the band/first_era/example_* columns scripts/build_evidence.py adds to
`lemmas` (see that module's docstring for the band thresholds and the
per-lemma-not-per-sense scope note) and shapes them into the API's evidence
block. EVAL_PLAN.md T-UC4 requires: band + attestation count + >=1 example
with a source label when data exists, and a fail-closed "no attestation
data" (never a fabricated 0 or invented example) when it doesn't.

Every fact in the block carries its own `source` string -- the "provenance
label on every badge" exit-check requirement -- via the `badges` list.
"""

BAND_LABELS = {
    1: "core -- memorise",
    2: "frequent -- learn early",
    3: "common -- recognise",
    4: "attested -- look up",
    5: "unattested -- dictionary-only (no DCS corpus signal)",
}

SOURCE_BAND = "kosha frequency layer, rank_all (DCS archive.sqlite M9 via VisualDCS)"
SOURCE_FREQ = "DCS archive.sqlite M9 (VisualDCS)"
SOURCE_EXAMPLE = "corpus_lexicon.jsonl (pwg_ru Phase 4, SanskritLexicography/RussianTranslation)"
SOURCE_GAP = "n/a -- gap documented, not fabricated (see app/evidence.py)"


def build_evidence(lemma_row) -> dict:
    """`lemma_row` is a sqlite3.Row (or None) from `lemmas` for one slp1 key.
    Returns the evidence block for /api/v1/lemma entries. Fail-closed: a
    lemma with no frequency signal (rank_all IS NULL) still gets band 5 and
    an honest "no attestation data" -- never a numeric 0 count, never an
    invented example (EVAL_PLAN.md rule 4)."""
    if lemma_row is None:
        # Slp1 key present on an entry but absent from the lemma spine --
        # should not happen given lemmas is the union spine entries key off
        # of, but fail closed rather than raise.
        band = 5
        count_all = rank_all = first_era = None
        example = None
    else:
        band = lemma_row["band"] if lemma_row["band"] is not None else 5
        count_all = lemma_row["count_all"]
        rank_all = lemma_row["rank_all"]
        first_era = lemma_row["first_era"]
        if lemma_row["example_sa"]:
            example = {
                "sa": lemma_row["example_sa"],
                "ru": lemma_row["example_ru"],
                "work": lemma_row["example_work"],
                "passage": lemma_row["example_passage"],
                "kind": lemma_row["example_kind"],
                "source": SOURCE_EXAMPLE,
            }
        else:
            example = None

    badges = [
        {
            "field": "band",
            "value": band,
            "label": BAND_LABELS[band],
            "source": SOURCE_BAND,
        },
        {
            "field": "count_all",
            "value": count_all,
            "label": ("no attestation data" if count_all is None
                      else f"{count_all} attestations in DCS"),
            "source": SOURCE_FREQ if count_all is not None else SOURCE_GAP,
        },
        {
            "field": "first_era",
            "value": first_era,
            "label": ("no attestation data" if first_era is None
                      else f"first attested: {first_era}"),
            "source": SOURCE_FREQ if first_era is not None else SOURCE_GAP,
        },
        {
            # Genre sketch is NOT derivable from the current DCS extraction:
            # `periods` (data/frequency/README.md) is a chronological
            # period-count vector only, with no per-genre breakdown attached.
            # Honestly reported as an absent field rather than fabricated --
            # see IMPLEMENTATION_PLAN.md P3 bullet + this session's report.
            "field": "genre",
            "value": None,
            "label": "genre sketch not derivable from current DCS extraction "
                      "(only a chronological period vector is stored, no "
                      "per-genre breakdown)",
            "source": SOURCE_GAP,
        },
    ]

    return {
        "band": band,
        "band_label": BAND_LABELS[band],
        "rank_all": rank_all,
        "count_all": count_all,
        "first_era": first_era,
        "genre": None,
        "example": example,
        "badges": badges,
    }
