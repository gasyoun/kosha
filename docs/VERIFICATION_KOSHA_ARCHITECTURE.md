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
- Salt `/api/v1` plus `/dicts/*` parity;
- API/static/SSR payload parity;
- sanitizer adversarial fixtures;
- manifest/truth and surface-registry checks;
- citation archive and public-base resolution.

Every required command must exit zero. Warnings are accepted only when the
handoff explicitly classifies them as known noncritical residue.

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
- API, Salt facade, static cards, and SSR share one serializer and pass parity;
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
