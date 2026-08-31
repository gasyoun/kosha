# kosha OxAlpha code-review roadmap

_Created: 26-08-2026 · Last updated: 31-08-2026_

**Truth-pass verdict (31-08-2026, H3786):** finished — H3549 done 28-08-2026
(OxAlpha `opencode/z-ai/glm-5.3-flash`): Wave 0 adapter [PR #463](https://github.com/gasyoun/kosha/pull/463) merged;
Wave 1 evidence report (0 proven P0/P1, 1×P2 + 5×P3 ledgered) and Wave 3 inactive status-gate
design [PR #465](https://github.com/gasyoun/kosha/pull/465) merged. Wave 2 had nothing proven to repair. No open work on this file.

Owner: H3549 (OxAlpha) — kosha 30-day risk-ranked code review and future independent review gate; intended executor OxAlpha (x-preview-f-free).

## Wave 0

Install canonical GitHub adapter and labels in a setup-only green PR.

## Wave 1

Rank fixed-window PRs, retain at most ten executable-risk slices, run independent Standards and Spec passes, and publish an evidence ledger without merging axes.

## Wave 2

Reproduce candidates and merge only minimal regression-tested P0/P1 repairs.

## Wave 3

Design executable-path OxAlpha status review, extra human approval for sensitive paths, failure policy, rollout, observability, and rollback. Do not activate it.

## Non-goals

No P2/P3 fixes, deployment, generated-data rewrite, workflow activation, or protection mutation.

_Dr. Mārcis Gasūns_
