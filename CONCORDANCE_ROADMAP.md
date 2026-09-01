# Sanskrit Concordance Program — 1-Year Roadmap

_Created: 08-07-2026 · Last updated: 01-09-2026_

> **Truth-pass 27-08-2026** (Grok 4.6 `grok-4.6`). D4 addendum: this file joined the Wave 1 FLAG list after 21-08. Closed references checked against the combined registry. Kept in place ([FINDINGS §475](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md) clause 3). Not archived.

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
| `match_method` | `exact` / `floor` / `xref` (strict tiers only; relaxed & fuzzy dropped D6) |
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
| **A3** | **Generated-vs-attested paradigm** | `kosha-db` `inflections` (6.9M rows / 3.33M distinct forms, **Cologne MW-inflect**, not vidyut — corrected H3782), `dcs-full-sqlite` (5.7M tokens) | **Q3 flagship** — both joins shipped (H1262 · H3782); web page owed |
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

**Status: SHIPPED 10-07-2026 (H380, Fable 5 `claude-fable-5`), RELEASED 19-07-2026 in
[data-v0.2.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.2.0) (asset
`dict_corpus_concordance.tsv`, 6,738,653 bytes). Every exit check met.** Verified
mechanically 01-09-2026 (H3782) — see the Q1–Q3 status table below.

- **Inputs:** [`dcs-cdsl-xref`](https://github.com/sanskrit-lexicon/csl-apidev) (81.4% linked), `union-headwords`, `dcs-full-sqlite`, kosha rendered entries.
- **Build:** generalize the GRA `id_gra` exact-match to CDSL headword → DCS lemma across MW/PWG/AP90 with strict tiers only (`xref`, `exact`, `floor`); the 18.6% residue unfilled per decision D6 (relaxed tier scored 0/3 on golden sample, dropped). **Build the concordance core here** (schema, `form_key()` join, scan anchoring, the reusable web viewer).
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
- **Release status corrected 01-09-2026 (H3782).** The "release pending — same 'unreleased'
  state as B1" clause above was **already false when it was written**: both
  `parallel_passage_concordance.tsv` (32,224,842 bytes) and `bloomfield_rv_citations.tsv`
  (2,790,672 bytes) shipped as assets of
  [data-v0.2.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.2.0) on **19-07-2026**,
  five weeks before this file's 27-08 truth-pass, and `datasets.json` carries
  `in_release: data-v0.2.0` for both. B1 is released too. Nothing is pending.
- **`@DECIDE` (a human should decide, not self-ruled) — one item remains:** confirm
  `Polnorazmernye/` as the released-canonical parallel-passage variant (or direct otherwise) —
  R-C2. The Bloomfield-digitization-source `@DECIDE` is **resolved** (see above).

### Q3 (months 7–9) — A3 · Generated-vs-attested morphology audit

**Status: BOTH JOINS SHIPPED; the web-page deliverable is still open.** A3 was never run as
its own quarter — the 17-07-2026 ruling (D1) promoted A4 into the Q3 slot and **absorbed
A3's join into A4's wave 1 as a prerequisite**, so only the slice A4 needed was built.
H3782 (01-09-2026) ran the join this section actually specifies. Detail below.

- **Inputs:** `kosha-db` inflected forms, `dcs-full-sqlite` (5,688,416 attested tokens), the [E1 dual-engine work](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md) (already built).
  **Input attribution corrected 01-09-2026 (H3782): the 6.9M is NOT vidyut.** `kosha.db`
  `inflections` holds 6,917,018 rows / 3,326,312 distinct `form_slp1`, of which
  **6,916,522 are `source='cologne_mwinflect'`** (plus 326 `hybrid-natva-fix`, 153
  `curated-gita-pronoun`, 17 `vidyut-gap-fill`). vidyut's actual output lives in the
  separate `forms` table (28,567 rows). The two tables are different generators and the
  audit means different things on each.
- **Build:** join generated forms ⨯ attested forms on `form_key()` into three buckets — **attested & generated** (confirmed), **generated-never-attested** (over-generation), **attested-never-generated** (engine/grammar gaps). Absorbs A1 (root→forms) and A2 (paradigm-token→attestation). ⚠ handle the manifest-noted **DCS `Tense=Past` aorist/perfect conflation** in verb buckets.
- **Deliverables:** dataset `morphology-attestation-audit` (manifest row ✅ + released ✅ in
  [data-v0.2.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.2.0), asset
  `morph_attest_AG.tsv`) · dataset `morphology-attestation-audit-inflections` (manifest row
  ✅ 01-09-2026, unreleased — rides the next data cut) · web page `/concordance/morphology/`
  (paradigm cell → attested? with corpus evidence) — **❌ NOT BUILT.** `concordance/` carries
  `dict/`, `panini/`, `parallels/` and `senses/`; there is no `morphology/`. This is the one
  Q3 deliverable with no artefact behind it.

#### The two joins, and why the second one had to exist

| | W1b (H1262, 18-07-2026) | H3782 (01-09-2026) |
|---|---|---|
| Generated side | `forms`, heritage excluded — 426,410 rows | `inflections` — 3,326,312 distinct forms |
| Generator | 93.3% `source='dcs'` + 28,567 vidyut | 99.99% `cologne_mwinflect` |
| Attested side | `token.form` (sandhied) — 381,413 | `token.form` **+** `token.m_unsandhied` — 386,012 keys |
| **AG** | 401,368 of 426,410 (94.1%) | **239,443 of 3,326,312 (7.20%)** |
| **G¬A** | 25,042 | **3,086,869 (92.80%)** |
| **A¬G** | **2** | **196,378 of 386,012 (50.87%)** |

The W1b A¬G of **2** is not a finding about Sanskrit morphology; it is an artefact of
joining DCS against a generated side that is itself 93% ingested DCS. That build's own
report says so and hands the question on. The `inflections` side is derived from MW
headwords with no DCS input, so it is the only one of the two on which
"attested but never generated" carries engine meaning — and there the corpus half of the
asymmetry is **196,378 keys, not 2**.

⚠ **The A¬G residue is not 196,378 engine defects.** The generator's lemma inventory is
**222,736 nominal lemmas against 680 verbal**, so finite verbs are territory
`inflections` never claimed; the report cross-tabs every triage class against DCS `upos`
so a verb-shaped gap is never quoted as a nominal-engine defect. Full method, triage and
four human-checkable sample tables:
[`data/concordance/MORPHOLOGY_ATTESTATION_INFLECTIONS_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/MORPHOLOGY_ATTESTATION_INFLECTIONS_BUILD_REPORT.md).

- **Exit checks:** full 6.9M ⨯ 5.7M join complete ✅ (H3782 — W1b did **not** satisfy this:
  it joined 426,410 rows, not 6.9M); the "attested-never-generated" residue triaged
  ✅ (H3782 triages it into `paradigm_gap` / `lexicon_gap` / `segmentation_artefact` /
  `non_sanskrit_or_ocr`, each cross-tabbed by `upos`; W1b's triage ran over a residue of 2);
  gaps routed to the csl-inflect give-back (H185) — **⏳ payload built, hand-off owed**: W1b
  had `genuine_engine_gap = 0` so nothing was ever routed. H3782 produces the first real
  payload and narrows it honestly —
  [`morph_giveback_candidates.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/morph_giveback_candidates.tsv),
  **5,656 rows**, from `paradigm_gap`'s 94,018 by three measured subtractions (verbs 26,470 ·
  sandhied-surface-only 61,330 · bare stems 562). Quoting A¬G as "forms the engine misses"
  overstates the actionable set **35×**. The head cross-validates (pronoun dative/locative
  cells and irregular feminine/consonant stems — precisely where MW-inflect is weak, and
  `inflections` already carries a hand-made `curated-gita-pronoun` patch), but allomorphic
  bound stems still pass the filter (`rājñ`, `ātma` at ranks 2–3), so this is a **candidate
  set needing human triage, not a defect list**. Routing it is a queued port, never an
  in-pass csl-inflect edit.

#### Q1–Q3 status, verified mechanically 01-09-2026 (H3782)

| Quarter | Workstream | Dataset | Release | Web page | Verdict |
|---|---|---|---|---|---|
| Q1 | B1 dict ↔ corpus | `dict-corpus-concordance` ✅ 74,520 rows | data-v0.2.0 ✅ | [`/concordance/dict/`](https://github.com/gasyoun/kosha/blob/main/concordance/dict/index.html) ✅ | **complete** |
| Q2 | B3 parallel passages | `parallel-passage-concordance` ✅ 153,045 · `bloomfield-rv-citations` ✅ | data-v0.2.0 ✅ | [`/concordance/parallels/`](https://github.com/gasyoun/kosha/blob/main/concordance/parallels/index.html) ✅ | **complete**, one `@DECIDE` open (R-C2 variant) |
| Q3 | A3 morphology audit | `morphology-attestation-audit` ✅ 401,368 · `morphology-attestation-audit-inflections` ✅ 239,443 · `morphology-giveback-candidates` ✅ 5,656 | data-v0.2.0 ✅ / unreleased ×2 | `/concordance/morphology/` ❌ | **data complete, web page + give-back hand-off owed** |
| (Q3 slot) | A4 Pāṇini *(promoted, D1)* | `panini-derivation-status` · `paninian-corpus-concordance` 893,482 · `paninian-sutra-coverage-map` | data-v0.3.0 ✅ | [`/concordance/panini/`](https://github.com/gasyoun/kosha/blob/main/concordance/panini/index.html) ✅ | **complete**, W4a polish open |

### Q4 (months 10–12) — A4 · Pāṇinian sūtra ↔ corpus  ·  *flagship, highest novelty*

**Calendar-slot correction (01-09-2026, H3782).** A human ruling of 17-07-2026 (D1 in
[`docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md`](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md))
**promoted A4 into the Q3 calendar slot, ahead of A3**. That plan states the roadmap's own
A4 section "should be re-labelled in the same pass that this plan lands, so a third naming
does not appear" — **the re-labelling never happened**, and this file has read "Q4 = A4"
against a shipped-in-Q3 reality ever since. The workstream label **A4** is correct; the
quarter is not. A4 shipped W2a–W3b between 20-07 and 24-07-2026 and released in
[data-v0.3.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.3.0).

- **Inputs:** vidyut-prakriya derivations (emit the Aṣṭādhyāyī sūtra chain per form), the Q3 attested-form join.
- **Build:** for each attested form, run the vidyut derivation, capture the sūtra sequence, invert to `sūtra → {attested forms exemplifying it}`. A concordance keyed by sūtra number — **unpublished territory: no corpus-grounded Pāṇinian concordance exists.**
- **Deliverables:** dataset `paninian-corpus-concordance` (manifest row + release) · web page `/concordance/panini/` (click a sūtra → its attested corpus exemplars, scan-anchored).
- **Exit checks:** a sūtra-coverage map (which of ~4,000 sūtras have real corpus exemplars, which are "dark"); sampled human verification that the derivation chain is correct for N forms; derivation-metadata license settled (see @DECIDE).
- **W2a (derivation harness) DONE 20-07-2026 (Sonnet 5 `claude-sonnet-5`, H1368).** [`scripts/build_panini_derivations.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_panini_derivations.py) ran the FULL 401,368-row W1b AG bucket (pilot 10k reported first per exit-check 2a-1, then the full run — 883.8s, 454.1 forms/s, well under the 40-min scaling cap): `ok` 72,764 (18.13%) · `no-derivation` 237,447 (59.16%) · `ambiguous` 86,857 (21.64%) · `engine-error` 4,300 (1.07%); 2,815 distinct sūtra chains, length min 6 / median 12 / max 37. Full detail + 30-example sampled human-verification section: [`data/concordance/DERIVATION_HARNESS_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/DERIVATION_HARNESS_BUILD_REPORT.md).
- **W2b (invert to the sūtra concordance) DONE 20-07-2026 (Sonnet 5 `claude-sonnet-5`, H1390).** [`scripts/build_panini_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_panini_concordance.py) inverts W2a's `ok`-status forms (chain data verified absent for `ambiguous` forms — see gap note below) into `data/concordance/paninian_concordance.tsv`: **893,482** `(sūtra, form, locus)` rows, **221** distinct sūtras with a corpus exemplar across **7** of the 8 adhyāyas (adhyāya 5: none — a "dark" adhyāya for A4, pending W3a's full dark-class map), chain length min 6 / median 12 / max 36 (Ashtadhyayi-only steps). Per-sūtra ambiguity rate (2b-6, lemma-attributed): median 27.1%, range 0.0–69.2%, `data/concordance/panini_ambiguity_by_sutra.tsv`. Web page: [`concordance/panini/index.html`](https://github.com/gasyoun/kosha/blob/main/concordance/panini/index.html) (adhyāya-sharded `kwic_<1-8>.js`, chain view + a lit-only coverage preview). **PARKED GAP:** exit-check 2b-1's literal wording ("`ok`/`ambiguous` forms") could not be satisfied for `ambiguous` rows — W2a's shipped `derivation_status.tsv` records an empty `chain_id` for all 86,857 `ambiguous` rows (verified exhaustively), diverging from ARCHITECTURE §4's stated "records all of them" design; inverting them would require re-deriving with vidyut, out of scope for a build whose input is W2a's output. Full detail: [`data/concordance/PANINI_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/PANINI_BUILD_REPORT.md). **W3a (sūtra-coverage/dark-sūtra map) DONE 24-07-2026 (Grok 4.5 `grok-4.5` on Opus-lock override, H1468).** [`scripts/build_sutra_coverage_map.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sutra_coverage_map.py) classifies the named **vidyut 0.4.0** Aṣṭādhyāyī enumeration (**n = 3983**, never "~4,000") into four statuses: **`lit` 221** (5.55%) · **`dark-unattested` 55** (1.38%) · **`dark-out-of-scope` 3707** (93.07%) · **`dark-engine-gap` 0** (W2a records no partial rule traces on `engine-error` — class kept named, not inflated). Fire-set = 276 codes that appear in any successful AG-lemma cell `vidyut.prakriya` history (91,027 lemmas harvested). Map: [`data/concordance/sutra_coverage_map.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/sutra_coverage_map.tsv); report: [`SUTRA_COVERAGE_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/SUTRA_COVERAGE_BUILD_REPORT.md). VERIFICATION 3a-1…3a-8. **W3b (manifest row + public release) DONE 24-07-2026 (Grok 4.5 `grok-4.5` on Sonnet-lock override, H1574).** Rights gate W1a verified. Data statements under [`docs/data-statements/`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/) for `panini-derivation-status`, `paninian-corpus-concordance`, `paninian-sutra-coverage-map`. Flipped `in_release` → **`data-v0.3.0`** (CC BY-SA 4.0 A4 composition). Release: [data-v0.3.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.3.0). **W4a (`/concordance/panini/` polish) is next.**

---

## Cross-cutting

**Dependencies (build order is load-bearing):** the concordance core (Q1) is a hard
prerequisite for Q2–Q4. Q4 depends on Q3's attested-form join. Per the kosha data
rule, running a later stage against a stale earlier one produces silently wrong
output, not an error.

**Risks:**
- **R-C1** Pan-corpus matching noise (B1's 18.6% residue) — accepted as unfilled per D6 (strict-tier-only, no relaxed/fuzzy); reported honestly in build report and manifest, never silent.
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

## Related documents (awareness weave H1728)

**Name collision — different programme.** Uprava grammar/non-grammar concordance is *not* this file:

- Uprava: [CONCORDANCE_ROADMAP_GRAMMAR_NONGRAMMAR_2026_2027.md](https://github.com/gasyoun/Uprava/blob/main/CONCORDANCE_ROADMAP_GRAMMAR_NONGRAMMAR_2026_2027.md) — VedaWeb/Type-D grammar join
- This kosha file — pedagogical/corpus concordance surfaces over DCS/lemma data


_Dr. Mārcis Gasūns_
