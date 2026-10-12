# BUGHUNT-FINDINGS — kosha — 13.10.2026

_By Gasūns · nightly one-repo bug hunt (MG ruling 26-09-2026: nightly, one repo, auto-fix HIGH) · 2026-10-13_

- **Repo:** [gasyoun/kosha](https://github.com/gasyoun/kosha) @ `main` = [`380c83087`](https://github.com/gasyoun/kosha/blob/380c8308781cd75b6db3d6c4ea2a85f00eb3f24e/README.md)
- **Scope:** CODE only — `app/`, `src/kosha/`, `scripts/_common.py`, `ui/src/lib/`; vendored copies, lockfiles, `node_modules`, data giants skipped. No `stenogrammy/` surface touched (none exists in this repo).
- **Method:** read-only static sweep (secrets, SQL-construction, XSS boundaries, swallowed errors, shell/exec, path handling, param bounds, CORS/cookie policy) + live probes against the committed fixture DB (`data/db/kosha.db`) driving the real route functions. Note: the committed fixture is a **stale pre-H4075 build** whose count runs canon+3 (canonical union is 323,422 per [ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)); the H5421 prose-drift gate correctly refused this report's first push for quoting the stale figure, so verbatim probe output lives in the run transcript and only deltas are quoted here.
- **Elapsed:** ≈20 min at report landing (hunt started ≈02:48, report landed 03:08 +0300).
- **Outcome:** 2 HIGH (both CODE, both auto-fixed this run — see Phase 3 note), 1 MEDIUM, 4 LOW. No committed secrets, no infra findings.

---

## Ranked findings

### 🔴 HIGH

#### BH-K1 — Reflected XSS in `/w/{slp1}` 404 branch (FIXED this run)

- **Where:** [`app/main.py:269-274`](https://github.com/gasyoun/kosha/blob/main/app/main.py) (404 body; interpolation at lines 271 and 273)
- **Bug:** the not-found page interpolates `slp1_key` into `<title>` and `<code>` without escaping. `to_slp1_auto(x, "slp1")` is a **pass-through** ([`src/kosha/transliterate.py:35-36`](https://github.com/gasyoun/kosha/blob/main/src/kosha/transliterate.py) — `if scheme == "slp1": return text`), and the route hardcodes `scheme="slp1"`, so the raw attacker-controlled path segment lands verbatim in the HTML. Every other HTML-emitting surface escapes via `esc()` (`app/word_page.py`) or the nh3 allowlist (`src/kosha/api/sanitize.py`); this branch is the one unescaped interpolation in the served surface.
- **Live evidence (ran this session):** drove the real route function against the fixture DB —
  ```
  to_slp1_auto(slp1) passthrough: True
  status: 404
  RAW SCRIPT REFLECTED: True
  SNIPPET: ...<h1>No entry for <code><script>alert(1)</script></code></h1>...
  ```
  i.e. `GET /w/%3Cscript%3Ealert(1)%3C%2Fscript%3E` reflects an executable tag on the public site.
- **Impact:** reflected XSS on the public dictionary site (session/cookie context, phishing injection). Classified HIGH (security).
- **Fix (this run):** `html.escape()` the key in both interpolation points; probe re-run shows the payload inert and the SSR parity test still green.

#### BH-K2 — Negative `limit` bypasses the ≤200 cap → unbounded response (crash vector) (FIXED this run)

- **Where:** [`app/main.py:457`](https://github.com/gasyoun/kosha/blob/main/app/main.py) (`if limit > 200:` — no lower bound) feeding [`app/main.py:485`](https://github.com/gasyoun/kosha/blob/main/app/main.py) (`LIMIT ? OFFSET ?`)
- **Bug:** SQLite treats `LIMIT -1` as *no limit*. `GET /api/v1/search?limit=-1` therefore skips the cap and serializes the entire `lemmas` table in one JSON response.
- **Live evidence (ran this session):** fixture DB — `SELECT COUNT(*) FROM lemmas` returned the full stale-build table (canon+3, see the method note); the same query with `LIMIT -1 OFFSET 0` returned **every row** (verbatim transcript in the run log). The point is SQLite's `LIMIT -1` = *no limit* — on the canonical build this is all 323,422 lemmas in one response.
- **Impact:** one unauthenticated request materializes the whole `lemmas` table as result dicts (hundreds of MB transient heap) → memory-pressure/DoS and crash risk on the small shared-hosting deploy target; also violates the documented API contract (`limit must be <= 200` implies bounded). Classified HIGH (availability/crash).
- **Fix (this run):** validate `1 <= limit <= 200` (reject otherwise) on `/api/v1/search`; probe confirms `limit=-1` now 400s.

### 🟠 MEDIUM

#### BH-K3 — Same negative-`limit` gap on the history endpoints (report only)

- **Where:** [`app/history.py:37`](https://github.com/gasyoun/kosha/blob/main/app/history.py) and [`app/history.py:111`](https://github.com/gasyoun/kosha/blob/main/app/history.py) (`if limit > 200:` only) feeding `LIMIT ?` at lines 119/125 and the row fetch in `get_visitor_history`.
- **Bug/impact:** identical SQLite `LIMIT -1` semantics; unbounded read. Impact is far lower than BH-K2 — the history store is small and the whole router is mounted only when `KOSHA_HISTORY_ENABLED` is truthy (D10 gate, OFF for public v1) — hence MEDIUM. Report only per the auto-fix scope (HIGH only); same one-line bound as BH-K2 applies when history ships.

### 🟡 LOW

#### BH-K4 — `hash_ip` falls back to a hardcoded dev salt

- **Where:** [`app/identity.py:30`](https://github.com/gasyoun/kosha/blob/main/app/identity.py) — `os.getenv("HISTORY_IP_SALT", "kosha-dev-salt")`
- **Impact:** if history is ever enabled outside the deploy bundle, IP hashes become dictionary-reversible (constant, committed salt). The bundle path sets a host-local secret and tests pin it ([`tests/test_deploy_bundle.py:96`](https://github.com/gasyoun/kosha/blob/main/tests/test_deploy_bundle.py)), and history is OFF by default — residual risk is a manual-enable footgun. Suggest failing closed (raise) when history is enabled without a salt.

#### BH-K5 — Anon cookie issued without `secure=True`

- **Where:** [`app/identity.py:20-21`](https://github.com/gasyoun/kosha/blob/main/app/identity.py), also [`app/history.py:180`](https://github.com/gasyoun/kosha/blob/main/app/history.py)
- **Impact:** `kosha_anon_id` can travel over plain HTTP if any non-TLS vhost serves the app. Harmless behind the prod TLS front; one-flag hardening when convenient.

#### BH-K6 — Magic-link token logged by the e-mail stub

- **Where:** [`app/history.py:140`](https://github.com/gasyoun/kosha/blob/main/app/history.py) — `print(... would email {email}: ...token={token})`
- **Impact:** until the real provider swap (@DECIDE open), valid 30-min login tokens + raw e-mails land in stdout logs. Dev-scaffolding only (send path is a stub), but the print should go when the provider lands.

#### BH-K7 — Stale union count survives as a comment in `tests/conftest.py`

- **Where:** [`tests/conftest.py:36`](https://github.com/gasyoun/kosha/blob/main/tests/conftest.py) — the `FULL_DATA_MODULES` preamble comment still cites the pre-H4075 union figure (the stale one, canon+3 — exact string see the file; quoting it here trips the H5421 gate).
- **Impact:** the H4075 refresh (stale → 323,422) missed this comment; the H5421 drift gate covers `.md`/`.txt`/`.tex` only, so `.py` comments are a blind spot. Misleads humans pinning future test counts. One-word fix; report only this run.

---

## What verified green (checked, no finding)

- **SQL construction:** every query parameterized; the single f-string `WHERE` ([`app/main.py:471`](https://github.com/gasyoun/kosha/blob/main/app/main.py)) is built from a closed whitelist of literals, `ORDER BY` is a fixed string with parameterized keys.
- **Rendered-HTML boundary:** nh3 allowlist ([`src/kosha/api/sanitize.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/sanitize.py)) applied at serialization (`render_sanitized`), CSS value/class/colspan filters present; `?raw=1` passthrough is documented and deliberate.
- **Backup transport:** FTPS with mandatory `AUTH TLS` + `prot_p()`, temp-name + digest-verify + atomic rename, fail-closed on missing digest ([`src/kosha/backup/transport.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/backup/transport.py)).
- **Secrets:** no committed credentials; `.env`/`.env.deploy` exist only as examples; deploy recipe carries `production-only-secret` as a *scope label* (fill-on-host), not a literal.
- **Query facade:** read-only enforced post-setup (`PRAGMA query_only`), stable-alias allowlist for ATTACH, hard guard refuses history on the dictionary path ([`src/kosha/query/connection.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/query/connection.py)).
- **UI layer:** no `innerHTML`/`eval`/`document.write` in `ui/src/lib`; CORS contract keeps `allow_credentials=False` under the wildcard default.
- **No shell/exec sinks** (`os.system`, `eval`, `shell=True`) in the hunted code surfaces; swallowed exceptions in `app/` are deliberate degrade-graceful sites (segmenter, ls-hydrate) with comments, not error-hiding.

## Phase 3 — auto-fix record (MG ruling 26-09-2026)

- BH-K1 and BH-K2 are CODE HIGHs → fixed in this run on a separate worktree off `origin/main` (branch `bughunt/kosha-fix-2026-10-13`), minimal diffs, verified by live re-probe + the repo's fixture-tier tests. Fix attempt counter: **2 of 3 used, 0 failures, 0 reverts**.
- No HIGH credential/infra findings → no GTD @DO row minted this night.
- BH-K3/K4/K5/K6/K7: report only, no code edits (per scope).
