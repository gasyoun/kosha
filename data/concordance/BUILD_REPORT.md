# dict-corpus-concordance — build report

_Created: 10-07-2026 · Last updated: 10-07-2026_

Built by [scripts/build_dict_corpus_concordance.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_dict_corpus_concordance.py) (H380, Fable 5 `claude-fable-5`).

## Per-tier link counts (exit-check: no silent fuzzy blur)

| tier | confidence | links | status |
|---|---|---|---|
| xref | 0.99 | 12836 | asserted |
| exact | 0.95 | 61373 | asserted |
| floor | 0.85 | 311 | asserted |
| relaxed | 0.60 | 2171 | **quarantined** — review candidates only |
| fuzzy | 0.40 | 0 | **quarantined** — review candidates only |
| **asserted total** | | **74520** | |

**Golden-sample ruling:** the stratified verification sample (seed 20260710; 4 xref / 4 exact / 3 floor / 3 relaxed) passed every mechanical check (lemma identity, token counts, citable-locus resolution 14/14), but adjudication found **all 3 relaxed links semantically wrong** (aṃśaka 'share' ↔ aṃsaka 'shoulder'; vikarṣaṇa 'dragging' ↔ vikarśana 'emaciating'; ram ↔ rāṃ) — `norm()` folds vowel length and s/ś/ṣ, the exact axes of Sanskrit minimal pairs. relaxed/fuzzy links are therefore shipped only as `dict_corpus_relaxed_candidates.tsv` (review queue), never asserted.

## Coverage over the union headword master

| status | headwords | share |
|---|---|---|
| attested (>=1 DCS token) | 66257 | 20.5% |
| corpus-gap-single-dict | 134602 | 41.6% |
| corpus-gap-multi-dict | 122566 | 37.9% |
| **explained (attested or classed absence)** | 323425 | 100.0% |

DCS side: 98606 lemmas with tokens; 0 junk-string lemmas skipped; 21970 lemmas matched no headword (residue, listed honestly — mostly proper names, segmentation artifacts, and corpus-only vocabulary).

**Stated cap:** the static viewer shards carry at most 2 KWIC samples per link, sentences truncated at 160 chars — a preview layer only; every attestation remains queryable against the canonical `dcs-full-sqlite` (the dataset row carries the full `evidence_count`).

_Dr. Mārcis Gasūns_
