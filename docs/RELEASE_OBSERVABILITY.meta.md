# Metadoc — RELEASE_OBSERVABILITY.md

_Created: 13-08-2026 · Last updated: 13-08-2026_

## Purpose

Operator notes for W2C release observability: correlation header, locked
low-cardinality metric names, readiness-failure export, and the post-deploy
watch list. Companion to the H2343 `/ready` checks, not a second readiness
implementation.

## Audience

- M.G. at promote / rollback time
- Agents extending rehearsal or adding a metric (must stay low-cardinality)

## Provenance

- Handoff: H2348 (Grok 4.6 `grok-4.6`)
- Depends: H2343 W1C readiness, H2347 W2B catalog API
- Code: `src/kosha/api/observability.py`, `GET /metrics`, middleware on `app/main.py`

## Ranked improvement backlog

1. If a scrape network is isolated, document the nginx allowlist for `/metrics`.
2. Add a one-line `journalctl` example once the production unit name is frozen.
3. Optionally export `kosha_ready` to a host-local node-exporter textfile if
   Prometheus is not scraping the app directly.

## Limitations

- Process-local registry (one uvicorn worker). Multi-worker deploy sums
  counters at the scraper, not in-process.
- Does not deploy or hold secrets.
- Does not enable history/auth/analytics.

## Related docs

- [docs/RELEASE_OBSERVABILITY.md](https://github.com/gasyoun/kosha/blob/main/docs/RELEASE_OBSERVABILITY.md)
- [KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md)
- [src/kosha/api/readiness.py](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/readiness.py)
- [docs/ROADMAP_KOSHA_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026_2027.md)

## Revision history

| Date | Change |
|---|---|
| 13-08-2026 | Initial metadoc with H2348 W2C notes |

---

_Dr. Mārcis Gasūns_
