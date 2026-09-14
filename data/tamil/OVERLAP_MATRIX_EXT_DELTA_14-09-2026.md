# Headword overlap matrix — Tamil-fold extension, delta report (H4732, census C5)

_Generated 14/15-09-2026 by `scripts/build_overlap_matrix_ext.py`; inputs pinned in [overlap_matrix_ext_stats.json](overlap_matrix_ext_stats.json)._

- Registered `headword-overlap-matrix`: 15 dicts / 105 cells (predates the 06-09-2026 [tamil-fold](fold_stats.json) ingest, H4178).
- This extension: **18 dicts / 153 cells** (+ mwd, cap, otl from csl-santam; cpd/Pahlavi excluded as in csl-santam's own UI).
- New cells: **48** (3 x 15 vs the union + 3 among the fold); extension-invariance of the 105 base cells (recomputed with and without the fold): **PASS**.

## Keying (the load-bearing decision)

- Fold `st` keys are Kyoto-Harvard (mwd/cap) or HK-like (otl) — [fold_stats.json](fold_stats.json); the union is keyed SLP1.
- Chain: `scheme_bridge.hk_to_iast` -> `sanskrit_util.to_slp1` (house SLP1 table imported, never re-typed). otl runs the same HK-like treatment; residual scheme risk is flagged, fold normalization stays a Wave-4 item.
- Minimal cleaning: strip; `&` variants split into separate keys; `-`-prefixed continuation tokens dropped; non-alphabet residue counted, keys kept (they simply cannot match the union).

## Baseline drift (reported, not caused by this extension)

- 27 of 105 registered cells differ from a recomputation on the CURRENT union — max union-size delta 3.
- Cause: registered matrix (H684, 11-07-2026) was computed on the pre-H4075 union (323,425 rows); union regenerated 04-09-2026 (323,422 rows) — drift is upstream of and independent from this extension.
- The extension-invariance gate above proves the fold changes none of them; the authoritative current-union values are the ones in the extended TSV.

## Per-dictionary profile (extended matrix)

| dict | headwords | fold keys matched into union | corpus-attested % |
|---|---:|---:|---:|
| MW | 193851 | — | 31.69 |
| mwd | 158956 | 155095 (97.57%) | 34.71 |
| PWK | 151314 | — | 33.58 |
| otl | 107197 | 1593 (1.49%) | 0.59 |
| PWG | 106054 | — | 41.21 |
| AP | 88747 | — | 22.35 |
| VCP | 48583 | — | 50.02 |
| SKD | 40703 | — | 14.16 |
| CAE | 38476 | — | 58.99 |
| cap | 36431 | 33315 (91.45%) | 54.48 |
| CCS | 28743 | — | 64.09 |
| SCH | 28431 | — | 30.98 |
| MD | 20095 | — | 67.87 |
| BUR | 19135 | — | 48.62 |
| BHS | 17761 | — | 27.29 |
| GRA | 11108 | — | 68.28 |
| INM | 9431 | — | 58.67 |
| VEI | 3702 | — | 76.63 |

## Top 12 and bottom 6 of the 48 new cells

| dict_a | dict_b | shared | union | jaccard |
|---|---|---:|---:|---:|
| CAE | cap | 33193 | 41714 | 0.795728 |
| MW | mwd | 155026 | 197781 | 0.783827 |
| CCS | cap | 24801 | 40373 | 0.614297 |
| PWK | mwd | 113790 | 196480 | 0.579143 |
| PWG | mwd | 87194 | 177816 | 0.490361 |
| MD | cap | 12059 | 44467 | 0.271190 |
| PWG | cap | 25429 | 117056 | 0.217238 |
| VCP | mwd | 36067 | 171472 | 0.210338 |
| CAE | mwd | 32640 | 164792 | 0.198068 |
| PWK | cap | 29654 | 158091 | 0.187576 |
| VCP | cap | 13093 | 71921 | 0.182047 |
| cap | mwd | 28680 | 166707 | 0.172038 |
| GRA | otl | 254 | 118051 | 0.002152 |
| SKD | otl | 260 | 147640 | 0.001761 |
| SCH | otl | 217 | 135411 | 0.001603 |
| BHS | otl | 150 | 124808 | 0.001202 |
| INM | otl | 98 | 116530 | 0.000841 |
| VEI | otl | 80 | 110819 | 0.000722 |

## Reading

- **cap x CAE = 33193 shared (0.7957 J)** — the same Capeller dictionary via two routes (union CAE key1s vs csl-santam fold), so this cell is the keying-chain canary: a near-full match validates HK->SLP1 end to end.
- **mwd x MW = 155026 shared (0.7838 J)** — Cologne MW re-edition vs the union's MW; the gap is union key2/variant entries and fold encoding noise, not missing content.
- **otl x MW = 913 shared (0.0030 J)** — the Tamil Lexicon's Sanskrit layer; the only genuinely new content of the three (the estate's first otl surface beyond the fold).
- **otl residue is expected, not loss:** 34870 of 107197 unique keys (32.5%) carry non-SLP1-alphabet residue — Tamil Lexicon headwords are largely Tamil words in Tamil-specific phonology (ẓ/ṉ/ṟ-class letters the Sanskrit alphabet has no SLP1 letter for); only its Sanskrit layer can overlap the union by construction.
- cpd (Concise Pahlavi) is deliberately excluded: csl-santam's own form and `all` query exclude it (`id<4`).

## What this changes / does not change

- Changes: nothing registered. The 15-dict `headword-overlap-matrix` dataset, the union master and `HeadwordLists` are untouched; this ships a kosha-side extended dataset (`headword-overlap-matrix-ext`).
- The 105 base cells proved extension-invariant (identical with and without the fold); against the registered baseline they drift by ≤3 in union size purely from the 04-09 H4075 union regen — recorded per cell in the stats JSON.

_Auto-generated; do not hand-edit numbers._
