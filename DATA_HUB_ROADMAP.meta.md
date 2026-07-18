# DATA_HUB_ROADMAP.meta.md — metadoc for `DATA_HUB_ROADMAP.md`

_Created: 18-07-2026 · Last updated: 18-07-2026_

This is a **metadoc** — a document *about* a document. Its subject is
[DATA_HUB_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md).
It does not duplicate the subject's content; it records everything *around* it. Kept per the
standing "one metadoc per important document" convention (`~/.claude/CLAUDE.md`).

## Subject
- **Document:** [DATA_HUB_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md)
- **Purpose:** Locks kosha's role as the org's Sanskrit **data-hub** — the place that hosts
  bytes (not just catalogues them), fixing the census finding that 70% of derived data
  (19.2 GB) sits local-only/gitignored/unbackuped and unreusable. Records the 8 locked
  decisions (D-HUB-1…8), the two-tier (public/restricted) architecture, and the P-D0…P-D6
  phase table.
- **Audience:** Any agent session about to derive/reuse a dataset anywhere in the org
  (via `/prior-art`), plus the human deciding the samskrtam.ru deploy gate (P-D4) and the
  archive_stopword.sqlite split-or-exclude ruling (P-D2, H233).
- **Format / contract:** Locked-decisions table (D-HUB-#) is append-only — decisions are
  never silently revised, only superseded with a new row citing the old one. The phase
  table's Status column must track ✅/🟡/⛔ against real handoffs, not aspirational.

## Provenance
- **Created:** 18-07-2026 (handoff H968, Sonnet 5 `claude-sonnet-5`); the roadmap itself
  was authored 06-07-2026 (Fable 5 `claude-fable-5`-run MG interview).
- **Next hardening:** none scheduled — updates ride on P-D2/P-D4/P-D5/P-D6 landing.

## Improvement backlog (ranked)

| # | Improvement | Why | Status |
|---|---|---|---|
| 1 | Resolve the `archive_stopword.sqlite` (11 GB) split-or-exclude question blocking P-D2 | P-D2 (restricted-tier backup, kills single-copy risk on the 19.2 GB census giants) cannot close without it | queued (H233) |
| 2 | MG deploy gate for samskrtam.ru canonical hosting (P-D4) | Everything downstream (P-D5 queryable DB, P-D6 API tier) is sequenced after P-D4 | parked: MG deploy gate (GTD @DO) |
| 3 | Add a manifest-completeness check to CI (every dataset in `datasets.json` has a matching public/restricted classification) | Rule "every changed/new derived dataset ends its session with a manifest row" is currently honor-system, no enforcement | parked: no CI in this repo yet (per root `CLAUDE.md`) |
| 4 | Cross-link this roadmap from `Uprava/PROJECT_INTERLINKS.md`'s data-hub row once P-D4 lands | Keeps the hub-of-hubs pointer current instead of just the census | parked: do at P-D4 landing |

## Known limitations / caveats
- The roadmap describes an *architecture*, not a working deploy — P-D4 (samskrtam.ru
  canonical hosting) is gated on a human action (MG deploy gate) with no committed date;
  reading the phase table as a timeline overstates certainty.
- P-D1's "already public in their source repos" claim for the first data release
  (mw_roots, mw_etymology, etc.) should be re-verified against each source repo's actual
  license file before reuse by an external consumer — the roadmap asserts it but does not
  re-derive it per-asset.
- The two-tier rights model (D-HUB-6) depends on `/publish-safety-check` being run on every
  public-tier addition; the roadmap states the rule but enforcement is procedural, not
  automated.

## Intended use / known misuse
- **For:** orienting any session that is about to derive, publish, or look for a reusable
  Sanskrit NLP dataset — read this before rebuilding an existing asset.
- **Misuse:** treating the phase table as guaranteeing P-D4/P-D5/P-D6 are scheduled — they
  are gated (⛔/🟡), not committed dates. Also misuse: adding a new dataset without a
  `data/manifest/datasets.json` row and citing this roadmap as sufficient documentation —
  the roadmap is the policy, the manifest is the enforcement point.

## Maintenance & sunset plan
- Owner: whichever session executes the next P-D phase updates the Status column in the
  same pass (per the roadmap's own "Rules" section).
- Sunset trigger: once P-D6 (API tier) ships and the hub role is fully realized, this
  roadmap is superseded by an operational runbook (candidate:
  [docs/PIPELINE_OPERATOR_RUNBOOK.md](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.md)
  absorbing the hub-serving concerns) — not yet triggered.

## Deprecation status
`active`

## Related documents
- [data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) — the machine-readable enforcement point this roadmap mandates.
- [IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md) — kosha's own P1–P7 engineering plan; the data-hub role is additive to it.
- [docs/PIPELINE_OPERATOR_RUNBOOK.md](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.md) and its [metadoc](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.meta.md) — sibling operational doc, already metadoc-covered.
- [Uprava/DATA_LAYERS_CENSUS.md](https://github.com/gasyoun/Uprava/blob/main/DATA_LAYERS_CENSUS.md) — the census this roadmap responds to.
- [Uprava/PROJECT_INTERLINKS.md](https://github.com/gasyoun/Uprava/blob/main/PROJECT_INTERLINKS.md) — cross-repo "who owns what data" ledger this roadmap should eventually register into.

## Revision history

| Date | Event | Who (tier+version) |
|---|---|---|
| 06-07-2026 | Roadmap authored (D-HUB-1…8 locked, P-D0/P-D1/P-D3 marked done) | Fable 5 `claude-fable-5` |
| 18-07-2026 | Metadoc backfilled (H968) | Sonnet 5 `claude-sonnet-5` |

_Dr. Mārcis Gasūns_
