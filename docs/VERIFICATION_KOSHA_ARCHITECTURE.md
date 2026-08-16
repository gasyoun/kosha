# Kosha architecture verification and risks

_Created: 30-07-2026_

This gate applies to the
[W0 implementation](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_ARCHITECTURE_WAVE1.md)
and the later roadmap waves.

## Required PR gate

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q -p no:cacheprovider
Push-Location ui
npm test
npm run build
Pop-Location
```

W0 adds commands for:

- fixture build from an empty target;
- DAG order and missing-prerequisite failures;
- settings aliases/conflicts and history-disabled routes;
- `/api/v1` full-entry and strict `/dicts/*` shared-field parity;
- API/static/SSR payload parity;
- sanitizer adversarial fixtures;
- manifest/truth and surface-registry checks
  (`python scripts/validate_surfaces.py` — W1B / H2342, required CI step);
- citation archive and public-base resolution;
- readiness probes (`GET /ready` — W1C / H2343; `pytest tests/test_readiness.py`).

Every required command must exit zero. Warnings are accepted only when the
handoff explicitly classifies them as known noncritical residue.

## Required checks (branch protection)

W0B (H1944) shipped the two workflows this gate runs in CI. The protected
`main` branch requires both status checks by name.

> **History, 31-07-2026 (H1945).** That sentence was in this file before the
> control behind it existed. H1945 checked it against the API and found
> `branches/main` returning `"protected": false` and `rulesets` returning `[]`
> — `main` had never carried protection, so no check was *required*, both
> workflows were advisory, and a red CI run did not block a merge
> ([#223](https://github.com/gasyoun/kosha/issues/223)). Protection was enabled
> the same day, on human instruction, with the exact configuration recorded
> below. Kept as a note rather than deleted because the gap is the reason every
> "CI enforces X" claim in the W0 documents is now stated with its
> configuration attached.

**Configuration as enabled (31-07-2026).** Readable at any time with
`gh api repos/gasyoun/kosha/branches/main/protection`:

| Setting | Value | Why |
|---|---|---|
| `required_status_checks.contexts` | `Fixture build + tests`, `vitest + vite build` | the two workflows below, by job name |
| `required_status_checks.strict` | `false` | a branch need not be rebased onto the latest `main` to merge; the gate is correctness, not freshness, and `strict` would force a re-run of every open PR on each merge |
| `enforce_admins` | `true` | without it an admin — which is everyone who can merge here — could merge past a red run, i.e. the exact gap #223 recorded. **Consequence: direct pushes to `main` are refused for everyone, including release commits. Cut releases through a PR** (as [#225](https://github.com/gasyoun/kosha/pull/225) did) |
| `required_pull_request_reviews` | `null` | a solo maintainer and an agent workflow cannot supply a second approver; requiring one would block every merge rather than gate it |
| `allow_force_pushes` · `allow_deletions` | `false` | `main` is the branch every citation and release tag is cut from |

`Changelog — no duplicated entries` runs on pull requests and is deliberately
**not** required: it is a hygiene check, and this table lists what the freeze-exit
checklist names. Adding it is one API call if that changes.

The two required workflows, and what each proves:

| Check | Workflow | What it proves |
|---|---|---|
| `Fixture build + tests` | [python-ci.yml](https://github.com/gasyoun/kosha/blob/main/.github/workflows/python-ci.yml) | the declared DAG plans, builds from zero **twice**, and the fixture-tier suite passes |
| `vitest + vite build` | [ui-ci.yml](https://github.com/gasyoun/kosha/blob/main/.github/workflows/ui-ci.yml) | the Svelte UI tests pass and the bundle still builds |

Dependency auto-merge cannot bypass them, and since 31-07-2026 that is true of
both barriers rather than one:
[dependabot-auto-merge.yml](https://github.com/gasyoun/kosha/blob/main/.github/workflows/dependabot-auto-merge.yml)
is triggered by `workflow_run` on those two workflows and refuses to act unless
the run concluded `success`; it then enables GitHub's *queued* auto-merge,
which waits on branch protection — which now exists. Until protection was
enabled the second barrier waited on nothing, and the `workflow_run` condition
was carrying the whole guarantee alone.

The fixture tier is deliberately not the whole suite. Eight test modules are
pinned to full-data counts (323,425 lemmas and similar) and skip themselves
when the core DB is absent — see
[tests/conftest.py](https://github.com/gasyoun/kosha/blob/main/tests/conftest.py).
Running those remains a workstation and full-data-release-gate duty.

## Full-data release gate

1. Resolve only immutable source tags/commits/checksums.
2. Build in an isolated temporary workspace from no pre-existing database.
3. Verify the declared topological stage order.
4. Run `PRAGMA foreign_key_check` and required table/count/provenance checks.
5. Verify attached-layer queries against the monolith compatibility sample.
6. Run size thresholds.
7. Build public JSON, TSV, HTML, and archives twice; require byte identity.
8. Compare SQLite through normalized logical dumps, not raw file hashes.
9. Verify every release citation asset, checksum, public URL, and historical
   sense resolution.

## Freeze-exit checklist

- H1943, H1944, and H1945 merged;
- retrospective Codex review has no open P0/P1;
- fixture clean build succeeds from zero;
- required Python/UI CI is protected and green;
- dependency auto-merge cannot bypass those checks;
- full default DAG contains every declared stage;
- [integrity issue #210](https://github.com/gasyoun/kosha/issues/210) closes
  only after a fresh no-flag build proves every declared stage ran;
- API, Salt facade, static cards, and SSR share one serializer; full kosha
  surfaces pass equality parity and Salt faces pass strict-key/shared-field parity;
- sanitizer adversarial suite passes;
- history/auth/stats endpoints return 404 by default;
- current and historical citation smoke tests pass;
- no known deployment-blocking configuration contradiction remains.

Rights uncertainty is not a freeze-exit criterion.

## Risks and spikes

| Risk | Required treatment |
|---|---|
| API migration breaks unknown clients | Pre-public breaking change; freeze golden old/new fixtures and document the cut |
| SQLite attached-layer resolution changes query plans | Build repository facade first; compare query results and latency before split |
| Raw SQLite is not byte deterministic | Use normalized logical dumps and deterministic public artifacts |
| Sanitizer removes legitimate Cologne display markup | Build allowlist from golden corpus; every removal needs a regression fixture |
| Fixture DB misses full-data behavior | Keep fixture gate fast; full-data gate remains mandatory before release |
| Locking local sibling packages is awkward | Package canonical runtime dependencies; keep explicit local override only for development |
| Registry/status cleanup causes link rot | Banner in place; never mass-move historical documents |
| Plaintext backup replacement cannot verify remote digest | Fail closed for backup execution; do not upload until the selected transport proves digest verification |
| Citation archive assets remain absent | Public v1 stays blocked; generate and verify before deploy |
| Rights record is incomplete or uncertain | Record what is known and proceed; block only confirmed prohibition, explicit restricted tier, privacy, or platform rule |

## Stop and retry policy

Claude Code makes at most three serious repair attempts for a repeated required
gate. It halts the handoff for security/privacy exposure, destructive-data risk,
incompatible Salt/citation contracts, or the third repeated failure. It logs and
skips isolated noncritical failures. Rights uncertainty never halts the work.

---

_Dr. Mārcis Gasūns_
