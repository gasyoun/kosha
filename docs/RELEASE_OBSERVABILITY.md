# kosha — release observability (W2C)

_Created: 13-08-2026 · Last updated: 13-08-2026_

What to watch after a deploy, how to confirm `data_version` and archive
health, and which signals are **not** a visitor-analytics product.

Agents never deploy production. This page is for the human operator
(M.G.) and for the local rehearsal path in
[KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md).
Implementation: [src/kosha/api/observability.py](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/observability.py).
Readiness checks (the ones exported here) are still owned by
[src/kosha/api/readiness.py](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/readiness.py)
(H2343 / W1C).

## Correlation

Every HTTP response carries `X-Request-ID`.

- Client may send `X-Request-ID` or `X-Correlation-ID`.
- Accepted tokens: `A–Z a–z 0–9 . _ : -`, length 8–128.
- Anything else is replaced with a UUID4. The replacement is what the
  response header and the log line both show.
- Structured log field: `request_id=` on the `kosha.api` logger, next to
  `method=`, `route=` (FastAPI **template**, e.g. `/api/v1/lemma/{key}`),
  `status=`, `duration_ms=`. The raw path and the query string are not
  logged.

Confirm after deploy:

```sh
curl -sS -D - -o /dev/null https://HOST/health
# look for: X-Request-ID: <uuid>

curl -sS -D - -o /dev/null -H "X-Request-ID: deploy-smoke-01" https://HOST/ready
# look for: X-Request-ID: deploy-smoke-01
```

Then grep the process log for `request_id=deploy-smoke-01`.

## Endpoints

| Path | Role | Green |
|---|---|---|
| `GET /health` | liveness only — process is up | 200 `{"status":"ok"}` even if the DB is gone |
| `GET /ready` | H2343 readiness (core, version, archives, optional writables) | 200 + `"ready": true`. 503 when a **required** check fails. Never 500 for history disabled. |
| `GET /metrics` | Prometheus text, low-cardinality only | 200, `text/plain`, contains `kosha_ready 1` |

History / auth / stats routers stay unmounted (`KOSHA_HISTORY_ENABLED=false`).
`GET /api/v1/history` is a real 404.

## Metric names (locked)

Low-cardinality labels only. Headword, query, raw path, request id, IP,
and dataset id are **forbidden** as labels.

| Name | Type | Labels | Meaning |
|---|---|---|---|
| `kosha_http_requests_total` | counter | `method`, `route`, `status_class` | Request count. `route` is the template (`/api/v1/lemma/{key}`), `status_class` is `2xx` / `4xx` / `5xx`. |
| `kosha_http_request_duration_seconds` | histogram | `method`, `route` | Duration in seconds. Coarse buckets 5 ms … 10 s. |
| `kosha_ready` | gauge | (none) | `1` if `/ready` would succeed right now, else `0`. |
| `kosha_ready_check` | gauge | `name`, `status` | One series per H2343 check × status (`ok` / `fail` / `disabled` / `absent` / `unconfigured`). Current state is `1`. |
| `kosha_ready_failures_total` | counter | `check` | Increments only on `GET /ready` when that required check failed. Scraping `/metrics` does **not** increment it. |
| `kosha_data_version_info` | gauge | `version` | Info gauge: `1` for the store's `meta.data_version`. |

H2343 `name` values: `core_db`, `inflections_db`, `layers_db`,
`data_version`, `data_version_match` (only when
`KOSHA_EXPECTED_DATA_VERSION` is set), `citation_archives`, `history`.

## What to watch on deploy

1. **Process is up.** `GET /health` → 200.
2. **Instance is fit to serve.** `GET /ready` → 200, `"ready": true`.
   If 503, read `checks[]` (or `kosha_ready_check`) — do not restart
   blindly.
3. **Pinned data version.** Set `KOSHA_EXPECTED_DATA_VERSION` to the
   staged `meta.data_version` before promote. A wrong DB then fails
   `/ready` closed (`data_version_match=fail`). Confirm:
   `kosha_data_version_info{version="<expected>"} 1`.
4. **Citation archives.** If `KOSHA_ARCHIVE_DIR` is mounted, look for
   `citation_archives` `ok`. Empty mount is `unconfigured` (not a hard
   fail). A corrupt mounted release is `fail` and `/ready` is 503.
5. **History stays off.** `history` status must be `disabled`. If it
   is `ok` or `fail`, the D10 flag leaked on.
6. **Error rate.** `kosha_http_requests_total{status_class="5xx"}` stays
   near zero. A burst of `4xx` on `{key}` templates after a DB swap can
   mean the fixture/prod mix-up, not a code defect.
7. **Latency.** `kosha_http_request_duration_seconds` for
   `/api/v1/lemma/{key}` and `/api/v1/search` — watch `_bucket{le="0.25"}`
   covering almost all observations.
8. **Trace one request.** Send a chosen `X-Request-ID`, hit `/ready` then
   one lemma, confirm the same id in the response header and in the log.

Local rehearsal (`python scripts/rehearse_deploy.py`) now probes
`/health`, `/ready`, a lemma smoke, and `/metrics` (`kosha_ready`).

## Confirm data_version

```sh
curl -sS https://HOST/ready | python -c "import sys,json; print(json.load(sys.stdin)['data_version'])"
curl -sS https://HOST/metrics | findstr kosha_data_version_info
```

The JSON field and the info-gauge label must match each other and the
staged pin. Sense citations resolve against this version, not the repo
tag (see [CHANGELOG.md](https://github.com/gasyoun/kosha/blob/main/CHANGELOG.md)
header).

## Confirm archive health

```sh
curl -sS https://HOST/ready
# checks[] name=citation_archives → ok | unconfigured | fail

curl -sS https://HOST/metrics | findstr citation_archives
```

Historical sense resolve (`GET /api/v1/sense/...?v=<prior>`) is the
functional check; readiness is the cheap gate. W2A archives are
documented in
[docs/DOI_CHECKLIST_W2A.md](https://github.com/gasyoun/kosha/blob/main/docs/DOI_CHECKLIST_W2A.md).

## What this is not

- Not visitor tracking, not search analytics, not an auth product.
- `request_id` is never a metric label (high cardinality).
- No prod deploy by an agent. Live-smoke sign-off stays in
  [docs/MG_LIVE_SMOKE_PACKET_W1E.md](https://github.com/gasyoun/kosha/blob/main/docs/MG_LIVE_SMOKE_PACKET_W1E.md).

---

_Dr. Mārcis Gasūns_
