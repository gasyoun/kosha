# A56 — A Zaliznyak-Style Grammar-Token Index for 98,639 Sanskrit Headwords (JOHD data paper, draft)

_Created: 11-07-2026 · Last updated: 11-07-2026_

**Target venue:** Journal of Open Humanities Data (JOHD), data-paper track.
**Dataset:** [`zaliznyak-grammar-index`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/zaliznyak-grammar-index.meta.md)
(98,639 rows, 335 paradigm tokens), release
[data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0).
**Readiness:** 2/5 (structured draft from the data statement; numbers verified,
prose to be tightened for submission).

## Abstract (draft)

Zaliznyak's *Grammatical Dictionary of Russian* (1977) demonstrated that a
small closed inventory of paradigm tokens can fully specify the inflection of
every word in a large lexicon. We apply this design to Sanskrit for the first
time at dictionary scale: every headword of the Petersburg Dictionary
(Böhtlingk-Roth, the largest European-compiled Sanskrit lexicon) is assigned
one of 335 compact paradigm tokens, from which a complete paradigm is
generated deterministically by the open-source vidyut morphology engine —
no inflection tables are transcribed. The released TSV (98,639 rows) records
headword, homonym number, lexical category, Vedic accentuation where marked,
paradigm token, stem class, compound decomposition, and recorded
irregularities. The token inventory itself is a finding: a full Sanskrit
lexicon exercises two orders of magnitude fewer paradigm types than its
headword count. Released under CC BY-SA 4.0.

## Keywords

Sanskrit · morphology · inflection · grammatical dictionary · Zaliznyak ·
paradigm generation · PWG

## 1. Overview

**Repository location:** GitHub release asset `zaliznyak_grammar_index.tsv`,
[github.com/gasyoun/kosha/releases/tag/data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0);
manifest row in
[datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).

**Context.** Sanskrit dictionaries state a headword's gender and stem class
but delegate inflection to reference grammars — usable by trained readers,
opaque to software and learners. Russian lexicography solved the analogous
problem in 1977: Zaliznyak's dictionary attaches to every word a compact
index token from a closed inventory that fully determines its inflection.
No Sanskrit dictionary has carried such a layer. This dataset retrofits one
onto the Petersburg Dictionary (PWG), produced within the pwg_ru
translation programme (provenance trail:
[PIPELINE_HISTORY.md](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/PIPELINE_HISTORY.md)).
The design decision with the widest consequence: paradigms are *generated* by
[vidyut](https://github.com/ambuda-org/vidyut) (Ambuda project, MIT) from the
token, never transcribed from static grammar tables — the token layer stays
compact and the generation stays auditable and re-runnable.

## 2. Method

**Steps.** (1) PWG headwords with their grammar labels were taken from the
CDSL digitization on the normalized key1 layer, preserving PWG homonym
numbering and Vedic accentuation. (2) Each headword was classified
programmatically into a paradigm token from PWG's own labels (gender, stem
shape, lexical category); ambiguous or deviant entries carry explicit markers
in `irregularities` rather than a silent default. (3) Token→paradigm
realization was validated by generating full paradigms via vidyut and checking
generated forms for the token classes.

**Quality control.** Classification is deterministic and reproducible from
PWG labels; the closed token inventory (335 types) was grown only when an
attested headword fit no existing token; unresolved cases are marked, not
guessed.

**Limitations of method.** Token assignment inherits PWG's labeling
inconsistencies; the inventory is calibrated to PWG's lexicon; the system is
nominal-first (the Zaliznyak analogy is strongest for nominal/adjectival
paradigms); tokens predict inflection, they do not attest it in a corpus. Full
bias discussion in the
[data statement](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/zaliznyak-grammar-index.meta.md).

## 3. Dataset description

- **Object name:** `zaliznyak_grammar_index.tsv`
- **Format:** TSV, UTF-8; 8 columns (`k1`, `hom`, `lex`, `accented`,
  `index_token`, `stem_class`, `compound_members`, `irregularities`);
  98,639 data rows; 6.1 MB.
- **Creation dates:** built 2026 within the pwg_ru pipeline; first public
  release 06-07-2026 (data-v0.1.0).
- **Dataset creators:** Mārcis Gasūns (design, compilation); Cologne Digital
  Sanskrit Dictionaries (PWG digitization); vidyut/Ambuda (paradigm engine).
- **Language:** Sanskrit (ISO 639-3 `san`), romanized (SLP1, key1 layer);
  metadata in English.
- **License:** CC BY-SA 4.0 (ShareAlike inherited from the CDSL PWG
  digitization; see
  [LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md));
  vidyut engine MIT.
- **Repository:** GitHub (kosha data-hub); Zenodo DOI pending the next release
  freeze.
- **Publication date:** 06-07-2026 (data-v0.1.0).

## 4. Reuse potential

Immediate consumers exist in the origin ecosystem: kosha's P4 grammar-token
layer renders paradigms in the dictionary UI from the token alone; the pwg_ru
nominal translation layer uses tokens to control paradigm-sensitive wording;
a gramdict mapping aligns the tokens with other grammatical-dictionary
schemes. External reuse: (a) **learner tooling** — card decks and readers can
render full inflection tables for any of 98k words from an 8-column TSV plus
an MIT-licensed engine; (b) **quantitative morphology** — the token frequency
distribution over a complete lexicon (which paradigm types carry the lexicon,
how heavy the irregular tail is) is directly computable, and comparable with
Zaliznyak-style inventories for Russian and other languages — a rare
cross-linguistic object; (c) **NLP** — a lexicon-scale morphological prior
for taggers/lemmatizers, complementary to corpus-trained models; (d)
**lexicographic method** — a worked template for retrofitting
grammatical-dictionary layers onto other digitized dictionaries (MW being the
obvious next candidate). ShareAlike licensing permits commercial reuse with
attribution.

## Backlog to 5/5

1. Compute and table the token-frequency distribution (the §4b analysis) —
   likely the paper's core figure.
2. Validation sample: human check of N generated paradigms against reference
   grammars; report an error rate.
3. Freeze a Zenodo DOI via `/cut-release` (CITATION.cff pending).
4. Tighten the Zaliznyak comparison with exact citation of the 1977
   inventory size and design.
5. JOHD metadata table conformance check against current author guidelines.

## Provenance

Drafted 11-07-2026 by Fable 5 (`claude-fable-5`) under handoff
[H665](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H665-Fable_kosha_dataset-data-statements_11.07.26.md)
from the dataset's data statement. Registered as A56 in
[ARTICLES.md](https://github.com/gasyoun/Uprava/blob/main/ARTICLES.md).

_Dr. Mārcis Gasūns_
