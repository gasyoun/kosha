# Data statement — Zaliznyak-style grammar-token index over PWG (`zaliznyak-grammar-index`)

_Created: 11-07-2026 · Last updated: 11-07-2026_

Data statement for the `zaliznyak-grammar-index` dataset served by the kosha
data-hub. Manifest row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
Download: [`zaliznyak_grammar_index.tsv` in release data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0).

## Composition & counts

98,639 rows, one per PWG (Böhtlingk-Roth, Petersburg Dictionary) headword,
each assigned one of 335 compact paradigm tokens in the style of Zaliznyak's
grammatical dictionary of Russian (a closed token inventory that fully
determines a word's inflection). TSV, UTF-8, 8 columns:

| Column | Content |
|---|---|
| `k1` | headword, normalized key1 (SLP1) |
| `hom` | homonym number where PWG splits entries |
| `lex` | lexical category / gender as recorded (e.g. `f.`) |
| `accented` | accented headword form where the source marks accent |
| `index_token` | the compact paradigm token (e.g. `f·1`) — the dataset's payload |
| `stem_class` | stem-class label (e.g. `a-stem`) |
| `compound_members` | member decomposition for compounds, where analyzed |
| `irregularities` | recorded deviations from the token's default paradigm |

## Source provenance

Built by the grammar-index pipeline in
[gasyoun/SanskritLexicography](https://github.com/gasyoun/SanskritLexicography)
(`RussianTranslation/src/headword_index.tsv`), part of the pwg_ru translation
effort: PWG headwords and grammar labels (CDSL digitization of
Böhtlingk-Roth) classified into paradigm tokens, with full paradigms generated
via the [vidyut](https://github.com/ambuda-org/vidyut) morphology engine
rather than transcribed from static grammar tables (the manifest note makes
this a rule: "paradigms generated via vidyut, never transcribe static tables").

## Curation rationale

Sanskrit dictionaries state gender and stem class but leave inflection to the
reader's grammar. Zaliznyak's insight — a small closed token set that *fully
specifies* inflection — had no Sanskrit application at dictionary scale. This
index attaches such a token to every PWG headword so that a dictionary UI (or
a learner's card deck) can render a complete paradigm from the token alone,
and so the token inventory itself (335 types) becomes a studiable object: how
much paradigm diversity does a full Sanskrit lexicon actually exercise?

## Language variety

Sanskrit (ISO 639-3 `san`) as lemmatized by PWG — the largest
European-compiled Sanskrit dictionary, Vedic through Classical, with Vedic
accentuation preserved in the `accented` column where the source marks it.
Keys in SLP1 (key1 normalization); homonymy follows PWG's entry splitting.

## Annotator / process information

Programmatic classification from PWG grammar labels + stem shape, with
paradigm generation delegated to vidyut (deterministic, MIT-licensed engine
from the Ambuda project). No per-row human annotation; ambiguous headwords
carry their unresolved markers in `irregularities` rather than a silent guess.
Produced within the pwg_ru pipeline (see
[PIPELINE_HISTORY.md](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/PIPELINE_HISTORY.md)
for the effort's provenance trail).

## Known biases & limitations

- Token assignment is only as good as PWG's grammar labels; entries PWG left
  unlabeled or labeled inconsistently inherit that uncertainty.
- The 335-token inventory is calibrated to PWG's lexicon; rare paradigm types
  attested only outside PWG have no token yet.
- Verbal lemmas are indexed by their dictionary form; the token system is
  strongest for nominal/adjectival paradigms (the Zaliznyak analogy is
  nominal-first).
- `compound_members` is filled only where the pipeline analyzed the compound —
  emptiness is "unanalyzed", not "not a compound".

## Intended use / known misuse

**For:** paradigm rendering in dictionary UIs (kosha P4 grammar tokens),
pwg_ru's nominal layer, gramdict mapping, quantitative morphology (token-type
frequency distributions over a full lexicon). **Misuse:** reading tokens as
attested-in-corpus paradigms (they are *predicted* inflection — join DCS data
for attestation); transcribing generated paradigms back into static tables
(regenerate via vidyut instead); applying the token inventory to non-PWG
lexica without re-calibration.

## License

CC BY-SA 4.0 (derivative of the CDSL PWG digitization) per
[LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md).
Attribution: Cologne Digital Sanskrit Dictionaries and the kosha data release;
paradigm generation via vidyut (MIT, Ambuda project). Packaged as a FAIR data
asset (manifest note).

## Maintenance & sunset plan

Maintained by the RussianTranslation grammar-index pipeline as pwg_ru
progresses (token inventory may grow past 335 as edge paradigms are ruled);
kosha re-mirrors at each `data-v*` cut. Sunset: a future union-lexicon grammar
index (beyond PWG) would supersede this row; until then it is the canonical
grammar-token layer.

## Deprecation status

`active`.

## Citation

Cite the release: *Gasuns Sanskrit Dictionary data release v0.1.0* (CC BY-SA
4.0), asset `zaliznyak_grammar_index.tsv`,
[github.com/gasyoun/kosha/releases/tag/data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0),
with attribution to the Cologne Digital Sanskrit Dictionaries and vidyut.
`CITATION.cff` + Zenodo DOI pending the next `/cut-release` freeze.

## Provenance of this statement

Authored 11-07-2026 by Fable 5 (`claude-fable-5`) under handoff
[H665](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H665-Fable_kosha_dataset-data-statements_11.07.26.md),
from the manifest row, the release assets, and column inspection of the live file.

_Dr. Mārcis Gasūns_
