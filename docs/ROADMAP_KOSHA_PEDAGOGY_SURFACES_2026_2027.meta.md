_Created: 15-07-2026 · Last updated: 15-07-2026_

# Metadoc — kosha pedagogy surfaces roadmap

Companion to [ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md).

## Purpose
The wave-by-wave plan for kosha's learner-facing pedagogy build layer: it instantiates
the shipped sandhi programme's six-stage pattern (source → rank → curriculum+drills+reference
→ page → manifest+tests → export) for every other aspect kosha can teach. Onboards a fresh
session into *what has shipped, what each surface consumes, and which build-vs-reuse verdict
applies* — so the next wave is a small marginal-cost instantiation, not a fresh design.

## Audience
Engineering sessions (Sonnet+ for the BUILD surfaces, Opus for the difficulty-metric
judgment call) picking up a wave; a human owner ruling on the difficulty-scorer weighting
(W2a, R5) and on rights before any public deck (R8). Pairs with the architecture spec
([`ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md))
and the acceptance/risks doc
([`VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md)).

## Provenance
- **Minted:** parent [H945](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H945-Opus_kosha_pedagogy-engine-room-build-plan_14.07.26.md), 14-07-2026, via [`/ask`](https://github.com/gasyoun/claude-config/blob/main/commands/ask.md) ([kosha PR #103](https://github.com/gasyoun/kosha/pull/103)). Sibling of the engine-room plan [`PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md); subordinate to the org field metadoc [`DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md`](https://github.com/gasyoun/SanskritGrammar/blob/main/DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md) (H912) — it builds the layer H912 deferred, does not restate the field.
- **Author model:** Opus 4.8 (`claude-opus-4-8`).
- **Wave handoffs:** H946 (W1a) · H947 (W1b) · H948 (W1c) · H949 (W2a) · H950 (W2b) · H951 (W3a), minted `mint_handoff.py --batch`.
- **Grounded, not speculative:** the build-vs-reuse verdicts came from a kosha internal asset sweep + a cross-repo pedagogy-asset inventory (Systema, SanskritGrammar, csl-guides, SanskritKaraoke, WhitneyRoots, VisualDCS), so REUSE surfaces (roots→WhitneyRoots, metre→SanskritKaraoke, script→csl-guides) do not rebuild an existing app.

## Status (as of 15-07-2026)
Waves 0–2 are **fully shipped**; the roadmap's status column carries the release per surface.

| Wave | Surface | State |
|---|---|---|
| 0 | Sandhi (reference impl.) | ✅ shipped (H882–H918) |
| 1a | Morphology drills | ✅ v0.54.0 (H946) |
| 1b | Vocabulary curriculum | ✅ v0.51.0 (H947) |
| 1c | Samāsa trainer | ✅ v0.52.0 (H948) |
| 2a | Difficulty scorer + graded readers | ✅ v0.55.0 (H949) |
| 2b | Roots frequency layer | ✅ v0.50.0 (H950, reuse/integrate) |
| 3a | Metre-in-reading | ✅ v0.59.0 (H951, reuse/integrate) |
| 3b | Script / Devanāgarī | ⚪ roadmap-only (csl-guides owns it) |
| 4 | Audio | agenda — external-gated (recorded reciter / TTS decision) |

## Ranked improvement backlog (of the roadmap itself)
1. ~~**W3a is the only actionable wave left.**~~ **DONE (H951, 15-07-2026, v0.59.0):**
   W3a shipped (per-verse metre annotation, reuse/integrate). **The kosha build programme
   is now complete** — every buildable surface (W1a–c, W2a–b, W3a) is shipped; only W3b
   (reuse-only, csl-guides owns it) and W4 (external-gated audio agenda) remain, neither a
   kosha build. Row + status table flipped this pass (the §84 stale-row discipline held).
2. **Difficulty-scorer weighting is unconfirmed (W2a/R5).** The scorer shipped with
   defensible default weights in [`difficulty_weights.json`](https://github.com/gasyoun/kosha/blob/main/data/difficulty/difficulty_weights.json)
   but "a human should confirm" is still open. Record the ruling here + in the W2a data
   statement once made, the way the sandhi roadmap recorded its difficulty-metric ruling.
3. ~~**The 18 Gītā reading packs are unscored** (no UD morphology).~~ **DONE (H977,
   15-07-2026, v0.57.0):** took option (b) — a reduced 3-axis score (vocab + the packs'
   own per-token `sandhi` field + hyphen-compound), a **separate** `gita_reading_pack_difficulty.tsv`
   ordering ranked among the Gītā chapters only, explicitly not comparable to the UD 4-axis
   packs (different axes + a different sandhi definition). Remaining option (a) — re-annotate
   the Gītā packs with UD features so they fold into the single 4-axis ranking — stays open
   as a nicer-but-larger future.
4. **W4 audio has no concrete entry condition.** It waits on an external content decision
   (reciter or TTS) owned at the field/Systema level (H912 Wave 4); the roadmap should link
   the decision once it exists rather than leave "agenda".

## Limitations / known gaps
- The roadmap states verdicts + unblock-conditions, **not** measured outcomes — those live
  in each surface's CHANGELOG entry, manifest row, data statement, and (for W2a) METHODS.md.
  Do not read a ✅ here as a claim about *learning* gain (frequency ≠ learnability, R6).
- The six-stage contract is a *shape*; each wave still makes aspect-specific judgment calls
  (e.g. W2a's four difficulty axes, W1a's class I/VI ambiguity handling) that the roadmap
  does not spell out — read the surface's own handoff + verification row.
- Cross-repo REUSE surfaces (W2b/W3a/W3b) depend on the consuming repo (WhitneyRoots /
  SanskritKaraoke / csl-guides) actually wiring the emitted data layer; the roadmap tracks
  the kosha-side data, not the downstream UI integration.

## Intended use / known misuse
**For:** onboarding a session before it picks up the next pedagogy wave (which surface,
what it consumes, build-vs-reuse verdict); a human checking wave status at a glance.
**Misuse:** reading a ✅ SHIPPED marker as a *learning-outcome* claim (it is a build
status; frequency ≠ learnability, R6) — outcomes belong to the deferred user study;
treating the roadmap as the source of truth for a surface's *measured* results (those
live in each surface's CHANGELOG, manifest row, data statement, and METHODS.md); reading
a REUSE surface's ✅ as "the downstream app is wired" (it marks the kosha-side data layer
only). Do not add a surface here without its build-vs-reuse verdict grounded in the
cross-repo asset sweep — the whole point is not to rebuild what another repo owns.

## Maintenance & sunset plan
Updated per wave, in the same pass the wave ships: flip the surface's roadmap-table row
to ✅ with its release version, and tick this metadoc's status table + revision history
with it (the §84 stale-row discipline — a shipped surface left at 🟢 BUILD re-invites a
duplicate build). Only W3a (H951) remains actionable; W3b is roadmap-only and W4 is an
external-gated agenda. Sunset: when W3a ships and W4's external content decision is made,
the build programme is complete — at that point this roadmap becomes a historical record
of the pedagogy-surface build-out and its status table freezes; it is superseded, not
deleted (the shipped surfaces remain the reference).

## Deprecation status
`active` — the plan of record for kosha's pedagogy-surface build-out (Waves 0–2 shipped,
W3a next).

## Related
- Plan (cover): [`PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md) (+ its metadoc).
- Architecture: [`docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md).
- Acceptance/risks: [`docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md).
- Reference implementation it generalises: [`ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md) (+ its metadoc) · [`SANDHI_PROGRAMME.md`](https://github.com/gasyoun/kosha/blob/main/SANDHI_PROGRAMME.md).
- Org field metadoc it serves: [`DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md`](https://github.com/gasyoun/SanskritGrammar/blob/main/DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md) (H912).

## Revision history
| Date | Model | Change |
|---|---|---|
| 14-07-2026 | Opus 4.8 `claude-opus-4-8` | Roadmap created (H945, `/ask`): Waves 1–4 planned over the shipped Wave-0 sandhi pattern; build-vs-reuse verdicts set from a cross-repo asset sweep. |
| 15-07-2026 | Opus 4.8 `claude-opus-4-8[1m]` | Metadoc created. Recorded that Waves 0–2 are fully shipped (W1a–c, W2a, W2b) with per-surface releases and W3a unblocked; seeded the improvement backlog (W3a flip discipline, W2a weighting ruling, unscored Gītā packs, W4 entry condition). |
| 15-07-2026 | Opus 4.8 `claude-opus-4-8[1m]` | Added the three template-v2 sections (Intended use / known misuse · Maintenance & sunset plan · Deprecation status) so the metadoc registers 3/3 in the org census. |
| 15-07-2026 | Opus 4.8 `claude-opus-4-8[1m]` | Backlog item 3 (18 Gītā packs unscored) closed via H977 — reduced 3-axis Gītā ordering (v0.57.0). |
| 15-07-2026 | Opus 4.8 `claude-opus-4-8[1m]` | W3a metre-in-reading shipped (H951, v0.59.0) — status table + backlog item 1 flipped; **kosha build programme complete** (W3b reuse-only, W4 external-gated remain). |
| 19-07-2026 | Fable 5 `claude-fable-5` | Wave RU appended (queued, H1278/H1279): inline Sa→Ru gloss layer + beginner subhāṣita reader; implementation doc `IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE_RU.md` authored; rights gate recorded. |

_Dr. Mārcis Gasūns_
