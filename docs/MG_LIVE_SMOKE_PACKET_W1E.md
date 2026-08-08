# W1E — MG live-smoke packet (public-product readiness exit)

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Handoff:** [H2345](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2345-Grok_kosha_architecture-roadmap-w1e-mg-live-smoke-packet_07.08.26.md)
(Grok 4.5 `grok-4.5` — agent half: this packet only).

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

---

## 0. Agent non-execution fence (hard)

| Rule | Status this session |
|---|---|
| No production credentials received or used | **held** |
| No SSH / FTP / `deploy_guhya.py --upload` / host panel | **held** |
| No production systemd / nginx / DB swap | **held** |
| Agent does not declare W1 complete | **held** — only MG fills § results |

W1 is **not** complete when this packet merges. W1 is complete only when MG fills the
result tables below (all required rows PASS or explicit WAIVE with reason) and signs §9.

Agents may re-run the **local** rehearsal from H2344; that does not substitute for live smoke.

---

## 1. Public URLs (from H2344 runbook — do not invent hosts)

Use the host that is actually serving the **promoted** bundle. Defaults from
[`KOSHA_DEPLOYMENT.md`](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md)
Part III:

| Surface | Default public URL | Role |
|---|---|---|
| API liveness | `https://samskrtam.ru/health` | process up |
| API readiness | `https://samskrtam.ru/ready` | DB + version + archives |
| Lemma card | `https://samskrtam.ru/api/v1/lemma/banD` | Salt-compatible envelope |
| Sense / citation live | `https://samskrtam.ru/api/v1/sense/{dict}.{L}.{n}` | live resolve |
| Sense / citation pinned | `https://samskrtam.ru/api/v1/sense/{dict}.{L}.{n}@{data_version}` | archive path |
| SSR word page | `https://samskrtam.ru/w/{slp1}` | long-tail / head SSR |
| Pages static SPA | `https://gasyoun.github.io/kosha/` | committed static tier |
| Pages reading packs | `https://gasyoun.github.io/kosha/reading/` | Gītā packs (if Pages path used) |
| Pages word head (when deployed) | `https://gasyoun.github.io/kosha/w/{token}.html` | static head (gitignored; MG deploys) |

If the live API is mounted under a path prefix (e.g. `https://samskrtam.ru/kosha/`),
rewrite every absolute path in this packet by that prefix and record the rewrite in §9.

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
| Staged bundle assembled | | |
| Previous `BUNDLE_IDENTITY` saved | | |
| Host `.env` pinned | | |
| systemd unit up | | |
| nginx reloaded | | |
| Static head / cards out-of-band (if in scope) | | |

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

### Results (MG fills)

| Field | Value |
|---|---|
| Date (UTC) | |
| Live base URL used | |
| Repo tag / bundle id promoted | |
| `data_version` from `/ready` or `/meta` | |
| `GET /health` status + body snippet | |
| `GET /ready` status + `ready` | |
| Notable `checks[]` rows | |
| Lemma `banD` status | |
| PASS / FAIL | |

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

### Results (MG fills)

| ID | URL | Performance | Report path / screenshot | PASS? |
|---|---|---:|---|---|
| L1 | | | | |
| L2 | | | | |
| L3 | | | | |
| L4 | | | | |

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

### Results (MG fills)

| Field | Value |
|---|---|
| Date (UTC) | |
| Reading base URL | |
| Pack id (e.g. gita-1) | |
| Verse / block id | |
| Token count in block | |
| Tokens that failed (list) | |
| Sample successful word-page URL | |
| Prose toggle checked? (Y/N/n/a) | |
| PASS / FAIL | |

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

### Results (MG fills)

| Field | Value |
|---|---|
| Live sense URL tested | |
| Live HTTP + `resolved_from` | |
| Pinned sense URL tested | |
| Pinned HTTP + `resolved_from` | |
| Release asset URL opened | |
| Asset HTTP / size note | |
| Archive mount configured? (Y/N) | |
| PASS / FAIL | |

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

### Results (MG fills)

| Field | Value |
|---|---|
| Date (UTC) | |
| Previous bundle id / stamp | |
| New bundle id that was rolled back from | |
| Identity live **after** drill | |
| `/health` after rollback | |
| `/ready` after rollback | |
| Lemma smoke after rollback | |
| Re-promoted new bundle after drill? (Y/N) | |
| PASS / FAIL | |

---

## 8. Gate summary (MG fills after live run)

| Gate | Threshold | Result (PASS/FAIL/WAIVE) | Evidence link / note |
|---|---|---|---|
| Pre-flight deploy | §2 all critical steps | | |
| Readiness | §3 | | |
| Lighthouse mobile | ≥90 on L1–L3 | | |
| Gītā walkthrough | §5 | | |
| Citation resolve | §6 | | |
| Rollback | §7 | | |

**W1 product exit:** all required gates **PASS** (WAIVE only with written reason a human accepts).

**W2 unlock:** only after this summary is fully filled and §9 is signed. Next agent series:
**H2346+** (W2 citable v1) — do **not** start W2 engineering on agent say-so alone.

---

## 9. Sign-off

| Field | Value |
|---|---|
| Operator | M.G. |
| Date (UTC) | |
| Live API base | |
| Live static base | |
| Bundle / tag promoted | |
| W1 product exit | ☐ not yet · ☐ complete |
| Notes / waivers | |

---

## 10. Related artifacts

| Artifact | Role |
|---|---|
| [KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md) | Deploy + rollback procedure |
| [data/manifest/deploy_bundle.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/deploy_bundle.json) | Machine bundle recipe |
| [docs/DEPLOY_REHEARSAL_LOG.md](https://github.com/gasyoun/kosha/blob/main/docs/DEPLOY_REHEARSAL_LOG.md) | Local fixture rehearsal (agent) |
| [docs/P5_WORD_PAGE_EXIT_PACKET.md](https://github.com/gasyoun/kosha/blob/main/docs/P5_WORD_PAGE_EXIT_PACKET.md) | Static head / Lighthouse / Gītā product exit (P5) |
| [src/kosha/api/readiness.py](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/readiness.py) | `/ready` checks (W1C) |
| GTD row | Existing **kosha P5 product exit (live checks)** `@DO` — fill **this** packet as the W1 superseding checklist |

---

## 11. Agent close evidence (this half)

| Item | Value |
|---|---|
| Packet path | `docs/MG_LIVE_SMOKE_PACKET_W1E.md` |
| Model | Grok 4.5 (`grok-4.5`) |
| Production host touched by agent | **no** |
| W1 declared complete by agent | **no** |
| Next after live smoke | H2346+ W2 (citable v1) — only when §8–§9 filled |

---

_Dr. Mārcis Gasūns_
