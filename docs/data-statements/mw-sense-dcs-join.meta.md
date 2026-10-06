# Data statement — MW senses × DCS citations, full-volume join (`mw-sense-dcs-join`)

_Created: 06-10-2026 · Last updated: 06-10-2026_

Manifest row: [data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
Report: [MW_SENSE_DCS_JOIN_REPORT.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/MW_SENSE_DCS_JOIN_REPORT.md).

## Composition & counts

`data/concordance/mw_sense_dcs_join.tsv.gz` — 303,023 rows (one per MW numbered
sense, kosha.db `entries`/`senses`, dict='mw'), 18 columns: entry/locus keys
(`entry_id`, `L`, `slp1`, `k2`, `n_entries_key`, `sense_n`, `sense_ord`,
`gloss`), corpus tier (`dcs_match`, `dcs_count_all`, `dcs_rank_all`,
`dcs_grammar`, `dcs_periods_sum`), WordSem tier (`ws_count`, `ws_rank`,
`ws_share`, `ws_prov`), estimate flag (`mfs_est`). `dict_only` rows keep empty
corpus columns. Companion `mw_sense_dcs_join_corpus_only.tsv` (26,120 DCS
lemmas with no MW headword) and `mw_sense_dcs_observatory_feed.json`
(dashboard feed for csl-observatory H6071).

## Source provenance

Built by `scripts/build_mw_sense_dcs_join.py` (H6066, 06-10-2026) READ-ONLY over:

- kosha.db MW entries/senses (286,525 entries; cross-dated csl-sqlite release per D5) — dictionary side, full volume
- `kosha-lemma-frequency` sidecar (lemma_frequency.tsv, committed; source M9 archive.sqlite period_freq) — corpus citation aggregates
- `kosha-sense-frequency` sidecar layer=mw (sense_frequency.tsv, H1453/H1459/H1588) — WordSem per-sense ATTESTED counts (gold wins over fused estimates)
- `wsd_untagged_mfs_counts.tsv` (H1588) — mfs_est flag only, never a count
- dcs_full.sqlite (sha256 8f3b06bd…, manifest pin) — validation probe only, not a build input

Sense ordinal = 1-based printed order per slp1_key over
`(CAST(L AS INTEGER), sense_n)` — byte-identical convention to
`wn_to_mw_map.tsv` sense_id (H1453), so ws counts land on the right sense.

## Coverage (both denominators)

47.33% of MW senses have a DCS-attested headword (143,428/303,023); 7.62%
carry WordSem per-sense attested counts (23,088); 68.63% of DCS lemmas match
an MW headword (57,157/83,277). Residues first-class: 159,595 `dict_only`
senses (NOT ghost senses by default — corpus lacunarity, FINDINGS §86);
136,092 senses on homonym-collision keys — declared via `n_entries_key`,
never silently resolved.

## Known limits

`dcs_count_all` comes from the M9 sidecar: a 50-sample cross-check against
dcs_full-2026 raw tokens found it a strict lower bound (24 within ±5%, 26
below, 0 above). Homonym attribution is headword-level. Validation probes
transcode IAST→SLP1 with sanskrit-util (SLP1 capitals are phonemes — never
casefold). Recompute: `--check` (parity) and `--validate` (evidence re-query),
both green at build time.
