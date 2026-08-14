# W1E — MG live-smoke packet (public-product readiness exit)

_Created: 08-08-2026 · Last updated: 14-08-2026_

**Branded API (13-08-2026):** [https://samskrtam.ru/health](https://samskrtam.ru/health) and the other kosha paths are live.

**Handoff:** [H2345](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2345-Grok_kosha_architecture-roadmap-w1e-mg-live-smoke-packet_07.08.26.md)
(Grok 4.5 `grok-4.5` — agent half shipped; public-probe fill 08-08-2026;
first live promote 08-08-2026 same day — see §1b).

**Roadmap:** [ROADMAP_KOSHA_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026_2027.md)
W1 exit criteria — MG production deploy, Lighthouse mobile ≥90, Gītā walkthrough,
citation checks, rollback confirmation.

**Depends on:** [H2344](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2344-Grok_kosha_architecture-roadmap-w1d-deploy-bundle-rehearsal_07.08.26.md)
merged ([kosha PR #257](https://github.com/gasyoun/kosha/pull/257), v0.103.0) —
runbook [`KOSHA_DEPLOYMENT.md`](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md),
recipe [`data/manifest/deploy_bundle.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/deploy_bundle.json),
local rehearsal [`docs/DEPLOY_REHEARSAL_LOG.md`](https://github.com/gasyoun/kosha/blob/main/docs/DEPLOY_REHEARSAL_LOG.md).

**Companion (P5 static head, still human-gated):**
[`docs/P5_WORD_PAGE_EXIT_PACKET.md`](https://github.com/gasyoun/kosha/blob/main/docs/P5_WORD_PAGE_EXIT_PACKET.md).

**Fill modes:**

1. Public HTTP + Lighthouse only (Grok 4.5 `grok-4.5`, 2026-08-08T09:44Z) — §1–§8
   morning probe; samskrtam.ru API **404**.
2. **First live promote** (Grok 4.5 `grok-4.5`, 2026-08-08T12:25Z) — API on
   `193.232.229.92` via sslip.io; human asked to promote.
3. **Post-promote residual fill** (Grok 4.5 `grok-4.5`, 2026-08-08T12:34Z) —
   Lighthouse L1–L3 **100**, Gītā 1.1 **13/13** SSR, unit-restart recovery —
   see §8b. Residuals remaining: branded `samskrtam.ru`, Pages `w/` hrefs,
   archive mount, digests-based identity rollback, human §9.
4. **W2C re-fill** (Grok 4.6 `grok-4.6`, 2026-08-13T11:13Z, H2642) —
   `git pull --ff-only` `/opt/kosha/repo` `0cd22ef5` → `ae4f93c4` (v0.110.3),
   unit restart, public probe of W2C (`X-Request-ID` + `GET /metrics`) plus
   the original W1 gates. See §8c.
5. **Citation-archive mount** (Grok 4.6 `grok-4.6`, 2026-08-14T00:30Z, H2671) —
   snapshot of live `0.1.0-dev` under `/opt/kosha/archive/0.1.0-dev/`;
   `/ready` `citation_archives` **ok**; pinned sense 200. See §8e.
6. **Identity rollback drill** (Grok 4.6 `grok-4.6`, 2026-08-14T00:27Z, H2672) —
   first `BUNDLE_IDENTITY` pair on `.92`, Part IV restore of previous, then
   immediate re-promote of current. Unit left on current. See **8f**.

---

## 0. Agent non-execution fence (hard)

| Rule | Morning probe 09:44Z | Promote pass 12:25Z |
|---|---|---|
| Production credentials invent / leak | **held** | **held** |
| SSH / host panel | not used | used on known key host `root@193.232.229.92` only (same box as Systema/Samudra) |
| systemd / nginx / DB promote | not done | **done** on `.92` (`kosha.service`, port **8001**, nginx + certbot) |
| Agent does not declare W1 complete | **held** | **held** — live-base gates PASS; branded/Pages/archive/§9 residual |

W1 is complete only when all required rows PASS (or explicit WAIVE with reason a human
accepts) **and** §9 is signed by M.G.

Agents may re-run the **local** rehearsal from H2344; that does not substitute for live smoke.

---

## 1. Public URLs (from H2344 runbook — do not invent hosts)

Use the host that is actually serving the **promoted** bundle. Defaults from
[`KOSHA_DEPLOYMENT.md`](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md)
Part III:

| Surface | Default public URL | Role | Probe 08-08-2026 |
|---|---|---|---|
| API liveness | `https://samskrtam.ru/health` | process up | **404** |
| API readiness | `https://samskrtam.ru/ready` | DB + version + archives | **404** |
| Lemma card | `https://samskrtam.ru/api/v1/lemma/banD` | Salt-compatible envelope | **404** |
| Sense / citation live | `https://samskrtam.ru/api/v1/sense/{dict}.{L}.{n}` | live resolve | not probed (API absent) |
| Sense / citation pinned | `https://samskrtam.ru/api/v1/sense/{dict}.{L}.{n}@{data_version}` | archive path | not probed (API absent) |
| SSR word page | `https://samskrtam.ru/w/{slp1}` | long-tail / head SSR | **404** (`/w/BU`, sample lemmas) |
| Path-prefix try | `https://samskrtam.ru/kosha/health` | alternate mount | **404** (also `/kosha/`, `/api/health`) |
| Site root | `https://samskrtam.ru/` | marketing WP | **200** HTML (not kosha API) |
| Pages static root | `https://gasyoun.github.io/kosha/` | committed static tier | **200** → redirect to `./docs-site/` |
| Pages reading packs | `https://gasyoun.github.io/kosha/reading/` | Gītā packs | **200** |
| Pages word head (pack href target) | `https://gasyoun.github.io/kosha/w/{token}.html` | static head | **404** (not deployed) |
| Pages cards at pack-relative path | `https://gasyoun.github.io/kosha/docs/cards/{token}.json` | static cards under `docs/` | **200** for several head lemmas |

**Path rewrite (morning):** none on `samskrtam.ru` — WP 200, kosha routes 404.

**Citation durability (RISKS R5):** `KOSHA_PUBLIC_BASE` used in minting must remain a
**durable** citation base (typically the GitHub Pages / release-asset policy), not a
single deployment host that can vanish. Live resolve on the API host is a smoke check;
release-asset openability is the product gate.

---

## 1b. First live promote — 2026-08-08T12:25Z (sslip.io on .92)

Human instruction this session: **promote**. DNS facts:

| Name | IP | Agent SSH |
|---|---|---|
| `samskrte.ru` (Systema) | `193.232.229.92` | yes (`root`, key already trusted) |
| `samskrtam.ru` (WP / packet default) | `193.232.229.95` | **no** (publickey denied) |

Promote therefore landed on **`.92`** with a Samudra-style public URL (not branded
`samskrtam.ru` until DNS/proxy on `.95` is wired).

| Item | Value |
|---|---|
| Host | `samskrtam150` / `193.232.229.92` |
| Code | `/opt/kosha/repo` @ `2728b2bf` (`origin/main`) |
| Venv | `/opt/kosha/venv` |
| Core DB | `/opt/kosha/db/kosha.db` (1.7 GB, integrity ok; **323 425** lemmas / **692 403** senses; `data_version=0.1.0-dev`) |
| Env | `/opt/kosha/.env` — `KOSHA_EXPECTED_DATA_VERSION=0.1.0-dev`, `KOSHA_PUBLIC_BASE=https://gasyoun.github.io/kosha`, history off |
| Unit | `kosha.service` → uvicorn `127.0.0.1:8001` (samudra keeps `:8000`) |
| nginx + TLS | `/etc/nginx/sites-enabled/kosha` + Let's Encrypt `kosha.193.232.229.92.sslip.io` |
| Ops note | `/opt/kosha/OPS.md` |
| Public base (API) | **https://kosha.193.232.229.92.sslip.io/** |

### Promote smoke (external client, 12:25Z)

| Check | Result |
|---|---|
| `GET /health` | **200** `{"status":"ok"}` |
| `GET /ready` | **200** `ready:true`, `data_version=0.1.0-dev`, core + version match ok; archives **unconfigured**; history **disabled** |
| `GET /api/v1/lemma/banD` | **200** Salt envelope, MW/PWG/AP90 results |
| `GET /api/v1/sense/mw.101.1` | **200** `resolved_from: live`, `sense_id` …`@0.1.0-dev` |
| `GET /w/BU` (SSR) | **200** |
| `samskrtam.ru` same paths | still **404** (different host `.95`) |
| Pages `…/kosha/w/{token}.html` | still **404** (static head not on Pages) |

Hairpin note: curling the public hostname *from the host itself* may time out; probe from outside or `http://127.0.0.1:8001`.

---

## 2. Pre-flight (production deploy)

Follow [`KOSHA_DEPLOYMENT.md`](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md)
Part III in full. Checklist condensed:

1. Offline assemble staged bundle:
   `python scripts/assemble_deploy_bundle.py --profile staged --out ./kosha-bundle-prod`
2. Record **current live** `BUNDLE_IDENTITY.json` → becomes `previous_bundle_identity`.
3. Host `.env` from `.env.example` — pin `KOSHA_EXPECTED_DATA_VERSION`, set
   `KOSHA_ARCHIVE_DIR` if citation archives are mounted, never `CORS_ORIGINS=["*"]`
   with credentials.
4. systemd `Type=exec` + nginx explicit `proxy_pass` blocks (`/api/`, `/dicts/`, `/w/`,
   `/health`, `/ready`).
5. Static regenerable tier (cards + `docs/w/` + `docs/browse/`) per pipeline runbook /
   P5 packet — independent of the API unit.
6. Save previous payload tree under e.g. `/srv/kosha/releases/<stamp>/` before swap.

| Step | Done? (Y/N) | Notes |
|---|---|---|
| Staged bundle assembled | **N** | not observed from public net |
| Previous `BUNDLE_IDENTITY` saved | **N** | host-only |
| Host `.env` pinned | **N** | host-only |
| systemd unit up | **N** | `/health` 404 ⇒ unit not public |
| nginx reloaded | **N** | no kosha locations public |
| Static head / cards out-of-band (if in scope) | **partial** | `docs/cards/*.json` live on Pages for some keys; `w/*.html` **missing** at pack href targets |

---

## 3. Readiness probe (required)

### Commands

```sh
curl -fsS https://samskrtam.ru/health
curl -fsS https://samskrtam.ru/ready
curl -fsS 'https://samskrtam.ru/api/v1/meta' | head -c 400
curl -fsS 'https://samskrtam.ru/api/v1/lemma/banD' | head -c 200
```

### Thresholds

| Check | Pass criterion |
|---|---|
| `GET /health` | HTTP **200**, body `{"status":"ok"}` (or equivalent `status: ok`) |
| `GET /ready` | HTTP **200**, `"ready": true` |
| `GET /ready` checks | `core_db` **ok**; data_version readable; corrupt mounted archive → **fail** (not silent) |
| Optional layers | `absent` / `unconfigured` OK while monolith default; **fail** only if required |
| History | `disabled` when `KOSHA_HISTORY_ENABLED=false` — must not look "ready" as a writable |
| Lemma smoke | HTTP **200** with Salt envelope, **or** clean 404 error envelope (not 500 / HTML) |

### Results (public probe 08-08-2026)

| Field | Value |
|---|---|
| Date (UTC) | 2026-08-08T09:44Z |
| Live base URL used | `https://samskrtam.ru` (also tried `/kosha` prefix) |
| Repo tag / bundle id promoted | **none observable** — API not public |
| `data_version` from `/ready` or `/meta` | n/a (404) |
| `GET /health` status + body snippet | **404** Not Found |
| `GET /ready` status + `ready` | **404** Not Found |
| Notable `checks[]` rows | n/a |
| Lemma `banD` status | **404** at `/api/v1/lemma/banD` |
| PASS / FAIL | **FAIL** — production API surface absent |

Also: `https://samskrtam.ru/` → **200** WordPress HTML (site up; kosha routes not mounted).

---

## 4. Lighthouse mobile ≥ 90 (required)

### Scope

Run **Chrome Lighthouse mobile** (Device = Mobile, throttling default mobile) on at
least:

| # | Target | Example URL |
|---|---|---|
| L1 | Static or SSR head word page | `https://samskrtam.ru/w/BU` or Pages `…/w/_42_55.html` (*bhū*) |
| L2 | Second head lemma | pick a high-frequency key from the static head |
| L3 | Third head lemma | different card density (multi-dict) |
| L4 | SPA / reading or `#/w/` route if that is the public entry | `https://gasyoun.github.io/kosha/` or live SPA |

CLI option (when Chrome is available):

```sh
npx --yes lighthouse "https://samskrtam.ru/w/BU" --only-categories=performance --form-factor=mobile --screenEmulation.mobile --output=json --output-path=./lh-w-BU.json --chrome-flags="--headless"
```

Or DevTools → Lighthouse → Mobile → Analyze page load. Paste Performance score only;
Accessibility/SEO are out of scope for this gate.

### Threshold

| Metric | Pass |
|---|---|
| Performance (mobile) | **≥ 90** on **each** of L1–L3; L4 recorded (target ≥90; note if SPA budget differs) |

### Results (public probe 08-08-2026)

| ID | URL | Performance | Report path / screenshot | PASS? |
|---|---|---:|---|---|
| L1 | `https://gasyoun.github.io/kosha/w/_42_55.html` (*bhū*) | n/a | HTTP **404** — surface missing | **FAIL** (blocked) |
| L2 | `https://samskrtam.ru/w/BU` | n/a | HTTP **404** — API/SSR missing | **FAIL** (blocked) |
| L3 | `https://gasyoun.github.io/kosha/w/vac.html` (sample pack token) | n/a | HTTP **404** | **FAIL** (blocked) |
| L4 | `https://gasyoun.github.io/kosha/reading/` | **99** | local `lh-reading.json` (852 695 B; FCP 1.3 s · LCP 1.3 s · TBT 110 ms · CLS 0) | **PASS** (reading only) |

Gate requires L1–L3 ≥90 → **FAIL** overall (word pages not deployed). L4 alone does not pass W1.

---

## 5. Gītā walkthrough (required)

### Goal

Paste / open a **Gītā verse pack**, walk every linked token, and confirm each opens a
word page (static head or SSR) with dictionary panels — same product path as P5 §2.

### Suggested path

1. Open reading surface:
   - Pages: [gasyoun.github.io/kosha/reading/](https://gasyoun.github.io/kosha/reading/)
   - or live host equivalent if reading is reverse-proxied.
2. Open pack **gita-1** (Arjunaviṣāda) — or any single chapter pack under
   [`reading/`](https://github.com/gasyoun/kosha/tree/main/reading).
3. For **one full verse block** (all tokens in that block):
   - click each word link;
   - confirm the word page loads (no blank shell, no uncaught 500);
   - confirm at least one dictionary panel / gloss is visible (static card or API).
4. Optional: toggle Word-by-word / Prose on a Gītā pack if the control is present
   ([H1493](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1493-Sonnet_kosha_kosha-gita-prose-reading-view_22.07.26.md)).

### Thresholds

| Check | Pass |
|---|---|
| Pack opens | chapter UI loads without console-blocking error |
| Token → word page | **every** token in the chosen verse block opens a page |
| Dict content | each opened page shows lemma/dict content or honest empty state (not crash) |
| SSR tail (optional) | one out-of-head lemma via `GET /w/{slp1}` if API is live |

### Results (public probe 08-08-2026)

| Field | Value |
|---|---|
| Date (UTC) | 2026-08-08T09:44Z |
| Reading base URL | https://gasyoun.github.io/kosha/reading/ |
| Pack id (e.g. gita-1) | **gita-1** — pack JS **200** at `reading/data/gita-1.js` (slug `gita-1`, 47 sentences, 570 tokens, 568 linked / 99.6%) |
| Verse / block id | **1.1** (`dhṛtarāṣṭra uvāca` / locus Bhagavadgītā 1.1) |
| Token count in block | **13** (all carry `href` like `../w/_44ftar_41zwra.html`) |
| Tokens that failed (list) | **all 13 href targets** resolve under `https://gasyoun.github.io/kosha/w/…` → **404** (sampled: `_44ftar_41zwra`, `vac`, `_44armakzetra`, `kurukzetra`, …). Side note: some cards exist at `docs/cards/{token}.json` (200) but pack links point at `../w/`, not cards. |
| Sample successful word-page URL | **none** at pack href path |
| Prose toggle checked? (Y/N/n/a) | n/a (HTTP probe of pack data only; `data/gita_prose.js` is listed in the reading index) |
| PASS / FAIL | **FAIL** — pack + data load; **token → word page** broken (static `w/` not on Pages; API SSR 404) |

---

## 6. Citation resolve checks (required for release assets)

### Purpose

Prove a sense citation of the form `{dict}.{L}.{senseN}@{data_version}` remains
resolvable — live DB for current version; **archive / GitHub release asset** for a
pinned older (or current published) data version (RISKS R1).

### Commands (live API)

Replace IDs with values present on the promoted DB (from `/api/v1/meta` /
a known MW entry). Example shape only — **do not invent L numbers**:

```sh
# Live (current data_version)
curl -fsS 'https://samskrtam.ru/api/v1/sense/mw.1.1'

# Pinned (must match an archived or live version string)
curl -fsS 'https://samskrtam.ru/api/v1/sense/mw.1.1@DATA_VERSION_HERE'
```

### Release-asset openability (product gate)

From a `cite` object returned by the sense endpoint (or from a published data release):

1. Open the `release_asset` / archive URL named in the cite payload (GitHub Releases
   `data-v*` asset — e.g. [data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0)
   or the current data release on the host).
2. Confirm HTTP 200 and non-empty body (or browser download starts).
3. If `KOSHA_ARCHIVE_DIR` is mounted on the host, confirm `/ready` reports archives
   **ok** (not corrupt) and a pinned sense resolves with `"resolved_from": "archive"`
   when the pin ≠ live `data_version`.

### Thresholds

| Check | Pass |
|---|---|
| Live sense | HTTP 200, `resolved_from: live`, `sense_id` carries `@data_version` |
| Pinned sense (if archive mounted) | 200 + `resolved_from: archive`, **or** honest 404 `version_not_archived` with release-asset suggestion |
| Release asset URL | opens / downloads (200) for at least one published `data-v*` asset used in production cites |
| No host-only cite | cite URLs must not require the production host as the **only** resolve path (R5) |

### Results (public probe 08-08-2026)

| Field | Value |
|---|---|
| Live sense URL tested | `https://samskrtam.ru/api/v1/sense/…` |
| Live HTTP + `resolved_from` | **API 404** — cannot exercise live sense resolve |
| Pinned sense URL tested | n/a (no live API / no archive mount signal) |
| Pinned HTTP + `resolved_from` | n/a |
| Release asset URL opened | https://github.com/gasyoun/kosha/releases/download/data-v0.1.0/datasets.json |
| Asset HTTP / size note | **200**, **11 728** bytes; tag `data-v0.1.0` has **8** assets (incl. `union_headwords.tsv`, `lemma_frequency.tsv`, …) |
| Archive mount configured? (Y/N) | **N** (public — no `/ready` to confirm host mount) |
| PASS / FAIL | **FAIL** overall (live/pinned sense blocked). **Partial PASS** on release-asset openability alone (R1 durable tier works without samskrtam.ru). |

---

## 7. Rollback confirmation (required)

### Goal

Prove the **previous** bundle identity can be restored and the API returns healthy
after restore — per [`KOSHA_DEPLOYMENT.md`](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md)
Part IV and `deploy_bundle.json` `rollback` object.

### Steps (production, MG)

1. Confirm `previous_bundle_identity` file exists (saved in §2).
2. `sudo systemctl stop kosha`
3. Point `current` (WorkingDirectory) at the previous payload tree whose digests match
   that identity.
4. Restore previous core DB (and attached stores) named by those digests — do **not**
   hot-patch `kosha.db` for dictionary corrections.
5. Restore previous `.env` path values if they changed.
6. `sudo systemctl start kosha`
7. Verify:

```sh
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/ready
curl -fsS 'http://127.0.0.1:8000/api/v1/lemma/banD' | head -c 200
```

8. Optionally re-promote the new bundle after the drill, or leave previous live if the
   new promote failed — record which identity is live at end of session.

### Thresholds

| Check | Pass |
|---|---|
| Previous identity retained before promote | file present, digests recorded |
| Restore completes | unit starts without crash loop |
| Post-rollback `/health` | 200 |
| Post-rollback `/ready` | 200 + `ready: true` (or documented expected fail if previous was intentionally incomplete) |
| Lemma smoke | 200 or clean 404 envelope |

### Results (public probe 08-08-2026)

| Field | Value |
|---|---|
| Date (UTC) | 2026-08-08T09:44Z |
| Previous bundle id / stamp | n/a — no public promote observed |
| New bundle id that was rolled back from | n/a |
| Identity live **after** drill | n/a |
| `/health` after rollback | not run (host-only; no public unit) |
| `/ready` after rollback | not run |
| Lemma smoke after rollback | not run |
| Re-promoted new bundle after drill? (Y/N) | n/a |
| PASS / FAIL | **FAIL** / blocked — requires host access after first promote |

### Results (live Part IV drill 2026-08-14T00:27Z, H2672)

No previous identity existed (first promote 08-08 had none). Created
previous from the live tree, then a no-op second identity, restored
previous, smoked, immediately re-promoted current. Same
`kosha.db` digest on both hops (hashed in place; never copied or replaced).

| Field | Value |
|---|---|
| Date (UTC) | 2026-08-14T00:26:59Z restore · 00:27:31Z re-promote |
| Operator | Grok 4.6 (`grok-4.6`) |
| Previous identity | `/opt/kosha/releases/h2672-previous/bundle/BUNDLE_IDENTITY.json` — git `2649f046`, 63 payload files, no stamp; runtime `/opt/kosha/releases/h2672-previous/runtime` |
| Current identity | `/opt/kosha/releases/h2672-current/bundle/BUNDLE_IDENTITY.json` — git `2649f046` + `deploy/H2672_NOOP_STAMP`; live WD `/opt/kosha/repo` |
| Core DB | `/opt/kosha/db/kosha.db` sha256 `140c6638811559677c4335c034dce5c2718e56868a188acc1e9bac15b6b34f04` (1 732 337 664 B) |
| `/health` after restore | **200** `{"status":"ok"}` — local `:8001`, [samskrtam.ru/health](https://samskrtam.ru/health), sslip |
| `/ready` after restore | **200** `ready:true` `0.1.0-dev`; `core_db` ok; archives **ok**; history disabled |
| Lemma after restore | [samskrtam.ru/api/v1/lemma/banD](https://samskrtam.ru/api/v1/lemma/banD) **200** 179 914 B |
| `/health` after re-promote | **200** `{"status":"ok"}` — same three URLs |
| `/ready` after re-promote | **200** `ready:true`; archives still **ok** |
| Lemma / SSR after re-promote | `banD` **200** 179 914 B; [samskrtam.ru/w/BU](https://samskrtam.ru/w/BU) **200** 240 211 B |
| Identity live **after** drill | **current** — WD `/opt/kosha/repo` @ `2649f046` (H2670); drop-in removed |
| Re-promoted new bundle after drill? (Y/N) | **Y** — immediately |
| PASS / FAIL | **PASS** — both hops green; unit left on current. Wave 1 **not** declared complete |

---

## 8. Gate summary

### 8a. Morning public probe 09:44Z (pre-promote)

| Gate | Result | Note |
|---|---|---|
| Pre-flight / readiness / live cite | **FAIL** | `samskrtam.ru` kosha routes 404 |
| Lighthouse L1–L3 | **FAIL** | surfaces 404; L4 reading **99** |
| Gītā walkthrough | **FAIL** | pack OK; `../w/` hrefs 404 |
| Rollback | blocked | no first promote yet |

### 8b. After first promote 12:25Z (sslip.io)

| Gate | Threshold | Result | Evidence |
|---|---|---|---|
| Pre-flight deploy (API unit) | systemd + nginx + DB | **PASS** on `.92` | `/opt/kosha/OPS.md`; unit `kosha` active |
| Readiness | §3 | **PASS** on sslip public URL | `/ready` `ready:true`, `0.1.0-dev` |
| Lemma smoke | Salt envelope | **PASS** | `/api/v1/lemma/banD` 200 |
| Live sense | `resolved_from: live` | **PASS** | `/api/v1/sense/mw.101.1` 200 |
| SSR `/w/{slp1}` | 200 | **PASS** | `/w/BU` 200 on sslip |
| Branded host `samskrtam.ru` | same as sslip | **FAIL** residual | still WP on `.95`; no agent SSH |
| Lighthouse mobile L1–L3 | ≥90 | **PASS 100/100/100** | sslip `/w/vac`, `/w/BU`, `/w/banD` (`lh-w-*.json`, 12:34Z) |
| Gītā walkthrough | pack → word pages | **PASS 13/13** | pack Pages + sslip SSR `/w/{slp1}` for verse 1.1; Pages relative `../w/` still 404 residual |
| Citation archives | mount + pinned | **unconfigured** | empty `/opt/kosha/archive`; live path works |
| Rollback drill | previous identity | **PASS*** | unit stop/start recovery; *no prior identity (first promote) |

**W1 product exit on live base sslip.io:** **PASS** (measured 12:34Z).  
**Branded / Pages / archive product residuals:** still open (list below).

**W2 unlock (H2346):** live API smoke is green; engineering may proceed when a human
accepts the sslip base (or after branded DNS). Residual work below is the honest gap.

### Residual work (ordered)

1. ~~Optional: point `samskrtam.ru` (`.95`) reverse-proxy or DNS at kosha on `.92:8001` / sslip.~~ — **done** 13-08-2026 (H2646): path proxy, not DNS move.
2. ~~Optionally deploy Pages **static head** so pack hrefs `../w/{token}.html` resolve without sslip.~~ — **done** 13-08-2026 (H2665): committed pack-token HTML at repo-root `w/` (2,324 pages / 60.4 MB); full D4 `docs/w/` head stays gitignored.
3. ~~Lighthouse mobile ≥90 on three real `/w/` URLs~~ — **done** 100×3 on sslip.
4. ~~Re-walk Gītā 1.1 (13 tokens) on SSR~~ — **done** 13/13 on sslip.
5. ~~Mount citation archives under `/opt/kosha/archive` + pinned-sense smoke.~~ — **done** 14-08-2026 (H2671): live `0.1.0-dev` snapshot; `/ready` archives **ok**; see §8e.
6. ~~On **second** promote: retain `BUNDLE_IDENTITY` and run full Part IV restore.~~ — **done** 14-08-2026 (H2672): previous+current identities under `/opt/kosha/releases/`; restore then immediate re-promote; unit left on current. See **8f. Identity rollback drill**.
7. Sign-off table in **Sign-off** below — a human ticks the branded-complete box. An agent must not mark Wave 1 complete.

### 8c. W2C re-fill 2026-08-13T11:13Z (sslip.io @ v0.110.3)

Host was 12 commits behind (`0cd22ef5`, first-promote docs). Pulled
`origin/main` **ff-only** to `ae4f93c4` (`v0.110.3`), `pip install -r
requirements.txt` (no new runtime pins), `systemctl restart kosha`. DB
untouched (`/opt/kosha/db/kosha.db`, `0.1.0-dev`). nginx `location /`
already proxies `/metrics`; no site-file edit required.

| Gate | Threshold | Result | Evidence |
|---|---|---|---|
| Code SHA | `origin/main` | **PASS** | `/opt/kosha/repo` @ `ae4f93c4` |
| Unit | active | **PASS** | `kosha.service` active after restart |
| `GET /health` | 200 `status:ok` | **PASS** | public sslip 200 + minted `X-Request-ID` |
| `GET /ready` | 200 `ready:true` | **PASS** | `data_version=0.1.0-dev`; `core_db` ok; `data_version_match` ok; archives **unconfigured**; history **disabled** |
| Correlation | echo / mint | **PASS** | `X-Request-ID: w1e-fill-01` echoed; minted UUID on bare `/health` |
| `GET /metrics` | Prometheus, low-card | **PASS** | 200 `text/plain; version=0.0.4`; `kosha_ready`, `kosha_http_requests_total{route="/ready"}` — no headword labels |
| Lemma `banD` | Salt envelope | **PASS** | 200, `data_version=0.1.0-dev`, MW/PWG/AP90 |
| Live sense `mw.101.1` | `resolved_from: live` | **PASS** | 200, `sense_id` `mw.101.1@0.1.0-dev`; cite `resolution_url` on Pages |
| Catalog `GET /api/v1/datasets` | W2B public list | **PASS** | 200, `schema=kosha-dataset-catalog-v1`, `count=84` |
| SSR `/w/BU` | 200 HTML | **PASS** | 200, 236 426 B |
| Gītā 1.1 tokens | 13/13 SSR | **PASS 13/13** | sslip `/w/{slp1}` for `DftarAzwra vac Darmakzetra kurukzetra samaveta yuyutsu mAmaka pARqava ca eva kim kf ji` |
| Lighthouse L1–L3 | ≥90 | **PASS (prior 100)** | not re-run this pass; SSR still 200 on the same three URLs; 08-08 scores 100/100/100 stand unless a human re-measures |
| Branded `samskrtam.ru` | same as sslip | **FAIL** residual | `/health` now **403** (was 404 on 08-08) — still not kosha; host `.95` |
| Pages `w/` hrefs | pack `../w/` | **FAIL** residual | `https://gasyoun.github.io/kosha/w/vac.html` 404; cards at `docs/cards/vac.json` 200 |
| Release asset | data-v0.1.0 | **PASS** | `datasets.json` 200, 11 728 B |
| Archives | mount | **unconfigured** | `/opt/kosha/archive` empty |

**W1 product exit on live sslip base:** still **PASS** (re-confirmed 13-08-2026, now including W2C).  
**W1 branded / Pages / archive / §9:** branded API **PASS** 13-08 (H2646); Pages `w/` + archives + §9 still open. Agent does not sign §9.

### 8d. Branded wire 2026-08-13T13:05Z (`samskrtam.ru` → LAN `:8002`)

`.95` has no SSH. FTP + WordPress `.htaccess` + mu-plugin proxy to
`192.168.200.92:8002` (nginx allowlist). WordPress `/` and `/faq/` stay on `.95`.

| Check | Result |
|---|---|
| `https://samskrtam.ru/health` | **200** `{"status":"ok"}` |
| `https://samskrtam.ru/ready` | **200** `ready:true` `0.1.0-dev` |
| `https://samskrtam.ru/metrics` | **200** Prometheus |
| `https://samskrtam.ru/api/v1/lemma/banD` | **200** 179 914 B |
| `https://samskrtam.ru/w/BU` | **200** HTML |
| `X-Request-ID: brand-wire-01` | echoed; `X-Kosha-Proxy: http://192.168.200.92:8002` |
| `https://samskrtam.ru/` WP home | **200** (unchanged) |
| `https://samskrtam.ru/faq/` | **200** (unchanged) |
| `https://samskrtam.ru/wp-json/` | **200** (not proxied) |

### 8e. Citation-archive mount 2026-08-14T00:30Z (H2671)

R3/R10/R18: one pin, snapshot of live `0.1.0-dev` (not a new `data_version`).
Live DB opened read-only and not written (`/opt/kosha/db/kosha.db` mtime
still 08-08 12:16). No unit restart. `KOSHA_ARCHIVE_DIR=/opt/kosha/archive`
was already in `/opt/kosha/.env`.

| Check | Result |
|---|---|
| Mount | `/opt/kosha/archive/0.1.0-dev/senses.sqlite` **98 MB**, `kosha:kosha` |
| Identity | `release.json` `version=0.1.0-dev` `senses=692403` `sha256=cb3f6988859fa83ab92706a0f83d289ba060baf560cee369ae58d997631bbdfc` |
| Archive count | **692403** (matches live `senses` count) |
| Sample row | `mw.101.1` → headword `aMseBAra` |
| `GET https://samskrtam.ru/ready` | **200** `ready:true`; `citation_archives` **ok** `1 archived version(s) validated` |
| `GET https://samskrtam.ru/api/v1/sense/mw.101.1@0.1.0-dev` | **200** `sense_id=mw.101.1@0.1.0-dev` `resolved_from=live` |

`resolved_from` is **live** because the pin equals the live `data_version`
(`app/main.py` `get_sense`: archive path only when `want_version != dv`).
That is the documented equivalent for R10 (do not invent a second version
just to force `resolved_from: archive`). The mount is proven by `/ready`
`citation_archives=ok` plus the on-disk dump. Wave 1 is **not** declared
complete.

### 8f. Identity rollback drill 2026-08-14T00:27Z (H2672)

R4/R11/R19: live
[KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md)
Part IV restore on `.92`, not a paper rehearsal. First promote had no prior
identity, so previous was assembled from the live tree (`2649f046`, H2670)
and current is the same tree plus a no-op `deploy/H2672_NOOP_STAMP`. Restore
switched systemd `WorkingDirectory` to the previous runtime snapshot; re-promote
removed the drop-in and returned WD to `/opt/kosha/repo`. Core DB was **not**
copied or replaced (same sha256 on both hops). H2670 language groups and
H2671 archive mount remain the live product.

| Check | Result |
|---|---|
| Previous identity | `/opt/kosha/releases/h2672-previous/bundle/BUNDLE_IDENTITY.json` git `2649f046` 63 files |
| Current identity | `/opt/kosha/releases/h2672-current/bundle/BUNDLE_IDENTITY.json` git `2649f046` + stamp 64 files |
| Pointers | `/opt/kosha/releases/previous_bundle_identity` · `/opt/kosha/releases/current_bundle_identity` |
| DB digest | `140c6638811559677c4335c034dce5c2718e56868a188acc1e9bac15b6b34f04` in place; `core_db_copied=false` |
| Restore start/stop | 00:26:59Z stop+WD previous · 00:27:02Z `/health`+`/ready` 200 |
| Restore WD | `/opt/kosha/releases/h2672-previous/runtime` unit `active` |
| Re-promote start/stop | 00:27:31Z stop+WD live · 00:27:34Z `/health`+`/ready` 200 |
| Re-promote WD | `/opt/kosha/repo` @ `2649f046` unit `active`; drop-in gone |
| [samskrtam.ru/health](https://samskrtam.ru/health) both hops | **200** `{"status":"ok"}` |
| [samskrtam.ru/ready](https://samskrtam.ru/ready) both hops | **200** `ready:true` archives **ok** |
| sslip `/health`+`/ready` both hops | **200** / **200** |
| Host log | `/opt/kosha/OPS.md` section **Identity rollback drill** |

Wave 1 is **not** declared complete.

---

## 9. Sign-off

| Field | Value |
|---|---|
| Operator (probe) | Grok 4.5 (`grok-4.5`) public probe 09:44Z |
| Operator (promote) | Grok 4.5 (`grok-4.5`) first live promote 12:25Z on human “promotes” |
| Operator (W2C re-fill) | Grok 4.6 (`grok-4.6`) 2026-08-13T11:13Z (H2642) |
| Operator (archive mount) | Grok 4.6 (`grok-4.6`) 2026-08-14T00:30Z (H2671) |
| Operator (identity rollback) | Grok 4.6 (`grok-4.6`) 2026-08-14T00:27Z (H2672) |
| Date (UTC) | 2026-08-14 (rollback drill); first promote 2026-08-08 |
| Live API base | **https://kosha.193.232.229.92.sslip.io/** (`data_version` **0.1.0-dev**, code **v0.110.10** / `2649f046`) |
| Branded API base | **https://samskrtam.ru** — kosha paths live 13-08-2026 (H2646); WP `/` unchanged |
| Live static base | `https://gasyoun.github.io/kosha/` (reading + docs-site; pack-token `w/` from H2665) |
| Host layout | `/opt/kosha/{repo,venv,db,archive,.env,releases}` + `kosha.service` |
| W1 product exit (live sslip base) | ☑ measured **PASS** (re-confirmed 14-08) · ☐ branded complete |
| Notes / waivers | Live-base smoke **PASS** including W2C, archive mount, and Part IV rollback drill. The Sign-off branded-complete box still needs a human tick. An agent must not mark Wave 1 complete. |

---

## 10. Related artifacts

| Artifact | Role |
|---|---|
| [KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md) | Deploy + rollback procedure |
| [data/manifest/deploy_bundle.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/deploy_bundle.json) | Machine bundle recipe |
| [docs/DEPLOY_REHEARSAL_LOG.md](https://github.com/gasyoun/kosha/blob/main/docs/DEPLOY_REHEARSAL_LOG.md) | Local fixture rehearsal (agent) |
| [docs/P5_WORD_PAGE_EXIT_PACKET.md](https://github.com/gasyoun/kosha/blob/main/docs/P5_WORD_PAGE_EXIT_PACKET.md) | Static head / Lighthouse / Gītā product exit (P5) |
| [src/kosha/api/readiness.py](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/readiness.py) | `/ready` checks (W1C) |
| [docs/RELEASE_OBSERVABILITY.md](https://github.com/gasyoun/kosha/blob/main/docs/RELEASE_OBSERVABILITY.md) | W2C correlation + `/metrics` watch list |
| GTD row | Existing **kosha W1 / P5 live checks** `@DO` — this packet is the superseding checklist |

---

## 11. Agent evidence

| Item | Value |
|---|---|
| Packet path | `docs/MG_LIVE_SMOKE_PACKET_W1E.md` |
| Model | Grok 4.6 (`grok-4.6`) re-fill; original promote Grok 4.5 (`grok-4.5`) |
| Morning probe credentials | **no** |
| Promote host access | SSH `root@193.232.229.92` (existing key; no new secrets committed) |
| W1 declared complete by agent | **no** |
| Public probe date | 2026-08-08T09:44Z |
| Promote date | 2026-08-08T12:25Z |
| W2C re-fill date | 2026-08-13T11:13Z |
| Archive mount date | 2026-08-14T00:30Z (H2671) |
| Identity rollback date | 2026-08-14T00:27Z (H2672) |
| Public API | https://kosha.193.232.229.92.sslip.io/ |
| Host SHA | `2649f046` / v0.110.10 (H2670 tree; unit left here after drill) |
| Host ops | `/opt/kosha/OPS.md` |
| Lighthouse artifacts (local, not committed) | `lh-w-vac.json` / `lh-w-BU.json` / `lh-w-banD.json` = **100** (08-08); not re-run 13-08 |
| Next | human tick of the branded-complete box in **Sign-off** — an agent must not mark Wave 1 complete |

---

_Dr. Mārcis Gasūns_
