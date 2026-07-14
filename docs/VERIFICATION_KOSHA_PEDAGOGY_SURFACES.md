_Created: 14-07-2026 · Last updated: 14-07-2026_

# Verification — kosha pedagogy surfaces (acceptance + risks)

Cover: [`PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md).
Steps: [`docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE1.md`](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE1.md).

## Acceptance criteria per Wave-1 build

A build is **done** when all of its rows below pass — mirroring how the sandhi programme
defined done (dataset + page + manifest + tests + a coverage headline).

### W1a — Morphology drills ([H946](https://github.com/gasyoun/Uprava/blob/main/handoffs/H946-Sonnet_kosha_pedagogy-w1-morphology-drills_14.07.26.md))

| Check | Pass condition |
|---|---|
| Every drill item is answer-keyed | 100 % of items in `drills.json` have a non-empty `answer` **and** `evidence`; `tests/test_morphology_drills.py` green |
| No fabricated forms | in default mode, every drilled form has a DCS attestation (join on `form_key()`); unattested forms appear only under `--include-generated` |
| Coverage headline present | the curriculum prints "learn N paradigms → cover X % of attested nominal/verbal tokens" |
| Page renders | `reading/morphology/curriculum/index.html` loads self-contained, theme-aware, Devanāgarī + IAST/SLP1 toggle work |
| Manifest + release | `morphology-drills` row in `datasets.json`; `CHANGELOG.md` bumped + `/cut-release` |

### W1b — Vocabulary curriculum ([H947](https://github.com/gasyoun/Uprava/blob/main/handoffs/H947-Sonnet_kosha_pedagogy-w1-vocabulary-frequency-curriculum_14.07.26.md))

| Check | Pass condition |
|---|---|
| Monotone coverage | cumulative `coverage_pct` is non-decreasing down the curriculum; test asserts it |
| Every lemma resolves | each curriculum lemma links to a real kosha `/w/` card (no dead links) |
| Coverage headline | "learn N lemmas → read X %" table emitted from `coverage_pct` |
| Page + export | `reading/vocabulary/curriculum/index.html` renders; Anki `.apkg` exports and re-imports |
| Manifest + release | `vocab-curriculum` row; changelog + release |

### W1c — Samāsa trainer ([H948](https://github.com/gasyoun/Uprava/blob/main/handoffs/H948-Sonnet_kosha_pedagogy-w1-samasa-compound-trainer_14.07.26.md))

| Check | Pass condition |
|---|---|
| Gold agreement | every gold-seeded item's type matches the [`gita_morphology_gold.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_morphology_gold.tsv) `compound` column exactly |
| Evidence on every item | 100 % of items carry `evidence` (attestation / gold locus) |
| Type balance sane | the four types are all represented; distribution reported, not silently skewed |
| Page + cross-link | `reading/samasa/curriculum/index.html` renders and links out to the csl-guides `samasa-quiz` |
| Manifest + release | `samasa-trainer` row; changelog + release |

## Global acceptance (every wave)

- **Six-stage contract satisfied** (ARCHITECTURE §): source → rank → curriculum+drills+reference → page → manifest+tests → export.
- **Instrumentation:** the coverage metric is computed and surfaced (the learning-outcome instrument), even though no paper is written this cycle.
- **`pytest` green**, no regressions in the existing suite.
- **Provenance:** model tier + exact version recorded in the PR/changelog; a data-statement `.meta.md` follows the manifest row.

## Risks & mitigations

| # | Risk | Mitigation |
|---|---|---|
| R1 | **Morphology: unaccented DCS can't disambiguate class I/VI, IV/passive** (VisualDCS finding) | Surface the ambiguity in the drill (mark "class I or VI"), never fabricate a single answer; drop the cell from strict mode |
| R2 | **Over-generation** — the paradigm engine emits forms no text attests | Default-off filter (attested-only); `--include-generated` opt-in; mirrors the heritage-forms `default-off` decision |
| R3 | **DCS `Tense=Past` conflates aorist/perfect** | Carry the caveat into verb drills; do not present a false aorist/perfect distinction |
| R4 | **Samāsa: corpus-derived splits are unverified** (only the Gītā-gold subset is hand-checked) | Provenance flag on every item (gold vs DCS-derived); gold items only in strict mode; a review sheet before any public deck |
| R5 | **Difficulty scorer (W2a) subjectivity** — the weighting is a modelling choice, not a truth | Weights in a tunable JSON + a documented formula (the MG ruling); ship the formula honestly as one estimator, not "the" difficulty |
| R6 | **Frequency ≠ learnability** — `core_rank` order is a hypothesis, not proven pedagogy | The coverage metric measures *text coverage*, not learning gain; do not claim learning-gain without the (deferred) user study (field RQ4) |
| R7 | **Scope creep into a second field doc / a course** | The fence: this is a build layer; Systema owns courses, H912 owns the field definition |
| R8 | **Rights** — decks derived from CC BY-SA data inherit share-alike | `/publish-safety-check` + `/data-release` gate before any public deck; attribute DCS (Hellwig) + Cologne |

## Autonomy-readiness verdict

Every Wave-1 build has: an architecture spec (the six-stage contract), ordered file-level
steps (IMPLEMENTATION §W1a–c), acceptance criteria (above), and identified risks (above).
Zero blocking forks remain. No build duplicates an existing asset (prior-art gate in the
PLAN). **PASS — Wave 1 is launchable unattended.**

---

_Dr. Mārcis Gasūns_
