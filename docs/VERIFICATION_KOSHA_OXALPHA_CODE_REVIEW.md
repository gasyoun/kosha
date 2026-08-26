# kosha OxAlpha code-review verification and risks

_Created: 26-08-2026 · Last updated: 26-08-2026_

| Deliverable | Proof | Failure |
|---|---|---|
| Adapter | Three docs, one Agent skills block, five labels, intake OFF | Missing/duplicate config |
| Selection | Zero to ten fixed-window rows with risk evidence | Churn substituted for risk |
| Standards | Rule or named smell plus exact hunk | Generic advice |
| Spec | Quoted requirement or no spec available | Inference as fact |
| Finding | Severity, location, failure mode, repro/test | No reproducible evidence |
| Fix | Regression fails before and passes after; CI green | Untested/fenced mutation |
| Design | Rollout and rollback; no activation | Workflow/protection enabled |

Verification: run surface validation, fixture build twice, pytest without cache, requirements audit, and UI tests/build; run git diff --check; verify full links.

Risks: restricted rights; Heritage digest refusal; atomic DB promotion; build order; citation durability; archive immutability; zero-byte deploy assets. Exclude generated/data mega-PRs and never publish restricted bytes or mutate generated surfaces.

Autonomy gate: PASS when every wave-1 deliverable has architecture, ordered steps, command-level acceptance, and named risks; no blocking decision remains.

_Dr. Mārcis Gasūns_
