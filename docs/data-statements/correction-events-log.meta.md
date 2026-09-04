# Data statement — Correction-event log, full trio (`correction-events-log`)

_Created: 04-09-2026 · Last updated: 04-09-2026_

Data statement for the `correction-events-log` dataset served by the kosha
data-hub — the git-mined correction history of the Cologne digitization trio.
Manifest row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
Citable deposit: OBS-T snapshot `obs-t-data-v1.0.0`, concept DOI
[10.5281/zenodo.21346705](https://doi.org/10.5281/zenodo.21346705)
(version 21965649), license CC BY 4.0.

## Composition & counts

Three CSV views of one event log — `_all`, `_typed`, `_final` — **52,498 data
rows per view** (sizes 57.8 + 59.0 + 61.2 MB). Keying: `event_id` → date,
dict, headword IAST, old/new IAST, edit-op trace, corrector, latency, evidence
level; `_typed` adds the empirical error typology; `_final` is the canonical
enriched view.

## Source provenance

Built by the csl-observatory `obs_q` pipeline
([gasyoun/csl-observatory](https://github.com/sanskrit-lexicon/csl-observatory),
`observatory/site/src/data/correction_events_{all,typed,final}.csv`):
28,057 git-mined correction events plus release diffs
(H694 provenance, 11-07-2026; 52,498-row release snapshot swept across
citation surfaces 24-08-2026, csl-observatory b243ef7).

## Citation

Cite the concept DOI above (all versions). Consumers: SanskritLexicography
FEATURES_INDEX (E41), Uprava DATA_LAYERS_CENSUS §4, corrector-behaviour /
error-typology studies (A36 family, paper A12/OBS-T).

_Misuse:_ the released snapshot is a frozen 52,498-row view — do not quote
growing working-copy counts as release counts.

_Dr. Mārcis Gasūns_
