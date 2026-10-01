# DATASET_DISCIPLINES_REPORT — kosha reads the meso→discipline crosswalk (H4737)

_Created: 15-09-2026 · Last updated: 15-09-2026_

H4737 (F5 consumer leg, kosha half): [dataset_disciplines.json](dataset_disciplines.json) joins
every registered kosha dataset (132, [datasets.json](../manifest/datasets.json)) through the
estate's ratified Russian-Indology meso vocabulary to the discipline taxonomy of
[IndologyScholars](https://github.com/gasyoun/IndologyScholars) —
[curation/meso_discipline_crosswalk.csv](https://github.com/gasyoun/IndologyScholars/blob/main/curation/meso_discipline_crosswalk.csv)
(50 confidence-scored mappings) + [curation/disciplines.csv](https://github.com/gasyoun/IndologyScholars/blob/main/curation/disciplines.csv)
(15-code spine, D1 10-07-2026). The taxonomy is **never re-derived kosha-side**; the consumer reads the
sibling crosswalk read-only and pins its commit in [dataset_disciplines.source.json](dataset_disciplines.source.json).
kosha contributes only the reviewed assignment layer
[data/manifest/dataset_meso_assignments.json](../manifest/dataset_meso_assignments.json), mirroring the
csl-atlas precedent (H4178 flip 3, `dict_meso_assignments.json`) so both consumers speak one vocabulary.

## Coverage at build (15-09-2026)

| Metric | Value |
|---|---|
| Datasets joined | 132 (100% of the registry, self-row included) |
| Assigned | 126 |
| Honest nulls (no facet, never forced) | 6 (incl. the packet's own self-row) |
| Distinct disciplines reached | 4 |
| NOT-MAPPED sentinels surfaced from the crosswalk | 8 |
| Per-discipline confidence rows | 138 (min 0.3, max 0.9025) |

Per-discipline dataset coverage: sanskritology 115 · literature 20 · linguistics 2 · dravidology 1
(literature exceeds the 8 literary-subject datasets because the crosswalk gives
`epic_ramayana_mahabharata` and `prosody`/`translation_reception` deliberate **dual** mapping —
«двойная принадлежность ожидаема» — so epic and metre datasets carry a secondary literature face).

## Assignment layer — the honest parts

- **General Sanskrit lexicography has no meso code.** The ratified precedent (csl-atlas) routes it to
  `sanskrit_grammar_panini` (crosswalk target sanskritology) at deliberately ≤ 0.6. 101 of 132 kosha
  datasets take that nearest-facet route — kosha is a lexicography hub, and the packet says so.
- **Text-apparatus vs phenomenon.** Datasets whose subject is a text take the text's facet (Gita/Nala/MBh →
  `epic_ramayana_mahabharata` ×10; Hitopadeśa/Kirātārjunīya/subhāṣita → `literary_studies` ×6); datasets
  whose subject is a linguistic phenomenon (sandhi, morphology, paradigms, Pāṇini) take the grammar facet
  even when sourced from one text (e.g. `gita-sandhi` → grammar 0.7, not epic).
- **Direct facets get high confidence:** Bloomfield RV × Elizarenkova → vedic 0.95; Sundarakāṇḍa/MBh
  vulgate-critical → epic 0.95; Pāṇinian machinery (derivation status, sūtra coverage, Śiva Sūtras) → 0.9;
  `tamil-fold` → dravidology 0.75; metre datasets → prosody.
- **Honest nulls — 6, never forced:** `reading-pack-difficulty` (mixed-text pedagogy metrics, no single
  facet), `handoff-lifecycle-gold` (org-process meta), `akshara-mt-benchmark-pilot` + `-full` (NLP eval;
  no NLP facet, and `translation_reception` is scoped to the literary-translation plot),
  `zaliznyak-lectures-transcripts` (teaching-material census), `dataset-disciplines` (the packet's own
  self-row — a self-referential discipline assignment is not meaningful).
- **Sentinels surfaced, not hidden:** the crosswalk's 8 `НЕ МАППИТСЯ` rows (regional/methodological codes:
  bengal, himalaya, assam, nepal_newar_kathmandu, china_mongolia_inner_asia, twentieth_century,
  comparative_analysis, board_games) are carried verbatim into the packet's `notMappedSentinels`.

## Provenance & verification

- Consumer: [scripts/build_dataset_disciplines.py](../../scripts/build_dataset_disciplines.py); `--check`
  re-derives the committed packet **byte-identically** (the payload carries no timestamps) and pins the
  sibling `feedCommit` — stale pins warn without failing, missing sibling degrades to internal-consistency
  so CI stays green (csl-atlas validator contract).
- Canaries (deterministic, re-derived at every `--check`): `gita-reading-pack` → sanskritology 0.68 +
  literature 0.595; `bloomfield-rv-citations` → sanskritology 0.9025; `tamil-fold` → dravidology 0.7125;
  `mw-etymology` → linguistics 0.6375; `reading-pack-metre` → literature 0.49 + sanskritology 0.35.
- License: crosswalk + spine are IndologyScholars derived exports, CC-BY-4.0 with archive attribution
  (carried in the packet envelope).
- Build: PASS, `python3 scripts/build_dataset_disciplines.py --check` — 132/126/6/4, exit 0, ~0.1 s, no
  network. Manifest row `dataset-disciplines` (tier public).

_Гасунс_
