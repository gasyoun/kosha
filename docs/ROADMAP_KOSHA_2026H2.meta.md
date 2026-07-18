# Metadoc — ROADMAP_KOSHA_2026H2.md

_Created: 18-07-2026 · Last updated: 18-07-2026_

Companion record for [ROADMAP_KOSHA_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026H2.md).
It exists because the roadmap is registered in
[Uprava/ROADMAP_INDEX.md](https://github.com/gasyoun/Uprava/blob/main/ROADMAP_INDEX.md) and is
therefore consulted independently of the plan set it came from — a reader can arrive here without
ever seeing [PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md).

## Purpose

State the wave order for kosha's 2026 H2 under the rulings recorded in the plan, so a fresh session
can pick up the next wave without re-deriving why the programme is shaped this way.

## Audience

A future agent session picking up a kosha wave; and a human scanning ROADMAP_INDEX for what kosha is
committed to this half-year.

## Provenance

| Field | Value |
|---|---|
| Produced by | [`/ask-batch`](https://github.com/gasyoun/claude-config/blob/main/commands/ask-batch.md) 2026-07 pass 2 (`--resume`, slice 2), 18-07-2026 |
| Control doc | [ASK_BATCH_STAGING_2026-07.md](https://github.com/gasyoun/Uprava/blob/main/ASK_BATCH_STAGING_2026-07.md) |
| Model | Opus 4.8 (`claude-opus-4-8`) — audit, authoring, adversarial verify, and patch passes |
| Rulings | Human, 17-07 and 18-07-2026; recorded in the plan's decisions-taken table |
| Wave-1 handoffs | H1262–H1267 (all 🟡 queued at authoring time) |

## Limitations

| # | Limitation |
|---|---|
| L1 | Written the same day the repo's build queue emptied. The premise "there is nothing agent-runnable left" is a snapshot; concurrent sessions mint constantly, and four handoffs landed in this repo's neighbours *during* the authoring pass. |
| L2 | The Pāṇini programme is named **Q3** in the ruling and **A4/Q4** in [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md). The plan reconciles the two names in its §1; this roadmap inherits that reconciliation rather than repeating it. |
| L3 | A3 (the attested-form join) was found missing during authoring and absorbed into wave 1 as the long pole. Its cost is an estimate, not a measurement — nothing comparable has been built in this repo. |
| L4 | The DCS licence is contested *inside kosha's own files* (`external_tools.json` says CC BY-SA 4.0; `CONCORDANCE_ROADMAP.md`:151 and the `reading-pack-*` rows say CC BY 4.0). H1263 resolves it. Until then every licence statement downstream is provisional. |
| L5 | H1262's fill pass measured that ~93.3% of the non-heritage generated form set is itself DCS-derived, which would make a raw attested-vs-generated join substantially circular. This is surfaced as a stop-and-report item, **not** resolved — it may reshape or invalidate the A3 wave. |

## Improvement backlog

| Rank | Item | Why |
|---|---|---|
| 1 | Resolve the A3 circularity (L5) before committing to the full join | If 93.3% of the generated side is DCS-derived, the headline "attested ∧ generated" number measures the pipeline, not the language. This is the single finding most likely to change the programme. |
| 2 | Settle the DCS licence contradiction (L4) | It blocks publication of any A4 dataset and it is currently wrong in at least one committed kosha file. |
| 3 | Replace the deploy-interim language once samskrtam.ru lands | The roadmap assumes GitHub Pages as an explicit interim with a named migration step; that assumption expires when the deploy happens (expected ~25-07-2026). |
| 4 | Re-derive the release/commit counts per window | The authoring pass shipped two different windows' numbers side by side once already; the corrected form should be checked rather than trusted. |

## Related

- [PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md) — the index this roadmap serves, and its own `.meta.md`
- [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md) — the parent programme doc
- [DATA_HUB_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md) — the data-hub track the D-rulings land in

## Revision history

| Date | Change | Model |
|---|---|---|
| 18-07-2026 | Created alongside the roadmap in the `/ask-batch` slice-2 pass | Opus 4.8 (`claude-opus-4-8`) |

_Dr. Mārcis Gasūns_
