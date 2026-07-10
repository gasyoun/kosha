# PIPELINE_OPERATOR_RUNBOOK.md — metadoc

_Created: 10-07-2026 · Last updated: 10-07-2026_

Companion record for
[docs/PIPELINE_OPERATOR_RUNBOOK.md](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.md).

## Purpose & audience

The single operational spine of the kosha data chain (DB build → API → static
cache → Pages → inflection ingest) for an operator on a fresh machine or a
fresh session after context loss. It answers *what to run, in what order, how
to verify, what breaking looks like, what never to touch* — and deliberately
nothing else (design rationale stays in ARCHITECTURE/PHASE1_PLAN; per-script
detail stays in docstrings).

## Provenance

Authored 10-07-2026 by Fable 5 (`claude-fable-5`) under
[H501](https://github.com/gasyoun/Uprava/blob/main/handoffs/H501-Fable_kosha_operator_runbook_manual_10.07.26.md)
(the Fable manuals programme, manual-coverage census 10-07-2026; stub authored
+ executed in one pass at MG's direction). Shipped in
[PR #39](https://github.com/gasyoun/kosha/pull/39). Every command/flag was
cross-checked against the script source at commit `45a4bc67` (e.g. the seven
`build_db.py --stage` values were read from its argparse, the TSV/card counts
from the docstrings) — nothing recalled from memory.

## Known limitations / caveats

- Command surface reflects `scripts/` as of 10-07-2026; a new build stage or a
  renamed script silently ages §2/§8 — see maintenance rule below.
- Latency/size numbers are deliberately absent (they live in `measure_d5.py`
  output, machine-specific).
- The Pages deploy description assumes the legacy branch-root builder; if the
  repo moves to Actions-based Pages deploy, §0/§4 need a rewrite.

## Improvement backlog (ranked)

1. *(open)* Add a smoke-test one-liner per stage (row-count SQL per table) so
   verification doesn't require the full pytest run.
2. *(open)* Fold in the restricted-tier (`deploy_guhya`) inventory table once
   H235's backup plan is executed.
3. *(open)* A short "first hour on a fresh machine" walkthrough that sequences
   §1→§2→§3 with expected wall-clock times.

## Maintenance rule

Any PR that adds/renames a `scripts/build_*.py` stage or changes a deploy path
must update the runbook §2/§4/§8 in the same pass, and tick a row here.

## Related documents

[CLAUDE.md](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md) (agent-facing
conventions; links here) ·
[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md) ·
[PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md) ·
[CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md)

## Revision history

| Date | Change | By |
|---|---|---|
| 10-07-2026 | Initial version (PR #39) + this metadoc & README link (follow-up PR) | Fable 5 (`claude-fable-5`), H501 |

_Dr. Mārcis Gasūns_
