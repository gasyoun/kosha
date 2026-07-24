# Verification — kosha next programme

_Created: 24-07-2026 · Last updated: 24-07-2026_

Index: [PLAN_KOSHA_NEXT_PROGRAMME_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_NEXT_PROGRAMME_2026H2.md).

## Wave-1 acceptance

| ID | Criterion | How to prove |
|---|---|---|
| 1a-1 | H1265: README dataset count matches `datasets.json` via markers + test | `pytest` invariant green; count == JSON public+restricted+intermediate |
| 1a-2 | H1267: DEAD_ENDS record for relaxed tier exists; sheet cancelled language present | File in epistemic registry; no live instruction to vote 2,171 items |
| 1b-1 | H1461: ≥1000 drill items load; tests green; nav link live | Open drills page; `pytest tests/test_zaliznyak_drills.py` |
| 1b-2 | H1492: corpus_sandhi includes Śāstra tier; manifest counts updated | TSV/build report event counts rise; per-text tables exist |
| 1b-3 | H1493 (if run): prose toggle on Gītā reader | `gita_prose.tsv` + UI toggle |
| 1c-1 | Panini page shows four coverage statuses distinctly | Visual + test for status strings |
| 1c-2 | Chain view resolves ≥1 exemplar chain for a top lit sūtra (e.g. 1.4.13) | Manual click or automated HTML fixture |
| 1c-3 | Trust block has source, n, date | HTML contains report links |
| 1d-1 | Budget log has **new dated row** with A4 + head projection | Diff of log file / architecture §6 |

## Wave-2 acceptance

| ID | Criterion |
|---|---|
| 2-1 | Pilot TSV row count == pilot headword count (± documented drops) |
| 2-2 | Viewer renders PWG + MW columns for pilot; Apte nulls honest |
| 2-3 | No MW/kosha `senses` bytes changed |
| 2-4 | publish-safety GO or tier=intermediate |

## Wave-3 acceptance

| ID | Criterion |
|---|---|
| 3-1 | SCL cache path gitignored; `git check-ignore` true; no SCL body in tree |
| 3-2 | Held-out WordSem accuracy ≥70% for the fused (or LLM-only degraded) arm |
| 3-3 | `sense_frequency.tsv` gains `provenance=estimated` rows only where gate passes |
| 3-4 | Cards show estimated tier without blending into attested |
| 3-5 | Disagreement queue TSV non-empty or explicitly empty-with-reason |

## Wave-4 acceptance

| ID | Criterion |
|---|---|
| 4-1 | New tables queryable; smoke lemmas return non-null joins where expected |
| 4-2 | Restricted data not exposed on public API routes |
| 4-3 | Tests green; runbook updated |

## Wave-5 acceptance

| ID | Criterion |
|---|---|
| 5-1 | Static head N=11,148 build completes; size logged |
| 5-2 | SSR parity test green (DB-gated may skip in CI — document) |
| 5-3 | Exit packet written; live checks marked pass/blocked honestly |
| 5-4 | Host-independent links (no hard-coded deploy host in citations) |

## Risks register

| ID | Risk | Mitigation |
|---|---|---|
| R-N1 | SCL scrape blocked / Anubis | Fail closed to LLM-only; log degradation (autonomy contract) |
| R-N2 | SCL labels leak into git | gitignore + publish-safety + CI check for cache path |
| R-N3 | WSD invents senses / reorders MW | Sidecar only; never write MW senses |
| R-N4 | Pages budget overrun | D4 head bound; W1d measurement before W5 |
| R-N5 | Deploy assumption wrong | W5 still ships static head + honest blocked live checks |
| R-N6 | Pilot cross-dict over-claims full recon | UI + docs say **pilot 500 only** |
| R-N7 | `kosha.db` toward 2 GB ceiling | W4 prefers summary tables; large assets stay separate release files (R-Q1 discipline) |
| R-N8 | Dual-run collision on residual handoffs | Claim + session-unique worktree names |

## Stop conditions (summary)

Halt the wave if rights-red cannot clear or acceptance metric unachievable after genuine attempt. Everything else: default + log + continue.

---

_Dr. Mārcis Gasūns_
