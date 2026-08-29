# Future OxAlpha status-gate design for kosha (inactive)

_Created: 26-08-2026 · Last updated: 26-08-2026_

Design only. **Nothing in this document is enabled**: no workflow file is
added, no required status check is registered, no protection rule is touched.
Proof of non-enablement is §7. Plan of record:
[PLAN_KOSHA_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.md)
(decision 12: designed but not enabled; decision 13: human approval covers
money/security/production paths).

## 1. Purpose

A future gate under which every PR that touches executable code receives an
**independent** OxAlpha review pass as a status check, with human approval
reserved for sensitive paths. Retrospective evidence for the design's
feasibility: [CODE_REVIEW_KOSHA_OXALPHA_30D_2026-08-26.md](https://github.com/gasyoun/kosha/blob/main/docs/CODE_REVIEW_KOSHA_OXALPHA_30D_2026-08-26.md)
(ten slices, two-axis passes, 0 P0/P1).

## 2. Executable-code matching

The gate fires only when the PR diff (merge-base…head, `git diff --name-only`)
matches:

```text
include:
  app/**  src/**  scripts/**  tests/**  ui/src/**  .githooks/**
  .github/workflows/**  data/manifest/surfaces.json
exclude (generated / data-bulk / vendor):
  docs/js/data/**  docs/cards/**  docs/w/**  docs/browse/**  w/**
  data/eval/**  data/akshara_pilot/**  data/raw*/  data/releases/
  **/*.sqlite  **/*.db  **/*.jsonl  **/*.tsv
```

Pure docs/manifest churn skips the review check (matching the H3549 exclusion
classes). `data/manifest/datasets.json` changes skip the review check but
**always** trigger the human-approval lane (§4) — rights tiers live there.

## 3. The independent required status check (designed)

A single workflow `oxalpha-review.yml` (not committed) would:

1. Run on `pull_request` with `permissions: {checks: write, pull-requests: read}`.
2. Compute the §2 match; no match → conclude `neutral` ("no executable code
   changed") and exit — an explicit neutral, never a silent pass.
3. Match → dispatch an OxAlpha reviewer session on the diff slice with two
   prompts kept separate (H3549 axis discipline): a Standards pass
   (CLAUDE.md/AGENTS.md rules + named smells) and a Spec pass (PR body →
   issue → linked plan → `no spec available`).
4. Conclude exactly one of:
   - `pass` — both verdicts PASS, findings ledger empty or P2+ only;
   - `fail` — any proven P0/P1, **with** severity, file/line, failure mode,
     and a failing repro, posted as a PR comment;
   - `neutral` — no executable diff, or infrastructure failure (retry ≤3 then
     neutral, so CI outages never masquerade as review failures).
5. Report via the Checks API (`createCheckRun`, conclusion + evidence summary
   in the output text).

The check is designed to become a **required** status check on `main`
(branch protection, "Require status checks to pass") only after §6 rollout.

## 4. Human approval on sensitive paths

Environment-gated required reviewer (`required_reviewers: 1`) on an environment
named `sensitive-paths`, applied when the diff touches any of:

| Path pattern | Why human |
|---|---|
| `KOSHA_DEPLOYMENT.md`, `scripts/assemble_deploy_bundle.py`, `scripts/rehearse_deploy.py`, `src/kosha/deploy/**` | production/deploy contour (A3: MG deploys) |
| `.env*`, `**/ftp*`, `scripts/akshara_pilot_crawl.py` | secrets / external-fetch posture |
| `data/manifest/datasets.json`, `data/manifest/surfaces.json` (rights-tier fields) | rights/restricted tiers |
| `app/history_db.py`, `src/kosha/api/observability.py` | visitor-data adjacency |

Money paths do not yet exist in kosha (no payments code); the lane is defined
so a future payment webhook automatically lands in it via the deploy/secret
patterns above plus an added `payments/**` row at that time.

## 5. Failure policy

- `fail` blocks merge only while the check is required; the finding must carry
  repro evidence or the check itself is defective (revert the gate, not the
  repo).
- The repair lane follows plan decision 10/11: one minimal PR per proven
  P0/P1, regression test fails-before/passes-after, merged only green, max
  four repair attempts per finding before a stop-condition report.
- Stop conditions (per-fix): secrets/PII exposure, production-state mutation,
  irreversible migration, unclear money behavior, bulk generated/vendor/data
  churn — the affected fix stops, all other slices continue.

## 6. Rollout, observability, rollback

Rollout ladder (each rung ≥ 2 weeks or ≥ 10 PRs of evidence):

1. **Dry-lab**: workflow runs on `pull_request` as non-required; verdicts
   logged only; retrospective replay over the ten H3549 slices must reproduce
   the §5 ledger (0 false P0/P1).
2. **Shadow-required**: required on agent-authored branches only.
3. **Required**: flipped on `main` after false-positive ratio < 10 % over the
   shadow window.

Observability: check duration, verdict distribution, false-positive count
appended monthly to this file's Revision history. Alert on `neutral`
(infrastructure) rate > 20 %.

Rollback: remove the required-check entry (branch protection) and delete
`oxalpha-review.yml`; both reversible in one PR. No data migration is
involved, so rollback is always available.

## 7. Proof that no live gate exists (as of 26-08-2026)

- No `oxalpha-review.yml` (or any new workflow) is added by the carrying PR —
  `.github/workflows/` diff is empty; the four existing workflows are
  `python-ci.yml`, `ui-ci.yml`, `changelog-lint.yml`, `dependabot-auto-merge.yml`.
- No branch-protection mutation was performed; `main`'s required-check set is
  unchanged (`Fixture build + tests`, `vitest + vite build`,
  `Changelog — no duplicated entries`).
- This file is documentation-only; `git diff --check` clean, full test suite
  unaffected (598 passed / 177 skipped in the carrying PR's session).

## Revision history

| Date | Change |
|---|---|
| 26-08-2026 | Initial design (H3549 Wave 3) — inactive by contract |

---

_Dr. Mārcis Gasūns_
