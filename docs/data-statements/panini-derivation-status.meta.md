# Data statement — vidyut derivation harness over the AG bucket (`panini-derivation-status`)

_Created: 24-07-2026 · Last updated: 24-07-2026_

Data statement for Concordance-Q3 **W2a** (H1368). Manifest:
[datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
`id: panini-derivation-status`. Download in
[data-v0.3.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.3.0):
`derivation_status.tsv` + sidecar `derivation_chains.tsv`.

## Composition & counts

**401,368** rows — one per W1b AG-bucket form (`morph_attest_AG.tsv`). Status
distribution (always all four buckets):

| Status | Count | % |
|---|---:|---:|
| `ok` | 72,764 | 18.13% |
| `no-derivation` | 237,447 | 59.16% |
| `ambiguous` | 86,857 | 21.64% |
| `engine-error` | 4,300 | 1.07% |

`derivation_chains.tsv`: **2,815** distinct `chain_id` values; ordered
`(source, sutra_code, step_result)` steps. Only `ok` rows carry a non-empty
`chain_id` in the shipped build.

## Source provenance

[`scripts/build_panini_derivations.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_panini_derivations.py)
over AG forms + read-only `kosha.db` `inflections` cells + local
`vidyut.prakriya` 0.4.0 (R12 — no network). Rights gate:
[vidyut_prakriya_derivation_2026-07.md](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/vidyut_prakriya_derivation_2026-07.md).

## Curation rationale

Captures the ordered sūtra chain that produced each attested∧generated form so
W2b can invert to a sūtra concordance without re-calling the engine.

## Known biases & limitations

- Verbal dhātu/gaṇa/lakāra mapping sources most `engine-error` rows.
- `ambiguous` rows lack recorded candidate chains (parked W2a gap).
- R-C4: 256 ok rows carry `tense_caveat=1`.
- Top-frequency AG lemmas include short function words with floor-tier lemma
  collisions (documented in DERIVATION_HARNESS_BUILD_REPORT.md).

## License

**CC BY-SA 4.0** with vidyut (MIT) + DCS (CC BY 4.0) attribution — same A4
composition as `paninian-corpus-concordance`.

## Deprecation status

`active`.

_Dr. Mārcis Gasūns_
