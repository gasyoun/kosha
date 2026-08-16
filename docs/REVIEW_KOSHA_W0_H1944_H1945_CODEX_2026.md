# Codex retrospective review — kosha W0 H1944 and H1945

_Created: 14-08-2026 · Review date: 14-08-2026 · Reviewer: Codex Sol (`gpt-5.6-sol`)_

This is the written review required by H2681. It compares the shipped work in
[H1944 / PR #215](https://github.com/gasyoun/kosha/pull/215) and
[H1945 / PR #224](https://github.com/gasyoun/kosha/pull/224) with their
archived handoffs, and compares the merged H1944 lane with the independent,
unmerged implementation at
[`4688ad3a3`](https://github.com/gasyoun/kosha/commit/4688ad3a3fb90aaf9a042010774ac8c8e4d99c04).

## Verdict

**PASS for the W0 retrospective gate: no open P0 or P1 finding.** Both merged
PRs materially satisfy their handoffs, their historical required checks were
green, and the current focused W0 suite passes (**188 passed, 30 skipped**).
The earlier process overrides are now discharged by this review; they were not
evidence that the review had already happened.

One open **P2 contract conflict** remains: kosha's strict `/dicts/*` Salt faces
return a top-level `kosha` extension even though the normative Salt profile
§9 permits only the additive `csl` object and says no other structural
divergence is allowed. This is not a security, data-loss, or availability
defect, so it does not block the W0 no-P0/P1 criterion. It is routed to
[H2768 (Codex) — Resolve kosha extension on strict Salt compatibility faces](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2768-Codex_kosha_salt-face-kosha-extension-contract_14.08.26.md).

This verdict closes the technical W0 review debt. It does **not** claim that
Wave 1, deployment, DOI, or later roadmap work is complete.

## Method and evidence

The review used the archived
[H1944](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1944-Opus_kosha_architecture-roadmap-w0b-reproducible-substrate_30.07.26.md)
and
[H1945](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1945-Opus_kosha_architecture-roadmap-w0c-contract-trust-boundaries_30.07.26.md)
bodies; the merged trees and PR descriptions; historical PR checks; the
independent H1944 branch; the current Salt profile; and the current branch
protection readback. No product code was changed.

Historical checks were green on both PRs:

| PR | Fixture build + tests | UI test + build | Changelog guard |
|---|---:|---:|---:|
| [#215](https://github.com/gasyoun/kosha/pull/215) | pass | pass | pass |
| [#224](https://github.com/gasyoun/kosha/pull/224) | pass | pass | pass |

Current focused verification:

```text
python -m pytest -q -p no:cacheprovider \
  tests/test_build_dag.py tests/test_dependency_lock.py \
  tests/test_backup_transport.py tests/test_salt_profile.py \
  tests/test_contract_parity.py tests/test_sanitizer.py \
  tests/test_citation_archive.py tests/test_history_disabled_by_default.py

188 passed, 30 skipped, 3 deprecation warnings in 6.89s
```

The warnings cover the deliberately supported deprecated
`KOSHA_RELEASES_DIR` alias; they are not failures.

## H1944 — handoff versus merged PR #215

| Handoff obligation | Class | Review and adjudication |
|---|---|---|
| Installable package, compatibility entry points, committed dependency lock | **Equivalent with resolved conflict** | `pyproject.toml`, `src/kosha/`, shims and a lock landed. The first lock contradicted its own declared floors; [PR #218](https://github.com/gasyoun/kosha/pull/218) made generation contradiction-fatal, added an independent audit, and regenerated it. Keep the merged design plus #218. |
| Typed settings; deprecated `DATABASE_PATH`; conflicts fail | **Equivalent** | The requested stores and flags landed; alias conflicts fail explicitly. No contrary evidence found. |
| History/auth/stats absent by default | **Equivalent** | Routes are absent from OpenAPI and return 404; search does not mint a visitor cookie or write history while disabled. |
| Declarative ten-stage default DAG | **Equivalent** | The declared order and prerequisite closure replace the incomplete `if` dispatch. A no-flag fixture build executes all declared stages and #210 was closed only after that proof. |
| Locks, prerequisite checks, postconditions, temp target, atomic promotion, immutable releases | **Equivalent** | These controls landed with `foreign_key_check` before promotion and release rejection of `latest`. The later lock audit closes the one contradiction missed by the original gate. |
| Compact public fixture, clean build twice | **Equivalent** | The merged lane's small hand-authored fixture is preferable to the rival lane's much larger verbatim feed slices: it meets the public/no-restricted-bytes fence with less provenance and redistribution risk. |
| Required Python/UI CI and safe dependency auto-merge | **Equivalent after external control; documentation caveat** | Both checks passed. At merge, `main` was not protected, so the guarantee was incomplete; branch protection was enabled later under [#223](https://github.com/gasyoun/kosha/issues/223) with both contexts and `enforce_admins: true`. The workflow itself triggers once per completed workflow and checks only that triggering run, so its prose claiming it independently waits for *both* is too strong. Branch protection is the real two-check barrier. Keep the current behavior; treat this memo as the precision correction. |
| Encrypted, temporary-name, digest-verified, atomic backup; no upload | **Equivalent with resolved conflict** | FTPS and fail-closed promotion landed. The first `HASH` parser assumed the digest was the last token and rejected HASH-only servers; #218 fixed it with reply-shape tests. The rival's size-only fallback conflicts with the handoff's explicit fail-closed rule, so the merged design wins. |
| Gates and non-goals | **Equivalent** | Required historical checks passed; no Salt migration, deploy, DOI, restricted fixture, or canonical asset rebuild landed in #215. |
| Serial dependency/review discipline | **Conflicting process history** | H1944 began after H1943 merged but before a visible Codex review; H1945 likewise ran after an explicit human override of the missing review. Adjudication: do not pretend the dependency was met at the time; this retrospective supplies the missing review now. No code correction follows from the process defect. |

## Independent H1944 lane — keep-best comparison

The unmerged `origin/h1944-w0b-reproducible-substrate` branch is one commit
from the same pre-H1944 base and is not a patch on #215. Its architecture is
mostly **equivalent**, but its tree is not safely mergeable over the shipped
line: it replaces the DAG, lock, fixture, transport, and test implementations
wholesale and predates H1945.

| Rival contribution | Class | Adjudication |
|---|---|---|
| Separate stage registry, runner, lock, settings, CI, and FTPS implementation | **Equivalent** | Keep merged #215: it is shipped, subsequently exercised, and is the base H1945 hardened. Wholesale replacement has no demonstrated benefit proportional to its integration risk. |
| Direct fixes for legacy loader paths captured as import-time defaults | **Net-new** | Valuable diagnosis. The merged DAG already passes inflection paths explicitly and temporarily rebinds layer-loader defaults with restoration, so its source lock names the bytes actually read. The rival's direct cleanup may be reconsidered separately, but it is not an open W0 correctness defect. |
| Correct parsing of `HASH` replies | **Net-new, salvaged** | This found a real merged defect. The minimal fix and tests shipped in #218; do not merge the rival transport. |
| Large fixture sliced from live feeds | **Conflicting** | Reject in favor of the merged hand-authored fixture. The handoff asked for compact public fixtures and prohibited restricted fixtures; copying upstream feed bytes expands rights/provenance review without improving the contract proof needed in CI. |
| Size-only fallback when the server cannot prove a digest | **Conflicting** | Reject. H1944 explicitly required the selected transport to fail closed when it cannot prove a remote digest. |
| Higher local pass count | **Not directly comparable** | The rival reported 482 passed / 2 skipped against a different fixture and environment; #215 reported 272 passed / 164 skipped on its hermetic tier. Compare contractual coverage and reproducibility, not raw test totals. |

## H1945 — handoff versus merged PR #224

| Handoff obligation | Class | Review and adjudication |
|---|---|---|
| Typed Salt entry/envelope/error models | **Equivalent; P2 resolved 16-08-2026** | Models forbid undeclared fields and preserve Salt names. The handoff-mandated `kosha` namespace remains on `/api/v1`; H2768 added the strict `/dicts/*` §9 projection. |
| One repository/query and serializer boundary | **Equivalent** | API, Salt faces, static cards and SSR delegate through the same repository/serializer. Structural and output parity tests replace the previous copied dictionaries. |
| `/api/v1` Salt-shaped migration and namespacing | **Equivalent** | The envelope stayed stable; Salt fields are top-level and kosha additions moved under `kosha`. The breaking change was documented and in-repo clients were migrated. |
| `/dicts/*` parity as a contract | **Equivalent; strict projection resolved by H2768** | One serializer remains authoritative; actual wire keys are checked against the profile-derived v0.1.0 fixture and shared Salt fields are compared with `/api/v1`. |
| One documented error shape per contract | **Equivalent** | `/api/v1` errors normalize to the structured object; Salt faces retain the bare-string profile form. Starlette 404/405 handling is covered at the base exception class. |
| Allowlist sanitizer plus adversarial and golden gates | **Equivalent** | Active tags, handlers, unsafe URLs and CSS are rejected; legitimate Cologne display text/tags are protected, with `<pb>` as the one documented structural removal. Both live and archived sense paths cross the boundary. |
| Archive path/base/metadata/checksum/asset URL and current/historical resolution | **Equivalent** | The archive validator distinguishes absent local archives from corrupt declared archives, checks SQLite readability and metadata hashes, and the route tests cover live and pinned historical senses. The `archive_dir`/`KOSHA_RELEASES_DIR` contradiction found during implementation was resolved conflict-fatally. |
| History/auth/stats remain absent | **Identical** | H1945 preserved and extended H1944's default-off proof, including non-collection. |
| Required gates and non-goals | **Equivalent** | Historical checks and the present focused suite are green. No deploy, DOI, physical DB split, history implementation, W3 research, or restricted-byte publication landed. |
| Freeze-exit verdict | **Equivalent, now superseded by this review** | #224 correctly recorded that the review was missing and did not claim W0 exit. This document supplies that review and finds no open P0/P1. |

## Findings ledger

| Severity | State | Finding | Disposition |
|---|---|---|---|
| P0 | none | — | — |
| P1 | none open | The original H1944 lock/HASH defects and absent branch protection were material, but all were corrected before this review (#218, #223). | Resolved; verified by current tests and protection readback. |
| P2 | resolved 16-08-2026 | `/dicts/*` emitted top-level `kosha` although the normative profile permits only additive `csl`. | H2768 (Codex) — Resolve kosha extension on strict Salt compatibility faces; strict-face decision and regression merged in this lane. |
| P3 | documented | Dependabot workflow prose says it independently waits for both CI workflows; code observes only the triggering successful run. | Branch protection supplies the actual two-check barrier. No W0 code change required. |

## Final adjudication

Keep the merged H1944 and H1945 lines, including the focused corrections in
#218 and the branch-protection control from #223. Do not merge or cherry-pick
the rival H1944 implementation wholesale. Preserve its two useful discoveries:
the `HASH` defect is already fixed, and its loader-path observation is recorded
here for future simplification. H2768 resolved the sole P2 Salt/profile conflict
with a strict face projection. With no open P0/P1, the retrospective-review
criterion passes.

_Dr. Mārcis Gasūns_
