# Changelog

All notable changes to the Gasuns Sanskrit Dictionary (kosha) are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is
[SemVer](https://semver.org/). Keep upcoming work under [Unreleased], then **cut a new
version every time the changelog is updated** (promote [Unreleased] to the next `x.y.z`
with today's date, tag `vx.y.z`, publish a GitHub release — same pass).

Two version tracks, do not conflate: **repo releases** (`vX.Y.Z` tags, this file) cover
code + docs; **data releases** (`data_version` in `kosha.db` meta, shipped as release
assets from P1 on) are versioned separately per
[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md) §A2 —
sense citations pin to `data_version`, not to repo tags.

## [Unreleased]

### Added

- **Wave RU staged in the pedagogy plan** ([`docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE_RU.md`](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE_RU.md),
  via [`/ask-batch`](https://github.com/gasyoun/claude-config/blob/main/commands/ask-batch.md), Fable 5 `claude-fable-5`):
  W-RU-a inline Sa→Ru gloss layer over reading packs
  ([H1278](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1278-Opus_kosha_pedagogy-wave-ru-inline-gloss-reader_19.07.26.md), queued)
  and W-RU-b graded beginner subhāṣita reader from Indische Sprüche
  ([H1279](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1279-Fable_kosha_pedagogy-wave-ru-subhashita-reader_19.07.26.md), queued);
  roadmap/plan/verification docs extended with the wave, decisions 13–14 (RU wave + rights gate) recorded.

## [0.61.0] - 2026-07-18

### Added

- `data/manifest/rights/vidyut_prakriya_derivation_2026-07.md` — the A4-gating rights record
  (W1a / [H1263](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1263-Opus_kosha_vidyut_derivation_metadata_rights_record_18.07.26.md)):
  vidyut **code** licence (MIT, from the installed `LICENSE.md`) and vidyut **derivation-data**
  licence (MIT, from `vidyut-prakriya/data/README.md` via ashtadhyayi.com; source sūtra/dhātu
  texts public domain) stated **separately**, each with its source file; the composition ruling
  for A4 output (**CC BY-SA 4.0, vidyut attributed**, ShareAlike inherited from CDSL). No `@DECIDE`
  triggered — both licences compose cleanly into BY-SA.
- `scripts/build_morphology_attestation_audit.py` + `data/concordance/morph_attest_{AG,GnA,AnG}.tsv`
  + `data/concordance/MORPHOLOGY_ATTESTATION_BUILD_REPORT.md` — **A3, the generated-vs-attested
  morphology audit** (Concordance-Q3 W1b, [H1262](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1262-Opus_kosha_a3_attested_form_join_morphology_audit_18.07.26.md)).
  Joins `kosha.db` `forms` (non-heritage, 426,410 rows) against DCS attested surface forms (381,413
  distinct) on `form_key()` equality (length-preserving floor tier; no NFD+strip path): **AG 401,368
  / G¬A 25,042 / A¬G 2**, both denominators reconciled. Manifest row `morphology-attestation-audit`
  added (`in_release: unreleased` — publication gated on the W1a rights record, H1263 / D2).
- **Key finding (the artefact A4 cannot start without, D12):** 93.30% of the generated side is
  itself DCS-derived, so full-set AG is a 99.99% round-trip — the **vidyut-engine subtotal (AG
  3,550 / 28,567 = 12.43% attested)** is the only research-meaningful figure, and A¬G is degenerate
  (=2) and cannot measure engine gaps here. Reported the `forms`-vs-`inflections` (1.38M vs 6.9M)
  plan-set contradiction (STOP-AND-SURFACE, not resolved) — see
  [SanskritLexicography CONTRADICTIONS §6 / FINDINGS §94](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md).
  Read-only build; no data release cut.

### Fixed

- **DCS licence contradiction resolved from Hellwig's own published terms.** DCS's
  [`dcs/data/conllu/readme.md`](https://github.com/OliverHellwig/sanskrit/blob/master/dcs/data/conllu/readme.md)
  states the CoNLL-U data is **CC BY 4.0**; `data/manifest/external_tools.json` (`id: dcs`) was the
  outlier at CC BY-SA 4.0 and is corrected to **CC BY 4.0** (with a `license_source` citation).
  `CONCORDANCE_ROADMAP.md`:151 and the 14 `datasets.json` assertions were already correct and left
  unchanged (the unrelated Gita Supersite BY-4.0 mention deliberately untouched). Added
  `bundled_data_license`/`bundled_data_provenance` to the `vidyut` manifest row; marked the two
  resolved rows in `ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md` §7.

## [0.60.0] - 2026-07-18

### Added

- `docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md` + its `.meta.md` — the Concordance Q3 (Pāṇini /
  derivation chains) plan index, with the decisions-taken table for the 18-07-2026 rulings and the
  autonomy contract. Wave-1 handoffs H1262–H1267 (all 🟡 queued).
- `docs/ROADMAP_KOSHA_2026H2.md` + its `.meta.md`, `docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md`,
  `docs/IMPLEMENTATION_KOSHA_CONCORDANCE_Q3.md`, `docs/VERIFICATION_KOSHA_CONCORDANCE_Q3.md` —
  the rest of the layered plan set, authored by the `/ask-batch` 2026-07 slice-2 pass.

### Changed

- Recorded four corrections the authoring + adversarial-verify passes measured against the repo:
  A3 (the attested-form join A4 depends on) **does not exist** and is absorbed into wave 1;
  all 77 manifest rows already carry `in_release` (the field missing from 38 is `release_asset`),
  so the defect is an undefined vocabulary rather than an absent field; the static-head cutoff is
  **N = 11,148** for exactly 95.00% of 4,550,704 corpus tokens; and 402 + 477 MB = 879 MB is 86% of
  the Pages cap rather than an overflow, so the head/tail split stands on headroom grounds.

## [0.59.0] - 2026-07-15

### Added
- **H951: per-verse metre annotation over the reading packs — Wave 3 pedagogy (W3a).**
  The field (§3.9) names "metre-ID wired into reading" as a gap. This ships the **data
  layer** for it and **no UI** — SanskritKaraoke owns the metre trainer (scope re-checked
  15-07, unchanged); kosha's contribution is the corpus-grounded per-verse annotation those
  tools lack (the ARCHITECTURE integration-surface rule). `scripts/build_reading_pack_metre.py`
  annotates every reading-pack sentence via **`vidyut.chandas`** (the real metre classifier,
  over a vendored `data/vidyut/chandas/meters.tsv`) with an honest two-tier + null method:
  strict vṛtta (`method=vidyut-chandas`, high confidence, **≥8-syllable guard** so a prose
  heading can't spuriously match); anuṣṭubh (`method=syllable-heuristic`, medium — vidyut
  doesn't classify the loose śloka, but the DCS sentences align to half-ślokas, and **all
  840 anuṣṭubh tags land at exactly 16 syllables** = 2 pādas); everything else left
  **unresolved with an empty metre** (prose, speaker-tags, fragments — never guessed).
- **Coverage: 89% identified** (12% strict vṛtta + 77% anuṣṭubh) across 1,095 sentences /
  23 packs, **11% honestly unresolved**. Validation anchor: Bhāravi's Kirātārjunīya-1 scans
  **92/92 as vaṃśastha** — correct for that canto. Outputs: `data/metre/reading_pack_metre.tsv`
  (per-sentence: metre, type, method, confidence, syllables) + `metre_coverage.tsv` (per-pack
  distribution). Two `datasets.json` rows (`reading-pack-metre`, the vendored
  `vidyut-chandas-meters`), `vidyut` added to `requirements.txt`, and 9 tests (no fabricated
  metre, ≥8-syllable vṛtta guard, anuṣṭubh pāda-alignment, Kirātārjunīya-all-vṛtta anchor,
  coverage-sums-match, non-SLP1-doesn't-crash). Deterministic. Build: Opus 4.8 (`claude-opus-4-8[1m]`).

## [0.58.0] - 2026-07-15

### Added
- **H972 — defgen eval, F1_fable_ctx arm (15-07-2026, Fable 5 `claude-fable-5`)**: the
  non-DeepSeek model family called for by the protocol's next-steps #6, generated
  in-session by the Claude Code session itself over a **gold-free inputs projection**
  (next-steps #7a; new [`scripts/defgen_fable_arm.py`](https://github.com/gasyoun/kosha/blob/main/scripts/defgen_fable_arm.py)
  emit/assemble, so the MW gold gloss is structurally absent from the generation
  context). 500/500 items, scored with the existing H730 harness (`defgen_score.py`
  ARMS extended) and judged blind by `deepseek-chat`. **F1 leads every arm on every
  metric**: corpus chrF 24.35 (+4.78 over A1), token-F1 0.340, BLEU 5.14, judge
  adequacy 4.60 (floor separation intact, judge~chrF ρ 0.415); mean gloss length 17.1
  words, so the lead is content, not verbosity. Frequency-gradient inversion and
  polysemy penalty replicate. Full numbers + caveats (in-session arm is a strong-model
  reference point, not a reproducible baseline):
  [`docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md`](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md);
  manifest row `mw-defgen-eval-sample` updated.

## [0.57.0] - 2026-07-15

### Added
- **H977: reduced 3-axis difficulty ordering for the 18 Gītā reading packs — W2a follow-up.**
  W2a (v0.55.0) shipped the difficulty scorer but **skipped the 18 Gītā packs**: their builder
  (`build_reading_pack_gita.py`) emits no UD morphology, so scoring them on the 4 axes would
  fabricate the morphology + compound loads. This closes that gap the honest way. The Gītā
  packs do carry three signals of their own (verified: 100 % a lemma via `slp1`, 37.5 % a
  populated per-token `sandhi` field, 24.9 % a hyphenated compound lemma), so
  `scripts/build_difficulty_scorer.py` gained `score_pack_reduced`:
  `difficulty_reduced = w_vocab·VOCAB + w_sandhi·SANDHI + w_compound·COMPOUND` — the morphology
  weight dropped and the other three renormalised. VOCAB = rarity of **non-compound** content
  lemmas (compounds excluded so they are not double-penalised as unknown-rare); SANDHI =
  fraction of tokens carrying the pack's **own induced junction rule** (a real signal, *not*
  the 4-axis boundary proxy); COMPOUND = hyphen-lemma share.
- **Shipped as a SEPARATE ordering, explicitly not comparable to the 4-axis packs** (R5/R6
  honesty carries over): different axis set *and* a different sandhi definition, so the 18
  Gītā chapters are ranked **among themselves** only. New `data/difficulty/gita_reading_pack_difficulty.tsv`
  (+ `.json`), a labelled section on `reading/difficulty/index.html`, an extended
  `data/difficulty/METHODS.md`, a `gita-reading-pack-difficulty` manifest row, and 5 new tests
  (all 18 scored, reduced axes in range + ascending, composite == reduced formula with no
  morphology term, Gītā packs never leak into the 4-axis table, no double-count of compounds).
  The 4-axis UD ordering (5 packs) is unchanged. Build: Opus 4.8 (`claude-opus-4-8[1m]`).

## [0.56.0] - 2026-07-15

### Changed
- **W2a follow-through: pedagogy-surfaces roadmap marked shipped ([#116](https://github.com/gasyoun/kosha/pull/116)).**
  [`docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md)
  still showed `🟢 BUILD` / `🟡 REUSE` verdicts for six surfaces that had all shipped;
  flipped them to `✅ SHIPPED vX.Y.Z` **preserving the build-vs-reuse design intent**
  (W1a v0.54.0 · W1b v0.51.0 · W1c v0.52.0 · W2a v0.55.0 · W2b v0.50.0), marked W3a
  **UNBLOCKED** (next; consumes the W2a reading packs), and ticked the Wave 1 + Wave 2
  headings ✅ to match Wave 0.

### Added
- **Companion metadoc for the pedagogy-surfaces roadmap ([#117](https://github.com/gasyoun/kosha/pull/117)).**
  New [`docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.meta.md)
  (the last genre-named doc in the pedagogy set lacking one): purpose · audience ·
  provenance (H945, `/ask`) · status table (Waves 0–2 shipped, W3a unblocked) · ranked
  improvement backlog (flip W3a on ship — the §84 stale-row lesson applied to roadmaps;
  W2a weighting ruling; the 18 unscored Gītā packs) · limitations · revision history.
  Registered in [`Uprava/METADOCS_INDEX.md`](https://github.com/gasyoun/Uprava/blob/main/METADOCS_INDEX.md).

### Fixed
- **Two kosha pedagogy metadocs aligned to template-v2 ([#118](https://github.com/gasyoun/kosha/pull/118)).**
  The roadmap metadoc and the [`reading-pack-difficulty`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/reading-pack-difficulty.meta.md)
  data statement scored 0/3 on the org census's template-v2 check; added the three
  required sections — `## Intended use / known misuse` (carrying the R5 one-estimator and
  R6 build-status-≠-learning-gain caveats), `## Maintenance & sunset plan`, and
  `## Deprecation status` (`active`) — both now 3/3 (org v2 coverage 62/126 → 64/127).

## [0.55.0] - 2026-07-15

### Added
- **H949: reading-pack difficulty scorer — Wave 2 pedagogy (W2a), the difficulty spine.**
  The field (§3.4/§6) names a text-difficulty scorer as a gap; this scores every
  UD-annotated kosha reading pack on four corpus-grounded axes and orders them into a
  graded reading sequence (easiest first). `scripts/build_difficulty_scorer.py`:
  `difficulty = w_vocab·VOCAB + w_sandhi·SANDHI + w_morph·MORPH + w_compound·COMPOUND`,
  each axis a per-token load in [0,1] — **VOCAB** = mean corpus-rarity of content lemmas
  (from `lemma_frequency.tsv`, the W1b signal); **SANDHI** = fraction of word-boundaries
  fused by sandhi, measured off the pack; **MORPH** = mean surprisal of each token's
  `upos|morph` form over the 840 corpus signatures; **COMPOUND** = share of compound
  members (DCS `feat_case=Cpd`). The consumed morph signal is derived once by
  `scripts/build_difficulty_signals.py` (GROUP BY the UD morph features over the 5.69M-token
  DCS full sqlite → `data/difficulty/morph_signature_freq.tsv`, keyed byte-identically to
  how the reading packs display morph, so a pack token joins with no re-derivation), which
  keeps the scorer heavy-DB-free at score time — the same source→derive→consume split the
  sandhi programme uses.
- **W2a is ONE estimator, not "the" difficulty** (VERIFICATION R5). Weights live in
  `data/difficulty/difficulty_weights.json` (tunable — **a human should confirm**; defaults
  vocab 0.40 · sandhi 0.20 · morphology 0.25 · compound 0.15) and the formula + honest
  limitations (frequency ≠ learnability R6; sandhi is a boundary-fusion proxy) are documented
  in `data/difficulty/METHODS.md`. Outputs: `reading_pack_difficulty.tsv`/`.json`, the graded
  page `reading/difficulty/index.html`, and a data statement
  `docs/data-statements/reading-pack-difficulty.meta.md`.
- **Four new reading packs beyond Nala 1, ordered by the scorer** (via the existing
  `build_reading_pack.py`, all UD-complete, 96–98 % card-linked): `nala-2` (MBh 3.51),
  `nala-3` (MBh 3.52), `hitopadesa-0` (Hitopadeśa opening), `kiratarjuniya-1` (Bhāravi).
  On the 5 scored packs the ordering validates the scorer — Kirātārjunīya (dense kāvya)
  is hardest (0.389) while the Nala narrative chapters + Hitopadeśa cluster near 0.32,
  the expected register gradient. The 18 Gītā packs are **skipped, not scored**: their
  builder (`build_reading_pack_gita.py`) emits no UD morphology, so scoring them would
  fabricate morph/compound loads — the scorer detects this (`ud_coverage < 0.5`) and logs
  the skip rather than inventing a number.
- Tests: `tests/test_difficulty_scorer.py` (axes + composite in range, composite equals the
  documented weighted sum, ascending-difficulty ordering, deterministic scoring, non-UD
  packs skipped-not-fabricated, kāvya-harder-than-epic sanity anchor). Six new
  `datasets.json` rows (`reading-pack-difficulty`, `morph-signature-freq`, the four packs).
  Build: Opus 4.8 (`claude-opus-4-8[1m]`).

## [0.54.0] - 2026-07-15

### Added
- **H946: morphology drills — Wave 1 pedagogy (W1a).** `scripts/build_morphology_drills.py`
  turns the P4 paradigm engine (`app/paradigm.py`) into graded, frequency-filtered,
  answer-keyed declension/conjugation drills — the novel move: drill only forms the
  corpus actually attests (field RQ1: "stop drilling forms that never appear"). New
  one-pass VisualDCS `dcs_full.sqlite` attestation join (`(lemma, form, morphology)` ->
  corpus locus/count; nominal case/gender/number map directly from DCS's UD tags, verb
  person/number/tense-mood collapse onto kosha's `pre`/`ipf`/`ipv`/`opt` vocabulary —
  voice is NOT part of the verb match key since DCS's `feat_voice` marks only passive,
  an honest upstream limitation, not a silent overclaim). Over the 5,985 core-vocabulary
  lemmas with entries: 38,782/254,805 candidate paradigm cells (15.2%) survived
  attestation. `data/morphology/morphology_curriculum.tsv` (7,134 paradigms, class-bucket
  ordered a-stems → other-vowel-stems → consonant-stems → pronouns → present-class-verbs
  → other per `drill_weights.json`, tunable not hard-coded) — learn 4,862 paradigms to
  cover 50% of attested nominal/verbal tokens, 6,351 → 80%, 6,708 → 90%.
  `data/morphology/drills.json` (12,000 fill/match items over the top 6,000 attested
  cells by frequency, `--max-drill-cells 0` for the full set) + `morphology_drills.apkg`
  (Anki, 6,000 notes, verified re-imports as a valid collection) +
  `reading/morphology/{curriculum,drills}/index.html` (self-contained, theme-aware,
  Devanāgarī/IAST/SLP1 toggle). `morphology-curriculum` + `morphology-drills` manifest
  rows. `tests/test_morphology_drills.py` (11 tests: every item answer-keyed and
  evidence-backed, no unattested form in default mode, coverage monotone, lesson-bucket
  ordering never regresses, Anki note count matches).

## [0.53.0] - 2026-07-15

### Added
- **H955: SRS deck — Rung B1 demo (last-mile pipeline).** `scripts/build_demo_srs_deck.py`
  emits `data/srs/srs-deck-b1-demo.json`: the content-word vocabulary of the existing
  `dcs-reading-pack-nala-1` (439 tokens), joined to `lemma_frequency.tsv` `core_rank`,
  function words stripped (`grammar_all` in `ind`/`pron`, the wave-1a method) — 164
  cards, `core_rank`-ordered. Proves [`docs/LAST_MILE_PIPELINE_SPEC.md`](https://github.com/gasyoun/SanskritGrammar/blob/main/docs/LAST_MILE_PIPELINE_SPEC.md)
  Hop B end-to-end on one concrete text (reader ↔ SRS deck share the same word set) —
  deliberately narrower than H947's general `vocab_curriculum.tsv` (6,667 lemmas, already
  shipped in 0.51.0), which it does not duplicate or supersede. `kosha-srs-deck-b1-demo`
  manifest row registered. Systema-side import lands separately (H955, Systema-Sanscriticum).

## [0.52.0] - 2026-07-15

### Added
- **H948: samāsa (compound) analysis trainer — pedagogy Wave 1, surface W1c.**
  [`scripts/build_samasa_trainer.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_samasa_trainer.py)
  applies the six-stage pedagogy contract
  ([ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md))
  to compound analysis: [`data/gita/gita_morphology_gold.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_morphology_gold.tsv)
  (815 hand-tagged Gītā compounds) as the verified-type gold seed, joined against
  the VisualDCS `Kompozity` compound dictionary (`cmps.csv` × `names.csv`,
  168,421 corpus-attested compounds ranked by frequency) for corpus-scale
  split-only practice.
  [`data/samasa/samasa_curriculum.tsv`](https://github.com/gasyoun/kosha/blob/main/data/samasa/samasa_curriculum.tsv)
  (759 gold-verified compounds, karmadhāraya/tatpuruṣa first then
  bahuvrīhi/dvandva per the MG 14-07-2026 ordering ruling, ranked within type
  by corpus frequency) + [`reference.tsv`](https://github.com/gasyoun/kosha/blob/main/data/samasa/reference.tsv)
  (per-type look-up) + [`samasa_drills.json`](https://github.com/gasyoun/kosha/blob/main/data/samasa/samasa_drills.json)
  (3,565 identify/split items, 100% evidence-backed) + `samasa_drills.apkg`
  (Anki) + `reading/samasa/{curriculum,drills,reference}/index.html`
  (theme-aware, cross-links the hosted
  [csl-guides samāsa quiz](https://sanskrit-lexicon.github.io/csl-guides/docs/users/samasa-quiz)
  rather than duplicating it). Type distribution honestly reported, not
  balanced: TP=458, BV=298, DV=2, KD=1 — dvandva/karmadhāraya are severely
  underrepresented in the gold set and the corpus pool cannot fill the gap
  (no verified type there). `samasa-trainer` manifest row registered;
  [`tests/test_samasa_trainer.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_samasa_trainer.py)
  (11 tests) green, no regressions in the existing suite.

## [0.51.0] - 2026-07-14

### Added
- **H947: frequency-graded vocabulary curriculum (Wave 1, W1b).** Applies the shipped
  sandhi-curriculum method to words — "learn the N most frequent lemmas → read X% of the
  corpus" — over the Leonchenko core-vocabulary layer already carried by
  [`lemma_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv)
  (`core_rank`/`coverage_pct`). New
  [`scripts/build_vocab_curriculum.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_vocab_curriculum.py)
  emits [`data/frequency/vocab_curriculum.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/vocab_curriculum.tsv)
  (6,667 lemmas over 134 lessons; 453 core lemmas dropped for having no committed
  dictionary card — no dead `/w/` links), `vocab_drills.json` (13,334 recognition/recall
  items, ARCHITECTURE shared item schema), `vocab_curriculum.apkg` (Anki deck), and
  [`reading/vocabulary/curriculum/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/vocabulary/curriculum/index.html).
  Coverage headline: 284 lemmas → 30%, 1,122 → 50%, 4,978 → 70% of the core-vocabulary
  corpus mass. `datasets.json` gains `vocab-curriculum` + `vocab-drills` rows;
  `tests/test_vocab_curriculum.py` (8 tests, all green) locks monotone coverage, every
  lemma resolving to a real card, and lesson sizes. Gotcha worth flagging: the source
  feed's `coverage_pct` is a per-lemma **marginal** weight, not already-cumulative
  (`data/frequency/README.md`'s own caveat) — the cumulative column here is computed by
  this script, not copied from the source.

## [0.50.0] - 2026-07-14

### Added
- **H950 (pedagogy Wave 2, W2b): roots frequency + attestation curriculum.**
  REUSE/INTEGRATE, not a rebuild — [WhitneyRoots](https://github.com/gasyoun/WhitneyRoots)
  already owns the 935-root explorer and already computes a per-root
  MW↔Whitney↔DCS triangulation with corpus frequency and attested forms
  (`WhitneyRoots/src/dcs_freq.json`). New
  [`scripts/build_roots_frequency.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_roots_frequency.py)
  reads that canonical source and adds the missing graded-curriculum framing —
  rank order + cumulative `coverage_pct` — producing
  [`data/roots/roots_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/roots/roots_frequency.tsv)
  + `.json` (629 unique DCS-lemma rows, deduped from 717 Whitney-hub roots with
  attestation — 74 homonym-shared lemmas collapsed so the same corpus mass
  isn't triple-counted). Coverage headline: learn top 25 roots → 58.7% of
  verb-token occurrences; top 50 → 71.7%; top 100 → 85.4%; top 200 → 95.3%.
  `roots-frequency-curriculum` manifest row registered; no kosha roots UI
  shipped, per the architecture's integration-surface rule — WhitneyRoots and
  Systema are the intended consumers. `tests/test_roots_frequency.py` (8
  tests: monotone coverage, dense ranks, every root traceable to WhitneyRoots's
  own hub, no homonym double-counting, TSV/JSON agreement, no fabricated
  attested forms).

## [0.49.0] - 2026-07-14

### Added
- **H945: kosha pedagogy engine-room build plan (`/ask`).** A layered build plan
  generalising the shipped corpus-sandhi programme's six-stage pattern to the rest of
  kosha's pedagogy data — the *engine-room* half of the org-wide digital-Sanskrit-pedagogy
  field defined in
  [SanskritGrammar `DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md`](https://github.com/gasyoun/SanskritGrammar/blob/main/DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md)
  (H912). Cover + decisions
  [`PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md)
  (+ `.meta.md`); layers
  [roadmap](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md) ·
  [architecture](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md) ·
  [implementation](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE1.md) ·
  [verification](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md).
  Four build waves (morphology drills · vocabulary curriculum · samāsa trainer ·
  graded-reader + difficulty scorer), two reuse/integrate (roots → WhitneyRoots, metre →
  SanskritKaraoke), one agenda (audio); wave handoffs H946–H951 minted. No papers this
  cycle — surfaces + measurement instrumentation only.

## [0.48.0] - 2026-07-14

### Added
- **H918 (sandhi Phase 4, surface 4b): drills/flashcards — the last core-programme
  surface.** New
  [`scripts/build_sandhi_drills.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_drills.py)
  turns the graded curriculum's 132 highest-value rules (lessons 1–9, 90 % of all
  corpus sandhi) into 396 practice items — join (`X + Y → ?`), split
  (`Z → original junction?`), identify-class — each with 4-way multiple-choice
  same-class distractors and an attested corpus example. Shipped in all three
  formats MG requested: item-data JSON/TSV
  ([`data/sandhi/sandhi_drills.json`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/sandhi_drills.json) /
  [`.tsv`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/sandhi_drills.tsv)),
  an Anki deck
  ([`sandhi_drills.apkg`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/sandhi_drills.apkg),
  genanki), and a self-contained theme-aware web quiz at
  [`reading/sandhi/drills/`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/drills/index.html).
  Registered as the `sandhi-drills` dataset. Credit: Dr. Mārcis Gasūns. (Sibling
  surface 4a, reader hover, is a separate SanskritGrammar handoff, H917 — Phase 4
  is now fully shipped on the kosha side.)

## [0.47.0] - 2026-07-14

### Added
- **Sandhi programme hub doc** — new
  [SANDHI_PROGRAMME.md](https://github.com/gasyoun/kosha/blob/main/SANDHI_PROGRAMME.md)
  consolidates the whole sandhi programme (v0.36→v0.46) into one "what exists &
  how to use it" page: the pipeline, headline results (inducer 96.3 % Gītā-gold,
  17-text corpus, A/B/C bake-off verdict method C ≫ B), every dataset/script/page,
  rebuild steps, and cross-repo consumers. Linked from the README Document map.

## [0.46.0] - 2026-07-14

### Added
- **H902 (sandhi Phase 4, surface 3/4): per-class reference pages.** New
  [`scripts/build_sandhi_reference.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_reference.py)
  emits a corpus-wide look-up reference — every recurring sandhi grouped by class
  (anusvāra 34.7 % · visarga 32.1 % · vowel coalescence 19.9 % · consonant 13.3 %
  of all sandhi), each ranked by frequency with an attested example, at
  [`reading/sandhi/reference/`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/reference/index.html)
  (theme-aware, self-contained; top 50 per class, the 3,794-rule consonant tail
  summarised). A look-up companion to the graded curriculum. Credit: Dr. Mārcis
  Gasūns. (Remaining Phase-4 surfaces: reader hover, drills/flashcards.)

## [0.45.0] - 2026-07-14

### Added
- **H902 (sandhi Phase 4, surface 2/4): graded curriculum.** New
  [`scripts/build_sandhi_curriculum.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_curriculum.py)
  turns the corpus sandhi table into an ordered teaching syllabus — "learn these
  N junctions to read X % of all sandhi." Rules are ordered by the MG-ruled
  priority (`frequency × class × environment-generality`, 14-07-2026), with the
  weights in a tunable, visible config
  [`data/sandhi/difficulty_weights.json`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/difficulty_weights.json)
  (per the ruling — not hard-coded; edit + re-run to re-tune). Outputs
  `data/sandhi/sandhi_curriculum.tsv` (2,181 rules, 10 lessons) + a theme-aware
  page [`reading/sandhi/curriculum/`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/curriculum/index.html).
  **Headline: 23 rules → 50 %, 79 → 80 %, 132 → 90 %** of all corpus sandhi;
  easy high-frequency rules first. New `sandhi-curriculum` dataset registered in
  [`datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
  Credit: Dr. Mārcis Gasūns. (Remaining Phase-4 surfaces: reader hover, drills,
  reference pages.)

## [0.44.0] - 2026-07-14

### Added
- **H908 (sandhi Method C): DharmaMitra neural segmenter — the A/B/C bake-off's
  clear winner.** `method_C` in
  [`scripts/compare_sandhi_methods.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_sandhi_methods.py)
  segments each DCS sentence via the DharmaMitra `unsandhied` API
  ([`dharmamitra.org/api/tagging/`](https://dharmamitra.org/api/tagging/), contract
  reused from `csl-atlas/scripts/lib/dharmamitra_infer.py`) and feeds the split
  through the same induce tail as A/B — so only the splitter differs.
  `--allow-network`; responses cached under `data/sandhi/_cache/` (per-batch
  retry + incremental writes). **Method C ≫ Method B** on the fair (mode-1-only)
  comparison to DCS gold: F1 **0.795 vs 0.282** (Amaruśataka) and **0.704 vs
  0.224** (Hitopadeśa), with C precision 0.90–0.97 — the neural splitter's word
  boundaries match DCS far more often than vidyut-cheda's. **Verdict:** use
  method C as the splitter for the GRETIL path (Phase 3) where no DCS gold exists.

## [0.43.0] - 2026-07-14

### Added
- **H903 (sandhi Phase 1, method B): vidyut-cheda bake-off vs gold DCS splits.**
  [`scripts/compare_sandhi_methods.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_sandhi_methods.py)
  `method_B` binds the offline `vidyut-cheda` segmenter (`Chedaka` over the
  `vidyut-data/` root, not the `.msgpack` file directly), transliterates
  IAST↔SLP1, and induces sandhi rules from cheda's predicted pre-sandhi splits
  through the SAME `induce_rule()` gold uses — isolating splitter quality from
  notation. Scope: mode-1 (plain word-word) junctions only, since
  `Chedaka.run()` returns no character offsets to re-anchor a predicted
  sub-word split within an MWT span. Scored on 2 texts: Hitopadeśa (500 rules
  / 1,359 junctions scored, mode-1-only F1=0.224 vs gold's 437-rule slice) and
  Amaruśataka (61 rules / 73 junctions, F1=0.282). Also added
  `method_A_mode1_strict` (fair gold baseline matching B's scope) and
  no-gold-recovery instrumentation — which found the roadmap's planning-stage
  "~27 % no gold split" estimate does NOT reproduce on DCS (0 % on both texts
  + a 15-dir corpus sample); see
  [`ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md)
  §2 for the full writeup. Method C (DharmaMitra) remains explicitly deferred.
- **H901 (sandhi Phase 2b): broadened corpus sandhi sweep, 8 → 17 texts.**
  Extends H900's `scripts/build_corpus_sandhi.py` `TEXTS` list with kāvya
  (Buddhacarita, Kumārasaṃbhava, Kirātārjunīya, Meghadūta), more readers
  (Daśakumāracarita, Bhāratamañjarī), śataka/nīti (Śatakatraya,
  Bhallaṭaśataka), and the **full** Rāmāyaṇa (606 files) and **full**
  Mahābhārata (1,995 files) — the latter replaces H900's Bhagavadgītā-only
  glob (the Gītā's 18 chapters are already inside the full-corpus sweep, so
  keeping the narrow row would have double-counted those tokens in the merged
  global table; `data/sandhi/bhagavadgita_sandhi.tsv` retired accordingly).
  **580,230 sandhi events · 9,840 distinct rules** (was 53,291 / 1,674); the
  top **83** rules now cover 80% of all corpus sandhi (was 69 — moved up
  slightly, plausibly kāvya's more varied sandhi spreading the frequency mass
  across more rules, reported honestly rather than smoothed over). **Scale
  finding:** the handoff worried the full Mahābhārata (~2,000 files) would
  need a parvan/`--limit` sample gate — measured instead of assumed (~10
  files/s on a 300-file timing sample), the full corpus ran directly in a few
  minutes on one machine, no sampling gate needed. `corpus-sandhi` manifest
  row updated; `ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md` + its `.meta.md`
  updated (backlog item 2 ticked).

## [0.42.0] - 2026-07-14

### Added
- **H900 (sandhi Phase 2): corpus-wide sandhi sweep + merged frequency-ranked table.**
  New [`scripts/build_corpus_sandhi.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_corpus_sandhi.py)
  runs the validated method-A inducer (96.3 % Gītā-gold coverage) across a curated
  8-text pedagogical set in learner-difficulty order (Hitopadeśa, Vetālapañcaviṃśatikā,
  Śukasaptati, Amaruśataka, Aṣṭāvakragīta, Bhagavadgītā, Gītagovinda, Kathāsaritsāgara)
  and builds per-text tables plus the merged
  [`data/sandhi/corpus_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/corpus_sandhi.tsv)
  with global frequency ranks (`rule · category · global_count · global_pct ·
  n_texts · top_texts · examples`). **53,291 sandhi events, 1,674 distinct rules;
  the top 69 rules cover 80 % of all corpus sandhi** — the graded-curriculum
  backbone. New public dataset `corpus-sandhi` registered in
  [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
  Credit: Dr. Mārcis Gasūns; source DCS CC BY-SA 4.0 (Oliver Hellwig / DCS).

## [0.41.0] - 2026-07-14

### Changed
- **H897 (sandhi Phase 1.2): spaced-notation split — clears the 90 % Gītā-gold
  exit criterion.** Final-`t` assimilation, `i`→`y` semivowel, and MWT-internal
  visarga were being *induced* but written merged (`t a → da`, `i e → ye`,
  `ḥ v → rv`) rather than in the hand table's spaced form (`t a → d a`,
  `i e → y e`, `ḥ v → r v`). One rule in `induce_coalescence`
  ([`scripts/dcs_sandhi_induce.py`](https://github.com/gasyoun/kosha/blob/main/scripts/dcs_sandhi_induce.py))
  — split the output when the right word's initial phoneme survives unchanged —
  fixes it, leaving genuine coalescence (`a a → ā`, `a e → ai`) merged.
  **Gītā-gold frequency-mass coverage 87.1 % → 96.3 %** (rule-string 82 →
  116/161), clearing the roadmap's ≥90 % exit criterion. Residual 3.7 % is
  mostly malformed `gita_sandhi.tsv` entries + `aḥ`/`ḥ` notation variants.
  Credit: Dr. Mārcis Gasūns.

## [0.40.0] - 2026-07-14

### Added
- **Bloomfield RV pratīka cross-reference (H896)** — resolves the CONCORDANCE_ROADMAP.md
  Bloomfield-source `@DECIDE` left open by H836. MG obtained direct written permission from
  Marco Franceschini (University of Bologna) for his digital edition of Bloomfield's 1906
  *A Vedic Concordance* (Harvard Oriental Series 9) — public tier, non-exclusive/worldwide/
  perpetual (grant text in
  [`data/manifest/rights/franceschini_hos9_permission_2026-07-13.md`](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/franceschini_hos9_permission_2026-07-13.md)).
  New [`scripts/build_bloomfield_rv_crossref.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_bloomfield_rv_crossref.py)
  adds a `bloomfield_pratika` column to `parallel_passage_verses.tsv` for the RV subset
  (11,522/13,581 rows, 85%, independently text-validated rather than positionally assumed —
  see [`BLOOMFIELD_RV_CROSSREF_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/BLOOMFIELD_RV_CROSSREF_REPORT.md)
  for the method and the honest residue) + new dataset `bloomfield-rv-citations` (36,680 rows,
  every direct RV citation in Bloomfield's concordance). Manifest rows, `LICENSE-DATA.md`,
  and `/concordance/parallels/` updated.

## [0.39.0] - 2026-07-14

### Added
- **H894 (sandhi Phase 1.1): MWT right-edge visarga.** New **mode 2b**
  (`induce_mwt_edge` in [`scripts/dcs_sandhi_induce.py`](https://github.com/gasyoun/kosha/blob/main/scripts/dcs_sandhi_induce.py))
  recovers the last-in-MWT word's sandhi with the token *after* the MWT — hidden
  in the component's un-sandhied FORM, visible only in the MWT surface tail. It
  takes the last alignment op ending at the component's final phoneme, handling
  substitution (`ḥ t → s t`, `ḥ v → r v`), elision (`ḥ i → Ø i`), and multi-char
  (`aḥ → o`). Pilots regenerated; Gītā-gold notation coverage **58 % → 61 %**
  (93 → 98 of 161 hand rules), visarga now the top category. Credit: Dr. Mārcis
  Gasūns.
- **Gītā gold scoring** (roadmap item 5):
  [`scripts/score_gita_gold.py`](https://github.com/gasyoun/kosha/blob/main/scripts/score_gita_gold.py)
  runs method A on the *actual* DCS Bhagavadgītā (18 `MBh, 6, BhaGī N` chapters)
  and scores against `gita_sandhi.tsv`. **Frequency-mass coverage 87.1 %**
  (2,971 / 3,412 attestations) — the true figure, vs the 61 % rule-string proxy
  a small pilot gives. Missed 12.9 % = a long tail (final-`t` assimilation,
  `i`-semivowel before non-`a` vowels) → Phase 1.2.

## [0.38.0] - 2026-07-13

### Added
- **H888 (sandhi Phase 1): vowel-coalescence alignment mode.**
  [`scripts/dcs_sandhi_induce.py`](https://github.com/gasyoun/kosha/blob/main/scripts/dcs_sandhi_induce.py)
  now recovers the vowel-sandhi rules Phase 0 structurally missed. DCS records a
  coalesced surface span as a CoNLL-U **multi-word token** (`5-6 nāgnir` over
  `5 na` + `6 agniḥ`, whose own FORM stays un-coalesced), so a token-edge diff
  never sees the merge. New **mode 2** aligns each MWT surface against its
  component `Unsandhied` forms and reads the rule off the internal boundary
  (`na`+`agniḥ` in `nāgnir` → `a a → ā`), sandhi-aware so `na`+`eva`→`naiva`
  gives `a e → ai` (not a naïve alignment's `a e → i`).

### Fixed
- **Sandhi Phase-0 MWT bug:** the inducer counted CoNLL-U MWT range lines (ID
  `n-m`) as tokens, inflating `no-gold` junctions (Aṣṭāvakragīta 1,263 → **0**).
  Mode 1 now skips range/enhanced-node lines and processes syntactic words only.
- **PWG multi-volume scan-link disambiguation** (H839, Sonnet 5 `claude-sonnet-5`)
  — [`app/scan_resolver.py`](https://github.com/gasyoun/kosha/blob/main/app/scan_resolver.py)'s
  `scan_url()` silently defaulted a bare PWG page number to volume 1's scan
  regardless of the entry's real volume. Resolved by source read
  ([`csl-apidev/parm.php`](https://github.com/sanskrit-lexicon/csl-apidev/blob/main/parm.php)
  + `servepdfClass.php`) plus a live content-diff against the production
  `servepdf.php` endpoint: Cologne has **no** `vol=`/`volume=` GET parameter
  (any such param is silently ignored, which is why status-code probing alone
  always returned 200); volume is instead embedded inside `page` itself as
  `"{vol}-{page:04d}"`, matching PWG's own `<pc>` format and Cologne's
  `pdffiles.txt` keys. `scan_url()` now takes `vol` and requires it for PWG
  (returns `None` rather than an ambiguous link if omitted); every call site
  (`app/main.py` ×3, `app/salt.py`, `scripts/build_static_cache.py`,
  `scripts/build_colocation_page.py` ×2, `scripts/measure_d5.py`) updated to
  pass `entries.vol`. New tests:
  [`tests/test_scan_resolver.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_scan_resolver.py).
  **Not included in this pass:** regenerating the committed `docs/cards/*.json`
  static cache / `colocation/data/pwg.js` — deferred to a separate pass so it
  can be built from a current (not 39-commits-stale) database rather than
  mixed into this fix.

### Changed
- **Sandhi pilots regenerated** with the merged mode-1 + mode-2 output.
  Aṣṭāvakragīta now surfaces `a a → ā` as its #1 rule (122); Gītā-gold notation
  coverage rose **47 % → 58 %** (75 → 93 of the 161 hand rules). Residual gap =
  visarga elision at MWT right edges (`ḥ m → Ø m`), scoped as Phase 1.1. Credit:
  Dr. Mārcis Gasūns.

## [0.37.0] - 2026-07-13

### Changed
- **Pronoun correction phase 2: flag the wrong Cologne pronoun rows `disputed=1`.**
  The `build_db.py --stage pronoun` step now also marks wrong Cologne pronoun rows
  for editorial review (the E1 `disputed` mechanism; non-destructive). Scoped to the
  `(form, lemma)` pairs the Gītā gold attests, a row is flagged when its case is
  untagged (NULL) or its (case, number) is not gold-attested — **73 rows newly
  flagged** (9 were already E1-flagged; 79 gold-consistent rows left untouched),
  across 10 pronoun lemmas (sarva, etad, idam, kim, anya …). `(case, number)` — not
  gender — is used to avoid flagging gender-ambiguous valid rows; details in
  [`PRONOUN_CORRECTION_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/PRONOUN_CORRECTION_REPORT.md).

## [0.36.0] - 2026-07-13

### Added
- **H882: corpus-wide sandhi extraction roadmap + Phase 0 DCS scaffold.**
  Generalises the H872 Bhagavadgītā sandhi layer from one hand-annotated text to
  every DCS text (GRETIL phase-3). New:
  [ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md)
  + `.meta.md`;
  [`scripts/dcs_sandhi_induce.py`](https://github.com/gasyoun/kosha/blob/main/scripts/dcs_sandhi_induce.py)
  (method A — junction-rule inducer over DCS `Unsandhied=`, reuses the H872
  `categorise()` classifier verbatim, emits per-text `data/sandhi/<slug>_sandhi.tsv`);
  [`scripts/compare_sandhi_methods.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_sandhi_methods.py)
  (A/B/C split-method bake-off skeleton + notation validation vs the Gītā hand
  table). Pilots: Aṣṭāvakragīta (722 sandhi events, 100 % ruled, 147 rules) and
  Hitopadeśa (4,554 events, 453 rules); method A independently reproduced 75 of
  the Gītā's 161 hand rules. Finding: DCS pre-splits vowel coalescence into
  separate tokens, so token-edge induction misses it (Phase-1 `# text =`
  alignment mode planned). Credit: Dr. Mārcis Gasūns.

## [0.35.0] - 2026-07-13

### Fixed
- **Curated pronoun-paradigm correction — closes the W4 QA finding.** The Gītā
  inflection QA (H874) showed kosha's hybrid `inflections` layer mis-models
  pronouns (71 % of divergences). Per MG, this **corrects** it:
  [`scripts/build_pronoun_corrections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_pronoun_corrections.py)
  takes the **208 gold attested pronoun analyses** from the Gītā and inserts them
  into `inflections` as `source='curated-gita-pronoun'` rows — wired as
  **`build_db.py --stage pronoun`** (idempotent, non-destructive, re-applied on
  rebuild). Re-running the QA on the corrected engine: nominal agreement
  **93.0 % → 98.7 %**, divergences **360 → 73**, gaps **919 → 588**
  ([`PRONOUN_CORRECTION_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/PRONOUN_CORRECTION_REPORT.md);
  dataset [`pronoun-corrections`](https://github.com/gasyoun/kosha/blob/main/data/gita/pronoun_corrections.tsv)).
  Public/MIT, credit Dr. Mārcis Gasūns.

## [0.34.0] - 2026-07-13

### Fixed
- **`/api/v1/search` prefix mode: `LIKE 'ka%'` scan → `slp1 >= 'ka' AND slp1 <
  'kb'` range seek** (H838, Sonnet 5 `claude-sonnet-5`) — fixes the
  [D5_MEASUREMENTS.md](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md)
  §3-flagged defect: `LIKE` forced a full 323k-row `lemmas` scan (~62–70 ms) AND,
  being case-insensitive by default, silently over-matched SLP1's case-significant
  prefixes (`ka%` wrongly matched 1,504 `K`-initial/kha lemmas out of 12,495 hits).
  The range seek hits the index (`EXPLAIN QUERY PLAN` now shows `SEARCH ... USING
  COVERING INDEX`, not `SCAN`) and restores correctness (7,041 correct hits).
  Handler latency 61.8 ms → **3.26 ms** median (p95 7.17 ms); e2e 51 ms →
  **11.82 ms**. New regression test
  `tests/test_api.py::test_search_prefix_case_significant_excludes_kha` (fails
  against the old query, proving it catches the regression). D5 §3 re-measured
  and logged.
- **Re-ran the H345 `heritage_anchor` ingest on the live `kosha.db`** (H837,
  Sonnet 5 `claude-sonnet-5`) — fixes the H691-flagged regression where the
  05-07-built (and later 12-07-rebuilt) live DB carried no `heritage_anchor`
  table, so `/api/v1/lemma`'s `heritage` witness was silently absent. Re-ran
  `python scripts/build_db.py --stage heritage`; row counts match H345's
  original ingest exactly (185,803 MW keys, 25,140 Heritage-covered,
  24,549 anchor-resolved, 591 unresolved). Verified live against a running
  API instance (`GET /api/v1/lemma/akAra` now returns a populated `heritage`
  object). `data/manifest/datasets.json` `kosha-db` row updated (new SHA256,
  size, table count, provenance date).

### Added
- **H836 (CONCORDANCE_ROADMAP Q2, B3): Bloomfield-style parallel-passage concordance.**
  New public dataset `parallel-passage-concordance`
  ([manifest row](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json))
  built by [`scripts/build_parallel_passage_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_parallel_passage_concordance.py)
  from `VisualDCS/derived-data/Paralleli-v-tekstah-korpusa-SRC/PARA/Polnorazmernye/`
  (245 CSV files, the 2026 corrected full-text-match pass): 501,231 source verses
  parsed, 15,164 (3.0%) carry ≥1 parallel occurrence, 153,045 total links (13,862
  GOOD exact + 139,183 PARTLY partial, word-diff attached). New static viewer
  [`concordance/parallels/`](https://github.com/gasyoun/kosha/blob/main/concordance/parallels/index.html)
  (text picker → verse list → GOOD/PARTLY parallels with diffs). Full counts +
  honest caveats in [`data/concordance/PARALLEL_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/PARALLEL_BUILD_REPORT.md):
  the roadmap's prior "506,787 alignments" estimate (itself sourced from an
  admittedly-unverified upstream README note) doesn't match this build's
  directly-parsed counts — flagged, not silently reconciled. Two open `@DECIDE`
  surfaced to a human, not self-ruled: which of three PARA export variants is
  canonical (defaults to `Polnorazmernye/` per the folder's own README), and
  which Bloomfield *Vedic Concordance* (1906) digitization to key the Ṛgveda
  subset against (not found anywhere in the org — RV cross-reference not built
  this pass).
- **H836 Task A: relaxed-candidate pre-classification + review sheet.** New
  [`scripts/classify_relaxed_candidates.py`](https://github.com/gasyoun/kosha/blob/main/scripts/classify_relaxed_candidates.py)
  computes a per-row SLP1 diff signature for the 2,171 Q1/H380 relaxed-tier
  dict↔corpus candidates and pre-classifies 740 as "worth-a-closer-look"
  (single word-final vowel-length diff — the masc/neut -a vs fem -ā stem-citation
  pattern) vs 1,431 "likely-spurious" (default, per the Q1 golden sample's 3/3-wrong
  finding on this exact tier); emits `data/concordance/relaxed_candidates_classified.tsv`.
  [`scripts/build_relaxed_review_sheet.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_relaxed_review_sheet.py)
  generates a gitignored Russian-language `/review-sheet` HTML voting sheet
  (`review/kosha-concordance-relaxed_q2_review.html`, not committed — a personal
  working artifact) for MG. Only MG-approved rows get asserted into the concordance.

## [0.33.0] - 2026-07-13

### Added
- **Upasarga semantics on the `/w/` root card (H876 W6 follow-up).** Root word-pages
  now carry a crawlable "Preverb senses (upasarga)" `<details>` panel driven by the
  [`sanskrit-upasarga-semantics`](https://github.com/gasyoun/kosha/blob/main/data/gita/upasarga_semantics.tsv)
  dataset (√vac → pra-vac "declare"; √gam → ava-gam "understand"). Added
  `_upasarga_block()` to [`app/word_page.py`](https://github.com/gasyoun/kosha/blob/main/app/word_page.py)
  — a pure function of the SLP1 lemma + the committed dataset, so it is prerender ∥
  SSR byte-identical, host-independent and crawlable (all 15 word-page tests pass).
  This closes the deferred `/w/` surfacing of roadmap W6.

## [0.32.0] - 2026-07-13

### Added
- **H876 (roadmap W6, final workstream): Sanskrit root × preverb (upasarga)
  semantics.** New public/MIT dataset
  [`data/gita/upasarga_semantics.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/upasarga_semantics.tsv)
  — **148 verb roots + 69 preverb-modified senses** (√vac "speak" → pra-vac
  "declare"; √gam "go" → ava-gam "understand", sam-adhi-gam "attain") from the
  `Gita.xlsm` `verbs` sheet, a compositional dimension the Cologne dictionaries
  lack. Built by [`scripts/extract_upasarga_semantics.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_upasarga_semantics.py)
  (preverbs classified by their trailing `-`, so the sheet's irregular column
  alignment parses correctly) + a browsable page `reading/upasarga/`
  ([`scripts/build_upasarga_page.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_upasarga_page.py)),
  linked from the reader. Data statement
  [`docs/data-statements/upasarga-semantics.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/upasarga-semantics.meta.md);
  a `/w/` root-card panel is a documented follow-up. Credit: Dr. Mārcis Gasūns.
  **This completes the Gītā-gold extraction roadmap (W0–W6).**
## [0.31.0] - 2026-07-13

### Added
- **H875 (roadmap W5): Gītā Russian gloss layer + etymology dataset.** The Gītā
  reader gains an **English / Русский gloss toggle** (the master's `gloss_ru`,
  ~9,091 words, now carried per token and switchable in the viewer). New public/MIT
  dataset [`data/gita/gita_etymology.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_etymology.tsv)
  — **101 hand-written etymological notes** on selected words (`putra – one who
  saves from hell`; `uttama – superlative of ud`), extracted by
  [`scripts/extract_gita_etymology.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_etymology.py)
  from the `Grammar` sheet's col AG (which the master drops), aligned by
  verse+word-index. Data statement [`docs/data-statements/gita-etymology.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/gita-etymology.meta.md).
  Credit: Dr. Mārcis Gasūns.

## [0.30.0] - 2026-07-13

### Added
- **H872 (roadmap W2): Gītā sandhi layer.** New public/MIT dataset
  [`data/gita/gita_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_sandhi.tsv)
  — the **first corpus-attested, frequency-ranked sandhi table** in the ecosystem:
  161 distinct rules over 3,412 sandhi junctions across the whole Bhagavadgītā
  (`aḥ a → o '`, `ḥ t → s t`, anusvāra assimilations …), each with a category
  (visarga / anusvāra / vowel-coalescence / consonant), count, share and example
  words. Built by [`scripts/build_gita_sandhi.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_gita_sandhi.py)
  from the W0 master. A theme-aware teaching page `reading/sandhi/` renders the
  ranked table, and the Gītā reader now shows each word's **sandhi rule on hover**.
  Credit: Dr. Mārcis Gasūns.

## [0.29.0] - 2026-07-13

### Changed
- **H871 (roadmap W1): Gītā reader extended to all 18 adhyāyas.**
  [`scripts/build_reading_pack_gita.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_reading_pack_gita.py)
  now builds **one gold pack per chapter** (`reading/data/gita-1..18.js`) directly
  off the W0 master [`data/gita/gita_gold_master.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_gold_master.tsv)
  — **701 verses / 9,092 words, ~99.5 % linked** to `/w/` cards, with Devanagari +
  IAST + English gloss per verse. The [`reading/`](https://github.com/gasyoun/kosha/blob/main/reading/index.html)
  viewer gains a chapter picker (Nala 1 + Gītā 1–18). The chapter-1-only source
  (`gita-1_gold_sanskritgrammar.tsv`) and `extract_gita_gold.py` are retired —
  the reader is now unified on the master. Dataset `gita-reading-pack-1` →
  `gita-reading-pack` (all 18 adhyāyas).

## [0.28.0] - 2026-07-13

### Added
- **H874 (roadmap W4): Gītā inflection-engine QA — the first attested-corpus check
  of the E1 hybrid forms layer.** [`scripts/gita_inflection_qa.py`](https://github.com/gasyoun/kosha/blob/main/scripts/gita_inflection_qa.py)
  cross-checks every Bhagavadgītā nominal's **gold** case·number·gender (H873)
  against kosha's Cologne+vidyut hybrid `inflections` paradigm. Result:
  **93.0 % agreement** on nominals present in kosha (4,779/5,139); **360 divergences
  + 919 gaps** as a corrections feed. **Finding:** divergences are **71 % pronouns**
  (untagged `None.None.None` or wrong cell) — confirming and quantifying, with
  attested text, the pronominal mis-modelling
  [`E1_DIVERGENCE_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md)
  flagged synthetically; gaps are mostly long compounds. Report
  [`GITA_MORPHOLOGY_QA_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/GITA_MORPHOLOGY_QA_REPORT.md)
  + ledger [`data/gita/gita_inflection_divergences.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_inflection_divergences.tsv)
  (`gita-inflection-qa`). Candidate `disputed`/gap-fill corrections are surfaced,
  **not auto-applied** (a human `@DO` adjudicates). Public/MIT.

## [0.27.0] - 2026-07-13

### Added
- **H873 (roadmap W3): Gītā gold morphology + compound dataset.** New public/MIT
  dataset [`data/gita/gita_morphology_gold.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_morphology_gold.tsv)
  — 9,091 words, each with structured morphology decoded from the `Gita.xlsm`
  `Grammar`-sheet shorthand via the workbook's `Abbreviations` legend:
  case·number·gender (nominals), person·number·tense·voice (finite verbs),
  non-finite/derivation tags, and **compound type** (TP/BV/DV/KD). Built by
  [`scripts/extract_gita_morphology.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_morphology.py)
  (the decode legend is embedded from the `Abbreviations` sheet); `raw_morph`
  preserves the source shorthand. Registered (`gita-morphology-gold`) + data
  statement [`docs/data-statements/gita-morphology.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/gita-morphology.meta.md).
  This is the gold input to **W4** (the E1 inflection-engine QA). Credit: Dr. Mārcis Gasūns.

## [0.26.0] - 2026-07-13

### Added
- **H848 W0: Gītā gold master dataset.** New public/MIT dataset
  [`data/gita/gita_gold_master.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_gold_master.tsv)
  — the hand-curated word-by-word analysis of the **whole Bhagavadgītā** (9,092
  words · all 18 adhyāyas · 21 fields: lemma, root, gender, stem-class,
  **compound type**, morphology code, **sandhi rule**, English + Russian gloss),
  extracted from `SanskritGrammar/Concordance/Gita.xlsm`'s `Combined` sheet by
  [`scripts/extract_gita_master.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_master.py).
  The garbled private-use Russian *transliteration* column is dropped; the clean
  Cyrillic *gloss* is kept. Registered in the manifest (`gita-gold-master`) +
  data statement [`docs/data-statements/gita-gold.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/gita-gold.meta.md).
  This is **W0** of [`ROADMAP_GITA_GOLD_EXTRACTION_2026.md`](https://github.com/gasyoun/kosha/blob/main/ROADMAP_GITA_GOLD_EXTRACTION_2026.md)
  — the master every Gītā-gold workstream (reader all-18-ch, sandhi, morphology,
  inflection-QA, root/preverb semantics) derives from. Credit: Dr. Mārcis Gasūns.

## [0.25.0] - 2026-07-13

### Changed
- **H848: Gītā 1 reading pack upgraded EXPERIMENTAL → GOLD.** The machine
  (GRETIL + vidyut-cheda) build is replaced by a hand-curated word-by-word
  source — `SanskritGrammar/Concordance/Gita.xlsm` (`Grammar` sheet: lemma,
  root, morphology, English + Russian gloss), vendored via
  [`scripts/extract_gita_gold.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_gold.py)
  to [`reading/data/sources/gita-1_gold_sanskritgrammar.tsv`](https://github.com/gasyoun/kosha/blob/main/reading/data/sources/gita-1_gold_sanskritgrammar.tsv)
  (569 words / **47** verses — the full vulgate chapter). Rebuilt by
  [`scripts/build_reading_pack_gita.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_reading_pack_gita.py):
  **567/569 (99.6%) linked** to `/w/` cards (curated lemma 513 · root 46 ·
  forms-table 8). The viewer now shows **Devanagari + IAST + English glosses**;
  the experimental banner and the GRETIL source are removed. Dataset renamed
  `gita-reading-pack-1-experimental` → `gita-reading-pack-1`. Same gold quality
  class as the DCS-lemmatised Nala pack.

## [0.24.0] - 2026-07-13

### Added
- **H855: E1 verb dhātu-identity crosswalk — present-system agreement 12.68 % →
  70.24 %.** The H185 Task C verb comparison scored a misleading 12.68 % because
  `Dhatu.mula(bare_root, gaṇa)` is ambiguous where the nominal
  `Pratipadika.basic(stem)` was not — Cologne stores the bare SLP1 root, vidyut
  wants the *aupadeśika* dhātu — so 259/683 roots derived nothing (a mapping
  artifact, not divergence). New builder
  [`scripts/build_dhatu_crosswalk.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_dhatu_crosswalk.py)
  matches each Cologne `(root, gaṇa)` to the dhātupāṭha entry whose vidyut
  present-3sg-active equals Cologne's (else direct/normalized-bare), resolving
  **722/779 (92.7 %)** of the gaṇa-1/4/6/10 root-models. The committed
  [`data/e1/dhatu_crosswalk.json`](https://github.com/gasyoun/kosha/blob/main/data/e1/dhatu_crosswalk.json)
  carries only aupadeśika strings, so
  [`scripts/compare_vidyut_verbs.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_verbs.py)
  needs only bundled vidyut at run time (external `vidyut-data` is a build-time
  input to the crosswalk builder only — R12). Re-run: strict agreement
  **70.24 %** (near the nominal 90.5 %), roots-vidyut-can't-derive **259 → 110**,
  `COLOGNE_ONLY` **29,268 → 15,984**; the 11,056 residual conflicts are real
  accent/sandhi/gaṇa-shift divergences. New
  [`tests/test_dhatu_crosswalk.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_dhatu_crosswalk.py)
  (6 tests). Still **no verb hybridization** (D3); Task B give-back stays
  MG-gated. Answers [csl-inflect#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8).

### Changed
- **[`E1_DIVERGENCE_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md)**
  Verbs section rewritten with the crosswalk before/after; the ṇatva/gap-fill/
  `disputed` figures reconciled to the shipped-DB materialisation (326 ṇatva-fix
  rows / 55 stems, 17 gap-fill, 13,888 disputed) vs the top-10k characterization
  sample (89 stems / 16 / 13,770) — a sample-vs-full-run drift, not a classifier
  change.

## [0.23.0] - 2026-07-13

### Added
- **H848: Gītā 1 reading pack (EXPERIMENTAL, machine-segmented).** Since the
  Bhagavadgītā is absent from the DCS gold corpus (MBh book 6 omits adhyāyas
  23–40), this pack takes its mūla from GRETIL (vendored public-domain text,
  [`reading/data/sources/gita-1_mula_gretil.tsv`](https://github.com/gasyoun/kosha/blob/main/reading/data/sources/gita-1_mula_gretil.tsv),
  46 verses) and lemmatises it by machine via
  [`scripts/build_reading_pack_gita.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_reading_pack_gita.py)
  — kosha's `forms`-table reverse-lookup (549 tokens) with a vidyut-cheda
  fallback (16). **565/597 tokens (94.6%) linked** to `/w/` cards. Unlike the
  gold Nala pack, lemmas are auto-derived and some are wrong (long samāsa
  compounds, a few names/participles); the viewer shows an **experimental
  banner** and [`reading/BUILD_REPORT_GITA.md`](https://github.com/gasyoun/kosha/blob/main/reading/BUILD_REPORT_GITA.md)
  lists the residue. Dataset `gita-reading-pack-1-experimental`; the `reading/`
  viewer now offers both Nala 1 (gold) and Gītā 1 (experimental).

## [0.22.0] - 2026-07-13

### Added
- **H848: P5 step-6b reading packs — Nala 1 built; Gītā 1 parked.** New builder
  [`scripts/build_reading_pack.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_reading_pack.py)
  turns a DCS chapter into a word-by-word reading pack whose every word links to its
  kosha `/w/` dictionary card — **consuming** the H380 concordance core
  ([`scripts/concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py)'s
  `TieredMatcher`/`to_slp1` + the `card_token` twin), not re-rolling the join. **Nala 1**
  (`MBh, 3, 50`, Nalopākhyāna) shipped: 65 sentences / 439 tokens, **434 (98.9%) linked**
  (exact tier; 5 unlinked = DCS causative `-ay` stems + 1 indeclinable, honest residue).
  Self-contained viewer [`reading/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/index.html)
  (+ `reading/data/nala-1.{js,json}`, [`reading/BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/reading/BUILD_REPORT.md)),
  dataset `dcs-reading-pack-nala-1` in the manifest. Data-path finding: the real DCS DB is
  `VisualDCS/src/DCS-data-2026/dcs_full.sqlite` (the 0-byte `src/dcs_full.sqlite` is a decoy).
- **H848: Gītā 1 reading pack PARKED (data gap).** The Bhagavadgītā is absent from the DCS
  corpus — Mahābhārata book 6 (Bhīṣmaparvan) omits exactly adhyāyas 23–40 (the 18 Gītā
  chapters) and there is no standalone Bhagavadgītā text; a Gītā pack needs an external
  lemmatised source (surfaced as `@DECIDE`).

## [0.21.0] - 2026-07-12

### Added
- **H185: P4 Wave E1 hybridize — vidyut layered over the Cologne inflection base
  (MG ruling HYBRIDIZE).** New forms-layer pass
  [`scripts/build_hybrid_forms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_hybrid_forms.py)
  (`build_db.py --stage hybrid`, run after `--stage inflections`) reuses the E1
  comparison's classifier — so the applied set matches
  [E1_DIVERGENCE_REPORT.md](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md)
  cell-for-cell (top-10k sample): **326 ṇatva cells / 89 stems** auto-fixed
  ([MWinflect#6](https://github.com/sanskrit-lexicon/MWinflect/issues/6)) as
  `source='hybrid-natva-fix'` rows, **16 `m_card` cells** gap-filled as
  `source='vidyut-gap-fill'`, **13,770 cells / 1,440 stems** flagged
  `disputed=1` (pronominal + feminine/consonant forks, for editorial review).
  No Cologne row is deleted — the buggy form stays reverse-resolvable; the
  display layer prefers the fix and records the superseded form. `inflections`
  gains a `disputed` column; [`app/paradigm.py`](https://github.com/gasyoun/kosha/blob/main/app/paradigm.py)
  emits a sparse per-model `cell_notes` provenance map and
  [`app/reverse_lookup.py`](https://github.com/gasyoun/kosha/blob/main/app/reverse_lookup.py)
  adds `source`/`disputed` to each `/analyze` parse. New
  [`tests/test_hybrid_forms.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_hybrid_forms.py)
  (6 tests); demo paradigm/reverse shards regenerated; **229 passed / 2 skipped**.
- **H185 Task C: present-system verb comparison** answering
  [csl-inflect#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8).
  [`scripts/compare_vidyut_verbs.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_verbs.py)
  maps Cologne `v_<gana>`/`v_p` rows into vidyut's `Tinanta` API. Finding: strict
  agreement is only **12.68 %** (683 roots, 34,056 both-nonempty cells) — a
  dhātu-IDENTITY mapping gap (bare Cologne root ≠ vidyut aupadeśika), not a
  grammar disagreement. **No verb hybridization applied** (a bare-root
  substitution would inject a different lexeme's forms); Cologne verb tables stay
  as-is (D3). The dhātu-identity crosswalk is the flagged larger follow-on.

### Note
- The csl-inflect#10 nominal give-back drafted in E1 stays **parked** — posting
  to the dormant, noise-averse upstream is diplomacy-gated (RELATIONS.md §2/§7)
  and awaits a separate MG go-ahead (unchanged by this release).

## [0.20.1] - 2026-07-11

### Changed
- **H752: parked rival H730 lane salvaged into the merged protocol** (docs/provenance
  only — no scored output changed). Grafted into
  [docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md):
  the verified [Hellwig et al. 2026 (ISCLS)](https://aclanthology.org/2026.iscls-1.2/)
  delta (supervised MW-definition WSD with Sanskrit Sembank gold — closes the
  previously-flagged overlap check), SHA-256 input digests in
  [frozen_sample.meta.json](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/frozen_sample.meta.json)
  (independently computed by both racing lanes, byte-identical inputs confirmed), and the
  gold-free inputs projection + 3-rater Fleiss-κ WSD design queued for the A59 paper
  phase. The 500-headword seed-730 sample is declared the **single canonical frozen set**;
  the parked 520-headword rival sample was never scored and its branch
  `h730-defgen-eval-fable-lane` was deleted after salvage
  ([Uprava FINDINGS §67](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md)).

## [0.20.0] - 2026-07-11

### Added
- **H730: first CDSL-side definition-generation + gloss-grounded WSD eval** — frozen
  500-headword MW sample (3×3 frequency×polysemy strata, seed 730) with ≤5 DCS attestation
  sentences each ([data/eval/defgen/](https://github.com/gasyoun/kosha/tree/main/data/eval/defgen)),
  4 baseline arms (random floor, deepseek-chat ±attestations, deepseek-reasoner), sacrebleu
  BLEU/chrF + token-F1 + gated blinded LLM judge, WSD inter-model agreement pilot
  (κ=0.706). Harness: `scripts/defgen_build_sample.py` / `defgen_run_baselines.py` /
  `defgen_score.py`; protocol + results:
  [docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md);
  manifest row `mw-defgen-eval-sample`.

## [0.19.0] - 2026-07-11

### Changed
- **Heritage surplus forms are now default-off in every lookup path** (H696,
  Fable 5 `claude-fable-5`) — implements the R7 ruling (10-07-2026,
  [Uprava docs/DECISIONS_roadmap_forks_2026H2.md](https://github.com/gasyoun/Uprava/blob/main/docs/DECISIONS_roadmap_forks_2026H2.md)):
  the 928,262 distinct `source='heritage'` forms (ingested provenance-flagged by
  H111, count re-verified this pass) are excluded from `GET /api/v1/form/{form}`,
  `GET /api/v1/forms/{form}/analyze` (stages 2–3, incl. per-pada segmentation
  re-resolution) and the static paradigm/reverse tier
  ([`scripts/build_paradigms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_paradigms.py))
  unless the caller opts in with `?heritage=1`. Committed demo reverse shards
  regenerated without heritage witnesses; `dcs`/`vidyut` results are unchanged
  in both modes. Heritage's external oracle role (ruling point 3) is untouched.

### Added
- [`tests/test_heritage_default_off.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_heritage_default_off.py)
  (8 tests): heritage-only form absent by default / present with the flag on
  both endpoints, native-source invariance under the flag, and the ruled
  928,262 surplus-form ingest count asserted against the live DB.

## [0.18.0] - 2026-07-11

### Added
- **Provenance fields across the dataset manifest** (H691, Fable 5
  `claude-fable-5`, [PR #52](https://github.com/gasyoun/kosha/pull/52)): the census-§2
  local-only giants now carry `sha256` (streamed), `provenance_verified` and an honest
  `rebuild` recipe in
  [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  — `corpus-lexicon`, `sa-ru-glossary`, `kosha-db`, `dcs-full-sqlite`,
  `samudra-corpus-db` updated with live counts.
- **Three new manifest rows**: `archive-stopword-sqlite` (11 GB, 40,573,260 stop-word
  parallels — the census's "uncounted blind spot" resolved, fully regenerable),
  `samudra-offline-packs` (base+dict, SHA256s verified against their sidecars) and
  `kosha-raw-sqlite` (mw/pwg/ap90 inputs, re-fetchable from the csl-sqlite release).

### Fixed
- `kosha-db` manifest keying corrected from "9 tables" to the live 8; flagged that the
  current `kosha.db` build (05-07-2026) lacks the H345 `heritage_anchor` table — the
  heritage witness needs a re-ingest on next rebuild.

## [0.17.0] - 2026-07-11

### Added
- **Data statements for the entire public data tier** (H665, Fable 5
  `claude-fable-5`, [PR #47](https://github.com/gasyoun/kosha/pull/47)): one
  Bender-Friedman (2018) / Gebru et al. (2021) datasheet-form statement per
  `data-v0.1.0` release asset under
  [`docs/data-statements/`](https://github.com/gasyoun/kosha/tree/main/docs/data-statements)
  — `mw-roots`, `mw-etymology`, `dcs-cdsl-xref`, `union-headwords`,
  `mw-heritage-crosswalk`, `kosha-lemma-frequency`, `zaliznyak-grammar-index` —
  each covering composition & schema, provenance, curation rationale, language
  variety, process info, biases/limitations, intended use / known misuse,
  license, maintenance & sunset plan, deprecation status, citation; plus a
  [README index](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/README.md)
  with the queued backlog for the not-yet-covered manifest rows.
- **`data_statement` field in the dataset manifest**
  ([`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)):
  each of the 7 public released rows now links its data statement.
- **Two JOHD data-paper drafts** (readiness 2/5, registered as A55/A56 in the
  Uprava publication inventory):
  [`papers/A55_UNION_HEADWORDS_DATA_PAPER_JOHD.md`](https://github.com/gasyoun/kosha/blob/main/papers/A55_UNION_HEADWORDS_DATA_PAPER_JOHD.md)
  (union headword index, 323,425 rows / 15 dictionaries) and
  [`papers/A56_ZALIZNYAK_GRAMMAR_INDEX_DATA_PAPER_JOHD.md`](https://github.com/gasyoun/kosha/blob/main/papers/A56_ZALIZNYAK_GRAMMAR_INDEX_DATA_PAPER_JOHD.md)
  (grammar-token index, 98,639 rows / 335 paradigm tokens).
- **`CITATION.cff`** — repo-level citation metadata (this release's freeze-time
  sync; Zenodo DOI slot pending the GitHub–Zenodo wiring, a human `@DO`).
- **Minimal-direction mockup of the data directory** (H587,
  [PR #45](https://github.com/gasyoun/kosha/pull/45)):
  [`directory/mockups/minimal.html`](https://github.com/gasyoun/kosha/blob/main/directory/mockups/minimal.html),
  CSS-only restyle with markup byte-identical to the live directory page.

### Changed
- **README refreshed to the current data-hub role** (H550,
  [PR #46](https://github.com/gasyoun/kosha/pull/46)): P4/P5 state, data-hub
  framing brought current.

## [0.16.0] - 2026-07-11

### Added
- **P5 advanced UI — the word page** (H537, Opus 4.8 `claude-opus-4-8`), built
  from the locked design spec
  [`P5_ADVANCED_UI_DESIGN.md`](https://github.com/gasyoun/kosha/blob/main/P5_ADVANCED_UI_DESIGN.md)
  (MG rulings 10-07-2026: Tabs · all-3 view modes · full P5 scope · both render
  targets). One addressable word page per headword — every dictionary's entry,
  its evidence, its paradigm — reached by the crawlable `/w/{slp1}` permalink.
  - **Crawlable static prerender** — new
    [`app/word_page.py`](https://github.com/gasyoun/kosha/blob/main/app/word_page.py)
    shared template + [`scripts/build_word_pages.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_word_pages.py):
    every dict panel present in the DOM (active shown, rest hidden) with a
    `<noscript>` all-stacked fallback so a JS-less fetcher reads every entry
    (§5); progressive JS hydrates tabs (P5-1), the Gloss/Full/Adaptive view-mode
    toggle (P5-2, persisted to `localStorage`), and disclosures. Runs off the
    committed static card set (no DB); logs actual N + Pages budget + dropped
    tail (no silent caps). Plus a `/browse/<varṇa>` alphabetic spine linking
    every word page. Regenerable Pages output, gitignored like the cards.
  - **FastAPI SSR** — new `GET /w/{slp1}` route renders the long tail through the
    *same* `render_word_page()` template, so static ∥ SSR are byte-comparable
    (P5-4 parity); locked by
    [`tests/test_word_page.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_word_page.py)
    (15 no-DB structural/crawlability tests + a DB-gated SSR byte-parity check).
  - **SPA word page** — new `WordPage.svelte` interactive twin (MW/PWG/AP90 tabs,
    view-mode toggle sharing the same `localStorage` key, evidence + lazy
    paradigm + scan disclosures), reached by `#/w/{slp1}` hash routing; composes
    the existing `getEntry`/`getParadigm`/`ParadigmTable` (reuse ledger §7).
  - **Search operators** (§4) — `root:` and `sandhi:` in the search box (caught
    before transliteration), bare input auto-routes; `sandhi:` prefills the
    reverse analyser.
  - **Study tooling** — CSV (RFC-4180) and Anki (TSV) export of a session's word
    lookups (`lib/export.js`). *Gītā 1 / Nala 1 reading packs are data-gated —
    the DCS sentence-level lemmatised corpus is not present on disk
    (`VisualDCS/dcs_full.sqlite` is a 0-byte LFS placeholder); tracked as a
    follow-up, no verse tokenisation was fabricated.*
  - +34 tests green (19 vitest lib + 15 pytest template); the SPA word-page and
    `sandhi:` operator e2e flows verified in-browser. **Exit checks (MG sign-off
    on live staging · Lighthouse mobile ≥90 · Gītā-verse walkthrough) remain
    gated on MG's P2 `samskrtam.ru` deploy**, per the plan.
- **Type-D concordance record shape + `typed_link_lint.py`** (H539, Sonnet 5
  `claude-sonnet-5`) — extends
  [`scripts/concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py)
  per [`TYPED_LINK_ID_GRAMMAR.md`](https://github.com/gasyoun/Uprava/blob/main/TYPED_LINK_ID_GRAMMAR.md)
  §1 (H499) so every Type-D (grammar ↔ non-grammar) concordance builder imports
  one implementation instead of forking a schema: `RECORD_FIELDS`' `corpus_locus`/
  `corpus_text_id` renamed to `target_locus`/`source_dataset` (positions/semantics
  unchanged); `TYPE_D_RECORD_FIELDS` adds `link_type` + `date`;
  `normalize_record()` maps either shape into one shared view; two new
  `match_method` tiers above `exact` in trust — `id-link` (pure host-stable-id
  join) and `curated` (source concordance's own assertion). New
  [`scripts/typed_link_lint.py`](https://github.com/gasyoun/kosha/blob/main/scripts/typed_link_lint.py)
  validates a Type-D dataset's anchor/target-locus prefixes, tail syntax,
  `link_type`/`match_method`/`date` against the spec, exits non-zero per bad
  row; tested against the spec's §4a/§4b landed worked examples plus negative
  fixtures (URL-host locus, unknown prefix, bad date) in
  `tests/fixtures/typed_link/`. No Type-D dataset registered in the manifest
  (D2b parks that until Q2.1).
- **Pipeline operator runbook** ([docs/PIPELINE_OPERATOR_RUNBOOK.md](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.md),
  H501, Fable 5 `claude-fable-5`) — the single operational spine for the whole
  chain: the seven `build_db.py` stages in dependency order with rerun triggers,
  API serve, the two static-tier deploy classes (committed-goes-live vs
  gitignored-MG-deploys), the data-release citability ritual
  (`archive_senses` → `build_crosswalk` → release asset → manifest refresh),
  maintenance scripts, the verbatim never-touch list, and a failure-symptom
  decoder (the `unable to open database file` wave = DB-less checkout, not a
  regression). Every command/flag cross-checked against script source.
- **B1 dictionary ↔ corpus concordance + the shared concordance core (Q1 of
  [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md)).**
  Executor: Fable 5 (`claude-fable-5`), handoff H380.
  - [`scripts/concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py) —
    the Q1–Q4 shared core: canonical record schema, tiered matcher (exact →
    length-preserving `form_key` floor → lossy tiers, unique-bucket only) on the
    canonical `sanskrit-util` keys, host-independent `dcs:<sent_id>` citable loci.
  - [`scripts/build_dict_corpus_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_dict_corpus_concordance.py) →
    [`data/concordance/`](https://github.com/gasyoun/kosha/tree/main/data/concordance):
    **74,520 asserted links** (xref 12,836 · exact 61,373 · floor 311) joining the
    323,425-headword union to the 5.69M-token DCS corpus; coverage sidecar classes
    every headword (66,257 attested = 20.5%, the honest Zipf reality); manifest row
    `dict-corpus-concordance` added same pass.
  - **Golden-sample ruling** ([GOLDEN_SAMPLE.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/GOLDEN_SAMPLE.md)):
    mechanical checks 14/14, but the lossy `norm`-fold tier was 0/3 semantically
    correct (aṃśaka↔aṃsaka, vikarṣaṇa↔vikarśana) — its 2,171 links are
    **quarantined** to `dict_corpus_relaxed_candidates.tsv`, never asserted.
  - [`concordance/dict/`](https://github.com/gasyoun/kosha/tree/main/concordance/dict) —
    the reusable static concordance viewer (search → dict-provenance chips →
    tier-badged lemma links → KWIC with citable loci; 25 lazy shards, 32.9 MB;
    works on file://, trust block, CSV fallback; RISKS R12: no live service).
- **Static print co-location page (public Pages tier).** Executor: Opus 4.8
  (`claude-opus-4-8`), handoff H441.
  - [`scripts/build_colocation_page.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_colocation_page.py)
    renders [`colocation/`](https://github.com/gasyoun/kosha/tree/main/colocation)
    from `kosha.db` only (RISKS.md R12, no live service) — the static web
    counterpart of the `/api/v1/page` + `/api/v1/neighbors` endpoints (v0.15.0),
    live at [gasyoun.github.io/kosha/colocation](https://gasyoun.github.io/kosha/colocation/).
  - Self-contained `colocation/index.html` + lazy per-dict `colocation/data/<dict>.js`.
    Grouped on each dict's finest printed unit: PWG `(vol, page)` = Spalte;
    MW `(page, col)` cited `page,col`; Apte `(page, col)` cited `page+letter`.
    444,773 located entries.
  - **Paged two-column leaf view** — the book sets two columns per page, so the
    browser shows a whole leaf (left col `2P−1` + right col `2P` for PWG, all
    columns of the physical page for MW/Apte), with ← / → paging (and arrow keys),
    a column jump box, dictionary-wide head-word search, and per-head-word
    highlighting. Deep-linkable: `#<dict>/<col>?w=<slp1>` (the RU PWG article site
    links every column-mate in here). Honest caveat surfaced in the UI: the source
    records column numbers, not the book's printed page number, so left/right
    *column* is exact but recto/verso of the leaf is not derivable.

## [0.15.0] - 2026-07-09

### Added
- **Print co-location endpoints — "which words shared a printed page/column".**
  Executor: Opus 4.8 (`claude-opus-4-8`), handoff H434.
  - [`app/neighbors.py`](https://github.com/gasyoun/kosha/blob/main/app/neighbors.py)
    groups entries by the `(vol, page, col)` already parsed from each `<pc>`
    marker (for PWG, `page` is the Böhtlingk-Roth Spalte — the same value
    [`scan_resolver`](https://github.com/gasyoun/kosha/blob/main/app/scan_resolver.py)
    feeds to `servepdf.php`).
  - `GET /api/v1/page/{dict}?vol=&page=&merge=` — every entry sharing one printed
    column (`merge=1` folds the two columns of a physical leaf).
  - `GET /api/v1/neighbors/{dict}/{L}` — the column-mates of one entry, in
    printed order, query entry flagged `is_query`; each result carries its
    `headword` + `scan_url`.
  - `(dict, vol, page, L)` index in
    [`scripts/build_db.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db.py)
    for the group-filter + printed-order seek; 5 new tests
    ([`tests/test_api.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_api.py),
    25 green). Live PWG: 123,366 entries, 100 % `<pc>` coverage, 8,171 columns.
    Fail-closed on unparseable `<pc>` (G-PC gate). [PR #33](https://github.com/gasyoun/kosha/pull/33).

## [0.14.0] - 2026-07-09

### Added
- **Search-history retention purge.** Executor: Sonnet 5
  (`claude-sonnet-5`), handoff H416.
  - [`scripts/purge_search_events.py`](https://github.com/gasyoun/kosha/blob/main/scripts/purge_search_events.py)
    + [`history_db.purge_old_search_events()`](https://github.com/gasyoun/kosha/blob/main/app/history_db.py)
    delete raw `search_events` rows (per-visitor query log) older than
    `--days` (default 180). `daily_rollup` — the permanent anonymous
    per-day/per-term aggregate the `/api/v1/stats/*` charts read from — is
    never touched. `--dry-run` reports the count without deleting.
    MG-run maintenance script (A3 local-first: no agent cron).

## [0.13.0] - 2026-07-06

### Added
- **Sanskrit data-hub P-D3: public data + tools directory page.** Executor:
  Opus 4.8 (`claude-opus-4-8`), MG ruling D-HUB-7 (06-07-2026), handoff H236.
  - [`directory/index.html`](https://github.com/gasyoun/kosha/blob/main/directory/index.html)
    (live at [gasyoun.github.io/kosha/directory](https://gasyoun.github.io/kosha/directory/))
    — the first curated directory for Sanskrit computational linguistics: 9
    public datasets (downloadable), 6 restricted (listed "on request"), and 8
    external stacks (vidyut/Ambuda, Sanskrit Heritage/INRIA, Samsaadhanii/SCL,
    DharmaMitra, DCS, VedaWeb, Cologne CDSL) with what-it-does / how-to-call /
    license / our-relation.
  - [`scripts/build_directory.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_directory.py)
    renders it from [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
    + a new [`data/manifest/external_tools.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json)
    (single sources — no facts hand-copied into HTML). Carries schema.org
    `Dataset` JSON-LD per public asset on an Organization `@id` spine (SEO
    playbook P0) — the lever for Google/Yandex Dataset Search indexing.
  - `datasets.json` gained a `release_asset` field on the 7 released rows so the
    page can build 1-click download URLs from the manifest.
  - Test invariants: [`tests/test_directory.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_directory.py)
    (one Dataset node per public row, `@id` spine, no restricted-download or
    gitignored-path leak). Wired from the README + docs-site landing footer.

## [data-v0.1.0] - 2026-07-06

### Added
- **P-D0 data-hub roadmap + machine-readable datasets manifest** (D-HUB-1..8,
  [#23](https://github.com/gasyoun/kosha/pull/23)) — kosha becomes the org
  Sanskrit data-hub per MG rulings 06-07-2026: two-tier (public releases /
  restricted backups), samskrtam.ru as the canonical big-file host after
  deploy, interim distribution via GitHub Releases `data-v*` tags, and
  [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  as the single source of truth for public/restricted asset metadata. This
  tag is the first of the separate **data-release** track (see the file
  header above) — distinct from the `vX.Y.Z` **repo-release** track this
  changelog otherwise documents.

## [0.12.0] - 2026-07-06

### Added
- **Sanskrit data-hub P-D0/P-D1 (kosha becomes the org data-hub).** Executor: Fable 5
  (`claude-fable-5`), MG rulings 06-07-2026.
  - [`DATA_HUB_ROADMAP.md`](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md)
    — 8 locked decisions (D-HUB-1…8), two-tier architecture (public releases /
    restricted private backups), phases P-D0–P-D6.
  - [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
    — machine-readable manifest of 15 canonical derived datasets across the org
    (7 public released, 5 restricted, 3 already-public listed for discovery), with
    keying, rights tier, builder, consumers per row + the agent contract
    ([`data/manifest/README.md`](https://github.com/gasyoun/kosha/blob/main/data/manifest/README.md)).
  - First public data release
    [`data-v0.1.0`](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0):
    mw_roots · mw_etymology · dcs_cdsl_xref · union_headwords ·
    mw_heritage_crosswalk · lemma_frequency · headword_index (~29 MB, 718k rows,
    all already public in source repos; CC BY-SA 4.0).

## [0.11.0] - 2026-07-05

### Added
- **Search history + analytics (Phases A/B/C-frontend).** Executor: Sonnet 5
  (`claude-sonnet-5`).
  - Backend (Phases A/B): anonymous per-visitor search history
    ([`app/history.py`](https://github.com/gasyoun/kosha/blob/main/app/history.py),
    [`app/history_db.py`](https://github.com/gasyoun/kosha/blob/main/app/history_db.py),
    [`app/identity.py`](https://github.com/gasyoun/kosha/blob/main/app/identity.py))
    via a `kosha_anon_id` cookie, no login required; `GET`/`DELETE
    /api/v1/history`; public credential-free aggregate analytics
    (`GET /api/v1/stats/summary|timeseries|top`); a magic-link login stub
    (`/api/v1/auth/request-link|verify`) for cross-device history sync,
    email provider not yet chosen (@DECIDE). Writable history SQLite store
    kept separate from the read-only dictionary DB so the monthly dict
    rebuild never touches it. 13 new tests.
  - Frontend (Phase C): `History.svelte` (recent searches, clear button,
    magic-link request form) and `Stats.svelte` (summary cards, Chart.js
    daily-volume chart, top-terms table) added to the K2b inflection UI's
    tab bar, both hidden when no live API is configured (no static fallback
    exists for personal/live-aggregate data). First use of **Chart.js** in
    `ui/`. 4 new component tests.

### Notes
- Two items remain, both tracked in
  [Uprava/GTD_NEXT_ACTIONS.md](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md):
  MG `@DECIDE` (email provider + production `CORS_ORIGINS`, both deploy-time
  A3 steps) and an agent-doable `search_events` retention-purge script.

## [0.10.0] - 2026-07-05

### Added
- **Wave E1 (inflection roadmap) — dual-engine comparison, nominal pass.**
  Executor: Opus 4.8 (`claude-opus-4-8`).
  - [`scripts/compare_vidyut_cologne.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_cologne.py)
    diffs **vidyut-prakriya** (0.4.0, local library — R12-clean, no live call)
    against the ingested Cologne `inflections` tables, classifying every
    case×number cell (`AGREE`/`DIFF`/`VIDYUT_ONLY`/`COLOGNE_ONLY`) with DIFF
    sub-classification (ṇatva / pronominal / final-stop / superset / fork).
  - [`E1_DIVERGENCE_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md) —
    **90.5 % cell agreement** over 240k cells / 10k entry-bearing nominal stems.
    Findings: the ṇatva bug ([MWinflect#6](https://github.com/sanskrit-lexicon/MWinflect/issues/6))
    is confirmed with a **larger blast radius than the documented 69** (89 stems
    in the top-10k sample); pronominal stems (`sarva`) mis-modelled as nominals;
    cardinal numerals (`saptadaśan`) missing from Cologne but generated by
    vidyut; feminine consonant/monosyllabic-stem derivation forks. Continues Jim
    Funderburk's Cologne-vs-Huet line ([csl-inflect#10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10))
    with an independent third engine.
  - **Recommendation: hybridize** (keep Cologne base per D3, layer vidyut to
    auto-fix ṇatva + fill gaps + flag forks) — filed as an @DECIDE for MG.

### Notes
- E1 remainder is human-gated: the migrate/hybridize/stay **ruling** (MG
  @DECIDE) and the **give-back post** to csl-inflect#10 (diplomacy-gated,
  drafted not posted), plus the agent-doable **verb comparison** (answers
  csl-inflect#8) — all queued in
  [H185](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md).
  E1 raw comparison output (`data/e1/`) is gitignored (regenerable).

## [0.9.0] - 2026-07-05

### Added
- **P4 Wave K2b** (H183) — the translator-first Sanskrit **inflection lookup
  UI**, the frontend half of the drastically-improved Cologne inflection tool.
  Executor: Opus 4.8 (`claude-opus-4-8`).
  - **Svelte 5 + Vite app** ([`ui/`](https://github.com/gasyoun/kosha/tree/main/ui))
    building into [`docs/inflect/`](https://github.com/gasyoun/kosha/tree/main/docs/inflect),
    served by the existing Pages deploy at `gasyoun.github.io/kosha/inflect/`
    (62 kB JS bundle). Four features (H183 K2b-3, roadmap Wave K3 folded in):
    **stem → paradigm** (auto-detect input → SLP1, Devanagari-default
    case×number / verb grids with an IAST/SLP1 toggle), **paste-anything
    reverse analysis** (wraps `/analyze`, shows `resolved_by` provenance),
    **autocomplete** (prefix range-seek over the shared 323k `lemmas.json`,
    live transliteration), and **dictionary cross-links** (every stem links to
    its in-app MW/PWG/AP90 entry; the entry has a "show all forms" control back
    to the paradigm — two silos, one tool).
  - **Data backend is "both"** (K2b-2, [`ui/src/lib/datasource.js`](https://github.com/gasyoun/kosha/blob/main/ui/src/lib/datasource.js)):
    static pre-generated JSON by default (works with **no live server** —
    RISKS.md R1/R5/R12-clean), and the live FastAPI `/api/v1/…` when
    `window.KOSHA_API` is set. Stage-3 vidyut segmentation degrades honestly to
    `segmentation_available:false` in the static tier (the live-API path
    resolves it).
  - **New `GET /api/v1/paradigm/{lemma}`** endpoint + shared
    [`app/paradigm.py`](https://github.com/gasyoun/kosha/blob/main/app/paradigm.py)
    grouping module, and
    [`scripts/build_paradigms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_paradigms.py)
    emitting parity-locked static paradigm + reverse-index shards
    (`--demo` committed, `--all` deployed by MG out-of-band per A3). Bridged
    stems fold (`Bagavant`→`Bagavat`).
  - **Auto-detect input** (Devanagari/IAST/SLP1) via the vendored **sanskrit-util**
    JS package (SHARED_CODE.md family #1 — no new transcoder); Devanagari
    rendering uses `slp1_to_devanagari` (composes matras/conjuncts) not the
    naive `iast_to_devanagari`.
  - **Tests:** 6 new pytest (`tests/test_paradigms.py`, endpoint + static-shard
    byte-parity) → **167 passed**; 17 vitest (translit auto-detect, token
    parity, prefix seek, static data-path integration, full App e2e).
  - **Data caveat surfaced verbatim** (D3): the Cologne m_a ṇatva bug
    (MWinflect#6) is shown as-is, not silently "fixed" in the frontend.

### Notes
- Roadmap Wave **K3 folded into K2b** per MG 05-07-2026 — the inflection roadmap
  now owes only Wave E1 (dual-engine vidyut comparison).
- Pages tier re-measured: `docs/inflect/` = 2.0 MB (app + committed demo data);
  total tier ~404 MB, ~60% headroom under the 1 GB soft limit unchanged.

## [0.8.0] - 2026-07-05

### Added
- **P4 Wave K2a** (H181) — reverse-lookup query pipeline, verb-form ingest,
  and the stem-normalization bridge. Executor: Opus 4.8 (`claude-opus-4-8`).
  - **Reverse-lookup cascade** ([`app/reverse_lookup.py`](https://github.com/gasyoun/kosha/blob/main/app/reverse_lookup.py))
    behind `GET /api/v1/forms/{form}/analyze`: `inflections` exact hit →
    `forms` witness → **vidyut-cheda segmentation** of a sandhied/compound
    string, each stage tagged with a `resolved_by` provenance field
    (`inflections`/`forms`/`segmentation`/`null`). Segmentation
    ([`app/segmenter.py`](https://github.com/gasyoun/kosha/blob/main/app/segmenter.py))
    runs vidyut 0.4.0 as a **local library over vendored data**
    (`data/vidyut/`, gitignored); no live third-party call at build or query
    (RISKS.md R12), and it degrades to an honest miss (`segmentation_available:
    false`) when the data isn't vendored.
  - **Verb conjugations ingested** — the upstream MWinflect Python-2 syntax
    bug in `verbs/pysanskritv2/inputs/clean.py` (parenthesized-tuple lambda
    parameter) that blocked `verbs/redo.sh` in K1 is fixed and prepared as an
    on-its-merits upstream PR. [`scripts/build_inflections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_inflections.py)
    now loads present-system conjugations (pre/ipf/ipv/opt × active/middle/
    passive) into `inflections` (**+67,140** rows; total 6,916,522) with new
    `person`/`tense`/`voice` columns (NULL for nominals). So `Bavati` now
    resolves as 3sg present of `BU`.
  - **Stem-normalization bridge** ([`scripts/build_stem_bridge.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_stem_bridge.py)
    → `stem_bridge` table, `--stage stem_bridge`) maps strong/weak stem-spelling
    variants across `inflections` (`Bagavat`) and `forms` (`Bagavant`) to one
    canonical lemma key. Narrow, data-gated rule (nt→t / drop-final-n, only
    when the two spellings share a surface form) — 380 mappings; the named exit
    case `Bagavant → Bagavat` unifies to one lemma.
  - Tests: new [`tests/test_reverse_lookup.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_reverse_lookup.py)
    (cascade, verb ingest, bridge, segmentation + graceful degradation); full
    suite **161 passed**. Documented in
    [`data/SOURCES.md`](https://github.com/gasyoun/kosha/blob/main/data/SOURCES.md)
    (incl. the ṇatva caveat and the honest `dharmakSetre`-resolves-at-stage-1
    deviation from the brief's assumption).

## [0.7.0] - 2026-07-03

Phase 3 (evidence layer) + Phase 4 Wave K1 (inflection data ingest), landed
together via [PR #9](https://github.com/gasyoun/kosha/pull/9) (branch
`feat/p3-evidence-p4-k1-inflect`, Sonnet 5 `claude-sonnet-5`) — both tracks
ran as parallel sessions against the same checkout and ended up
file-interleaved in `app/main.py`/`scripts/build_db.py`, so they ship as one
release. P3 builds on P1's frequency LEFT-JOIN rather than duplicating it in
a new table (the P3 plan's original spec is now redundant with what's
already on `lemmas`). Full suite green: 149 passed (26 new in
`tests/test_evidence.py`, 6 new in `tests/test_inflections.py`), 1
pre-existing unrelated failure (`test_docs_site.py::test_committed_output_is_current`,
docs-site staleness from the parallel Wave-3 docs-site work already in
flight, not caused by this release).

### Added
- **P4 Wave K1** (data ingest + JSON API) — new `inflections` sidecar table
  ([`scripts/build_db.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db.py)
  SCHEMA + `--stage inflections`) loaded by
  [`scripts/build_inflections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_inflections.py)
  from the sibling MWinflect checkout's Cologne csl-inflect nominal
  declension tables (`nominals/pysanskritv2/tables/calc_tables.txt`, engine =
  Cologne verbatim per
  [ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md)
  D3). 6,849,382 (form, lemma, model, gender, case, number) rows from
  288,844 stems, 3,267,305 distinct forms. New read-only
  `GET /api/v1/forms/{form}/analyze` endpoint
  ([`app/main.py`](https://github.com/gasyoun/kosha/blob/main/app/main.py))
  returns every grammatical parse for a form. Verb conjugations are **not**
  included — MWinflect's `verbs/` pipeline is blocked by a Python-2-only
  syntax bug in `verbs/pysanskritv2/inputs/clean.py` (upstream issue, not
  fixed here; see `.ai_state.md` for the exact trace). 6 new tests in
  [`tests/test_inflections.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_inflections.py)
  hand-verify the roadmap's exit-test forms (`bhagavAn`, `rAmeRa`,
  `dharmakSetre`) against `calc_tables.txt`.
- **P3 evidence layer** —
  [`scripts/build_evidence.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_evidence.py)
  (new `--stage evidence`, wired into the default full build) adds two things
  additively to `lemmas` via `ALTER TABLE`: a **frequency band** (1–5, over
  `rank_all`; thresholds chosen from the D5-measured fact that the top 10,000
  ranked lemmas already cover 95.4% of corpus token mass — full reasoning in
  the module docstring) and **one corpus example per lemma** (Sanskrit
  citation + aligned Russian, joined from the sibling
  [`SanskritLexicography/RussianTranslation/src/corpus_lexicon.jsonl`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/corpus_lexicon.jsonl)
  (1,091,528 rows) via the existing `forms.form_slp1 -> lemma_slp1` join —
  examples ship **per lemma, not per sense**: the corpus feed has no
  sense-level tagging, stated explicitly rather than silently downgraded.
  Band distribution on the live spine: 1=493, 2=1,441, 3=7,484, 4=51,922,
  5=262,085 (no DCS signal); 38,595 lemmas got a corpus example.
- **[`app/evidence.py`](https://github.com/gasyoun/kosha/blob/main/app/evidence.py)** —
  shapes the DB columns into the API's evidence block; `/api/v1/lemma`
  entries now carry `evidence: {band, band_label, rank_all, count_all,
  first_era, genre, example, badges}`, every `badges[]` item carrying its own
  `source` string (fail-closed per EVAL_PLAN.md rule 4: a lemma with no DCS
  signal gets `count_all: null` / `example: null`, never a fabricated `0` or
  invented citation; `genre` is honestly `null` — not derivable from the
  current DCS extraction, which stores only a chronological period vector).
  Mirrored into
  [`scripts/build_static_cache.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_static_cache.py)'s
  `entry_payload()` (same lockstep-mirror pattern as `sense_ids`) so the P2
  static tier stays byte-identical to the live API.
- **`/api/v1/search` frequency-weighted ranking** — results now order by
  exact-key-match-first, then `rank_all ASC` (nulls last), then `slp1 ASC`,
  replacing plain alphabetical.
- **[`tests/test_evidence.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_evidence.py)**
  (26 tests) — `dharma` band/count/example (T-UC4 positive), a fail-closed
  negative case (band-5 lemma: no fabricated 0, no invented example),
  provenance-label-on-every-badge, a frozen 20-headword sample spanning all 5
  bands checking both band assignment and that search ranking measurably
  differs from alphabetical order (>=50% of multi-result queries in the
  sample reorder; sortedness verified directly).

## [0.6.0] - 2026-07-03

### Added
- **H111: Heritage/INRIA forms as a third, low-trust `forms` witness.**
  `forms` gains a nullable `category` column (migrated in `scripts/build_db.py`
  for pre-existing `kosha.db`s) and `scripts/build_forms.py` now loads
  [`heritage_only_forms.tsv`](https://github.com/gasyoun/SanskritLexicography/blob/master/HeadwordLists/heritage_only_forms.tsv)
  as `source='heritage'`, purely additive and loaded last: **+951,991** rows
  (`dcs` 397,843 and `vidyut` 28,567 unchanged). Trust ordering
  `dcs > vidyut > heritage` — Heritage's declension engine over-generates
  grammatically-possible but unattested forms — documented in
  [ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md),
  `build_forms.py`, and
  [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md).
  `/api/v1/form` already returned `source` per result, so heritage-only hits
  are distinguishable client-side without an API change.

## [0.5.0] - 2026-07-03

Phase 2 (public alpha) first agent-doable slice: the **static-cache generator**
that emits the GitHub Pages tier from `kosha.db` (branch `feat/p2-static-cache`,
Opus 4.8 `claude-opus-4-8`), built to the fixed D5-3 targets. 107 → **115** tests
green. Enabling Pages / deploying stays MG's (A3).

### Added
- **P2 static-cache generator** —
  [`scripts/build_static_cache.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_static_cache.py)
  emits three deliverables from the local DB (never a live service, R12), each
  matching [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md)
  D5-3:
  1. **Sharded per-lemma cards** — one JSON per lemma (never one bundle; a single
     `lemmas.json` crosses the 100 MB/file cap at ~33k), for the **50,355**
     lemmas with both a dict entry and a corpus attestation, **frequency-ranked**
     so a partial/interrupted run front-loads value (top-10k = 95.4% of corpus
     token mass) and resumes idempotently (existing shards skipped). Each card is
     **byte-identical** to `GET /api/v1/lemma/<slp1>?in=slp1` (reuses `app/`
     render/scan/transliterate — no reimplementation). ~155 MB, ~3 KB/file.
  2. **Headword autocomplete index** — one ~13 MB columnar file, all 323,425
     lemmas (`slp1`+`iast`+`dicts`); this is what the gitignored
     `docs/js/data/lemmas.json` path holds (D5-3a: the INDEX, not the cards),
     plus a tiny `attested_keys.json` sidecar so the UI picks static-vs-dynamic
     without a 404 probe.
  3. **Full 222,179-lemma card set** as an opt-in `--full-tarball` release asset
     (R1c/R4 rebuildability), deterministic (`mtime=0`), not committed.
- **Card filename encoding** (`card_token`) — keeps `[a-z0-9]` verbatim, escapes
  every other UTF-8 byte (incl. uppercase — SLP1 is case-significant and would
  collide on a case-insensitive FS) as `_<hexbyte>`; lossless, URL/FS-safe, with
  a documented JS twin for the frontend.
- **[docs/README.md](https://github.com/gasyoun/kosha/blob/main/docs/README.md)** —
  the Pages static-tier layout, token scheme + JS twin, and regeneration/deploy
  commands.
- **[tests/test_static_cache.py](https://github.com/gasyoun/kosha/blob/main/tests/test_static_cache.py)**
  (8 tests) — locks card↔live-API byte parity, `card_token` case-safety and
  lossless round-trip, ranked-shard generation, and index/attested counts
  (323,425 / 50,355).

### Changed
- `.gitignore` — the generated Pages tier (`docs/cards/`,
  `docs/js/data/attested_keys.json`, alongside the already-ignored
  `docs/js/data/lemmas.json`) is regenerable and MG-deployed, so it is not
  committed.

## [0.4.0] - 2026-07-03

Phase 1 **D5 — measure, then decide** (branch `feat/phase1-d5-measure`, Opus 4.8
`claude-opus-4-8`). The last Phase-1 step: real numbers behind the parked SLO
items, the decisions they force, a fixed latency bug the measuring surfaced, and
the R3 fallback turned from a comment into a tested path. 107/107 tests still
green. Phase 1 is complete; P2 (public alpha) can start against fixed targets.

### Added
- **D5 measurement report** —
  [D5_MEASUREMENTS.md](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md):
  DB size (276.4 MiB, 2.9× over the GitHub 100 MB/file cap → release-asset only,
  R11), cold/warm latency across all four read endpoints incl. the fat MW `ka`
  homonym group, per-dict `render()` cost + the full body-size distribution
  (97.3% of entries <1k chars; only 9 bodies >100k, all PWG), and a top-N
  static-cache projection. Reproducible from the committed harness
  [`scripts/measure_d5.py`](https://github.com/gasyoun/kosha/blob/main/scripts/measure_d5.py).
- **D5 decisions record** —
  [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md):
  latency SLO (p50<20ms / p95<100ms / p99<250ms server-side), rebuild cadence
  (change-triggered ~monthly, **not** nightly — nightly would mint needless
  citable `data_version`s, R1 tension), static-cache N (~50,355 attested-with-
  entry lemmas, sharded per-lemma ~155 MB, frequency-ranked). Relocated from the
  referenced SanskritLexicography path to this repo (canonical home); doc links
  repointed.
- **R3 csl-orig fallback exercised** (RISKS.md R3, now a tested path) —
  [`scripts/fallback_csl_orig.py`](https://github.com/gasyoun/kosha/blob/main/scripts/fallback_csl_orig.py)
  parses csl-orig `ap90.txt` directly and recovers **100%** of the entry
  inventory (34,882 records; every `<L>`, `<k1>` key, `<pc>` token matches the
  csl-sqlite-built DB). Honest boundary documented: bodies are the upstream
  display-markup stage, so a render()-able fallback also needs the csl-orig→XML
  `make_xml` step.

### Fixed
- **Lemma-lookup table scan (240 ms → ~0.3 ms).** `GET /api/v1/lemma` filtered
  `(dict, slp1_key)` but the planner seeked only on `dict` (via the
  `UNIQUE(dict,L)` autoindex, which also served `ORDER BY L`) and scanned all
  ~286k MW rows. A covering index `entries(dict, slp1_key, L)` (replacing
  `entries_key`, plus `ANALYZE` at build) serves both the seek and the ordering.
  Warm handler latency: lemma `kamala` 172→10.9 ms, `ka` 169→19.6 ms; e2e over
  HTTP 338→31 ms. Schema change in
  [`scripts/build_db.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db.py);
  the SLO (D5-1) assumes this index.

### Changed
- **`sources.csl_orig_commit` provenance resolved** (was flagged open) by
  cross-dating the csl-sqlite release timestamp against the local csl-orig commit
  log (offline, R12-safe): mw `392ed6b`, pwg `8822922`, ap90 `51232f2` — an
  upper bound, labelled as such. Wired into
  [`scripts/build_entries.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_entries.py)
  (`cross_date_csl_orig_commit`) and applied to the DB so `/api/v1/meta` surfaces
  it. Feeds R3's "data as of {date}" footer.
- ARCHITECTURE.md parked table: latency-SLO/cadence and static-cache-N rows
  resolved; DDL updated to the covering index. PHASE1_PLAN.md D5 marked done.

### Still open (not blocking)
- PWG multi-volume `servepdf.php` disambiguation needs a **live content diff**
  against Cologne (not a build-time or offline check, R12) — left flagged in
  [`.ai_state.md`](https://github.com/gasyoun/kosha/blob/main/.ai_state.md);
  belongs to scan-link hardening (G-SCAN/R2), not D5.

## [0.3.0] - 2026-07-03

Phase 1 D1–D4 **plus** the three D4-contract pieces PR
[#2](https://github.com/gasyoun/kosha/pull/2) deferred, closed here (branch
`feat/phase1-d4-followon`, Opus 4.8 `claude-opus-4-8`). 20 → **107** tests
green. Every measured number + deviation stays in
[`data/SOURCES.md`](https://github.com/gasyoun/kosha/blob/main/data/SOURCES.md).

### Added
- **Phase 1 D1–D4** (originally PR #2): lemma spine + frequency join (D1),
  per-dict `<pc>` entry loader for mw/pwg/ap90 (D2), forms layer + scan-URL
  resolver (D3), kosha API v1 + Salt facade REST faces + pytest suite (D4).
- **Full `render()` port** (ARCHITECTURE.md A1) —
  [`app/render.py`](https://github.com/gasyoun/kosha/blob/main/app/render.py) is
  now a code-level faithful port of the mw/pwg/ap90 path of csl-websanlexicon's
  canonical `basicdisplay.php` (SAX display engine) + the relevant
  `basicadjust.php` passes, replacing the earlier partial subset. Two documented
  deviations: server-side `<s>` SLP1→IAST via sanskrit-util (not client-JS
  `<SA>`), and no DB-backed abbreviation tooltips / external `<ls>` hrefs (the
  ls_resolver.py D3 follow-on). **38 frozen, checksummed golden HTML snapshots**
  (mw 14 incl. the banD/akṣa fixtures, pwg 12, ap90 12 — ≥10/dict merge bar) in
  [`tests/golden/`](https://github.com/gasyoun/kosha/tree/main/tests/golden),
  seeded-selected per EVAL_PLAN.md §0 anti-gaming, tested by
  [`tests/test_render_golden.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_render_golden.py).
- **Per-dict sense segmentation** (D2) —
  [`app/segment.py`](https://github.com/gasyoun/kosha/blob/main/app/segment.py)
  splits each body at its `<div>` division markers (MW `to`/`vp`, PWG numbered
  `1〉`/`a〉`, AP90 bold-numbered) into byte-anchored `senseN` spans (A2),
  replacing the single-sense fallback (kept only for markerless entries). Live
  counts: MW 303,022 · PWG 223,446 · AP90 165,935 senses.
- **R1 citability** (RISKS.md R1 Commitments 1–2) — the `cite` object now
  carries a browser-resolvable `resolution_url` + durable `release_asset`
  permalink + BibTeX/CSL-JSON
  ([`app/cite.py`](https://github.com/gasyoun/kosha/blob/main/app/cite.py));
  `/api/v1/sense/{id}@version` resolves an **old** citation against its archived
  release dump
  ([`app/versions.py`](https://github.com/gasyoun/kosha/blob/main/app/versions.py),
  [`scripts/archive_senses.py`](https://github.com/gasyoun/kosha/blob/main/scripts/archive_senses.py)),
  the path **T-UC10** forces; every rebuild can emit `sense_crosswalk.tsv`
  (old→new senseN via span-text similarity, SPLIT/MERGED/GONE/MOVED, zero-cost
  when unchanged —
  [`scripts/build_crosswalk.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_crosswalk.py)).
  Verified on real PWG data + unit-tested in
  [`tests/test_citability.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_citability.py).

### Still deferred (flagged, not silent)
- `sources.csl_orig_commit` still records the csl-sqlite release tag only (the
  underlying csl-orig commit is not exposed by the release format).
- PWG multi-volume scan disambiguation: `servepdf.php` returns 200 for `page=`,
  `page=&vol=`, and `page=&volume=` alike (tolerant of unknown params); whether
  `vol` is honored is not determinable from status alone. Still open.

## [0.2.1] - 2026-07-02

README rewritten for a layered dual audience (MG request; authored by Fable 5
`claude-fable-5`): public-facing top, engineering spine below.

### Changed
- **[README.md](https://github.com/gasyoun/kosha/blob/main/README.md)** — drastic
  rewrite: brand-led H1 (**Gasuns Sanskrit Dictionary**, kosha = codename); prominent
  pre-alpha "nothing runs yet" banner; public pitch + feature list + P1–P7 roadmap
  snapshot; new **FAQ** (18 questions across using-it / vs-existing-sites /
  status-timeline / licensing-reuse); planning spine preserved under "For contributors
  & agents" (reuse-first table, A1–A4, ground rules, full document map incl. the
  SanskritLexicography planning corpus). No decisions changed — presentation only.

## [0.2.0] - 2026-07-02

The judgment layer completed — the three plans queued in
[.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md) §Next Steps 1,
authored by Fable 5 (`claude-fable-5`). With these, the P1 execution session (Sonnet 5
`claude-sonnet-5` / Opus 4.8 `claude-opus-4-8`) is fully gated: EVAL_PLAN's gates bind.

### Added
- **[EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md)** — quality
  gates designed so an executor can't game them: 8 anti-gaming ground rules (freeze
  before first scored run, selection by committed procedure, thresholds live in the doc,
  fail closed, snapshot discipline, scorer ≠ system, no ✅ without artifact); G-SEG
  200-form stratified segmentation gold (9 classes incl. out-of-DCS contamination
  holdout + calibration rule); G-RENDER adversarial golden selection (accented PWG
  key2, `-L{lnum}` homonyms, densest MW `<ls>` cards, the ळ→x + IAST traps from
  [FINDINGS §36/§39](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md));
  G-SALT parity tolerances vs csl-apidev's `agni`/`indra`/`ka` envelopes (unlisted =
  exact); G-SCAN page-truth beyond HTTP 200; every
  [USE_CASES.md](https://github.com/gasyoun/kosha/blob/main/USE_CASES.md) *Accept:* line
  as a named test (T-UC1…T-UC13, Gītā 1.1 locked as the UC6 verse).
- **[RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md)** — ecosystem
  diplomacy: the Meyer permission ask drafted (his 7 self-digitized indices off-limits
  without written yes; send at P2 exit); Cologne-maintainer framing paragraph ("kosha
  serves your Salt standard", one csl-standards issue, no noise); Ambuda/vidyut
  give-back (G-SEG report upstream, name-collision rule: public name = Gasuns Sanskrit
  Dictionary); C-SALT/CCeH sense-face contribution; binding upstream-vs-track-3
  decision table; 7-row contact registry (all sends = MG).
- **[RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md)** — pre-mortem
  register R1–R12: `@data_version` is airtight only under 4 new commitments (in-browser
  version resolution forced by T-UC10, `sense_crosswalk.tsv` per release, **Zenodo
  mirroring moved up from P7 to the first citable release**, never-delete policy);
  scan-link page-truth (a wrong link is worse than none); csl-sqlite lag measured +
  surfaced as "data as of"; single-maintainer rot mirror-test + archive-banner policy;
  samskrtam.ru bus factor (citations never point at the server); license geometry
  (DCS dump license ask before P3 public; gramdict CC BY-NC must not enter BY-SA data).

## [0.1.0] - 2026-07-02

Founding release — the complete planning/contract layer, authored in one day by
Fable 5 (`claude-fable-5`) after MG green-lit Phase 1. No application code beyond the
honest stub; nothing claims ✅ without a passing check.

### Added
- **Repo created** per meta-decisions M1–M4 (triage of the fabricated planning corpus:
  [SanskritLexicography v0.0.34](https://github.com/gasyoun/SanskritLexicography/releases/tag/v0.0.34)); seeded README, reuse-first
  [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md) (D1–D5 with per-day exit checks), stub `app/main.py`.
- **[POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md)** + [summary](https://github.com/gasyoun/kosha/blob/main/POSITIONING_SUMMARY.md):
  product name **Gasuns Sanskrit Dictionary**; three-track identity (improve source ·
  improve Cologne UI · own advanced service); MG override recorded — own advanced UI,
  API-first.
- **[COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md)** — 12-platform live survey (all fetched 02-07-2026):
  michaelmeyer.fr = 41 dicts w/ per-sense scan links (positioning corrected — the
  read-only collapse exists); Heritage Inria bot-walled; DCS HTTPS broken; VedaWeb→Tekst;
  vidyut-kosha has no end-user UI. Mirrored as
  [FINDINGS §41](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md) (PR [#55](https://github.com/gasyoun/SanskritLexicography/pull/55)).
- **[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)** — engineering contract A1–A4: raw-markup storage +
  csl-websanlexicon-ported renderer (golden tests mandatory); sense IDs
  `dict.L.senseN@data_version`; local-first (MG deploys, agents never SSH); Sonnet/Opus
  executes. SQLite DDL, API v1 contract, encoding policy.
- **Salt API max-reuse (required):** Salt-profile entry object as the interchange shape
  inside `/api/v1`; entry data from csl-sqlite releases; Salt facade REST faces in P1/D4
  parity-tested vs csl-apidev envelopes; GraphQL face by P7.
- **Licenses:** code CC BY-NC 4.0 ([LICENSE.md](https://github.com/gasyoun/kosha/blob/main/LICENSE.md)); data releases CC BY-SA 4.0
  inherited from Cologne ([LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md) — csl-orig verified BY-SA, so NC
  attaches to code only).
- **[IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md)** — P1 data+API → P2 public alpha → P3 evidence
  layer → P4 forms+grammar → P5 advanced UI → P6 trilingual RU (G5 + Kochergina gates) →
  P7 citable v1.0 (DOI); per-phase exit checks; MG critical path.
- **[USE_CASES.md](https://github.com/gasyoun/kosha/blob/main/USE_CASES.md)** — 13 concrete scenarios (translators, students, scholars,
  machine consumers) mapped to delivering phases; acceptance-test seeds for EVAL_PLAN.
- **[.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md)** — session-state protocol; next queued: Fable chat authoring
  EVAL_PLAN.md + RELATIONS.md + RISKS.md, and the Sonnet/Opus P1 execution session.

_Dr. Mārcis Gasūns_
