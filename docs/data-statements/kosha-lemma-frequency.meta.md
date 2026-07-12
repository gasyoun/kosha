# Data statement — DCS lemma frequency sidecar (`kosha-lemma-frequency`)

_Created: 11-07-2026 · Last updated: 11-07-2026_

Data statement for the `kosha-lemma-frequency` dataset served by the kosha
data-hub. Manifest row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
Download: [`lemma_frequency.tsv` in release data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0).

## Composition & counts

83,277 rows, one per lemma attested in the Digital Corpus of Sanskrit (DCS),
with whole-corpus counts and per-period frequency vectors. TSV, UTF-8,
8 columns:

| Column | Content |
|---|---|
| `lemma_slp1` | lemma, SLP1 |
| `count_all` | whole-corpus token count |
| `grammar_all` | DCS grammar tag(s) for the lemma |
| `rank_all` | whole-corpus frequency rank |
| `periods` | pipe-separated per-period vector, `slot label=count` (e.g. `9 Vedic=8283\|1 -800=2897\|…\|12 Classic=55544`) — chronological slots plus the aggregate Epic/Classic slots |
| `periods_sum` | sum across period slots (exceeds `count_all` where aggregate slots overlap dated slots — see limitations) |
| `coverage_pct` | cumulative core-vocabulary coverage at this rank, where computed |
| `core_rank` | rank within the core-vocabulary ordering, where assigned |

## Source provenance

Derived in [gasyoun/kosha](https://github.com/gasyoun/kosha)
(`data/frequency/lemma_frequency.tsv`) by the DCS M9 join: token/lemma data
from the [Digital Corpus of Sanskrit](https://github.com/OliverHellwig/sanskrit)
(© Oliver Hellwig, CC BY; ~5.7M tokens, 270 texts in the 2026 snapshot,
ingested via the canonical VisualDCS CoNLL-U import) joined against the
[`union-headwords`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/union-headwords.meta.md)
spine.

## Curation rationale

Frequency ordering is the single most re-derived statistic in the ecosystem —
teaching orders, translation-priority worklists, and evidence layers all need
it. This sidecar freezes one canonical ordering (whole-corpus + diachronic
vectors) so consumers LEFT-JOIN it instead of re-counting the corpus (the
manifest note is explicit: "LEFT-JOIN this — never re-derive frequency
ordering").

## Language variety

Sanskrit (ISO 639-3 `san`) as sampled by DCS: a digitized, lemmatized corpus
spanning Vedic to early-modern texts, with well-known genre skew (śāstra,
epic, and kāvya heavily represented; inscriptional and vernacular-adjacent
Sanskrit absent). Period labels follow DCS dating slots, which assign one date
per *text* — a composite text's internal chronology is flattened.

## Annotator / process information

Deterministic aggregation over DCS's expert lemmatization (Hellwig's
annotation pipeline upstream); no LLM-generated content in this table. Lemma
identity, grammar tags, and text dating are inherited from DCS editorial
decisions, not re-adjudicated here.

## Known biases & limitations

- **Corpus ≠ language:** counts measure DCS's text selection. Low count means
  "rare in DCS", not "rare in Sanskrit".
- **Upstream tagging caveat (manifest ⚠):** DCS's Universal Dependencies
  export conflates aorist and perfect under `Tense=Past` — any tense-sensitive
  use of `grammar_all` inherits that conflation.
- `periods_sum` double-counts where DCS's aggregate slots (Epic, Classic)
  overlap dated slots; use `count_all` for totals and the vector for *shape*,
  not for re-summation.
- Frequencies are snapshot-frozen (DCS 2026); DCS grows continuously.
- `coverage_pct`/`core_rank` are filled only for the core-vocabulary band.

## Intended use / known misuse

**For:** frequency-ranked teaching and translation worklists, kosha's evidence
layer, diachronic profile plots per lemma, core-vocabulary selection.
**Misuse:** re-deriving frequency from raw DCS instead of joining this file;
treating ranks as stable across DCS releases; reading per-period cells as
independent observations for statistics without handling the aggregate-slot
overlap; tense-based claims built on the conflated `Tense=Past`.

## License

DCS-derived content: CC BY, attribution to Oliver Hellwig's Digital Corpus of
Sanskrit; the released compilation follows the public-tier terms in
[LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md)
(CC BY-SA 4.0 where CDSL-derived keys are joined in).

## Maintenance & sunset plan

Rebuilt by the kosha M9 join when a new DCS snapshot is ingested (via the
canonical VisualDCS CoNLL-U import — never a fresh parse); kosha re-releases at
the next `data-v*` cut with the snapshot date in the release notes. Sunset:
each snapshot's file remains downloadable in its release for reproducibility;
a new snapshot supersedes for live use without retiring the old asset.

## Deprecation status

`active`.

## Citation

Cite the release: *Gasuns Sanskrit Dictionary data release v0.1.0* (CC BY-SA
4.0), asset `lemma_frequency.tsv`,
[github.com/gasyoun/kosha/releases/tag/data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0),
with attribution to the Digital Corpus of Sanskrit (Hellwig). `CITATION.cff`
+ Zenodo DOI pending the next `/cut-release` freeze.

## Provenance of this statement

Authored 11-07-2026 by Fable 5 (`claude-fable-5`) under handoff
[H665](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H665-Fable_kosha_dataset-data-statements_11.07.26.md),
from the manifest row, the release assets, and column inspection of the live file.

_Dr. Mārcis Gasūns_
