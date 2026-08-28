# kosha OxAlpha 30-day risk-ranked code review — evidence report

_Created: 26-08-2026 · Last updated: 26-08-2026_

Executor: H3549 (OxAlpha, `opencode/z-ai/glm-5.3-flash`). Fixed window:
**26-07-2026 through 25-08-2026** (merge dates, UTC). Method: bounded risk
selector (executable code + critical-path exposure outranks churn), then two
**independent** passes per retained slice — a Standards pass (repository rules
in CLAUDE.md/AGENTS.md + named smells) and a Spec pass (ruled evidence chain:
PR body → issue → handoff/plan → matching doc → no spec available). Plan of
record: [PLAN_KOSHA_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.md).

## 1. Reviewer-session verification gates (own evidence)

| Gate | Command | Result |
|---|---|---|
| Fixture build #1 | `python scripts/build_db.py --profile fixture` | 9 stages promoted, 1 skipped |
| Fixture build #2 (idempotence) | same, second run | 9 stages promoted, identical |
| Full tests, no cache | `pytest -q -p no:cacheprovider` | **598 passed, 177 skipped** |
| Surface registry | `python scripts/validate_surfaces.py` | OK: 28 surfaces |
| Whitespace gate | `git diff --check` | clean |

Adapter bootstrap PR (Wave 0): [gasyoun/kosha#463](https://github.com/gasyoun/kosha/pull/463)
— merged 26-08-2026, all checks green (`Fixture build + tests`, `vitest + vite
build`, `Changelog — no duplicated entries`).

## 2. Window census and exclusions

~100 PRs merged in the window. Exclusion classes (generated/vendor/data-only
churn, or no executable-code delta):

| Class | Examples | Reason |
|---|---|---|
| Generated bulk publishes | #232, #387, #402, #434, #439, #452 | 23 k–233 k committed static/pack files; behavior governed by the earlier wave PRs that built them |
| Release cuts / CITATION sync | #202, #217, #219, #225, #230-ish `chore(release)` series | metadata only |
| Docs-only | #206, #208, #211, #213, #230, #233, #399, #400, #421, #429, #446 | no executable delta |
| Manifest/data registrations | #203, #204, #237, #243, #396, #397, #403, #408–#413, #426, #428, #448–#451, #459 | data-only churn; rights posture unchanged by the diff |
| Dependency bumps | #205, #238, #240 | vendor-managed, auto-merge gated |
| Process/docs waves | #222, #221, #242, #246, #247, #249, #425, #441, #445, #454–#458 | CI-line/lint/regen only |

Ten executable-risk slices were retained (candidates pre-named by the
implementation plan; all ten validated in-window and executable — none
replaced).

## 3. Retained slices — ranking, SHAs, verdicts

Risk rank: storage/query blast radius → citation durability → deploy path →
repo-integrity tooling → restricted ingest/crawl → public SSR surface → ops
gates → CI config gates.

| # | PR (title) | Merged | base → head SHA | Executable paths reviewed | Standards | Spec |
|---|---|---|---|---|---|---|
| 1 | [#252](https://github.com/gasyoun/kosha/pull/252) W1A multi-DB storage facade + query parity | 2026-08-07 | `d453dabb` → `5673a369` | `src/kosha/query/{connection,split,samples}.py`, `app/db.py`, `tests/conftest.py` | PASS (2 minor smells, F-252-1/-2) | PASS |
| 2 | [#342](https://github.com/gasyoun/kosha/pull/342) W2A immutable sense archives | 2026-08-08 | `5920aab5` → `b17f164a` | `src/kosha/api/archive.py`, `app/versions.py`, `scripts/validate_release_archives.py` | PASS (F-342-1 informational) | PASS |
| 3 | [#257](https://github.com/gasyoun/kosha/pull/257) W1D deploy bundle + rehearsal + rollback | 2026-08-08 | `8b751eb3` → `4b6ebf0b` | `src/kosha/deploy/bundle.py`, `scripts/{assemble_deploy_bundle,rehearse_deploy}.py` | PASS | PASS |
| 4 | [#245](https://github.com/gasyoun/kosha/pull/245) pre-push silent-revert guard + CRLF gate | 2026-08-06 | `cb2a5922` → `df3cbba2` | `.githooks/pre-push`, `scripts/pre_push_stale_base_check.py`, `scripts/eol_census.py` | PASS (F-245-1 wording) | PASS |
| 5 | [#364](https://github.com/gasyoun/kosha/pull/364) Heritage French glosses second reference | 2026-08-09 | `4ddf05fe` → `fccd3b00` | `scripts/defgen_heritage_{ref,delta,coverage,manifest_row}.py` (data files excluded per rules) | PASS | PASS |
| 6 | [#431](https://github.com/gasyoun/kosha/pull/431) akshara.ru bounded MT scrape pilot | 2026-08-24 | `88263db3` → `91c2e98e` | `scripts/akshara_pilot_{sample,crawl,parse}.py` | PASS (1 P2, F-431-1) | PASS |
| 7 | [#393](https://github.com/gasyoun/kosha/pull/393) EN/DE/RU language groups + pwg_ru/mw_ru join | 2026-08-13 | `8473f688` → `17545cc1` | `src/kosha/api/ru_join.py`, `app/word_page.py`, `app/main.py` | PASS (F-393-1 smell) | PASS |
| 8 | [#256](https://github.com/gasyoun/kosha/pull/256) W1C readiness checks | 2026-08-07 | `580a8bee` → `d3d55eaa` | `src/kosha/api/readiness.py`, `app/main.py`, `src/kosha/settings.py` | PASS | PASS |
| 9 | [#375](https://github.com/gasyoun/kosha/pull/375) W2C request correlation + low-cardinality metrics | 2026-08-13 | `4bfd51e3` → `a412796b` | `src/kosha/api/observability.py`, `app/main.py`, `scripts/rehearse_deploy.py` | PASS | PASS |
| 10 | [#254](https://github.com/gasyoun/kosha/pull/254) W1B generated-surface registry + CI | 2026-08-07 | `a59e6c41` → `201ca953` | `src/kosha/surfaces/registry.py`, `scripts/validate_surfaces.py`, `.github/workflows/python-ci.yml` | PASS | PASS |

## 4. Spec pass — quoted requirements (evidence chain: PR body, step 1)

Every retained slice had a PR body with acceptance criteria; no slice required
falling through to issue/handoff/plan, and **no slice is `no spec available`**.

- #252: "History is never mounted on this path … `app/db.get_db` and fixture connections go through the facade only" — verified: hard guard in `open_query_connection` raises if `history` alias appears; `test_history_file_is_never_attached` proves it with `KOSHA_HISTORY_ENABLED=1`.
- #342: "`write_archive` always freezes `release.json` … validator fails closed on missing metadata, checksum mismatch, bad public base, or unresolved sense" — verified in `validate_release_archives` (`require_metadata=True`, `require_versions=True`) and tamper tests.
- #257: "No production credentials, no SSH, no FTP upload" — verified: assemble copies only committed paths; env template keys labelled `production-only-secret`; `test_production_secret_env_keys_are_labelled`.
- #245: "Advisory: it warns, it does not block (`STALE_BASE_PUSH_STRICT=1` blocks …) … fails OPEN if the checker is missing" — verified: checker returns 1 only under STRICT env; hook guards `[ -f "$CHECKER" ]`; CRLF half blocks with `ALLOW_CRLF_BLOB_PUSH=1` escape.
- #364: "No gloss text is copied into kosha … `defgen_heritage_ref.py` refuses to score if any digest stops matching" — verified: `verify_join` → `sys.exit("REFUSE: …")` on mismatch; committed subset carries sha256 + word count only.
- #431: "HTML card pages only (allow-list regex), identified UA, ≥2 s throttle … raws + parsed corpus gitignored" — verified: `ALLOWED_URL` regex guard raises before fetch; `THROTTLE_S=2.0` + jitter; `.gitignore` additions.
- #393: "RU panels render Russian from a read-only join … `review_status` is never written" — verified: `join_ru` opens files read-only; `test_join_reads_fixture_only_and_does_not_write` pins file digests before/after.
- #256: "Never 500 for correctly disabled optional writables; history never looks 'ready' while unmounted" — verified: route maps only `ready → 200 / 503`; `history` check is `disabled` when flag off; fail-closed aggregate over required checks.
- #375: "Forbidden as labels: headword, query, path, request_id, IP, dataset_id" — verified: `FORBIDDEN_LABEL_KEYS` raises `LabelError` before recording; `test_metrics_omit_headword_and_forbidden_labels`; scrapes do not increment `kosha_ready_failures_total` (test-pinned).
- #254: "Dictionary-payload surfaces must consume `kosha.api.repository` + `kosha.api.serializer`" — verified: `DICTIONARY_KINDS` enforcement + `test_dictionary_payload_surfaces_share_query_serializer`.

## 5. Findings ledger

Every finding carries severity, location, failure mode, and repro/test. **Zero
P0/P1 defects were proven, therefore zero repair PRs are required** (plan
decision 10: only proven P0/P1 may be fixed). The P0/P1 set is empty; the
goal's "every proven P0/P1 has a regression-test PR merged or a named
stop-condition blocker" is satisfied vacuously and recorded here explicitly —
no fix was silently treated as complete because no fix lane was opened.

| ID | Severity | Location | Failure mode | Repro / test | Disposition |
|---|---|---|---|---|---|
| F-431-1 | **P2** | [scripts/akshara_pilot_sample.py](https://github.com/gasyoun/kosha/blob/main/scripts/akshara_pilot_sample.py) `MAIN_CHECKOUT`/`TM_PATH` (module level, `C:\Users\user\…` hardcoded) | `FileNotFoundError` at import on any non-Windows clone (macOS/Linux) — sampler cannot re-run off the original workstation | `python scripts/akshara_pilot_sample.py --selftest` off-Windows → import-time `FileNotFoundError` (verified by inspection of the merged diff; module-level `_first_existing`) | Not fixed: below P0/P1 bar; one-shot script, output committed, not wired into tests/CI. Fix path if ever re-run: env-var the two roots |
| F-252-1 | P3 smell | [src/kosha/query/connection.py](https://github.com/gasyoun/kosha/blob/main/src/kosha/query/connection.py) `_attach_ro` probe | Candidate DB probed via `sqlite3.connect` without `mode=ro` (RW handle); no write is ever issued, `query_only` lands before return | Code inspection | Accepted; documented tradeoff, no exploit path |
| F-252-2 | P3 smell | [src/kosha/query/split.py](https://github.com/gasyoun/kosha/blob/main/src/kosha/query/split.py) `_copy_tables` | `fetchall()` loads whole tables into memory — would not scale to the production monolith | Docstring scopes it "test / parity tool, not the production bulk move" | Accepted; out of production scope |
| F-342-1 | P3 informational | [app/versions.py](https://github.com/gasyoun/kosha/blob/main/app/versions.py) `write_archive` | Non-atomic sqlite→`release.json` window; crash between leaves metadata missing | Release gate then fails **closed** (desired direction) | Accepted |
| F-393-1 | P3 smell | [src/kosha/api/ru_join.py](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/ru_join.py) `unreviewed()` | Helper never called; `app/word_page.py` inlines the reviewed-set — drift risk only | `grep unreviewed` — zero call sites | Not fixed (cosmetic) |
| F-245-1 | P3 wording | [scripts/pre_push_stale_base_check.py](https://github.com/gasyoun/kosha/blob/main/scripts/pre_push_stale_base_check.py) `report()` | Prints "PUSH BLOCKED" even in WARN mode (push proceeds) | Manual run without `STALE_BASE_PUSH_STRICT` | Not fixed (cosmetic) |

## 6. Repository-rule compliance spot-checks (Standards pass anchors)

- Windows `sys.stdout.reconfigure(encoding="utf-8")` convention — present in every new script (#257, #342, #364, #431, #245) ✓
- Citation durability (R1/R5): #342 release gate rejects deployment-host public bases (`test_release_gate_fails_on_deployment_public_base` pins `samskrtam.ru` refusal) ✓
- Restricted-tier discipline: #364 stores digests not text; #431 keeps raws/parsed gitignored + RESTRICTED manifest row ✓
- Generated surfaces never committed: exclusions in §2; #254's registry now makes future violations a required-CI failure ✓
- `sacrebleu` eval-only dependency: #364 tests skip on ImportError in CI (473 passed / 218 skipped at merge) ✓

## 7. Repair lane statement

No P0/P1 was proven in this window, so no repair PRs exist. Fix-lane rules
(one minimal regression-tested PR per defect, fails-before/passes-after proof,
merge only green) remain armed in
[OXALPHA_STATUS_GATE_DESIGN_2026.md](https://github.com/gasyoun/kosha/blob/main/docs/OXALPHA_STATUS_GATE_DESIGN_2026.md)
for future windows.

---

_Dr. Mārcis Gasūns_
