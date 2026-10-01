# Sanskrit Concordance Program — 1-Year Roadmap

_Created: 08-07-2026 · Last updated: 06-09-2026_

> **Truth-pass 27-08-2026** (Grok 4.6 `grok-4.6`). D4 addendum: this file joined the Wave 1 FLAG list after 21-08. Closed references checked against the combined registry. Kept in place ([FINDINGS §475](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md) clause 3). Not archived.
>
> **Exit-check truth-pass 02-09-2026** (Claude Code Opus 5 `claude-opus-5`, H3783). The Q4/A4 **exit-check** bullet and open-`@DECIDE` 1 still read as unbuilt six weeks after the work shipped and was released, and a handoff was minted from that prose. Both are corrected below with per-check evidence. The lesson, in this file: a truth-pass that checks a section's **status line** has not checked its **exit checks, risks and `@DECIDE` list** — those are separate claims, and they are the ones a later `/fruit` or `/ask` pass reads to decide what is still open ([FINDINGS §644](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md)).

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
  `inflections` holds **6,930,902 rows / 3,333,034 distinct `form_slp1`** (re-measured
  06-09-2026 against the `kosha.db` rebuilt on 04-09-2026 — 1,732.3 → 1,767.5 MB; the
  H3782-vintage figures were 6,917,018 / 3,326,312), of which
  **99.99% are `source='cologne_mwinflect'`** (plus 326 `hybrid-natva-fix`, 153
  `curated-gita-pronoun`, 17 `vidyut-gap-fill`). vidyut's actual output lives in the
  separate `forms` table (28,567 rows). The two tables are different generators and the
  audit means different things on each.
- **Build:** join generated forms ⨯ attested forms on `form_key()` into three buckets — **attested & generated** (confirmed), **generated-never-attested** (over-generation), **attested-never-generated** (engine/grammar gaps). Absorbs A1 (root→forms) and A2 (paradigm-token→attestation). ⚠ handle the manifest-noted **DCS `Tense=Past` aorist/perfect conflation** in verb buckets.
- **Deliverables:** dataset `morphology-attestation-audit` (manifest row ✅ + released ✅ in
  [data-v0.2.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.2.0), asset
  `morph_attest_AG.tsv`) · dataset `morphology-attestation-audit-inflections` (manifest row
  ✅ 01-09-2026, unreleased — rides the next data cut) · web page
  [`/concordance/morphology/`](https://github.com/gasyoun/kosha/blob/main/concordance/morphology/index.html)
  (paradigm cell → attested? with corpus evidence) — **✅ BUILT 02-09-2026 (H3861).**
  Every generated cell of a lemma is rendered as a case × number grid per gender, marked
  attested or not against DCS, with occurrence counts, citable `dcs:<sent_id>` loci and KWIC;
  below it, the forms DCS attests that the generator never produced. Static head = the
  **measured** 95% token-coverage set (N=11,148 lemmas, 9,150 of them carrying generator rows
  — measured at build time per standing rule D4/D5, never hardcoded), 370,805 cells of which
  174,894 (47.17%) attested. The audit's two controls are rendered, not footnoted: gap lists
  state how many of their rows are verbal (out of scope: 680 verbal lemmas against 222,737
  nominal) or sandhied-surface-only, and the trust block explains that homographic cells
  share one `form_key` evidence count. Builder:
  [`scripts/build_morphology_concordance_page.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_morphology_concordance_page.py);
  invariants in
  [`tests/test_morphology_page.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_morphology_page.py).
  **Q3 now has no deliverable without an artefact behind it.**

#### The two joins, and why the second one had to exist

| | W1b (H1262, 18-07-2026) | H3782 (01-09-2026) |
|---|---|---|
| Generated side | `forms`, heritage excluded — 426,410 rows | `inflections` — 3,333,034 distinct forms |
| Generator | 93.3% `source='dcs'` + 28,567 vidyut | 99.99% `cologne_mwinflect` |
| Attested side | `token.form` (sandhied) — 381,413 | `token.form` **+** `token.m_unsandhied` — 352,112 keys |
| **AG** | 401,368 of 426,410 (94.1%) | **239,189 of 3,333,034 (7.18%)** |
| **G¬A** | 25,042 | **3,093,845 (92.82%)** |
| **A¬G** | **2** | **163,058 of 352,112 (46.31%)** |

The H3782 column carries the numbers from the **06-09-2026 rebuild** (H3975, sanskrit-util
0.12.0, over the `kosha.db` rebuilt 04-09-2026); the two key fixes and what each one moved
are in the tables below.

The W1b A¬G of **2** is not a finding about Sanskrit morphology; it is an artefact of
joining DCS against a generated side that is itself 93% ingested DCS. That build's own
report says so and hands the question on. The `inflections` side is derived from MW
headwords with no DCS input, so it is the only one of the two on which
"attested but never generated" carries engine meaning — and there the corpus half of the
asymmetry is **163,058 keys, not 2**.

#### The join key was broken, and what fixing it moved

The first run of this join (H3782) used a `form_key()` that folded anusvāra to `n` at **every**
position while never touching a literal `m`, so `rasaṃ` → `rasan` but `rasam` → `rasam`: **the
two standard spellings of a Sanskrit word-final nasal could never collide**, and every
anusvāra-final attestation read as un-generated. Fixed in
[sanskrit-util 0.11.0](https://github.com/sanskrit-lexicon/sanskrit-util/pull/72) — word-final
anusvāra now folds to `m`, the medial fold is unchanged (`saṃskṛta == sanskṛta`), and final
`-n` stays distinct from final `-m` (`rājan != rājam`). The whole A3 chain was then re-run
against the fixed library (H3925, 02-09-2026). The pre-fix column is kept so the size of the
defect stays visible:

| | pre-fix key (H3782) | fixed key 0.11.0 (H3925) | Δ |
|---|---:|---:|---:|
| distinct attested keys | 386,012 | **352,745** | −33,267 |
| **AG** (generated view) | 239,443 | **238,312** | −1,131 |
| **G¬A** | 3,086,869 | **3,088,000** | +1,131 |
| **AG** (attested view) | 189,634 | **188,509** | −1,125 |
| **A¬G** | 196,378 | **164,236** | **−32,142 (−16.4%)** |
| attested-side coverage | 49.13% | **53.44%** | +4.31 pp |

Two things are worth reading off this table rather than assuming. First, the correction is
**larger than the 24,149 the sampled estimate predicted**: that sample could only see rows
whose anusvāra twin was already inside the candidate set, so it was a floor, not a forecast.
Second, the fix is a **re-partition, not a monotone gain** — folding final `-ṃ` onto `-m`
also *breaks* matches that existed only because final `-ṃ` and final `-n` were conflated, and
the net effect on the generated view is −1,131 forms. The coverage rise is likewise partly a
denominator effect: 33,267 of the old "attested keys" were spelling twins of each other, not
distinct words. The AG / G¬A split and every conclusion drawn from the audit's *direction*
are unchanged.

#### The same defect one position inward — fixed 06-09-2026, and measured against a control

The 0.11.0 fix was word-final only, and the `orthographic-variant` detector emptying to 0
read like completeness. It was not. *Homorganic* is a **place of articulation**, so anusvāra
before a labial (`p ph b bh m`) is phonetically /m/ as well: under 0.11.0 `vaiśaṃpāyana` keyed
as `vaiśanpāyana` and could never meet the `vaiśampāyanaḥ` the generator already emits.
Measured on the one class that reaches a human — the 2,521 `slot-conflict` rows —
**278 (11.03%, 11.58% by corpus weight) were not disagreements at all**: `saṃbhavaḥ` vs
`sambhavaḥ`, `saṃbandhaḥ` vs `sambandhaḥ`, `samyaksaṃbuddhaḥ` vs `samyaksambuddhaḥ`, with a
further 90 candidates that collapse into their own lemma once refolded.
[sanskrit-util 0.12.0](https://github.com/sanskrit-lexicon/sanskrit-util/pull/75) (H3975)
narrows the medial fold to labials only — `saṃskṛta == sanskṛta`, `saṃvatsara → sanvatsara`
(`v` is not a labial stop) and `ṅ/ñ/ṇ` are all unchanged — and this chain is rebuilt on it.
**Both counts are now 0**, and
[`scripts/measure_medial_anusvara_residual.py`](https://github.com/gasyoun/kosha/blob/main/scripts/measure_medial_anusvara_residual.py)
is the standing PASS/FAIL regression check for that rather than a one-shot measurement.

⚠️ **A raw before/after diff would misreport this, and the roadmap deliberately does not quote
one.** `kosha.db` was itself rebuilt on 04-09-2026 (1,732.3 → 1,767.5 MB; distinct generated
forms 3,326,312 → 3,333,034), so the 02-09 figures differ from today's for two reasons at
once. The key effect was isolated instead with a **control arm**: the identical audit, over
the identical inputs, with a pinned 0.11.0 checkout of sanskrit-util. Both directions, as
§626 requires:

| | control — 0.11.0 | treatment — 0.12.0 | Δ |
|---|---:|---:|---:|
| distinct attested keys | 352,745 | **352,112** | −633 |
| **AG** (generated view) | 238,466 | **239,189** | **+723** |
| **G¬A** | 3,094,568 | **3,093,845** | −723 |
| **AG** (attested view) | 188,509 | **189,054** | +545 |
| **A¬G** | 164,236 | **163,058** | **−1,178 (−0.72%)** |
| attested-side coverage | 53.44% | **53.69%** | +0.25 pp |

**1,178 keys left A¬G; 0 entered** — measured as a set diff of the two arms' A¬G key lists,
not inferred from the totals. It reconciles exactly: 633 of the leavers stopped being distinct
keys at all (they merged into their `m`-spelled twin, which is the denominator change) and 545
became matched. **Unlike the 0.11.0 fix, this one is monotone**: the final-position fold had to
break 1,131 generated matches that existed only because final `-ṃ` and final `-n` had been
conflated, whereas nothing rides on the `-ṃp-`/`-mp-` contrast — a loss here would require an
attested form spelled with a literal `-nb-`/`-np-`/`-nm-`, which Sanskrit orthography does not
produce. That is the phonological reason the two positions behave differently, and it is why
the direction had to be measured rather than assumed.

The control arm is not free: it cost one whole 7-minute run to a silent failure first, because
kosha's `concordance_core.py` did its own `sys.path.insert(0, …)` at import time and shadowed
the pinned checkout, so both arms loaded 0.12.0 and agreed to the byte. That module now honours
`GITHUB_ROOT`. Evidence and method:
[`data/concordance/evidence/H3975_CONTROL_ARM_KEY_ISOLATION.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/evidence/H3975_CONTROL_ARM_KEY_ISOLATION.md);
process lesson: [Uprava FINDINGS §715](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md).

⚠ **The A¬G residue is not 163,058 engine defects.** The generator's lemma inventory is
**222,737 nominal lemmas against 680 verbal**, so finite verbs are territory
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
  **5,224 rows**, from `paradigm_gap`'s 69,881 by three measured subtractions (verbs 23,935 ·
  sandhied-surface-only 40,165 · bare stems 557). Quoting A¬G as "forms the engine misses"
  overstates the actionable set **31×**. The head cross-validates (pronoun dative/locative
  cells and irregular feminine/consonant stems — precisely where MW-inflect is weak, and
  `inflections` already carries a hand-made `curated-gita-pronoun` patch).

  **The candidate set has since been triaged cell-by-cell (H3863), and it is machine-decidable.**
  DCS's own morphological tagging resolves 5,223 of the 5,224 rows: **4,900 are owed**
  (slot-conflict 2,212 — the engine fills that paradigm cell with a different form, and every one
  of them is now a real disagreement: the medial-anusvāra twins no longer reach A¬G at all;
  coverage-hole 2,688 — the cell is empty) and **323 are not** (compound-member, lexicon-gap,
  indeclinable), with a single untagged residue. That triage is also the cleanest evidence
  the key fixes landed: the `orthographic-variant` verdict — the class that existed solely to
  catch anusvāra twins the broken key had split — matched **146 rows before the rebuilds and 0
  after**, and the medial-labial twins it could not see went **278 → 0** on the same evidence,
  because those forms no longer reach A¬G at all. Full method, the corrected `rājñ`
  reading and the dominance rule that separates a bound stem from a missing cell:
  [`MORPHOLOGY_GIVEBACK_TRIAGE_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/MORPHOLOGY_GIVEBACK_TRIAGE_REPORT.md).
  Routing it is a queued port, never an in-pass csl-inflect edit.

#### Q1–Q3 status, verified mechanically 01-09-2026 (H3782)

| Quarter | Workstream | Dataset | Release | Web page | Verdict |
|---|---|---|---|---|---|
| Q1 | B1 dict ↔ corpus | `dict-corpus-concordance` ✅ 74,520 rows | data-v0.2.0 ✅ | [`/concordance/dict/`](https://github.com/gasyoun/kosha/blob/main/concordance/dict/index.html) ✅ | **complete** |
| Q2 | B3 parallel passages | `parallel-passage-concordance` ✅ 153,045 · `bloomfield-rv-citations` ✅ | data-v0.2.0 ✅ | [`/concordance/parallels/`](https://github.com/gasyoun/kosha/blob/main/concordance/parallels/index.html) ✅ | **complete**, one `@DECIDE` open (R-C2 variant) |
| Q3 | A3 morphology audit | `morphology-attestation-audit` ✅ 401,368 · `morphology-attestation-audit-inflections` ✅ 239,189 · `morphology-giveback-candidates` ✅ 5,224 | data-v0.2.0 ✅ / unreleased ×2 | [`/concordance/morphology/`](https://github.com/gasyoun/kosha/blob/main/concordance/morphology/index.html) ✅ | **complete** (H3782 data + H3861 page + H3863 triage, all rebuilt on the narrowed join key in H3975); give-back hand-off owed |
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
- **Exit checks — all three met; verified line by line 02-09-2026 (H3783).** This bullet
  read as open prose for six weeks after the work shipped, and that is what minted a
  duplicate handoff ([FINDINGS §644](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md)
  class: a follow-on sentence under a ✅ row is a separate claim from the status column).
  Each check with the artefact that satisfies it:
  1. **Sūtra-coverage map ✅** — W3a, 24-07-2026 (H1468,
     [PR #180](https://github.com/gasyoun/kosha/pull/180)).
     [`data/concordance/sutra_coverage_map.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/sutra_coverage_map.tsv)
     classifies the **named** enumeration (vidyut 0.4.0 `Source.Ashtadhyayi`,
     **n = 3983** — the map never publishes "~4,000" as if exact) into `lit` 221 ·
     `dark-unattested` 55 · `dark-out-of-scope` 3707 · `dark-engine-gap` 0. Methodology,
     per-class assignment rule and reproduction command:
     [`SUTRA_COVERAGE_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/SUTRA_COVERAGE_BUILD_REPORT.md).
  2. **Sampled verification of the derivation chains ✅ built, human sign-off not recorded**
     — W2a's report renders **30 `ok` chains** in full (lemma → attested form, every sūtra
     step with its intermediate string) as exit-check 2a-7:
     [`DERIVATION_HARNESS_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/DERIVATION_HARNESS_BUILD_REPORT.md)
     § *Sampled human-verification*. Honest residual: the report states neither **why N = 30**
     nor a human's verdict on the 30 — it is a rendered sample awaiting sign-off, not a
     recorded audit. Tracked as a human `@DO` in
     [Uprava GTD](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md); no agent
     can close it by re-reading the same chains.
  3. **Derivation-metadata licence settled ✅** — 18-07-2026 (H1263), *before* the release,
     in [`data/manifest/rights/vidyut_prakriya_derivation_2026-07.md`](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/vidyut_prakriya_derivation_2026-07.md):
     vidyut **code** MIT and vidyut **derivation data** MIT are verified as two separate
     artefacts from two separate files, DCS resolved to CC BY 4.0 from Hellwig's own terms,
     and A4 output ships **CC BY-SA 4.0** because CDSL's ShareAlike binds regardless. That
     record's own § *Human gate — not triggered* states the reason no `@DECIDE` is owed:
     neither incompatibility branch occurred. See @DECIDE 1 below.
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
1. ~~**License composition** — B1/B3 join DCS (CC BY 4.0) → concordances inherit BY-SA cleanly; but A4 embeds vidyut-prakriya derivation metadata — confirm the derivation output's license before the A4 release.~~ **RESOLVED 18-07-2026 (H1263), five days before the A4 release** — [`data/manifest/rights/vidyut_prakriya_derivation_2026-07.md`](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/vidyut_prakriya_derivation_2026-07.md) verifies vidyut code (MIT, installed `LICENSE.md`) and vidyut derivation data (MIT, `vidyut-prakriya/data/README.md`) as two separate licences, corrects kosha's own DCS contradiction to CC BY 4.0 from the primary source, and rules A4 output **CC BY-SA 4.0** with vidyut + DCS attribution. Its § *Human gate — not triggered* records why no human decision is owed. Carried into all three data statements and released in [data-v0.3.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.3.0). This line stood open for six weeks after the fact and was quoted back as an open `@DECIDE` by handoff H3783 (02-09-2026).
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
