# XCHECK — Appendix-6 per-period collocate cores vs `lemma_frequency.tsv` period vectors (H4710)

_Created: 15-09-2026 · Last updated: 15-09-2026_

Independent cross-check of the two per-period frequency derivations in the estate, closing
the `dcs-sintagmatic-appendix6-periods` consumer candidate "kosha frequency-layer cross-check"
(minted H3596, executed H4710).

**Inputs**

- A6 — [`dcs-sintagmatic-appendix6-periods`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json):
  Leonchenko's 7 per-period syntagmatic tables of frequent lexical cores
  ([VisualDCS, Приложение 6](https://github.com/gasyoun/VisualDCS/tree/main/derived-data/Lexical-Cores)),
  pre-2026 DCS dump (244 texts, 4,577,915 token usages), 19,083 rows across `1.csv…7.csv`,
  each row `lemma(IAST);period_count;collocate;co_count;…`.
- TSV — [`kosha-lemma-frequency`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/kosha-lemma-frequency.meta.md):
  kosha's own M9 sidecar ([`lemma_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv)),
  `periods` column built from `period_freq source='QL/FRQ_P'` of the 2026 archive refresh.

**Join:** IAST → SLP1 via [`sanskrit-util`](https://github.com/sanskrit-lexicon/sanskrit-util)
`to_slp1` against `lemma_slp1`. Join rate **99.9–100% per file** (19,073 of 19,083 rows
joined; 10 A6-only lemmas; 0 transcoding failures; 1 replaced byte across all 7 files).

## Period mapping — proven, not assumed

The Leonchenko study (§ method, [`.doc` in VisualDCS](https://github.com/gasyoun/VisualDCS/blob/main/derived-data/Lexical-Cores/Леонченко%20В.В.%20Цифровой%20корпус%20санскрита%20для%20исследования%20лексических%20ядер%20древнеиндийской%20литературы.doc))
defines exactly 7 periods: до −800; five 500-year buckets to 1700; 1700–1956 — i.e. the
seven dated DCS buckets. Its Table 1 core sizes match the A6 line counts **exactly**,
pinning file N → bucket N:

| file | study period | TSV key | A6 rows | Table 1 core size |
|---|---|---|---:|---:|
| 1.csv | до −800 | `1 -800` | 1,932 | 1,932 |
| 2.csv | −800…−300 | `2 -300` | 2,334 | 2,334 |
| 3.csv | −300…200 | `3200` | 2,327 | 2,327 |
| 4.csv | 200…700 | `4700` | 3,428 | 3,428 |
| 5.csv | 700…1200 | `5 1200` | 3,096 | 3,096 |
| 6.csv | 1200…1700 | `6 1700` | 3,493 | 3,493 |
| 7.csv | 1700…1956 | `7 1900` | 2,473 | 2,473 |

The TSV umbrella slots `9 Vedic` / `11 Epic` / `12 Classic` have no A6 counterpart.

## Baseline calibration (why ratios ≠ 1)

The A6/Прил-7 dump runs systematically above the TSV's `count_all`: median ratio
**1.396** (n=301, all-corpus [Приложение 7](https://github.com/gasyoun/VisualDCS/blob/main/derived-data/Lexical-Cores/Prilozhenie-7.-«Sintagmaticheskaya-tablica-dlya-vseh-lemm-korpusa»v/DCS_Sintagmatic.csv)
field-2 vs `count_all`). Two snapshots, two extractions — the check is rank agreement +
delta quantification, not equality.

## Per-period aggregates

Full table: [`appendix6_xcheck_delta.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/appendix6_xcheck_delta.tsv)
(19,083 rows; ratio = a6/tsv). `ρ` = Spearman over all joined lemmas of the period;
ratio stats over lemmas with TSV count > 20.

| period | key | ρ | median ratio | n(>20) | % within ±2× | verdict |
|---|---|---:|---:|---:|---:|---|
| до −800 | `1 -800` | 0.835 | 1.71 | 1,586 | 83.7% | confirmed |
| −800…−300 | `2 -300` | 0.270 | 3.76 | 450 | 26.7% | **NOT confirmed** |
| −300…200 | `3200` | 0.889 | 1.54 | 2,325 | 97.1% | confirmed (best) |
| 200…700 | `4700` | 0.807 | 1.29 | 3,035 | 89.6% | confirmed |
| 700…1200 | `5 1200` | 0.793 | 0.95 | 3,031 | 86.9% | confirmed |
| 1200…1700 | `6 1700` | 0.527 | 1.88 | 1,546 | 41.9% | **partial** |
| 1700…1956 | `7 1900` | 0.500 | 7.10 | 308 | 11.7% | **NOT confirmed** |

## Findings

1. **Buckets 1/3/4/5 independently confirmed** — ρ 0.79–0.89, ≥ 84% of lemmas within ±2×.
   The two derivations are the same population at the rank level; the TSV LEFT-JOIN
   contract ("never re-derive frequency ordering") stands.
2. **Buckets 2/6/7 are the delta surface.** A6 puts Epic-scale counts in `2 -300`
   (mahat 6,172 vs 121; indra 5,647 vs 158; ratha, mitra, jana, bāhu all >30×) and
   epic/śāstra-scale counts in `6 1700` (rājan 2,721 vs 71; brū, vīra, putra >20×),
   plus a Rasaśāstra-heavy `7 1900` (kṣip, pac, cūrṇa, bhasman, sūta all >30×) where
   the TSV slot is thin. Consistent with text re-dating / extraction-coverage drift
   between Leonchenko's dump and the 2026 archive's FRQ_P (Hellwig's Bayesian
   re-dating sits between them); observed as delta, cause not asserted here.
3. **A6 carries duplicate lemma rows** — 723 lemmas appear >1× per file (768 extra rows;
   worst: `vid` ×4, `akṣa` ×4, `pā` ×4). Consumers must aggregate (sum) before use.
   The delta table keeps one row per source line; sample verification is line-indexed.
4. **A6 stays a collocate-profile asset.** For exact per-period counts the TSV remains
   authoritative; A6's value for kosha is its ranked per-period collocate lists
   (e.g. Sanskrit-in-Numbers period modules — the second registered consumer candidate).

## Verification (frozen sample)

21 rows, seed 4710, 3 per period —
[`appendix6_xcheck_sample_frozen.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/appendix6_xcheck_sample_frozen.tsv):

- In-script: each sampled line re-parsed through an independent char-walk parser and
  asserted equal (lemma + count) before delta computation — **21/21 PASS**.
- Out-of-script: awk first-match spot-check over the raw A6 files — 19/21 exact; the 2
  misses (`durga`, `amṛta`) are finding-3 duplicates (awk first row vs sampled row),
  consistent with the duplicate census above.
- Offline selftest with embedded fixture: `python scripts/xcheck_appendix6_period_freq.py --selftest` → PASS.

## Reproduce

```
python3 scripts/xcheck_appendix6_period_freq.py            # needs sibling VisualDCS checkout
python3 scripts/xcheck_appendix6_period_freq.py --selftest # offline, no data
```

**Changed:** cross-check script + delta table + frozen sample + this report; datasets.json
consumer promotion for `dcs-sintagmatic-appendix6-periods`. **Unchanged:**
`lemma_frequency.tsv` bytes (no repair warranted — findings 2/3 are A6-side properties).
**Risks:** buckets 2/6/7 drift means per-period vector consumers should not be re-pointed
at A6 counts; duplicate-row trap for future A6 consumers (flagged in datasets.json notes).
**Inspect first:** the aggregate table above, then finding 3.

_Гасунс_
