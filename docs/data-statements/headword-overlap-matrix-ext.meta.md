# Data statement — Headword overlap matrix, Tamil-fold extension (18 dicts)

_Created: 15-09-2026 · Last updated: 15-09-2026_

**Dataset:** `headword-overlap-matrix-ext` — the registered
`headword-overlap-matrix` (15-dict union, H684) extended with the three
lexica of the 06-09-2026 `tamil-fold` ingest (H4178): **mwd** (Cologne Digital
Sanskrit Lexicon = MW), **cap** (Capeller), **otl** (Cologne Online Tamil
Lexicon). 18 dictionaries, 153 pairwise cells. cpd (Concise Pahlavi) is
excluded exactly as csl-santam's own UI excludes it (`id<4`).

**File:** [`data/tamil/headword_overlap_matrix_ext.tsv`](https://github.com/gasyoun/kosha/blob/main/data/tamil/headword_overlap_matrix_ext.tsv)
(153 data rows; regenerate: [`scripts/build_overlap_matrix_ext.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_overlap_matrix_ext.py),
verify: `python scripts/build_overlap_matrix_ext.py --verify`).
Delta report: [`data/tamil/OVERLAP_MATRIX_EXT_DELTA_14-09-2026.md`](https://github.com/gasyoun/kosha/blob/main/data/tamil/OVERLAP_MATRIX_EXT_DELTA_14-09-2026.md);
provenance pins + per-cell drift: [`data/tamil/overlap_matrix_ext_stats.json`](https://github.com/gasyoun/kosha/blob/main/data/tamil/overlap_matrix_ext_stats.json).

**Source legs (all read-only, never rebuilt here).**

1. Union master `HeadwordLists/union/union_headwords.tsv`
   ([SanskritLexicography](https://github.com/gasyoun/SanskritLexicography/blob/master/HeadwordLists/union/union_headwords.tsv),
   H4075 regen, 323,422 rows) — the 15 union codes.
2. [`csl-santam/sqlite/tamil.sqlite`](https://github.com/sanskrit-lexicon/csl-santam/blob/master/sqlite/tamil.sqlite)
   (pinned by [`data/tamil/fold_stats.json`](https://github.com/gasyoun/kosha/blob/main/data/tamil/fold_stats.json))
   — the fold keys, per-cell UTF-8/cp1252/latin-1 decoded as in
   `scripts/ingest_tamil_fold.py`.
3. House translit chain — `sanskrit-util` `to_slp1` (SLP1 table imported,
   never re-typed) × `tools/KeySwap/scheme_bridge` `hk_to_iast`. Fold `st`
   keys are Kyoto-Harvard (mwd/cap) or HK-like (otl); otl runs the same
   treatment and its Tamil-specific phonology shows up as counted, expected
   residue (32.5% of its keys), not as loss.

**Verification.** Extension-invariance gate: the 105 base cells recomputed
with and without the fold are identical (PASS) — the extension adds
rows/columns only. 27 of the 105 registered cells drift by ≤3 in union size
against the H684 baseline because that baseline was computed on the
pre-H4075 union (323,422 rows); the drift is upstream of this extension and
is recorded per cell in the stats JSON. Canaries: cap×CAE J = 0.7957 and
mwd×MW J = 0.7838 validate the HK→SLP1 chain end to end; otl contributes
its Sanskrit layer (1,593 keys into the union; 913 shared with MW).

**Rights.** Derived pairwise counts on public dictionary headwords —
CC BY-SA 4.0, credit Dr. Mārcis Gasūns, consistent with the
`headword-overlap-matrix` and `tamil-fold` family.

_Гасунс_
