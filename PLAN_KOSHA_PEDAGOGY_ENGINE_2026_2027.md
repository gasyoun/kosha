_Created: 14-07-2026 · Last updated: 19-07-2026_

# Kosha pedagogy engine — the build plan (2026–2027)

**This is the cover/index** of kosha's layered build plan for **digital Sanskrit
pedagogy**. It is the *engine-room* half of the field: where
[`DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md`](https://github.com/gasyoun/SanskritGrammar/blob/main/DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md)
(SanskritGrammar, handoff [H912](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H912-Opus_SanskritGrammar_digital-pedagogy-field-established_14.07.26.md))
**defines the field** org-wide — its aspect taxonomy, aspect×CEFR matrix, research
agenda, and gap register — this plan **builds kosha's learner-facing surfaces** for
it. The Systema Sanskrit-HUB LMS is the *showroom* that consumes what this engine
produces (see [`SANSKRIT_HUB_LEARNER_PROGRESSION_A0_C2.md`](https://github.com/gasyoun/Systema-Sanscriticum/blob/main/docs/SANSKRIT_HUB_LEARNER_PROGRESSION_A0_C2.md)).

Authored via [`/ask`](https://github.com/gasyoun/claude-config/blob/main/commands/ask.md)
(front-loaded interview → layered plan) by Opus 4.8 (`claude-opus-4-8`), 14-07-2026,
under handoff [H945](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H945-Opus_kosha_pedagogy-engine-room-build-plan_14.07.26.md).

**This is NOT a second field metadoc.** Per the field doc's own §8 ("do not spawn a
parallel pedagogy doc — this is the single org-wide one"), this plan is a *repo build
plan*: it consumes the field doc's taxonomy by reference and cross-links every wave to
its aspect §3.x there. It never restates the field definition.

---

## Goal in one paragraph

Generalise the **already-shipped corpus-sandhi pedagogy programme**
([`SANDHI_PROGRAMME.md`](https://github.com/gasyoun/kosha/blob/main/SANDHI_PROGRAMME.md))
from one aspect to the rest of kosha's data: turn kosha's paradigm engine, frequency
layer, compound data, reading packs, and concordance into **frequency/difficulty-graded,
corpus-attested learner surfaces** — each an ordered curriculum + drills + reference page
+ Anki/JSON export, instrumented with the same "learn N items → read X % of real text"
coverage metric the sandhi curriculum proved. Ship **data + web + course-consumable
surfaces**; no papers this cycle. Never rebuild what a sibling repo already owns.

---

## Layer docs

- **Roadmap (waves + build-vs-reuse verdicts):** [`docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md)
- **Architecture (the shared "pedagogy surface" contract):** [`docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md)
- **Implementation (wave-1 file-level steps):** [`docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE1.md`](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE1.md)
- **Verification (acceptance + risks):** [`docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md)
- **Companion metadoc:** [`PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.meta.md`](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.meta.md)

---

## Decisions taken (the execution agent trusts these without re-deriving)

Elicited from a human 14-07-2026 (this session) + inherited from H912 where the field is
already ruled.

| # | Decision | Ruling | Rationale |
|---|---|---|---|
| 1 | Scope of *this* plan | **kosha's learner-facing build layer** (the engine room) | The field is already defined org-wide (H912); this session builds kosha's surfaces, not a second field doc |
| 2 | Home | **kosha** | The data (paradigms, frequency, compounds, reading, concordance) lives here; surfaces sit with their substrate |
| 3 | Relation to Sanskrit-HUB | **Subordinate research/data layer feeding the Systema showroom** | Division of labour: kosha builds the graded surfaces, Systema wraps them in courses/SRS/access |
| 4 | Thesis / instrumentation | **Learning-outcome science** — every surface carries the "learn N → read X %" coverage metric | Extends H912 RQ4; the sandhi curriculum already proved it (23 rules → 50 %) |
| 5 | Output | **Data + web + course-consumable surfaces; NO papers this cycle** | Diverges from H912's paper-central wave; matches the interview |
| 6 | Surface pattern | **The sandhi-programme contract** (source → rank → curriculum+drills+reference → page → manifest+tests → export) | One proven pattern, instantiated per aspect; see ARCHITECTURE |
| 7 | Dimensions to build | morphology drills · vocabulary curriculum · samāsa trainer · graded-reader + difficulty scorer | Data-ready, non-duplicative (see build-vs-reuse below) |
| 8 | Dimensions to **reuse/integrate, not rebuild** | roots → WhitneyRoots · metre → SanskritKaraoke · script → csl-guides | Prior-art gate: greenfield rebuilds here would duplicate shipped sibling assets |
| 9 | Audio | **External-gated agenda, no kosha build** | Matches H912 §3.7 / Wave 4 — needs external content (reciter/TTS) |
| 10 | Merge authority | **Commit → PR → merge autonomously** | Handoff-scoped; per global rules + H912 ruling #16 |
| 11 | Ambiguity policy | **Pick the marked default + log; press on** | Keeps unattended waves moving |
| 12 | The fence | **csl-orig · the shipped sandhi data · sibling-repo source** (integrate via their data/API, never fork) | Only added build-scope fence; global publish/rights gates still bind |
| 13 | Russian-learner wave (added 19-07-2026, [`/ask-batch`](https://github.com/gasyoun/claude-config/blob/main/commands/ask-batch.md) interview) | **Wave RU: inline Sa→Ru gloss layer + beginner subhāṣita reader** — heavier builds prove standalone in kosha first, Systema consumes later (mixed-per-candidate ruling) | The shipped surfaces gloss in English; the org's RU lexical assets feed no reading surface — the audited gap sits at the Russian × corpus-attestation intersection |
| 14 | RU rights gate (19-07-2026) | **Published RU glosses only from the SanskritRussian public site-tier subset**; restricted bulk layers + `corpus_lexicon` stay local-only inputs | The bulk layers align published Russian translations — not redistributable; `/publish-safety-check` before any site deploy |

---

## Build-vs-reuse verdicts (the prior-art gate — nothing scheduled rebuilds an existing asset)

| Aspect | Field §3.x | Verdict | Handoff |
|---|---|---|---|
| **Sandhi** | [§3.1](https://github.com/gasyoun/SanskritGrammar/blob/main/DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md) | ✅ **SHIPPED** — the reference implementation of the whole pattern | H882–H918 (done) |
| **Morphology drills** | §3.2 | 🟢 **BUILD** — graded drill + answer-key surface over the shipped paradigm engine | [H946](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H946-Sonnet_kosha_pedagogy-w1-morphology-drills_14.07.26.md) |
| **Vocabulary curriculum** | §3.3 | 🟢 **BUILD** — frequency-graded syllabus (the sandhi-curriculum method on words) | [H947](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H947-Sonnet_kosha_pedagogy-w1-vocabulary-frequency-curriculum_14.07.26.md) |
| **Samāsa trainer** | §3.10 | 🟢 **BUILD** — compound-analysis surface over compound data + Gītā gold | [H948](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H948-Sonnet_kosha_pedagogy-w1-samasa-compound-trainer_14.07.26.md) |
| **Graded reader + difficulty scorer** | §3.4 | 🟢 **BUILD** — the difficulty scorer (named gap) + scale reading packs | [H949](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H949-Opus_kosha_pedagogy-w2-graded-reader-difficulty-scorer_14.07.26.md) |
| **Roots (dhātu)** | §3.2 | 🟡 **REUSE/INTEGRATE** — [WhitneyRoots](https://github.com/gasyoun/WhitneyRoots) owns the 935-root app; kosha adds frequency-rank + corpus attestation | [H950](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H950-Sonnet_kosha_pedagogy-w2-roots-frequency-corpus-integration_14.07.26.md) |
| **Metre (chandas)** | §3.9 | 🟡 **REUSE/INTEGRATE** — [SanskritKaraoke](https://github.com/gasyoun/SanskritKaraoke) owns the trainer; kosha wires metre-ID into reading | [H951](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H951-Sonnet_kosha_pedagogy-w3-metre-in-reading-integration_14.07.26.md) |
| **Script / Devanāgarī** | §3.8 | ⚪ **REUSE** — [csl-guides](https://github.com/sanskrit-lexicon/csl-guides) owns the quizzes; kosha role deferred (roadmap only) | — |
| **Audio / recitation** | §3.7 | ⬜ **AGENDA** — external-content-gated; no kosha build this plan | — |
| **RU gloss layer (Wave RU)** | §3.4 | 🟢 **BUILD** — additive Russian gloss language over reading packs; no sibling owns an RU reading surface (added 19-07-2026) | [H1278](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1278-Opus_kosha_pedagogy-wave-ru-inline-gloss-reader_19.07.26.md) |
| **Subhāṣita beginner reader (Wave RU)** | §3.4 | 🟢 **BUILD** — new pack family over public-domain Indische Sprüche (F33); subhāṣitas currently feed only PWG citations (added 19-07-2026) | [H1279](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1279-Fable_kosha_pedagogy-wave-ru-subhashita-reader_19.07.26.md) |

---

## Wave handoffs (minted 14-07-2026 via `mint_handoff.py --batch`)

| Handoff | Wave | Build | Executor |
|---|---|---|---|
| [H945](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H945-Opus_kosha_pedagogy-engine-room-build-plan_14.07.26.md) | — | Parent — this plan (done) | Opus 4.8 |
| [H946](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H946-Sonnet_kosha_pedagogy-w1-morphology-drills_14.07.26.md) | W1a | Morphology drills over the paradigm engine | Sonnet 5 |
| [H947](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H947-Sonnet_kosha_pedagogy-w1-vocabulary-frequency-curriculum_14.07.26.md) | W1b | Frequency-graded vocabulary curriculum | Sonnet 5 |
| [H948](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H948-Sonnet_kosha_pedagogy-w1-samasa-compound-trainer_14.07.26.md) | W1c | Samāsa (compound) analysis trainer | Sonnet 5 |
| [H949](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H949-Opus_kosha_pedagogy-w2-graded-reader-difficulty-scorer_14.07.26.md) | W2a | Graded-reader expansion + difficulty scorer | Opus 4.8 |
| [H950](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H950-Sonnet_kosha_pedagogy-w2-roots-frequency-corpus-integration_14.07.26.md) | W2b | Roots frequency + corpus attestation (integrate WhitneyRoots) | Sonnet 5 |
| [H951](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H951-Sonnet_kosha_pedagogy-w3-metre-in-reading-integration_14.07.26.md) | W3a | Metre-ID wired into reading (integrate SanskritKaraoke) | Sonnet 5 |
| [H1278](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1278-Opus_kosha_pedagogy-wave-ru-inline-gloss-reader_19.07.26.md) | W-RU-a | Inline Sa→Ru gloss layer in reading packs (minted 19-07-2026, queued) | Opus 4.8 |
| [H1279](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1279-Fable_kosha_pedagogy-wave-ru-subhashita-reader_19.07.26.md) | W-RU-b | Graded beginner subhāṣita reader, Indische Sprüche (minted 19-07-2026, queued) | Fable 5 |

---

## The autonomy contract (what each unattended wave agent runs under)

- **On unplanned ambiguity:** pick the plan's marked default and **log** it; press on. Do not halt.
- **Merge authority:** commit → open PR → **merge the green PR autonomously**, same pass. kosha is shared-tree-guarded — author in a `git worktree` off `origin/main`, never the canonical main tree.
- **Stop conditions:** stop only on a hard blocker — missing local data (`dcs-conllu`, `vidyut-data`), a failing build a marked default can't resolve, or a fence violation.
- **The fence (must NOT touch):** **csl-orig** source (corrections go via the monthly queue only); the **shipped sandhi programme data** (`data/sandhi/*`, `data/gita/gita_sandhi.tsv` — consume, never regenerate); **sibling-repo source** (WhitneyRoots, SanskritKaraoke, csl-guides, Systema — integrate via their published data/API, never fork into kosha). Standing **global** guardrails bind independent of the fence: no making anything newly public (Pages/visibility) and no publishing rights-gated corpus bulk without a human GO/NO-GO via [`/publish-safety-check`](https://github.com/gasyoun/claude-config/blob/main/commands/publish-safety-check.md).
- **Provenance / agent contract:** every deliverable records model tier + exact version; **any new/changed derived dataset earns a `datasets.json` manifest row in the same pass** (kosha standing rule); each `CHANGELOG.md` edit → `/cut-release`. No papers this cycle — surfaces + instrumentation only.

## Autonomy-readiness gate — verdict

Each wave-1 build has an architecture spec (ARCHITECTURE §), ordered file-level steps
(IMPLEMENTATION §), an acceptance criterion + risks (VERIFICATION §). Zero blocking forks
remain (all 12 decisions ruled). No scheduled build duplicates an existing asset — the
prior-art gate demoted roots/metre/script to reuse/integrate and audio to agenda. The
autonomy contract covers the plausible ambiguities. **Gate: PASS** — wave-1 (H946–H948)
is launchable unattended.

---

_Dr. Mārcis Gasūns_
