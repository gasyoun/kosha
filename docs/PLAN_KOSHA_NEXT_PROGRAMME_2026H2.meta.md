# Metadoc — PLAN_KOSHA_NEXT_PROGRAMME_2026H2

_Created: 24-07-2026 · Last updated: 24-07-2026_

## Purpose

Companion record for the kosha post-A4 / post-sense-W1 multi-wave plan. Holds
provenance, improvement backlog, and limitations so a later session does not
re-interview closed forks.

## Audience

- Execution agents launching wave handoffs
- Human reviewing autonomy gate before `/go`
- Future `/ask-batch --resume` on kosha

## Provenance

| Field | Value |
|---|---|
| Skill | `/ask-batch --repos kosha` (re-batch 24-07-2026) |
| Staging | [ASK_BATCH_STAGING_KOSHA_2026-07-24.md](https://github.com/gasyoun/Uprava/blob/main/ASK_BATCH_STAGING_KOSHA_2026-07-24.md) |
| Model (authoring) | Grok 4.5 (`grok-4.5`) |
| Interview | 2 sittings, 8 rulings (N1–N8) + defaults N9–N12 |
| Prior batch | [ASK_BATCH_STAGING_2026-07.md](https://github.com/gasyoun/Uprava/blob/main/ASK_BATCH_STAGING_2026-07.md) row 4 (18-07, superseded for next work) |

## Ranked improvement backlog

1. After W3 ships, re-evaluate whether Apte coverage in the pilot is empty — expand extract if nulls dominate.
2. Promote pilot cross-dict to full inventory only after the deferred human sample pass.
3. If samskrtam.ru deploy slips >2 weeks, re-open N6 and re-park W5 live exit checks.
4. Consider computed-table gate for budget log rows (derive-don't-store).
5. Archive executed residual handoffs still sitting in active `handoffs/` (registry hygiene).

## Limitations

- Assumes local `kosha.db` / DCS sqlite available for W3–W5; CI may skip DB-gated tests.
- SCL licence (H057) still open — architecture depends on gitignored cache + no redistribution.
- "Assume deploy within days" can be wrong; verification forces honest blocked labels.
- Does not replace sibling plan docs for A4 W1–W3 or sense W1 — those remain historical record of shipped work.

## Related docs

- [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md)
- [DATA_HUB_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md)
- [P5_ADVANCED_UI_DESIGN.md](https://github.com/gasyoun/kosha/blob/main/P5_ADVANCED_UI_DESIGN.md)

## Revision history

| Date | Change |
|---|---|
| 24-07-2026 | Initial metadoc with plan set |

---

_Dr. Mārcis Gasūns_
