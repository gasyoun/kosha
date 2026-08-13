# kosha — deployment runbook

_Created: 08-08-2026 · Last updated: 13-08-2026_

Branded dictionary routes on
[`https://samskrtam.ru`](https://samskrtam.ru/) (`/health` `/ready`
`/metrics` `/api/` `/dicts/` `/w/`) are reverse-proxied to the `.92`
unit — see
[`deploy/samskrtam-brand-proxy/`](https://github.com/gasyoun/kosha/blob/main/deploy/samskrtam-brand-proxy/README.md).
WordPress on the same host is untouched.

The human-facing deploy procedure for the **public API surface** on a host
M.G. controls (samskrtam.ru) and for **local rehearsal** every agent can run.
Companion machine recipe:
[`data/manifest/deploy_bundle.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/deploy_bundle.json).
Pipeline rebuild steps (DB stages, static generators) stay in
[`docs/PIPELINE_OPERATOR_RUNBOOK.md`](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.md)
— this file is deploy + rollback only.

**Hard fence (A3 / roadmap W1 non-goal):** agents never receive production
credentials, never SSH to production, never run `deploy_guhya.py --upload`, and
never claim W1 live-smoke done. Production steps below are for **M.G. only**.

---

## Part 0 — What a "bundle" is

A versioned **deployment bundle** is a directory containing:

| File | Role |
|---|---|
| `payload/` | Repo-relative copy of code + data paths named in the recipe |
| `BUNDLE_MANIFEST.json` | Recipe snapshot + per-file sha256 digests + runtime/env metadata |
| `BUNDLE_IDENTITY.json` | Compact identity used as "previous bundle" for rollback |

Assemble (local, any workstation):

```sh
python scripts/assemble_deploy_bundle.py --profile fixture   # agent / CI
python scripts/assemble_deploy_bundle.py --profile staged    # human with staged DBs
python scripts/assemble_deploy_bundle.py --validate-only     # recipe structure only
```

Default output: `data/deploy_bundles/<bundle_id>-<UTC stamp>/` (gitignored).

**Profiles**

| Profile | Core DB path | Who |
|---|---|---|
| `fixture` | rewrites `data/db/kosha.db` → `data/db/kosha_fixture.db` | agents, CI, local rehearsal |
| `staged` | recipe paths as written (local non-prod stage only) | human preparing a real DB offline |

---

## Part I — Local build prerequisites

1. Python ≥ 3.12, repo checkout, `pip install -r requirements.txt`.
2. For **fixture** rehearsal: either an existing
   `data/db/kosha_fixture.db` or:

   ```sh
   python scripts/build_db.py --profile fixture
   ```

3. Env for local serve (never commit secrets):

   ```sh
   Copy-Item .env.example .env   # PowerShell
   # set KOSHA_CORE_DB_PATH=./data/db/kosha_fixture.db for rehearsal
   ```

4. Validate the recipe and surface registry:

   ```sh
   python scripts/assemble_deploy_bundle.py --validate-only
   python scripts/validate_surfaces.py
   ```

---

## Part II — Local deployment rehearsal (agents + humans)

One command:

```sh
python scripts/rehearse_deploy.py
```

What it does:

1. Ensures fixture DB exists (builds if missing).
2. Assembles a fixture-profile bundle with digests.
3. Spawns `uvicorn app.main:app` on `127.0.0.1` (ephemeral port) with
   `KOSHA_CORE_DB_PATH` pointing at the fixture and history disabled.
4. Probes `GET /health` → 200, `GET /ready` → 200/`ready:true`, a lemma
   smoke (`/api/v1/lemma/banD` may be 200 or clean 404 on a tiny fixture),
   and `GET /metrics` → 200 containing `kosha_ready`.
5. Terminates the process. Writes
   `data/deploy_bundles/last_rehearsal.json` (gitignored).

**Pass criterion:** process exit code 0. Committed evidence of a green run is
recorded in
[`docs/DEPLOY_REHEARSAL_LOG.md`](https://github.com/gasyoun/kosha/blob/main/docs/DEPLOY_REHEARSAL_LOG.md).

Manual equivalent (if debugging):

```sh
$env:KOSHA_CORE_DB_PATH = (Resolve-Path .\data\db\kosha_fixture.db).Path
$env:KOSHA_HISTORY_ENABLED = "false"
uvicorn app.main:app --host 127.0.0.1 --port 8000
# other terminal:
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/ready
curl -fsS http://127.0.0.1:8000/metrics
```

Post-deploy watch list (correlation header, metric names, `data_version`,
archive health):
[`docs/RELEASE_OBSERVABILITY.md`](https://github.com/gasyoun/kosha/blob/main/docs/RELEASE_OBSERVABILITY.md).

---

## Part III — Production deploy (M.G. only)

Agents stop at Part II. The checklist below is the restored reference that
ARCHITECTURE.md / README point at (`Type=exec` systemd + nginx `proxy_pass`).

### III.1 Prepare artifacts offline

1. On a trusted workstation, build or copy the production `kosha.db` (and
   optional attached stores) into a **staged** tree — not over SSH from an agent.
2. Assemble:

   ```sh
   python scripts/assemble_deploy_bundle.py --profile staged --out ./kosha-bundle-prod
   ```

3. Record `BUNDLE_IDENTITY.json` from the **currently live** tree before
   replacing anything (this becomes `previous_bundle_identity` for rollback).
4. Copy the new bundle payload + identity to the host by M.G.'s preferred
   channel (scp, panel, etc.). **No agent holds those credentials.**

### III.2 Environment on the host

Create a host-local `.env` (never committed) from `.env.example`:

| Key | Production expectation |
|---|---|
| `KOSHA_CORE_DB_PATH` | Absolute path to the staged core DB |
| `KOSHA_INFLECTIONS_DB_PATH` / `KOSHA_LAYERS_DB_PATH` | Set only when split files exist |
| `KOSHA_ARCHIVE_DIR` | Mount of published `data-v*` archives when citation resolve is required |
| `KOSHA_PUBLIC_BASE` | Durable public API base used in citations (**not** forced to samskrtam.ru if citations must stay host-independent — prefer the durable mirror policy in RISKS R5) |
| `CORS_ORIGINS` | Explicit JSON list, e.g. `["https://samskrtam.ru","https://gasyoun.github.io"]` — never `["*"]` with credentials |
| `KOSHA_HISTORY_ENABLED` | `false` for public v1 |
| `KOSHA_EXPECTED_DATA_VERSION` | Pin to the staged `meta.data_version` so `/ready` fails closed on a wrong DB |
| `HISTORY_IP_SALT` | Only if history is ever enabled — random secret, host-local |

### III.3 systemd unit sketch (`Type=exec`)

Example unit name `kosha.service` (paths illustrative — adjust to the host):

```ini
[Unit]
Description=kosha Sanskrit dictionary API
After=network.target

[Service]
Type=exec
User=kosha
WorkingDirectory=/srv/kosha/current
EnvironmentFile=/srv/kosha/current/.env
ExecStart=/srv/kosha/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now kosha
sudo systemctl status kosha
```

### III.4 nginx sketch (explicit `proxy_pass`)

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /dicts/ {
    proxy_pass http://127.0.0.1:8000/dicts/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

location /w/ {
    proxy_pass http://127.0.0.1:8000/w/;
    proxy_set_header Host $host;
}

location = /health {
    proxy_pass http://127.0.0.1:8000/health;
}

location = /ready {
    proxy_pass http://127.0.0.1:8000/ready;
}

location = /metrics {
    proxy_pass http://127.0.0.1:8000/metrics;
}
```

Reload nginx after editing. Prefer separate `location` blocks over a catch-all
so static Pages assets and the API do not silently collide.

### III.5 Post-deploy smoke (production host, M.G.)

```sh
curl -fsS https://samskrtam.ru/health
curl -fsS https://samskrtam.ru/ready
curl -fsS https://samskrtam.ru/metrics | findstr kosha_ready
curl -sS -D - -o /dev/null -H "X-Request-ID: deploy-smoke-01" https://samskrtam.ru/ready
curl -fsS 'https://samskrtam.ru/api/v1/lemma/banD' | head -c 200
```

Full live-smoke (Lighthouse mobile ≥90, Gītā walkthrough, citation resolve,
rollback confirmation) is the **H2345** packet:
[`docs/MG_LIVE_SMOKE_PACKET_W1E.md`](https://github.com/gasyoun/kosha/blob/main/docs/MG_LIVE_SMOKE_PACKET_W1E.md)
— not this handoff.

### III.6 Static / Pages tier

Committed surfaces go live on merge to `main` (GitHub Pages). Gitignored
static cache (`docs/cards/`, `docs/js/data/`, `docs/w/`) is still deployed
**out-of-band by M.G.** via existing generators — see pipeline runbook §4.
That path is independent of the API systemd unit.

---

## Part IV — Rollback packet

### Identity

- **Current:** `BUNDLE_IDENTITY.json` written at the last successful assemble
  that was promoted to the host.
- **Previous:** the identity file retained from the prior promotion (store under
  e.g. `/srv/kosha/releases/<stamp>/BUNDLE_IDENTITY.json`).

### Restore steps (production, M.G.)

1. `sudo systemctl stop kosha`
2. Point `current` (or the WorkingDirectory) at the previous payload tree
   whose digests match the previous `BUNDLE_IDENTITY.json`.
3. Restore the previous core DB (and attached stores) that those digests name —
   do **not** hot-patch `kosha.db` for dictionary corrections (RISKS / RELATIONS:
   corrections flow through csl-orig).
4. Restore the previous host `.env` path values if they changed.
5. `sudo systemctl start kosha`
6. Verification smoke:

   ```sh
   curl -fsS http://127.0.0.1:8000/health
   curl -fsS http://127.0.0.1:8000/ready
   curl -fsS 'http://127.0.0.1:8000/api/v1/lemma/banD' | head -c 200
   ```

7. If `/ready` is 503, read the JSON `checks[]` — wrong `KOSHA_EXPECTED_DATA_VERSION`
   or a missing core file are the common causes.

### Local rollback drill (agents)

Keep two fixture-profile bundles under `data/deploy_bundles/`. Re-run
`python scripts/rehearse_deploy.py` after switching `KOSHA_CORE_DB_PATH` is
sufficient to prove the API boots on a prior identity; no production contact.

Machine-readable restore list: the `rollback` object inside
`data/manifest/deploy_bundle.json` and every assembled `BUNDLE_MANIFEST.json`.

---

## Part V — Never do

- Commit `.env`, `.env.deploy`, FTP passwords, or host private keys.
- Run production deploy or restricted FTP upload from an agent session.
- Point citation minting at the deployment host as the only resolve path
  (RISKS R5).
- Skip `/ready` after a DB swap.
- Declare W1 complete before
  [`docs/MG_LIVE_SMOKE_PACKET_W1E.md`](https://github.com/gasyoun/kosha/blob/main/docs/MG_LIVE_SMOKE_PACKET_W1E.md)
  result tables are filled and signed by M.G.

---

## Appendix A — Public HTTP surfaces (deploy-relevant)

| Path | Role |
|---|---|
| `GET /health` | Liveness — process up |
| `GET /ready` | Readiness — DB + version + archives + optional writables (W1C) |
| `GET /api/v1/lemma/{key}` | Lemma card (Salt-compatible kosha envelope) |
| `GET /dicts/{id}/…` | Cologne Salt facade faces |
| `GET /w/{slp1}` | SSR word page |

Full API contract:
[`docs/ARCHITECTURE_KOSHA_PLATFORM.md`](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PLATFORM.md).

---

## Related docs

| Doc | Role |
|---|---|
| [`data/manifest/deploy_bundle.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/deploy_bundle.json) | Machine recipe |
| [`docs/DEPLOY_REHEARSAL_LOG.md`](https://github.com/gasyoun/kosha/blob/main/docs/DEPLOY_REHEARSAL_LOG.md) | Last committed local rehearsal evidence |
| [`docs/MG_LIVE_SMOKE_PACKET_W1E.md`](https://github.com/gasyoun/kosha/blob/main/docs/MG_LIVE_SMOKE_PACKET_W1E.md) | H2345 MG live-smoke (Lighthouse / Gītā / citation / rollback) |
| [`docs/PIPELINE_OPERATOR_RUNBOOK.md`](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.md) | Build stages + static generators |
| [`ARCHITECTURE.md`](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md) § A3 | Local-first / MG-deploys rule |

---

_Dr. Mārcis Gasūns_
