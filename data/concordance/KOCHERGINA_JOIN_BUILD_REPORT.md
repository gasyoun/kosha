# Kochergina 1987 read-only join — build report

_Created: 15-09-2026 · Last updated: 15-09-2026_

Built by [scripts/build_kochergina_concordance.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_kochergina_concordance.py) (H4748, OxAlpha `z-ai/glm-5.3-flash`), reusing the shared [concordance_core.py](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py) TieredMatcher + the verbatim B1 lemma_stats aggregation.

Source: `SamudraManthanam/web/corpus_builder/jsonl/kochergina.jsonl` (SLP1-keyed headwords, consumed READ-ONLY — 29180 head records; 3 without an slp1 key, skipped; 29177 keyed records → 28371 raw keys (806 homograph records folded); 271 dashed compound-member records; stripped citation forms add 213 keys → 28584 unique comparison keys).

## Per-tier link counts (exit-check: no silent fuzzy blur)

| tier | confidence | links | status |
|---|---|---|---|
| exact | 0.95 | 19560 | asserted |
| floor | 0.85 | 1091 | asserted |
| xref | — | n/a | third-party dict: dcs-cdsl-xref validates CDSL unions only |
| relaxed | 0.60 | 3256 | **quarantined** — review candidates only |
| fuzzy | 0.40 | 0 | **quarantined** — review candidates only |
| **asserted total** | | **20651** | |

**Golden-sample ruling inherited (10-07-2026):** relaxed/fuzzy links ship only as `kochergina_corpus_relaxed_candidates.tsv`, never asserted — `norm()` folds vowel length and s/ś/ṣ, the Sanskrit minimal-pair axes (3/3 relaxed links in the B1 sample were semantically wrong).

## Coverage over the Kochergina key master

| status | keys | share |
|---|---|---|
| attested (>=1 DCS token) | 15258 | 53.4% |
| corpus-gap (no DCS attestation) | 13326 | 46.6% |
| **explained** | 28584 | 100.0% |

DCS side: 98606 lemmas with tokens; 0 junk-string lemmas skipped; 74706 lemmas matched no Kochergina key (residue — mostly corpus-only vocabulary outside a RU learners' dictionary).

**Compound-member keys:** 271 records (267 unique dashed keys) carry elision hyphens (Kochergina's compound-member mark, e.g. `-ākhyāyin`); the stripped citation form is registered as an exact-tier comparison key on the same anchor — the hyphen is an elision mark, not part of the word.

**Rights fence (N10, human-gated):** the Russian gloss TEXT is deliberately NOT shipped. Kochergina 1987 is third-party and its RU glosses stay behind the human rights gate (ROADMAP_KOSHA_NEXT_PROGRAMME_2026H2.md N10); this layer carries links + counts only.

**Verification (H4748):** 25-entry stratified sample (seed 20260915; 15 exact / 5 floor / 5 relaxed-candidates) — mechanical checks 25/25 PASS (lemma identity, token counts, key-in-source round-trip; `KOCHERGINA_JOIN_SAMPLE_25.tsv`). Adjudication: all 20 asserted links same-lexeme (exact tier is identity; the 5 floor links carry only the documented anusvāra/homorganic-nasal fold); all 5 relaxed candidates are plausible but sit on vowel-length / sibilant minimal-pair axes (vasati↔vasatī, paridāha↔parīdāha, pāśaka↔pāsaka, svaccha↔svacchā, vamra↔vāmra) and stay quarantined per the golden-sample ruling.

_Dr. Mārcis Gasūns_
