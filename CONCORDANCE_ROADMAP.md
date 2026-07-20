# Sanskrit Concordance Program — 1-Year Roadmap

_Created: 08-07-2026 · Last updated: 13-07-2026_

A twelve-month plan to build a portfolio of four Sanskrit **concordances** —
grammar and nongrammar — each shipped as a citable dataset (registered in the
[kosha data-hub manifest](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json))
**and** an interactive web concordance (kosha Pages / samskrtam.ru). No research
papers this cycle — datasets + web are the definition of "done".

The seed already in hand: a **Grassmann ↔ Rigveda** concordance via VedaWeb's
`id_gra` field (exact match to the GRA `<L>` entry number, no fuzzy matching —
9,945 of 12,785 GRA entries linked to attested RV occurrences). That is one cell
of the matrix below; this roadmap generalizes it to the whole
[DCS corpus](https://github.com/gasyoun/VisualDCS) (5.7M tokens, 270 texts).

---

## The core idea — one schema, four instantiations

Every concordance here is the same shape: **link a lexicon/grammar anchor to a
corpus locus, with evidence**. So the year builds **one concordance core** up
front (Q1) and instantiates it four times.

**Canonical concordance record** (shared TSV/JSONL schema):

| field | meaning |
|---|---|
| `anchor_type` | `dict-entry` · `parallel-verse` · `inflection` · `panini-sutra` |
| `anchor_id` | stable ID in the source resource (e.g. GRA `<L>`, sūtra 6.1.77) |
| `anchor_key_slp1` | length-preserving `form_key()` (never NFD+strip — per [`/crosswalk-build`](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md) discipline) |
| `corpus_locus` | DCS sentence/token id |
| `corpus_text_id` | which of the 270 DCS texts |
| `match_method` | `exact` / `floor` / `relaxed` / `fuzzy` (tiered, per-tier counts reported) |
| `confidence` | tier-derived score |
| `evidence_count` | attestation count backing the link |

**Reuse, don't rebuild** (per [`../SHARED_CODE.md`](https://github.com/gasyoun/github-spine/blob/main/SHARED_CODE.md) + the kosha max-reuse rule):
the crosswalk, scan resolver, `form_key()`, and citation minting
([`app/cite.py`](https://github.com/gasyoun/kosha/blob/main/app/cite.py)) already
exist. The web layer is **one** reusable concordance viewer (anchor list → click →
KWIC attestations in context, scan-anchored to the printed source) built once and
themed four times.

---

## The buildable matrix (why these four)

### Axis A — Grammar concordances (morphology / Pāṇini ↔ attestation)

| # | Concordance | Existing inputs | In this roadmap |
|---|---|---|---|
| A1 | Root → attested corpus forms | [`mw-roots`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) (2,113), `dcs-verb-roots-by-class` (463) | folded into **A3** |
| A2 | Paradigm-token → attestation (335 Zaliznyak tokens) | `zaliznyak-grammar-index` (98,639) | folded into **A3** |
| **A3** | **Generated-vs-attested paradigm** | `kosha-db` (6.9M inflections), `dcs-full-sqlite` (5.7M tokens) | **Q3 flagship** |
| **A4** | **Pāṇinian sūtra → form → corpus** | vidyut-prakriya sūtra chains, DCS | **Q4 flagship (highest novelty)** |
| A5 | Compound (samāsa) structure → corpus | `dcs-compound-dictionary` (37,333) | stretch / Y2 |

### Axis B — Nongrammar concordances (lexicon / text / citation ↔ attestation)

| # | Concordance | Existing inputs | In this roadmap |
|---|---|---|---|
| **B1** | **Dictionary entry → corpus occurrence** (GRA sample generalized to MW/PWG/AP90) | `dcs-cdsl-xref` (**already 81.4% linked**), `union-headwords` (323k) | **Q1 flagship** |
| B2 | `<ls>` citation label → text locus | `indische-sprueche` (proven for PWG) | stretch / Y2 |
| **B3** | **Parallel-passage / repeated-verse concordance** (a Bloomfield for all DCS) | `dcs-parallel-passages-full` (**506,787 alignments already computed**) | **Q2 flagship** |
| B4 | Collocation / syntagmatic concordance | `dcs-sintagmatic-appendix7` (82k), `dcs-stem-cooccurrence-full` (353k) | stretch / Y2 |
| B5 | Cross-lingual entry → RU/EN → corpus | `corpus-lexicon`, `sa-ru-glossary` | rights-gated — out of scope |

**Prior art** (checked, not reinvented): [Bloomfield's *Vedic Concordance*](https://en.wikipedia.org/wiki/Vedic_Concordance) (1906) is the classic model for B3 — and DCS's 506k parallel-passage export is effectively a computed modern equivalent, just unsurfaced. VedaWeb's `id_gra` is the done B1 seed. `dcs-cdsl-xref` already solves 81% of B1's join.

---

## The year — a risk-ordered portfolio

Surface the two that are ~80% pre-computed first (fast wins, and they build the
shared core), then the greenfield grammar work.

### Q1 (months 1–3) — B1 · Dictionary ↔ corpus, pan-corpus  ·  *+ the shared core*

- **Inputs:** [`dcs-cdsl-xref`](https://github.com/sanskrit-lexicon/csl-apidev) (81.4% linked), `union-headwords`, `dcs-full-sqlite`, kosha rendered entries.
- **Build:** generalize the GRA `id_gra` exact-match to CDSL headword → DCS lemma across MW/PWG/AP90; fill the 18.6% residue with the tiered `floor/relaxed/fuzzy` matcher (per-tier counts reported, honest residue caveats). **Build the concordance core here** (schema, `form_key()` join, scan anchoring, the reusable web viewer).
- **Deliverables:** dataset `dict-corpus-concordance` (manifest row + public-tier release) · web page `/concordance/dict/`.
- **Exit checks:** ≥90% of CDSL headwords carry ≥1 DCS attestation *or* an explained absence; a golden sample is human-verified ([`/spot-check-sample`](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md)); every citation resolves scan-anchored and host-independent (RISKS R1/R5).

### Q2 (months 4–6) — B3 · Bloomfield-style parallel-passage concordance

**Status: core build shipped 13-07-2026 (H836); Bloomfield RV cross-reference shipped
13-07-2026 (H896). One exit check still blocked on a human decision — see below.**

- **Inputs:** [`dcs-parallel-passages-full`](https://github.com/gasyoun/VisualDCS) (245 files;
  the prior "506,787 alignments" estimate did not survive a direct parse — this build's
  authoritative count is 501,231 source verses / 153,045 GOOD+PARTLY links, see
  [`PARALLEL_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/PARALLEL_BUILD_REPORT.md)),
  `dcs-full-sqlite`.
- **Build:** normalize the 245-file PARA export into one verse-keyed concordance — **done**,
  via [`scripts/build_parallel_passage_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_parallel_passage_concordance.py).
  Content-diffing the three known variants (live `Polnorazmernye`, the 2022 archive, and the
  differently-scoped `Stopovye` per-pada export) was **not independently re-done row-by-row**
  this pass — the build defaults to `Polnorazmernye/` per the folder's own README default,
  flagged as `@DECIDE` rather than self-ruled (R-C2, still open). **Bloomfield *pratīka*
  cross-reference for the RV subset: DONE** (H896, 13-07-2026) — MG obtained written
  permission from Marco Franceschini (University of Bologna) for his digital edition of
  Bloomfield's 1906 *A Vedic Concordance* (HOS 9); see
  [`BLOOMFIELD_RV_CROSSREF_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/BLOOMFIELD_RV_CROSSREF_REPORT.md)
  for the full method (position-independent, text-validated join — 85% of the 13,581 RV
  subset rows populated, remainder is genuine orthographic edition variance, documented not
  forced) and
  [`data/manifest/rights/franceschini_hos9_permission_2026-07-13.md`](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/franceschini_hos9_permission_2026-07-13.md)
  for the rights grant.
- **Deliverables:** dataset `parallel-passage-concordance` (manifest row ✅, release pending —
  same "unreleased" state as B1) · dataset `bloomfield-rv-citations` (manifest row ✅) · web page
  [`/concordance/parallels/`](https://github.com/gasyoun/kosha/blob/main/concordance/parallels/index.html)
  ✅ live, now surfacing the Bloomfield pratīka when present.
- **Exit checks:** every source passage's parallels navigable ✅; verdict annotations surfaced
  ✅ (GOOD/PARTLY badges + word-diffs); RV subset cross-linked to Bloomfield ✅ (85% validated
  join, H896); variant provenance documented ✅ (build report + this section).
- **`@DECIDE` (a human should decide, not self-ruled) — one item remains:** confirm
  `Polnorazmernye/` as the released-canonical parallel-passage variant (or direct otherwise) —
  R-C2. The Bloomfield-digitization-source `@DECIDE` is **resolved** (see above).

### Q3 (months 7–9) — A3 · Generated-vs-attested morphology audit

- **Inputs:** `kosha-db` (6.9M vidyut-generated inflections), `dcs-full-sqlite` (5.7M attested tokens), the [E1 dual-engine work](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md) (already built).
- **Build:** join generated forms ⨯ attested forms on `form_key()` into three buckets — **attested & generated** (confirmed), **generated-never-attested** (over-generation), **attested-never-generated** (engine/grammar gaps). Absorbs A1 (root→forms) and A2 (paradigm-token→attestation). ⚠ handle the manifest-noted **DCS `Tense=Past` aorist/perfect conflation** in verb buckets.
- **Deliverables:** dataset `morphology-attestation-audit` (manifest row + release) · web page `/concordance/morphology/` (paradigm cell → attested? with corpus evidence).
- **Exit checks:** full 6.9M ⨯ 5.7M join complete; the "attested-never-generated" residue triaged (OCR/segmentation error vs genuine gap); gaps routed to the csl-inflect give-back (H185).

### Q4 (months 10–12) — A4 · Pāṇinian sūtra ↔ corpus  ·  *flagship, highest novelty*

- **Inputs:** vidyut-prakriya derivations (emit the Aṣṭādhyāyī sūtra chain per form), the Q3 attested-form join.
- **Build:** for each attested form, run the vidyut derivation, capture the sūtra sequence, invert to `sūtra → {attested forms exemplifying it}`. A concordance keyed by sūtra number — **unpublished territory: no corpus-grounded Pāṇinian concordance exists.**
- **Deliverables:** dataset `paninian-corpus-concordance` (manifest row + release) · web page `/concordance/panini/` (click a sūtra → its attested corpus exemplars, scan-anchored).
- **Exit checks:** a sūtra-coverage map (which of ~4,000 sūtras have real corpus exemplars, which are "dark"); sampled human verification that the derivation chain is correct for N forms; derivation-metadata license settled (see @DECIDE).
- **W2a (derivation harness) DONE 20-07-2026 (Sonnet 5 `claude-sonnet-5`, H1368).** [`scripts/build_panini_derivations.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_panini_derivations.py) ran the FULL 401,368-row W1b AG bucket (pilot 10k reported first per exit-check 2a-1, then the full run — 883.8s, 454.1 forms/s, well under the 40-min scaling cap): `ok` 72,764 (18.13%) · `no-derivation` 237,447 (59.16%) · `ambiguous` 86,857 (21.64%) · `engine-error` 4,300 (1.07%); 2,815 distinct sūtra chains, length min 6 / median 12 / max 37. Full detail + 30-example sampled human-verification section: [`data/concordance/DERIVATION_HARNESS_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/DERIVATION_HARNESS_BUILD_REPORT.md). **W2b (invert to the sūtra concordance) is next, not yet built.**

---

## Cross-cutting

**Dependencies (build order is load-bearing):** the concordance core (Q1) is a hard
prerequisite for Q2–Q4. Q4 depends on Q3's attested-form join. Per the kosha data
rule, running a later stage against a stale earlier one produces silently wrong
output, not an error.

**Risks:**
- **R-C1** Pan-corpus matching noise (B1's 18.6% residue) — mitigated by tiered matching + honest per-tier reporting, never a silent fuzzy blur.
- **R-C2** B3's three parallel-passage variants are not yet content-diffed — Q2 must resolve which is canonical before surfacing.
- **R-C3** vidyut derivation coverage/failures (A4) — some attested forms won't derive; report the dark set, don't hide it.
- **R-C4** DCS `Tense=Past` conflates aorist/perfect — affects A3 verb buckets and A4 sūtra attribution; carry the caveat through.

**Open @DECIDE (a human should decide):**
1. **License composition** — B1/B3 join DCS (CC BY 4.0) → concordances inherit BY-SA cleanly; but A4 embeds vidyut-prakriya derivation metadata — confirm the derivation output's license before the A4 release.
2. **Papers, later?** — this cycle is datasets + web only by choice. A3 ("generated vs attested Sanskrit morphology") and A4 ("a Paninian concordance of the DCS") are both strong Axx paper candidates for a Year-2 pass — parked, not dropped.
3. ~~**Bloomfield cross-reference source** (Q2) — which digitization of the 1906 *Vedic Concordance* to key against for the RV subset.~~ **RESOLVED 13-07-2026 (H896):** Marco Franceschini's digital edition (Harvard Oriental Series 9), rights-cleared by the author's direct written permission — see [`data/manifest/rights/franceschini_hos9_permission_2026-07-13.md`](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/franceschini_hos9_permission_2026-07-13.md).

**Delivery discipline:** each quarter → a manifest row in the **same pass** as the
dataset (agent contract), a public-tier release via [`/cut-release`](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md) +
[`/data-release`](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md) (safety-check
gate → license → provenance → DOI), and a web page via the [`/viz-page`](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md)
house pattern (trust block: source artifact, n, date; CSV fallback). Each quarter
gets its own `H###` handoff minted at kickoff; this doc is the parent.

---

_Dr. Mārcis Gasūns_
