# Data statement — DCS lemma ↔ CDSL headword crosswalk (`dcs-cdsl-xref`)

_Created: 11-07-2026 · Last updated: 11-07-2026_

Data statement for the `dcs-cdsl-xref` dataset served by the kosha data-hub.
Manifest row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
Download: [`dcs_cdsl_xref.tsv` in release data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0).

## Composition & counts

15,902 rows, one per Digital Corpus of Sanskrit (DCS) lemma considered for
linking; 81.4% carry a resolved CDSL link. TSV, UTF-8, 7 columns:

| Column | Content |
|---|---|
| `dcs_id` | DCS lemma id (stable upstream key) |
| `dcs_lemma_iast` | DCS lemma form, IAST |
| `slp1` | lemma in SLP1 |
| `normkey` | normalized join key used by the linking pipeline |
| `in_cdsl` | 1 if the lemma resolves to a CDSL headword, else 0 |
| `token_count` | DCS corpus token frequency of the lemma |
| `grammar` | DCS part-of-speech / grammar tag |

## Source provenance

Built by the `dcs_xref` pipeline in
[sanskrit-lexicon/csl-apidev](https://github.com/sanskrit-lexicon/csl-apidev)
(`simple-search/dcs_xref/dcs_cdsl_xref.tsv`), joining lemma exports of the
[Digital Corpus of Sanskrit](https://github.com/OliverHellwig/sanskrit)
(© Oliver Hellwig, CC BY) against Cologne Digital Sanskrit Dictionaries
headword lists. Mirrored into the kosha public tier at release cut.

## Curation rationale

DCS (a lemmatized corpus) and CDSL (a dictionary federation) are the two
central Sanskrit digital resources, and they key their lemmas differently.
Every project that wants corpus attestation next to dictionary senses has to
join them; historically each project re-derived the join. This linkset is the
one canonical DCS↔CDSL bridge — a reusable linked-open-data asset registered so
the join is never re-derived (the manifest note is explicit: "never re-derive
DCS↔CDSL joins").

## Language variety

Sanskrit (ISO 639-3 `san`) across the full DCS diachronic span (Vedic to
early-modern). Romanized (IAST + SLP1). Lemma normalization follows DCS
lemmatization decisions (e.g. homonym splitting, compound segmentation
policy), which do not always coincide with CDSL headword conventions — the
`normkey` column is the declared reconciliation layer.

## Annotator / process information

Programmatic key-normalization join (csl-apidev `dcs_xref` pipeline); no
LLM-generated content, no manual per-row annotation. Link decisions are
deterministic given the two upstream keyings; the 18.6% unlinked residue is
the honest remainder, not a sampled subset.

## Known biases & limitations

- 18.6% of DCS lemmas have `in_cdsl = 0`: proper names, corpus-specific
  segmentations, and late/technical vocabulary underrepresented in the
  dictionaries. Coverage failure is therefore *not random* — it skews against
  onomastics and late texts.
- The crosswalk is lemma-level, not sense-level: a link asserts "same lexeme",
  never "same sense inventory".
- `token_count` is frozen at build time from a DCS snapshot; DCS grows, so
  counts drift from the live corpus until the next rebuild.
- One-to-many cases (one DCS lemma, several CDSL homonym headwords) are
  resolved by the pipeline's normkey policy; consumers doing homonym-sensitive
  work should re-check those rows against the dictionaries.

## Intended use / known misuse

**For:** attaching corpus frequency/attestation to dictionary entries
(kosha's evidence layer, csl-atlas, VisualDCS), coverage studies ("which DCS
vocabulary is missing from the dictionaries"), LOD publication. **Misuse:**
reading `in_cdsl = 0` as "word absent from Sanskrit lexicography" (it may sit
under a different headword shape); treating the link as sense-level; deriving
frequency claims from `token_count` without naming the DCS snapshot date.

## License

CC BY-SA 4.0 for the crosswalk as released, per
[LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md);
the DCS-derived columns carry CC BY attribution to Oliver Hellwig's Digital
Corpus of Sanskrit; CDSL-derived keys attribute the Cologne Digital Sanskrit
Dictionaries.

## Maintenance & sunset plan

Rebuilt by the csl-apidev pipeline when either upstream moves materially (a
DCS release or a CDSL headword refresh); kosha re-mirrors at each `data-v*`
cut. Sunset: superseded if a richer sense-level DCS↔CDSL alignment ever ships —
in that case this row flips to `superseded by [X]` and the asset stays
downloadable for reproducibility.

## Deprecation status

`active`.

## Citation

Cite the release: *Gasuns Sanskrit Dictionary data release v0.1.0* (CC BY-SA
4.0), asset `dcs_cdsl_xref.tsv`,
[github.com/gasyoun/kosha/releases/tag/data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0),
with attribution to the Digital Corpus of Sanskrit (Hellwig) and the Cologne
Digital Sanskrit Dictionaries. `CITATION.cff` + Zenodo DOI pending the next
`/cut-release` freeze.

## Provenance of this statement

Authored 11-07-2026 by Fable 5 (`claude-fable-5`) under handoff
[H665](https://github.com/gasyoun/Uprava/blob/main/handoffs/H665-Fable_kosha_dataset-data-statements_11.07.26.md),
from the manifest row, the release assets, and column inspection of the live file.

_Dr. Mārcis Gasūns_
