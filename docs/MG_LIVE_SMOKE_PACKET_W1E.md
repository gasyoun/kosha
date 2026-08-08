# W1E — MG live-smoke packet (public-product readiness exit)

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Handoff:** [H2345](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2345-Grok_kosha_architecture-roadmap-w1e-mg-live-smoke-packet_07.08.26.md)
(Grok 4.5 `grok-4.5` — agent half shipped; public-probe fill 08-08-2026).

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

**Fill mode (this pass):** public HTTP + Lighthouse only (Grok 4.5 `grok-4.5`,
2026-08-08T09:44Z). **No SSH, no production credentials, no systemd rollback drill.**
W1 product exit remains **not complete** — see §8–§9.

---

## 0. Agent non-execution fence (hard)

| Rule | Status this session |
|---|---|
| No production credentials received or used | **held** |
| No SSH / FTP / `deploy_guhya.py --upload` / host panel | **held** |
| No production systemd / nginx / DB swap | **held** |
| Agent does not declare W1 complete | **held** — §8 is FAIL overall |

W1 is complete only when all required rows PASS (or explicit WAIVE with reason a human
accepts) **after a real production promote**, and §9 is signed by M.G.

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

**Path rewrite:** none found for the API — neither bare host nor `/kosha/` serves
`/health` / `/ready` / `/api/v1/*`. Production kosha API is **not promoted**.

**Citation durability (RISKS R5):** `KOSHA_PUBLIC_BASE` used in minting must remain a
**durable** citation base (typically the GitHub Pages / release-asset policy), not a
single deployment host that can vanish. Live resolve on the API host is a smoke check;
release-asset openability is the product gate.

---

## 2. Pre-flight (MG only — production deploy)

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

---

## 8. Gate summary (after public probe 08-08-2026)

| Gate | Threshold | Result (PASS/FAIL/WAIVE) | Evidence link / note |
|---|---|---|---|
| Pre-flight deploy | §2 all critical steps | **FAIL** | API not public; static `w/` missing |
| Readiness | §3 | **FAIL** | `/health` `/ready` `/api/v1/*` → 404 |
| Lighthouse mobile | ≥90 on L1–L3 | **FAIL** | L1–L3 surfaces 404; L4 reading **99** only |
| Gītā walkthrough | §5 | **FAIL** | pack OK; all verse-1.1 `../w/` hrefs 404 |
| Citation resolve | §6 | **FAIL** (partial) | live sense blocked; **data-v0.1.0** asset 200 |
| Rollback | §7 | **FAIL** / blocked | host-only; no first promote |

**W1 product exit:** **not complete** (required gates FAIL).

**W2 unlock:** still gated. Next agent series **H2346+** only after a human promote
clears §3–§7 and §9 is signed.

### Residual human work (ordered)

1. **Promote** kosha API per `KOSHA_DEPLOYMENT.md` Part III so `/health` and `/ready` are public.
2. Deploy regenerable **static head** so pack hrefs `../w/{token}.html` resolve (or retarget links to live cards/SSR).
3. Re-run Lighthouse on three real `/w/` pages; keep reading L4 as optional.
4. Re-walk Gītā 1.1 (13 tokens) on the fixed word-page path.
5. Exercise live + pinned sense resolve with real L-numbers from the promoted DB.
6. Host rollback drill with retained `BUNDLE_IDENTITY`.
7. Sign §9.

---

## 9. Sign-off

| Field | Value |
|---|---|
| Operator | public probe by Grok 4.5 (`grok-4.5`) — **not** M.G. product sign-off |
| Date (UTC) | 2026-08-08T09:44Z |
| Live API base | **absent** (`https://samskrtam.ru` serves WP; no kosha routes) |
| Live static base | `https://gasyoun.github.io/kosha/` (reading + docs-site; `w/` missing) |
| Bundle / tag promoted | none observed for API |
| W1 product exit | ☑ **not yet** · ☐ complete |
| Notes / waivers | Public-probe fill only. No WAIVE of FAIL gates. M.G. must re-fill after promote and tick complete. |

---

## 10. Related artifacts

| Artifact | Role |
|---|---|
| [KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md) | Deploy + rollback procedure |
| [data/manifest/deploy_bundle.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/deploy_bundle.json) | Machine bundle recipe |
| [docs/DEPLOY_REHEARSAL_LOG.md](https://github.com/gasyoun/kosha/blob/main/docs/DEPLOY_REHEARSAL_LOG.md) | Local fixture rehearsal (agent) |
| [docs/P5_WORD_PAGE_EXIT_PACKET.md](https://github.com/gasyoun/kosha/blob/main/docs/P5_WORD_PAGE_EXIT_PACKET.md) | Static head / Lighthouse / Gītā product exit (P5) |
| [src/kosha/api/readiness.py](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/readiness.py) | `/ready` checks (W1C) |
| GTD row | Existing **kosha W1 / P5 live checks** `@DO` — this packet is the superseding checklist |

---

## 11. Agent evidence

| Item | Value |
|---|---|
| Packet path | `docs/MG_LIVE_SMOKE_PACKET_W1E.md` |
| Model | Grok 4.5 (`grok-4.5`) |
| Production host credentials used | **no** |
| W1 declared complete by agent | **no** |
| Public probe date | 2026-08-08T09:44Z |
| Lighthouse artifact (local, not committed) | `lh-reading.json` Performance **99** on reading/ |
| Next after live smoke | H2346+ W2 — only when §8–§9 PASS after real promote |

---

_Dr. Mārcis Gasūns_
