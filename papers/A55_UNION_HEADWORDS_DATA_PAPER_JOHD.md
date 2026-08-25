# A55 — A Union Headword Index of Fifteen Digitized Sanskrit Dictionaries (JOHD data paper, submission draft)

_Created: 11-07-2026 · Last updated: 25-08-2026_

**Target venue:** Journal of Open Humanities Data (JOHD), data-paper track.
**Dataset:** [`union-headwords`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/union-headwords.meta.md)
(323,425 rows), release
[data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0).
**Readiness:** 4/5 (submission draft; all numbers re-verified against the frozen
release asset 02-08-2026; DOI mint and final human pass pending).

## Abstract

We present a union headword index of 323,425 distinct Sanskrit lexemes,
compiled from fifteen digitized dictionaries of the Cologne Digital Sanskrit
Dictionaries (CDSL) ecosystem — from Grassmann's Rig-Veda lexicon and the
Vedic name index through the great European bilingual dictionaries
(Böhtlingk–Roth, Monier-Williams, Apte) to Edgerton's Buddhist Hybrid
Sanskrit dictionary and the Sanskrit-medium encyclopedic tradition
(Śabdakalpadruma, Vācaspatyam). Each row records the headword in two
romanizations (SLP1, IAST), the set of attesting dictionaries, an attestation
count, and merged gender data, keyed on a normalized computational form
designed for machine joins across orthographically divergent digitizations.
44.1% of the union is attested in exactly one dictionary; only eleven
headwords appear in all fifteen. The index is the headword spine for
crosswalks, spell-checking lexica, translation worklists, and coverage
studies across the Sanskrit lexicographic ecosystem, and ships with a
pairwise overlap matrix and a witness-independence analysis that corrects
the naive reading of attestation counts as corroboration. Released under
CC BY-SA 4.0.

## Keywords

Sanskrit; lexicography; headword index; digital dictionaries; union lexicon;
Cologne Digital Sanskrit Dictionaries

## 1. Overview

### Repository location

GitHub release asset `union_headwords.tsv`,
[github.com/gasyoun/kosha/releases/tag/data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0);
machine-readable manifest row in
[datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json);
full data statement at
[docs/data-statements/union-headwords.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/union-headwords.meta.md).
Zenodo DOI pending — corrected 25-08-2026: the GitHub–Zenodo integration is
now live (webhook wired 14-08-2026; verified against the Zenodo API — kosha's
own concept DOI is
[10.5281/zenodo.21965599](https://doi.org/10.5281/zenodo.21965599)), but it
only archives releases published **after** that date, and `data-v0.1.0`
(06-07-2026) predates it — no automatic mint occurred, and no separate
deposit has been made for this dataset. Minting still requires either a new
`data-v*` release (auto-archived going forward) or a manual retroactive
Zenodo deposit of `data-v0.1.0`; citation metadata in
[CITATION.cff](https://github.com/gasyoun/kosha/blob/main/CITATION.cff)).

### Context

Sanskrit lexicography is unusually federated: the Cologne Digital Sanskrit
Dictionaries project has digitized dozens of dictionaries compiled between
1841 and the twentieth century, each with its own headword normalization,
homonym policy, and orthographic conventions. No shared headword spine
existed; every cross-dictionary project — spell-checkers, alignment
pipelines, coverage studies — re-derived its own union from per-dictionary
exports, with divergent results. One symptom circulated for years: the figure
"94,753" was repeatedly quoted as the size of "the" Sanskrit headword union,
when it is in fact exactly the intersection of Monier-Williams with the large
Petersburg dictionary, an intersection mislabeled as a union. This dataset
fixes one canonical union at the normalized key layer.

The fifteen members (CDSL codes) span four lexicographic traditions:
European-compiled bilingual dictionaries — Monier-Williams (MW), the large
and small Petersburg dictionaries of Böhtlingk–Roth (PWG) and Böhtlingk
(PWK), Apte (AP), Cappeller's English and German editions (CAE, CCS),
Burnouf (BUR), Macdonell (MD), Schmidt's Nachträge (SCH); Vedic special
lexica — Grassmann's Wörterbuch zum Rig-Veda (GRA) and the Vedic name index
(VEI); Buddhist Hybrid Sanskrit — Edgerton (BHS); the Mahābhārata name index
(INM); and the Sanskrit-medium encyclopedias Śabdakalpadruma (SKD) and
Vācaspatyam (VCP).

## 2. Method

### Steps

(1) Per-dictionary headword exports (`{DICT}-unique-key1` lists) were
produced from the CDSL digitizations, normalizing each dictionary's printed
forms to a computational key ("key1": the bare SLP1 lemma from each
dictionary's digitized `<k1>` field, accent marks and print-layer hyphenation
stripped, homograph numbering collapsed). (2) The fifteen lists were
set-unioned on key1; per-dictionary membership flags, attestation counts, and
gender fields were merged programmatically. (3) 237 gender-confirmed `-inī`
feminines were folded onto their `-in` base entries, each carrying an
explicit `fem_fold` note rather than merging silently. The overlap statistics
below were computed by
[headword_overlap_matrix.py](https://github.com/gasyoun/SanskritLexicography/blob/master/data/headword_overlap_matrix.py)
over the released file, never by rebuilding the union.

### Quality control

The union is deterministic and reproducible from the member exports. Row
count is embedded in the producing convention (count = line count, checked at
build); the distinct-code and count invariants (15 codes, 323,425 rows) were
re-verified at release cut and re-verified again against the frozen release
asset on 02-08-2026, including the full `n_dicts` distribution and the 237
`fem_fold` rows. Per-dictionary totals reconcile against the frozen 2014-era
exports (e.g. PWG 106,054 here vs. the frozen `PWG-unique-key1-106085`
export; small deltas are exactly the union's feminine folds and homograph
collapse).

### Limitations

The union inherits each member's digitization state: a headword missing from
a dictionary's export (OCR gap, digitization backlog) is missing from that
dictionary's flags here. Key1 merging deliberately collapses homonyms sharing
a spelling — correct for machine joins, wrong for philology (print-faithful
"key2" exports exist separately for that). Membership is binary per
dictionary: no entry IDs, page references, or sense counts.

Most importantly, **attestation count is not corroboration.** The dictionary
mix skews toward one European lineage: Cappeller's two editions are one work,
PWK and Schmidt descend from PWG, and Monier-Williams's inventory is itself
Petersburg-derived. The dominant pairwise overlaps (MW∩PWG 94,753, MW∩PWK
128,971, CAE∩CCS 27,008) are inheritance mass, not independent agreement. A
companion witness-independence re-audit
([WITNESS_INDEPENDENCE_REAUDIT_UNION15_2026.md](https://github.com/gasyoun/SanskritLexicography/blob/master/data/WITNESS_INDEPENDENCE_REAUDIT_UNION15_2026.md))
shows the union's corroborated share falling from 55.9% to 34.7% once
Monier-Williams is folded into the Petersburg witness. Users should treat
`n_dicts` as lexicographic attestation under that lineage structure, never as
corpus frequency or importance.

## 3. Dataset description

- **Object name:** `union_headwords.tsv`
- **Format names and versions:** TSV (tab-separated values), UTF-8; 6 columns
  (`slp1`, `iast`, `n_dicts`, `dicts`, `gender`, `fem_fold`); 323,425 data
  rows; 12,397,253 bytes. Companion analytical files:
  [headword_overlap_matrix.tsv](https://github.com/gasyoun/SanskritLexicography/blob/master/data/headword_overlap_matrix.tsv)
  (105 unordered dictionary pairs: shared / union / Jaccard) and
  [headword_unique_counts.tsv](https://github.com/gasyoun/SanskritLexicography/blob/master/data/headword_unique_counts.tsv)
  (per-dictionary totals and unique inventories).
- **Creation dates:** member exports and union build 2025–2026; first public
  release 06-07-2026 (data-v0.1.0).
- **Dataset creators:** Mārcis Gasūns (compilation, release); Cologne Digital
  Sanskrit Dictionaries (source digitizations: Funderburk, Malten et al.,
  University of Cologne).
- **Language:** Sanskrit (ISO 639-3 `san`), romanized (SLP1 and IAST);
  metadata and documentation in English.
- **License:** CC BY-SA 4.0 (ShareAlike inherited from the CDSL
  digitizations; see
  [LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md)).
- **Repository name:** GitHub (kosha data-hub, release `data-v0.1.0`);
  Zenodo deposit pending DOI mint — this release predates the GitHub–Zenodo
  webhook (wired 14-08-2026), so it was not auto-archived (verified 25-08-2026
  against the Zenodo API); the software repo's own concept DOI is
  [10.5281/zenodo.21965599](https://doi.org/10.5281/zenodo.21965599), a
  different citable object from this dataset.
- **Publication date:** 06-07-2026.

### Headline distributions

Attestation breadth over the union (re-verified 02-08-2026 on the release
asset):

| `n_dicts` | headwords | share |
|--:|--:|--:|
| 1 | 142,621 | 44.1% |
| 2 | 61,449 | 19.0% |
| 3 | 46,787 | 14.5% |
| 4 | 28,743 | 8.9% |
| 5 | 17,234 | 5.3% |
| 6–9 | 23,011 | 7.1% |
| 10–14 | 3,569 | 1.1% |
| 15 | 11 | 0.003% |

Nearly half the digitized Sanskrit lexicon is single-witness; the fully
saturated core — headwords every one of the fifteen dictionaries records — is
just eleven words. Per-dictionary highlights from the companion files: the
largest unique inventories are MW 44,156, AP 35,762 (40.3% of Apte is in no
other dictionary of the union), SKD 17,333, and BHS 10,434 (58.7% unique —
the most isolated member); the most subsumed are CCS 0.6% and CAE 1.7%
unique. The highest pairwise Jaccard similarities are CAE–CCS 0.672 (two
editions of one work), PWG–PWK 0.630, MW–PWK 0.597, and MW–PWG 0.462 —
quantifying, on a shared key, how much of the field is one
Böhtlingk–Monier-Williams lineage.

## 4. Reuse potential

The index is already the load-bearing spine of several independent consumers:
the kosha unified lookup database keys its lemma table on it; the
SanskritSpellCheck project uses membership tags as evidence tiers; the PWG
translation pilot sampled its worklist from it; the DCS corpus-frequency
sidecar and the dictionary–corpus concordance
([data-v0.2.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.2.0))
join corpus evidence onto its key.

Beyond the origin ecosystem: (a) **coverage studies** — which vocabulary
strata are attested only in Sanskrit-medium lexica, only in Vedic lexica, or
in a single dictionary, using the published `n_dicts` distribution as the
baseline; (b) **NLP lexicon induction** — a 323k-lemma candidate list with
per-source provenance for weighting, and a documented independence structure
for anyone tempted to use attestation count as a prior; (c) **history of
lexicography** — the overlap matrix quantifies inheritance between the
European and Indian dictionary traditions on a shared key, and the
witness-independence analysis is a worked method for any similarly
inbred lexicographic field; (d) **digitization QA** — a new digitization's
headword extraction can be diffed against the union to find both its gaps and
the union's. ShareAlike licensing permits commercial reuse with attribution.

## Acknowledgements

The dataset stands on the digitization work of the Cologne Digital Sanskrit
Dictionaries project (University of Cologne; Thomas Malten, Jim Funderburk
and collaborators), whose per-dictionary exports are the union's inputs.

## Funding statement

No external funding. The dataset was produced within the samskrtam.ru
Sanskrit-education programme.

## Competing interests

The author declares no competing interests.

## References

- Apte, V. S. *The Practical Sanskrit-English Dictionary.* Poona (revised
  and enlarged edition, 1957–1959).
- Böhtlingk, O., and R. Roth. *Sanskrit-Wörterbuch.* 7 vols. St. Petersburg:
  Kaiserliche Akademie der Wissenschaften, 1855–1875.
- Böhtlingk, O. *Sanskrit-Wörterbuch in kürzerer Fassung.* 7 vols.
  St. Petersburg, 1879–1889.
- Cologne Digital Sanskrit Dictionaries (CDSL), Cologne Sanskrit Lexicon
  project, University of Cologne.
  [www.sanskrit-lexicon.uni-koeln.de](https://www.sanskrit-lexicon.uni-koeln.de/).
- Edgerton, F. *Buddhist Hybrid Sanskrit Grammar and Dictionary.* New Haven:
  Yale University Press, 1953.
- Grassmann, H. *Wörterbuch zum Rig-Veda.* Leipzig: Brockhaus, 1873.
- Monier-Williams, M. *A Sanskrit-English Dictionary.* Oxford: Clarendon
  Press, 1899.
- Gasūns, M. *Gasuns Sanskrit Dictionary data release v0.1.0.* GitHub,
  06-07-2026.
  [github.com/gasyoun/kosha/releases/tag/data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0).

## Backlog to 5/5

1. Mint a Zenodo DOI for this dataset and replace the "DOI pending" slots
   (human step) — the GitHub–Zenodo integration is now live (wired
   14-08-2026) but only archives releases published after that date; either
   cut a fresh `data-v*` release (auto-archived) or MG manually
   retro-deposits `data-v0.1.0` on Zenodo.
2. Final human pass on the dictionary-tradition characterization (§1) and the
   reference list's edition details.
3. Transfer into JOHD's submission template (their online form re-keys the
   metadata table) at submission time.

## Provenance

Drafted 11-07-2026 by Fable 5 (`claude-fable-5`) under handoff
[H665](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H665-Fable_kosha_dataset-data-statements_11.07.26.md)
from the dataset's data statement. Upgraded to a submission draft 02-08-2026
by Fable 5 (`claude-fable-5`) under handoff
[H1872](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1872-Fable_kosha_a55-a56-johd-data-papers-submission-draft_29.07.26.md):
all counts re-verified against the frozen release asset; overlap and
witness-independence results integrated from
[HEADWORD_OVERLAP_UNION15_2026.md](https://github.com/gasyoun/SanskritLexicography/blob/master/data/HEADWORD_OVERLAP_UNION15_2026.md)
(H684/H1363). Registered as A55 in
[ARTICLES.md](https://github.com/gasyoun/Uprava/blob/main/ARTICLES.md).

_Dr. Mārcis Gasūns_
