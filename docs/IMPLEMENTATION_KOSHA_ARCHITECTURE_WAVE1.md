# Kosha W0 implementation sequence

_Created: 30-07-2026_

This sequence implements W0 from the
[plan of record](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_ARCHITECTURE_ROADMAP_2026_2027.md).
The handoffs are serial and Claude Code only.

## H1943 — governance and integrity

**Executor:** Sonnet 5 (`claude-sonnet-5`).

1. Re-audit `origin/main`, open issues, release metadata, manifest counts, and
   all status-bearing documents.
2. Establish `docs/ROADMAP.md` as the sole live roadmap, derived from
   [the twelve-month roadmap](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026_2027.md).
3. Expand the root architecture index to point at the integrated platform
   contract without deleting historical decisions.
4. Mark completed specialist plans immutable/superseded in place; do not move
   files or break blob links.
5. Reduce `.ai_state.md` to the canonical sections and current work.
6. Correct README/manifest count drift and every #198 false Bhagavadgītā mirror;
   regenerate only outputs whose committed builder owns them.
7. Add truth tests for manifest counts, version claims, active-queue completed
   markers, and plan banners.
8. Run the full Python/UI gates, merge only if green, then close #198 and #201
   with exact merged evidence.

Non-goals: packaging, API changes, build DAG, sanitizer, deployment.

## H1944 — reproducible substrate

**Executor:** Opus 4.8 (`claude-opus-4-8`). **Dependency:** H1943 merged and
Codex review has no unresolved P1.

1. Add `pyproject.toml`, installable `src/kosha/` package skeleton, and committed
   lock; preserve working entry points.
2. Add typed settings and the deprecated `DATABASE_PATH` alias; feature-gate
   history/auth/stats off by default.
3. Replace `build_db.py` conditional dispatch with a declarative stage registry
   and dependency expansion.
4. Add immutable build-lock schema, prerequisite checks, postconditions,
   temporary build targets, and atomic promotion.
5. Add a compact committed fixture DB/source pack that exercises every core
   contract without restricted bytes.
6. Add required Python and UI CI; make dependency auto-merge conditional on
   protected required checks.
7. Replace plaintext FTP code with encrypted, atomic, digest-verifying transport
   and dry-run tests. Do not upload.
8. Run fixture clean-build twice, full tests, UI build, and failure-path tests;
   merge only if green.
9. Close [integrity issue #210](https://github.com/gasyoun/kosha/issues/210)
   only after a fresh no-flag fixture build proves every declared stage ran and
   stale prerequisites cannot be reused silently.

Non-goals: physical DB split, Salt payload migration, production deployment.

## H1945 — contract and trust boundaries

**Executor:** Opus 4.8 (`claude-opus-4-8`). **Dependency:** H1944 merged and
Codex review has no unresolved P1.

1. Implement canonical Pydantic Salt entry/envelope/error models.
2. Extract the shared entry query and serializer used by `/api/v1`, `/dicts/*`,
   static cards, and SSR.
3. Migrate `/api/v1` to Salt-compatible entries with kosha fields namespaced
   under `kosha`; normalize top-level errors.
4. Wrap renderer output in an explicit sanitization policy and add adversarial
   fixtures for text, attributes, tags, URLs, and active content.
5. Add archive settings, release metadata/checksum validation, and current plus
   historical citation smoke tests.
6. Prove history routes are absent by default.
7. Run Salt parity, static/API/SSR parity, sanitizer, citation, Python, and UI
   gates; merge only if green.

Non-goals: production deployment, DOI mint, history implementation, W3 research.

## Codex reviews

After each merge Codex:

1. reviews the merged diff and checks the handoff acceptance evidence;
2. assigns P0–P3 findings;
3. releases the next handoff only when no P0/P1 remains;
4. routes corrections exclusively to a new Claude Code handoff.

---

_Dr. Mārcis Gasūns_
