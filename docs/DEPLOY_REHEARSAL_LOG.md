# Deploy rehearsal log — W1D local fixture

_Created: 08-08-2026 · Last updated: 08-08-2026_

Committed evidence for **H2344** (Grok 4.5 `grok-4.5`): local deployment
rehearsal against the fixture profile. **Zero production contact.** Machine
transcript (gitignored) lands at `data/deploy_bundles/last_rehearsal.json`
when the script runs.

## Command

```sh
python scripts/assemble_deploy_bundle.py --validate-only
python scripts/rehearse_deploy.py
```

## Expected gates

| Gate | Pass |
|---|---|
| Recipe validates (`--validate-only` exit 0) | structural + closed vocabularies |
| Fixture DB present or built | `data/db/kosha_fixture.db` |
| Bundle assemble | `BUNDLE_IDENTITY.json` written under `data/deploy_bundles/` |
| `GET /health` | HTTP 200 |
| `GET /ready` | HTTP 200 and `"ready": true` |
| Lemma smoke | HTTP 200 or clean 404 envelope |
| Process exit | 0 |

## This session

Filled after the green run in the H2344 worktree (see PR body for exact
timestamp). Re-run anytime with the commands above; overwrite this section's
result row only when the exit code is 0.

| Field | Value |
|---|---|
| Date (UTC) | 2026-08-08T06:47Z |
| Model | Grok 4.5 (`grok-4.5`) |
| Handoff | H2344 |
| Profile | fixture |
| Production host touched | **no** |
| Fixture `data_version` | `0.0.0-fixture` |
| Bundle files hashed | 61 |
| `GET /health` | 200 `{"status":"ok"}` |
| `GET /ready` | 200 `ready:true` (core ok; inflections/layers absent; history disabled) |
| Lemma smoke `/api/v1/lemma/banD` | 404 envelope (fixture has no `banD` — accepted) |
| Assemble exit | 0 |
| Rehearse exit | 0 |
| Next handoff | H2345 (Grok 4.5) — MG live-smoke packet |

## Rollback drill note

Keeping the previous assemble directory under `data/deploy_bundles/` is enough
to name a `previous_bundle_identity`. Full production restore steps live in
[KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md) Part IV.

---

_Dr. Mārcis Gasūns_
