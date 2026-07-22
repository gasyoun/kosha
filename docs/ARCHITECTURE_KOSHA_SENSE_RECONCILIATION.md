# ARCHITECTURE — kosha sense-reconciliation layer

_Created: 22-07-2026 · Last updated: 22-07-2026_

Index: [PLAN_KOSHA_SENSE_RECONCILIATION_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_RECONCILIATION_2026H2.md).

## The join, in one line

`(headword) → (numbered sense, per PWG microstructure) → (DCS/Samudra attestation)` — where today
only `(headword) → (attestation)` exists. The new artefact is the **middle arrow**: a sense id on
every attestation link.

## Data flow

```
PWG layer (csl-orig/v02/pwg/pwg.txt, read-only)
   │  microstructure.py  (RussianTranslation, REUSE — H1456 exports its per-sense output)
   ▼
pwg_sense_loci.tsv           one row per (headword, sense_id, gloss_de, <ls> loci[], hom)
   │                          e.g. nAgadanta | 1a | "Elephantenzahn, Elfenbein" | MED.t.203;MBH.12,3630
   │                               nAgadanta | 1b | "Pflock in der Wand …"       | H.1011;PAÑCAT.116,19;252,10
   │
   │   ┌─ dcs_cdsl_xref.tsv (csl-apidev, human-validated — consume)
   │   ├─ dcs_full.sqlite    (VisualDCS, 5.69M tokens — consume)
   │   ├─ SamudraManthanam FTS (verse-aligned corpus — query, never copy)
   │   └─ H1453 wordsem→MW-sense projection (candidate signal, when present)
   ▼
build_sense_corpus_concordance.py   (NEW — extends concordance_core.TieredMatcher)
   │   step A  resolve each <ls> locus string → citable DCS/Samudra passage  (deterministic)
   │   step B  candidate senses per attestation:
   │             (i) locus-match   attestation locus ∈ a sense's resolved <ls> set   → high conf
   │             (ii) gloss/synset-overlap  DCS WordSem gloss ∩ sense gloss tokens   → mid conf
   │   step C  residue (no/ambiguous candidate) → LLM adjudicator (batch, gloss-grounded)
   │   step D  assign best sense; confidence<τ → review queue
   ▼
data/concordance/
   ├─ sense_corpus_concordance.tsv   (headword, sense_id, lemma, locus, conf, method, rights)
   ├─ sense_corpus_coverage.tsv      per (headword,sense): #attestations, resolution status
   ├─ sense_review_queue.tsv         confidence<τ rows for the deferred human pass
   └─ SENSE_CONCORDANCE_BUILD_REPORT.md
concordance/senses/data/kwic_<a>.js  sense-sharded KWIC shards for the static viewer
```

## Component boundaries & build-vs-reuse (prior-art verdicts)

| Piece | Verdict | Source |
|---|---|---|
| headword ↔ DCS attestation link, KWIC shards, tiered matcher | **REUSE** | [`build_dict_corpus_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_dict_corpus_concordance.py), [`concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py) |
| PWG per-sense tree + per-sense `<ls>` loci parse | **REUSE** (export via H1456) | [`RussianTranslation/src/microstructure.py`](https://github.com/sanskrit-lexicon/SanskritLexicography/blob/master/RussianTranslation/src/microstructure.py) |
| `<ls>` abbrev → source resolution (98.9% of citations) | **REUSE** | [`RussianTranslation/src/pwg_sources.py`](https://github.com/sanskrit-lexicon/SanskritLexicography/blob/master/RussianTranslation/src/pwg_sources.py) + `pwgbib.txt` |
| verse-aligned corpus lookup | **REUSE (query)** | SamudraManthanam FTS ([reference_samudra_manthanam]) |
| WordSem→MW-sense projection (candidate signal) | **REUSE when built** | H1453 `data/frequency/` |
| **sense id on each attestation + hybrid aligner + sense-KWIC viewer** | **BUILD** (the only new code) | `build_sense_corpus_concordance.py` (new), `concordance/senses/index.html` (fork of `concordance/dict/`) |
| SLP1 keying | **REUSE** | length-preserving `form_key()` ([reference_iast_normalization_pitfalls]) |

## Contracts

- **`pwg_sense_loci.tsv` (H1456 output, this plan's sole external input).** Columns:
  `slp1 \t hom \t sense_id \t gloss_de \t ls_loci` (loci `;`-joined, verbatim `<ls>` strings).
  `sense_id` = the microstructure sense path, e.g. `1a`, `1b`, `3a`. One row per leaf sense.
- **Sidecar discipline.** `sense_corpus_concordance.tsv` is LEFT-JOINed onto headwords at build time;
  it never mutates MW/kosha `senses` or app_data. Same rule as `lemma_frequency.tsv`.
- **Rights column.** Every row carries `rights ∈ {public, evidence-only}`; the viewer and any public
  export filter to `public` (PWG/MW/Apte/PD-corpus). Modern-gloss-derived rows are `evidence-only`.

## Key/matching notes

- Loci match on the **resolved** citation, not the raw `<ls>` string (MBH 12,3630 and the DCS
  Mahābhārata token address must be normalised to one comparable form — reuse `pwg_sources.py` +
  `concordance_core.citable_locus`).
- Homonymy: assignment is scoped **within a homonym** (`hom`), so `nāga`-derived `nāgadanta` senses
  never collide with an unrelated homonym's attestations.
- Variant linking (`nāgadanta`↔`nāgadantaka`): recorded as a `variant_of` edge in coverage output so
  the `-ka` form's HIT 27,12 attestation can corroborate the base form's peg sense. Full lemma-variant
  graph is wave-2.

_Dr. Mārcis Gasūns_
