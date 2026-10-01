# A56 — A Zaliznyak-Style Grammar-Token Index for 98,639 Sanskrit Headwords (JOHD data paper, submission draft)

_Created: 11-07-2026 · Last updated: 06-09-2026_

Mārcis Gasūns, independent scholar ([ORCID 0000-0003-4513-884X](https://orcid.org/0000-0003-4513-884X)), gasyoun@ya.ru

**Target venue:** Journal of Open Humanities Data (JOHD), data-paper track.
**Dataset:** [`zaliznyak-grammar-index`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/zaliznyak-grammar-index.meta.md)
(98,639 rows, 335 paradigm tokens), release
[data-v0.4.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.4.0),
DOI [10.5281/zenodo.22102090](https://doi.org/10.5281/zenodo.22102090).
**Readiness:** 4/5 (submission draft; token-frequency distribution — the
paper's core result — computed and tabled from the frozen release asset
02-08-2026; DOI minted 25-08-2026; paradigm-sample validation and final human
pass pending).

## Abstract

Zaliznyak's *Grammatical Dictionary of Russian* (1977) demonstrated that a
small closed inventory of paradigm tokens can fully specify the inflection of
every word in a large lexicon. I apply this design to Sanskrit for the first
time at dictionary scale, to the large Petersburg Dictionary (PWG,
Böhtlingk–Roth), the largest European-compiled Sanskrit lexicon. Of PWG's
≈106,000 headwords, ≈94,000 (≈89%) are assigned one of 335 compact paradigm
tokens, from which the open-source vidyut morphology engine generates a
complete paradigm deterministically; no inflection tables are transcribed.
Cross-reference entries and a residue of verbal and rare nominal lemmas are
not yet tokenized. The released TSV (98,639 rows) records
headword, homonym number, lexical category, accentuation, paradigm token,
stem class, compound decomposition, and machine-readable paradigm feature
flags. The token inventory's frequency structure is itself a finding: six
tokens cover half the lexicon, 26 cover 80%, and 154 cover 99%, while 48
classes are singletons (classifier-dependent counts; see §3). A full Sanskrit
lexicon exercises two orders of magnitude fewer paradigm types than its
headword count, with a long thin irregular tail. The dataset is released
under CC BY-SA 4.0.

## Keywords

Sanskrit; morphology; inflection; grammatical dictionary; Zaliznyak;
paradigm generation; Petersburg Dictionary

## 1. Overview

### Repository location

GitHub release asset `zaliznyak_grammar_index.tsv`,
[github.com/gasyoun/kosha/releases/tag/data-v0.4.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.4.0);
machine-readable manifest row in
[datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json);
full data statement at
[docs/data-statements/zaliznyak-grammar-index.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/zaliznyak-grammar-index.meta.md).
**Zenodo DOI: [10.5281/zenodo.22102090](https://doi.org/10.5281/zenodo.22102090)**
(minted 25-08-2026 for [data-v0.4.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.4.0),
a re-cut of the identical `data-v0.1.0` content — `data-v0.1.0` itself
predates the GitHub–Zenodo webhook, wired 14-08-2026, so it was never
auto-archived); citation metadata in
[CITATION.cff](https://github.com/gasyoun/kosha/blob/main/CITATION.cff)).

### Context

Sanskrit dictionaries state a headword's gender and stem class but delegate
inflection to reference grammars — usable by trained readers but opaque to
software and learners. Russian lexicography solved the analogous problem in
1977: Zaliznyak's dictionary attaches to every one of roughly 100,000 words a
compact index symbol from a closed inventory that fully determines its
inflection. No Sanskrit dictionary has carried such a layer. This dataset
retrofits one onto the Petersburg Dictionary (PWG), produced within the
PWG→Russian translation programme (provenance trail:
[PIPELINE_HISTORY.md](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/PIPELINE_HISTORY.md)).

The design decision with the widest consequence is that paradigms are
*generated* by [vidyut](https://github.com/ambuda-org/vidyut) (Ambuda
project, MIT license) from the token, never transcribed from static grammar
tables; the token layer stays compact, and the generation stays auditable
and re-runnable. The token, not the table, is the datum.

## 2. Method

### Steps

(1) PWG headwords with their grammar labels were taken from the CDSL
digitization on the normalized key1 layer (SLP1), preserving PWG homonym
numbering and accent notation. (2) Each headword was classified
programmatically into a paradigm token from PWG's own labels (gender, stem
shape, lexical category); the token grammar is
`<gender>·<section>[+N]`, where the `+N` suffix records compound arity
without changing the declension pattern. Paradigm-relevant features that cut
across tokens — compound membership, three-gender adjective behaviour,
ā-stem feminine formation, common m/n gender — are carried as machine-readable
flags with grammar-paragraph anchors in a dedicated column, rather than
multiplying the token inventory. (3) Token→paradigm realization was validated
by generating full paradigms via vidyut for the token classes and checking
the generated forms.

### Quality control

Classification is deterministic and reproducible from PWG labels. I grew the
closed token inventory only when an attested headword fit no existing
token; unresolved or deviant entries carry explicit markers rather than a
silent default. I re-verified all headline counts in this paper (98,639
rows; 335 distinct tokens, of which 3 indeclinable classes covering 2,003
headwords; per-token member counts; column fill rates) directly against the
frozen `data-v0.1.0` release asset on 02-08-2026. The inventory is versioned:
the live pipeline's inventory has since grown past 335 as edge paradigms are
ruled, and each `data-v*` cut freezes one auditable state.

### Limitations

Token assignment is only as good as PWG's grammar labels; entries PWG left
unlabeled or labeled inconsistently inherit that uncertainty. The inventory
is calibrated to PWG's lexicon — rare paradigm types attested only outside
PWG have no token yet. The system is nominal-first: verbal lemmas carry a
token only where their dictionary form received one, and the Zaliznyak
analogy is strongest for
nominal/adjectival paradigms. Tokens predict inflection; they do not attest
it in a corpus (corpus attestation is a separate join against the Digital
Corpus of Sanskrit). A systematic human-validated error rate over a random
paradigm sample is still pending (see backlog); until it is published, the
generation layer should be treated as engine-validated, not
philologist-validated.

## 3. Dataset description

- **Object name:** `zaliznyak_grammar_index.tsv`
- **Format names and versions:** TSV (tab-separated values), UTF-8; 8 columns
  (`k1`, `hom`, `lex`, `accented`, `index_token`, `stem_class`,
  `compound_members`, `irregularities`); 98,639 data rows; 6,124,345 bytes.
  Column fill (frozen asset): `accented` carries the headword form on every
  row, with accent notation where PWG marks it; `irregularities` (the
  feature-flag column) is non-empty on 68,429 rows (69.4%);
  `compound_members` on 46,648 rows (47.3%); `hom` on 4,426 rows.
- **Creation dates:** built 2026 within the PWG→Russian pipeline; first
  public release 06-07-2026 (data-v0.1.0).
- **Dataset creators:** Mārcis Gasūns (design, compilation); Cologne Digital
  Sanskrit Dictionaries (PWG digitization); vidyut / Ambuda project (paradigm
  engine).
- **Language:** Sanskrit (ISO 639-3 `san`), romanized (SLP1, key1 layer);
  metadata and documentation in English.
- **License:** CC BY-SA 4.0 (ShareAlike inherited from the CDSL PWG
  digitization; see
  [LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md)).
  The vidyut paradigm engine is a separate work under MIT.
- **Repository name:** GitHub (kosha data-hub, release
  [data-v0.4.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.4.0));
  Zenodo DOI [10.5281/zenodo.22102090](https://doi.org/10.5281/zenodo.22102090)
  (minted 25-08-2026).
- **Publication date:** 06-07-2026.

### The token-frequency distribution

How much paradigm diversity does a full Sanskrit lexicon exercise?
Computed over the frozen release asset (02-08-2026):

| lexicon coverage | tokens required |
|--:|--:|
| 50% | 6 |
| 80% | 26 |
| 90% | 52 |
| 95% | 82 |
| 99% | 154 |
| 100% | 335 |

The head is extremely heavy: the six largest classes — masculine a-stems
(`m·1+2` 12,681; `m·1` 11,496), three-gender a-stem adjectives (`mfn·1`
8,346; `mfn·1+2` 6,736), and neuter a-stems (`n·1+2` 6,116; `n·1` 5,916) —
alone cover half of PWG. The tail is long and thin: 48 tokens have exactly
one member and 121 have five or fewer — classifier-dependent counts (the
software classifier's error rate on this thin stratum is unmeasured, and the
live inventory has already drifted to 53/129); a manual check of the 48
singletons against the printed PWG is owed before these figures are read as
a finding. Three indeclinable classes cover
2,003 headwords; the remaining 332 declension classes partition 96,636. This
distribution is directly comparable with Zaliznyak-style inventories for
Russian and other languages. That makes it a rare cross-linguistic object:
the paradigm entropy of a whole lexicon under a closed classification.

## 4. Reuse potential

Immediate consumers exist in the origin ecosystem: kosha's grammar-token
layer renders paradigms in the dictionary UI from the token alone; the
PWG→Russian nominal translation layer uses tokens to control
paradigm-sensitive wording; a public drill set
([`zaliznyak-drills`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/zaliznyak-drills.meta.md),
3,434 items) is generated from the class index with no additional
lexicographic work. That is evidence that the token layer, once present,
spawns derived educational assets nearly for free.

External reuse runs in four directions. (a) In learner tooling, card decks
and readers can render full inflection tables for any of 98k words from an
8-column TSV plus an MIT-licensed engine. (b) In quantitative morphology,
the published token-frequency distribution (which paradigm types carry the
lexicon, how heavy the irregular tail is) is comparable across languages
wherever Zaliznyak-style inventories exist. (c) In NLP, the index is a
lexicon-scale morphological prior for taggers and lemmatizers,
complementary to corpus-trained models. (d) As lexicographic method, it is
a worked template for retrofitting grammatical-dictionary layers onto other
digitized dictionaries (Monier-Williams being the obvious next candidate:
its headword inventory is Petersburg-derived, so token transfer is a join,
not a re-classification).
ShareAlike licensing permits commercial reuse with attribution.

## Acknowledgements

The dataset stands on the Cologne Digital Sanskrit Dictionaries digitization
of the Petersburg Dictionary (University of Cologne; Thomas Malten, Jim
Funderburk and collaborators) and on the vidyut morphology engine of the
Ambuda project.

## Funding statement

No external funding. The dataset was produced within the samskrtam.ru
Sanskrit-education programme.

## Competing interests

The author declares no competing interests.

## References

- Böhtlingk, O., and R. Roth. *Sanskrit-Wörterbuch.* 7 vols. St. Petersburg:
  Kaiserliche Akademie der Wissenschaften, 1855–1875.
- Cologne Digital Sanskrit Dictionaries (CDSL), Cologne Sanskrit Lexicon
  project, University of Cologne.
  [www.sanskrit-lexicon.uni-koeln.de](https://www.sanskrit-lexicon.uni-koeln.de/).
- Zaliznyak, A. A. *Грамматический словарь русского языка: Словоизменение*
  [Grammatical Dictionary of the Russian Language: Inflection]. Moscow:
  Russkij jazyk, 1977.
- vidyut — Sanskrit morphology toolkit, Ambuda project (MIT).
  [github.com/ambuda-org/vidyut](https://github.com/ambuda-org/vidyut).
- Gasūns, M. *Gasuns Sanskrit Dictionary data release v0.4.0.* Zenodo, 25-08-2026.
  [doi.org/10.5281/zenodo.22102090](https://doi.org/10.5281/zenodo.22102090).
- Gasūns, M. *Gasuns Sanskrit Dictionary data release v0.5.0.* Zenodo, 26-08-2026.
  [doi.org/10.5281/zenodo.22105641](https://doi.org/10.5281/zenodo.22105641).

## Backlog to 5/5

1. Validation sample: human check of N generated paradigms against reference
   grammars; report the error rate in §2 (the one validation gap named in
   Limitations).
2. ~~Mint a Zenodo DOI for this dataset~~ — done 25-08-2026:
   [10.5281/zenodo.22102090](https://doi.org/10.5281/zenodo.22102090)
   (`data-v0.4.0`).
3. Exact bibliographic verification of the Zaliznyak 1977 inventory-size
   comparison if a numeric side-by-side is added (current text deliberately
   avoids asserting his token count).
4. Transfer into JOHD's submission template at submission time.

## Provenance

Drafted 11-07-2026 by Fable 5 (`claude-fable-5`) under handoff
[H665](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H665-Fable_kosha_dataset-data-statements_11.07.26.md)
from the dataset's data statement. Upgraded to a submission draft 02-08-2026
by Fable 5 (`claude-fable-5`) under handoff
[H1872](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1872-Fable_kosha_a55-a56-johd-data-papers-submission-draft_29.07.26.md):
token-frequency distribution computed from the frozen release asset (335
tokens confirmed; the live inventory has since grown to 342, which the
versioning note in §2 now covers), column-fill census added, feature-flag
column semantics corrected from value inspection. Registered as A56 in
[ARTICLES.md](https://github.com/gasyoun/Uprava/blob/main/ARTICLES.md).
Author-voice pass 06-09-2026 by Fable 5.1 (`claude-fable-5-1`) under handoff [H3857](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3857-Fable_Uprava_all-articles-author-voice-pass-workflow_01.09.26.md) — voice, register and framing only, no number, claim or citation altered ([SIGNOFF_A56_author_pass.md](https://github.com/gasyoun/kosha/blob/main/papers/SIGNOFF_A56_author_pass.md)).

_Dr. Mārcis Gasūns_
