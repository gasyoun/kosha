_Created: 14-07-2026 · Last updated: 14-07-2026_

# Metadoc — PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md

Companion record for [`PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md)
— the "document about the document" a fresh session reads before editing the kosha pedagogy
build plan.

## Purpose

kosha's **build layer** for digital Sanskrit pedagogy — the engine-room half of the field
whose org-wide definition lives in
[`DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md`](https://github.com/gasyoun/SanskritGrammar/blob/main/DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md)
(SanskritGrammar, H912). It generalises the shipped corpus-sandhi programme's six-stage
pattern to morphology, vocabulary, compounds, and reading, and integrates roots/metre from
sibling repos. It is a repo build plan, **not** a second field metadoc.

## Audience

The agents executing the wave handoffs (H946–H951) and any session deciding what kosha
should build next in pedagogy. Not a learner-facing doc.

## Provenance

- **Method:** [`/ask`](https://github.com/gasyoun/claude-config/blob/main/commands/ask.md) — front-loaded interview (scope/home/thesis/dimensions/output over 3 rounds) then the layered plan. The interview surfaced a **prior-art collision**: the org-wide field metadoc + research plan already existed (H912, shipped the same day). The user chose "kosha build-plan (engine room)" — build the layer H912 deferred, do not duplicate the field definition.
- **Model:** Opus 4.8 (`claude-opus-4-8`), 14-07-2026.
- **Audit basis:** kosha internal sweep (paradigm/frequency/compound/reading/concordance assets) + a cross-repo pedagogy-asset inventory (Systema, SanskritGrammar, csl-guides, SanskritKaraoke, WhitneyRoots, VisualDCS) grounding the build-vs-reuse verdicts.
- **Handoffs:** parent [H945](https://github.com/gasyoun/Uprava/blob/main/handoffs/H945-Opus_kosha_pedagogy-engine-room-build-plan_14.07.26.md); waves H946–H951 (`mint_handoff.py --batch`).

## Ranked improvement backlog

1. **Fold the coverage metric into a single shared helper** — every wave recomputes "learn N → cover X %"; a `scripts/lib/coverage.py` would keep the instrument identical across surfaces (and make RQ4 comparisons apples-to-apples).
2. **A shared drill-item validator** — one schema-check (`answer` + `evidence` present, provenance flagged) reused by every wave's tests, so "no unverified item" is enforced once.
3. **Reconcile with the field doc's §4a matrix** — as each surface ships, add its row to the field doc's aspect (H912 §8 asks for exactly this: an asset row in the field doc + a line in the owning repo's map).
4. **Decide the difficulty-scorer estimator (W2a) explicitly** — the vocab×sandhi×morph×compound weighting is a modelling choice; pin it in a config + a short methods note before it drives graded-reader levelling.
5. **Last-mile JSON contract with Systema** — align the stage-⑥ item shape with the H916 last-mile pipeline spec so the LMS consumes one schema.

## Limitations

- **Build-vs-reuse verdicts are point-in-time** (14-07-2026) — re-check WhitneyRoots / SanskritKaraoke / csl-guides scope before executing W2b/W3a; a sibling may have moved.
- **No paper track here by choice** — the field's research/paper spine is H912/A62/A32/A60; this plan is surfaces only. If a measurable result emerges, route it to the field, do not paperise here.
- **Wave 2–4 are roadmap-level**, not file-level — only Wave 1 (H946–H948) carries full implementation steps; later waves get their own implementation pass at kickoff.

## Related docs

- Field definition: [`DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md`](https://github.com/gasyoun/SanskritGrammar/blob/main/DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md) (+ its meta).
- Layer docs: [roadmap](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md) · [architecture](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md) · [implementation](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE1.md) · [verification](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md).
- The reference implementation: [`SANDHI_PROGRAMME.md`](https://github.com/gasyoun/kosha/blob/main/SANDHI_PROGRAMME.md).

## Revision history

| Date | Change | Model |
|---|---|---|
| 14-07-2026 | Created — kosha pedagogy build plan; 4 build waves + 2 integrate + 1 agenda; wave handoffs H946–H951 minted | Opus 4.8 (`claude-opus-4-8`) |

---

_Dr. Mārcis Gasūns_
