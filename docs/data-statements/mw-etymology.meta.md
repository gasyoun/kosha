# Data statement — Headword→root derivation table (`mw-etymology`)

_Created: 11-07-2026 · Last updated: 11-07-2026_

Data statement for the `mw-etymology` dataset served by the kosha data-hub.
Manifest row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
Download: [`mw_etymology.tsv` in release data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0).

## Composition & counts

9,377 rows, one per headword→root derivation extracted from Monier-Williams
(1899) etymological notes. TSV, UTF-8, 18 columns — the widest schema in the
public tier:

| Column group | Columns | Content |
|---|---|---|
| identity | `L_id`, `headword`, `headword_slp1` | MW entry id + headword (IAST, SLP1) |
| root | `root`, `root_slp1`, `root_via`, `root_class`, `root_canonical` | the root derived from, how the attribution was made (`fr-root` etc.), class codes, canonical-form flag |
| morphology | `prefixes`, `affix`, `affix_slp1`, `group`, `anubandha`, `anubandha_steps`, `affix_source` | Pāṇinian affix analysis with anubandha (marker-letter) decomposition |
| record | `deriv_type`, `parse`, `context` | derivation type + the MW entry text span the attribution was read from |

The `context` column preserves the original dictionary prose (with markup), so
every derivation is auditable against its source sentence.

## Source provenance

Extracted from the CDSL digitization of MW 1899
([sanskrit-lexicon/csl-orig](https://github.com/sanskrit-lexicon/csl-orig),
`v02/mw/mw_etymology.tsv`), server-regenerated upstream by the Cologne project;
mirrored unmodified into the kosha public tier. Distinct from
[`mw-roots`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/mw-roots.meta.md):
that file inventories the roots themselves, this one maps derived headwords
*onto* roots.

## Curation rationale

Etymological attributions in MW are prose ("probably fr. √1. *aś*…"), unusable
for joins until parsed into structured rows. This table makes MW's derivational
claims machine-readable once, with Pāṇinian affix decomposition attached, so
that root-family grouping (e.g. all derivatives of √kṛ) is a join, not a
research task.

## Language variety

Sanskrit (ISO 639-3 `san`), Vedic through Classical as covered by MW.
Romanized (IAST + SLP1). The morphological framework is Pāṇinian (affix +
anubandha), applied to a dictionary whose own etymological practice is
19th-century comparative philology — two analytical traditions coexist in one
row, which is a feature to be aware of, not an error.

## Annotator / process information

Deterministic parse of MW entry markup by the Cologne upstream pipeline; the
`root_via` and `parse` columns record how each attribution was made. No
LLM-generated content. Hedged attributions in the source ("probably fr. …")
are carried through in `context` — the row does not upgrade MW's uncertainty
to certainty, but a consumer reading only the `root` column will lose the hedge.

## Known biases & limitations

- Coverage is partial by construction: 9,377 derivations against ~160k MW
  section entries — only headwords where MW states a derivation are present.
  Absence of a row ≠ underived word.
- MW's etymologies are 1899 scholarship; some are rejected today. The table
  encodes *MW's claims*, not modern etymological consensus.
- The hedge-loss problem above: filter on `context` when certainty matters.
- Affix/anubandha columns are sparsely filled where MW gave no analyzable
  affix statement.

## Intended use / known misuse

**For:** root-family grouping, derivational-morphology studies over a large
lexicon, joining MW headwords to the root layer (with
[`mw-roots`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/mw-roots.meta.md)),
teaching material on Sanskrit word-formation. **Misuse:** citing a row as a
modern etymological judgment without checking `context`; treating coverage as
exhaustive; using it as a Pāṇinian derivation gold standard (the Pāṇinian
columns annotate MW's claims, they do not independently derive).

## License

CC BY-SA 4.0, inherited from csl-orig per
[LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md).
Attribution: Cologne Digital Sanskrit Dictionaries (Univ. of Cologne) and the
kosha data release.

## Maintenance & sunset plan

Upstream-maintained (Cologne server regeneration on csl-orig corrections);
kosha re-mirrors at each `data-v*` release cut. Sunset condition identical to
`mw-roots`: an upstream release channel would turn this into a manifest
redirect row.

## Deprecation status

`active`.

## Citation

Cite the release: *Gasuns Sanskrit Dictionary data release v0.1.0* (CC BY-SA
4.0), asset `mw_etymology.tsv`,
[github.com/gasyoun/kosha/releases/tag/data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0),
with attribution to the Cologne Digital Sanskrit Dictionaries. `CITATION.cff`
+ Zenodo DOI pending the next `/cut-release` freeze.

## Provenance of this statement

Authored 11-07-2026 by Fable 5 (`claude-fable-5`) under handoff
[H665](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H665-Fable_kosha_dataset-data-statements_11.07.26.md),
from the manifest row, the release assets, and column inspection of the live file.

_Dr. Mārcis Gasūns_
