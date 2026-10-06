# 2026-10-06 — H6053 Zaliznyak token distribution (A55/A56 index)

Added `scripts/zaliznyak_token_distribution.py` plus committed artifacts:
`data/zaliznyak/zaliznyak_token_distribution.tsv` (342 tokens; coverage
guarantee — sum = 98,639 rows), `zaliznyak_markup_anomalies.tsv` (census: 0
empty tokens, 0 gender contradictions, 28 `-inI` fem_fold orphans, 9 doubled
lex abbreviations, 53 singleton tokens, 38+28 paradigm_classes drift),
summary JSON, and 4 SVG charts (`docs/charts/h6053_*.svg`). Headline for the
A56 revision: the data-v0.4.0 deposit carries **342** tokens (manifest/paper
say 335); 99% checkpoint is **153** tokens (paper: 154); 50%=6 and 80%=26
confirmed. Source-dictionary join: mean n_dicts 4.72/15, 42% of rows in ≥5
dictionaries. Report:
docs/H6053_ZALIZNYAK_TOKEN_DISTRIBUTION_REPORT_06.10.26.md. Manifest row
`zaliznyak-token-distribution` + data statement added.
