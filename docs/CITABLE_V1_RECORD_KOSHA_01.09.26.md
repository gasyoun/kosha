# Citable v1 — the record, and what W0/W1 actually shipped

_Created: 01-09-2026 · Last updated: 01-09-2026_

[H3788](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3788-Opus_kosha_kosha-2026-2027-w2-citable-v1_31.08.26.md)
asked for two things before any W2 work: establish which of W0 and W1 have
actually shipped and say so explicitly, then show that a citable release exists
with its DOI and manifest — or name the units that block it.

**Verdict: a citable release exists.** `v0.117.1`, archived 01-09-2026, version
DOI [`10.5281/zenodo.22231444`](https://doi.org/10.5281/zenodo.22231444), under
concept DOI [`10.5281/zenodo.21965599`](https://doi.org/10.5281/zenodo.21965599).
Neither W0 nor W1 blocks it. What was missing was not the release but the
**record and the policy** — plus four defects in the citability surface, all
repaired in this pass.

## 1. W0 — stabilization and truth reset: technically passed

Measured against the freeze-exit checklist in
[VERIFICATION_KOSHA_ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_ARCHITECTURE.md).

| Criterion | State | Evidence |
|---|---|---|
| H1943, H1944, H1945 merged | ✅ | all three archived |
| Retrospective review has no open P0/P1 | ✅ | H2681 retrospective; recorded in [.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md) |
| Manifest/README/state truth (#198, #201) | ✅ | both issues CLOSED |
| Full default DAG contains every declared stage (#210) | ✅ | issue CLOSED 2026-07-31 |
| Required Python/UI CI protected and green | ✅ | `main` protected 31-07-2026, `enforce_admins: true`, both workflows required by name |
| Dependency auto-merge cannot bypass those checks | ✅ | `dependabot-auto-merge.yml` gated on `workflow_run` success + queued auto-merge |

The roadmap's `**State:** ready` for W0 is what a reader stumbles on: it reads
as "ready to start" while the checklist behind it is satisfied. That wording is
the only W0 discrepancy found.

## 2. W1 — public-product readiness: every agent-measurable gate passes

From [MG_LIVE_SMOKE_PACKET_W1E.md](https://github.com/gasyoun/kosha/blob/main/docs/MG_LIVE_SMOKE_PACKET_W1E.md).

| Gate | State | Evidence |
|---|---|---|
| Production deploy | ✅ | `.92`, `kosha.service`, first promote 08-08-2026 |
| Branded API `samskrtam.ru` | ✅ | 13-08-2026 (H2646) — `/health`, `/ready`, `/metrics`, `/api/v1`, `/w/` all 200 |
| Lighthouse mobile ≥ 90 | ✅ | 100 / 100 / 100 on three real `/w/` URLs |
| Gītā walkthrough | ✅ | 13/13 tokens of 1.1 resolve via SSR |
| Pages `w/` pack hrefs | ✅ | 13-08-2026 (H2665), 2,324 committed pages |
| Citation archives mounted | ✅ | 14-08-2026 (H2671), `/ready` `citation_archives: ok`, 692,403 senses |
| Rollback confirmation | ✅ | 14-08-2026 (H2672), full Part IV restore then re-promote |
| §9 branded-complete tick | ⬜ **human** | an agent must not mark Wave 1 complete |

**W1 does not block W2.** The single open item is a human signature, and the
packet itself records that the W2 unlock condition — green live API smoke — was
met on 08-08-2026. `.ai_state.md` already states the box "is **not** a legal
signature and **not** a stop for further engineering."

## 3. W2 — citable v1: the four components

| Component | State | Evidence |
|---|---|---|
| Immutable sense archives + checksums | ✅ shipped | H2346, [PR #342](https://github.com/gasyoun/kosha/pull/342); release gate in required CI since H2870 |
| Public dataset API | ✅ shipped | H2347, `GET /api/v1/datasets`, `count=84` verified live |
| Release observability | ✅ shipped | H2348, `X-Request-ID` + `GET /metrics` |
| DOI + citation metadata | ✅ **shipped, was undocumented** | concept + 21 version DOIs; see below |
| Frozen dataset manifest | ✅ **built this pass** | [data/manifest/frozen/](https://github.com/gasyoun/kosha/tree/main/data/manifest/frozen) |
| Stated versioning policy | ✅ **written this pass** | [VERSIONING_AND_CITATION_POLICY_KOSHA.md](https://github.com/gasyoun/kosha/blob/main/docs/VERSIONING_AND_CITATION_POLICY_KOSHA.md) |

### The DOI series, as verified against the Zenodo API on 01-09-2026

21 archived deposits under concept `10.5281/zenodo.21965599`. The most recent,
and the ones a citer is most likely to want:

| Version | Version DOI | Archived |
|---|---|---|
| `v0.117.1` | `10.5281/zenodo.22231444` | 2026-09-01 |
| `v0.117.0` | `10.5281/zenodo.22182129` | 2026-08-31 |
| `v0.116.1` | `10.5281/zenodo.22177975` | 2026-08-30 |
| `v0.116.0` | `10.5281/zenodo.22132415` | 2026-08-27 (**supersedes** `…22131151`, §4.1) |
| `v0.115.3` | `10.5281/zenodo.22106970` | 2026-08-26 |
| `data-v0.5.0` | `10.5281/zenodo.22105641` | 2026-08-26 |
| `data-v0.4.0` | `10.5281/zenodo.22102090` | 2026-08-25 |
| `v0.110.13` | `10.5281/zenodo.21965600` | 2026-08-16 (first archived) |

`data-v0.1.0` … `data-v0.3.0` predate the webhook and have no DOI.

## 4. Defects found and repaired

### 4.1 A released tag was moved, and Zenodo archived both states

`v0.116.0` has **two** version DOIs — `10.5281/zenodo.22131151` (15:43Z,
187,386,121 B) and `10.5281/zenodo.22132415` (17:37Z, 187,389,165 B), both
titled `v0.116.0`, both pointing at the same tree URL. Zenodo deposits cannot be
withdrawn, so the ambiguity is permanent. Cite `…22132415`, which matches the
tag as it stands.

**Not repairable — recorded.** The rule that prevents a recurrence is §3 of the
versioning policy: a released tag is never moved; a wrong release is superseded
by the next patch version.

### 4.2 Release bytes depended on the uploader's checkout (28 rows)

`.gitattributes` pins `*.tsv text eol=lf`, but git does not renormalize files
already present in a working tree when that rule lands. The canonical checkout
still held CRLF; `git status` stayed clean; a manifest `refresh` run there
recorded CRLF sizes, and the release assets uploaded from there carry them.

Proven on `kosha-lemma-frequency`: canonical LF 4,827,466 B, CRLF 4,910,744 B,
delta 83,278 = exactly the line count, identical content
(`sha256` of the LF-normalised bytes matches from both checkouts:
`c07f6a0229067267d2bf18ba79f43f5081f05fef8875a352cc18f5e157ceccef`). The
published `data-v0.5.0` asset is 4,910,744 B — the CRLF variant.

**28 rows** carried an inflated `size_bytes`, spanning `data-v0.2.0`,
`data-v0.3.0` and `data-v0.5.0`. All repaired to canonical sizes. The freezer
now hashes LF-canonically and **refuses to cut a release from a CRLF working
tree**; the writers now open with `newline="\n"`.

### 4.3 The manifest's own pointers were stale

- `generated` said `2026-08-16` while the file had been edited through
  01-09-2026 — `update_manifest.py` deliberately no-ops that bump. Now
  `2026-09-01`.
- `interim_release` still named `data-v0.3.0` two releases after it was
  superseded, and `note_for_agents` directs every agent to download public-tier
  assets from exactly that URL. Now `data-v0.5.0`.

### 4.4 Sibling repos never resolved from a worktree — masking a worse hazard

`update_manifest.py` derived the checkout root as `REPO.parent`, correct only in
`…/GitHub/kosha`. Inside a linked worktree every `csl-orig` /
`SanskritLexicography` / `csl-apidev` row silently resolved to nothing and was
skipped, indistinguishably from "gitignored, leave alone". Fixed by
[scripts/manifest_paths.py](https://github.com/gasyoun/kosha/blob/main/scripts/manifest_paths.py),
which probes candidate roots for a known sibling.

Fixing it immediately exposed the hazard it had been masking: with siblings
resolving, `refresh` wanted to rewrite `pwg-tm-canonical-v1` from 101,677,729 B
to **17,668 B** and `pwg-de-edition-v1` from 46,382,247 B to **33,951 B** —
because those release directories ship their payload outside git and the local
clone holds only the 8 metadata files. Applying that would have destroyed a
curated fact with no trace it was ever known.

`refresh` now **refuses any drop below 50 % of the recorded size**, naming the
rows and requiring `--allow-shrink`. The floor cleanly separates the two hazards
(0.02 % and 0.07 %) from every legitimate update seen in the same run (smallest
96.6 %).

## 5. Named residuals

1. **Cut `data-v0.6.0` carrying a frozen manifest as its `datasets.json`.**
   Blocked on two of the five `in_release: unreleased` rows —
   `pwg-sense-attestation-window` and `kosha-mastery-schedule` — which have
   neither a `release_asset` nor a `data_statement`. Both are needed before a
   publish-safety check can pass.
2. **Renormalize the canonical checkout** (`git add --renormalize .` in
   `…/GitHub/kosha`) so it stops being a CRLF source for future uploads. Not
   done here: it is a working-tree operation on the guarded main checkout, and
   this pass ran from a worktree.
3. **Wire `freeze_release_manifest.py check` into the release gate**, so a data
   release cannot ship a stale frozen manifest.
4. **§9 branded-complete tick** in the W1E packet — human, unchanged.

## 6. How the numbers here were produced

- Zenodo series: `GET https://zenodo.org/api/records?q=conceptdoi:"10.5281/zenodo.21965599"&all_versions=true`
  (unauthenticated page size caps at 25; 21 deposits returned).
- Release/tag facts: `gh release list`, `gh api repos/gasyoun/kosha/git/ref/tags/v0.116.0`.
- CRLF proof: byte counts plus `sha256` of raw and LF-normalised forms of
  `data/frequency/lemma_frequency.tsv` in both the canonical checkout and a
  fresh worktree.
- Manifest repairs: `python scripts/update_manifest.py refresh` run from an
  LF-clean worktree, `--dry-run` first.
- Frozen manifests verified with
  `python scripts/freeze_release_manifest.py check --frozen <path>` — all four
  report OK.

_Dr. Mārcis Gasūns_
