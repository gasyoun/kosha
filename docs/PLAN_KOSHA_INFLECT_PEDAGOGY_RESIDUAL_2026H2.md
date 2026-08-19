# PLAN — kosha inflect + pedagogy residual programme, 2026 H2 (index)

_Created: 19-08-2026 · Last updated: 19-08-2026_

Authored by Opus 5 (`claude-opus-5`) under
[H3001 (Opus 5) — Stale-roadmap slice 3: full /ask replan of stale Tier-1 roadmaps](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3001-Opus_multi_stale-roadmap-s3-tier1-ask-replan_17.08.26.md).
Slice-3 index: [PLAN_UPRAVA_STALE_ROADMAP_ASK_BATCH_2026-08.md](https://github.com/gasyoun/Uprava/blob/main/docs/PLAN_UPRAVA_STALE_ROADMAP_ASK_BATCH_2026-08.md).

## Why this programme exists

kosha carries two July roadmaps that the 17-08-2026 staging sweep flagged stale:
[ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md)
(05-07-2026) and
[docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md)
(22-07-2026). The slice-3 truth-pass ran
[`roadmap_handoff_truth.py`](https://github.com/gasyoun/Uprava/blob/main/tools/roadmap_handoff_truth.py)
over both: **all 20 handoffs they reference are closed ✅**. Neither file is
superseded — both stay living — but both were **lying about their own state**, in
the specific and expensive way a conditional roadmap lies: the condition fired and
the document never noticed.

| Lie | The document said | Reality |
|---|---|---|
| **Wave U2 conditional** | *"drip the rest only if Jim merges within ~a month, else park"* | [csl-inflect PR #17](https://github.com/sanskrit-lexicon/csl-inflect/pull/17) merged **03-07-2026, same day**. The condition fired six weeks ago; three finished branches sit unsent |
| **Wave E1 `🔶 pending`** | ruling + give-back + verbs all pending | [H185 (Opus 4.8) — kosha E1 dual-engine ruling](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md) closed 12-07-2026 ([v0.21.0](https://github.com/gasyoun/kosha/releases/tag/v0.21.0)): hybridize layer + verb comparison shipped; only the diplomacy-gated post is parked |
| **Wave RU `🟡 queued 19-07-2026`** | two queued handoffs | both shipped 19-07-2026 — H1278 ([v0.63.0](https://github.com/gasyoun/kosha/releases/tag/v0.63.0)) and H1279 |

The residual programme below is what is genuinely left after those three
corrections land.

## The five documents

| Layer | Document |
|---|---|
| Index (this) | [PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md) |
| Roadmap | [ROADMAP_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md) |
| Architecture | [ARCHITECTURE_KOSHA_INFLECT_PEDAGOGY_RESIDUAL.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_INFLECT_PEDAGOGY_RESIDUAL.md) |
| Implementation | [IMPLEMENTATION_KOSHA_INFLECT_PEDAGOGY_RESIDUAL.md](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_INFLECT_PEDAGOGY_RESIDUAL.md) |
| Verification | [VERIFICATION_KOSHA_INFLECT_PEDAGOGY_RESIDUAL.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_INFLECT_PEDAGOGY_RESIDUAL.md) |
| Metadoc | [PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.meta.md) |

## Decisions carried in (the interview)

Per slice-3 ruling **R3**, the batch rulings *are* the interview. These are
inherited, not re-opened:

| # | Source | Ruling carried forward |
|---|---|---|
| D1 | INFLECT D1 | **Hybrid venue** — the drastic tool lives in kosha; upstream gets ordinary on-their-merits PRs |
| D3 | INFLECT D3 | **Cologne tables as the base, vidyut layered over** — never a vidyut-only engine, never a Cologne row deleted |
| D5 | INFLECT D5 | **One upstream PR at a time.** Batch-opening on a noise-averse repo stays banned even now that the probe merged |
| D6 | INFLECT D6 | Research give-back on Jim's open questions is welcome; **posting** is diplomacy-gated |
| — | [RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) §2/§7 | No "we fixed your frontend" framing, no bot comments, no new correspondence channels — standing |
| — | PEDAGOGY | Rights gate on RU glosses: **public site-tier subset only** of [SanskritRussian](https://github.com/gasyoun/SanskritRussian) |
| slice-3 D4 | PLAN_UPRAVA_STALE_ROADMAP | Ambiguity → marked default + one log line + continue |

## Residual units

| # | Unit | Handoff | Gate |
|---|---|---|---|
| K1 | Wave U2 — drip the three prepared csl-inflect PRs | [H3165 (Sonnet 5) — Wave U2: drip the three prepared csl-inflect PRs](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3165-Sonnet_csl-inflect_inflect-u2-drip-prepared-prs_19.08.26.md) | none — condition fired 03-07-2026 |
| K2 | Verb dhātu-identity crosswalk (makes the 12.68 % figure interpretable) | [H3166 (Opus 5) — Verb dhātu-identity crosswalk](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3166-Opus_kosha_inflect-dhatu-identity-crosswalk_19.08.26.md) | none |
| K3 | `gloss.ru` re-run over the subhāṣita beginner pack | [H3167 (Sonnet 5) — Re-run gloss.ru over the subhāṣita beginner pack](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3167-Sonnet_kosha_pedagogy-subhashita-gloss-ru-rerun_19.08.26.md) | none |

## Not mintable — human acts, recorded so they stop being invisible

| # | What | Why an agent must not do it | The concrete human act |
|---|---|---|---|
| N1 | Post the ṇatva give-back on [csl-inflect#10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10) | Diplomacy-gated by [RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) §2/§7 — the draft exists and is *correct*; what is missing is a human's judgment that now is the moment to tell a dormant maintainer their data has a 20-year-old bug with a bigger blast radius than documented | A human reads the draft in [H185](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md) and either posts it or says "not yet". Nothing else waits on it — K1, K2 and K3 all proceed regardless |
| N2 | Scaffold the three-engine (Cologne/Huet/vidyut) divergence paper | INFLECT E1(c) says *"scaffold only if MG wants it"* — a paper is a publication commitment, not an engineering unit | A human says yes or no. Until then the E1 data simply sits available |

## Non-goals (do not re-propose)

- **Adopt/mirror** csl-inflect, **upstream-only**, or a **vidyut-only engine** — all three ruled out in INFLECT §4.
- Rebuilding roots ([WhitneyRoots](https://github.com/gasyoun/WhitneyRoots)), metre ([SanskritKaraoke](https://github.com/gasyoun/SanskritKaraoke)), or script ([csl-guides](https://github.com/sanskrit-lexicon/csl-guides)) surfaces — PEDAGOGY W3b is REUSE, permanently.
- **Audio** — PEDAGOGY Wave 4 is a 2028 external-gated agenda pointer, not a wave. kosha builds none.
- A second field metadoc; a new SRS engine; a course/LMS.
- Touching `csl-orig`, the shipped sandhi data, or sibling-repo source.

## Autonomy contract

1. **Ambiguity** → marked default, one log line, continue.
2. **Hard stop** → about to post upstream without the N1 go-ahead; about to open a second simultaneous upstream PR; about to widen the RU gloss source past the public site tier; about to edit a guarded main checkout.
3. **Not a stop** → N1 and N2 unruled. Every mintable unit proceeds without them.
4. **Commit authority** → session-unique worktree → PR → merge on `gasyoun/kosha`. `sanskrit-lexicon/*` by PR only, one at a time.

_Dr. Mārcis Gasūns_
