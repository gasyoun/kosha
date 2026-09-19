# H4806 — Amarakosha synsets × MW/PWG sense-unit inventories

_Created: 19-09-2026 · Last updated: 19-09-2026_

Report of record for H4806 (shortlist cand.6, [CROSSWALK_CANDIDATES_SHORTLIST_14-09-2026.md](https://github.com/gasyoun/Uprava/blob/main/reports/CROSSWALK_CANDIDATES_SHORTLIST_14-09-2026.md) §6): the first thesaurus-×-dictionary structural join — Amarakośa varga/synsets against the MW and PWG sense-unit inventories. Complements the A58 semdom (SIL-domain) axis: there AK was mapped *laterally* to SIL domains; here it is mapped *forward* to the modern lexicographic sense division.

## Method (fence-compliant)

- **AK side (consumed as-is, H4746 reuse):** [`ak_lemma_cdsl_crosswalk.tsv`](https://github.com/gasyoun/SanskritLexicography/blob/master/data/ak_lemma_cdsl_crosswalk.tsv) — 14,036 (varga, eid, lemma_slp1) instances over 24 vargas / 5,590 synsets. The 477 union-miss instances (compounds/inflected/accented forms) contribute zero units — never promoted, zero false joins.
- **Dictionary side:** one Cologne `<L>` record (key1) = one sense unit. Sources read-only from csl-orig `v02/mw/mw.txt` (286,525 records / 194,083 distinct k1) and `v02/pwg/pwg.txt` (123,366 / 106,082). csl-orig is never committed.
- **Join:** exact SLP1 lemma = key1. **Language fence (sense-alignment-pilot trap):** no gloss-Jaccard, no gloss text read or emitted — the outputs carry keys + counts only. This is a coverage/split envelope, not a sense alignment (H1670 rule: no PWG-sense→synset mapping without gold + adjudication).
- A lemma belonging to several synsets contributes its units to each — by design; the measure is per-synset split, not a partition of MW/PWG.

## Headline numbers

| Measure | Value |
|---|---|
| AK synsets | 5,590 |
| Synsets with ≥1 MW sense unit | 5,512 (98.60%) |
| Synsets with ≥1 PWG sense unit | 5,253 (93.97%) |
| Synsets with ≥1 unit of either | 5,523 (98.80%) |
| Sense units attaching to AK synset members | 108,242 (MW 88,164 + PWG 20,078) |
| Share of all MW+PWG records | 26.4% (108,242 / 409,891) |
| Mean units per covered synset | 19.6 |

**Split distribution (dictionary sense units per AK synset):**

| Units | Synsets | Share |
|---|---|---|
| 0 | 67 | 1.20% |
| 1 | 57 | 1.02% |
| 2–3 | 444 | 7.94% |
| 4–10 | 1,647 | 29.46% |
| 11+ | 3,375 | 60.37% |

**Finding:** classical semantic clusters overwhelmingly fan out across the modern sense division — only 1.02% of AK synsets map to exactly one dictionary sense unit, while 60.4% spread over 11+. PWG units-per-synset run lower than MW consistently with the Kurzfassung's entry consolidation (123k records vs MW 286k). Top-split synsets are led by high-entry-mass lemmas — `Siva` (434 units), `haMsa` (423), `kfzRa` (357), `puzkara` (326), `go` (293) — where deity/proper-noun entry mass inflates the count; treat the measure as an envelope, not pure polysemy.

## Caveats

- Units-per-synset conflates genuine semantic split with member-lemma polysemy and homonymy (per-lemma Cologne entry mass).
- Exact-key only: the 67 zero-unit synsets are the tail of H4746's 449 distinct union misses; fold near-misses are counted diagnostically in H4746, never promoted here.
- This table is a **candidate-generator axis** (same status as the A58 bridge, top-1 17.5%): it ranks where a thesaurus-aligned sense grouping could organize MW/PWG sense units ([thematic-vocabulary](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) consumption), it does not adjudicate alignments.

## Artifacts & verification

- Alignment table: [`data/xwalk/ak_synset_mw_pwg_senses.tsv`](https://github.com/gasyoun/kosha/blob/main/data/xwalk/ak_synset_mw_pwg_senses.tsv) (5,590 rows, synset level) + lemma-level detail [`ak_lemma_mw_pwg_senses.tsv`](https://github.com/gasyoun/kosha/blob/main/data/xwalk/ak_lemma_mw_pwg_senses.tsv) (14,036 rows) + [`ak_synset_dict_senses_stats.json`](https://github.com/gasyoun/kosha/blob/main/data/xwalk/ak_synset_dict_senses_stats.json).
- Builder: [`scripts/ak_synset_dict_senses.py`](https://github.com/gasyoun/kosha/blob/main/scripts/ak_synset_dict_senses.py) — `--selftest` re-verifies a seed-42 sample of 30 synsets via an independent line-scan parse of both raw dictionary files (exit 1 on any drift): **PASS 30/30 + 3 canaries** (`deva` mw=23 pwg=3; `svarga` mw=6 pwg=1; `nara` mw=17 pwg=2).
- Data statement: [`docs/data-statements/amarakosa-mw-pwg-sense-crosswalk.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/amarakosa-mw-pwg-sense-crosswalk.meta.md).

_Гасунс_
