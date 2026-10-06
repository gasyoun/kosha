# Data statement — Zaliznyak token distribution over 98,639 headwords (`zaliznyak-token-distribution`)

_Created: 06-10-2026 · Last updated: 06-10-2026_

Derived companion table for [`zaliznyak-grammar-index`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/zaliznyak-grammar-index.meta.md).
Manifest row: [data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).

## Composition & counts

`data/zaliznyak/zaliznyak_token_distribution.tsv` — 342 rows (one per
paradigm token of the source index), columns: `index_token`, `gender`,
`stem_class`, `member_count`, `pct_rows`, `cum_pct_rows`, `mean_n_dicts`,
`pct_rows_ge5_dicts`, `in_paradigm_classes`. Coverage guarantee: sum of
`member_count` = 98,639 — every source row counted exactly once
(`scripts/zaliznyak_token_distribution.py --check`).
`data/zaliznyak/zaliznyak_markup_anomalies.tsv` — anomaly/markup-gap census
(14 rows: 0 empty tokens, 0 gender contradictions, 28 unjoined `-inI`
headwords, 9 doubled lex abbreviations, 53 singleton tokens, 38+28
`zaliznyak_paradigm_classes.tsv` drift tokens, 7 mixed-lex tokens).
`zaliznyak_token_distribution_summary.json` — machine summary incl. the
n_dicts source-dictionary join (99.97% of rows; mean 4.72 of 15 dictionaries).
Charts: `docs/charts/h6053_*.svg` (Zipf, cumulative coverage, stem classes,
n_dicts histogram). Report:
[H6053_ZALIZNYAK_TOKEN_DISTRIBUTION_REPORT_06.10.26.md](https://github.com/gasyoun/kosha/blob/main/docs/H6053_ZALIZNYAK_TOKEN_DISTRIBUTION_REPORT_06.10.26.md).

## Source provenance

Built by `scripts/zaliznyak_token_distribution.py` (H6053, 06-10-2026) from
the frozen data-v0.4.0 assets `zaliznyak_grammar_index.tsv` (98,639 rows) and
`union_headwords.tsv` (frozen data-v0.4.0 cut of the 15-dict union; live
union re-anchored to csl-orig v02 at 323,422 rows — H4075) read at build time
from the sibling
SanskritLexicography checkout (release asset MD5-identical to the live copy,
verified 06-10-2026). No source bytes vendored.

## Known biases & limitations

- Numbers are pinned to data-v0.4.0; a future re-cut of the grammar index
  (live token inventory may drift) requires a rebuild.
- `n_dicts` is dictionary breadth, not corpus frequency; 28 `-inI` headwords
  never join the union (fem_fold seam, documented in the report).
- The distribution counts headword types, not tokens-in-corpus.

## Intended use / known misuse

**For:** JOHD paper A56 revision (token inventory 342 not 335; 99% checkpoint
153 not 154; zero-contradiction QA claim), drills-layer regeneration scoping,
quantitative morphology. **Misuse:** reading member_count as corpus
attestation; treating `mean_n_dicts` as frequency.

## Maintenance & sunset plan

Rebuild via the script after each `data-v*` re-cut of the grammar index;
`--check` verifies committed outputs without source access. Sunset: subsumed
when the grammar index gains a per-release distribution sidecar.

## Deprecation status

`active` (derived, regen-checked 2026-10-06: PASS).

## License

CC BY-SA 4.0 per [LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md)
(derived from the CDSL PWG digitization served via the kosha data release).

## Provenance of this statement

Authored 06-10-2026 by GLM 5.3 (`opencode/zai-coding-plan/glm-5.3`) under
handoff [H6053](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6053-GLM_kosha_zaliznyak-morpho-distribution_04.10.26.md).

_Dr. Mārcis Gasūns_
