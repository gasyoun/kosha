# Data statement — Aṣṭādhyāyī sūtra-coverage / dark-class map (`paninian-sutra-coverage-map`)

_Created: 24-07-2026 · Last updated: 24-07-2026_

Data statement for Concordance-Q3 **W3a** (H1468) — the programme exit check.
Manifest: `id: paninian-sutra-coverage-map`. Download:
[`sutra_coverage_map.tsv` in data-v0.3.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.3.0).
Build report:
[SUTRA_COVERAGE_BUILD_REPORT.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/SUTRA_COVERAGE_BUILD_REPORT.md).

## Composition & counts

**Named enumeration:** vidyut 0.4.0 `Data.load_sutras()` Source.Ashtadhyayi
(`sutrapatha.tsv` catalogue) — **n = 3983** (exact; never "~4,000").

| Status | Count | % of 3983 |
|---|---:|---:|
| `lit` | 221 | 5.55% |
| `dark-unattested` | 55 | 1.38% |
| `dark-out-of-scope` | 3707 | 93.07% |
| `dark-engine-gap` | 0 | 0.00% |

Columns: `sutra_id`, `sutra_text_slp1`, `exemplar_forms`, `exemplar_loci`,
`texts`, `mean_chain_position`, `status`, `scope_justification`.

**Ratio headline (must never collapse the three dark classes):**  
lit : dark-unattested : dark-out-of-scope : dark-engine-gap = **221 : 55 : 3707 : 0**.

## Source provenance

[`scripts/build_sutra_coverage_map.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sutra_coverage_map.py)
over W2a/W2b TSVs + fire-set harvest of all 91,027 AG lemmas' successful
`vidyut.prakriya` cell histories + optional DCS text-name join. Rights: same
W1a A4 record.

## Curation rationale

"N sūtras have no exemplars" is nearly useless — the reasons differ in kind
(philological finding / engine-coverage fact / defect). The three dark classes
are the point of the deliverable (ARCHITECTURE §5; VERIFICATION 3a-3, 3a-8).

## Known biases & limitations

- `dark-engine-gap` is **not measurable** from W2a (empty `chain_id` on
  `engine-error`); reported 0 with that explanation, not inflated.
- `dark-out-of-scope` = complement of the AG-cell fire-set inside the named
  enumeration — a generator-surface fact, not a claim about classical grammar.
- Lit rollups inherit W2b ok-only inversion limits.

## License

**CC BY-SA 4.0** with vidyut + DCS attribution (A4 composition).

## Deprecation status

`active`.

_Dr. Mārcis Gasūns_
