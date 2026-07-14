# A55 — A Union Headword Index of Fifteen Digitized Sanskrit Dictionaries (JOHD data paper, draft)

_Created: 11-07-2026 · Last updated: 11-07-2026_

**Target venue:** Journal of Open Humanities Data (JOHD), data-paper track.
**Dataset:** [`union-headwords`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/union-headwords.meta.md)
(323,425 rows), release
[data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0).
**Readiness:** 2/5 (structured draft from the data statement; numbers verified,
prose to be tightened for submission).

## Abstract (draft)

We present a union headword index of 323,425 distinct Sanskrit lexemes,
compiled from fifteen digitized dictionaries of the Cologne Digital Sanskrit
Dictionaries ecosystem — from the Vedic concordances of Grassmann to the
Sanskrit-medium encyclopedic tradition (Śabdakalpadruma, Vācaspatyam) and
Edgerton's Buddhist Hybrid Sanskrit dictionary. Each row records the headword
in two romanizations (SLP1, IAST), the set of attesting dictionaries,
attestation count, and merged gender data. The index is keyed on a normalized
computational form (key1) designed for machine joins across orthographically
divergent digitizations. It serves as the headword spine for crosswalks,
spell-checking lexica, translation worklists, and coverage studies across the
Sanskrit lexicographic ecosystem, and is released under CC BY-SA 4.0.

## Keywords

Sanskrit · lexicography · headword index · digital dictionaries · CDSL ·
union lexicon

## 1. Overview

**Repository location:** GitHub release asset `union_headwords.tsv`,
[github.com/gasyoun/kosha/releases/tag/data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0);
machine-readable manifest row in
[datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).

**Context.** Sanskrit lexicography is unusually federated: the Cologne Digital
Sanskrit Dictionaries project has digitized dozens of dictionaries compiled
between 1841 and the 20th century, each with its own headword normalization,
homonym policy, and orthographic conventions. No shared headword spine
existed; every cross-dictionary project (spell-checkers, alignment pipelines,
coverage studies) re-derived its own union from per-dictionary exports, with
divergent results. This dataset fixes one canonical union at the normalized
key layer. The fifteen members span four lexicographic traditions:
European-compiled bilingual dictionaries (MW, PWG, PWK, AP, CAE, MD, BUR,
CCS, SCH), Vedic special lexica (GRA, VEI), Buddhist Hybrid Sanskrit (BHS),
proper-name indices (INM), and Sanskrit-medium encyclopedias (SKD, VCP).

## 2. Method

**Steps.** (1) Per-dictionary headword exports (`{DICT}-unique-key1` lists)
were produced from CDSL digitizations, normalizing each dictionary's printed
forms to a computational key (key1: accent marks and print-layer hyphenation
stripped, SLP1 encoding). (2) The lists were set-unioned on key1; per-dict
membership flags, attestation counts, and gender fields were merged
programmatically. (3) Feminine forms foldable to their stem entry were merged
with an explicit `fem_fold` note rather than silently.

**Quality control.** Row count is embedded in the producing file's naming
convention (count = line count, checked at build); the union is
deterministic and reproducible from the member exports; distinct-code and
count invariants are re-verified at release cut (15 codes, 323,425 rows,
re-confirmed 11-07-2026).

**Limitations of method.** The union inherits each member's digitization
state; key1 merging collapses homonyms sharing a spelling; binary membership
carries no entry ids or sense counts. See the full
[data statement](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/union-headwords.meta.md)
for the bias discussion (European-compiled skew; `n_dicts` is lexicographic
attestation, not corpus frequency).

## 3. Dataset description

- **Object name:** `union_headwords.tsv`
- **Format:** TSV, UTF-8; 6 columns (`slp1`, `iast`, `n_dicts`, `dicts`,
  `gender`, `fem_fold`); 323,425 data rows; 12.4 MB.
- **Creation dates:** member exports and union build 2025–2026; first public
  release 06-07-2026 (data-v0.1.0).
- **Dataset creators:** Mārcis Gasūns (compilation); Cologne Digital Sanskrit
  Dictionaries (source digitizations: Funderburk, Malten et al., Univ. of
  Cologne).
- **Language:** Sanskrit (ISO 639-3 `san`), romanized (SLP1/IAST); metadata in
  English.
- **License:** CC BY-SA 4.0 (ShareAlike inherited from CDSL; see
  [LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md)).
- **Repository:** GitHub (kosha data-hub); Zenodo DOI pending the next release
  freeze.
- **Publication date:** 06-07-2026 (data-v0.1.0).

## 4. Reuse potential

The index is already the load-bearing spine of several independent consumers:
the kosha unified lookup database keys its lemma table on it; the
SanskritSpellCheck project uses `n_dicts` membership tags as evidence tiers;
the PWG→English translation pilot sampled its 94,753-headword worklist from
it; the DCS frequency sidecar joins corpus counts onto it. Beyond the origin
ecosystem: (a) coverage studies — which vocabulary strata are attested only in
Sanskrit-medium lexica, only in Vedic lexica, or in a single dictionary;
(b) NLP lexicon induction — a 323k-lemma candidate list with per-source
provenance for weighting; (c) history of lexicography — quantifying overlap
and divergence between the European and Indian dictionary traditions on a
shared key; (d) OCR/digitization QA — a new digitization's headword extraction
can be diffed against the union to find both its gaps and the union's.
ShareAlike licensing permits commercial reuse with attribution.

## Backlog to 5/5

1. Tighten prose to JOHD length norms; add 2–3 figures (per-dictionary overlap
   matrix, `n_dicts` distribution).
2. Freeze a Zenodo DOI via `/cut-release` (CITATION.cff pending).
3. Human pass on the dictionary-tradition characterization (§1) and the
   fem_fold description against the build script.
4. JOHD metadata table conformance check against current author guidelines.

## Provenance

Drafted 11-07-2026 by Fable 5 (`claude-fable-5`) under handoff
[H665](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H665-Fable_kosha_dataset-data-statements_11.07.26.md)
from the dataset's data statement. Registered as A55 in
[ARTICLES.md](https://github.com/gasyoun/Uprava/blob/main/ARTICLES.md).

_Dr. Mārcis Gasūns_
