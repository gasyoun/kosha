# Digital Sanskrit dictionaries — live comparison

_Created: 02-07-2026 · Last updated: 02-07-2026_

Twelve platforms compared for the Gasuns Sanskrit Dictionary. **Method:** three
parallel research passes on 2026-07-02, each site actually fetched that day;
every claim is marked **VERIFIED** (fetched live 02-07-2026), **VERIFIED-M**
(fetched from an official mirror/archive that day), or *inferred* (search
snippets, docs, older snapshots). Research and synthesis: Fable 5
(`claude-fable-5`). Companion docs:
[POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md) ·
[POSITIONING_SUMMARY.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING_SUMMARY.md).

**Headline finding (a correction to our own earlier framing):**
[michaelmeyer.fr/sanskrit](https://michaelmeyer.fr/sanskrit) is not "a fast
Apte site" — it aggregates **41 dictionaries (1832–2000) on one page per
headword, with per-sense scan links for 19 of them**. It is the closest
existing thing to "Logeion for Sanskrit." What it deliberately does *not* do —
Devanagari, inflected-form lookup, morphology, corpus/frequency evidence,
non-Western gloss languages, API/open data, versioned citability — is exactly
the space left for this project.

---

## Feature matrix (state as fetched 02-07-2026)

| | Dicts | Multi-dict 1 screen | Scan links | Input auto-detect / diacritic-free | Inflected-form lookup | Sandhi/compound help | Morphology / paradigms | Corpus / frequency | Citability / provenance | API / open data | Crawlable permalinks | Mobile / offline |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **michaelmeyer.fr** | **41** | ✅ all, grouped by language | ✅ **per-sense**, p.+col., 19 dicts | ⚠️ IAST+Velthuis mix (no auto, no Deva) | — (cross-ref clusters instead) | ⚠️ phoneme wildcards + fuzzy `*term~` | — | — | ⚠️ scan = provenance; no cite/version | — closed | ✅ server-rendered | — |
| **sanskritdictionary.com** | opaque (MW+DCS+Vedabase…) | ⚠️ per-sense pages | — | ✅ auto-detect 5 schemes | — | ✅ `sandhi:` + `root:` operators | — | ⚠️ word-frequency tool | ⚠️ per-sense source label, no edition | — Cloudflare-walled | ⚠️ permalinks behind bot wall | — |
| **learnsanskrit.cc** (ex-spokensanskrit) | own crowd-DB | n/a (own data) | — | ✅ direction auto + ASCII/Deva/IAST | ⚠️ colloquial forms in DB | — ("split it yourself") | — | — (fable reader) | — | — | — SPA, invisible | — |
| **CDSL Cologne** | **43** | ⚠️ `/simple/` + experimental multi | ✅ per-entry `servepdf` | ✅ 5 schemes (no auto) | ⚠️ separate MW-inflected list | — | — | — | ✅ scan + corrections loop | ✅ XML downloads; no JSON API | ✅ server-rendered | ⚠️ Flutter app, unreleased |
| **Ambuda** | 8 | — one at a time | — | ✅ auto-detect + regional scripts | — | — (reader-side planned) | — (vidyut = dev library only) | ⚠️ 200+ proofread texts | — | ✅ fully open source (MIT) | ⚠️ | — |
| **Heritage (Inria/UoHyd)** | 2 (Huet FR + MW) | ⚠️ | — born-digital | ✅ "Sanskrit Made Easy" fuzzy | ✅ lemmatizer | ✅ **full segmenter, pick-a-split UI** | ✅ **declension + conjugation engines** | ⚠️ small curated corpus | ⚠️ | ⚠️ CGI endpoints; Inria host bot-walled | ⚠️ | — |
| **Wisdom Library** | ~6 Skt + others | ✅ stacked, per-block source | — | ⚠️ | — | — | ⚠️ notes only | ⚠️ links into hosted texts | ⚠️ source named, no edition/page | — | ✅ **best crawlable permalinks** | — |
| **DCS** | corpus-as-dict | n/a | — | ⚠️ | ✅ (corpus is analyzed) | ✅ (corpus is sandhi-split) | ⚠️ tags, not paradigms | ✅ **per-lemma counts + diachrony, KWIC** | ✅ BibTeX; CC BY 3.0 site | ✅ full CoNLL-U dump on GitHub | ⚠️ | — |
| **VedaWeb (→Tekst)** | via C-SALT links | n/a | — | ⚠️ | ✅ per-word RV annotation | ✅ | ✅ word-click analysis panel | ✅ RV, strata/metre | ✅ TEI export | ✅ REST API, open source | ⚠️ SPA | — |
| **Gandhāri.org** | 1 (born-digital) | n/a | — | ✅ search by Skt/Pali/EN equivalents | ✅ corpus-born | ✅ | ⚠️ grammar module | ✅ dictionary built *from* corpus | ✅ **Cite button** (unversioned) | — none stated | — JS-only | — |
| **Logeion** (Gk/Lat benchmark) | ~8+ | ✅ tabs per headword | — | ✅ autocomplete | ⚠️ lemma-based | n/a | ⚠️ | ✅ **frequency+collocations+textbook sidebar** | ⚠️ | ⚠️ data on GitHub, platform closed | — SPA | ✅ **offline iOS app** |
| **Gasuns SD (target)** | 40+ via CDSL | ✅ | ✅ per-sense via `ls_resolver` | ✅ auto-detect + fuzzy | ✅ glossary 86.6 % | ✅ vidyut/Heritage split | ✅ vidyut paradigms + Zaliznyak token | ✅ DCS bands + examples | ✅ sense-IDs + versioned DOI + Cite | ✅ public API + dumps | ✅ server-rendered | ✅ PWA offline |

Legend: ✅ has it · ⚠️ partial/qualified · — absent. Last row = the design
target this comparison justifies, not a claim about built software.

---

## Per-site profiles

### 1. michaelmeyer.fr/sanskrit — the silent front-runner (VERIFIED, deep-dive)

- **41 dictionaries** on one page per headword, grouped by target language,
  with an anchor TOC: Cologne-encoded classics (both MW 1872 *and* 1899, PWG,
  PW, Grassmann, Apte 1890 *and* 1959 via U. Chicago DSAL, Śabdakalpadruma,
  Vācaspatyam, BHS Edgerton…) **plus seven indices Meyer digitized himself**
  (Renou ×3, Tāntrikābhidhānakośa, Bergaigne, Caland-Henry, Whitney) —
  including **Stchoupak-Nitti-Renou 1932** with scan links. Credits Cologne
  (Funderburk/Malten) on-page.
- **Per-sense scan links** — "☞ p. 346, col. 1" → `/sanskrit/{dict}/scans/{vol}/{page}`,
  19 dictionaries; minimal viewer (PNG + prev/next). Finer-grained than
  CDSL's per-entry `servepdf`.
- **Search grammar** worth studying: `?` = one *phoneme* (not character),
  `*` = any phonemes, `~` = Levenshtein fuzzy, `#` = browse-autocomplete;
  `*uddyota~` is his compound-search workaround. Input = IAST + Velthuis
  freely mixed. **No Devanagari anywhere**, no inflected forms (doctrine:
  "input the stem, follow cross-references"), no morphology, no corpus.
- **Cross-reference clusters**: mechanically merged orthographic/inflectional
  variants (*gandharva ⇄ gandharvaḥ, gaṃdharvaḥ…*) reconciling
  nominative-headword dicts (Apte, ŚKD) with stem-headword ones — he calls
  the disambiguation ML-assisted and admits inaccuracy.
- **Tech**: no-framework server-rendered HTML (12.8 KB page), one vanilla-JS
  autocomplete XHR; no ads/analytics/cookies; fast. Site code closed; his
  [github.com/michaelnmmeyer](https://github.com/michaelnmmeyer) has C
  building blocks ([skt](https://github.com/michaelnmmeyer/skt)
  transliteration/collation — powering-the-site is *inferred*).
- **Author** (his own pages, VERIFIED): Michaël Meyer, PhD on vyākaraṇa +
  non-dual Kashmir Śaivism; GitHub bio: **ERC-DHARMA, CNRS, Paris**. (This
  replaces the unsourced "University of Geneva" claim from the pre-audit
  docs.)
- **Single-maintainer, closed, "last updated December 15, 2024"** — the
  fragility is the opportunity.

### 2. sanskritdictionary.com (Cloudflare-walled; archived snapshots ≤2 months old)

Mixed aggregation (MW + DCS + Vedabase + machine-translated "100 languages"
layer), "931,416 unique words" self-claim. Best ideas: **input auto-detection
across 5 schemes** ("we will detect and convert"), **`sandhi:` and `root:`
query operators**, stable per-sense permalinks with a source label. Weak:
provenance without editions/pages, opaque inventory, and a bot wall that
locks out scholarly reuse. Run under a vedicsociety.org account; no personal
attribution assertable.

### 3. learnsanskrit.cc (ex-spokensanskrit.org; old domain 301s, TLS broken)

Hand-curated crowd DB (edit UI visible in page source) with **CEFR/Basic-
Vocabulary levels per entry** — a learner-graded layer nobody else has.
Direction auto-detect (SA→EN/EN→SA/"Automatically"), ASCII+Devanagari+IAST
input, click-any-word fable reader as onboarding. Invisible-to-crawlers SPA,
no provenance, thin classical coverage.

### 4. CDSL Cologne (VERIFIED)

**43 dictionaries**, per-dict Basic/List/Advanced/Mobile displays, 5 input
schemes, per-entry scan click-through, XML+PDF downloads for everything, a
unified [/simple/](https://www.sanskrit-lexicon.uni-koeln.de/simple/) search
(scope undocumented) and an "experimental" multi-dict display. The substrate
of this project (tracks 1–2 of the program). Weaknesses: fragmented 1999-era
UX, no morphology in the main path, Flutter app unreleased.

### 5. Ambuda (VERIFIED)

8 dictionaries, one-at-a-time display, auto-detected input + regional-script
output, 200+ proofread texts, fully open source; **vidyut-kosha is a
developer library (`pip install vidyut`, ~100 M forms, MIT) with no end-user
UI anywhere** — the morphology backend is sitting on a shelf, usable by us.
Own 2026 blog names time/scans/funding as bottlenecks. No scan provenance,
no frequency.

### 6. Sanskrit Heritage (Inria host bot-walled today; UoHyd mirror v3.77, 03-2026, VERIFIED-M)

The only platform doing **sandhied-input segmentation with a pick-your-split
UI**, plus declension/conjugation *generation* engines and diacritic-free
"Sanskrit Made Easy". Two lexicons only (Huet's French + MW), classical-core
scope by design. Cautionary tale: the Anubis anti-bot wall currently breaks
every third-party integration against the Inria host.

### 7. Wisdom Library (VERIFIED)

Aggregates Cologne dicts + BHSD + regional dictionaries into **stacked
all-source definition pages with per-block attribution**, cross-linked into
its own hosted texts — and it was the only site in this survey whose pages a
fetcher could read completely (server-rendered permalinks: the SEO/archival
lesson). Shallow provenance (no edition/page/scan), affiliate links inside
definitions.

### 8. DCS (VERIFIED; **HTTPS cert broken**, plain HTTP only)

The corpus-as-dictionary: per-lemma attestation counts with diachronic
distribution, KWIC, parallels; **full 5.46 M-word CoNLL-U dump on GitHub**
(LemmaId/OccId-keyed, pushed 03-2026) — the evidence layer this project
consumes. Supplies its own BibTeX. License tension: CC BY 3.0 site vs no
license file in the dump.

### 9. VedaWeb → Tekst (VERIFIED — mid-migration)

The original DFG app (word-level RV morphology, grammar search, TEI export,
REST API, C-SALT dictionary links) was **archived 16-02-2026**; the domain
now runs the successor platform Tekst. Integration caution while URLs/docs
are in flux. The model for word-click → analysis + dictionary panel.

### 10. Gandhāri.org (VERIFIED)

Born-digital scholarly dictionary fused with its corpus/catalog/bibliography;
searchable **by Sanskrit/Pali/English equivalents**; a **Cite button on every
view**. No license/API/versioning — cite-without-version is fragile, a
mistake for us to avoid, not copy.

### 11. Logeion (SPA; about-page + App Store verified)

The Greek/Latin benchmark: autocomplete → simultaneous multi-dictionary tabs →
**sidebar with corpus frequency, collocations, "frequent authors" (click →
Perseus/PhiloLogic), and textbook chapter references**; free offline-capable
iOS app; dictionary *data* maintained openly on GitHub (platform closed).
Every sidebar ingredient has a Sanskrit equivalent already in our hands (DCS
bands, corpus_lexicon, teaching-grammar refs).

### 12. learnsanskrit.org (VERIFIED — exited the business)

`/dictionary/` is a hard 404; tools page offers transliteration only and
points users to Ambuda. Included for the record.

---

## What each site teaches the Gasuns Sanskrit Dictionary

**Steal (with attribution of the idea):**

1. meyer: per-**sense** scan links (page + column), phoneme wildcards +
   composable fuzzy, `#`-browse mode, `<abbr>` tooltips expanding every
   source abbreviation, variant/inflection cross-ref clusters.
2. sanskritdictionary.com: input auto-detection (no scheme picker), `sandhi:`
   / `root:` query operators.
3. learnsanskrit.cc: CEFR/basic-vocabulary grading per entry; direction
   auto-detect; click-any-word starter texts.
4. CDSL: the corrections feedback loop on every entry; bulk XML downloads as
   a standing offer.
5. Ambuda: vidyut-kosha as the form-lookup backend (MIT, unexposed to end
   users — first mover wins); regional-script output.
6. Heritage: pick-your-split segmentation UX; paradigm *generation* on
   demand.
7. Wisdom Library: server-rendered per-headword permalinks (crawlable,
   archivable, SEO); stacked multi-source view.
8. DCS: per-lemma diachronic attestation block; ship BibTeX (and go further:
   versioned per-sense citations).
9. VedaWeb: expose the dictionary as an API others embed (C-SALT seam).
10. Gandhāri: Cite button everywhere — but versioned.
11. Logeion: the corpus sidebar; offline app tier; dictionary data corrections
    via public GitHub.

**Avoid (observed failure modes, all live today):** single-maintainer closed
sites (meyer, DCS cert, spokensanskrit TLS); bot walls that break scholarly
reuse (sanskritdictionary.com, Inria); SPAs with no server-rendered
permalinks (Logeion, Gandhāri, learnsanskrit.cc); provenance without edition/
page (Wisdom Library, sanskritdictionary.com); citations without versions
(Gandhāri); mid-migration URL churn without redirects (VedaWeb,
learnsanskrit.org's dead /dictionary/).

## The revised positioning sentence

Before this survey: "nobody has built the collapse." After it: **meyer built
the read-only collapse** — 41 dictionaries, one page, scan-anchored — and
stopped there (no Devanagari, no forms, no morphology, no corpus, no API, no
versioning, one maintainer, closed source). The Gasuns Sanskrit Dictionary =
**meyer's collapse + Heritage's morphology + DCS's evidence + Logeion's
sidebar + Cologne's corrections loop + the trilingual DE/EN/RU layer — open,
API-first, versioned, and citable.** That composite exists nowhere.

---

_Dr. Mārcis Gasūns_
