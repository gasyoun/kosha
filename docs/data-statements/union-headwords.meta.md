# Data statement — Cross-dictionary union headword index (`union-headwords`)

_Created: 11-07-2026 · Last updated: 11-07-2026_

Data statement for the `union-headwords` dataset served by the kosha data-hub —
the headword master of the ecosystem. Manifest row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
Download: [`union_headwords.tsv` in release data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0).

## Composition & counts

323,425 rows, one per distinct SLP1 headword attested in at least one of 15
digitized Sanskrit dictionaries (codes: AP, BHS, BUR, CAE, CCS, GRA, INM, MD,
MW, PWG, PWK, SCH, SKD, VCP, VEI — Apte, Edgerton BHS, Burnouf, Cappeller,
Grassmann, Macdonell, Monier-Williams, the two Petersburg dictionaries,
Schmidt, Śabdakalpadruma, Vācaspatyam, and personal-/Vedic-name indices among
them). TSV, UTF-8, 6 columns:

| Column | Content |
|---|---|
| `slp1` | headword, SLP1 (the join key) |
| `iast` | headword, IAST |
| `n_dicts` | number of dictionaries attesting the headword |
| `dicts` | space-separated dictionary codes (per-dict provenance flags) |
| `gender` | union of recorded genders (e.g. `fmn`) |
| `fem_fold` | feminine-folding note where a feminine was merged to its stem |

## Source provenance

Built by the HeadwordLists union build in
[gasyoun/SanskritLexicography](https://github.com/gasyoun/SanskritLexicography)
(`HeadwordLists/union/union_headwords.tsv`) over the per-dictionary headword
exports of the Cologne Digital Sanskrit Dictionaries plus sibling digitized
sources. Each contributing list is itself a `{DICT}-unique-key1` export
(normalized computational keys — see the key1/key2 distinction in
[SanskritLexicography/CLAUDE.md](https://github.com/gasyoun/SanskritLexicography/blob/master/CLAUDE.md)).

## Curation rationale

Every cross-dictionary task — spell-checking, crosswalks, coverage studies,
translation worklists — needs one answer to "what is the set of Sanskrit
headwords, and who attests each?" Before this file, each pipeline unioned its
own subset. This is the single registered union, on the normalized key1 layer
so that orthographic variance between dictionaries does not fragment the index.

## Language variety

Sanskrit (ISO 639-3 `san`), the union of lexicographic traditions from Vedic
concordances (GRA, VEI) through Classical dictionaries (MW, PWG, AP) to
Buddhist Hybrid Sanskrit (BHS) and the Sanskrit-medium encyclopedic
tradition (SKD, VCP). Romanized: SLP1 + IAST, key1 normalization (accent marks
and print-layer hyphens stripped — use each dictionary's key2 lists for
print-faithful forms).

## Annotator / process information

Deterministic set-union over dictionary headword exports; no LLM-generated
content, no per-row human annotation. The `gender` and `fem_fold` columns are
carried/merged from the source exports programmatically.

## Known biases & limitations

- The union inherits every member's digitization state: a headword missing
  from a dictionary's export (OCR gap, digitization backlog) is missing from
  that dictionary's flags here.
- key1 normalization deliberately merges forms differing only in accent or
  print hyphens; homonyms sharing a spelling collapse to one row. This is
  correct for joins and wrong for philology — use key2 lists for the latter.
- Membership is binary per dictionary: no entry ids, page refs, or sense
  counts (join dictionary-specific tables for those).
- Dictionary mix skews toward European-compiled lexica; SKD/VCP are the only
  Sanskrit-medium members, so `n_dicts` is not a neutral "importance" score
  across traditions.

## Intended use / known misuse

**For:** the spine of crosswalks and coverage studies, spell-check lexica
(`union=N` tags in SanskritSpellCheck), sampling frames for translation
pipelines (the PWG→EN pilot drew a 94,753-row subset), kosha's lemma table.
**Misuse:** treating `n_dicts` as frequency or importance (it measures
lexicographic attestation, not corpus usage — join
[`kosha-lemma-frequency`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/kosha-lemma-frequency.meta.md)
for that); using key1 forms as citable printed forms; assuming 323,425 ≈ "the
Sanskrit lexicon" (it is the union of *digitized* dictionaries as of the build).

## License

CC BY-SA 4.0 (derivative of CDSL headword lists), per
[LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md).
Attribution: Cologne Digital Sanskrit Dictionaries and the kosha data release.

## Maintenance & sunset plan

Rebuilt by the HeadwordLists union build when a member dictionary's export is
refreshed or a new dictionary is digitized; kosha re-mirrors at each `data-v*`
cut. The row count is part of the asset's identity (filename-count convention
in HeadwordLists) — a rebuild that changes the count is a new version, released
as such. Sunset: none foreseeable while CDSL digitization continues; the file
would only retire into a successor union with entry-id resolution.

## Deprecation status

`active`.

## Citation

Cite the release: *Gasuns Sanskrit Dictionary data release v0.1.0* (CC BY-SA
4.0), asset `union_headwords.tsv`,
[github.com/gasyoun/kosha/releases/tag/data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0),
with attribution to the Cologne Digital Sanskrit Dictionaries. `CITATION.cff`
+ Zenodo DOI pending the next `/cut-release` freeze.

## Provenance of this statement

Authored 11-07-2026 by Fable 5 (`claude-fable-5`) under handoff
[H665](https://github.com/gasyoun/Uprava/blob/main/handoffs/H665-Fable_kosha_dataset-data-statements_11.07.26.md),
from the manifest row, the release assets, column inspection of the live file,
and a distinct-code scan of the `dicts` column (15 codes verified 11-07-2026).

_Dr. Mārcis Gasūns_
