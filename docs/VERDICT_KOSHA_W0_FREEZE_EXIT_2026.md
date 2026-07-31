# W0 freeze-exit verdict — kosha, 31-07-2026

_Created: 31-07-2026 · Last updated: 31-07-2026_

Recorded by [H1945](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1945-Opus_kosha_architecture-roadmap-w0c-contract-trust-boundaries_30.07.26.md)
(W0C, item 10), executed by Opus 5 1M (`claude-opus-5[1m]`). The checklist is
[VERIFICATION_KOSHA_ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_ARCHITECTURE.md)
§ Freeze-exit checklist. Each row below was checked against the repository as
it stands, not against what a previous handoff reported.

## Verdict

**W0 does not exit yet. Two of thirteen criteria fail, neither of them a W0C
deliverable.** All ten H1945 items are done and their gates are green; what
blocks the exit is (a) an enforcement control an earlier handoff's
documentation asserted but never established, and (b) the retrospective Codex
review, which has not happened for either H1944 or H1945.

W1 and W3 therefore stay gated, as the handoff requires.

## The checklist

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | H1943, H1944, H1945 merged | ⚠️ pending | H1943 · H1944 merged ([#215](https://github.com/gasyoun/kosha/pull/215)); H1945 is this PR |
| 2 | Retrospective Codex review has no open P0/P1 | ❌ **FAIL** | No Codex review exists for H1944 — [#215](https://github.com/gasyoun/kosha/pull/215) carries zero reviews and zero comments. H1945's dependency gate was cleared by explicit human authorization, not by a review |
| 3 | Fixture clean build succeeds from zero | ✅ | `--plan` lists all 10 stages; two consecutive builds from a removed target, `10 stage(s), 0 skipped` |
| 4 | Required Python/UI CI is protected and green | ❌ **FAIL** | Workflows run and are green, but `main` is **unprotected**: `branches/main` → `"protected": false`, `rulesets` → `[]`. No check is *required*; a red run does not block a merge. See [#223](https://github.com/gasyoun/kosha/issues/223) |
| 5 | Dependency auto-merge cannot bypass those checks | ⚠️ partial | `dependabot-auto-merge.yml`'s `workflow_run`+`success` condition holds and is real; the second barrier (queued auto-merge waiting on branch protection) waits on nothing while #4 fails |
| 6 | Full default DAG contains every declared stage | ✅ | `python scripts/build_db.py --profile fixture --plan` |
| 7 | [#210](https://github.com/gasyoun/kosha/issues/210) closed only after a fresh no-flag build proved every stage ran | ✅ | Closed by H1944; re-verified here by a from-zero build |
| 8 | API, Salt facade, static cards and SSR share one serializer and pass parity | ✅ | `tests/test_contract_parity.py`, 12 tests — including static-card ≡ API equality across four output schemes, and a structural check that no copy of the serializer survives |
| 9 | Sanitizer adversarial suite passes | ✅ | `tests/test_sanitizer.py`, 110 tests — active content, event handlers, `javascript:`/`data:`/`vbscript:`/`file:` URLs, CSS `url()`/`expression()`, attribute injection via a source `title`, idempotence, plus a golden-corpus non-destruction gate |
| 10 | History/auth/stats endpoints 404 by default | ✅ | `tests/test_history_disabled_by_default.py` — routes absent from the app *and* the OpenAPI schema; extended here to prove no cookie is minted and no history store is written while serving a search |
| 11 | Current and historical citation smoke tests pass | ✅ | `tests/test_citation_archive.py`, 24 tests — live resolution, archived resolution against a mounted release, honest miss with the asset URL, checksum/metadata validation |
| 12 | No known deployment-blocking configuration contradiction remains | ✅ | The one found was fixed: `archive_dir` (`data/archive`) vs `KOSHA_RELEASES_DIR` (`data/releases`) — two names for one mount, defaulting to different directories. Unified; a contradicting pair is now a hard error |
| 13 | Rights uncertainty is not a criterion | ✅ n/a | D18 — no rights question arose; the fixture pack is written for the fixture and carries none |

## The two failures, stated plainly

**#4 — the required-checks control does not exist.** W0B's own verification
document asserted "The protected `main` branch requires both status checks by
name". The API says otherwise, and has all along. This matters beyond the
checkbox: every claim of the form "CI enforces X" in the W0 documents inherits
its strength from this control, and that strength is currently zero. Enabling
protection is a repository-settings change, outside H1945's scope and outside
its guardrails, so it is reported rather than performed — a human decides
whether to enable it and with which required contexts.

**#2 — no Codex review has taken place.** The plan of record (D21) makes Codex
the retrospective reviewer of every merged handoff, and the W0 sequence gates
each handoff on the previous one's review carrying no unresolved P1. H1944 was
merged without one; H1945 was authorized to proceed regardless, by explicit
human instruction, which is a legitimate override of a process gate but is not
a substitute for the review itself. Both reviews remain owed before W0 exits.

## What W0C shipped

All ten H1945 items, with their gates:

1. Canonical Pydantic Salt entry/envelope/error models — `src/kosha/api/models.py`.
2. One repository query layer and one serializer — `repository.py`, `serializer.py`.
3. `/api/v1` migrated to Salt entries, kosha fields namespaced, envelope kept — documented in [CONTRACT_KOSHA_API_V1_SALT_BREAKING_CHANGE.md](https://github.com/gasyoun/kosha/blob/main/docs/CONTRACT_KOSHA_API_V1_SALT_BREAKING_CHANGE.md).
4. `/dicts/*` parity as a contract test rather than a second serializer.
5. FastAPI errors normalized to the documented top-level object.
6. Rendering wrapped in an nh3 allowlist, with the adversarial suite and the golden-corpus protection gate.
7. Archive path/public base/metadata/checksum/asset-URL validation and both resolution paths.
8. History/auth/stats proved absent by default, and proved non-collecting.
9. Salt, parity, sanitizer, citation, Python and UI gates run: **467 passed, 164 skipped** (up from 285 passed); UI **42 passed** + `vite build` clean.
10. This verdict.

Three defects were found by the new gates rather than by inspection, and fixed
in the same pass: `/api/v1/sense` bypassed the sanitizer on both branches;
Starlette's routing 404/405 escaped error normalization; and the static-card
builder's copy of the serializer had already drifted from the API's.

---

_Dr. Mārcis Gasūns_
