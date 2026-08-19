# ARCHITECTURE — kosha inflect + pedagogy residual

_Created: 19-08-2026 · Last updated: 19-08-2026_

Index: [PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md).

## The shape all three units share

Every unit here is **additive over an existing shipped layer**. None replaces a
table, an engine, or a curation decision. That is not modesty — it is the
constraint that makes the work safe to run without a human in the loop.

```
Cologne tables (Jim's 20 years of hand-correction)   ← never deleted
        │
        ├─ inflections sidecar (K1 ingest, shipped)
        │       │
        │       └─ hybrid layer (H185: vidyut over Cologne, disputed=1 flags)
        │                │
        │                └─ K2: dhātu-identity crosswalk ── re-run verb compare
        │
reading packs (W2a difficulty-scored)
        └─ ru_gloss_layer.tsv (H1278) ──▶ K3: apply to subhāṣita pack
```

## K2 — why an identity layer, not a better comparator

The verb comparison currently reports 12.68 % strict agreement against 90.5 % for
nominals. The tempting reading is *"vidyut and Cologne disagree wildly about
verbs"*. The likelier reading, and the one H185 recorded, is that the two engines
**key roots differently** — anubandhas, gaṇa membership, prefix decomposition,
homophonous dhātus — so most "disagreements" are two engines confidently inflecting
what they each believe is a different root.

Architecturally this means the fix belongs **between** the engines, not inside
either. A crosswalk table with an explicit `match_basis` column keeps the two
engines untouched and makes the comparison a function of a reviewable artifact
rather than of code nobody re-reads.

The failure mode to design against: a crosswalk that maximises matches. Collapsing
two genuinely distinct dhātus onto one row raises agreement and destroys the
measurement. Hence `match_basis` is mandatory per row and `ambiguous-multi` is a
first-class class, not a silent drop.

**Reporting invariant:** matched-subset agreement is meaningless without the
unmatched residue printed beside it. Both numbers or neither.

## K1 — the channel, not the payload

The three branches are built and tested; nothing about them is an engineering
question. The architecture that matters is **the drip protocol itself**: one open
PR at a time, each gated on the previous merge.

That protocol is a cheap, self-terminating probe of a dormant maintainer's
attention. Batch-opening would convert a signal into noise and, per
[RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) §2, into
the exact posture the org has ruled against. The protocol's stopping rule is its
whole value: **first non-merge parks the queue**, and parking is a success
outcome, not a failure.

## K3 — join, not re-curate

The subhāṣita pack's content decisions (the 106-saying band, the 144-row reject
log, the metre tags) are finished work. K3 attaches a gloss column and reports
coverage; it must not reach back into curation.

The rights boundary is architectural, not procedural: the gloss builder's input is
the **public site-tier subset** of SanskritRussian. Restricted layers may inform
local work but must not reach a published artifact. A coverage number that rose
because the source widened is a rights incident, not an improvement.

## Cross-cutting invariants

| Invariant | Why |
|---|---|
| No Cologne row deleted, ever | D3; and Jim's hand-corrections are irreplaceable |
| Additive columns + provenance (`resolved_by`, `cell_notes`, `match_basis`) | The shipped pattern since K2a; lets any number be traced to its source engine |
| One upstream PR open at a time | D5 + RELATIONS §2 |
| Published RU glosses = public site-tier subset only | Standing rights gate |
| Measure before ruling | D3's discipline; H185 honoured it for nominals, K2 inherits it for verbs |

_Dr. Mārcis Gasūns_
