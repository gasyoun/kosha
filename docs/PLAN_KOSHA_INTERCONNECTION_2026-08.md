# Plan — kosha interconnection, 2026-08

_Created: 26-08-2026 · Last updated: 26-08-2026_

kosha's slice of the spine-interconnection programme. Programme index:
[PLAN_SPINE_INTERCONNECTION_2026H2.md](https://github.com/gasyoun/Uprava/blob/main/docs/PLAN_SPINE_INTERCONNECTION_2026H2.md).

Architecture and verification are **not** restated here (ruling F13) — they are identical for
all fourteen repos and live once in Uprava:

- [ARCHITECTURE_SPINE_INTERCONNECTION.md](https://github.com/gasyoun/Uprava/blob/main/docs/ARCHITECTURE_SPINE_INTERCONNECTION.md) — the five attachment points and the rules governing them
- [IMPLEMENTATION_SPINE_INTERCONNECTION_W1.md](https://github.com/gasyoun/Uprava/blob/main/docs/IMPLEMENTATION_SPINE_INTERCONNECTION_W1.md) — execution order, per-handoff steps, isolation, risks
- [VERIFICATION_SPINE_INTERCONNECTION.md](https://github.com/gasyoun/Uprava/blob/main/docs/VERIFICATION_SPINE_INTERCONNECTION.md) — the five gates and what "done" means

**Nothing here has executed.** The handoff below is 🟡 queued and runs only when a human
launches it.

## Why kosha is in scope

kosha owns `datasets.json`, which overlaps Uprava's DATA_LAYERS_CENSUS. Ruling F7 declined to merge them, so the work is to make the boundary explicit rather than to move anything.

## Measured baseline and target

| | Value |
|---|---|
| Wiring score, 26-08-2026 | **80** / 100 |
| Target after this plan | **80** / 100 |
| How the target is reached | Unchanged at 80, and deliberately so: a scope line and a pointer clarify without adding artefacts. This is the clearest case that the score is a thermometer, not a goal. |

Measured by [`tools/interconnection_audit.py`](https://github.com/gasyoun/Uprava/blob/main/tools/interconnection_audit.py); full row in
[data/interconnection_audit_2026-08-26.json](https://github.com/gasyoun/Uprava/blob/main/data/interconnection_audit_2026-08-26.json);
report [AUDIT_REPO_INTERCONNECTION_2026-08-26.md](https://github.com/gasyoun/Uprava/blob/main/docs/AUDIT_REPO_INTERCONNECTION_2026-08-26.md).

The score counts artefacts, not whether they are true. It is **report-only** by ruling F2 and no
handoff closes on it — verification Gates 2 to 4 are what actually decide, and Gate 4 is read by
a human.

## Rulings that apply here

| Fork | Ruling |
|---|---|
| F7 | `datasets.json` and DATA_LAYERS_CENSUS stay separate, each gaining one scope line. |
| F1 | Local `FINDINGS.md` in exactly four repos; the other eight get a `CLAUDE.md` pointer line. No repo gains the other seven registries. |

Full rulings table with every fork:
[ASK_BATCH_STAGING_REPO_INTERCONNECTION_2026-08.md](https://github.com/gasyoun/Uprava/blob/main/ASK_BATCH_STAGING_REPO_INTERCONNECTION_2026-08.md) Phase 2.

## What this plan does

1. Add one scope line documenting `datasets.json` as the manifest for **published, fetchable** datasets, and naming DATA_LAYERS_CENSUS.md as the human survey of large on-disk data including the unpublishable (F7). The mirror line lands under the Uprava handoff.
2. Add the FINDINGS routing pointer line to kosha's `CLAUDE.md` (F1). **No registry files** — kosha is not in the four-repo middle tier.

## Handoff

- [H3565 (Sonnet 5) — interconnect kosha datasets scope line](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3565-Sonnet_kosha_interconnect-kosha-datasets-scope-line_26.08.26.md) · trivial · 🟡 queued

## Autonomy contract

The launching agent may create the files named above, add hub rows, open and merge its PR,
remove its worktree and close its handoff row — without asking.

It must stop and ask if a local `FINDINGS.md` cannot be given two genuine findings (the
documented fallback is to drop the file and take the pointer line, recorded not silent), if a
corpus row would carry an unmasked snapshot or quote a sample, or if a second speculative edge
becomes necessary. It must never turn the wiring score into a failing gate, commit to
`csl-orig`, or add the seven non-FINDINGS registries.

## Open @DECIDE

None. Every fork touching kosha was ruled in sitting 1 on 26-08-2026, so the autonomy gate
passes and nothing in the wave-1 path stalls on a human.

_Dr. Mārcis Gasūns_
