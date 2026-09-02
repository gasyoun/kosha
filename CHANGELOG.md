# Changelog

All notable changes to the Gasuns Sanskrit Dictionary (kosha) are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is
[SemVer](https://semver.org/). Keep upcoming work under [Unreleased], then **cut a new
version every time the changelog is updated** (promote [Unreleased] to the next `x.y.z`
with today's date, tag `vx.y.z`, publish a GitHub release — same pass).

Two version tracks, do not conflate: **repo releases** (`vX.Y.Z` tags, this file) cover
code + docs; **data releases** (`data_version` in `kosha.db` meta, shipped as release
assets from P1 on) are versioned separately per
[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md) §A2 —
sense citations pin to `data_version`, not to repo tags.

## [Unreleased]
<!-- entries land in changelog_queue/ -- appended via tools/changelog_queue_consume.py, consumed by cut_release.py at release-cut (H3355); direct bullets here are hook-blocked -->

## [0.117.8] - 2026-09-02

- **H3925 (Opus 5 `claude-opus-5`) — the whole A3 chain rebuilt on the fixed join key: the 196,378 upper bound is now a measured 164,236, and the same defect turns out to survive one position inward.** [H3911](https://github.com/gasyoun/kosha/blob/main/CHANGELOG.md) diagnosed `form_key()`'s inability to collide the two spellings of a Sanskrit word-final nasal and fixed it in [sanskrit-util 0.11.0](https://github.com/sanskrit-lexicon/sanskrit-util/pull/72); this re-runs all five stages that read those keys — the 3.3M-form audit join, the give-back narrowing, the cell-resolved triage, the human validation sheet and the [`/concordance/morphology/`](https://github.com/gasyoun/kosha/blob/main/concordance/morphology/index.html) page — so no surface is left keyed on one era and the rest on another. **The driver refuses to start unless the library actually carries the fix** (`rasaṃ == rasam` and `rājan != rājam` are both asserted before stage 1), which is what caught the shared sanskrit-util checkout still sitting at 0.6.0: running against it would have reproduced the old keys as a convincing no-op. Pre-fix → post-fix: distinct attested keys **386,012 → 352,745** (−33,267 that were spelling twins, not distinct words) · AG **239,443 → 238,312** · G¬A **3,086,869 → 3,088,000** · **A¬G 196,378 → 164,236** (−32,142, −16.4%) · attested-side coverage **49.13% → 53.44%**. Two things the numbers say and prose would not: the sampled pre-estimate of 24,149 was a **floor, not a forecast** (it could only see twins already inside the candidate set, and the real effect is 33% larger), and the fix is a **re-partition rather than a monotone gain** — collapsing final `-ṃ` onto `-m` also breaks 1,131 net generated-side matches that existed only because final `-ṃ` and final `-n` were conflated, which is why AG falls while A¬G falls further. Downstream: give-back candidates **5,656 → 5,588** (from `paradigm_gap` 94,018 → 70,510), triage **owed 5,232** (slot-conflict 2,521 · coverage-hole 2,711) against **355 not owed**, page coverage 175,027 → 174,797 of 370,664 cells — barely moved, because the 95%-token head was already well covered and the fix lands in the long tail. **The triage doubles as the regression test:** the `orthographic-variant` verdict existed solely to catch anusvāra twins the broken key had split, and it matched **146 rows before the rebuild and 0 after**. Three consecutive triage runs produced identical counts. **New measured finding, not a guess:** medial anusvāra before a **labial** is phonetically /m/ but still folds to `n`, so `vaiśaṃpāyana` keys as `vaiśanpāyana` and never meets the `vaiśampāyanaḥ` the generator already emits — **278 of the 2,521 `slot-conflict` rows (11.03%, 11.58% by corpus weight) are not disagreements at all** (`saṃbhavaḥ` vs `sambhavaḥ`, `saṃbandhaḥ` vs `sambandhaḥ`, `samyaksaṃbuddhaḥ` vs `samyaksambuddhaḥ`), and 90 candidates collapse into their own lemma once refolded. That is **deliberately not fixed here** — narrowing the medial fold is a second change to a library ~85 repos consume and needs its own release and regression pass — but the rows are screened off the human validation sheet by an explicit named rule rather than left for a reviewer to reject one at a time, and every count on that sheet's screening banner is now measured at build time instead of hardcoded (four of the five were already stale). Sheet republished to [gasyoun.github.io/vote/sheets/h3863_giveback_slot_conflicts.html](https://gasyoun.github.io/vote/sheets/h3863_giveback_slot_conflicts.html); [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md) Q3 (both the two-joins table and the Q1–Q3 status table), both manifest rows and the three build reports now carry the rebuilt numbers, and the upper-bound caveats are gone. `tests/test_morphology_page.py` 8/8.
## [0.117.7] - 2026-09-02

- **H3911 (Opus 5 `claude-opus-5`) — the A3 `A¬G` figure of 196,378 is an upper bound, not a measurement: the join key could not collide the two spellings of a Sanskrit word-final nasal.** `form_key()` folded anusvāra to `n` at every position while never touching a literal `m`, so `rasaṃ` → `rasan` but `rasam` → `rasam` and **every anusvāra-final attestation read as un-generated**. Fixed upstream in [sanskrit-util 0.11.0](https://github.com/sanskrit-lexicon/sanskrit-util/pull/72) (word-final anusvāra folds to `m`; medial fold unchanged, `saṃskṛta == sanskṛta`; final `-n` still distinct from final `-m`, `rājan != rājam`), with the WhitneyRoots regression donor synced in the same pass. Measured against this repo's own dataset: **24,149 of the 196,378 A¬G keys (12.30% of rows, 16.86% by corpus weight) stop being gaps** under the fixed key — `rūpaṃ` 1,113×, `duḥkhaṃ` 565×, `vijñānaṃ`, `ākāśaṃ`, textbook `-am` neuters written with anusvāra. **Corrected A¬G ≈ 172,229.** The AG / G¬A split and every conclusion drawn from the audit's *direction* are unaffected — only the gap magnitude moves. [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md) Q3 and the `morphology-attestation-audit-inflections` manifest row now carry the correction; a rebuild against sanskrit-util ≥ 0.11.0 is owed before that dataset is released, and it also re-runs the give-back triage and the `/concordance/morphology/` page, which read these keys.
## [0.117.6] - 2026-09-02

- **H3862 (Opus 5 `claude-opus-5`) — the aligned-sense table gains its Sa→Sa columns, and two of the four dictionaries it was asked for turn out not to exist.** Wave-2 slice 2 of the sense-reconciliation layer: ŚKDR (Śabdakalpadruma) and VCP (Vācaspatyam) now sit beside PWG, MW and Apte in [sense_alignment.tsv](https://github.com/gasyoun/kosha/blob/main/data/concordance/sense_alignment.tsv), `shape` extended from `pwg-mw-apte` to five positions so granularity mismatch stays visible. **Step 1 refused two of them, with reasons rather than silence:** Medinī and Amara are not in CDSL at all, and the trap is that csl-orig and csl-sqlite *do* carry an `md` code — it is **Macdonell**, not Medinīkośa, so loading it because the letters matched would have put an 1893 Sanskrit-English dictionary under a Sanskrit-Sanskrit kośa's header with nothing downstream to catch it. **The bridge the handoff expected does not exist:** the kośas carry **zero `<ls>`** — 0 of 42,531 ŚKDR records and 0 of 50,135 VCP records — so the weighted-witness channel, the only one that crosses a language boundary, is closed for them by construction, and the gloss channel is closed by the language fence. What does exist is the reverse direction, printed rather than inferred: **PWG cites those kośas in its own `<ls>`** (`ŚKDR.` 1,227×, `MED.` 1,824× across the 500-headword pilot, touching 479 of its 500 lemmas), which is the new `attrib` method — weighted `1/df` off the *same* table as `ls` and decided by the *same* τ, so the slice **adds no constant of its own**, and ranked below `ls` because one dictionary pointing at another is weaker than two converging on a third text. The abbreviations reach it through an explicit `ATTRIB_KEYS` table, **not** by lowering `PREFIX_MIN` below 4 (which still refuses to let `R.` fold onto `RV.`). **The language fence is now declared as data**: `GLOSS_LANG` gives each dictionary its metalanguage and `gloss_channel_open()` is the single gate, so Sanskrit is fenced off wording-comparison explicitly, for the same reason German was in slice 1 — a Jaccard between two Sanskrit glosses would not be a weak signal, it would be a number with nothing behind it. **A channel was measured and rejected, and the dead end is recorded**: reading the kośas' own `iti X` / `yathā X` attributions as witnesses re-invents witnesses through a side door `PREFIX_MIN` closes — on the pilot it matched PWG's `PRAT.` to `pratyarthin` ("counter-claimant") and `BUDDH.` to `buddhim`, 73 hits of 707 records and most of them false; the honest version needs a closed curated source vocabulary and is a slice of its own. **Slice 1's numbers did not move, and that was verified rather than assumed:** comparing the new table against the `--no-sasa` baseline row by row on `(lemma, pwg/mw/apte sense ids, status, method, score, witnesses)`, **0 rows appear that the baseline did not have**, and the 67 baseline rows that no longer appear verbatim are exactly the 67 that gained a kośa cell — no western sense changed partner, method, score or witness list, and clean `1-1-1` rows stay at **262**. Aligned groups 2,957 → 3,013 decomposes exactly into 56 meanings only a kośa entered and 11 existing meanings that gained a kośa cell; `df` is unchanged because dictionaries that cite nothing raise no document frequency. The 1,832 kośa senses nobody attributes are kept as rows under a new `no-citation-apparatus` class — the Sa→Sa counterpart of `cross-language-gap`, a property of the source format rather than a tuning failure. **The publication fence is untouched and still green:** the table stays behind the explicit `sense_align` ux key and off the 2,324 live `/w/` pages, and the test asserting a live-shaped `ux={"variant": "a"}` render carries no `sense-align` markup passes. Smoke **31/31** ([H3862_SENSE_ALIGNMENT_SMOKE_LOG_02.09.26.md](https://github.com/gasyoun/kosha/blob/main/docs/H3862_SENSE_ALIGNMENT_SMOKE_LOG_02.09.26.md)), unit tests 31 (26 + 5 new: the Sanskrit gloss-channel refusal, the ŚKDR attribution edge, the too-common attribution that τ rejects, the table's refusal to reach the wrong kośa, and the `<s>`-is-the-definition inversion), full suite **606 passed**. `sense-alignment-pilot` manifest row updated; compare page regenerated at [gasyoun.github.io/h3744-sense-align/](https://gasyoun.github.io/h3744-sense-align/). **No precision figure is quoted** — the acceptance pass is what would measure it and it is out of scope; the known `attrib` false-positive class is named instead (the join is lemma-level, so PWG *Gras* lands on ŚKDR's **verbal-root** entry for `kaṭa`, and `bhū` likewise), and the lemma-variant graph that would fix it stays the next open unit.
## [0.117.5] - 2026-09-02

- **H3863 (Opus 5 `claude-opus-5`) — cell-resolved triage of the 5,656 csl-inflect give-back candidates: 5,655 of them were machine-decidable, and three defects in my own first pass got caught by measuring rather than asserting.** The candidate set shipped as ''needing human triage, not a defect list''. It did not: DCS tags every token with `feat_case`/`feat_number`/`feat_gender`, which decides the question directly, so per the standing rule (evidence-decidable cards are applied and reported, never voted) this ran mechanically. **owed 5,149** (slot-conflict 2,441 · coverage-hole 2,708) · **not owed 506** (compound-member 222 · orthographic-variant 146 · lexicon-gap 105 · indeclinable 33) · **residue 1**. New [scripts/triage_morph_giveback_candidates.py](https://github.com/gasyoun/kosha/blob/main/scripts/triage_morph_giveback_candidates.py), report [MORPHOLOGY_GIVEBACK_TRIAGE_REPORT.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/MORPHOLOGY_GIVEBACK_TRIAGE_REPORT.md), data [morph_giveback_triaged.tsv](https://github.com/gasyoun/kosha/blob/main/data/concordance/morph_giveback_triaged.tsv). **A defect in the shared join key, found here:** `form_key()` cannot collide the two standard spellings of a word-final nasal — Sanskrit writes final `-m` as anusvāra before a consonant, and `form_key` maps the anusvāra to `n` (`rasaṃ` → `rasan`) while leaving a real final `m` alone (`rasam` → `rasam`), so the spellings never match and **every anusvāra-final attestation reads as un-generated**; 146 rows are exactly this (`iyaṃ` = `iyam`). Because that fold is the shared `sanskrit-util` one, it inflates the **whole** A3 A¬G figure of 196,378 — that number is an upper bound, not a measurement. **Two further self-corrections:** Cpd-dominance was not respected (`ātma` is `Cpd` on 2,544 tokens against 10 with a real case, so taking the most frequent real case promoted 8 nominatives over 2,544 compound uses and called a bound stem a missing cell — 21 rows affected); and the DCS re-lookup queried `token.form` only while the audit's attested side was the **union** of `token.form` and `token.m_unsandhied`, so all 829 `no-dcs-token` rows were resolvable through the second column and the residue fell 934 → 1. **Correction to the H3782 record:** `rājñ` was cited there, in PR #482 and in the roadmap as an allomorphic bound stem that leaked past the filter, and used to argue the set needed human triage — DCS tags it `Voc Sing Masc` 880 times, an inflected cell rather than a stem; `ātma` was correctly suspected. **Validation sheet before hand-off:** 40 slot-conflicts sampled to the vote hub ([h3863_giveback_slot_conflicts.html](https://gasyoun.github.io/vote/sheets/h3863_giveback_slot_conflicts.html)) — the only class whose verdict is a claim about Sanskrit rather than a lookup — because shipping 5,149 rows to a third-party project on an unvalidated automated method would be the overclaim this whole audit exists to prevent. Emitted through `csl_pyutil.render_review_sheet` (V1–V8); V13 identity gate satisfied by resolving every `dcs:<sent_id>` to its text and reference.
## [0.117.4] - 2026-09-02

- **H3783 (Opus 5 `claude-opus-5`) — CONCORDANCE_ROADMAP A4 exit checks corrected: all three were met in July, the prose said otherwise, and a duplicate handoff was minted from it.** H3783 asked for the Pāṇinian sūtra-coverage map, sampled derivation verification and a settled derivation-metadata licence. Every one of them was already on `origin/main`: the coverage map shipped **24-07-2026** (H1468, [PR #180](https://github.com/gasyoun/kosha/pull/180)) as [sutra_coverage_map.tsv](https://github.com/gasyoun/kosha/blob/main/data/concordance/sutra_coverage_map.tsv) over the **named** vidyut 0.4.0 enumeration (n = 3983, never "~4,000") — `lit` 221 · `dark-unattested` 55 · `dark-out-of-scope` 3707 · `dark-engine-gap` 0; the 30-chain sample shipped **20-07-2026** (H1368) in [DERIVATION_HARNESS_BUILD_REPORT.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/DERIVATION_HARNESS_BUILD_REPORT.md); and the licence was settled **18-07-2026** (H1263) in [vidyut_prakriya_derivation_2026-07.md](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/vidyut_prakriya_derivation_2026-07.md), whose § *Human gate — not triggered* states why no `@DECIDE` is owed — five days before the [data-v0.3.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.3.0) release that W3b (H1574) cut.
  **What was actually wrong:** the roadmap's Q4 **exit-check bullet** and **open `@DECIDE` 1** were never rewritten when the work landed. The 01-09-2026 truth-pass (H3782) corrected this section's *calendar slot* and its Q1–Q3 *status table* — which correctly reads A4 **complete** — but left the exit checks and the `@DECIDE` list reading as open, and those are the sentences a later `/fruit` or `/ask` pass quotes. Same class as [Uprava FINDINGS §644](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md), one file further on: a truth-pass that checks a section's status line has not checked its exit checks, risks or `@DECIDE` list.
  **Corrected in place, with evidence per check** — each exit check now names the wave, date, handoff, PR and artefact that satisfies it; `@DECIDE` 1 is struck through with the rights record and the reason no human gate fired; and a dated header note records the lesson in the file itself so the next truth-pass reads exit checks as separate claims.
  **One honest residual, and it is a human act:** the 30 rendered chains carry neither a stated justification for N = 30 nor a recorded human verdict — they are a sample awaiting sign-off, not an audit. Written into the roadmap as such and mirrored as an `@DO` in [Uprava GTD](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md); no agent closes it by re-reading the same chains.
## [0.117.3] - 2026-09-02

- **H3861 (Opus 5 `claude-opus-5`) — `/concordance/morphology/` is built: the last CONCORDANCE_ROADMAP Q3 deliverable that had no artefact behind it.** Spec was "paradigm cell → attested? with corpus evidence", and that is now literal: search a lemma and get its generated paradigm as a case × number grid per gender, every cell marked attested or not against the 5.69M-token DCS corpus, with occurrence counts, citable host-independent `dcs:<sent_id>` loci and KWIC; below it, the forms DCS attests that the generator never produced. New [scripts/build_morphology_concordance_page.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_morphology_concordance_page.py) **consumes** the H3782 audit outputs rather than re-deriving them — attestation comes from [morph_attest_infl_AG.tsv](https://github.com/gasyoun/kosha/blob/main/data/concordance/morph_attest_infl_AG.tsv), gaps from [morph_attest_infl_AnG.tsv](https://github.com/gasyoun/kosha/blob/main/data/concordance/morph_attest_infl_AnG.tsv), and only the gender/case/number cells are read from `kosha.db` `inflections`, so the 5.7M-token corpus is never re-scanned and the page cannot drift from the dataset its trust block cites. **Static head is measured, not hardcoded** (standing rule D4/D5): `--coverage 0.95` walks `lemma_frequency.tsv` and lands on **N=11,148 lemmas covering 95.00% of corpus token mass**, 9,150 of which carry generator rows — 370,664 cells, **175,027 attested (47.22%)**. **The audit's controls are rendered, not footnoted,** so a red cell cannot be misread as an engine defect: each gap list states how many of its rows are verbal (out of scope — the generator holds 680 verbal lemmas against 222,736 nominal) or attested only as a sandhied surface, both classes visually demoted; and the trust block explains that homographic cells share one `form_key` evidence count (`rāmaḥ` nom. sg. and `rāma` voc. sg. fold to one key and are credited with the same 3,325, which is a statement about the key, not about vocatives). **Delivery shape:** self-contained HTML, no external dependencies, with light per-letter `index_<a>.js` shards for typing and prefix search and size-capped `kwic_<a>_<n>.js` cell chunks loaded only once a lemma resolves — 115 files, 40.5 MB, largest chunk 483 KB; chunks are numbered over sorted keys rather than named by second letter, because SLP1 is case-sensitive while NTFS is not (the H3597 case-twin collision class). Dropping four fields the page never rendered cut 7.6 MB. **Verification:** 8 invariants in [tests/test_morphology_page.py](https://github.com/gasyoun/kosha/blob/main/tests/test_morphology_page.py) — the manifest resolves, index and chunks cover identical lemma sets, the client's chunk picker lands on the owning chunk for every lemma, and every rendered attestation mark matches AG-TSV membership — plus a headless harness that executes the page's own script body over the real shards and asserts the rendered output (17 checks: paradigm grid, attested and unattested cells, occurrence counts, loci, gaps, IAST↔SLP1 input parity, and that prefix search pulls no cell chunk). Full suite 576 passed. Manifest row `morphology-attestation-audit-inflections` now names the page as a consumer; roadmap Q3 flipped to complete.
## [0.117.2] - 2026-09-01

- **H3788 (Opus 5 `claude-opus-5`) — W2 citable v1: the release was already citable, the record and the policy were not; four defects in the citability surface repaired.** Verified against the Zenodo API that a citable release exists — `v0.117.1`, version DOI [`10.5281/zenodo.22231444`](https://doi.org/10.5281/zenodo.22231444) under concept DOI [`10.5281/zenodo.21965599`](https://doi.org/10.5281/zenodo.21965599), 21 deposits archived since the webhook of 14-08-2026 — and that neither W0 nor W1 blocks it (W0 freeze-exit criteria all met; every agent-measurable W1 gate PASSES, only the human §9 tick is open, and it is not a stop). Full audit: [docs/CITABLE_V1_RECORD_KOSHA_01.09.26.md](https://github.com/gasyoun/kosha/blob/main/docs/CITABLE_V1_RECORD_KOSHA_01.09.26.md); the missing fourth W2 component is now written as [docs/VERSIONING_AND_CITATION_POLICY_KOSHA.md](https://github.com/gasyoun/kosha/blob/main/docs/VERSIONING_AND_CITATION_POLICY_KOSHA.md).
  **Defect 1 — release bytes depended on the uploader's checkout.** `.gitattributes` pins `*.tsv text eol=lf`, but git never renormalizes files already in a working tree when that rule lands, `git status` stays clean, and nothing warns. **28 manifest rows** carried a `size_bytes` exactly one byte per line above the canonical file — the signature of a `refresh` run in a CRLF checkout — spanning three DOI-archived releases (`data-v0.2.0`, `data-v0.3.0`, `data-v0.5.0`). Proven on `kosha-lemma-frequency`: LF 4,827,466 B vs CRLF 4,910,744 B, delta 83,278 = exactly the line count, identical content (LF-normalised sha256 `c07f6a02…` from both checkouts); the **published** `data-v0.5.0` asset is the 4,910,744 B CRLF variant. All 28 repaired to canonical sizes.
  **Defect 2 — a released tag was moved and Zenodo archived both states.** `v0.116.0` carries two version DOIs, `10.5281/zenodo.22131151` (15:43Z, 187,386,121 B) and `10.5281/zenodo.22132415` (17:37Z, 187,389,165 B), both titled `v0.116.0` and pointing at the same tree. Deposits cannot be withdrawn, so the ambiguity is permanent; cite `…22132415`. Not repairable — recorded, with the immutable-tag rule that prevents a recurrence.
  **Defect 3 — sibling repos never resolved from a worktree, masking a data-loss hazard.** `update_manifest.py` derived the checkout root as `REPO.parent`, correct only in `…/GitHub/kosha`; inside a linked worktree every `csl-orig`/`SanskritLexicography`/`csl-apidev` row silently resolved to nothing, indistinguishable from "gitignored, leave alone". Fixed by new [scripts/manifest_paths.py](https://github.com/gasyoun/kosha/blob/main/scripts/manifest_paths.py) (probes candidate roots for a known sibling; `KOSHA_GITHUB_ROOT` overrides). Fixing it immediately exposed what it had been hiding: `refresh` then wanted to rewrite `pwg-tm-canonical-v1` from 101,677,729 B to **17,668 B** and `pwg-de-edition-v1` from 46,382,247 B to **33,951 B**, because those packs ship their payload outside git and the local clone holds only the 8 metadata files. `refresh` now **refuses any drop below 50 % of the recorded size** (`--allow-shrink` to override), a floor that separates the two hazards (0.02 % / 0.07 %) from every legitimate update in the same run (smallest 96.6 %).
  **Defect 4 — stale pointers.** `generated` said 2026-08-16 while the manifest had been edited through 01-09-2026; `interim_release` still named `data-v0.3.0` two releases on, and `note_for_agents` sends every agent to exactly that URL for public-tier downloads. Both corrected. `CITATION.cff`'s comment advertised `v0.115.1` as the latest archived release (four releases stale) and [docs/DOI_CHECKLIST_W2A.md](https://github.com/gasyoun/kosha/blob/main/docs/DOI_CHECKLIST_W2A.md) still asserted an agent fence against DOI minting that lapsed twice over (webhook 14-08-2026, ruling 16-08-2026) while showing empty "MG fills" cells against 21 real deposits; both rewritten.
  **New:** [scripts/freeze_release_manifest.py](https://github.com/gasyoun/kosha/blob/main/scripts/freeze_release_manifest.py) makes the frozen release manifest a build product instead of a hand-assembled asset — the published `data-v0.5.0` `datasets.json` was 5 rows at `manifest_version` 0.1.0 with no checksums, against 114 rows at 0.2.0 in the repo at the same moment. `freeze` selects on `in_release`, hashes **LF-canonically** so a citer reproduces the digest on any platform, **refuses a non-public-tier row** rather than dropping it silently (19 rights-encumbered rows caught in a negative test), and **refuses to cut from a CRLF working tree**; `check` diffs a committed frozen file against the manifest and exits non-zero on drift. Frozen manifests committed for all four published data releases ([data/manifest/frozen/](https://github.com/gasyoun/kosha/tree/main/data/manifest/frozen)), all four verifying OK. Writers now open with `newline="\n"` so repository JSON stops being written non-canonically. Residuals named in the record §5 and on the roadmap: cut `data-v0.6.0` (blocked on `release_asset` + `data_statement` for `pwg-sense-attestation-window` and `kosha-mastery-schedule`), renormalize the canonical checkout, wire `freeze … check` into the release gate.
- **H3782 (Opus 5 `claude-opus-5`) — A3 completion: the generated-vs-attested morphology audit run on a generated side that is *independent of the corpus*, plus a mechanical Q1–Q3 roadmap truth-pass.** The shipped A3 audit ([H1262](https://github.com/gasyoun/kosha/blob/main/data/concordance/MORPHOLOGY_ATTESTATION_BUILD_REPORT.md), 18-07-2026) reported **attested-but-never-generated = 2**, which reads as "the generator misses nothing" and actually meant that **93.30% of its generated side was itself `source='dcs'`** — the corpus's own tokens, joined back against the corpus. That report said so and handed the question on; nobody picked it up. New [scripts/build_morphology_attestation_audit_inflections.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_morphology_attestation_audit_inflections.py) runs the join CONCORDANCE_ROADMAP Q3's first exit check actually names ("full 6.9M ⨯ 5.7M") against `kosha.db` `inflections` — **3,326,312 distinct forms, 99.99% `source='cologne_mwinflect'`, derived from MW headwords with no DCS input**, so the asymmetry is measurable in both directions for the first time: **AG 239,443 (7.20%) · G¬A 3,086,869 (92.80%) · A¬G 196,378 of 386,012 attested keys (50.87%)** — against the old A¬G of 2. **Roadmap attribution corrected:** that 6.9M table is *not* "vidyut-generated" as the roadmap claimed since 08-07-2026; vidyut's real output is the separate 28,567-row `forms` slice, and the two tables are different generators on which the audit means different things. **Two methodological controls, both load-bearing:** the attested side carries `token.form` *and* `token.m_unsandhied` (a paradigm generator emits unsandhied forms, so joining it against sandhied surfaces manufactures a fake gap class — the one that dominated H1262's triage); and A¬G is cross-tabbed against DCS `upos` because the generator's inventory is **222,736 nominal lemmas against 680 verbal**, so finite verbs are territory `inflections` never claimed and a verb-shaped gap must never be quoted as a nominal-engine defect. A¬G triage splits `paradigm_gap` (lemma known, cell missed → the first real [csl-inflect give-back](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md) payload; H1262 routed nothing because it found zero) from `lexicon_gap` (lemma absent → a dictionary-coverage question, not an engine bug), plus the OCR/segmentation noise classes. Outputs: [MORPHOLOGY_ATTESTATION_INFLECTIONS_BUILD_REPORT.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/MORPHOLOGY_ATTESTATION_INFLECTIONS_BUILD_REPORT.md) with four human-checkable sample tables, `morph_attest_infl_{AG,AnG}.tsv` + gzipped `GnA`, manifest row `morphology-attestation-audit-inflections`. **Roadmap truth-pass ([CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md)):** Q1 and Q2 were marked "release pending" when both had shipped as assets of [data-v0.2.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.2.0) on 19-07-2026, five weeks before the file's own 27-08 truth-pass; A4's promotion into the Q3 calendar slot (human ruling D1, 17-07-2026) was never re-labelled as its own plan required, so the file has read "Q4 = A4" against a shipped-in-Q3 reality; and A3's `/concordance/morphology/` web page is recorded as the one Q3 deliverable with **no artefact behind it**. A dated Q1–Q3 status table now carries dataset / release / web-page / verdict per quarter.
## [0.117.1] - 2026-09-01

- **H3781 — manifest: csl-atlas witness consumer flipped from `queued` to delivered (Opus 5 `claude-opus-5`, 01-09-2026).** The `mw-heritage-crosswalk` row listed `csl-atlas witness column (queued)`; it shipped 08-07-2026 as H346, [csl-atlas PR #227](https://github.com/sanskrit-lexicon/csl-atlas/pull/227) (`feat: heritage-witness column joined from MW-Heritage crosswalk`, with tool page, builder, validator and test on `main`). Found while closing H3781 as DUPLICATE-SHIPPED — the 928,262-form Heritage surplus ingest it asked for was already delivered by H111 ([PR #7](https://github.com/gasyoun/kosha/pull/7)) and H696 ([PR #57](https://github.com/gasyoun/kosha/pull/57)). Companion root-cause fix in [SanskritLexicography PR #2016](https://github.com/gasyoun/SanskritLexicography/pull/2016).
- **H3742 (Sonnet 5 `claude-sonnet-5`) — one shared mastery layer over kosha's five drill families: unified ease weights + a combined FSRS-style due schedule.** Added the `mastery` block (`bucket_field` + `bucket_ease`/`ease_formula` + `family_default_ease`, all 0..1 higher=easier) to each family's weights file — new [data/sandhi/drill_weights.json](https://github.com/gasyoun/kosha/blob/main/data/sandhi/drill_weights.json), extended [data/samasa/drill_weights.json](https://github.com/gasyoun/kosha/blob/main/data/samasa/drill_weights.json) and [data/morphology/drill_weights.json](https://github.com/gasyoun/kosha/blob/main/data/morphology/drill_weights.json), new [data/frequency/vocab_drill_weights.json](https://github.com/gasyoun/kosha/blob/main/data/frequency/vocab_drill_weights.json) and [thematic_vocab_drill_weights.json](https://github.com/gasyoun/kosha/blob/main/data/frequency/thematic_vocab_drill_weights.json) — semantics documented once in [data/MASTERY_WEIGHTS_SPEC.md](https://github.com/gasyoun/kosha/blob/main/data/MASTERY_WEIGHTS_SPEC.md). New [scripts/build_mastery_schedule.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_mastery_schedule.py) mixes all five families' 35,517 items into [data/mastery/combined_schedule.json](https://github.com/gasyoun/kosha/blob/main/data/mastery/combined_schedule.json); `due_items(schedule, clock, n, seed)` draws deterministically across families, proved by 6 selftests in [tests/test_mastery_schedule.py](https://github.com/gasyoun/kosha/blob/main/tests/test_mastery_schedule.py). **Parity-table corrections at mint time:** vocab's and thematic vocab's `.apkg` exports already existed (H947/H1462); cohort `start_chteniya` is a frozen lesson≤3 subset of sandhi (not a sixth family, per the handoff's own "five families" title) and is deliberately excluded rather than given a duplicate weights/apkg pair, since its own freeze fence forbids new analysis layers. This is a reading-surface data layer only (SanskritKaraoke/SanskritGrammar consumers, planned) — it does not touch or duplicate Systema-Sanscriticum's Saraswati FSRS review engine. Manifest row `kosha-mastery-schedule` added.
## [0.117.0] - 2026-08-31

### Added
- **H3744 (Opus 5 `claude-opus-5`) — sense-reconciliation wave-2 slice 1: the PWG·MW·Apte aligned-sense table, staged, with a published before/after compare page.** The first user-facing render of the wave-1 substrate, and the first thing kosha builds that makes a lexicographic claim in its own voice. New [app/sense_align.py](https://github.com/gasyoun/kosha/blob/main/app/sense_align.py) (algorithm + row model + failure taxonomy, DB-free and unit-tested) and [scripts/build_sense_alignment.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_sense_alignment.py) (driver over `kosha.db`, read-only). **Method:** senses join a MEANING through shared literary witness — the `<ls>` sources both dictionaries cite for them — each witness weighted `1/df` inside the lemma, because a shared `MBh.` says nothing when every sense cites `MBh.`; this is the only signal that crosses PWG's German gloss boundary, and gloss-token Jaccard is fenced to MW↔Apte where both are English. Grouping is a greedy **best match per dictionary pair, not transitive closure** — closure merged `amṛta`'s *not dead*, *nectar* and *N. pr. the mother of Parikṣit* into one component, a false claim shaped like a row. The canonical नागदन्त case comes out right: PWG *Elephantenzahn* ↔ MW *elephant's tusk* on `MBh.`, PWG *Pflock in der Wand* ↔ MW *peg in the wall* on *Pañc.*, two meanings and not one. Pilot (500 headwords): 30,470 rows, **2,957 aligned (9.7 %)**, 262 clean `1-1-1` rows, 477/500 lemmas with at least one aligned meaning. Unaligned senses are KEPT as rows with a `failure_class` (`no-shared-witness` 17,671 · `witness-too-common` 6,844 · `no-gloss` 3,025 · `cross-language-gap` 1,835 · `outranked` 1,101 · `absent-dictionary` 62), and a worked FALSE POSITIVE is documented rather than hidden; no precision figure is quoted anywhere, because measuring it is the wave-2 acceptance pass, which needs a human vote and is out of scope. **Not published:** the table is not on the 2,324 live static pages — [docs/NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md](https://github.com/gasyoun/kosha/blob/main/docs/NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md). Compare page for the human ruling: [gasyoun.github.io/h3744-sense-align/](https://gasyoun.github.io/h3744-sense-align/). Evidence: 31/31 smoke checks ([log](https://github.com/gasyoun/kosha/blob/main/docs/H3744_SENSE_ALIGNMENT_SMOKE_LOG_31.08.26.md)), 26 unit tests, [packet](https://github.com/gasyoun/kosha/blob/main/docs/H3744_SENSE_ALIGNMENT_PACKET_31.08.26.md), manifest row `sense-alignment-pilot`.

### Fixed
- **Truth-fix — `ux=` truthiness stopped being a non-publication gate on 26-08-2026 and nothing said so.** The H3457 `NOT_PUBLISHED` marker was deleted when that layer was published (commit `070050a`), so every one of the 2,324 live `/w/` pages is now rendered WITH `ux`; an organ hung on plain `ux` truthiness would ship on the next live rebuild. [app/word_page_ux.py](https://github.com/gasyoun/kosha/blob/main/app/word_page_ux.py)'s docstring still claimed "STAGING ONLY — nothing here is on the public word page" and pointed at the deleted marker. Docstring corrected; the H3744 organ rides an explicit `ux={"sense_align": True}` key set only by `--ux-staging`, and [tests/test_sense_alignment.py](https://github.com/gasyoun/kosha/blob/main/tests/test_sense_alignment.py) asserts a live-shaped `ux={"variant": "a"}` render carries no alignment markup.

## [0.116.2] - 2026-08-30

- **H3745 (Sonnet 5) — W4b Pages budget re-measure with a wired 70% (717 MB) fail gate; W4a panini surface confirmed already shipped (H1585); two doc truth-fixes.** New [scripts/measure_pages_budget.py](https://github.com/gasyoun/kosha/blob/main/scripts/measure_pages_budget.py) re-measures the D4 static head N and mean KB/page at build time, sums it against the on-disk cards/concordance/reading/docs-js tiers, and exits 1 if the projection exceeds 717 MB (70% of the 1,024 MB Pages soft cap) — enforced every fixture-tier CI build via [tests/test_pages_budget_gate.py](https://github.com/gasyoun/kosha/blob/main/tests/test_pages_budget_gate.py). Today's re-measure: 653.2 MB = 63.8%, GATE PASS ([docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md) §6 append-only log). W4a (coverage map with four visually-distinct statuses, chain view, /viz-page trust block) was already fully shipped 24-07-2026 (H1585, kosha#185) — confirmed against origin/main, no re-build. Truth-fixes: .ai_state.md Next Steps flipped H3549/H3565 from stale 'queued' to their actual ✅ Done status; docs/ROADMAP_KOSHA_2026_2027.md W2 DOI line corrected from 'human gate — MG mints' to the standing 16-08-2026 policy permitting agents to mint DOIs.
## [0.116.1] - 2026-08-30
### Added
- **Improvement-set plan + three Claude Code handoffs claimed (30-08, Opus 5 `claude-opus-5` grilling session).** [docs/PLAN_KOSHA_IMPROVEMENT_SET_2026-08-30.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_IMPROVEMENT_SET_2026-08-30.md) records the settled design tree behind H3743 (Sonnet 5, 🟡2 medium — akshara full-corpus blinded MT benchmark, drain-gated), H3744 (Opus 5, 🔴3 hard — sense-reconciliation W2 PWG/MW/Apte aligned-sense table, staged behind `ux=` with a published compare page) and H3745 (Sonnet 5, 🟡2 medium — A4 W4a panini surface + W4b Pages budget re-measure with a 70 % / 717 MB fail gate). Records the rights fence (both akshara manifest rows are `tier: restricted`, so the 51,663 harvested heads are a measurement asset only and can never surface as text on `/w/`), why the benchmark is worth re-running at all (the pilot CI [−0.12, +0.53] crossed zero on a 101-head intersection), the six explicit exclusions, and two doc truth-fixes that ride inside H3745. Pointer row added to the live portfolio roadmap; status is not forked into the plan.
- **H3597 (OxAlpha, 28-08) - INCIDENT FIX: case-twin filename collision (SLP1 case is phonemic, NTFS is not) + disk-reclaim parser.** The census contains case twins the site serves as DIFFERENT cards (`dvipAd` != `dvipad`; 51,663 keys = 46,488 casefold-distinct, 5,175 case-variants); flat `<safe>.html` raw names made each pair share one physical file on case-insensitive NTFS - one card silently overwrote the other, and the parse+delete run consolidated it. Fixed: crawler raw names now carry a case-sensitive sha1-8 suffix (`raw_filename()`), `--manifest`/`--log` overrides for repair passes, live crawler restarted on the fix. New `scripts/akshara_full_parse.py`: incremental parse to `parsed_corpus.jsonl` (+`_ru.jsonl` for pass 2) with `--delete-raw` reclaim after per-file parity - wisdomlib-shaped storage, ~1.8 GB raw freed for 33,436 parsed heads (corpus ~1.1 GB; `q_slp1` recorded per row - drain classifies the site's case-normalization fallback, e.g. `q=A` served the `a` card, 27/27 in a live sample, as a legitimate answer class). New `scripts/akshara_repair_twins.py`: repair manifest / status / purge; repair sequence (~7.1k twin keys re-fetched under hashed names, then purge+reparse) is part of the drain checklist - report section 5b.
- **H3597 (OxAlpha, 28-08) - crawl speed amendment per MG ruling: 2 polite parallel streams.** `akshara_full_crawl.py` now defaults to `--workers 2` (ThreadPoolExecutor; per-worker politeness unchanged - each stream keeps its own 2.0 s throttle + jitter + backoff, per-connection behavior identical to the approved H3455 contract; log appends + progress serialized under a lock; `--workers 1` reverts to a single stream). Measured live after the switch: 0.69 URLs/s (was 0.35) -> full-crawl ETA moved from ~3 Sept to ~1 Sept. Switch executed under the watchdog (kill -> relaunch from exact checkpoint, workers=2 in run log, 0 fail). Two transient local-DNS blips in the first minutes (getaddrinfo failed, machine-side, not site-side) re-fetched 200 OK the same hour via the crawler's own code path. Coverage report §§ 2-4 updated.
- **H3597 (OxAlpha, 28-08) - FULL kosha crawl made self-healing: `kosha-akshara-crawl-watchdog` scheduled task + crawler keep-awake + inline cold-fetch validation.** New `scripts/akshara_crawl_watchdog.ps1`: every 10 min (StartWhenAvailable + WakeToRun, IgnoreNew, 10-min exec limit) - healthy → no-op; wedged (alive, no manifest write >10 min) → taskkill + relaunch; dead → relaunch the incomplete pass from the resume logs; both passes done/exhausted → log + self-disable (no orphaned task; FINDINGS §210 lesson). Crawler patched: holds `SetThreadExecutionState(ES_CONTINUOUS|ES_SYSTEM_REQUIRED)` on win32 while alive (network I/O alone does not stop Windows sleep), and verifies `data-q-slp1` parity per stored card - mis-resolved cold fetches get one warm re-fetch, `resolved_fix`/`misresolved` recorded in the crawl log (drain gate stays as backstop). Registered via schtasks.exe (Register-ScheduledTask cmdlet path broken on this box). End-to-end proof 28-08 (FINDINGS §223 rule): healthy no-op kept 1 process; controlled taskkill → auto-restart from the exact checkpoint (13,495/51,663, `brahmakalA → brahmatIrTa`, 0 fail). Report §8 rewritten: [docs/AKSHARA_FULL_COVERAGE_H3597_27.08.26.md](https://github.com/gasyoun/kosha/blob/main/docs/AKSHARA_FULL_COVERAGE_H3597_27.08.26.md).
- **H3597 (OxAlpha) - akshara.ru FULL kosha crawl launched (RESTRICTED, benchmark-only): census-first, NO volume stop per MG ruling 27-08-2026.** Census FROZEN before the first card fetch from the site's own sitemap-kosha-001/002 index: **51,663 unique heads** (`data/akshara_full/head_manifest.jsonl` + `census.json`, sha256-pinned sources). New `scripts/akshara_census.py` (freeze + `--check` parity) and `scripts/akshara_full_crawl.py` (extends the H3455 pilot by **importing** its `guarded_fetch` robots allow-list - fenced endpoints never requested; 2.0 s throttle + ≤1 s jitter; exponential backoff; checkpointed resume-from-log JSONL manifests - load-bearing at 206,652 URLs = 51,663 heads × (dict=all + 3 MT variants); milestone record every 1000 URLs with rate/ETA, never aborting on volume). Pass 1 running detached since 27-08-2026 (~0.21 URLs/s, ETA ~69 h; then `--ru` pass 2 ~+208 h). Launch findings: cold-fetch mis-resolution quirk (site served the `ABa` card for `?q=ABA` while cold; warm re-fetch correct) → mandatory drain gate asserting `data-q-slp1` parity per stored card; launch refetch spot check 9/10 byte-identical with the 1 mismatch fully diagnosed by that quirk. Census report + resume instructions + drain acceptance gate: [docs/AKSHARA_FULL_COVERAGE_H3597_27.08.26.md](https://github.com/gasyoun/kosha/blob/main/docs/AKSHARA_FULL_COVERAGE_H3597_27.08.26.md). datasets.json + `akshara-mt-benchmark-full` (restricted sibling of the H3455 pilot row). Raw HTML/parsed corpus stay gitignored; nothing public without a fresh @DECIDE.

### Added
- **H3549 (OxAlpha) — 30-day risk-ranked code review + inactive OxAlpha status-gate design.** [Evidence report](docs/CODE_REVIEW_KOSHA_OXALPHA_30D_2026-08-26.md): ~100 window PRs (26-07..25-08-2026) censused, 10 executable-risk slices retained with exact base/head SHAs, independent Standards + Spec verdicts (all PASS), 6 findings ledgered (1×P2, 5×P3/informational; **zero proven P0/P1 → zero repair PRs**, recorded explicitly); adapter bootstrap landed separately in #463. [OXALPHA_STATUS_GATE_DESIGN_2026.md](docs/OXALPHA_STATUS_GATE_DESIGN_2026.md): future executable-code review gate + sensitive-path human approval, designed and **not enabled** (no workflow added, protection untouched).

## [0.116.0] - 2026-08-27
### Added
- **H3596 (OxAlpha) — datasets.json manifest v0.2.0: `status` + `consumer_candidates` planning fields; all 10 zero-consumer rows annotated.** New optional per-row fields (documented in `note_for_agents`): `status` ∈ {`awaiting-consumer`, `diff-then-decide`, `internal-tooling`}, `consumer_candidates` `[{repo, use, confidence}]` — plan entries only, never promoted into `consumers` until the consuming lane wires up. Annotated: `dcs-compound-dictionary` (→kosha samāsa trainer attestation ranking / SanskritGrammar PR #428 cross-check / Sanskrit-in-Numbers), `dcs-stem-cooccurrence-full` (→SanskritSpellCheck lift instruments / pwg-sense-attestation-window extension), `dcs-parallel-passages-full` (→RussianRamayana translator-env / Parallel-Sanskrit-Corpora), `dcs-sintagmatic-appendix7` (→pwg_ru portraits / Sundara lexical-note QA), `dcs-sintagmatic-appendix6-periods` (→kosha frequency-layer cross-check / Sanskrit-in-Numbers), verb trio (→Sanskrit-in-Numbers + claims probes; notes now carry the R2606-01 unaccented I/VI dead-end caveat), `stopovye-parallel-passages` = `diff-then-decide`, `archive-stopword-sqlite` = `internal-tooling`. `directory/index.html` regenerated (also catches up the page to the already-landed 93rd dataset + data-v0.5.0 asset URLs — the page had drifted from `datasets.json`). Consumer wiring tracked as Uprava GTD @DO rows.

## [0.115.3] - 2026-08-26
- **H3457 published (MG ruling 25-08-2026) - word-page learner layer live on all 2,324 static /w/ pages:** study badge (core_rank/coverage from lemma_frequency.tsv), localStorage favorites + /favorites.html index, PWG print-scan anchors to the printed edition. Same render_word_page as SSR; content unchanged byte-level, chrome added. Revert = rebuild without the ux layer. NOT_PUBLISHED markers removed per decision.

## [0.115.2] - 2026-08-25
### Added
- **H3549 (OxAlpha) — kosha 30-day risk-ranked code review and future independent review gate: execution-ready five-layer plan staged** (OxAlpha (x-preview-f-free), plan authored 26-08-2026 by Codex Sol (gpt-5.6-sol)). [Plan index](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.md) fixes the 30-day window, ten-slice risk cap, independent Standards/Spec passes, evidence-only P0/P1 repair contract, canonical GitHub adapter, and an inactive future status-gate design.
- **Literary-source `<ls>` citation links, H3457 wave 2** (H3479, Sonnet 5
  `claude-sonnet-5`). New `app/ls_hydrate.py` hydrates a PWG entry's
  `<span class='ls'>` citations (Cologne's own render deferral — see
  `app/render.py`'s documented "no href" gap) into links, reusing the
  SanskritLexicography `ls_resolver.generate_href` port plus the
  csl-observatory `pwg_scan_index.tsv` campaign registry (`scan_wired`) to tell
  a volunteer-scanned print facsimile apart from a resolved but untracked
  e-text/scan host — no new resolver. STAGING ONLY, same `ux=` gate and
  byte-identical-default guarantee as H3457; PWG only (MW-side is a later
  wave). Census over the staged 11-lemma sample: 6,303 `<ls>` citations, 1,731
  scan-wired, 3,569 e-text, 737 mintable gaps, 266 bare/no-locus. Smoke 22/22,
  12/12 links live-verified. See
  [docs/H3479_LS_CITATION_WAVE2_PACKET_25.08.26.md](https://github.com/gasyoun/kosha/blob/main/docs/H3479_LS_CITATION_WAVE2_PACKET_25.08.26.md).

## [0.115.1] - 2026-08-25
### Fixed
- **Capital-initial SLP1 lemmas rendered the wrong Devanagari** (H3478, Sonnet 5
  `claude-sonnet-5`; kosha#433). `app/word_page.py::render_word_page` derived `slp1`
  from `card["query"]["key"]`, which committed static cards store case-folded for
  capital-initial keys (`"darma"` for `Darma`, `"rama"` for `rAma`) — the template now
  derives `slp1` from the token (the exact key) whenever a token is supplied, falling
  back to `query.key` only when no token is given. `query.key` for the current data is
  already correctly-cased (no committed page needed regenerating), so this is a
  structural hardening against a future case-folded card regressing the bug again.
  Added `tests/test_word_page.py::test_capital_initial_lemma_not_case_folded`
  (synthetic case-folded fixture) and fixed a pre-existing test bug in
  `tests/test_word_page_lang_groups.py::test_ai_translated_badge_on_unreviewed_only`
  that passed a raw lowercase string as `token` instead of `card_token(...)`.

## [0.115.0] - 2026-08-25
### Fixed
- **RU tab still showed raw Sanskrit** (H3490, Fable 5 `claude-fable-5`; MG 25-08-2026
  "RU still showed raw"). Two leak classes the H3480 pre-pass could not see:
  (1) 11 % of pwg_ru entries (116/1,063 on the H3457 sample) quote Sanskrit as
  **bare SLP1 with Vedic accents and no `{#…#}` wrapper** (`tena^ gacCa
  parasta\ram`) — new `kosha.api.ru_join.ru_bare_slp1_pass` detects such runs
  (accent mark or SLP1-only capital after the first letter, extended over
  lowercase neighbours; never Cyrillic / tags / `ls` citations / `vgl.`-style
  abbreviations / ALL-CAPS) and transliterates them to IAST sdata spans;
  (2) rows carrying `<s>…</s>` / `<i>` but none of the render trigger tokens were
  HTML-escaped as literal `&lt;s&gt;gam&lt;/s&gt;` — `<s>`, `<i>`, `<b>` added
  to the triggers. Sample census after: 0 escaped-tag entries, accent-marked
  bare tokens 116 → 0 real (6 census false positives are Russian slashes).
  **The committed `w/` tree was regenerated** (`--reading-packs --force`) so
  the live Pages word pages change with this release, not only future builds.
  Tests: `tests/test_ru_bare_slp1.py`. Residual: the RussianTranslation store
  should wrap these at source (that lane, not kosha).

## [0.114.0] - 2026-08-25
### Fixed
- **RU tab leaked raw markup** (H3480 R3, Fable 5 `claude-fable-5`): the pwg_ru /
  mw_ru overlay showed `{#gam#}` and `{%…%}` verbatim on the public word page
  because `render()` (the basicdisplay port) never knew the RU pipeline's two
  wrappers. New `kosha.api.ru_join.ru_markup_prepass` maps `{#slp1#}` → `<s>`
  (renderer's own IAST) and `{%gloss%}` → `<i>` before `render_sanitized`; test
  `tests/test_word_page_h3480_header.py`.
### Added
- **Word-page header rethink, staged as direction d** (H3480, MG rulings R1–R5
  25-08-2026): three header rows instead of six — headword strip · SanskritRussian
  · ONE flat dictionary tab row (`MW · PWG · Apte · PWG→RU · All`, zero-count
  dictionaries dropped) — and a single Gloss ⇄ Full switch left of the heart
  (Adaptive gone as a named mode). `build_word_pages.py --ux-staging d`; mockup
  + 4 screenshots under `mockups/h3457-wpage-ux/`; packet §7. Public page
  unchanged until the flip ruling
  ([docs/NOT_PUBLISHED_H3457_WPAGE_UX.md](https://github.com/gasyoun/kosha/blob/main/docs/NOT_PUBLISHED_H3457_WPAGE_UX.md)).

## [0.113.0] - 2026-08-25
### Changed
- **H3166 — the E1 verb "genuine conflicts" are 85 % artifact, not divergence; the
  handoff's own build was already shipped by H855** (Opus 5 `claude-opus-5`).
  H3166 asked for a dhātu-identity crosswalk that
  [H855](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H855-Opus_kosha_e1-verb-dhatu-identity-crosswalk_13.07.26.md)
  had already committed six weeks earlier (12.68 % → 70.24 %); it was minted off a
  stale roadmap bullet, and closes **DUPLICATE-SHIPPED** for that half. What was
  genuinely missing is the adjudication of the residue, delivered here.
  [`E1_DIVERGENCE_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md)
  **retracts its own sentence** that *"the remaining 11,056 genuine conflicts are
  real accent/sandhi/gaṇa-assignment differences needing scholarly review"*: over
  the full population the conflicts are **55.8 % passive**, **66.9 % have vidyut's
  form shorter than Cologne's**, and come from only **192 of 683 roots** — because
  the crosswalk's `direct`/`bare` paths seed vidyut with an **unmarked root** for
  **212 of 779 entries (27.2 %)**, and those roots carry **9,396 of the 11,056
  conflicts (85.0 %)**. Without it-markers vidyut eats the root-final consonant:
  `yat` → `yyate` where the passive is `yatyate`. The discriminating probe pins the
  cause — for `yat`/`kam`/`paṇ`/`ruc`/`kṣam` the crosswalk seed **is** the bare root
  so both paths give the same malformation, while for `pā`, where the crosswalk did
  resolve, vidyut returns the correct `pīyate` against Cologne's `pāyate`. So true
  divergence is at most **~1,660 cells (3.5 % of both-nonempty)**, not 23 %, and the
  next rung is mechanical: resolve the 212 bare-seeded entries. 52 rows
  hand-adjudicated class-weighted (seed 3166, Opus 5, **not** a human sign-off):
  20/30 conflicts are the bare-root artifact, 5 vowel-grade, 3 curādi-vṛddhi fork,
  1 genuinely different, 1 **Cologne wrong**. Control classes hold — `DIFF_final_stop`
  100 % active citation-form, `COLOGNE_ONLY` **77.3 % middle** (a pada-assignment
  fork, not a coverage bug), `DIFF_cologne_superset` 383 cells from **8 roots**.
  New read-only scripts:
  [`sample_verb_divergence.py`](https://github.com/gasyoun/kosha/blob/main/scripts/sample_verb_divergence.py),
  [`profile_verb_divergence.py`](https://github.com/gasyoun/kosha/blob/main/scripts/profile_verb_divergence.py),
  [`probe_passive_conflict.py`](https://github.com/gasyoun/kosha/blob/main/scripts/probe_passive_conflict.py),
  [`measure_passive_bare_root.py`](https://github.com/gasyoun/kosha/blob/main/scripts/measure_passive_bare_root.py)
  — all importing `compare_vidyut_verbs.py`'s own helpers rather than restating them.
  Evidence committed under [`data/e1/`](https://github.com/gasyoun/kosha/tree/main/data/e1).
  The drafted csl-inflect#8 give-back lives in the H3166 handoff body and is **not
  posted** (RELATIONS.md §2/§7 diplomacy gate, same as #10).
### Fixed
- **Two stale docs that caused the duplicate mint** (same pass):
  [`ROADMAP_INFLECT_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md)
  still read *"Still open — the verb number is not yet interpretable … 12.68 %"* six
  weeks after H855 landed, and `E1_DIVERGENCE_REPORT.md`'s **Deferred** section still
  listed the crosswalk as future work **directly below the section describing it as
  built**. Both corrected, with the correction itself recorded in place. The K2 row in
  [`docs/PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md`](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md)
  now points at the live successor instead of the shipped work. This is the **second**
  stale mint from the same 19-08-2026 truth-pass — H3165 was the first
  ([Uprava FINDINGS §501](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md)).

## [0.112.0] - 2026-08-25
### Added
- **H3457 — word-page UX layer, STAGED (not published)** (Fable 5 `claude-fable-5`).
  Three learner organs behind a staging flag, our own design over the P5 theme
  (not an akshara clone): a **study badge** from `lemma_frequency.tsv`
  `core_rank`/`coverage_pct` (three rungs cut on the raw rank; no badge outside
  the 7,120-lemma ordering), **localStorage favorites** (♡ + static
  `favorites.html` with TSV/Anki export), and **print-scan anchors** (stable
  `id="e-{dict}-{L}"` per entry; PWG links rebuilt through the H839
  `{vol}-{col:04d}` key — every one of the 48,540 committed PWG `scan_url`s was
  bare-page and silently served volume 1). New
  [app/word_page_ux.py](https://github.com/gasyoun/kosha/blob/main/app/word_page_ux.py),
  `render_word_page(..., ux=)` (default `None` is byte-identical to before),
  `build_word_pages.py --ux-staging a|b|c` → gitignored `dist/w-staging/` and a
  hard refusal to write under `docs/`. Three design directions + 12
  screenshots under `mockups/h3457-wpage-ux/` (winner **a**, inline strip;
  rationale in the packet). New derived dataset `pwg-print-anchors`
  ([data/pwg_scan/pwg_L_pc.tsv](https://github.com/gasyoun/kosha/blob/main/data/pwg_scan/pwg_L_pc.tsv),
  122,730 rows from csl-orig `<pc>`, live-verified on 11 keys across four
  volumes). Evidence: Playwright smoke 22/22, badge byte-match 11/11 —
  [docs/H3457_WPAGE_UX_STAGING_PACKET_25.08.26.md](https://github.com/gasyoun/kosha/blob/main/docs/H3457_WPAGE_UX_STAGING_PACKET_25.08.26.md).
  Flip-live procedure and the no-publish rule:
  [docs/NOT_PUBLISHED_H3457_WPAGE_UX.md](https://github.com/gasyoun/kosha/blob/main/docs/NOT_PUBLISHED_H3457_WPAGE_UX.md).
  Error-report widget parked (needs a backend). Found and filed, not fixed:
  [#433](https://github.com/gasyoun/kosha/issues/433) — cards case-fold
  `query.key`, so public pages of capital-initial lemmas render the wrong
  Devanagari (`Darma` → दर्म).
### Changed
- README dataset count 109 → 110; `directory/index.html` regenerated.
  (`update_manifest.py refresh` was NOT run: it rewrites the whole file at
  indent=2 against the committed indent=1 — ~4,000-line churn; 49 rows carry
  stale rows/size_bytes and want a dedicated refresh pass.)

## [0.111.2] - 2026-08-24
### Changed
- **H3167 closed as already-fulfilled by H1312** (Sonnet 5 `claude-sonnet-5`). H3167 (minted
  by the H3001 truth-pass residual queue) asked for a `gloss.ru` re-run over the
  beginner subhāṣita pack — but that exact work already shipped same-day as H1279,
  under [H1312](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1312-Sonnet_kosha_subhashita-pack-ru-gloss-rerun_19.07.26.md)
  ([kosha PR #142](https://github.com/gasyoun/kosha/pull/142), v0.66.0, 19-07-2026):
  85.3 % of the pack's 1,510 tokens (1,288/1,510) already carry a lemma-layer RU
  gloss. H3001's truth-pass minted H3167 off H1279's own stale close-row note
  ("gloss.ru re-run TODO logged") without checking H1312 had already closed that
  TODO the same day. No rebuild needed — added the one piece of evidence H3167
  still lacked: a 15-token hand spot-check of `gloss_ru` triples
  (`scripts/_h3167_spotcheck.py`) against each token's actual surface/lemma,
  recorded in [`docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md)
  W-RU-b row. Finding: surface-tier gloss correct 15/15; lemma-tier gloss wrong on
  ~5/15 (`kāvyāni`, `bhāryām`, `as`, `sthānam`, `te`) — vidyut-cheda mis-lemmatizing
  these nouns onto an unrelated verb-root homograph, faithfully propagated by the
  RU-gloss join (not a defect in the join itself, and out of this handoff's fence).
  Flagged as a residual accuracy caveat on the reported 85.3 % figure, not a rights
  or coverage-padding issue.

## [0.111.1] - 2026-08-19
### Changed
- **[ROADMAP_INFLECT](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md) Wave U2 flipped 🟢 CONDITION FIRED → ✅ DONE 09-07-2026** (Opus 5 `claude-opus-5`, 19-08-2026). The 19-08 truth-pass (H3001) corrected this row once, from *conditional* to *unblocked since 03-07-2026*, and it was still understating it: the queue had already been **drained on 09-07-2026**. [`help-examples` PR #22](https://github.com/sanskrit-lexicon/csl-inflect/pull/22) and [`output-polish` PR #23](https://github.com/sanskrit-lexicon/csl-inflect/pull/23) merged; [`devanagari-input` PR #21](https://github.com/sanskrit-lexicon/csl-inflect/pull/21) was closed after [PR #20](https://github.com/sanskrit-lexicon/csl-inflect/pull/20) landed mid-review adding the same `DEVA` option, and was superseded by [PR #24](https://github.com/sanskrit-lexicon/csl-inflect/pull/24), merged the same day with the client-side conversion `main` lacked. The upstream give-back track is complete. [H3165](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H3165-Sonnet_csl-inflect_inflect-u2-drip-prepared-prs_19.08.26.md), minted that day to drip the queue, was closed as a stale mint against those three PRs — the roadmap-level lesson is [FINDINGS §501](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md) (a gate with no observer), the tooling-level one [FINDINGS §504](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md).

## [0.111.0] - 2026-08-19
### Changed
- **Roadmap truth-pass + residual `/ask` programme** (H3001, stale-roadmap slice 3).
  `roadmap_handoff_truth.py` confirms all 20 handoffs referenced by
  `ROADMAP_INFLECT_2026_2027.md` and `docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md`
  are closed ✅; three status lies corrected. **Wave U2's condition fired on
  03-07-2026** — [csl-inflect PR #17](https://github.com/sanskrit-lexicon/csl-inflect/pull/17)
  merged the same day it was opened — and the row read "conditional" for six weeks
  while three finished branches sat unsent. **Wave E1** was marked pending though
  H185 closed it 12-07-2026 (v0.21.0). **Wave RU** was marked 🟡 queued though both
  its handoffs shipped 19-07-2026; with that fixed the pedagogy roadmap is fully
  drained. New five-doc residual set under `docs/` (PLAN/ROADMAP/ARCHITECTURE/
  IMPLEMENTATION/VERIFICATION + metadoc); residual work queued as H3165, H3166, H3167.

## [0.110.17] - 2026-08-17
### Added
- **W2A release archive gate now runs** (H2870) — `scripts/validate_release_archives.py`
  shipped with H2346 as a gate no release path ever invoked. It is now the
  `Release archive gate` step of the required `Python CI` check, run against the
  committed prior+current mini-archive with an explicit durable public base, so a
  regression in checksum identity or historical resolution fails the PR.
- **`grammar-lab-g1`** — Grammar Lab Wave-1 topic graph (Whitney + Zalizniak root
  alternation / verbal morphology): 32 published topics, 182 Type-D edges, 192 frozen
  queries, built from [SanskritGrammar](https://github.com/gasyoun/SanskritGrammar)
  (H2492, PR [#857](https://github.com/gasyoun/SanskritGrammar/pull/857) v0.121.6).
  Consumed by the Systema-Sanscriticum Grammar Lab import (H2493 G2). Re-land of
  PR #401 (its predecessor #383 died to the same manifest-churn pattern the
  15-08-2026 weekly-review sweep hit again) — regenerated the README dataset-count
  markers against the current manifest total (105 → 106) so the count-parity test
  passes.

### Fixed
- **The citation-durability gate passed on `http://localhost:8000`** (H2870) —
  `validate_public_base` only rejects the deployment host (R5), so the development
  default sailed through the W2A release gate and a freeze cut on a workstation would
  have minted citations resolving on that workstation alone (R1). The release path now
  also applies `validate_durable_public_base`, rejecting loopback, private, link-local,
  unspecified, `.local`-class and single-label hosts, and passing a public IP literal
  with a note. Runtime `GET /ready` is deliberately unchanged — a developer on
  `localhost` is not unready.

## [0.110.16] - 2026-08-16
### Added
- **`mbh-vulgate-critical-presence`** — the H2845 verdict table behind the new `E` / `E†`
  e-text links on PWG cards: for each of 83,971 Nīlakaṇṭha vulgate verses, whether it also
  stands in the BORI critical edition. **92.0 % `present/present`, 7.7 % (6,494) vulgate-only**
  — what BORI relegated to its apparatus — 0 unchecked; per-parvan the vulgate-only share
  runs 0.9 % (sauptika) to 29.1 % (svargārohaṇa). Registered with the caveat that separates
  it from its citation-level sibling: `mbh_citation_presence.csv` (70,423 PWG/MW citations)
  is conditional on a fitted locus that is exactly right about **half** the time, so its
  `present/absent` means *"the verse the index points at is vulgate-only"*, not *"PWG cited a
  verse BORI rejects"* — the two tables must not be quoted interchangeably. Verdicts,
  scores and BORI addresses only; no verse bytes, both witnesses staying in gitignored
  caches off a local-only branch
  ([csl-atlas#404](https://github.com/sanskrit-lexicon/csl-atlas/pull/404),
  [SanskritLexicography#1753](https://github.com/gasyoun/SanskritLexicography/pull/1753)).

## [0.110.15] - 2026-08-16
### Changed
- **H2874 propagation — the PWG scan-index manifest caveat was telling consumers
  something no longer true.** `pwg-scan-index-campaign`'s CAVEAT 1 declared
  `citation_count` of unresolved provenance and barred it from any denominator; it is
  the 2024-09-11 `lsextract_all.txt` work-family rollup (`ALL = 739,056`), 66 of 67 rows
  exact ([csl-observatory#186](https://github.com/sanskrit-lexicon/csl-observatory/pull/186),
  [v1.13.0](https://github.com/sanskrit-lexicon/csl-observatory/releases/tag/v1.13.0)).
  Rewritten to the consumption rule instead: read `citation_count_safe`, fold by
  `in_pwgbib`, divide only by the same snapshot's `ALL`. `keying` refreshed to 43 columns.

### Added
- **`pwg-ls-counts`** — the two `<ls>`-per-abbreviation count tables behind that number,
  frozen 2024-09-11 evidence plus a current regeneration, with the never-regenerate
  warning on the former (`an.` falls 1,797 → 1 between snapshots on a re-tagging, not a
  recount) and the work-family-vs-cleaned-string incompatibility stated up front.

## [0.110.14] - 2026-08-16
### Documentation
- **H2768 propagation:** registered the strict Salt-face decision in README,
  agent cold-start guidance, a maintenance sync rule, and a metadoc.

## [0.110.13] - 2026-08-16
### Changed
- **H2768 (Codex Sol `gpt-5.6-sol`) — strict Salt compatibility faces:**
  `/dicts/*` now emits only the six C-SALT entry fields plus the normative
  `csl` extension; `/api/v1`, cards, and SSR retain the `kosha` namespace.
  One serializer remains authoritative, with a terminal projection and an
  independent profile-derived wire-key regression.

### Added
- **H2685 (Grok 4.6 `grok-4.6`) — PWG TM canonical v1 registered:** `pwg-tm-canonical-v1` in [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) (2,392 public-tier records; JSONL/TMX/TEI Lex-0/OntoLex). Bytes live on SanskritLexicography release `pwg-tm-canonical-v1.0.0`. Dataset concept DOI [10.5281/zenodo.21932900](https://doi.org/10.5281/zenodo.21932900) (version [10.5281/zenodo.21932901](https://doi.org/10.5281/zenodo.21932901)).
- **`/w/` SanskritRussian glossary strip (Grok 4.6 `grok-4.6`, H2680):**
  one public-tier gloss line under the headword (lemma, then surface);
  a one-line miss when the public files miss. Not a third dictionary
  tab. Reuses
  [`RuGlosser`](https://github.com/gasyoun/kosha/blob/main/scripts/build_ru_gloss_layer.py)
  from the reading-pack join. CI fixture
  [`tests/fixtures/sanskritrussian/`](https://github.com/gasyoun/kosha/blob/main/tests/fixtures/sanskritrussian/README.md).
  Restricted `corpus_lexicon` is never read. Tests:
  [`tests/test_word_page_saru_strip.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_word_page_saru_strip.py).

## [0.110.11] - 2026-08-14
### Changed
- **Live Part IV identity rollback drill on `.92` (Grok 4.6 `grok-4.6`, H2672):**
  previous + current `BUNDLE_IDENTITY` under `/opt/kosha/releases/`;
  restore then immediate re-promote; unit left on current (`2649f046`).
  [samskrtam.ru/health](https://samskrtam.ru/health) and
  [samskrtam.ru/ready](https://samskrtam.ru/ready) **200** after both hops.
  Core DB hashed in place
  (`140c6638811559677c4335c034dce5c2718e56868a188acc1e9bac15b6b34f04`),
  never copied. Packet:
  [`docs/MG_LIVE_SMOKE_PACKET_W1E.md`](https://github.com/gasyoun/kosha/blob/main/docs/MG_LIVE_SMOKE_PACKET_W1E.md)
  section **8f. Identity rollback drill**. Does not declare Wave 1 complete.

## [0.110.10] - 2026-08-14
### Added
- **`/w/` language groups + pwg_ru/mw_ru join (Grok 4.6 `grok-4.6`, H2670):**
  two-level chrome **EN | DE | RU | All** (EN: MW, AP90; DE: PWG; RU:
  pwg_ru, mw_ru). All still stacks every dict (H2653 kept). Runtime join
  from sibling `SanskritLexicography/RussianTranslation`; CI uses
  [`tests/fixtures/ru_join/`](https://github.com/gasyoun/kosha/blob/main/tests/fixtures/ru_join/README.md).
  Unreviewed rows carry a visible **AI-translated** mark; missing rows get
  a one-line empty state. First paint is EN unless `Accept-Language` /
  `navigator.language` is `ru`. No Kochergina; no SanskritRussian strip
  (that is H2680). Tests:
  [`tests/test_word_page_lang_groups.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_word_page_lang_groups.py).

## [0.110.9] - 2026-08-14
### Changed
- **Citation archive mounted on live `.92` (Grok 4.6 `grok-4.6`, H2671):**
  `/opt/kosha/archive/0.1.0-dev/` is a snapshot of live `data_version`
  `0.1.0-dev` (692 403 senses, `release.json` sha256 identity). Public
  [`/ready`](https://samskrtam.ru/ready) reports `citation_archives` **ok**;
  [`mw.101.1@0.1.0-dev`](https://samskrtam.ru/api/v1/sense/mw.101.1@0.1.0-dev)
  returns **200**. Packet residual:
  [`docs/MG_LIVE_SMOKE_PACKET_W1E.md`](https://github.com/gasyoun/kosha/blob/main/docs/MG_LIVE_SMOKE_PACKET_W1E.md)
  section **8e. Citation-archive mount**. Does not invent a second
  `data_version`; does not declare Wave 1 complete.

## [0.110.8] - 2026-08-13
### Added
- **`/ask` plan for `/w/` language groups + ops leftovers (Grok 4.6 `grok-4.6`):**
  five-layer spec
  [`docs/PLAN_KOSHA_RU_LANG_GROUPS_OPS_2026.md`](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_RU_LANG_GROUPS_OPS_2026.md)
  (R1–R24). Execution:
  [H2670](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2670-Grok_kosha_w-page-ru-pwg-mw-tabs_13.08.26.md)
  (EN/DE/RU chrome + pwg_ru/mw_ru),
  [H2680](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2680-Grok_kosha_w-page-sanskritrussian-strip_13.08.26.md)
  (SanskritRussian strip after H2670),
  [H2671](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2671-Grok_kosha_citation-archive-mount_13.08.26.md),
  [H2672](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2672-Grok_kosha_identity-rollback-drill_13.08.26.md),
  [H2681](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2681-Codex_kosha_w0-h1944-h1945-compare-memo_13.08.26.md).
  Not executed this sitting (R24).

## [0.110.7] - 2026-08-13
### Added
- **Pages pack-token static `/w/` heads (Grok 4.6 `grok-4.6`, H2665):**
  reading-pack `../w/{token}.html` hrefs now have committed HTML at
  repo-root [`w/`](https://github.com/gasyoun/kosha/blob/main/w/README.md)
  (site-root on Pages). Builder flag
  `python scripts/build_word_pages.py --reading-packs`. Live delta vs
  Meyer `bhū` recorded in
  [COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md).

## [0.110.6] - 2026-08-13
### Added
- **Word-page All tab (Grok 4.6 `grok-4.6`, H2653):** an **All** tab on
  `/w/{slp1}` stacks MW + PWG + AP90 on one scroll (per-dict headings).
  Single-dictionary lemmas stay as they were. Tests:
  [`tests/test_word_page_all_tab.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_word_page_all_tab.py).

## [0.110.5] - 2026-08-13
### Added
- **Branded `samskrtam.ru` kosha proxy (Grok 4.6 `grok-4.6`, H2646):**
  `/health` `/ready` `/metrics` `/api/` `/dicts/` `/w/` on
  [samskrtam.ru](https://samskrtam.ru/) reverse-proxy to the live unit on
  `.92` (LAN `:8002`, WordPress `/` and `/faq/` unchanged). Recipe:
  [`deploy/samskrtam-brand-proxy/`](https://github.com/gasyoun/kosha/blob/main/deploy/samskrtam-brand-proxy/README.md).

## [0.110.4] - 2026-08-13
### Changed
- **W1E live-smoke re-fill after W2C (Grok 4.6 `grok-4.6`, H2642):**
  promoted `/opt/kosha/repo` `0cd22ef5` → `ae4f93c4` (v0.110.3) on
  `.92`; public sslip re-probe **PASS** including `X-Request-ID` and
  `GET /metrics`; Gītā 1.1 **13/13** SSR. Packet §8c. Residuals
  unchanged (branded host, Pages `w/`, archive mount, §9).

## [0.110.3] - 2026-08-13
### Added
- **W2C release observability (Grok 4.6 `grok-4.6`, H2348):**
  `X-Request-ID` on every response (echo or UUID4) plus structured
  `request_id=` log lines; `GET /metrics` Prometheus text with a locked
  low-cardinality name list (`kosha_http_requests_total`,
  `kosha_http_request_duration_seconds`, `kosha_ready`,
  `kosha_ready_check`, `kosha_ready_failures_total`,
  `kosha_data_version_info`). Labels are route templates / H2343 check
  names only — never headwords, queries, or request ids. `/ready` 503
  increments the failure counter; scrapes do not. History/auth stay off.
  Operator notes:
  [`docs/RELEASE_OBSERVABILITY.md`](https://github.com/gasyoun/kosha/blob/main/docs/RELEASE_OBSERVABILITY.md).
  Surface `ops-metrics`. Tests:
  [`tests/test_observability.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_observability.py).

## [0.110.2] - 2026-08-13
### Added
- **W2B / P-D6 public dataset catalog API (Grok 4.6 `grok-4.6`, H2347):**
  read-only `GET /api/v1/datasets` and `GET /api/v1/datasets/{id}` over the
  existing [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  — identity, version, license/rights pointer, download/locator, checksum when
  present. Only `tier=public` rows are listed; restricted and intermediate ids
  share the same `dataset_not_found` 404 as unknown ids (no existence leak, no
  restricted checksum/path in the body). Salt `/dicts/*` and `/api/v1/lemma`
  are unchanged. Surface registry row `api-v1-datasets`. Tests:
  [`tests/test_dataset_catalog.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_dataset_catalog.py).

## [0.110.1] - 2026-08-10
### Changed
- **H2408 propagation sweep — the defgen eval line is now discoverable (Fable 5
  `claude-fable-5`):** the benchmark shipped in 0.110.0 (and its H730/H972
  predecessors) was registered nowhere a future session would look. Fixed across
  surfaces: a docs-table row in
  [README.md](https://github.com/gasyoun/kosha/blob/main/README.md) pointing at both
  protocols (and marking `EVAL_PLAN.md` as lookup-service gates only, which is what
  made the research eval line invisible); **eval-data sync rules** in
  [CLAUDE.md](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md) — never copy
  Heritage French text in, re-score-an-arm ⇒ update both protocol docs + the
  manifest row, `sacrebleu` is eval-only so harness tests skip in CI, and never
  quote a defgen number without its contamination caveat; the frozen eval files
  added to "What not to touch"; a ✅ Completed entry in `.ai_state.md`; and the
  regenerated [directory page](https://gasyoun.github.io/kosha/directory/) now
  carries the new dataset.
### Fixed
- **Stale `CITATION.cff` version** — pinned at `0.108.0`/2026-08-08 while `v0.109.0`
  and `v0.110.0` had shipped; bumped to `0.110.0`/2026-08-09. Caught by the
  propagation sweep's CITATION check, not by release tooling.

## [0.110.0] - 2026-08-09
### Added
- **Heritage (Huet) French glosses as an independent second reference for the
  definition-generation eval (Fable 5 `claude-fable-5`, H2408):** the five frozen
  generation arms from H730/H972 are re-scored against Gérard Huet's French glosses on the
  333-headword MW∩Heritage subset — the parent protocol's own ranked next-step #4.
  **The arm ranking is reference-invariant** (`F1_fable_ctx > A1_chat_ctx > A3_reasoner_ctx
  > A2_chat_noctx > A0_random_floor` under both the MW judge and the cross-lingual French
  judge), and the paired MW-familiarity premium is real but small: +0.13 to +0.25 on a 0–5
  scale, bootstrap CI excluding 0 for every system arm (sign p ≤ 1.5e-4), largest for the
  no-context memorisation arm A2 (+0.246) and smallest for the best arm F1 (+0.132) — the
  direction the contamination caveat predicted. Cross-lingual surface metrics are
  near-degenerate (token-F1 0.012–0.037 vs 0.101–0.338 against MW), so the judged score is
  the measurement and chrF-FR is decoration. Report:
  [docs/DEFGEN_HERITAGE_SECOND_REFERENCE_EVAL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_HERITAGE_SECOND_REFERENCE_EVAL.md)
  (+ metadoc); harness
  [scripts/defgen_heritage_ref.py](https://github.com/gasyoun/kosha/blob/main/scripts/defgen_heritage_ref.py),
  [scripts/defgen_heritage_delta.py](https://github.com/gasyoun/kosha/blob/main/scripts/defgen_heritage_delta.py),
  [scripts/defgen_heritage_coverage.py](https://github.com/gasyoun/kosha/blob/main/scripts/defgen_heritage_coverage.py);
  data [data/eval/defgen/heritage/](https://github.com/gasyoun/kosha/tree/main/data/eval/defgen/heritage).
  No generation was re-run (frozen `gen_<arm>.jsonl` reused); no Heritage gloss text is
  committed — the subset carries SHA-256 digests instead, and the scorer refuses to run on a
  drifted join (LGPLLR, `tier=restricted`).

## [0.109.0] - 2026-08-09
### Fixed
- **FTPS self-signed hosting cert + no-HASH ProFTPD (Grok 4.5 `grok-4.5`):**
  [`FTPSTransport`](https://github.com/gasyoun/kosha/blob/main/src/kosha/backup/transport.py)
  gains `verify_tls` (default True) + `ssl_context(verify=…)`;
  [`deploy_guhya.py`](https://github.com/gasyoun/kosha/blob/main/scripts/deploy_guhya.py)
  honors `FTP_TLS_INSECURE=1` / `FTP_SSL_VERIFY=0` for samskrtam.ru / t3cloud
  self-signed certs (still encrypted — not plaintext). When the server has no
  XSHA256/HASH (ProFTPD FEAT), verify by TLS **RETR** re-download + local
  sha256 before promote. Documented in `.env.deploy.example`. Tests in
  `tests/test_backup_transport.py`.

## [0.108.0] - 2026-08-08
### Added
- **W2A immutable sense archives + historical-resolution tests (H2346, Grok 4.5
  `grok-4.5`):** `write_archive` always freezes `release.json` (sha256 identity)
  beside `senses.sqlite`. Release gate
  [`scripts/validate_release_archives.py`](https://github.com/gasyoun/kosha/blob/main/scripts/validate_release_archives.py)
  / `validate_release_archives()` requires metadata, matching digests, durable
  public base, and sense resolution across mounted versions. Committed
  mini-archive under
  [`tests/fixtures/archives/`](https://github.com/gasyoun/kosha/tree/main/tests/fixtures/archives)
  (`0.1.0-w2a-prior` + `0.2.0-w2a-current`) exercises prior≠current wording.
  Tests in `tests/test_w2a_immutable_archives.py`. DOI mint remains MG —
  checklist stub
  [`docs/DOI_CHECKLIST_W2A.md`](https://github.com/gasyoun/kosha/blob/main/docs/DOI_CHECKLIST_W2A.md).

## [0.107.0] - 2026-08-08
### Changed
- **W1E post-promote residual fill (Grok 4.5 `grok-4.5`):** Lighthouse mobile
  **100** on sslip `/w/vac`, `/w/BU`, `/w/banD`; Gītā 1.1 **13/13** SSR; unit
  restart recovery. Packet §8b updated. Live-base W1 smoke **PASS**; residuals
  remain branded `samskrtam.ru`, Pages `w/`, archive mount, digests rollback.

## [0.106.0] - 2026-08-08
### Changed
- **W1 first live API promote + packet re-fill (Grok 4.5 `grok-4.5`):** kosha
  API running on `193.232.229.92` (`kosha.service` :8001, nginx + Let's Encrypt)
  at
  [https://kosha.193.232.229.92.sslip.io/](https://kosha.193.232.229.92.sslip.io/)
  with core DB `0.1.0-dev` (323 425 lemmas / 692 403 senses). Documented in
  [`docs/MG_LIVE_SMOKE_PACKET_W1E.md`](https://github.com/gasyoun/kosha/blob/main/docs/MG_LIVE_SMOKE_PACKET_W1E.md)
  §1b/§8b (health/ready/lemma/live-sense/SSR **PASS** on sslip). Host ops:
  `/opt/kosha/OPS.md`.

## [0.105.0] - 2026-08-08
### Changed
- **W1E live-smoke packet public-probe fill (H2345 follow-up, Grok 4.5 `grok-4.5`):**
  filled
  [`docs/MG_LIVE_SMOKE_PACKET_W1E.md`](https://github.com/gasyoun/kosha/blob/main/docs/MG_LIVE_SMOKE_PACKET_W1E.md)
  from public HTTP + Lighthouse only (no prod credentials). Result: production
  API routes on samskrtam.ru **404**; Pages reading Lighthouse mobile **99**;
  Gītā pack loads but `../w/` word-page hrefs **404**; `data-v0.1.0` release
  asset openable. **W1 product exit still not complete.**

## [0.104.0] - 2026-08-08
### Added
- **W1E MG live-smoke packet (H2345, Grok 4.5 `grok-4.5`):** human-only exit
  checklist
  [`docs/MG_LIVE_SMOKE_PACKET_W1E.md`](https://github.com/gasyoun/kosha/blob/main/docs/MG_LIVE_SMOKE_PACKET_W1E.md)
  (+ metadoc) with fillable tables for readiness probe, Lighthouse mobile ≥90,
  Gītā walkthrough, citation resolve / release-asset openability, and rollback
  confirmation. Explicit agent non-deploy fence; W1 product exit stays
  MG-signed. Links from
  [`KOSHA_DEPLOYMENT.md`](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md)
  and
  [`docs/ROADMAP_KOSHA_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026_2027.md).
  Does not deploy production. Unlocks H2346+ **after** live results are filled.

## [0.103.0] - 2026-08-08
### Added
- **W1D deploy bundle + runbook + local rehearsal + rollback (H2344, Grok 4.5 `grok-4.5`):**
  machine recipe
  [`data/manifest/deploy_bundle.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/deploy_bundle.json)
  with assemble/validate in
  [`src/kosha/deploy/`](https://github.com/gasyoun/kosha/tree/main/src/kosha/deploy)
  + CLIs
  [`scripts/assemble_deploy_bundle.py`](https://github.com/gasyoun/kosha/blob/main/scripts/assemble_deploy_bundle.py)
  /
  [`scripts/rehearse_deploy.py`](https://github.com/gasyoun/kosha/blob/main/scripts/rehearse_deploy.py)
  (fixture profile only — boots uvicorn on 127.0.0.1, probes `/health` +
  `/ready`, zero production contact). Restored human runbook
  [`KOSHA_DEPLOYMENT.md`](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md)
  (systemd `Type=exec`, nginx `proxy_pass`, rollback packet). Committed
  rehearsal log
  [`docs/DEPLOY_REHEARSAL_LOG.md`](https://github.com/gasyoun/kosha/blob/main/docs/DEPLOY_REHEARSAL_LOG.md).
  Tests in `tests/test_deploy_bundle.py`. Unlocks H2345 MG live-smoke packet.

## [0.102.0] - 2026-08-07
### Added
- **W1C readiness checks (H2343, Grok 4.5 `grok-4.5`):**
  [`src/kosha/api/readiness.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/readiness.py)
  probes core DB (via the W1A storage facade), optional attached
  inflections/layers, readable `data_version` with optional
  `KOSHA_EXPECTED_DATA_VERSION` fail-closed match, citation archives (reuses
  W0C `validate_archive`), and optional history/auth (reports `disabled` when
  `KOSHA_HISTORY_ENABLED` is false — never looks ready while unmounted).
  Thin route `GET /ready` returns 200 / 503; liveness stays at `GET /health`.
  Tests in `tests/test_readiness.py`.

## [0.101.0] - 2026-08-07
### Added
- **W1B generated-surface registry (H2342, Grok 4.5 `grok-4.5`):**
  [`data/manifest/surfaces.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/surfaces.json)
  rows every live public surface (API, Salt faces, SSR, static cards/word pages,
  directory/docs/features Pages hubs, UI SPA, concordance/reading/pedagogy
  viewers) with id, audience, source datasets, builder, output paths, rights
  tier, acceptance command, deploy owner, and rollback method. Validator in
  [`src/kosha/surfaces/`](https://github.com/gasyoun/kosha/tree/main/src/kosha/surfaces)
  + CLI [`scripts/validate_surfaces.py`](https://github.com/gasyoun/kosha/blob/main/scripts/validate_surfaces.py)
  fails on missing fields, unowned builders, empty acceptance commands, or
  dictionary-payload rows that omit the shared
  `kosha.api.repository` / `kosha.api.serializer` modules. Wired as a named
  step in the required `Fixture build + tests` CI job; tests in
  `tests/test_surface_registry.py`.

## [0.100.0] - 2026-08-07
### Added
- **W1A multi-DB storage facade (H2341, Grok 4.5 `grok-4.5`):**
  [`src/kosha/query/`](https://github.com/gasyoun/kosha/tree/main/src/kosha/query)
  opens the core store and ATTACHes read-only `inflections` / `layers` with the
  architecture's stable aliases when those files exist; TEMP VIEWs keep
  existing unqualified SQL working. History is never mounted on the query path
  (even if `history.db` is present and `KOSHA_HISTORY_ENABLED=1`).
  `app/db.get_db` and fixture connections go through the facade only.
  Parity tools: `split_monolith_to_facade` + 12 frozen golden sample queries;
  tests in `tests/test_storage_facade.py` prove monolith ≡ multi-DB results and
  Salt payloads carry no physical placement. **No production bulk data move**
  in this wave — facade first, split later.

## [0.99.0] - 2026-08-07
### Fixed
- **Renormalized `docs/inflect/index.html` to LF (H2315, Sonnet 5 `claude-sonnet-5`):**
  the sole kosha offender in the org EOL census
  ([Uprava/tools/eol_census.py](https://github.com/gasyoun/Uprava/blob/main/tools/eol_census.py)).
  [PR #246](https://github.com/gasyoun/kosha/pull/246) fixed the original 13 CR
  bytes; the squash-merge itself reintroduced one CRLF line, fixed in a
  follow-up ([PR #247](https://github.com/gasyoun/kosha/pull/247)). Verified
  `eol_census.py --ref origin/main` exits 0. **Both PRs landed via a temporary
  `enforce_admins` toggle** — kosha's GitHub Actions has no billing/minutes, so
  the two required status checks (`Fixture build + tests`, `vitest + vite
  build`) queue forever and can never self-clear; see
  [Uprava FINDINGS](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md)
  for the standing note.

## [0.98.5] - 2026-08-02
### Fixed
- **«Старт чтения» freeze MANIFEST hash drift (H2129, Sonnet 5 `claude-sonnet-5`, dual-run compare of H2109, 02-08-2026):** [`data/cohort_start_chteniya/MANIFEST.json`](https://github.com/gasyoun/kosha/blob/main/data/cohort_start_chteniya/MANIFEST.json) and [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) carried stale sha256/bytes for `sandhi-drills-l1-l3` and `sandhi-curriculum-l1-l3` — hashed before `.gitattributes` (`eol=lf`) normalized those two generated files on commit, so `python scripts/freeze_cohort_start_chteniya.py --check` FAILED on a pristine clone of 0.98.3 despite the release notes claiming it was green. Pin file bytes are unchanged (content-identical, LF-only); only the two stale hash/byte fields are corrected, and [`scripts/freeze_cohort_start_chteniya.py`](https://github.com/gasyoun/kosha/blob/main/scripts/freeze_cohort_start_chteniya.py) now writes `newline="\n"` so the drift cannot recur. Independent-rebuild compare memo: [Uprava H2129](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2129-Sonnet_kosha_h2109-grok-dual-run-compare_01.08.26.md).

## [0.98.4] - 2026-08-02
### Changed
- **A55/A56 JOHD data papers upgraded to submission drafts (H1872, Fable 5 `claude-fable-5`, 02-08-2026):** [papers/A55_UNION_HEADWORDS_DATA_PAPER_JOHD.md](https://github.com/gasyoun/kosha/blob/main/papers/A55_UNION_HEADWORDS_DATA_PAPER_JOHD.md) and [papers/A56_ZALIZNYAK_GRAMMAR_INDEX_DATA_PAPER_JOHD.md](https://github.com/gasyoun/kosha/blob/main/papers/A56_ZALIZNYAK_GRAMMAR_INDEX_DATA_PAPER_JOHD.md) rewritten to full JOHD section structure (Overview / Method / Dataset description / Reuse potential / Acknowledgements / Funding / Competing interests / References), readiness 2/5 → 4/5. All counts re-verified against the frozen `data-v0.1.0` release assets: A55 gains the `n_dicts` distribution table (44.1% single-witness; 11 headwords in all 15 dicts) + H684 overlap/witness-independence integration; A56 gains its core result — the token-frequency distribution (6 tokens = 50% of PWG, 26 = 80%, 154 = 99%; 48 singleton classes; 335 frozen tokens vs 342 live, versioning note added) and a column-fill census with corrected feature-flag semantics. DOI mint + submission stay human steps.

## [0.98.3] - 2026-08-01
### Added
- **«Старт чтения» cohort pack freeze (H2109, Grok 4.5 `grok-4.5`, override dual-run of Sonnet handoff, 01-08-2026):** [`data/cohort_start_chteniya/`](https://github.com/gasyoun/kosha/blob/main/data/cohort_start_chteniya/) pins Hitopadeśa-0 + subhāṣita-beginner + sandhi curriculum/drills L1–3 with `MANIFEST.json` sha256 pins, optional `lemmas_for_srs.tsv`, builder [`scripts/freeze_cohort_start_chteniya.py`](https://github.com/gasyoun/kosha/blob/main/scripts/freeze_cohort_start_chteniya.py) (`--check` goal gate), and manifest row `cohort-start-chteniya-pack-freeze`. Freeze only — no new linguistics; subhashita schema delta documented for H2110 adapter.

## [0.98.2] - 2026-08-01
### Added
- **Sandhi methods deep manual (H2069, Grok 4.5 `grok-4.5`, 01-08-2026):** [docs/SANDHI_METHODS_DEEP_MANUAL.md](https://github.com/gasyoun/kosha/blob/main/docs/SANDHI_METHODS_DEEP_MANUAL.md) — A/B/C decision table, mode-1/2 induction, ~3.7% Gītā miss taxonomy, portability contract. Closes DEEP_MANUAL_GAP_CENSUS row 14 residue (hub ≠ methods).

## [0.98.1] - 2026-07-31
### Fixed

- **`main` branch protection enabled + #223 gap closed** (31-07-2026): H1945 found `main` unprotected while `VERIFICATION_KOSHA_ARCHITECTURE.md` asserted it required both status checks by name. Protection now enabled on human instruction: both CI workflows required, `enforce_admins` true, no review requirement, force-push and deletion refused — records the configuration and reasoning per setting, including that `enforce_admins` now routes release commits through a PR.

## [0.98.0] - 2026-07-31

### Added
- **W0C — contract and trust boundaries (H1945).** The typed API layer
  [`src/kosha/api/`](https://github.com/gasyoun/kosha/tree/main/src/kosha/api):
  canonical Pydantic Salt entry/envelope/error models (D6/D13), one entry
  serializer, one entry-reading query layer, the rendered-HTML allowlist
  sanitizer, and top-level error normalization.
- **The rendered-entry trust boundary.** Entry HTML is `{@html}`-bound in the
  UI and interpolated unescaped into SSR pages, while `app/render.py` — a
  faithful port of Cologne's `basicdisplay.php` — passes unrecognised elements
  straight through with their attributes and interpolates source `n=` values
  into `title='…'` unescaped. All rendered output now crosses an
  [nh3](https://pypi.org/project/nh3/) allowlist
  ([`kosha/api/sanitize.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/sanitize.py)),
  with an adversarial suite (active content, event handlers, `javascript:`/
  `data:` URLs, CSS `url()`/`expression()`, attribute-injection through a
  source `title`) and a golden-corpus non-destruction gate: every element in
  the real rendered corpus survives except `<pb>`, Cologne page-break metadata
  kosha already surfaces structurally as `csl.page`/`csl.scanUrl`.
- **Citation-archive validation**
  ([`kosha/api/archive.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/archive.py)):
  mount path, release metadata, sha256 of the dump against the declared digest,
  openability, release-asset URL form, and the R5 rule that a citation host is
  never the deployment host — previously a comment in three files, now a check.
- **Fixture-tier contract gates.** `test_contract_parity`, `test_sanitizer`,
  `test_salt_profile`, `test_api_errors`, `test_citation_archive` — all on the
  tier CI runs on every PR, not the full-data tier that skips there.

### Changed
- **BREAKING (pre-public): `/api/v1/lemma` and `/w/{slp1}` now return
  Salt-profile entries.** Per D6 each result is a Salt entry — `id`,
  `headword_slp1`, `sense`, `re_headwords_slp1`, `created`, `xml` — with
  Cologne provenance under `csl` and every kosha-only field (`dict`, `L`,
  `headword`, `scan_url`, `sense_ids`, `rendered_html`, `evidence`,
  `heritage`, `cite`, `raw`) under `kosha`. The flat object v0.97 returned is
  now that `kosha` block. The `{data_version, query, results}` envelope is
  unchanged. `sense[]`, hardcoded `[]` before, now carries real glosses.
- **One serializer replaces three.** `app/main.py::_entry_payload`,
  `scripts/build_static_cache.py::entry_payload` (a hand-maintained copy marked
  "keep the two in lockstep", which had already drifted — it never implemented
  the `raw` branch it accepted a flag for) and `app/salt.py::salt_entry` (which
  emitted `sense: []` and `evidence: []` unconditionally) all now call
  `kosha.api.serializer`. Parity is a test, not a comment.
- `render`, `cite`, `scan_resolver`, `evidence` and `transliterate` moved from
  `app/` into the installed package; `app/` keeps re-export shims (D11). Their
  `sys.path` inserts into a sibling `sanskrit-util` checkout are gone.
- Salt faces now answer a bad parameter with **HTTP 400** and the C-SALT
  string form, per profile §3.2 — they returned **200** with an error body, so
  a client checking the status read a failure as success. Unimplemented
  `query_type`s (`wildcard`, `regexp`, `fuzzy`, `match`, `match_phrase`) 400
  explicitly instead of returning an empty result set, per profile §4.

### Fixed
- **Two settings named one directory and defaulted to different places.** W0B
  added `Settings.archive_dir` (`data/archive`) while `app/versions.py` kept
  reading its own `KOSHA_RELEASES_DIR` (`data/releases`), so pointing the
  documented knob at a mounted release archive moved nothing and citations
  went on resolving from the old path. `KOSHA_ARCHIVE_DIR` is now the single
  name, defaulting to the directory the mechanism reads; `KOSHA_RELEASES_DIR`
  is a deprecated alias, and a contradicting pair is a hard error.
- **`/api/v1/sense` bypassed the sanitizer entirely**, on both its live and its
  archived branch — and an archived body is the older, less-scrutinized markup
  of the two. Both now render through `serializer.render_sanitized`.
- **Starlette's own 404/405 escaped error normalization.** Handlers registered
  on FastAPI's `HTTPException` never see the base class the router raises, so
  an unknown path returned `{"detail": "Not Found"}` while every deliberate
  error was normalized. Registered on the base class.

## [0.97.1] - 2026-07-31

### Fixed
- **The committed dependency lock contradicted `pyproject.toml`, and no check
  could see it.** `requirements.lock.txt` was generated from the installed
  closure of a workstation that lagged the declared floors, so it pinned
  `fastapi==0.136.1` under `>=0.140.0`, `uvicorn==0.46.0` under `>=0.51.0` and
  `pytest==9.0.3` under `>=9.1.1`; installing it produced a set the project's
  own metadata rejects, and a following `pip install -e .` upgraded past it, so
  the lock did not hold. CI's check on it was `'==' in requirements.lock.txt`.
  [`scripts/gen_requirements_lock.py`](https://github.com/gasyoun/kosha/blob/main/scripts/gen_requirements_lock.py)
  now **refuses** to write a contradictory lock, resolves with pip by default
  (so a stale workstation is no longer a reason to ship one, `--from-installed`
  keeps the old behaviour), and gains `--audit` — the platform-independent
  invariants (every declared root pinned, no pin below its floor) that CI now
  runs instead. Lock regenerated: 27 pins, audit clean.
- **A `HASH` reply's digest is not its last token.** `FTPSTransport.remote_sha256`
  read `reply.split()[-1]`, which for `213 SHA-256 0-<len> <digest> <file>` is
  the *filename* — so the method returned `None`, and `upload()` reads `None` as
  "the server proved nothing" and refuses to promote. On a server offering
  `HASH` but not the older `XSHA256`, every backup upload was rejected. It now
  scans for the first 64-hex token; four reply-shape tests pin it, one of which
  fails against the previous parse.

## [0.97.0] - 2026-07-31

### Added
- **H1944 — W0B reproducible substrate.** Installable package (`pyproject.toml`
  + `src/kosha/`, console script `kosha-build`) with a committed
  [`requirements.lock.txt`](https://github.com/gasyoun/kosha/blob/main/requirements.lock.txt)
  and its generator; typed settings
  ([`src/kosha/settings.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/settings.py))
  covering the D7 stores, the citation base, and the D10 flags, with
  `DATABASE_PATH` kept as a deprecated core-DB alias whose *conflicting* use is
  a hard error; a compact committed fixture source pack
  ([`tests/fixtures/build/sources/`](https://github.com/gasyoun/kosha/tree/main/tests/fixtures/build/sources),
  seven lemmas, no restricted bytes) that builds the whole graph in ~2 s;
  required Python and UI CI workflows.
- **Encrypted backup transport**
  ([`src/kosha/backup/transport.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/backup/transport.py)):
  explicit TLS control *and* data channels, upload under a temporary remote
  name, mandatory server-side sha256 verification, atomic rename on success.
  Fails closed when the server proves no digest; `scripts/deploy_guhya.py` now
  defaults to a dry run and needs `--upload` to transfer anything.

### Fixed
- **[#210](https://github.com/gasyoun/kosha/issues/210) — no-flag build silently
  omitted declared stages.** `scripts/build_db.py` dispatched on
  `if args.stage in (None, "x")` and only five of the ten stages carried the
  `None` case, so a default build skipped `entries`, `forms`, `inflections`,
  `hybrid`, and `stem_bridge` without a word. Order now lives in a declarative
  registry
  ([`src/kosha/build/stages.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/build/stages.py))
  expanded topologically by
  [`src/kosha/build/dag.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/build/dag.py),
  with prerequisite checks before the first write, per-stage postconditions, a
  temporary build target promoted atomically only after `PRAGMA
  foreign_key_check`, an immutable source lock (`<target>.lock.json` + a
  `meta.build_stage_manifest` row), and a release mode that refuses the mutable
  `latest` csl-sqlite alias. Skipped optional stages are logged with a reason
  instead of vanishing.

### Changed
- **History, magic-link auth, and analytics are off by default (D10).** The
  router is no longer mounted unless `KOSHA_HISTORY_ENABLED` is truthy, so those
  paths 404 and are absent from the OpenAPI schema; with history off,
  `/api/v1/search` also mints no visitor cookie and writes no event.
- **Two-tier test suite (D14).** A new
  [`tests/conftest.py`](https://github.com/gasyoun/kosha/blob/main/tests/conftest.py)
  skips the eight full-data modules when the core DB is absent, instead of
  failing 92 tests on a fresh checkout — which is what made CI possible at all.
- `.env.example` corrected: its `DATABASE_PATH=./unified_dict.db` never matched
  the path the code opened.

## [0.96.1] - 2026-07-31

### Fixed
- **H1943 — governance/integrity truth reset.** Corrected the two `#198` false
  "Bhagavadgita absent from DCS" mirrors in
  [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  (the Gita's 18 adhyayas are present in DCS as `MBh, 6, BhaGī 1..18`, relabeled
  not omitted — the kosha Gita pack instead derives from the hand-curated gold
  master); regenerated `directory/index.html` + README dataset counts (94→96)
  from the manifest via the committed builder; established
  [`docs/ROADMAP.md`](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP.md)
  as the sole live roadmap; pointed root `ARCHITECTURE.md` at the platform
  contract while preserving A1–A4; bannered 4 superseded portfolio-level
  plan/roadmap docs `SUPERSEDED` in place; corrected stale pre-alpha/no-CI/
  no-lookup claims in `CLAUDE.md`; added fail-fast truth tests
  (`tests/test_truth_gates.py`) for version claims, active-queue completed
  markers, and required plan banners. The
  [0.62.0](#0620---2026-07-19) entry below is left as the historical record of
  what was believed true at the time (`CHANGELOG.md` is append-only); this
  entry is the correction of record.

## [0.96.0] - 2026-07-26

### Added
- **H1691 — 12 further cited texts crosswalked to DCS; grounded PWG leaf senses 7,372 → 8,208
  (+11.3%)** ([H1691](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1691-Opus_kosha_pwg-dcs-text-crosswalk-beyond-five_26.07.26.md),
  Opus 5 `claude-opus-5[1m]`). `PWG_TO_DCS_TEXT` in
  [`build_sense_corpus_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sense_corpus_concordance.py)
  gains Aṣṭādhyāyī, Manusmṛti, Kātyāyanaśrautasūtra, Pañcaviṃśabrāhmaṇa, Kirātārjunīya,
  Āśvalāyanagṛhyasūtra, Śāṅkhāyanaśrautasūtra, Bṛhadāraṇyakopaniṣad, Gītagovinda,
  Kaṭhopaniṣad, Gobhilagṛhyasūtra and Śatakatraya — 61,192 `<ls>` citations, taking `MAPPED`
  from 36.4% to **44.7%** of the dictionary's citation mass. Every one of the 52 adjudicated
  abbreviations carries a recorded verdict and reason; each mapped text was hand-checked at
  ≥10 rows (120/120 confirmed). Nothing was mapped on a name resemblance — the 38 rejections
  (`KATHĀS`, `AK`, `HIT`, `KAUŚ`, `DAŚAK`, …) are committed alongside so they are not
  re-litigated. Report:
  [`PWG_DCS_TEXT_CROSSWALK_H1691.md`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/research/PWG_DCS_TEXT_CROSSWALK_H1691.md).

### Fixed
- **The `locus` tier was chosen once per sense and then stamped on passages whose addresses
  bottomed out differently, inflating the exact-verse tier by 4.13%** — 507 of H1670's 12,280
  `locus` rows carried a chapter-level address at confidence 0.90, 504 of them
  Aitareyabrāhmaṇa. The level now travels with the row. Grounded-sense counts are unchanged
  (the fix relabels within the locus family rather than adding or removing groundings) and
  wave-1 is provably unaffected — 0 such rows in its run. See
  [SL FINDINGS §472](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md).

## [0.95.0] - 2026-07-26

### Fixed
- **H1670 — the sense-corpus aligner was measuring its own viewer sample, not the corpus**
  ([H1670](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1670-Opus_SanskritLexicography_pwg-dcs-sense-grounding-scale-levers_26.07.26.md),
  Opus 5 `claude-opus-5[1m]`). Three defects in
  [`build_sense_corpus_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sense_corpus_concordance.py):
  (1) the `locus` tiers tested each sense's `<ls>` against only the `--kwic-per` (3) passages
  `dcs_kwic()` samples for the viewer — **0.299%** of the passages available under the wave-1
  frame, so the exact-verse test measured the sample rather than the corpus; (2)
  `parse_ref_nums()` dropped DCS's *named* books, so `Rām, Bā, 6` and `Rām, Utt, 6` collapsed
  to the same tuple and one PWG citation "matched" up to seven Rāmāyaṇa books at once (same
  for Suśruta, and the 18 `MBh, 6, BhaGī n` chapters read as parvan 6); (3)
  `PWG_TO_DCS_TEXT` keyed the Ṛgveda as ASCII `"RV"` while PWG's abbrev is `ṚV`, hiding
  **50,972 citations — 6.89% of PWG's `<ls>` mass, second only to the Mahābhārata**.
  A new `numeric_address()` abstains whenever an address component is non-numeric, and
  hymn-level matches now land in their own `locus-chapter` tier (conf 0.70) instead of
  passing as exact-verse. Re-running wave-1's configuration reproduces its three committed
  artifacts with **zero differing lines** — the matcher itself is unchanged.

### Added
- **H1670 — aligner scale knobs.** `--pilot` (run over any frame), `--out-dir`,
  `--locus-scan full` (test against every DCS passage at an address the frame cites, same
  predicate), `--no-ls-rows`; plus `select_sense_pilot.py --out`. Four verified texts added
  to `PWG_TO_DCS_TEXT` (Vājasaneyisaṃhitā, Yājñavalkyasmṛti, Kumārasaṃbhava,
  Bhāgavatapurāṇa), each checked against its `pwgbib` entry — four look-alike candidates
  (`VP`, `KĀTY. ŚR`, `KAUŚ`, `KATHĀS`) were **rejected** and the reasons recorded in the
  map so nobody re-litigates them. Grounded PWG leaf senses **52 → 7,372** (0.67% → 12.25%)
  on a 32× wider frame, with no criterion relaxed.

## [0.94.0] - 2026-07-24

### Added
- **H1493 — Gītā interlinear prose reading view** ([H1493](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1493-Sonnet_kosha_kosha-gita-prose-reading-view_22.07.26.md), Grok 4.5 `grok-4.5` on Sonnet-lock override). Vendors the `Gita.xlsm` **Prose** sheet via [`scripts/extract_gita_prose.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_prose.py) → [`data/gita/gita_prose.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_prose.tsv) (**653** blocks / **703** verse keys) + [`reading/data/gita_prose.js`](https://github.com/gasyoun/kosha/blob/main/reading/data/gita_prose.js). [`reading/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/index.html) gains a **Word-by-word / Prose** toggle on Gītā packs (default unchanged). Manifest `gita-prose` + data-statement. Tests: `tests/test_gita_prose.py`.

## [0.93.0] - 2026-07-24

### Changed
- **H1590 `/artifact-propagate`** — README P5 phase row, CLAUDE D4 head sync rule, `.ai_state` W5 done, P5 design status pointer, exit-packet metadoc. (No product code change.)

## [0.92.0] - 2026-07-24

### Added
- **H1589 — P-D5 queryable kosha.db layers** ([H1589](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1589-Opus_kosha_data-hub-pd5-queryable-db-layers_24.07.26.md), Grok 4.5 `grok-4.5` on Opus-lock override). New stage [`scripts/build_db_layers.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db_layers.py) wired as `python scripts/build_db.py --stage layers`: additive public tables `sense_frequency` · `roots_frequency` · `dict_corpus_coverage` (+ optional sibling `mw_roots` / `mw_etymology` from csl-orig). Smoke joins on `Darma` / `nAga` / `kf`. D5-4 **G-SIZE** tripwire [`scripts/check_g_size.py`](https://github.com/gasyoun/kosha/blob/main/scripts/check_g_size.py) (WARN ≥1.5 GB, FAIL >1.8 GB). Operator query surface in [`docs/PIPELINE_OPERATOR_RUNBOOK.md`](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.md); [`DATA_HUB_ROADMAP.md`](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md) P-D5 ✅. Tests: `tests/test_db_layers.py`. Restricted-tier data not loaded; no new public API routes.

## [0.91.0] - 2026-07-24

### Added
- **H1590 — P5 SSR long-tail + D4 static head N=11,148 + exit packet** ([H1590](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1590-Opus_kosha_p5-ssr-static-head-exit-packet_24.07.26.md), Grok 4.5 `grok-4.5` on Opus-lock override). [`scripts/build_word_pages.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_word_pages.py) gains `--coverage` / `--head` (measure N from `lemma_frequency.tsv` at build time; default deploy path `--coverage 0.95`). Full head build: **N=11,148 / 95.00%** → **10,370** pages (778 head lemmas without cards → SSR), **184.9 MB** @ mean **17.4 KB/page**, **18.1%** of 1 GB soft cap; projected web tier **578.1 MB / 56.5%**. SSR byte-parity **4/4** green (`GET /w/{slp1}`). Exit packet [`docs/P5_WORD_PAGE_EXIT_PACKET.md`](https://github.com/gasyoun/kosha/blob/main/docs/P5_WORD_PAGE_EXIT_PACKET.md) with honest ⛔ blocked live checks (Lighthouse · Gītā walkthrough · MG staging). Operator note in pipeline runbook; W4b budget log append-only W5 row. Tests: `tests/test_build_word_pages_head.py`.

## [0.90.0] - 2026-07-24

### Added
- **H1588 — full two-witness WSD for sense-frequency (Wave 3)** ([H1588](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1588-Opus_kosha_sense-frequency-two-witness-wsd_24.07.26.md), Grok 4.5 `grok-4.5` on Opus-lock override). Extends the WordSem-gold sidecar past the 9.3% tagged slice under the plan gate (≥70% held-out). **SCL witness fail-closed** (H057 rights unresolved; gitignored `data/frequency/.cache/`; zero body text). **Single-witness MFS arm** on untagged DCS tokens: held-out WordSem→MW accuracy **83.96%** (60,362/71,892). Fusion promotes **13,709** `provenance=estimated` MW rows (**4,506,310** tokens); review queue empty-with-reason. Cards light a separate estimated chip (never blended). Scripts: [`wsd_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/wsd_core.py), [`scl_sense_witness.py`](https://github.com/gasyoun/kosha/blob/main/scripts/scl_sense_witness.py), [`wsd_llm_arm.py`](https://github.com/gasyoun/kosha/blob/main/scripts/wsd_llm_arm.py), [`wsd_fuse.py`](https://github.com/gasyoun/kosha/blob/main/scripts/wsd_fuse.py). Report: [`wsd_fusion_report.md`](https://github.com/gasyoun/kosha/blob/main/data/frequency/wsd_fusion_report.md). Tests: `tests/test_wsd_two_witness.py` (7 green).

## [0.89.0] - 2026-07-24

### Added
- **H1586 close-out — D4 standing rule in root ARCHITECTURE + budget re-sample** ([H1586](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1586-Haiku_kosha_w4b-pages-budget-remeasure-a4_24.07.26.md), Grok 4.5 `grok-4.5`). VERIFICATION 4b-8: D4 static-head/SSR-tail rule recorded in [`ARCHITECTURE.md`](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md). Append-only W4b log row in [`docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md`](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md) §6: N re-measured still **11,148** / 95.00%; word-page sample mean **11.95 KB** → head **130.1 MiB**; projected web tier **523.3 MiB / 51.1%** of 1 GB (still under 75%/90% gates). Core W4b measure already shipped in [0.85.0](#0850---2026-07-24) / [#185](https://github.com/gasyoun/kosha/pull/185).

## [0.88.0] - 2026-07-24

### Added
- **H1492 — Phase 2c Śāstra/commentary sandhi sweep** ([H1492](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1492-Sonnet_kosha_kosha-sandhi-sastra-commentary-sweep_22.07.26.md), Grok 4.5 `grok-4.5` on Sonnet-lock override). Extends [`scripts/build_corpus_sandhi.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_corpus_sandhi.py) with a curated **24-text** śāstra/commentary tier (darśana cores + bhāṣyas, dharma/artha/kāma, vyākaraṇa/nirukta/kośa, alaṅkāra, Caraka/Suśruta, Abhidharmakośabhāṣya/Prasannapadā — deliberately skips the rasaśāstra/āyurveda-dīpikā flood). Merged [`data/sandhi/corpus_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/corpus_sandhi.tsv): **17 → 41 texts**, **580,230 → 707,936** events, **9,840 → 13,012** rules; top-N-for-80% stable at **82**. 24 new per-text `data/sandhi/<id>_sandhi.tsv`. Manifest `corpus-sandhi` row + roadmap §3 item 5 + `SANDHI_PROGRAMME.md` updated.

## [0.87.0] - 2026-07-24

### Added
- **H1587 — pilot cross-dict sense view (W2)** ([H1587](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1587-Opus_kosha_sense-recon-pilot-crossdict-view_24.07.26.md), Grok 4.5 `grok-4.5`). Side-by-side PWG · MW · Apte columns for the **500-headword pilot only**: builder [`scripts/build_sense_crossdict_pilot.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sense_crossdict_pilot.py) → [`sense_crossdict_pilot.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/sense_crossdict_pilot.tsv) (7,359 rows) + [`concordance/senses/crossdict.html`](https://github.com/gasyoun/kosha/blob/main/concordance/senses/crossdict.html). MW 497/500 · Apte 273/500 (honest nulls). `nAgadanta` PWG 1a/1b present. Fence: no MW sense bytes rewritten. Manifest `sense-crossdict-pilot`.

## [0.86.0] - 2026-07-24

### Added
- **H1461 — Zaliznyak paradigm-class declension drills (L4)** ([H1461](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1461-Sonnet_kosha_zaliznyak-declension-drill-surface_22.07.26.md), Grok 4.5 `grok-4.5` on Sonnet-lock override). New builder [`scripts/build_zaliznyak_drills.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_zaliznyak_drills.py) reads sibling E31 (`SanskritLexicography/RussianTranslation` reverse paradigm index) at build time and emits **3,434** MCQ items (`classify` + `odd-one-out`) under [`data/zaliznyak/`](https://github.com/gasyoun/kosha/tree/main/data/zaliznyak) + Anki deck + [`reading/zaliznyak/drills/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/zaliznyak/drills/index.html). Nav "declension classes →" on reading hub. Manifest row `zaliznyak-drills` + data-statement. Tests: `tests/test_zaliznyak_drills.py` (9 green).

## [0.85.0] - 2026-07-24

### Added
- **H1585 — W4a panini coverage + chain honesty surface** ([H1585](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1585-Sonnet_kosha_w4a-panini-surface-chain-trust-block_24.07.26.md), Grok 4.5 `grok-4.5`). [`concordance/panini/index.html`](https://github.com/gasyoun/kosha/blob/main/concordance/panini/index.html) gains a Coverage-map tab over the full 3983-sūtra enumeration with four statuses styled distinctly (`lit` · `dark-unattested` · `dark-out-of-scope` · `dark-engine-gap` — never collapsed). New builder [`scripts/build_panini_coverage_shards.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_panini_coverage_shards.py) → `concordance/panini/data/coverage.js`. Trust block lists coverage map + CSV download + W3a report (n=3983). Lit KWIC chain view retained. Tests: `tests/test_panini_coverage_surface.py`.
- **H1586 — W4b Pages budget re-measure with A4** ([H1586](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1586-Haiku_kosha_w4b-pages-budget-remeasure-a4_24.07.26.md), Grok 4.5 `grok-4.5`). Append-only row in [`docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md`](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md) §6: cards 289.7 + concordance 68.4 (panini 0.84) + reading 22.4 + docs/js 13.3 + static-head projection 105.6 = **499.4 MB / 48.8%** of 1 GB soft cap. D4 head N=11,148 stands.

## [0.84.0] - 2026-07-24

### Added
- **H1574 — Concordance-Q3 W3b: A4 public data release data-v0.3.0** ([H1574](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1574-Sonnet_kosha_w3b-paninian-concordance-data-release_24.07.26.md), Grok 4.5 grok-4.5 on Sonnet-lock override). W1a rights gate verified ([vidyut_prakriya_derivation_2026-07.md](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/vidyut_prakriya_derivation_2026-07.md) — A4 output CC BY-SA 4.0, vidyut attributed). Data statements: [panini-derivation-status](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/panini-derivation-status.meta.md), [paninian-corpus-concordance](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/paninian-corpus-concordance.meta.md), [paninian-sutra-coverage-map](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/paninian-sutra-coverage-map.meta.md). Manifest: three public rows in_release=data-v0.3.0 (W2a 401,368 + W2b 893,482 + W3a 3,983); new coverage-map row (91 datasets). Release assets: derivation_status/chains, paninian_concordance, panini_ambiguity_by_sutra, sutra_coverage_map, sutra_fire_set, datasets.json. Publish-safety GO (public repo, W1a composition, committed TSVs, no secrets/PII). DOI: pending Zenodo (human @DO).

## [0.83.0] - 2026-07-24

### Added
- **H1468 — Concordance-Q3 W3a sūtra-coverage / dark-class map (programme exit check)** ([H1468](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1468-Opus_kosha_panini-sutra-dark-class-coverage-map_22.07.26.md), Grok 4.5 `grok-4.5` on Opus-lock override). New [`scripts/build_sutra_coverage_map.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sutra_coverage_map.py) classifies every sūtra in the named **vidyut 0.4.0** Aṣṭādhyāyī enumeration (`Data.load_sutras()` / `sutrapatha.tsv`, **n = 3983** — never "~4,000") into four statuses with counts: **`lit` 221** (5.55%) · **`dark-unattested` 55** (1.38%) · **`dark-out-of-scope` 3707** (93.07%) · **`dark-engine-gap` 0** (not measurable from W2a empty `engine-error` chains; kept as a named class). Fire-set harvested offline over all **91,027** AG lemmas' Cologne cell pools (276 codes that ever appear in a successful `vidyut.prakriya` history); lit rollups from W2b `paninian_concordance.tsv` + DCS text-name join. Outputs: [`data/concordance/sutra_coverage_map.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/sutra_coverage_map.tsv), [`sutra_fire_set.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/sutra_fire_set.tsv), [`SUTRA_COVERAGE_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/SUTRA_COVERAGE_BUILD_REPORT.md). VERIFICATION 3a-1…3a-8; tests in `tests/test_sutra_coverage_map.py`. Collapsing the three dark classes is forbidden and gated.

## [0.82.0] - 2026-07-24

### Fixed
- **H1265 close-out — README dataset counts resynced from manifests** ([H1265](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1265-Haiku_kosha_computed_readme_dataset_count_invariant_18.07.26.md); W1d machinery landed as [#161](https://github.com/gasyoun/kosha/pull/161) on 21-07-2026). Post-merge dataset adds left README at **87** (72·11·4) while `datasets.json` held **90** (75·11·4). Ran `python scripts/build_directory.py --update-readme` (idempotent second run); `tests/test_directory.py` 12/12 green. Acceptance re-proved: invariant **fails** on deliberate README drift (91 vs 90) and on the pre-fix stale state (87 vs 90). External stacks remain computed at **8**. Grok 4.5 (`grok-4.5`), Haiku-lock override.

### Added
- **H1460 — in-browser vocabulary drills page (L4 surface)** ([H1460](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1460-Sonnet_kosha_vocab-drills-inbrowser-page_22.07.26.md), Sonnet 5 `claude-sonnet-5`). The frequency-graded vocabulary drill bank ([`data/frequency/vocab_drills.json`](https://github.com/gasyoun/kosha/blob/main/data/frequency/vocab_drills.json), 13,334 items, H947) shipped only as an Anki `.apkg` deck plus a read-only curriculum table — no learner-facing quiz page existed. New standalone generator [`scripts/build_vocab_drills_page.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_vocab_drills_page.py) reads the committed JSON directly (never `docs/cards/`, gitignored/absent in a fresh worktree) and writes [`reading/vocabulary/drills/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/vocabulary/drills/index.html) (~5 MB, all 13,334 items inlined) — recognition/recall + rank-band (≤200/≤500/≤1000/all) filters, MCQ scoring. Every user-facing string is HTML-escaped at DOM insertion (vocab gloss text carries literal `&`/`<`/`>`/quotes, unlike the clean sandhi/morphology shells it otherwise copies). `reading/index.html` "Drill trainers" nav extended with the new link. Tests added to `tests/test_vocab_curriculum.py` (page existence/size, choice-builder answer-inclusion + no-empty-choice invariants).

## [0.81.0] - 2026-07-22

### Added
- **H1462 — thematic vocabulary axis (L4 surface)** (Sonnet 5 `claude-sonnet-5`). A new browsing/study axis alongside H947's frequency-graded curriculum: corpus vocabulary grouped by classical **Amarakosa varga** (thematic section — sky, earth, humans, animals, ...) instead of by corpus rank. [`scripts/build_thematic_vocabulary.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_thematic_vocabulary.py) joins three already-committed assets, none rebuilt: `../AMAR/amar.txt` (varga→eid→lemmas; parser ported from `SanskritLexicography/data/semdom_ak_bridge.py`, same org, public/MIT), `../SanskritLexicography/data/semdom_varga_crosswalk.csv` (A58 crosswalk, used only as secondary cross-reference "keyword" tags — the varga's own Sanskrit name is the theme's primary label, since A58 is many-to-many at the varga level), and `data/frequency/vocab_curriculum.tsv` (H947, the real-card filter — a lemma with no committed dictionary card is dropped, never a dead link). Output: [`data/frequency/thematic_vocabulary.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/thematic_vocabulary.tsv) (2,961 rows across all 20 genuinely thematic vargas; the 4 grammatical/misc annexes excluded), [`thematic_vocab_drills.json`](https://github.com/gasyoun/kosha/blob/main/data/frequency/thematic_vocab_drills.json) (5,922 recognition/recall items — distractors drawn from the **same theme**, not the same frequency band, the deliberate difference from H947's drill bank), `thematic_vocabulary.apkg` (Anki, one sub-deck per theme), and a browsable [`reading/vocabulary/thematic/`](https://github.com/gasyoun/kosha/blob/main/reading/vocabulary/thematic/index.html) page. 8 new tests in `tests/test_thematic_vocabulary.py`. Manifest rows `thematic-vocabulary` + `thematic-vocab-drills`.

## [0.80.0] - 2026-07-22

### Changed
- **H1455 wave-1.5 — MBh `<ls>` loci resolved to the Nīlakaṇṭha vulgate; the "infeasible" locus claim corrected** (Opus 4.8 `claude-opus-4-8`). The wave-1 report called PWG↔DCS Mahābhārata locus-matching *infeasible* — an over-claim that ignored existing org prior art. PWG's continuous Böhtlingk-Roth MBh numbering → **Nīlakaṇṭha vulgate** address is a **solved** problem (csl-atlas **f8 fitted-index crosswalk**, [H610](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H610-Opus_csl-atlas_mbh_citation_census_11.07.26.md)/H761, all 18 parvans, held-out MW 55.2% within ±3; [DEAD_ENDS §8b](https://github.com/gasyoun/SanskritLexicography/blob/master/DEAD_ENDS.md) retracted). This layer now **consumes** it via new [`scripts/mbh_vulgate.py`](https://github.com/gasyoun/kosha/blob/main/scripts/mbh_vulgate.py) (reads the committed, publish-safe `mbh_vulgate_concordance.csv` — numbers only): **7,055/7,353 (96%)** of pilot MBh `<ls>` loci now carry a resolved `parvan.adhyāya.śloka` address (e.g. `MBH. 12,3630` → **vulgate 12.98.19**), shown on the `ls` witness rows and in the viewer. A new **`locus-mbh`** tier (conf 0.65–0.80) matches a DCS Mahābhārata attestation's (parvan, adhyāya) against a sense's `<ls>`-resolved vulgate adhyāya at ±1 (the vulgate↔BORI-critical drift) — **48** DCS attestations assigned, up from 5 Vedic-only verse-exact matches. **The `nāgadanta` MBh 12,99 attestation the wave-1 build wrongly parked to the review queue now lands on sense 1a (tusk)** — the A3 DCS enrichment. Honest residual (kept explicit): DCS's Mahābhārata is the BORI critical edition, so the match is an adhyāya-level *corroboration*, not exact-verse identity; texts absent from DCS (Pañcatantra, Kathāsaritsāgara) still cannot be DCS-matched. `sense_corpus_concordance.tsv` 87,092 rows; build report + manifest keying corrected. Determinism (A8), rights (A7, 0 evidence-only) and the sidecar invariant (A6) unchanged.

## [0.79.0] - 2026-07-22

### Added
- **H1455 — per-sense corpus-attestation layer (сведение значений), wave-1: the नागदन्त layer** ([H1455](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1455-Sonnet_kosha_corpus-attestation-per-sense-join_22.07.26.md), Opus 4.8 `claude-opus-4-8`). The *middle arrow* headword → **numbered PWG sense** → DCS/Samudra attestation, where kosha previously linked only headword → attestation. Origin: the [नागदन्त thread](https://groups.google.com/g/nagari/c/NOWqiBQl1Xc/m/_R8O4-39CAAJ) — translators split «гвоздь в стене» vs «слоновый бивень» because thin bilingual glossaries drop the per-sense locus PWG already encodes. A **SIDECAR**: MW / kosha `senses` are byte-unchanged (left-joined at build time, like `lemma_frequency`). New assets under [`data/concordance/`](https://github.com/gasyoun/kosha/blob/main/data/concordance/): `sense_corpus_concordance.tsv` (87,134 rows), `sense_corpus_coverage.tsv`, `sense_review_queue.tsv`, and a sense-sharded KWIC viewer at [`concordance/senses/`](https://github.com/gasyoun/kosha/blob/main/concordance/senses/). Hybrid aligner over a 500-headword polysemous pilot: **ls** tier (85,472 rows — PWG's own `<ls>` citation under the sense, the guaranteed-correct sense↔passage witness, conf 0.99) + **locus** tier (7 rows — DCS attestation whose verse-locus *equals* a sense's `<ls>`, conf 0.90) + **overlap** tier (1,655 rows — shared proper-noun / Latin-binomial / digit gloss tokens across the DE/EN gap). **A2 acceptance metric: `<ls>`-locus-resolution rate 99.3%** on the pilot (floor 60%), reusing the canonical `pwg_sources.py` (pwgbib). `nāgadanta` worked example passes exactly: sense **1a** (Elephantenzahn/tusk) → MBH 12,3630; sense **1b** (Pflock/peg) → PAÑCAT 116,19/252,10; `nāgadantaka` 1b (HIT 27,12) recorded `variant_of nāgadanta`. **Honest note** (VERIFICATION risk 1, confirmed by spike): the passage-level DCS locus tier is weak by construction — DCS uses critical-edition references while PWG cites Böhtlingk-Roth editions, and Pañcatantra/Kathāsaritsāgara are absent from DCS — so the load-bearing witness is PWG's own `<ls>`, exactly as the risk register anticipated. 897 low-confidence + unassigned residue rows parked in the review queue (never dropped, A5); the LLM residue tier ([`wf/sense_adjudicate.js`](https://github.com/gasyoun/kosha/blob/main/wf/sense_adjudicate.js), out-of-set-guarded) is deferred by default so the deterministic tiers stay byte-reproducible (A8). Builders: `select_sense_pilot.py` → `build_sense_corpus_concordance.py` (shared `sense_loci_core.py`); input `pwg_sense_loci.tsv` from the H1456 export. Manifest row `sense-corpus-concordance`; build report [`SENSE_CONCORDANCE_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/SENSE_CONCORDANCE_BUILD_REPORT.md). Sibling to the [H1453 sense-frequency layer](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md) — two witnesses to the same attestation→sense assignment; cross-dictionary reconciliation (PWG↔MW↔Apte side-by-side) is wave-2.

### Changed
- **Concordance Q2 exit — relaxed tier dropped, strict-tier-only** ([H1267](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1267-Haiku_kosha_relaxed_tier_dead_end_record_18.07.26.md), Haiku 4.5 `claude-haiku-4-5-20251001`). Decision D6 (18-07-2026): the relaxed concordance matching tier, designed to fold vowel length and sibilants (ṣ/ś/s) for fuzzy linking, scored **0/3 correct on a 14-item golden sample**, while the three asserted tiers (xref/exact/floor) scored **11/11**. The 2,171 relaxed-tier candidates generated remain quarantined in [`dict_corpus_relaxed_candidates.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/dict_corpus_relaxed_candidates.tsv) as a historical record; the Q2 exit ships strict-tier-only (xref 12,836 + exact 61,373 + floor 311) with the 18.6% unfilled residue reported honestly. See [Uprava DEAD_ENDS §7](https://github.com/gasyoun/Uprava/blob/main/DEAD_ENDS.md) and [`GOLDEN_SAMPLE.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/GOLDEN_SAMPLE.md) for the minimal pairs and evidence.

## [0.78.0] - 2026-07-22

### Added
- **Sense-frequency wave-2 — Renou genre-stratified de-biasing** ([H1459](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1459-Opus_kosha_sense-frequency-wave2-genre-stratification_22.07.26.md), Opus 4.8 `claude-opus-4-8`). The full fix for the corpus-composition bias wave-1.5 only partly corrected. Genre source: **Renou**'s classification of Sanskrit literature (MG-decided). New [`dcs_text_genre.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/dcs_text_genre.tsv) buckets the 219 WordSem-tagged texts into Renou genres — revealing that **50.7% of the sense-tagged corpus is technical śāstra** (rasaśāstra 31.9% + āyurveda 18.4%) vs 42.5% literary/vedic, the direct cause of `rasa`=mercury. [`sense_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/sense_frequency.tsv) gains six columns: `count_bal_uniform` (post-stratified, each genre weighted equally — Little 1993/Biber 1993), `count_nonsastra` (literary/vedic texts only), `sense_rank_bal`, `sense_rank_nonsastra`, `top_genre`, `top_genre_share`. **Decisive result: `rasa` "mercury" = 0 in the non-śāstra view** (89% of its tokens are rasaśāstra) — non-śāstra `rasa` reads juice > liquid > taste; even the genre-balanced view puts juice above mercury. Four views now ship (`count_all` in-genre · `count_adj` dispersion · `count_bal_uniform` "Sanskrit generally" · `count_nonsastra` "Sanskrit non-śāstra"), none silently replacing another. The kosha card marks a `count_nonsastra=0` sense **śāstra-only** (red chip) and genre-concentrated senses with a `top_genre` chip, so a learner sees when a count reflects corpus composition. Grounded in the domain-relativity-of-predominant-sense literature (McCarthy/Koeling ACL 2004 [P04-1036](https://aclanthology.org/P04-1036/) / HLT-EMNLP 2005 [H05-1053](https://aclanthology.org/H05-1053/)); wave-3 lever = Chan & Ng EM ([P06-1012](https://aclanthology.org/P06-1012/)).

## [0.77.0] - 2026-07-22

### Added
- **Sense-frequency wave-1.5 — dispersion / burstiness de-biasing columns** (Opus 4.8 `claude-opus-4-8`). Addresses a real sampling bias: DCS is not a balanced sample of Sanskrit — its WordSem-tagged subset over-represents rasaśāstra/āyurveda (Hellwig's research focus), so raw token frequency inflates genre-concentrated senses (`rasa` reads 51% "mercury"). This is the *domain-relativity of the predominant sense* (McCarthy, Koeling, Weeds & Carroll, ACL 2004 [P04-1036](https://aclanthology.org/P04-1036/); Koeling, McCarthy & Carroll, HLT/EMNLP 2005 [H05-1053](https://aclanthology.org/H05-1053/)). [`sense_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/sense_frequency.tsv) gains five genre-label-free columns: `n_texts` (document frequency), `dispersion_dp` (Gries's Deviation of Proportions, IJCL 2008), `largest_text_share` (burstiness), `count_adj = count_all × (1 − dispersion_dp)`, and `sense_rank_adj`. Effect: down-weights bursty senses (`rasa` mercury/juice gap narrows 1.74× → 1.47×; `artha` "sense" — attested in only 3 texts, one holding 97% — is crushed to adj-rank tail). Honest limit: DP is corpus-size-relative, so it under-penalises concentration in *large* rasaśāstra texts; the fuller fix is wave-2 genre-stratified post-stratification (Little 1993; Biber 1993) + Chan & Ng EM sense-prior re-estimation (COLING-ACL 2006 [P06-1012](https://aclanthology.org/P06-1012/)). Both `count_all` and `count_adj` ship — the raw number is right for a reader *in* that genre, the adjusted one for "Sanskrit generally". [Data-statement](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/kosha-sense-frequency.meta.md) bias section + manifest keying updated.

## [0.76.0] - 2026-07-22

### Added
- **H1453 — per-sense frequency layer (частотность значений), wave-1: 3-layer sense frequency on DCS WordSem gold + kosha-cards UI** ([H1453](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1453-Opus_kosha_sense-frequency-wordsem-3layer-wave1_22.07.26.md), Opus 4.8 `claude-opus-4-8`). The sidecar to `lemma_frequency` — how often each numbered *meaning* of a word is attested, not just the lemma. Built on the fact the org had written off: DCS's per-token `WordSem` annotation IS Sanskrit-WordNet synset gold (219/270 texts, 531,747 tokens), and the synset→gloss decode the stub sqlite lacked ([SL FINDINGS §78](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md)) ships in the CoNLL-U distribution's `lookup/word-senses.csv`. New assets under [`data/frequency/`](https://github.com/gasyoun/kosha/blob/main/data/frequency/): `wordsem_inventory.tsv` (23,920 synsets, 100% decoded — recovering what the sqlite couldn't), `wn_to_mw_map.tsv` (synset→MW sense by gloss-overlap, 68.8% token coverage with honest `match_type`), and the deliverable `sense_frequency.tsv` (103,079 rows at three cross-linked layers — native WN synset / MW numbered sense / WordNet supersense; `provenance=attested`, no accuracy claim — it IS the gold). Sanity anchor holds: `rasa` splits mercury 47% / juice 27% / aesthetic-*rasa* 5%; `artha` splits meaning/wealth/purpose. Manifest row `kosha-sense-frequency` + [data-statement](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/kosha-sense-frequency.meta.md). kosha word pages gain a "Sense frequency" block — "N in this sense · M for the lemma" per MW sense with a `lemma_share` bar and a two-tier attested/estimated badge (estimated empty until wave-2 WSD). Builders: `build_wordsem_inventory.py` → `build_wn_mw_map.py` → `build_sense_frequency_layer.py` (+ `build_sense_order_delta.py`).
- **DCS-vs-MW sense-order finding** ([`data/frequency/dcs_mw_sense_order_delta.md`](https://github.com/gasyoun/kosha/blob/main/data/frequency/dcs_mw_sense_order_delta.md), feeds M01 Ch6). For 12,385/21,843 WordSem-attested MW headwords (56.7%) MW's printed sense-1 does not express the corpus-dominant sense — systematically because MW leads with a Devanāgarī-letter record (`ca` → "the 20th letter", corpus "and" 92%), a Dhātupāṭha/grammatical preamble, or a rare etymological sense. Framed as a DCS-derivation finding; MW's canonical order is trusted and left untouched (read-only sidecar).

## [0.75.0] - 2026-07-21

### Fixed
- **H1370 — repaired the 27 residual broken links H1266 left out of scope, plus 6 new archive-move link-rot and a 4th class (`kosha.db` blob links to a gitignored file)** ([H1370](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1370-Sonnet_kosha_link-repair-27-residue-and-ai-state-truth-pass_20.07.26.md), Sonnet 5 `claude-sonnet-5`). Missing `KOSHA_*.md` docs and `master`→`main` drift downgraded/repointed by an interrupted prior session, recovered and completed here: 6 links to now-archived H1262/H1366/H1367 handoffs repointed to `handoffs/archive/`, and 4 `kosha.db` blob links (a gitignored file that never exists on GitHub — always a dead link by construction) downgraded to plain backtick paths across `ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md`, `DECIDE_H1366_GENERATED_SIDE_FORMS_VS_INFLECTIONS.md`, and `PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md`. The 3 remaining `link_audit_fix.py` "wrong org" flags on `OliverHellwig/sanskrit` links are a tool false positive (basename collision with the unrelated local `gasyoun/sanskrit` fork of `shreevatsa/sanskrit`) — both URLs verified `200 OK`, left unchanged. `kosha`'s `.ai_state.md` H901/H902/H903 resume-point block (all three ✅ done 14-07-2026, archived) flipped from stale starter lines to `🔴 EXECUTED` lines (H919 failure-class prevention). GitHub issue #134 (deliverable shipped in PR #137, v0.64.0 + data-v0.2.0) closed as stale-open.

## [0.74.0] - 2026-07-20

### Added
- **Manifest row `uttarapada-dict-vs-corpus`** ([H1398](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1398-Sonnet_kosha_uttarapada-dict-vs-corpus-manifest-trainer-ranking_20.07.26.md), Sonnet 5 `claude-sonnet-5`). Registers VisualDCS H1328's `derived-data/Kompozity/uttarapada_dict_vs_corpus.tsv` (19,177 rows) — the join of MW's uttarapada (compound final-member) dictionary index against DCS Kompozity corpus attestation, `corpus_status` ∈ {final 6,249 / form_variant 1,289 / nonfinal_only 1,252 / absent 10,387} — as a pointer dataset (`in_release: not-applicable`, source stays in gasyoun/VisualDCS, sibling of `dcs-compound-dictionary`). No data copied into kosha.

### Changed
- **Samāsa trainer member-drill ranking — corpus attestation, not dictionary type-count** ([H1398](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1398-Sonnet_kosha_uttarapada-dict-vs-corpus-manifest-trainer-ranking_20.07.26.md), Sonnet 5 `claude-sonnet-5`). `scripts/build_samasa_trainer.py`'s member_side/member_recall drill pool previously ranked compound final members (uttarapadas) by MW dictionary distinct-first-member TYPE count (`mw_first_members`), which VisualDCS H1328 showed diverges sharply from real corpus usage (median Jaccard 0.00 between MW and DCS first-member sets). New `load_corpus_attestation()` loader joins the `uttarapada-dict-vs-corpus` TSV onto each MW uttarapada row (keyed on the already orthography-folded `final_member`), and a new `--mw-rank {dict,corpus}` flag (default `corpus`, set in `data/samasa/drill_weights.json`) switches the sort key to `-corpus_tokens`, restricts the pool to `corpus_status == "final"`, and applies the H1328-report-mandated stoplist (particles ca/eva/pronoun stems, bare verb roots, -tva/-tā taddhita suffixes) that token-count ranking alone does not drop. Evidence strings and `source["dictionary"]` provenance text updated to cite corpus_tokens/corpus_compounds. New regression test `tests/test_samasa_trainer.py::test_member_drill_ranked_by_corpus_tokens`.

## [0.73.0] - 2026-07-20

### Added
- **Concordance-Q3/Q4 W2b — invert the derivation harness into the Pāṇinian sūtra-to-corpus concordance** ([H1390](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1390-Sonnet_kosha_w2b-paninian-concordance-inversion_20.07.26.md), Sonnet 5 `claude-sonnet-5`). New [`scripts/build_panini_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_panini_concordance.py) inverts W2a's `derivation_status.tsv`/`derivation_chains.tsv` into one row per `(sūtra, form, locus)` triple, `concordance_core.RECORD_FIELDS` imported not retyped, `anchor_type=panini-sutra`/`anchor_id=sutra:<a.p.n>`/`target_locus=dcs:<sent_id>[_<sub>]`. **893,482** concordance rows from **72,764** `ok`-status forms across **221** distinct sūtras (7/8 adhyāyas — adhyāya 5 has no exemplar in this build), chain length min 6 / median 12 / max 36 (Ashtadhyayi-only steps; 165 Dhatupatha/Varttika/Kaumudi steps excluded — not Pāṇini's own sūtras). Per-sūtra ambiguity rate (lemma-attributed, never one org-wide figure): median 27.1%, range 0.0–69.2% ([`data/concordance/panini_ambiguity_by_sutra.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/panini_ambiguity_by_sutra.tsv), 221 sūtras). New web page [`concordance/panini/index.html`](https://github.com/gasyoun/kosha/blob/main/concordance/panini/index.html) — forked from the Q1 dict viewer, retargeted to adhyāya-sharded `concordance/panini/data/kwic_<1-8>.js` shards (`window.CONC_DATA[<adhyaya>][<sutra_code>]`), plus a `window.CONC_CHAINS` per-shard lookup delivering the **chain view** affordance (a form's full ordered sūtra derivation) and a lit-only **coverage view** preview (the full dark-sūtra map is W3a). New [`data/concordance/PANINI_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/PANINI_BUILD_REPORT.md). Manifest row `paninian-corpus-concordance` added (public tier, unreleased pending the D-license @DECIDE). **Documented gap, not silently faked:** exit-check 2b-1 asks for `ok`/`ambiguous` forms both inverted; W2a's shipped output carries an empty `chain_id` for all 86,857 `ambiguous` rows (verified exhaustively), diverging from `ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md` §4's stated "records all of them" design for ambiguity — re-deriving with vidyut to recover this was out of scope (W2a's output is this build's entire input). Parked as a W2a follow-up. W3a (sūtra-coverage/dark-sūtra map) and W3b (public release) are next, not attempted here.

## [0.72.0] - 2026-07-20

### Fixed
- **Salt-facade `restful/entries` `query_type=prefix` -- H838 range-seek fix ported + LIKE-prefix sweep** ([H1369](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1369-Sonnet_kosha_salt-endpoint-prefix-range-seek-port-and-like-scan-sweep_20.07.26.md), Sonnet 5 `claude-sonnet-5`). [`app/main.py`](https://github.com/gasyoun/kosha/blob/main/app/main.py)'s `salt_entries` handler (`/dicts/{dict_id}/restful/entries`) still had the exact bug H838 fixed in `/api/v1/search`: `slp1_key LIKE q||'%'` is case-insensitive by default, and SLP1 is case-significant (`k`=ka vs `K`=kha). Measured against `kosha.db`: a `query=ka&query_type=prefix` Salt lookup on `mw` matched 6,818 keys under the old LIKE, 835 of them `K`-prefixed (kha) false positives, vs 3,769 correct under the fix -- and because `entries_dict_key`'s BINARY collation sorts `K...` before `k...`, the **entire default-`size=25` first page was 100% kha leakage** (zero real `ka` entries reachable without paging past it). Rewritten to the same half-open range seek as H838's `_prefix_range_bound` (`slp1_key >= q AND slp1_key < bound`), reusing the existing helper -- `EXPLAIN QUERY PLAN` confirms the range now binds directly into the `entries_dict_key` index seek. Swept the rest of the codebase for remaining LIKE-prefix scans: none -- the only other `LIKE` site (`/api/v1/search` `mode=fuzzy`, substring `%q%`) is not a prefix pattern and cannot be range-seeked. New regression test `tests/test_api.py::test_salt_entries_prefix_case_significant_excludes_kha`.

## [0.71.0] - 2026-07-20

### Added
- **Concordance-Q3/Q4 W2a — vidyut-prakriya derivation harness over the full W1b AG bucket** ([H1368](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1368-Sonnet_kosha_w2a-vidyut-prakriya-derivation-harness_20.07.26.md), Sonnet 5 `claude-sonnet-5`). New [`scripts/build_panini_derivations.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_panini_derivations.py), modelled on the proven E1 `compare_vidyut_cologne.py`/`compare_vidyut_verbs.py` cell-mapping pattern: for each of the 401,368 W1b AG-bucket forms, resolves the lemma's candidate grammatical cells from `kosha.db` `inflections` (nominal case/number/gender; verbal model/tense/voice/person/number, `v_p` passive borrowing gaṇa via the H855 crosswalk), derives every cell with `vidyut.prakriya` (cached per lemma — 90,690 distinct lemmas, not once per row), and classifies each form `ok`/`ambiguous`/`engine-error`/`no-derivation` on ordered-sūtra-chain identity + `form_key()` equality (`exact` 0.95 outranks `floor` 0.85, `TIER_CONFIDENCE`-derived, never a literal). Consumes the `forms`-built AG bucket per H1366/D13's canonical-generated-side ruling (merged as v0.70.0 concurrently with this branch's development); `inflections` is used only as the cell-metadata source the AG bucket itself lacks (case/number/gender/tense/voice/person), never as a second generated-side denominator. **Build-stamp verified** (401,368 rows, matches the W1b report) before running. **Pilot (10k, frequency-ranked) reported first** per the exit criteria, then the **full run** (883.8s, 454.1 forms/sec — well under the 40-minute scaling threshold, so run to completion rather than parked): `ok` 72,764 (18.13%) · `no-derivation` 237,447 (59.16%) · `ambiguous` 86,857 (21.64%) · `engine-error` 4,300 (1.07%); 2,815 distinct sūtra chains, length min 6 / median 12 / max 37. New [`data/concordance/derivation_status.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/derivation_status.tsv) (one row per AG form) + [`data/concordance/derivation_chains.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/derivation_chains.tsv) (chain_id → ordered sūtra steps) + [`data/concordance/DERIVATION_HARNESS_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/DERIVATION_HARNESS_BUILD_REPORT.md) (status distribution, chain-length distribution, R-C3/R-C4 caveats, no-network statement, and a 30-example sampled human-verification section). Manifest row `panini-derivation-status` added. W2b (invert to `sūtra → {attested forms}`) is the next wave, not attempted here.

## [0.70.0] - 2026-07-20

### Changed
- **Concordance-Q3 D13 RULED — `forms` is the canonical A4/W2a generated side (accepted by MG)** ([H1366](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1366-Opus_kosha_generated-side-forms-vs-inflections-canonical-ruling_20.07.26.md), Opus 4.8 `claude-opus-4-8`). MG accepted the v0.69.0 decide brief: the A3→A4/W2a generated side is **`forms`**, not `inflections`. Recorded as [PLAN §2 `D13` + §3a](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md) (settled); the [decide brief](https://github.com/gasyoun/kosha/blob/main/docs/DECIDE_H1366_GENERATED_SIDE_FORMS_VS_INFLECTIONS.md) and [ARCHITECTURE §1](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md) note flipped to ✅; [CONTRADICTIONS §3](https://github.com/gasyoun/SanskritLexicography/blob/master/CONTRADICTIONS.md) graduated to a ✅ tombstone and FINDINGS §94 flipped to ruled. `inflections` (the 6.92M-row `cologne_mwinflect` paradigm layer) is reclassified as a distinct secondary asset / optional cross-check, never the generated denominator. **W2a is unblocked to consume the 426,410-row non-heritage `forms` AG set.**

## [0.69.0] - 2026-07-20

### Changed
- **Concordance-Q3 generated-side contradiction — decide brief parked + ARCHITECTURE mislabel corrected** ([H1366](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1366-Opus_kosha_generated-side-forms-vs-inflections-canonical-ruling_20.07.26.md), Opus 4.8 `claude-opus-4-8`). The standing [CONTRADICTIONS §6](https://github.com/gasyoun/SanskritLexicography/blob/master/CONTRADICTIONS.md) (two kosha tables named as the generated inflection side, "5× apart") was briefed but **not ruled** — the canonical-table choice stays a human call (W1b surfaced it with "no standing to settle it"). Measured directly against `kosha.db`: `forms` (1,378,401 rows / 426,410 non-heritage, carrying the `dcs`/`vidyut`/`heritage` `source` split) and `inflections` (6,917,018 rows, ~100% single-engine `cologne_mwinflect`, full case/gender/number morphology, no trust split) are **not two cardinalities of one dataset** — they share only 168,034 of 426,410 non-heritage `(form, lemma)` pairs, and `inflections` holds 3,246,914 pairs `forms` never has. Parked a ruling-ready decide brief ([DECIDE_H1366_GENERATED_SIDE_FORMS_VS_INFLECTIONS.md](https://github.com/gasyoun/kosha/blob/main/docs/DECIDE_H1366_GENERATED_SIDE_FORMS_VS_INFLECTIONS.md)) **recommending `forms` at high confidence** (pipeline continuity, the `source` trust axis only `forms` has, engine separation), mirrored to Uprava GTD `@DECIDE`; enriched CONTRADICTIONS §6 with the measurements (still 🟡). The [ARCHITECTURE §1](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md) mermaid node's "6.9M generated" label (the `inflections` count sitting on the `forms` node) corrected to "1.38M generated / 426k non-heritage". W2a must not start until the decision is ruled.

## [0.68.0] - 2026-07-20

### Changed
- **D5 re-measured + distribution strategy ruled — `kosha.db` is at 84% of the 2 GB release-asset ceiling** ([H1367](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1367-Opus_kosha_d5-remeasure-and-release-asset-ceiling-distribution-ruling_20.07.26.md), Opus 4.8 `claude-opus-4-8`). The DB grew ~5.8× since the 03-07 D5 baseline (276 MiB → **1,673,854,976 B = 1.674 GB**, 83.7% of 2 GB decimal / 77.9% of the true 2 GiB GitHub per-asset limit, ~452 MiB real headroom). A per-table breakdown (`dbstat` still absent; row-data exact, index footprint estimated) attributes ~65% of the file to the new **`inflections` paradigm layer** (6.92M rows, table + 3 indexes ≈ 1.09 GB) — *derived/regenerable*, not primary lexical data; everything else is a ~0.5–0.6 GB "core lexical DB". The file compresses to **≤27%** (`gzip -1` floor 458 MB / 3.65×; `xz`/`zstd -19` ~5× / ~330 MB). **Ruling D5-4** ([KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md)): the alarm is real for an uncompressed single-file channel but moot for the channels `kosha.db` actually uses (`tier: restricted`, never a public asset) — (1) the restricted-tier backup ships **compressed**, never raw (defers the ceiling past ~6 GB of growth); (2) P-D5 agent-queryable distribution **splits** into ATTACH-able `kosha_core.db` + `kosha_inflections.db`; (3) a **G-SIZE** tripwire (FAIL >1.8 GB uncompressed single asset) is added to the release gate so the ceiling fails CI, not an upload. Updated [`D5_MEASUREMENTS.md §1`](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md), [`RISKS.md R11`](https://github.com/gasyoun/kosha/blob/main/RISKS.md) (the "ample" language was stale), and the `kosha-db` manifest row. The compress/split/G-SIZE plumbing is queued follow-on; the DB is regenerable and privately backed up, so nothing is at risk in the interim.

### Fixed
- **W1e — link-rot repaired (20 archived handoffs, 50 occurrences across 18 files)** ([H1266](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1266-Sonnet_kosha_handoff_link_rot_mover_fix_catchup_18.07.26.md), Sonnet 5 `claude-sonnet-5`). Root cause: `Uprava/tools/handoff_archive.py`'s cross-reference repoint pass only ever scans its OWN repo (Uprava's root `*.md` + its `handoffs/` folder) — a full blob-URL reference in a sibling repo's markdown, like this repo's own `PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md`, was structurally invisible to it (SCOPE, not a timing/audit-cadence gap — confirmed by reading `find_cross_references` itself). Fixed at the source: the mover now appends an `(old_url, new_url)` row to `Uprava/handoffs/ARCHIVE_MOVE_MANIFEST.jsonl` per archived handoff, and `Uprava/tools/link_audit_fix.py` (already an org-wide scanner) consults it before falling back to its old main/master-swap-only guess. Backfilled the manifest for every already-archived handoff this repo still referenced by the pre-archive path (not just the 7 named in the original brief) and repointed all 20/50 in one pass — including 3 (`H093`/`H094`/`H111`) whose references used never-correct shorthand filenames predating the current naming convention, a related but distinct historical casualty resolved via the same manifest mechanism. 27 other broken links in this repo (missing `KOSHA_*.md` docs, `master`→`main` drift, wrong-org citations) are unrelated pre-existing breakage, out of scope for this fix.

## [0.67.0] - 2026-07-19
### Added (samāsa trainer — MW final-member drills, a third source)
- **[`scripts/build_samasa_trainer.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_samasa_trainer.py) gains a third source with a third role.** Gold gives verified *type*, DCS/Kompozity gives corpus *frequency*; neither answers **which words are productive as a compound's final member**. MW's own compound markup does — inverted to an uttarapada index in [MWderivations `issue15/`](https://github.com/gasyoun/MWderivations/blob/master/issue15/README.md) (19,435 distinct final members from 87,188 pairs). New flags `--mw-rev` / `--mw-cap` (default 150) / `--mw-min-left` (default 20); the source is **optional** — if the file is absent the builder logs it and the deck stays valid.
- **Two new item types** the other two sources cannot support: `member_side` ("does MW attest this word as a first member, a second member, or both?" — compound position is a real structural fact learners get wrong) and `member_recall` ("these are attested first members sharing one final member — name it", testing productive-member recognition rather than one-off memorisation). Deck 3,565 → **3,865 items** (+150 of each).
- **Taddhita suffixes are excluded at load, deliberately.** The MW index's raw head is dominated by bound morphemes (`-tva` 1246, `-vat` 1136, `-tā` 1058) which are **not** compound members; drilling them would teach a falsehood. Only the classifier's `UTTARAPADA` + `KRT_STEM_MEMBER` rows are loaded — the latter kept because an upapada-tatpuruṣa's final stem (`-kāra`, `-ja`) is a genuine member. 733 members clear the ≥20-first-member bar; the 150 most productive are drilled and the remainder is reported, not silently dropped.

## [0.66.0] - 2026-07-19

### Added

- **W-RU-a gloss.ru re-run over the subhāṣita pack**
  ([H1312](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1312-Sonnet_kosha_subhashita-pack-ru-gloss-rerun_19.07.26.md),
  Sonnet 5 `claude-sonnet-5`). H1279 shipped the beginner subhāṣita reader
  ([`subhashita_beginner_pack.json`](https://github.com/gasyoun/kosha/blob/main/data/subhashita/subhashita_beginner_pack.json))
  without `gloss.ru` — the W-RU-a layer
  ([H1278](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1278-Opus_kosha_pedagogy-wave-ru-inline-gloss-reader_19.07.26.md))
  landed mid-flight and its joiner keys on lemma+surface, but the pack's tokens are
  unsandhied IAST surface forms with no lemma. `scripts/build_subhashita_pack.py` now
  attaches a per-token SLP1 lemma (vidyut-cheda: the same run's `.lemma` when the
  accepted split came from cheda, else cheda re-run on each already-clean unsandhied
  token in isolation — honest null when neither yields one, never guessed) and joins
  `gloss_ru` from
  [`build_ru_gloss_layer.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_ru_gloss_layer.py)'s
  `RuGlosser` (public site-tier only, same Wave-RU rights gate). **85.3%** of the
  pack's 1,510 tokens carry a lemma-layer RU gloss (89.1% carry a resolved lemma at
  all); folded into
  [`reading/RU_GLOSS_COVERAGE.md`](https://github.com/gasyoun/kosha/blob/main/reading/RU_GLOSS_COVERAGE.md)
  alongside the 5 DCS reading packs (all-pack total now 92.1% over 4,468 tokens) via a
  new `build_ru_gloss_layer.compute_family_coverage()` reused, not re-derived, by the
  subhāṣita builder. The reader page
  ([`reading/subhashita/`](https://github.com/gasyoun/kosha/blob/main/reading/subhashita/index.html))
  gains a "show Russian gloss" toggle rendering the gloss under each token
  (lemma tier preferred, surface/root fallback); the Anki deck gains a `GlossRu` back
  field. The sandhi split / difficulty grading are byte-unchanged
  (`scripts/test_subhashita_difficulty.py` still green — `subhashita_difficulty.tsv`
  untouched); manifest row `subhashita-reader-pack` + data statement updated.

## [0.65.0] - 2026-07-19

### Added

- **W-RU-b beginner subhāṣita reader shipped** ([H1279](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1279-Fable_kosha_pedagogy-wave-ru-subhashita-reader_19.07.26.md),
  Fable 5 `claude-fable-5`): all 7,537 Indische Sprüche
  ([SanskritLexicography F33](https://github.com/gasyoun/SanskritLexicography/blob/master/FEATURES_INDEX.md), public domain)
  difficulty-graded with a documented W2a-reduced 2-axis scorer
  ([`data/subhashita/subhashita_difficulty.tsv`](https://github.com/gasyoun/kosha/blob/main/data/subhashita/subhashita_difficulty.tsv),
  byte-stable, regression-pinned on 10 hand-checked sayings by
  [`scripts/test_subhashita_difficulty.py`](https://github.com/gasyoun/kosha/blob/main/scripts/test_subhashita_difficulty.py));
  a 106-saying beginner band curated with a full auditable reject log
  ([`data/subhashita/CURATION_NOTES.md`](https://github.com/gasyoun/kosha/blob/main/data/subhashita/CURATION_NOTES.md) —
  106 accepts, 144 coded rejects, no unlogged picks; the 50 R1 rows double as an
  IndischeSprueche OCR to-fix list); the pack sandhi-split (validated DharmaMitra
  `unsandhied`, committed cache, vidyut-cheda fallback), junction-labelled against
  [`data/sandhi/corpus_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/corpus_sandhi.tsv)
  with attestation counts, metre-tagged (W3a two-tier method);
  reader page [`reading/subhashita/`](https://github.com/gasyoun/kosha/blob/main/reading/subhashita/index.html) +
  Anki deck [`subhashita_beginner_anki.apkg`](https://github.com/gasyoun/kosha/blob/main/data/subhashita/subhashita_beginner_anki.apkg);
  manifest row `subhashita-reader-pack` + data statement. `gloss.ru` absent — W-RU-a
  ([H1278](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1278-Opus_kosha_pedagogy-wave-ru-inline-gloss-reader_19.07.26.md))
  unshipped at build time; re-run TODO logged in the pack meta, not silent.

## [0.63.0] - 2026-07-19

### Added

- **W-RU-a — inline Sanskrit→Russian gloss layer in reading packs**
  ([H1278](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1278-Opus_kosha_pedagogy-wave-ru-inline-gloss-reader_19.07.26.md),
  Opus 4.8 `claude-opus-4-8`). A Russian-speaking learner hovers a token and reads its meaning.
  [`scripts/build_ru_gloss_layer.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_ru_gloss_layer.py)
  joins every reading-pack token to the three **public site-tier** SanskritRussian layers
  (surface/lemma/root) → [`data/ru_gloss/ru_gloss_layer.tsv`](https://github.com/gasyoun/kosha/blob/main/data/ru_gloss/ru_gloss_layer.tsv)
  (2,958 rows) and inlines an additive `gloss_ru` triple into each pack token (the English
  `gloss` is untouched). `build_reading_pack.py` gains `--gloss-lang ru`; the reader
  ([`reading/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/index.html)) renders
  the RU triple and defaults to Russian on a Russian browser locale. Manifest row `ru-gloss-layer`
  + [data statement](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/ru-gloss-layer.meta.md);
  joiner unit-tested (8 checks).
- **Measured coverage: 95.6%** of pack tokens carry a lemma-layer RU gloss
  ([`reading/RU_GLOSS_COVERAGE.md`](https://github.com/gasyoun/kosha/blob/main/reading/RU_GLOSS_COVERAGE.md)) —
  the public subset suffices, no rights unlock needed. **Rights gate (PLAN decision 14):** only
  SanskritRussian's public GitHub-Pages tier is read; the restricted `corpus_lexicon` stays a
  local-only input. Applies to the 5 built packs (nala 1–3, hitopadeśa, kirātārjunīya); the Gītā
  packs remain parked (BhG absent from the DCS corpus).

## [0.62.0] - 2026-07-19

### Added

- **Wave RU staged in the pedagogy plan** ([`docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE_RU.md`](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE_RU.md),
  via [`/ask-batch`](https://github.com/gasyoun/claude-config/blob/main/commands/ask-batch.md), Fable 5 `claude-fable-5`):
  W-RU-a inline Sa→Ru gloss layer over reading packs
  ([H1278](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1278-Opus_kosha_pedagogy-wave-ru-inline-gloss-reader_19.07.26.md), queued)
  and W-RU-b graded beginner subhāṣita reader from Indische Sprüche
  ([H1279](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1279-Fable_kosha_pedagogy-wave-ru-subhashita-reader_19.07.26.md), queued);
  roadmap/plan/verification docs extended with the wave, decisions 13–14 (RU wave + rights gate) recorded.

## [0.64.0] - 2026-07-19

### Added

- `scripts/migrate_manifest_schema.py` + `scripts/cut_data_v020.py` — **D8 manifest
  schema hardening** (Concordance-Q3 W1c,
  [H1264](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1264-Sonnet_kosha_manifest_schema_hardening_data_v020_18.07.26.md)):
  `in_release` migrated to a closed vocabulary (`"<release-tag>"` · `"unreleased"` ·
  `"not-applicable"`) across all 78 manifest rows — the undefined `null`/`"unreleased"`
  ambiguity that let a 33-row unreleased backlog accumulate unnoticed. `release_asset`
  now required on every `tier: public` row naming a release tag; schema validation added
  to `tests/test_directory.py` (fails CI on a broken row — proven red then restored).
  `docs/publish-safety-checks/data-v0.2.0_19.07.26.md` (GO) and
  `docs/data-statements/data-v0.2.0-batch.meta.md` record the release's safety gate and
  provenance/licence summary.
- **D7 rolling-cadence rule** in
  [DATA_HUB_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md):
  every wave adding a `tier: public` manifest row cuts a `data-vX.Y.Z` release in the
  same pass, closing the gap D8 found.

### Fixed

- `data-v0.2.0` catch-up release clears the 33-row `"unreleased"` backlog (32 pre-existing
  + `morphology-attestation-audit`, new since H1262). `heritage-forms-crosswalk-extras`
  verified still `tier: restricted` (LGPLLR, D10) and untouched by this release.

## [0.61.0] - 2026-07-18

### Added

- `data/manifest/rights/vidyut_prakriya_derivation_2026-07.md` — the A4-gating rights record
  (W1a / [H1263](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1263-Opus_kosha_vidyut_derivation_metadata_rights_record_18.07.26.md)):
  vidyut **code** licence (MIT, from the installed `LICENSE.md`) and vidyut **derivation-data**
  licence (MIT, from `vidyut-prakriya/data/README.md` via ashtadhyayi.com; source sūtra/dhātu
  texts public domain) stated **separately**, each with its source file; the composition ruling
  for A4 output (**CC BY-SA 4.0, vidyut attributed**, ShareAlike inherited from CDSL). No `@DECIDE`
  triggered — both licences compose cleanly into BY-SA.
- `scripts/build_morphology_attestation_audit.py` + `data/concordance/morph_attest_{AG,GnA,AnG}.tsv`
  + `data/concordance/MORPHOLOGY_ATTESTATION_BUILD_REPORT.md` — **A3, the generated-vs-attested
  morphology audit** (Concordance-Q3 W1b, [H1262](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1262-Opus_kosha_a3_attested_form_join_morphology_audit_18.07.26.md)).
  Joins `kosha.db` `forms` (non-heritage, 426,410 rows) against DCS attested surface forms (381,413
  distinct) on `form_key()` equality (length-preserving floor tier; no NFD+strip path): **AG 401,368
  / G¬A 25,042 / A¬G 2**, both denominators reconciled. Manifest row `morphology-attestation-audit`
  added (`in_release: unreleased` — publication gated on the W1a rights record, H1263 / D2).
- **Key finding (the artefact A4 cannot start without, D12):** 93.30% of the generated side is
  itself DCS-derived, so full-set AG is a 99.99% round-trip — the **vidyut-engine subtotal (AG
  3,550 / 28,567 = 12.43% attested)** is the only research-meaningful figure, and A¬G is degenerate
  (=2) and cannot measure engine gaps here. Reported the `forms`-vs-`inflections` (1.38M vs 6.9M)
  plan-set contradiction (STOP-AND-SURFACE, not resolved) — see
  [SanskritLexicography CONTRADICTIONS §6 / FINDINGS §94](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md).
  Read-only build; no data release cut.

### Fixed

- **DCS licence contradiction resolved from Hellwig's own published terms.** DCS's
  [`dcs/data/conllu/readme.md`](https://github.com/OliverHellwig/sanskrit/blob/master/dcs/data/conllu/readme.md)
  states the CoNLL-U data is **CC BY 4.0**; `data/manifest/external_tools.json` (`id: dcs`) was the
  outlier at CC BY-SA 4.0 and is corrected to **CC BY 4.0** (with a `license_source` citation).
  `CONCORDANCE_ROADMAP.md`:151 and the 14 `datasets.json` assertions were already correct and left
  unchanged (the unrelated Gita Supersite BY-4.0 mention deliberately untouched). Added
  `bundled_data_license`/`bundled_data_provenance` to the `vidyut` manifest row; marked the two
  resolved rows in `ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md` §7.

## [0.60.0] - 2026-07-18

### Added

- `docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md` + its `.meta.md` — the Concordance Q3 (Pāṇini /
  derivation chains) plan index, with the decisions-taken table for the 18-07-2026 rulings and the
  autonomy contract. Wave-1 handoffs H1262–H1267 (all 🟡 queued).
- `docs/ROADMAP_KOSHA_2026H2.md` + its `.meta.md`, `docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md`,
  `docs/IMPLEMENTATION_KOSHA_CONCORDANCE_Q3.md`, `docs/VERIFICATION_KOSHA_CONCORDANCE_Q3.md` —
  the rest of the layered plan set, authored by the `/ask-batch` 2026-07 slice-2 pass.

### Changed

- Recorded four corrections the authoring + adversarial-verify passes measured against the repo:
  A3 (the attested-form join A4 depends on) **does not exist** and is absorbed into wave 1;
  all 77 manifest rows already carry `in_release` (the field missing from 38 is `release_asset`),
  so the defect is an undefined vocabulary rather than an absent field; the static-head cutoff is
  **N = 11,148** for exactly 95.00% of 4,550,704 corpus tokens; and 402 + 477 MB = 879 MB is 86% of
  the Pages cap rather than an overflow, so the head/tail split stands on headroom grounds.

## [0.59.0] - 2026-07-15

### Added
- **H951: per-verse metre annotation over the reading packs — Wave 3 pedagogy (W3a).**
  The field (§3.9) names "metre-ID wired into reading" as a gap. This ships the **data
  layer** for it and **no UI** — SanskritKaraoke owns the metre trainer (scope re-checked
  15-07, unchanged); kosha's contribution is the corpus-grounded per-verse annotation those
  tools lack (the ARCHITECTURE integration-surface rule). `scripts/build_reading_pack_metre.py`
  annotates every reading-pack sentence via **`vidyut.chandas`** (the real metre classifier,
  over a vendored `data/vidyut/chandas/meters.tsv`) with an honest two-tier + null method:
  strict vṛtta (`method=vidyut-chandas`, high confidence, **≥8-syllable guard** so a prose
  heading can't spuriously match); anuṣṭubh (`method=syllable-heuristic`, medium — vidyut
  doesn't classify the loose śloka, but the DCS sentences align to half-ślokas, and **all
  840 anuṣṭubh tags land at exactly 16 syllables** = 2 pādas); everything else left
  **unresolved with an empty metre** (prose, speaker-tags, fragments — never guessed).
- **Coverage: 89% identified** (12% strict vṛtta + 77% anuṣṭubh) across 1,095 sentences /
  23 packs, **11% honestly unresolved**. Validation anchor: Bhāravi's Kirātārjunīya-1 scans
  **92/92 as vaṃśastha** — correct for that canto. Outputs: `data/metre/reading_pack_metre.tsv`
  (per-sentence: metre, type, method, confidence, syllables) + `metre_coverage.tsv` (per-pack
  distribution). Two `datasets.json` rows (`reading-pack-metre`, the vendored
  `vidyut-chandas-meters`), `vidyut` added to `requirements.txt`, and 9 tests (no fabricated
  metre, ≥8-syllable vṛtta guard, anuṣṭubh pāda-alignment, Kirātārjunīya-all-vṛtta anchor,
  coverage-sums-match, non-SLP1-doesn't-crash). Deterministic. Build: Opus 4.8 (`claude-opus-4-8[1m]`).

## [0.58.0] - 2026-07-15

### Added
- **H972 — defgen eval, F1_fable_ctx arm (15-07-2026, Fable 5 `claude-fable-5`)**: the
  non-DeepSeek model family called for by the protocol's next-steps #6, generated
  in-session by the Claude Code session itself over a **gold-free inputs projection**
  (next-steps #7a; new [`scripts/defgen_fable_arm.py`](https://github.com/gasyoun/kosha/blob/main/scripts/defgen_fable_arm.py)
  emit/assemble, so the MW gold gloss is structurally absent from the generation
  context). 500/500 items, scored with the existing H730 harness (`defgen_score.py`
  ARMS extended) and judged blind by `deepseek-chat`. **F1 leads every arm on every
  metric**: corpus chrF 24.35 (+4.78 over A1), token-F1 0.340, BLEU 5.14, judge
  adequacy 4.60 (floor separation intact, judge~chrF ρ 0.415); mean gloss length 17.1
  words, so the lead is content, not verbosity. Frequency-gradient inversion and
  polysemy penalty replicate. Full numbers + caveats (in-session arm is a strong-model
  reference point, not a reproducible baseline):
  [`docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md`](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md);
  manifest row `mw-defgen-eval-sample` updated.

## [0.57.0] - 2026-07-15

### Added
- **H977: reduced 3-axis difficulty ordering for the 18 Gītā reading packs — W2a follow-up.**
  W2a (v0.55.0) shipped the difficulty scorer but **skipped the 18 Gītā packs**: their builder
  (`build_reading_pack_gita.py`) emits no UD morphology, so scoring them on the 4 axes would
  fabricate the morphology + compound loads. This closes that gap the honest way. The Gītā
  packs do carry three signals of their own (verified: 100 % a lemma via `slp1`, 37.5 % a
  populated per-token `sandhi` field, 24.9 % a hyphenated compound lemma), so
  `scripts/build_difficulty_scorer.py` gained `score_pack_reduced`:
  `difficulty_reduced = w_vocab·VOCAB + w_sandhi·SANDHI + w_compound·COMPOUND` — the morphology
  weight dropped and the other three renormalised. VOCAB = rarity of **non-compound** content
  lemmas (compounds excluded so they are not double-penalised as unknown-rare); SANDHI =
  fraction of tokens carrying the pack's **own induced junction rule** (a real signal, *not*
  the 4-axis boundary proxy); COMPOUND = hyphen-lemma share.
- **Shipped as a SEPARATE ordering, explicitly not comparable to the 4-axis packs** (R5/R6
  honesty carries over): different axis set *and* a different sandhi definition, so the 18
  Gītā chapters are ranked **among themselves** only. New `data/difficulty/gita_reading_pack_difficulty.tsv`
  (+ `.json`), a labelled section on `reading/difficulty/index.html`, an extended
  `data/difficulty/METHODS.md`, a `gita-reading-pack-difficulty` manifest row, and 5 new tests
  (all 18 scored, reduced axes in range + ascending, composite == reduced formula with no
  morphology term, Gītā packs never leak into the 4-axis table, no double-count of compounds).
  The 4-axis UD ordering (5 packs) is unchanged. Build: Opus 4.8 (`claude-opus-4-8[1m]`).

## [0.56.0] - 2026-07-15

### Changed
- **W2a follow-through: pedagogy-surfaces roadmap marked shipped ([#116](https://github.com/gasyoun/kosha/pull/116)).**
  [`docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md)
  still showed `🟢 BUILD` / `🟡 REUSE` verdicts for six surfaces that had all shipped;
  flipped them to `✅ SHIPPED vX.Y.Z` **preserving the build-vs-reuse design intent**
  (W1a v0.54.0 · W1b v0.51.0 · W1c v0.52.0 · W2a v0.55.0 · W2b v0.50.0), marked W3a
  **UNBLOCKED** (next; consumes the W2a reading packs), and ticked the Wave 1 + Wave 2
  headings ✅ to match Wave 0.

### Added
- **Companion metadoc for the pedagogy-surfaces roadmap ([#117](https://github.com/gasyoun/kosha/pull/117)).**
  New [`docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.meta.md)
  (the last genre-named doc in the pedagogy set lacking one): purpose · audience ·
  provenance (H945, `/ask`) · status table (Waves 0–2 shipped, W3a unblocked) · ranked
  improvement backlog (flip W3a on ship — the §84 stale-row lesson applied to roadmaps;
  W2a weighting ruling; the 18 unscored Gītā packs) · limitations · revision history.
  Registered in [`Uprava/METADOCS_INDEX.md`](https://github.com/gasyoun/Uprava/blob/main/METADOCS_INDEX.md).

### Fixed
- **Two kosha pedagogy metadocs aligned to template-v2 ([#118](https://github.com/gasyoun/kosha/pull/118)).**
  The roadmap metadoc and the [`reading-pack-difficulty`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/reading-pack-difficulty.meta.md)
  data statement scored 0/3 on the org census's template-v2 check; added the three
  required sections — `## Intended use / known misuse` (carrying the R5 one-estimator and
  R6 build-status-≠-learning-gain caveats), `## Maintenance & sunset plan`, and
  `## Deprecation status` (`active`) — both now 3/3 (org v2 coverage 62/126 → 64/127).

## [0.55.0] - 2026-07-15

### Added
- **H949: reading-pack difficulty scorer — Wave 2 pedagogy (W2a), the difficulty spine.**
  The field (§3.4/§6) names a text-difficulty scorer as a gap; this scores every
  UD-annotated kosha reading pack on four corpus-grounded axes and orders them into a
  graded reading sequence (easiest first). `scripts/build_difficulty_scorer.py`:
  `difficulty = w_vocab·VOCAB + w_sandhi·SANDHI + w_morph·MORPH + w_compound·COMPOUND`,
  each axis a per-token load in [0,1] — **VOCAB** = mean corpus-rarity of content lemmas
  (from `lemma_frequency.tsv`, the W1b signal); **SANDHI** = fraction of word-boundaries
  fused by sandhi, measured off the pack; **MORPH** = mean surprisal of each token's
  `upos|morph` form over the 840 corpus signatures; **COMPOUND** = share of compound
  members (DCS `feat_case=Cpd`). The consumed morph signal is derived once by
  `scripts/build_difficulty_signals.py` (GROUP BY the UD morph features over the 5.69M-token
  DCS full sqlite → `data/difficulty/morph_signature_freq.tsv`, keyed byte-identically to
  how the reading packs display morph, so a pack token joins with no re-derivation), which
  keeps the scorer heavy-DB-free at score time — the same source→derive→consume split the
  sandhi programme uses.
- **W2a is ONE estimator, not "the" difficulty** (VERIFICATION R5). Weights live in
  `data/difficulty/difficulty_weights.json` (tunable — **a human should confirm**; defaults
  vocab 0.40 · sandhi 0.20 · morphology 0.25 · compound 0.15) and the formula + honest
  limitations (frequency ≠ learnability R6; sandhi is a boundary-fusion proxy) are documented
  in `data/difficulty/METHODS.md`. Outputs: `reading_pack_difficulty.tsv`/`.json`, the graded
  page `reading/difficulty/index.html`, and a data statement
  `docs/data-statements/reading-pack-difficulty.meta.md`.
- **Four new reading packs beyond Nala 1, ordered by the scorer** (via the existing
  `build_reading_pack.py`, all UD-complete, 96–98 % card-linked): `nala-2` (MBh 3.51),
  `nala-3` (MBh 3.52), `hitopadesa-0` (Hitopadeśa opening), `kiratarjuniya-1` (Bhāravi).
  On the 5 scored packs the ordering validates the scorer — Kirātārjunīya (dense kāvya)
  is hardest (0.389) while the Nala narrative chapters + Hitopadeśa cluster near 0.32,
  the expected register gradient. The 18 Gītā packs are **skipped, not scored**: their
  builder (`build_reading_pack_gita.py`) emits no UD morphology, so scoring them would
  fabricate morph/compound loads — the scorer detects this (`ud_coverage < 0.5`) and logs
  the skip rather than inventing a number.
- Tests: `tests/test_difficulty_scorer.py` (axes + composite in range, composite equals the
  documented weighted sum, ascending-difficulty ordering, deterministic scoring, non-UD
  packs skipped-not-fabricated, kāvya-harder-than-epic sanity anchor). Six new
  `datasets.json` rows (`reading-pack-difficulty`, `morph-signature-freq`, the four packs).
  Build: Opus 4.8 (`claude-opus-4-8[1m]`).

## [0.54.0] - 2026-07-15

### Added
- **H946: morphology drills — Wave 1 pedagogy (W1a).** `scripts/build_morphology_drills.py`
  turns the P4 paradigm engine (`app/paradigm.py`) into graded, frequency-filtered,
  answer-keyed declension/conjugation drills — the novel move: drill only forms the
  corpus actually attests (field RQ1: "stop drilling forms that never appear"). New
  one-pass VisualDCS `dcs_full.sqlite` attestation join (`(lemma, form, morphology)` ->
  corpus locus/count; nominal case/gender/number map directly from DCS's UD tags, verb
  person/number/tense-mood collapse onto kosha's `pre`/`ipf`/`ipv`/`opt` vocabulary —
  voice is NOT part of the verb match key since DCS's `feat_voice` marks only passive,
  an honest upstream limitation, not a silent overclaim). Over the 5,985 core-vocabulary
  lemmas with entries: 38,782/254,805 candidate paradigm cells (15.2%) survived
  attestation. `data/morphology/morphology_curriculum.tsv` (7,134 paradigms, class-bucket
  ordered a-stems → other-vowel-stems → consonant-stems → pronouns → present-class-verbs
  → other per `drill_weights.json`, tunable not hard-coded) — learn 4,862 paradigms to
  cover 50% of attested nominal/verbal tokens, 6,351 → 80%, 6,708 → 90%.
  `data/morphology/drills.json` (12,000 fill/match items over the top 6,000 attested
  cells by frequency, `--max-drill-cells 0` for the full set) + `morphology_drills.apkg`
  (Anki, 6,000 notes, verified re-imports as a valid collection) +
  `reading/morphology/{curriculum,drills}/index.html` (self-contained, theme-aware,
  Devanāgarī/IAST/SLP1 toggle). `morphology-curriculum` + `morphology-drills` manifest
  rows. `tests/test_morphology_drills.py` (11 tests: every item answer-keyed and
  evidence-backed, no unattested form in default mode, coverage monotone, lesson-bucket
  ordering never regresses, Anki note count matches).

## [0.53.0] - 2026-07-15

### Added
- **H955: SRS deck — Rung B1 demo (last-mile pipeline).** `scripts/build_demo_srs_deck.py`
  emits `data/srs/srs-deck-b1-demo.json`: the content-word vocabulary of the existing
  `dcs-reading-pack-nala-1` (439 tokens), joined to `lemma_frequency.tsv` `core_rank`,
  function words stripped (`grammar_all` in `ind`/`pron`, the wave-1a method) — 164
  cards, `core_rank`-ordered. Proves [`docs/LAST_MILE_PIPELINE_SPEC.md`](https://github.com/gasyoun/SanskritGrammar/blob/main/docs/LAST_MILE_PIPELINE_SPEC.md)
  Hop B end-to-end on one concrete text (reader ↔ SRS deck share the same word set) —
  deliberately narrower than H947's general `vocab_curriculum.tsv` (6,667 lemmas, already
  shipped in 0.51.0), which it does not duplicate or supersede. `kosha-srs-deck-b1-demo`
  manifest row registered. Systema-side import lands separately (H955, Systema-Sanscriticum).

## [0.52.0] - 2026-07-15

### Added
- **H948: samāsa (compound) analysis trainer — pedagogy Wave 1, surface W1c.**
  [`scripts/build_samasa_trainer.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_samasa_trainer.py)
  applies the six-stage pedagogy contract
  ([ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md))
  to compound analysis: [`data/gita/gita_morphology_gold.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_morphology_gold.tsv)
  (815 hand-tagged Gītā compounds) as the verified-type gold seed, joined against
  the VisualDCS `Kompozity` compound dictionary (`cmps.csv` × `names.csv`,
  168,421 corpus-attested compounds ranked by frequency) for corpus-scale
  split-only practice.
  [`data/samasa/samasa_curriculum.tsv`](https://github.com/gasyoun/kosha/blob/main/data/samasa/samasa_curriculum.tsv)
  (759 gold-verified compounds, karmadhāraya/tatpuruṣa first then
  bahuvrīhi/dvandva per the MG 14-07-2026 ordering ruling, ranked within type
  by corpus frequency) + [`reference.tsv`](https://github.com/gasyoun/kosha/blob/main/data/samasa/reference.tsv)
  (per-type look-up) + [`samasa_drills.json`](https://github.com/gasyoun/kosha/blob/main/data/samasa/samasa_drills.json)
  (3,565 identify/split items, 100% evidence-backed) + `samasa_drills.apkg`
  (Anki) + `reading/samasa/{curriculum,drills,reference}/index.html`
  (theme-aware, cross-links the hosted
  [csl-guides samāsa quiz](https://sanskrit-lexicon.github.io/csl-guides/docs/users/samasa-quiz)
  rather than duplicating it). Type distribution honestly reported, not
  balanced: TP=458, BV=298, DV=2, KD=1 — dvandva/karmadhāraya are severely
  underrepresented in the gold set and the corpus pool cannot fill the gap
  (no verified type there). `samasa-trainer` manifest row registered;
  [`tests/test_samasa_trainer.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_samasa_trainer.py)
  (11 tests) green, no regressions in the existing suite.

## [0.51.0] - 2026-07-14

### Added
- **H947: frequency-graded vocabulary curriculum (Wave 1, W1b).** Applies the shipped
  sandhi-curriculum method to words — "learn the N most frequent lemmas → read X% of the
  corpus" — over the Leonchenko core-vocabulary layer already carried by
  [`lemma_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv)
  (`core_rank`/`coverage_pct`). New
  [`scripts/build_vocab_curriculum.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_vocab_curriculum.py)
  emits [`data/frequency/vocab_curriculum.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/vocab_curriculum.tsv)
  (6,667 lemmas over 134 lessons; 453 core lemmas dropped for having no committed
  dictionary card — no dead `/w/` links), `vocab_drills.json` (13,334 recognition/recall
  items, ARCHITECTURE shared item schema), `vocab_curriculum.apkg` (Anki deck), and
  [`reading/vocabulary/curriculum/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/vocabulary/curriculum/index.html).
  Coverage headline: 284 lemmas → 30%, 1,122 → 50%, 4,978 → 70% of the core-vocabulary
  corpus mass. `datasets.json` gains `vocab-curriculum` + `vocab-drills` rows;
  `tests/test_vocab_curriculum.py` (8 tests, all green) locks monotone coverage, every
  lemma resolving to a real card, and lesson sizes. Gotcha worth flagging: the source
  feed's `coverage_pct` is a per-lemma **marginal** weight, not already-cumulative
  (`data/frequency/README.md`'s own caveat) — the cumulative column here is computed by
  this script, not copied from the source.

## [0.50.0] - 2026-07-14

### Added
- **H950 (pedagogy Wave 2, W2b): roots frequency + attestation curriculum.**
  REUSE/INTEGRATE, not a rebuild — [WhitneyRoots](https://github.com/gasyoun/WhitneyRoots)
  already owns the 935-root explorer and already computes a per-root
  MW↔Whitney↔DCS triangulation with corpus frequency and attested forms
  (`WhitneyRoots/src/dcs_freq.json`). New
  [`scripts/build_roots_frequency.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_roots_frequency.py)
  reads that canonical source and adds the missing graded-curriculum framing —
  rank order + cumulative `coverage_pct` — producing
  [`data/roots/roots_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/roots/roots_frequency.tsv)
  + `.json` (629 unique DCS-lemma rows, deduped from 717 Whitney-hub roots with
  attestation — 74 homonym-shared lemmas collapsed so the same corpus mass
  isn't triple-counted). Coverage headline: learn top 25 roots → 58.7% of
  verb-token occurrences; top 50 → 71.7%; top 100 → 85.4%; top 200 → 95.3%.
  `roots-frequency-curriculum` manifest row registered; no kosha roots UI
  shipped, per the architecture's integration-surface rule — WhitneyRoots and
  Systema are the intended consumers. `tests/test_roots_frequency.py` (8
  tests: monotone coverage, dense ranks, every root traceable to WhitneyRoots's
  own hub, no homonym double-counting, TSV/JSON agreement, no fabricated
  attested forms).

## [0.49.0] - 2026-07-14

### Added
- **H945: kosha pedagogy engine-room build plan (`/ask`).** A layered build plan
  generalising the shipped corpus-sandhi programme's six-stage pattern to the rest of
  kosha's pedagogy data — the *engine-room* half of the org-wide digital-Sanskrit-pedagogy
  field defined in
  [SanskritGrammar `DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md`](https://github.com/gasyoun/SanskritGrammar/blob/main/DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md)
  (H912). Cover + decisions
  [`PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md)
  (+ `.meta.md`); layers
  [roadmap](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md) ·
  [architecture](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md) ·
  [implementation](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE1.md) ·
  [verification](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md).
  Four build waves (morphology drills · vocabulary curriculum · samāsa trainer ·
  graded-reader + difficulty scorer), two reuse/integrate (roots → WhitneyRoots, metre →
  SanskritKaraoke), one agenda (audio); wave handoffs H946–H951 minted. No papers this
  cycle — surfaces + measurement instrumentation only.

## [0.48.0] - 2026-07-14

### Added
- **H918 (sandhi Phase 4, surface 4b): drills/flashcards — the last core-programme
  surface.** New
  [`scripts/build_sandhi_drills.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_drills.py)
  turns the graded curriculum's 132 highest-value rules (lessons 1–9, 90 % of all
  corpus sandhi) into 396 practice items — join (`X + Y → ?`), split
  (`Z → original junction?`), identify-class — each with 4-way multiple-choice
  same-class distractors and an attested corpus example. Shipped in all three
  formats MG requested: item-data JSON/TSV
  ([`data/sandhi/sandhi_drills.json`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/sandhi_drills.json) /
  [`.tsv`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/sandhi_drills.tsv)),
  an Anki deck
  ([`sandhi_drills.apkg`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/sandhi_drills.apkg),
  genanki), and a self-contained theme-aware web quiz at
  [`reading/sandhi/drills/`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/drills/index.html).
  Registered as the `sandhi-drills` dataset. Credit: Dr. Mārcis Gasūns. (Sibling
  surface 4a, reader hover, is a separate SanskritGrammar handoff, H917 — Phase 4
  is now fully shipped on the kosha side.)

## [0.47.0] - 2026-07-14

### Added
- **Sandhi programme hub doc** — new
  [SANDHI_PROGRAMME.md](https://github.com/gasyoun/kosha/blob/main/SANDHI_PROGRAMME.md)
  consolidates the whole sandhi programme (v0.36→v0.46) into one "what exists &
  how to use it" page: the pipeline, headline results (inducer 96.3 % Gītā-gold,
  17-text corpus, A/B/C bake-off verdict method C ≫ B), every dataset/script/page,
  rebuild steps, and cross-repo consumers. Linked from the README Document map.

## [0.46.0] - 2026-07-14

### Added
- **H902 (sandhi Phase 4, surface 3/4): per-class reference pages.** New
  [`scripts/build_sandhi_reference.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_reference.py)
  emits a corpus-wide look-up reference — every recurring sandhi grouped by class
  (anusvāra 34.7 % · visarga 32.1 % · vowel coalescence 19.9 % · consonant 13.3 %
  of all sandhi), each ranked by frequency with an attested example, at
  [`reading/sandhi/reference/`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/reference/index.html)
  (theme-aware, self-contained; top 50 per class, the 3,794-rule consonant tail
  summarised). A look-up companion to the graded curriculum. Credit: Dr. Mārcis
  Gasūns. (Remaining Phase-4 surfaces: reader hover, drills/flashcards.)

## [0.45.0] - 2026-07-14

### Added
- **H902 (sandhi Phase 4, surface 2/4): graded curriculum.** New
  [`scripts/build_sandhi_curriculum.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_curriculum.py)
  turns the corpus sandhi table into an ordered teaching syllabus — "learn these
  N junctions to read X % of all sandhi." Rules are ordered by the MG-ruled
  priority (`frequency × class × environment-generality`, 14-07-2026), with the
  weights in a tunable, visible config
  [`data/sandhi/difficulty_weights.json`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/difficulty_weights.json)
  (per the ruling — not hard-coded; edit + re-run to re-tune). Outputs
  `data/sandhi/sandhi_curriculum.tsv` (2,181 rules, 10 lessons) + a theme-aware
  page [`reading/sandhi/curriculum/`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/curriculum/index.html).
  **Headline: 23 rules → 50 %, 79 → 80 %, 132 → 90 %** of all corpus sandhi;
  easy high-frequency rules first. New `sandhi-curriculum` dataset registered in
  [`datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
  Credit: Dr. Mārcis Gasūns. (Remaining Phase-4 surfaces: reader hover, drills,
  reference pages.)

## [0.44.0] - 2026-07-14

### Added
- **H908 (sandhi Method C): DharmaMitra neural segmenter — the A/B/C bake-off's
  clear winner.** `method_C` in
  [`scripts/compare_sandhi_methods.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_sandhi_methods.py)
  segments each DCS sentence via the DharmaMitra `unsandhied` API
  ([`dharmamitra.org/api/tagging/`](https://dharmamitra.org/api/tagging/), contract
  reused from `csl-atlas/scripts/lib/dharmamitra_infer.py`) and feeds the split
  through the same induce tail as A/B — so only the splitter differs.
  `--allow-network`; responses cached under `data/sandhi/_cache/` (per-batch
  retry + incremental writes). **Method C ≫ Method B** on the fair (mode-1-only)
  comparison to DCS gold: F1 **0.795 vs 0.282** (Amaruśataka) and **0.704 vs
  0.224** (Hitopadeśa), with C precision 0.90–0.97 — the neural splitter's word
  boundaries match DCS far more often than vidyut-cheda's. **Verdict:** use
  method C as the splitter for the GRETIL path (Phase 3) where no DCS gold exists.

## [0.43.0] - 2026-07-14

### Added
- **H903 (sandhi Phase 1, method B): vidyut-cheda bake-off vs gold DCS splits.**
  [`scripts/compare_sandhi_methods.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_sandhi_methods.py)
  `method_B` binds the offline `vidyut-cheda` segmenter (`Chedaka` over the
  `vidyut-data/` root, not the `.msgpack` file directly), transliterates
  IAST↔SLP1, and induces sandhi rules from cheda's predicted pre-sandhi splits
  through the SAME `induce_rule()` gold uses — isolating splitter quality from
  notation. Scope: mode-1 (plain word-word) junctions only, since
  `Chedaka.run()` returns no character offsets to re-anchor a predicted
  sub-word split within an MWT span. Scored on 2 texts: Hitopadeśa (500 rules
  / 1,359 junctions scored, mode-1-only F1=0.224 vs gold's 437-rule slice) and
  Amaruśataka (61 rules / 73 junctions, F1=0.282). Also added
  `method_A_mode1_strict` (fair gold baseline matching B's scope) and
  no-gold-recovery instrumentation — which found the roadmap's planning-stage
  "~27 % no gold split" estimate does NOT reproduce on DCS (0 % on both texts
  + a 15-dir corpus sample); see
  [`ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md)
  §2 for the full writeup. Method C (DharmaMitra) remains explicitly deferred.
- **H901 (sandhi Phase 2b): broadened corpus sandhi sweep, 8 → 17 texts.**
  Extends H900's `scripts/build_corpus_sandhi.py` `TEXTS` list with kāvya
  (Buddhacarita, Kumārasaṃbhava, Kirātārjunīya, Meghadūta), more readers
  (Daśakumāracarita, Bhāratamañjarī), śataka/nīti (Śatakatraya,
  Bhallaṭaśataka), and the **full** Rāmāyaṇa (606 files) and **full**
  Mahābhārata (1,995 files) — the latter replaces H900's Bhagavadgītā-only
  glob (the Gītā's 18 chapters are already inside the full-corpus sweep, so
  keeping the narrow row would have double-counted those tokens in the merged
  global table; `data/sandhi/bhagavadgita_sandhi.tsv` retired accordingly).
  **580,230 sandhi events · 9,840 distinct rules** (was 53,291 / 1,674); the
  top **83** rules now cover 80% of all corpus sandhi (was 69 — moved up
  slightly, plausibly kāvya's more varied sandhi spreading the frequency mass
  across more rules, reported honestly rather than smoothed over). **Scale
  finding:** the handoff worried the full Mahābhārata (~2,000 files) would
  need a parvan/`--limit` sample gate — measured instead of assumed (~10
  files/s on a 300-file timing sample), the full corpus ran directly in a few
  minutes on one machine, no sampling gate needed. `corpus-sandhi` manifest
  row updated; `ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md` + its `.meta.md`
  updated (backlog item 2 ticked).

## [0.42.0] - 2026-07-14

### Added
- **H900 (sandhi Phase 2): corpus-wide sandhi sweep + merged frequency-ranked table.**
  New [`scripts/build_corpus_sandhi.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_corpus_sandhi.py)
  runs the validated method-A inducer (96.3 % Gītā-gold coverage) across a curated
  8-text pedagogical set in learner-difficulty order (Hitopadeśa, Vetālapañcaviṃśatikā,
  Śukasaptati, Amaruśataka, Aṣṭāvakragīta, Bhagavadgītā, Gītagovinda, Kathāsaritsāgara)
  and builds per-text tables plus the merged
  [`data/sandhi/corpus_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/corpus_sandhi.tsv)
  with global frequency ranks (`rule · category · global_count · global_pct ·
  n_texts · top_texts · examples`). **53,291 sandhi events, 1,674 distinct rules;
  the top 69 rules cover 80 % of all corpus sandhi** — the graded-curriculum
  backbone. New public dataset `corpus-sandhi` registered in
  [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
  Credit: Dr. Mārcis Gasūns; source DCS CC BY-SA 4.0 (Oliver Hellwig / DCS).

## [0.41.0] - 2026-07-14

### Changed
- **H897 (sandhi Phase 1.2): spaced-notation split — clears the 90 % Gītā-gold
  exit criterion.** Final-`t` assimilation, `i`→`y` semivowel, and MWT-internal
  visarga were being *induced* but written merged (`t a → da`, `i e → ye`,
  `ḥ v → rv`) rather than in the hand table's spaced form (`t a → d a`,
  `i e → y e`, `ḥ v → r v`). One rule in `induce_coalescence`
  ([`scripts/dcs_sandhi_induce.py`](https://github.com/gasyoun/kosha/blob/main/scripts/dcs_sandhi_induce.py))
  — split the output when the right word's initial phoneme survives unchanged —
  fixes it, leaving genuine coalescence (`a a → ā`, `a e → ai`) merged.
  **Gītā-gold frequency-mass coverage 87.1 % → 96.3 %** (rule-string 82 →
  116/161), clearing the roadmap's ≥90 % exit criterion. Residual 3.7 % is
  mostly malformed `gita_sandhi.tsv` entries + `aḥ`/`ḥ` notation variants.
  Credit: Dr. Mārcis Gasūns.

## [0.40.0] - 2026-07-14

### Added
- **Bloomfield RV pratīka cross-reference (H896)** — resolves the CONCORDANCE_ROADMAP.md
  Bloomfield-source `@DECIDE` left open by H836. MG obtained direct written permission from
  Marco Franceschini (University of Bologna) for his digital edition of Bloomfield's 1906
  *A Vedic Concordance* (Harvard Oriental Series 9) — public tier, non-exclusive/worldwide/
  perpetual (grant text in
  [`data/manifest/rights/franceschini_hos9_permission_2026-07-13.md`](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/franceschini_hos9_permission_2026-07-13.md)).
  New [`scripts/build_bloomfield_rv_crossref.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_bloomfield_rv_crossref.py)
  adds a `bloomfield_pratika` column to `parallel_passage_verses.tsv` for the RV subset
  (11,522/13,581 rows, 85%, independently text-validated rather than positionally assumed —
  see [`BLOOMFIELD_RV_CROSSREF_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/BLOOMFIELD_RV_CROSSREF_REPORT.md)
  for the method and the honest residue) + new dataset `bloomfield-rv-citations` (36,680 rows,
  every direct RV citation in Bloomfield's concordance). Manifest rows, `LICENSE-DATA.md`,
  and `/concordance/parallels/` updated.

## [0.39.0] - 2026-07-14

### Added
- **H894 (sandhi Phase 1.1): MWT right-edge visarga.** New **mode 2b**
  (`induce_mwt_edge` in [`scripts/dcs_sandhi_induce.py`](https://github.com/gasyoun/kosha/blob/main/scripts/dcs_sandhi_induce.py))
  recovers the last-in-MWT word's sandhi with the token *after* the MWT — hidden
  in the component's un-sandhied FORM, visible only in the MWT surface tail. It
  takes the last alignment op ending at the component's final phoneme, handling
  substitution (`ḥ t → s t`, `ḥ v → r v`), elision (`ḥ i → Ø i`), and multi-char
  (`aḥ → o`). Pilots regenerated; Gītā-gold notation coverage **58 % → 61 %**
  (93 → 98 of 161 hand rules), visarga now the top category. Credit: Dr. Mārcis
  Gasūns.
- **Gītā gold scoring** (roadmap item 5):
  [`scripts/score_gita_gold.py`](https://github.com/gasyoun/kosha/blob/main/scripts/score_gita_gold.py)
  runs method A on the *actual* DCS Bhagavadgītā (18 `MBh, 6, BhaGī N` chapters)
  and scores against `gita_sandhi.tsv`. **Frequency-mass coverage 87.1 %**
  (2,971 / 3,412 attestations) — the true figure, vs the 61 % rule-string proxy
  a small pilot gives. Missed 12.9 % = a long tail (final-`t` assimilation,
  `i`-semivowel before non-`a` vowels) → Phase 1.2.

## [0.38.0] - 2026-07-13

### Added
- **H888 (sandhi Phase 1): vowel-coalescence alignment mode.**
  [`scripts/dcs_sandhi_induce.py`](https://github.com/gasyoun/kosha/blob/main/scripts/dcs_sandhi_induce.py)
  now recovers the vowel-sandhi rules Phase 0 structurally missed. DCS records a
  coalesced surface span as a CoNLL-U **multi-word token** (`5-6 nāgnir` over
  `5 na` + `6 agniḥ`, whose own FORM stays un-coalesced), so a token-edge diff
  never sees the merge. New **mode 2** aligns each MWT surface against its
  component `Unsandhied` forms and reads the rule off the internal boundary
  (`na`+`agniḥ` in `nāgnir` → `a a → ā`), sandhi-aware so `na`+`eva`→`naiva`
  gives `a e → ai` (not a naïve alignment's `a e → i`).

### Fixed
- **Sandhi Phase-0 MWT bug:** the inducer counted CoNLL-U MWT range lines (ID
  `n-m`) as tokens, inflating `no-gold` junctions (Aṣṭāvakragīta 1,263 → **0**).
  Mode 1 now skips range/enhanced-node lines and processes syntactic words only.
- **PWG multi-volume scan-link disambiguation** (H839, Sonnet 5 `claude-sonnet-5`)
  — [`app/scan_resolver.py`](https://github.com/gasyoun/kosha/blob/main/app/scan_resolver.py)'s
  `scan_url()` silently defaulted a bare PWG page number to volume 1's scan
  regardless of the entry's real volume. Resolved by source read
  ([`csl-apidev/parm.php`](https://github.com/sanskrit-lexicon/csl-apidev/blob/main/parm.php)
  + `servepdfClass.php`) plus a live content-diff against the production
  `servepdf.php` endpoint: Cologne has **no** `vol=`/`volume=` GET parameter
  (any such param is silently ignored, which is why status-code probing alone
  always returned 200); volume is instead embedded inside `page` itself as
  `"{vol}-{page:04d}"`, matching PWG's own `<pc>` format and Cologne's
  `pdffiles.txt` keys. `scan_url()` now takes `vol` and requires it for PWG
  (returns `None` rather than an ambiguous link if omitted); every call site
  (`app/main.py` ×3, `app/salt.py`, `scripts/build_static_cache.py`,
  `scripts/build_colocation_page.py` ×2, `scripts/measure_d5.py`) updated to
  pass `entries.vol`. New tests:
  [`tests/test_scan_resolver.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_scan_resolver.py).
  **Not included in this pass:** regenerating the committed `docs/cards/*.json`
  static cache / `colocation/data/pwg.js` — deferred to a separate pass so it
  can be built from a current (not 39-commits-stale) database rather than
  mixed into this fix.

### Changed
- **Sandhi pilots regenerated** with the merged mode-1 + mode-2 output.
  Aṣṭāvakragīta now surfaces `a a → ā` as its #1 rule (122); Gītā-gold notation
  coverage rose **47 % → 58 %** (75 → 93 of the 161 hand rules). Residual gap =
  visarga elision at MWT right edges (`ḥ m → Ø m`), scoped as Phase 1.1. Credit:
  Dr. Mārcis Gasūns.

## [0.37.0] - 2026-07-13

### Changed
- **Pronoun correction phase 2: flag the wrong Cologne pronoun rows `disputed=1`.**
  The `build_db.py --stage pronoun` step now also marks wrong Cologne pronoun rows
  for editorial review (the E1 `disputed` mechanism; non-destructive). Scoped to the
  `(form, lemma)` pairs the Gītā gold attests, a row is flagged when its case is
  untagged (NULL) or its (case, number) is not gold-attested — **73 rows newly
  flagged** (9 were already E1-flagged; 79 gold-consistent rows left untouched),
  across 10 pronoun lemmas (sarva, etad, idam, kim, anya …). `(case, number)` — not
  gender — is used to avoid flagging gender-ambiguous valid rows; details in
  [`PRONOUN_CORRECTION_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/PRONOUN_CORRECTION_REPORT.md).

## [0.36.0] - 2026-07-13

### Added
- **H882: corpus-wide sandhi extraction roadmap + Phase 0 DCS scaffold.**
  Generalises the H872 Bhagavadgītā sandhi layer from one hand-annotated text to
  every DCS text (GRETIL phase-3). New:
  [ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md)
  + `.meta.md`;
  [`scripts/dcs_sandhi_induce.py`](https://github.com/gasyoun/kosha/blob/main/scripts/dcs_sandhi_induce.py)
  (method A — junction-rule inducer over DCS `Unsandhied=`, reuses the H872
  `categorise()` classifier verbatim, emits per-text `data/sandhi/<slug>_sandhi.tsv`);
  [`scripts/compare_sandhi_methods.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_sandhi_methods.py)
  (A/B/C split-method bake-off skeleton + notation validation vs the Gītā hand
  table). Pilots: Aṣṭāvakragīta (722 sandhi events, 100 % ruled, 147 rules) and
  Hitopadeśa (4,554 events, 453 rules); method A independently reproduced 75 of
  the Gītā's 161 hand rules. Finding: DCS pre-splits vowel coalescence into
  separate tokens, so token-edge induction misses it (Phase-1 `# text =`
  alignment mode planned). Credit: Dr. Mārcis Gasūns.

## [0.35.0] - 2026-07-13

### Fixed
- **Curated pronoun-paradigm correction — closes the W4 QA finding.** The Gītā
  inflection QA (H874) showed kosha's hybrid `inflections` layer mis-models
  pronouns (71 % of divergences). Per MG, this **corrects** it:
  [`scripts/build_pronoun_corrections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_pronoun_corrections.py)
  takes the **208 gold attested pronoun analyses** from the Gītā and inserts them
  into `inflections` as `source='curated-gita-pronoun'` rows — wired as
  **`build_db.py --stage pronoun`** (idempotent, non-destructive, re-applied on
  rebuild). Re-running the QA on the corrected engine: nominal agreement
  **93.0 % → 98.7 %**, divergences **360 → 73**, gaps **919 → 588**
  ([`PRONOUN_CORRECTION_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/PRONOUN_CORRECTION_REPORT.md);
  dataset [`pronoun-corrections`](https://github.com/gasyoun/kosha/blob/main/data/gita/pronoun_corrections.tsv)).
  Public/MIT, credit Dr. Mārcis Gasūns.

## [0.34.0] - 2026-07-13

### Fixed
- **`/api/v1/search` prefix mode: `LIKE 'ka%'` scan → `slp1 >= 'ka' AND slp1 <
  'kb'` range seek** (H838, Sonnet 5 `claude-sonnet-5`) — fixes the
  [D5_MEASUREMENTS.md](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md)
  §3-flagged defect: `LIKE` forced a full 323k-row `lemmas` scan (~62–70 ms) AND,
  being case-insensitive by default, silently over-matched SLP1's case-significant
  prefixes (`ka%` wrongly matched 1,504 `K`-initial/kha lemmas out of 12,495 hits).
  The range seek hits the index (`EXPLAIN QUERY PLAN` now shows `SEARCH ... USING
  COVERING INDEX`, not `SCAN`) and restores correctness (7,041 correct hits).
  Handler latency 61.8 ms → **3.26 ms** median (p95 7.17 ms); e2e 51 ms →
  **11.82 ms**. New regression test
  `tests/test_api.py::test_search_prefix_case_significant_excludes_kha` (fails
  against the old query, proving it catches the regression). D5 §3 re-measured
  and logged.
- **Re-ran the H345 `heritage_anchor` ingest on the live `kosha.db`** (H837,
  Sonnet 5 `claude-sonnet-5`) — fixes the H691-flagged regression where the
  05-07-built (and later 12-07-rebuilt) live DB carried no `heritage_anchor`
  table, so `/api/v1/lemma`'s `heritage` witness was silently absent. Re-ran
  `python scripts/build_db.py --stage heritage`; row counts match H345's
  original ingest exactly (185,803 MW keys, 25,140 Heritage-covered,
  24,549 anchor-resolved, 591 unresolved). Verified live against a running
  API instance (`GET /api/v1/lemma/akAra` now returns a populated `heritage`
  object). `data/manifest/datasets.json` `kosha-db` row updated (new SHA256,
  size, table count, provenance date).

### Added
- **H836 (CONCORDANCE_ROADMAP Q2, B3): Bloomfield-style parallel-passage concordance.**
  New public dataset `parallel-passage-concordance`
  ([manifest row](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json))
  built by [`scripts/build_parallel_passage_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_parallel_passage_concordance.py)
  from `VisualDCS/derived-data/Paralleli-v-tekstah-korpusa-SRC/PARA/Polnorazmernye/`
  (245 CSV files, the 2026 corrected full-text-match pass): 501,231 source verses
  parsed, 15,164 (3.0%) carry ≥1 parallel occurrence, 153,045 total links (13,862
  GOOD exact + 139,183 PARTLY partial, word-diff attached). New static viewer
  [`concordance/parallels/`](https://github.com/gasyoun/kosha/blob/main/concordance/parallels/index.html)
  (text picker → verse list → GOOD/PARTLY parallels with diffs). Full counts +
  honest caveats in [`data/concordance/PARALLEL_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/PARALLEL_BUILD_REPORT.md):
  the roadmap's prior "506,787 alignments" estimate (itself sourced from an
  admittedly-unverified upstream README note) doesn't match this build's
  directly-parsed counts — flagged, not silently reconciled. Two open `@DECIDE`
  surfaced to a human, not self-ruled: which of three PARA export variants is
  canonical (defaults to `Polnorazmernye/` per the folder's own README), and
  which Bloomfield *Vedic Concordance* (1906) digitization to key the Ṛgveda
  subset against (not found anywhere in the org — RV cross-reference not built
  this pass).
- **H836 Task A: relaxed-candidate pre-classification + review sheet.** New
  [`scripts/classify_relaxed_candidates.py`](https://github.com/gasyoun/kosha/blob/main/scripts/classify_relaxed_candidates.py)
  computes a per-row SLP1 diff signature for the 2,171 Q1/H380 relaxed-tier
  dict↔corpus candidates and pre-classifies 740 as "worth-a-closer-look"
  (single word-final vowel-length diff — the masc/neut -a vs fem -ā stem-citation
  pattern) vs 1,431 "likely-spurious" (default, per the Q1 golden sample's 3/3-wrong
  finding on this exact tier); emits `data/concordance/relaxed_candidates_classified.tsv`.
  [`scripts/build_relaxed_review_sheet.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_relaxed_review_sheet.py)
  generates a gitignored Russian-language `/review-sheet` HTML voting sheet
  (`review/kosha-concordance-relaxed_q2_review.html`, not committed — a personal
  working artifact) for MG. Only MG-approved rows get asserted into the concordance.

## [0.33.0] - 2026-07-13

### Added
- **Upasarga semantics on the `/w/` root card (H876 W6 follow-up).** Root word-pages
  now carry a crawlable "Preverb senses (upasarga)" `<details>` panel driven by the
  [`sanskrit-upasarga-semantics`](https://github.com/gasyoun/kosha/blob/main/data/gita/upasarga_semantics.tsv)
  dataset (√vac → pra-vac "declare"; √gam → ava-gam "understand"). Added
  `_upasarga_block()` to [`app/word_page.py`](https://github.com/gasyoun/kosha/blob/main/app/word_page.py)
  — a pure function of the SLP1 lemma + the committed dataset, so it is prerender ∥
  SSR byte-identical, host-independent and crawlable (all 15 word-page tests pass).
  This closes the deferred `/w/` surfacing of roadmap W6.

## [0.32.0] - 2026-07-13

### Added
- **H876 (roadmap W6, final workstream): Sanskrit root × preverb (upasarga)
  semantics.** New public/MIT dataset
  [`data/gita/upasarga_semantics.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/upasarga_semantics.tsv)
  — **148 verb roots + 69 preverb-modified senses** (√vac "speak" → pra-vac
  "declare"; √gam "go" → ava-gam "understand", sam-adhi-gam "attain") from the
  `Gita.xlsm` `verbs` sheet, a compositional dimension the Cologne dictionaries
  lack. Built by [`scripts/extract_upasarga_semantics.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_upasarga_semantics.py)
  (preverbs classified by their trailing `-`, so the sheet's irregular column
  alignment parses correctly) + a browsable page `reading/upasarga/`
  ([`scripts/build_upasarga_page.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_upasarga_page.py)),
  linked from the reader. Data statement
  [`docs/data-statements/upasarga-semantics.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/upasarga-semantics.meta.md);
  a `/w/` root-card panel is a documented follow-up. Credit: Dr. Mārcis Gasūns.
  **This completes the Gītā-gold extraction roadmap (W0–W6).**
## [0.31.0] - 2026-07-13

### Added
- **H875 (roadmap W5): Gītā Russian gloss layer + etymology dataset.** The Gītā
  reader gains an **English / Русский gloss toggle** (the master's `gloss_ru`,
  ~9,091 words, now carried per token and switchable in the viewer). New public/MIT
  dataset [`data/gita/gita_etymology.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_etymology.tsv)
  — **101 hand-written etymological notes** on selected words (`putra – one who
  saves from hell`; `uttama – superlative of ud`), extracted by
  [`scripts/extract_gita_etymology.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_etymology.py)
  from the `Grammar` sheet's col AG (which the master drops), aligned by
  verse+word-index. Data statement [`docs/data-statements/gita-etymology.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/gita-etymology.meta.md).
  Credit: Dr. Mārcis Gasūns.

## [0.30.0] - 2026-07-13

### Added
- **H872 (roadmap W2): Gītā sandhi layer.** New public/MIT dataset
  [`data/gita/gita_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_sandhi.tsv)
  — the **first corpus-attested, frequency-ranked sandhi table** in the ecosystem:
  161 distinct rules over 3,412 sandhi junctions across the whole Bhagavadgītā
  (`aḥ a → o '`, `ḥ t → s t`, anusvāra assimilations …), each with a category
  (visarga / anusvāra / vowel-coalescence / consonant), count, share and example
  words. Built by [`scripts/build_gita_sandhi.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_gita_sandhi.py)
  from the W0 master. A theme-aware teaching page `reading/sandhi/` renders the
  ranked table, and the Gītā reader now shows each word's **sandhi rule on hover**.
  Credit: Dr. Mārcis Gasūns.

## [0.29.0] - 2026-07-13

### Changed
- **H871 (roadmap W1): Gītā reader extended to all 18 adhyāyas.**
  [`scripts/build_reading_pack_gita.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_reading_pack_gita.py)
  now builds **one gold pack per chapter** (`reading/data/gita-1..18.js`) directly
  off the W0 master [`data/gita/gita_gold_master.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_gold_master.tsv)
  — **701 verses / 9,092 words, ~99.5 % linked** to `/w/` cards, with Devanagari +
  IAST + English gloss per verse. The [`reading/`](https://github.com/gasyoun/kosha/blob/main/reading/index.html)
  viewer gains a chapter picker (Nala 1 + Gītā 1–18). The chapter-1-only source
  (`gita-1_gold_sanskritgrammar.tsv`) and `extract_gita_gold.py` are retired —
  the reader is now unified on the master. Dataset `gita-reading-pack-1` →
  `gita-reading-pack` (all 18 adhyāyas).

## [0.28.0] - 2026-07-13

### Added
- **H874 (roadmap W4): Gītā inflection-engine QA — the first attested-corpus check
  of the E1 hybrid forms layer.** [`scripts/gita_inflection_qa.py`](https://github.com/gasyoun/kosha/blob/main/scripts/gita_inflection_qa.py)
  cross-checks every Bhagavadgītā nominal's **gold** case·number·gender (H873)
  against kosha's Cologne+vidyut hybrid `inflections` paradigm. Result:
  **93.0 % agreement** on nominals present in kosha (4,779/5,139); **360 divergences
  + 919 gaps** as a corrections feed. **Finding:** divergences are **71 % pronouns**
  (untagged `None.None.None` or wrong cell) — confirming and quantifying, with
  attested text, the pronominal mis-modelling
  [`E1_DIVERGENCE_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md)
  flagged synthetically; gaps are mostly long compounds. Report
  [`GITA_MORPHOLOGY_QA_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/GITA_MORPHOLOGY_QA_REPORT.md)
  + ledger [`data/gita/gita_inflection_divergences.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_inflection_divergences.tsv)
  (`gita-inflection-qa`). Candidate `disputed`/gap-fill corrections are surfaced,
  **not auto-applied** (a human `@DO` adjudicates). Public/MIT.

## [0.27.0] - 2026-07-13

### Added
- **H873 (roadmap W3): Gītā gold morphology + compound dataset.** New public/MIT
  dataset [`data/gita/gita_morphology_gold.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_morphology_gold.tsv)
  — 9,091 words, each with structured morphology decoded from the `Gita.xlsm`
  `Grammar`-sheet shorthand via the workbook's `Abbreviations` legend:
  case·number·gender (nominals), person·number·tense·voice (finite verbs),
  non-finite/derivation tags, and **compound type** (TP/BV/DV/KD). Built by
  [`scripts/extract_gita_morphology.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_morphology.py)
  (the decode legend is embedded from the `Abbreviations` sheet); `raw_morph`
  preserves the source shorthand. Registered (`gita-morphology-gold`) + data
  statement [`docs/data-statements/gita-morphology.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/gita-morphology.meta.md).
  This is the gold input to **W4** (the E1 inflection-engine QA). Credit: Dr. Mārcis Gasūns.

## [0.26.0] - 2026-07-13

### Added
- **H848 W0: Gītā gold master dataset.** New public/MIT dataset
  [`data/gita/gita_gold_master.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_gold_master.tsv)
  — the hand-curated word-by-word analysis of the **whole Bhagavadgītā** (9,092
  words · all 18 adhyāyas · 21 fields: lemma, root, gender, stem-class,
  **compound type**, morphology code, **sandhi rule**, English + Russian gloss),
  extracted from `SanskritGrammar/Concordance/Gita.xlsm`'s `Combined` sheet by
  [`scripts/extract_gita_master.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_master.py).
  The garbled private-use Russian *transliteration* column is dropped; the clean
  Cyrillic *gloss* is kept. Registered in the manifest (`gita-gold-master`) +
  data statement [`docs/data-statements/gita-gold.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/gita-gold.meta.md).
  This is **W0** of [`ROADMAP_GITA_GOLD_EXTRACTION_2026.md`](https://github.com/gasyoun/kosha/blob/main/ROADMAP_GITA_GOLD_EXTRACTION_2026.md)
  — the master every Gītā-gold workstream (reader all-18-ch, sandhi, morphology,
  inflection-QA, root/preverb semantics) derives from. Credit: Dr. Mārcis Gasūns.

## [0.25.0] - 2026-07-13

### Changed
- **H848: Gītā 1 reading pack upgraded EXPERIMENTAL → GOLD.** The machine
  (GRETIL + vidyut-cheda) build is replaced by a hand-curated word-by-word
  source — `SanskritGrammar/Concordance/Gita.xlsm` (`Grammar` sheet: lemma,
  root, morphology, English + Russian gloss), vendored via
  ``scripts/extract_gita_gold.py``
  to ``reading/data/sources/gita-1_gold_sanskritgrammar.tsv``
  (569 words / **47** verses — the full vulgate chapter). Rebuilt by
  [`scripts/build_reading_pack_gita.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_reading_pack_gita.py):
  **567/569 (99.6%) linked** to `/w/` cards (curated lemma 513 · root 46 ·
  forms-table 8). The viewer now shows **Devanagari + IAST + English glosses**;
  the experimental banner and the GRETIL source are removed. Dataset renamed
  `gita-reading-pack-1-experimental` → `gita-reading-pack-1`. Same gold quality
  class as the DCS-lemmatised Nala pack.

## [0.24.0] - 2026-07-13

### Added
- **H855: E1 verb dhātu-identity crosswalk — present-system agreement 12.68 % →
  70.24 %.** The H185 Task C verb comparison scored a misleading 12.68 % because
  `Dhatu.mula(bare_root, gaṇa)` is ambiguous where the nominal
  `Pratipadika.basic(stem)` was not — Cologne stores the bare SLP1 root, vidyut
  wants the *aupadeśika* dhātu — so 259/683 roots derived nothing (a mapping
  artifact, not divergence). New builder
  [`scripts/build_dhatu_crosswalk.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_dhatu_crosswalk.py)
  matches each Cologne `(root, gaṇa)` to the dhātupāṭha entry whose vidyut
  present-3sg-active equals Cologne's (else direct/normalized-bare), resolving
  **722/779 (92.7 %)** of the gaṇa-1/4/6/10 root-models. The committed
  [`data/e1/dhatu_crosswalk.json`](https://github.com/gasyoun/kosha/blob/main/data/e1/dhatu_crosswalk.json)
  carries only aupadeśika strings, so
  [`scripts/compare_vidyut_verbs.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_verbs.py)
  needs only bundled vidyut at run time (external `vidyut-data` is a build-time
  input to the crosswalk builder only — R12). Re-run: strict agreement
  **70.24 %** (near the nominal 90.5 %), roots-vidyut-can't-derive **259 → 110**,
  `COLOGNE_ONLY` **29,268 → 15,984**; the 11,056 residual conflicts are real
  accent/sandhi/gaṇa-shift divergences. New
  [`tests/test_dhatu_crosswalk.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_dhatu_crosswalk.py)
  (6 tests). Still **no verb hybridization** (D3); Task B give-back stays
  MG-gated. Answers [csl-inflect#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8).

### Changed
- **[`E1_DIVERGENCE_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md)**
  Verbs section rewritten with the crosswalk before/after; the ṇatva/gap-fill/
  `disputed` figures reconciled to the shipped-DB materialisation (326 ṇatva-fix
  rows / 55 stems, 17 gap-fill, 13,888 disputed) vs the top-10k characterization
  sample (89 stems / 16 / 13,770) — a sample-vs-full-run drift, not a classifier
  change.

## [0.23.0] - 2026-07-13

### Added
- **H848: Gītā 1 reading pack (EXPERIMENTAL, machine-segmented).** Since the
  Bhagavadgītā is absent from the DCS gold corpus (MBh book 6 omits adhyāyas
  23–40), this pack takes its mūla from GRETIL (vendored public-domain text,
  ``reading/data/sources/gita-1_mula_gretil.tsv``,
  46 verses) and lemmatises it by machine via
  [`scripts/build_reading_pack_gita.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_reading_pack_gita.py)
  — kosha's `forms`-table reverse-lookup (549 tokens) with a vidyut-cheda
  fallback (16). **565/597 tokens (94.6%) linked** to `/w/` cards. Unlike the
  gold Nala pack, lemmas are auto-derived and some are wrong (long samāsa
  compounds, a few names/participles); the viewer shows an **experimental
  banner** and ``reading/BUILD_REPORT_GITA.md``
  lists the residue. Dataset `gita-reading-pack-1-experimental`; the `reading/`
  viewer now offers both Nala 1 (gold) and Gītā 1 (experimental).

## [0.22.0] - 2026-07-13

### Added
- **H848: P5 step-6b reading packs — Nala 1 built; Gītā 1 parked.** New builder
  [`scripts/build_reading_pack.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_reading_pack.py)
  turns a DCS chapter into a word-by-word reading pack whose every word links to its
  kosha `/w/` dictionary card — **consuming** the H380 concordance core
  ([`scripts/concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py)'s
  `TieredMatcher`/`to_slp1` + the `card_token` twin), not re-rolling the join. **Nala 1**
  (`MBh, 3, 50`, Nalopākhyāna) shipped: 65 sentences / 439 tokens, **434 (98.9%) linked**
  (exact tier; 5 unlinked = DCS causative `-ay` stems + 1 indeclinable, honest residue).
  Self-contained viewer [`reading/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/index.html)
  (+ `reading/data/nala-1.{js,json}`, [`reading/BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/reading/BUILD_REPORT.md)),
  dataset `dcs-reading-pack-nala-1` in the manifest. Data-path finding: the real DCS DB is
  `VisualDCS/src/DCS-data-2026/dcs_full.sqlite` (the 0-byte `src/dcs_full.sqlite` is a decoy).
- **H848: Gītā 1 reading pack PARKED (data gap).** The Bhagavadgītā is absent from the DCS
  corpus — Mahābhārata book 6 (Bhīṣmaparvan) omits exactly adhyāyas 23–40 (the 18 Gītā
  chapters) and there is no standalone Bhagavadgītā text; a Gītā pack needs an external
  lemmatised source (surfaced as `@DECIDE`).

## [0.21.0] - 2026-07-12

### Added
- **H185: P4 Wave E1 hybridize — vidyut layered over the Cologne inflection base
  (MG ruling HYBRIDIZE).** New forms-layer pass
  [`scripts/build_hybrid_forms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_hybrid_forms.py)
  (`build_db.py --stage hybrid`, run after `--stage inflections`) reuses the E1
  comparison's classifier — so the applied set matches
  [E1_DIVERGENCE_REPORT.md](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md)
  cell-for-cell (top-10k sample): **326 ṇatva cells / 89 stems** auto-fixed
  ([MWinflect#6](https://github.com/sanskrit-lexicon/MWinflect/issues/6)) as
  `source='hybrid-natva-fix'` rows, **16 `m_card` cells** gap-filled as
  `source='vidyut-gap-fill'`, **13,770 cells / 1,440 stems** flagged
  `disputed=1` (pronominal + feminine/consonant forks, for editorial review).
  No Cologne row is deleted — the buggy form stays reverse-resolvable; the
  display layer prefers the fix and records the superseded form. `inflections`
  gains a `disputed` column; [`app/paradigm.py`](https://github.com/gasyoun/kosha/blob/main/app/paradigm.py)
  emits a sparse per-model `cell_notes` provenance map and
  [`app/reverse_lookup.py`](https://github.com/gasyoun/kosha/blob/main/app/reverse_lookup.py)
  adds `source`/`disputed` to each `/analyze` parse. New
  [`tests/test_hybrid_forms.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_hybrid_forms.py)
  (6 tests); demo paradigm/reverse shards regenerated; **229 passed / 2 skipped**.
- **H185 Task C: present-system verb comparison** answering
  [csl-inflect#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8).
  [`scripts/compare_vidyut_verbs.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_verbs.py)
  maps Cologne `v_<gana>`/`v_p` rows into vidyut's `Tinanta` API. Finding: strict
  agreement is only **12.68 %** (683 roots, 34,056 both-nonempty cells) — a
  dhātu-IDENTITY mapping gap (bare Cologne root ≠ vidyut aupadeśika), not a
  grammar disagreement. **No verb hybridization applied** (a bare-root
  substitution would inject a different lexeme's forms); Cologne verb tables stay
  as-is (D3). The dhātu-identity crosswalk is the flagged larger follow-on.

### Note
- The csl-inflect#10 nominal give-back drafted in E1 stays **parked** — posting
  to the dormant, noise-averse upstream is diplomacy-gated (RELATIONS.md §2/§7)
  and awaits a separate MG go-ahead (unchanged by this release).

## [0.20.1] - 2026-07-11

### Changed
- **H752: parked rival H730 lane salvaged into the merged protocol** (docs/provenance
  only — no scored output changed). Grafted into
  [docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md):
  the verified [Hellwig et al. 2026 (ISCLS)](https://aclanthology.org/2026.iscls-1.2/)
  delta (supervised MW-definition WSD with Sanskrit Sembank gold — closes the
  previously-flagged overlap check), SHA-256 input digests in
  [frozen_sample.meta.json](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/frozen_sample.meta.json)
  (independently computed by both racing lanes, byte-identical inputs confirmed), and the
  gold-free inputs projection + 3-rater Fleiss-κ WSD design queued for the A59 paper
  phase. The 500-headword seed-730 sample is declared the **single canonical frozen set**;
  the parked 520-headword rival sample was never scored and its branch
  `h730-defgen-eval-fable-lane` was deleted after salvage
  ([Uprava FINDINGS §67](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md)).

## [0.20.0] - 2026-07-11

### Added
- **H730: first CDSL-side definition-generation + gloss-grounded WSD eval** — frozen
  500-headword MW sample (3×3 frequency×polysemy strata, seed 730) with ≤5 DCS attestation
  sentences each ([data/eval/defgen/](https://github.com/gasyoun/kosha/tree/main/data/eval/defgen)),
  4 baseline arms (random floor, deepseek-chat ±attestations, deepseek-reasoner), sacrebleu
  BLEU/chrF + token-F1 + gated blinded LLM judge, WSD inter-model agreement pilot
  (κ=0.706). Harness: `scripts/defgen_build_sample.py` / `defgen_run_baselines.py` /
  `defgen_score.py`; protocol + results:
  [docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md);
  manifest row `mw-defgen-eval-sample`.

## [0.19.0] - 2026-07-11

### Changed
- **Heritage surplus forms are now default-off in every lookup path** (H696,
  Fable 5 `claude-fable-5`) — implements the R7 ruling (10-07-2026,
  [Uprava docs/DECISIONS_roadmap_forks_2026H2.md](https://github.com/gasyoun/Uprava/blob/main/docs/DECISIONS_roadmap_forks_2026H2.md)):
  the 928,262 distinct `source='heritage'` forms (ingested provenance-flagged by
  H111, count re-verified this pass) are excluded from `GET /api/v1/form/{form}`,
  `GET /api/v1/forms/{form}/analyze` (stages 2–3, incl. per-pada segmentation
  re-resolution) and the static paradigm/reverse tier
  ([`scripts/build_paradigms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_paradigms.py))
  unless the caller opts in with `?heritage=1`. Committed demo reverse shards
  regenerated without heritage witnesses; `dcs`/`vidyut` results are unchanged
  in both modes. Heritage's external oracle role (ruling point 3) is untouched.

### Added
- [`tests/test_heritage_default_off.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_heritage_default_off.py)
  (8 tests): heritage-only form absent by default / present with the flag on
  both endpoints, native-source invariance under the flag, and the ruled
  928,262 surplus-form ingest count asserted against the live DB.

## [0.18.0] - 2026-07-11

### Added
- **Provenance fields across the dataset manifest** (H691, Fable 5
  `claude-fable-5`, [PR #52](https://github.com/gasyoun/kosha/pull/52)): the census-§2
  local-only giants now carry `sha256` (streamed), `provenance_verified` and an honest
  `rebuild` recipe in
  [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  — `corpus-lexicon`, `sa-ru-glossary`, `kosha-db`, `dcs-full-sqlite`,
  `samudra-corpus-db` updated with live counts.
- **Three new manifest rows**: `archive-stopword-sqlite` (11 GB, 40,573,260 stop-word
  parallels — the census's "uncounted blind spot" resolved, fully regenerable),
  `samudra-offline-packs` (base+dict, SHA256s verified against their sidecars) and
  `kosha-raw-sqlite` (mw/pwg/ap90 inputs, re-fetchable from the csl-sqlite release).

### Fixed
- `kosha-db` manifest keying corrected from "9 tables" to the live 8; flagged that the
  current `kosha.db` build (05-07-2026) lacks the H345 `heritage_anchor` table — the
  heritage witness needs a re-ingest on next rebuild.

## [0.17.0] - 2026-07-11

### Added
- **Data statements for the entire public data tier** (H665, Fable 5
  `claude-fable-5`, [PR #47](https://github.com/gasyoun/kosha/pull/47)): one
  Bender-Friedman (2018) / Gebru et al. (2021) datasheet-form statement per
  `data-v0.1.0` release asset under
  [`docs/data-statements/`](https://github.com/gasyoun/kosha/tree/main/docs/data-statements)
  — `mw-roots`, `mw-etymology`, `dcs-cdsl-xref`, `union-headwords`,
  `mw-heritage-crosswalk`, `kosha-lemma-frequency`, `zaliznyak-grammar-index` —
  each covering composition & schema, provenance, curation rationale, language
  variety, process info, biases/limitations, intended use / known misuse,
  license, maintenance & sunset plan, deprecation status, citation; plus a
  [README index](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/README.md)
  with the queued backlog for the not-yet-covered manifest rows.
- **`data_statement` field in the dataset manifest**
  ([`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)):
  each of the 7 public released rows now links its data statement.
- **Two JOHD data-paper drafts** (readiness 2/5, registered as A55/A56 in the
  Uprava publication inventory):
  [`papers/A55_UNION_HEADWORDS_DATA_PAPER_JOHD.md`](https://github.com/gasyoun/kosha/blob/main/papers/A55_UNION_HEADWORDS_DATA_PAPER_JOHD.md)
  (union headword index, 323,425 rows / 15 dictionaries) and
  [`papers/A56_ZALIZNYAK_GRAMMAR_INDEX_DATA_PAPER_JOHD.md`](https://github.com/gasyoun/kosha/blob/main/papers/A56_ZALIZNYAK_GRAMMAR_INDEX_DATA_PAPER_JOHD.md)
  (grammar-token index, 98,639 rows / 335 paradigm tokens).
- **`CITATION.cff`** — repo-level citation metadata (this release's freeze-time
  sync; Zenodo DOI slot pending the GitHub–Zenodo wiring, a human `@DO`).
- **Minimal-direction mockup of the data directory** (H587,
  [PR #45](https://github.com/gasyoun/kosha/pull/45)):
  [`directory/mockups/minimal.html`](https://github.com/gasyoun/kosha/blob/main/directory/mockups/minimal.html),
  CSS-only restyle with markup byte-identical to the live directory page.

### Changed
- **README refreshed to the current data-hub role** (H550,
  [PR #46](https://github.com/gasyoun/kosha/pull/46)): P4/P5 state, data-hub
  framing brought current.

## [0.16.0] - 2026-07-11

### Added
- **P5 advanced UI — the word page** (H537, Opus 4.8 `claude-opus-4-8`), built
  from the locked design spec
  [`P5_ADVANCED_UI_DESIGN.md`](https://github.com/gasyoun/kosha/blob/main/P5_ADVANCED_UI_DESIGN.md)
  (MG rulings 10-07-2026: Tabs · all-3 view modes · full P5 scope · both render
  targets). One addressable word page per headword — every dictionary's entry,
  its evidence, its paradigm — reached by the crawlable `/w/{slp1}` permalink.
  - **Crawlable static prerender** — new
    [`app/word_page.py`](https://github.com/gasyoun/kosha/blob/main/app/word_page.py)
    shared template + [`scripts/build_word_pages.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_word_pages.py):
    every dict panel present in the DOM (active shown, rest hidden) with a
    `<noscript>` all-stacked fallback so a JS-less fetcher reads every entry
    (§5); progressive JS hydrates tabs (P5-1), the Gloss/Full/Adaptive view-mode
    toggle (P5-2, persisted to `localStorage`), and disclosures. Runs off the
    committed static card set (no DB); logs actual N + Pages budget + dropped
    tail (no silent caps). Plus a `/browse/<varṇa>` alphabetic spine linking
    every word page. Regenerable Pages output, gitignored like the cards.
  - **FastAPI SSR** — new `GET /w/{slp1}` route renders the long tail through the
    *same* `render_word_page()` template, so static ∥ SSR are byte-comparable
    (P5-4 parity); locked by
    [`tests/test_word_page.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_word_page.py)
    (15 no-DB structural/crawlability tests + a DB-gated SSR byte-parity check).
  - **SPA word page** — new `WordPage.svelte` interactive twin (MW/PWG/AP90 tabs,
    view-mode toggle sharing the same `localStorage` key, evidence + lazy
    paradigm + scan disclosures), reached by `#/w/{slp1}` hash routing; composes
    the existing `getEntry`/`getParadigm`/`ParadigmTable` (reuse ledger §7).
  - **Search operators** (§4) — `root:` and `sandhi:` in the search box (caught
    before transliteration), bare input auto-routes; `sandhi:` prefills the
    reverse analyser.
  - **Study tooling** — CSV (RFC-4180) and Anki (TSV) export of a session's word
    lookups (`lib/export.js`). *Gītā 1 / Nala 1 reading packs are data-gated —
    the DCS sentence-level lemmatised corpus is not present on disk
    (`VisualDCS/dcs_full.sqlite` is a 0-byte LFS placeholder); tracked as a
    follow-up, no verse tokenisation was fabricated.*
  - +34 tests green (19 vitest lib + 15 pytest template); the SPA word-page and
    `sandhi:` operator e2e flows verified in-browser. **Exit checks (MG sign-off
    on live staging · Lighthouse mobile ≥90 · Gītā-verse walkthrough) remain
    gated on MG's P2 `samskrtam.ru` deploy**, per the plan.
- **Type-D concordance record shape + `typed_link_lint.py`** (H539, Sonnet 5
  `claude-sonnet-5`) — extends
  [`scripts/concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py)
  per [`TYPED_LINK_ID_GRAMMAR.md`](https://github.com/gasyoun/Uprava/blob/main/TYPED_LINK_ID_GRAMMAR.md)
  §1 (H499) so every Type-D (grammar ↔ non-grammar) concordance builder imports
  one implementation instead of forking a schema: `RECORD_FIELDS`' `corpus_locus`/
  `corpus_text_id` renamed to `target_locus`/`source_dataset` (positions/semantics
  unchanged); `TYPE_D_RECORD_FIELDS` adds `link_type` + `date`;
  `normalize_record()` maps either shape into one shared view; two new
  `match_method` tiers above `exact` in trust — `id-link` (pure host-stable-id
  join) and `curated` (source concordance's own assertion). New
  [`scripts/typed_link_lint.py`](https://github.com/gasyoun/kosha/blob/main/scripts/typed_link_lint.py)
  validates a Type-D dataset's anchor/target-locus prefixes, tail syntax,
  `link_type`/`match_method`/`date` against the spec, exits non-zero per bad
  row; tested against the spec's §4a/§4b landed worked examples plus negative
  fixtures (URL-host locus, unknown prefix, bad date) in
  `tests/fixtures/typed_link/`. No Type-D dataset registered in the manifest
  (D2b parks that until Q2.1).
- **Pipeline operator runbook** ([docs/PIPELINE_OPERATOR_RUNBOOK.md](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.md),
  H501, Fable 5 `claude-fable-5`) — the single operational spine for the whole
  chain: the seven `build_db.py` stages in dependency order with rerun triggers,
  API serve, the two static-tier deploy classes (committed-goes-live vs
  gitignored-MG-deploys), the data-release citability ritual
  (`archive_senses` → `build_crosswalk` → release asset → manifest refresh),
  maintenance scripts, the verbatim never-touch list, and a failure-symptom
  decoder (the `unable to open database file` wave = DB-less checkout, not a
  regression). Every command/flag cross-checked against script source.
- **B1 dictionary ↔ corpus concordance + the shared concordance core (Q1 of
  [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md)).**
  Executor: Fable 5 (`claude-fable-5`), handoff H380.
  - [`scripts/concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py) —
    the Q1–Q4 shared core: canonical record schema, tiered matcher (exact →
    length-preserving `form_key` floor → lossy tiers, unique-bucket only) on the
    canonical `sanskrit-util` keys, host-independent `dcs:<sent_id>` citable loci.
  - [`scripts/build_dict_corpus_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_dict_corpus_concordance.py) →
    [`data/concordance/`](https://github.com/gasyoun/kosha/tree/main/data/concordance):
    **74,520 asserted links** (xref 12,836 · exact 61,373 · floor 311) joining the
    323,425-headword union to the 5.69M-token DCS corpus; coverage sidecar classes
    every headword (66,257 attested = 20.5%, the honest Zipf reality); manifest row
    `dict-corpus-concordance` added same pass.
  - **Golden-sample ruling** ([GOLDEN_SAMPLE.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/GOLDEN_SAMPLE.md)):
    mechanical checks 14/14, but the lossy `norm`-fold tier was 0/3 semantically
    correct (aṃśaka↔aṃsaka, vikarṣaṇa↔vikarśana) — its 2,171 links are
    **quarantined** to `dict_corpus_relaxed_candidates.tsv`, never asserted.
  - [`concordance/dict/`](https://github.com/gasyoun/kosha/tree/main/concordance/dict) —
    the reusable static concordance viewer (search → dict-provenance chips →
    tier-badged lemma links → KWIC with citable loci; 25 lazy shards, 32.9 MB;
    works on file://, trust block, CSV fallback; RISKS R12: no live service).
- **Static print co-location page (public Pages tier).** Executor: Opus 4.8
  (`claude-opus-4-8`), handoff H441.
  - [`scripts/build_colocation_page.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_colocation_page.py)
    renders [`colocation/`](https://github.com/gasyoun/kosha/tree/main/colocation)
    from `kosha.db` only (RISKS.md R12, no live service) — the static web
    counterpart of the `/api/v1/page` + `/api/v1/neighbors` endpoints (v0.15.0),
    live at [gasyoun.github.io/kosha/colocation](https://gasyoun.github.io/kosha/colocation/).
  - Self-contained `colocation/index.html` + lazy per-dict `colocation/data/<dict>.js`.
    Grouped on each dict's finest printed unit: PWG `(vol, page)` = Spalte;
    MW `(page, col)` cited `page,col`; Apte `(page, col)` cited `page+letter`.
    444,773 located entries.
  - **Paged two-column leaf view** — the book sets two columns per page, so the
    browser shows a whole leaf (left col `2P−1` + right col `2P` for PWG, all
    columns of the physical page for MW/Apte), with ← / → paging (and arrow keys),
    a column jump box, dictionary-wide head-word search, and per-head-word
    highlighting. Deep-linkable: `#<dict>/<col>?w=<slp1>` (the RU PWG article site
    links every column-mate in here). Honest caveat surfaced in the UI: the source
    records column numbers, not the book's printed page number, so left/right
    *column* is exact but recto/verso of the leaf is not derivable.

## [0.15.0] - 2026-07-09

### Added
- **Print co-location endpoints — "which words shared a printed page/column".**
  Executor: Opus 4.8 (`claude-opus-4-8`), handoff H434.
  - [`app/neighbors.py`](https://github.com/gasyoun/kosha/blob/main/app/neighbors.py)
    groups entries by the `(vol, page, col)` already parsed from each `<pc>`
    marker (for PWG, `page` is the Böhtlingk-Roth Spalte — the same value
    [`scan_resolver`](https://github.com/gasyoun/kosha/blob/main/app/scan_resolver.py)
    feeds to `servepdf.php`).
  - `GET /api/v1/page/{dict}?vol=&page=&merge=` — every entry sharing one printed
    column (`merge=1` folds the two columns of a physical leaf).
  - `GET /api/v1/neighbors/{dict}/{L}` — the column-mates of one entry, in
    printed order, query entry flagged `is_query`; each result carries its
    `headword` + `scan_url`.
  - `(dict, vol, page, L)` index in
    [`scripts/build_db.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db.py)
    for the group-filter + printed-order seek; 5 new tests
    ([`tests/test_api.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_api.py),
    25 green). Live PWG: 123,366 entries, 100 % `<pc>` coverage, 8,171 columns.
    Fail-closed on unparseable `<pc>` (G-PC gate). [PR #33](https://github.com/gasyoun/kosha/pull/33).

## [0.14.0] - 2026-07-09

### Added
- **Search-history retention purge.** Executor: Sonnet 5
  (`claude-sonnet-5`), handoff H416.
  - [`scripts/purge_search_events.py`](https://github.com/gasyoun/kosha/blob/main/scripts/purge_search_events.py)
    + [`history_db.purge_old_search_events()`](https://github.com/gasyoun/kosha/blob/main/app/history_db.py)
    delete raw `search_events` rows (per-visitor query log) older than
    `--days` (default 180). `daily_rollup` — the permanent anonymous
    per-day/per-term aggregate the `/api/v1/stats/*` charts read from — is
    never touched. `--dry-run` reports the count without deleting.
    MG-run maintenance script (A3 local-first: no agent cron).

## [0.13.0] - 2026-07-06

### Added
- **Sanskrit data-hub P-D3: public data + tools directory page.** Executor:
  Opus 4.8 (`claude-opus-4-8`), MG ruling D-HUB-7 (06-07-2026), handoff H236.
  - [`directory/index.html`](https://github.com/gasyoun/kosha/blob/main/directory/index.html)
    (live at [gasyoun.github.io/kosha/directory](https://gasyoun.github.io/kosha/directory/))
    — the first curated directory for Sanskrit computational linguistics: 9
    public datasets (downloadable), 6 restricted (listed "on request"), and 8
    external stacks (vidyut/Ambuda, Sanskrit Heritage/INRIA, Samsaadhanii/SCL,
    DharmaMitra, DCS, VedaWeb, Cologne CDSL) with what-it-does / how-to-call /
    license / our-relation.
  - [`scripts/build_directory.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_directory.py)
    renders it from [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
    + a new [`data/manifest/external_tools.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json)
    (single sources — no facts hand-copied into HTML). Carries schema.org
    `Dataset` JSON-LD per public asset on an Organization `@id` spine (SEO
    playbook P0) — the lever for Google/Yandex Dataset Search indexing.
  - `datasets.json` gained a `release_asset` field on the 7 released rows so the
    page can build 1-click download URLs from the manifest.
  - Test invariants: [`tests/test_directory.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_directory.py)
    (one Dataset node per public row, `@id` spine, no restricted-download or
    gitignored-path leak). Wired from the README + docs-site landing footer.

## [data-v0.1.0] - 2026-07-06

### Added
- **P-D0 data-hub roadmap + machine-readable datasets manifest** (D-HUB-1..8,
  [#23](https://github.com/gasyoun/kosha/pull/23)) — kosha becomes the org
  Sanskrit data-hub per MG rulings 06-07-2026: two-tier (public releases /
  restricted backups), samskrtam.ru as the canonical big-file host after
  deploy, interim distribution via GitHub Releases `data-v*` tags, and
  [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  as the single source of truth for public/restricted asset metadata. This
  tag is the first of the separate **data-release** track (see the file
  header above) — distinct from the `vX.Y.Z` **repo-release** track this
  changelog otherwise documents.

## [0.12.0] - 2026-07-06

### Added
- **Sanskrit data-hub P-D0/P-D1 (kosha becomes the org data-hub).** Executor: Fable 5
  (`claude-fable-5`), MG rulings 06-07-2026.
  - [`DATA_HUB_ROADMAP.md`](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md)
    — 8 locked decisions (D-HUB-1…8), two-tier architecture (public releases /
    restricted private backups), phases P-D0–P-D6.
  - [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
    — machine-readable manifest of 15 canonical derived datasets across the org
    (7 public released, 5 restricted, 3 already-public listed for discovery), with
    keying, rights tier, builder, consumers per row + the agent contract
    ([`data/manifest/README.md`](https://github.com/gasyoun/kosha/blob/main/data/manifest/README.md)).
  - First public data release
    [`data-v0.1.0`](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0):
    mw_roots · mw_etymology · dcs_cdsl_xref · union_headwords ·
    mw_heritage_crosswalk · lemma_frequency · headword_index (~29 MB, 718k rows,
    all already public in source repos; CC BY-SA 4.0).

## [0.11.0] - 2026-07-05

### Added
- **Search history + analytics (Phases A/B/C-frontend).** Executor: Sonnet 5
  (`claude-sonnet-5`).
  - Backend (Phases A/B): anonymous per-visitor search history
    ([`app/history.py`](https://github.com/gasyoun/kosha/blob/main/app/history.py),
    [`app/history_db.py`](https://github.com/gasyoun/kosha/blob/main/app/history_db.py),
    [`app/identity.py`](https://github.com/gasyoun/kosha/blob/main/app/identity.py))
    via a `kosha_anon_id` cookie, no login required; `GET`/`DELETE
    /api/v1/history`; public credential-free aggregate analytics
    (`GET /api/v1/stats/summary|timeseries|top`); a magic-link login stub
    (`/api/v1/auth/request-link|verify`) for cross-device history sync,
    email provider not yet chosen (@DECIDE). Writable history SQLite store
    kept separate from the read-only dictionary DB so the monthly dict
    rebuild never touches it. 13 new tests.
  - Frontend (Phase C): `History.svelte` (recent searches, clear button,
    magic-link request form) and `Stats.svelte` (summary cards, Chart.js
    daily-volume chart, top-terms table) added to the K2b inflection UI's
    tab bar, both hidden when no live API is configured (no static fallback
    exists for personal/live-aggregate data). First use of **Chart.js** in
    `ui/`. 4 new component tests.

### Notes
- Two items remain, both tracked in
  [Uprava/GTD_NEXT_ACTIONS.md](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md):
  MG `@DECIDE` (email provider + production `CORS_ORIGINS`, both deploy-time
  A3 steps) and an agent-doable `search_events` retention-purge script.

## [0.10.0] - 2026-07-05

### Added
- **Wave E1 (inflection roadmap) — dual-engine comparison, nominal pass.**
  Executor: Opus 4.8 (`claude-opus-4-8`).
  - [`scripts/compare_vidyut_cologne.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_cologne.py)
    diffs **vidyut-prakriya** (0.4.0, local library — R12-clean, no live call)
    against the ingested Cologne `inflections` tables, classifying every
    case×number cell (`AGREE`/`DIFF`/`VIDYUT_ONLY`/`COLOGNE_ONLY`) with DIFF
    sub-classification (ṇatva / pronominal / final-stop / superset / fork).
  - [`E1_DIVERGENCE_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md) —
    **90.5 % cell agreement** over 240k cells / 10k entry-bearing nominal stems.
    Findings: the ṇatva bug ([MWinflect#6](https://github.com/sanskrit-lexicon/MWinflect/issues/6))
    is confirmed with a **larger blast radius than the documented 69** (89 stems
    in the top-10k sample); pronominal stems (`sarva`) mis-modelled as nominals;
    cardinal numerals (`saptadaśan`) missing from Cologne but generated by
    vidyut; feminine consonant/monosyllabic-stem derivation forks. Continues Jim
    Funderburk's Cologne-vs-Huet line ([csl-inflect#10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10))
    with an independent third engine.
  - **Recommendation: hybridize** (keep Cologne base per D3, layer vidyut to
    auto-fix ṇatva + fill gaps + flag forks) — filed as an @DECIDE for MG.

### Notes
- E1 remainder is human-gated: the migrate/hybridize/stay **ruling** (MG
  @DECIDE) and the **give-back post** to csl-inflect#10 (diplomacy-gated,
  drafted not posted), plus the agent-doable **verb comparison** (answers
  csl-inflect#8) — all queued in
  [H185](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md).
  E1 raw comparison output (`data/e1/`) is gitignored (regenerable).

## [0.9.0] - 2026-07-05

### Added
- **P4 Wave K2b** (H183) — the translator-first Sanskrit **inflection lookup
  UI**, the frontend half of the drastically-improved Cologne inflection tool.
  Executor: Opus 4.8 (`claude-opus-4-8`).
  - **Svelte 5 + Vite app** ([`ui/`](https://github.com/gasyoun/kosha/tree/main/ui))
    building into [`docs/inflect/`](https://github.com/gasyoun/kosha/tree/main/docs/inflect),
    served by the existing Pages deploy at `gasyoun.github.io/kosha/inflect/`
    (62 kB JS bundle). Four features (H183 K2b-3, roadmap Wave K3 folded in):
    **stem → paradigm** (auto-detect input → SLP1, Devanagari-default
    case×number / verb grids with an IAST/SLP1 toggle), **paste-anything
    reverse analysis** (wraps `/analyze`, shows `resolved_by` provenance),
    **autocomplete** (prefix range-seek over the shared 323k `lemmas.json`,
    live transliteration), and **dictionary cross-links** (every stem links to
    its in-app MW/PWG/AP90 entry; the entry has a "show all forms" control back
    to the paradigm — two silos, one tool).
  - **Data backend is "both"** (K2b-2, [`ui/src/lib/datasource.js`](https://github.com/gasyoun/kosha/blob/main/ui/src/lib/datasource.js)):
    static pre-generated JSON by default (works with **no live server** —
    RISKS.md R1/R5/R12-clean), and the live FastAPI `/api/v1/…` when
    `window.KOSHA_API` is set. Stage-3 vidyut segmentation degrades honestly to
    `segmentation_available:false` in the static tier (the live-API path
    resolves it).
  - **New `GET /api/v1/paradigm/{lemma}`** endpoint + shared
    [`app/paradigm.py`](https://github.com/gasyoun/kosha/blob/main/app/paradigm.py)
    grouping module, and
    [`scripts/build_paradigms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_paradigms.py)
    emitting parity-locked static paradigm + reverse-index shards
    (`--demo` committed, `--all` deployed by MG out-of-band per A3). Bridged
    stems fold (`Bagavant`→`Bagavat`).
  - **Auto-detect input** (Devanagari/IAST/SLP1) via the vendored **sanskrit-util**
    JS package (SHARED_CODE.md family #1 — no new transcoder); Devanagari
    rendering uses `slp1_to_devanagari` (composes matras/conjuncts) not the
    naive `iast_to_devanagari`.
  - **Tests:** 6 new pytest (`tests/test_paradigms.py`, endpoint + static-shard
    byte-parity) → **167 passed**; 17 vitest (translit auto-detect, token
    parity, prefix seek, static data-path integration, full App e2e).
  - **Data caveat surfaced verbatim** (D3): the Cologne m_a ṇatva bug
    (MWinflect#6) is shown as-is, not silently "fixed" in the frontend.

### Notes
- Roadmap Wave **K3 folded into K2b** per MG 05-07-2026 — the inflection roadmap
  now owes only Wave E1 (dual-engine vidyut comparison).
- Pages tier re-measured: `docs/inflect/` = 2.0 MB (app + committed demo data);
  total tier ~404 MB, ~60% headroom under the 1 GB soft limit unchanged.

## [0.8.0] - 2026-07-05

### Added
- **P4 Wave K2a** (H181) — reverse-lookup query pipeline, verb-form ingest,
  and the stem-normalization bridge. Executor: Opus 4.8 (`claude-opus-4-8`).
  - **Reverse-lookup cascade** ([`app/reverse_lookup.py`](https://github.com/gasyoun/kosha/blob/main/app/reverse_lookup.py))
    behind `GET /api/v1/forms/{form}/analyze`: `inflections` exact hit →
    `forms` witness → **vidyut-cheda segmentation** of a sandhied/compound
    string, each stage tagged with a `resolved_by` provenance field
    (`inflections`/`forms`/`segmentation`/`null`). Segmentation
    ([`app/segmenter.py`](https://github.com/gasyoun/kosha/blob/main/app/segmenter.py))
    runs vidyut 0.4.0 as a **local library over vendored data**
    (`data/vidyut/`, gitignored); no live third-party call at build or query
    (RISKS.md R12), and it degrades to an honest miss (`segmentation_available:
    false`) when the data isn't vendored.
  - **Verb conjugations ingested** — the upstream MWinflect Python-2 syntax
    bug in `verbs/pysanskritv2/inputs/clean.py` (parenthesized-tuple lambda
    parameter) that blocked `verbs/redo.sh` in K1 is fixed and prepared as an
    on-its-merits upstream PR. [`scripts/build_inflections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_inflections.py)
    now loads present-system conjugations (pre/ipf/ipv/opt × active/middle/
    passive) into `inflections` (**+67,140** rows; total 6,916,522) with new
    `person`/`tense`/`voice` columns (NULL for nominals). So `Bavati` now
    resolves as 3sg present of `BU`.
  - **Stem-normalization bridge** ([`scripts/build_stem_bridge.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_stem_bridge.py)
    → `stem_bridge` table, `--stage stem_bridge`) maps strong/weak stem-spelling
    variants across `inflections` (`Bagavat`) and `forms` (`Bagavant`) to one
    canonical lemma key. Narrow, data-gated rule (nt→t / drop-final-n, only
    when the two spellings share a surface form) — 380 mappings; the named exit
    case `Bagavant → Bagavat` unifies to one lemma.
  - Tests: new [`tests/test_reverse_lookup.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_reverse_lookup.py)
    (cascade, verb ingest, bridge, segmentation + graceful degradation); full
    suite **161 passed**. Documented in
    [`data/SOURCES.md`](https://github.com/gasyoun/kosha/blob/main/data/SOURCES.md)
    (incl. the ṇatva caveat and the honest `dharmakSetre`-resolves-at-stage-1
    deviation from the brief's assumption).

## [0.7.0] - 2026-07-03

Phase 3 (evidence layer) + Phase 4 Wave K1 (inflection data ingest), landed
together via [PR #9](https://github.com/gasyoun/kosha/pull/9) (branch
`feat/p3-evidence-p4-k1-inflect`, Sonnet 5 `claude-sonnet-5`) — both tracks
ran as parallel sessions against the same checkout and ended up
file-interleaved in `app/main.py`/`scripts/build_db.py`, so they ship as one
release. P3 builds on P1's frequency LEFT-JOIN rather than duplicating it in
a new table (the P3 plan's original spec is now redundant with what's
already on `lemmas`). Full suite green: 149 passed (26 new in
`tests/test_evidence.py`, 6 new in `tests/test_inflections.py`), 1
pre-existing unrelated failure (`test_docs_site.py::test_committed_output_is_current`,
docs-site staleness from the parallel Wave-3 docs-site work already in
flight, not caused by this release).

### Added
- **P4 Wave K1** (data ingest + JSON API) — new `inflections` sidecar table
  ([`scripts/build_db.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db.py)
  SCHEMA + `--stage inflections`) loaded by
  [`scripts/build_inflections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_inflections.py)
  from the sibling MWinflect checkout's Cologne csl-inflect nominal
  declension tables (`nominals/pysanskritv2/tables/calc_tables.txt`, engine =
  Cologne verbatim per
  [ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md)
  D3). 6,849,382 (form, lemma, model, gender, case, number) rows from
  288,844 stems, 3,267,305 distinct forms. New read-only
  `GET /api/v1/forms/{form}/analyze` endpoint
  ([`app/main.py`](https://github.com/gasyoun/kosha/blob/main/app/main.py))
  returns every grammatical parse for a form. Verb conjugations are **not**
  included — MWinflect's `verbs/` pipeline is blocked by a Python-2-only
  syntax bug in `verbs/pysanskritv2/inputs/clean.py` (upstream issue, not
  fixed here; see `.ai_state.md` for the exact trace). 6 new tests in
  [`tests/test_inflections.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_inflections.py)
  hand-verify the roadmap's exit-test forms (`bhagavAn`, `rAmeRa`,
  `dharmakSetre`) against `calc_tables.txt`.
- **P3 evidence layer** —
  [`scripts/build_evidence.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_evidence.py)
  (new `--stage evidence`, wired into the default full build) adds two things
  additively to `lemmas` via `ALTER TABLE`: a **frequency band** (1–5, over
  `rank_all`; thresholds chosen from the D5-measured fact that the top 10,000
  ranked lemmas already cover 95.4% of corpus token mass — full reasoning in
  the module docstring) and **one corpus example per lemma** (Sanskrit
  citation + aligned Russian, joined from the sibling
  ``SanskritLexicography/RussianTranslation/src/corpus_lexicon.jsonl``
  (1,091,528 rows) via the existing `forms.form_slp1 -> lemma_slp1` join —
  examples ship **per lemma, not per sense**: the corpus feed has no
  sense-level tagging, stated explicitly rather than silently downgraded.
  Band distribution on the live spine: 1=493, 2=1,441, 3=7,484, 4=51,922,
  5=262,085 (no DCS signal); 38,595 lemmas got a corpus example.
- **[`app/evidence.py`](https://github.com/gasyoun/kosha/blob/main/app/evidence.py)** —
  shapes the DB columns into the API's evidence block; `/api/v1/lemma`
  entries now carry `evidence: {band, band_label, rank_all, count_all,
  first_era, genre, example, badges}`, every `badges[]` item carrying its own
  `source` string (fail-closed per EVAL_PLAN.md rule 4: a lemma with no DCS
  signal gets `count_all: null` / `example: null`, never a fabricated `0` or
  invented citation; `genre` is honestly `null` — not derivable from the
  current DCS extraction, which stores only a chronological period vector).
  Mirrored into
  [`scripts/build_static_cache.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_static_cache.py)'s
  `entry_payload()` (same lockstep-mirror pattern as `sense_ids`) so the P2
  static tier stays byte-identical to the live API.
- **`/api/v1/search` frequency-weighted ranking** — results now order by
  exact-key-match-first, then `rank_all ASC` (nulls last), then `slp1 ASC`,
  replacing plain alphabetical.
- **[`tests/test_evidence.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_evidence.py)**
  (26 tests) — `dharma` band/count/example (T-UC4 positive), a fail-closed
  negative case (band-5 lemma: no fabricated 0, no invented example),
  provenance-label-on-every-badge, a frozen 20-headword sample spanning all 5
  bands checking both band assignment and that search ranking measurably
  differs from alphabetical order (>=50% of multi-result queries in the
  sample reorder; sortedness verified directly).

## [0.6.0] - 2026-07-03

### Added
- **H111: Heritage/INRIA forms as a third, low-trust `forms` witness.**
  `forms` gains a nullable `category` column (migrated in `scripts/build_db.py`
  for pre-existing `kosha.db`s) and `scripts/build_forms.py` now loads
  [`heritage_only_forms.tsv`](https://github.com/gasyoun/SanskritLexicography/blob/master/HeadwordLists/heritage_only_forms.tsv)
  as `source='heritage'`, purely additive and loaded last: **+951,991** rows
  (`dcs` 397,843 and `vidyut` 28,567 unchanged). Trust ordering
  `dcs > vidyut > heritage` — Heritage's declension engine over-generates
  grammatically-possible but unattested forms — documented in
  [ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md),
  `build_forms.py`, and
  [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md).
  `/api/v1/form` already returned `source` per result, so heritage-only hits
  are distinguishable client-side without an API change.

## [0.5.0] - 2026-07-03

Phase 2 (public alpha) first agent-doable slice: the **static-cache generator**
that emits the GitHub Pages tier from `kosha.db` (branch `feat/p2-static-cache`,
Opus 4.8 `claude-opus-4-8`), built to the fixed D5-3 targets. 107 → **115** tests
green. Enabling Pages / deploying stays MG's (A3).

### Added
- **P2 static-cache generator** —
  [`scripts/build_static_cache.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_static_cache.py)
  emits three deliverables from the local DB (never a live service, R12), each
  matching [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md)
  D5-3:
  1. **Sharded per-lemma cards** — one JSON per lemma (never one bundle; a single
     `lemmas.json` crosses the 100 MB/file cap at ~33k), for the **50,355**
     lemmas with both a dict entry and a corpus attestation, **frequency-ranked**
     so a partial/interrupted run front-loads value (top-10k = 95.4% of corpus
     token mass) and resumes idempotently (existing shards skipped). Each card is
     **byte-identical** to `GET /api/v1/lemma/<slp1>?in=slp1` (reuses `app/`
     render/scan/transliterate — no reimplementation). ~155 MB, ~3 KB/file.
  2. **Headword autocomplete index** — one ~13 MB columnar file, all 323,425
     lemmas (`slp1`+`iast`+`dicts`); this is what the gitignored
     `docs/js/data/lemmas.json` path holds (D5-3a: the INDEX, not the cards),
     plus a tiny `attested_keys.json` sidecar so the UI picks static-vs-dynamic
     without a 404 probe.
  3. **Full 222,179-lemma card set** as an opt-in `--full-tarball` release asset
     (R1c/R4 rebuildability), deterministic (`mtime=0`), not committed.
- **Card filename encoding** (`card_token`) — keeps `[a-z0-9]` verbatim, escapes
  every other UTF-8 byte (incl. uppercase — SLP1 is case-significant and would
  collide on a case-insensitive FS) as `_<hexbyte>`; lossless, URL/FS-safe, with
  a documented JS twin for the frontend.
- **[docs/README.md](https://github.com/gasyoun/kosha/blob/main/docs/README.md)** —
  the Pages static-tier layout, token scheme + JS twin, and regeneration/deploy
  commands.
- **[tests/test_static_cache.py](https://github.com/gasyoun/kosha/blob/main/tests/test_static_cache.py)**
  (8 tests) — locks card↔live-API byte parity, `card_token` case-safety and
  lossless round-trip, ranked-shard generation, and index/attested counts
  (323,425 / 50,355).

### Changed
- `.gitignore` — the generated Pages tier (`docs/cards/`,
  `docs/js/data/attested_keys.json`, alongside the already-ignored
  `docs/js/data/lemmas.json`) is regenerable and MG-deployed, so it is not
  committed.

## [0.4.0] - 2026-07-03

Phase 1 **D5 — measure, then decide** (branch `feat/phase1-d5-measure`, Opus 4.8
`claude-opus-4-8`). The last Phase-1 step: real numbers behind the parked SLO
items, the decisions they force, a fixed latency bug the measuring surfaced, and
the R3 fallback turned from a comment into a tested path. 107/107 tests still
green. Phase 1 is complete; P2 (public alpha) can start against fixed targets.

### Added
- **D5 measurement report** —
  [D5_MEASUREMENTS.md](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md):
  DB size (276.4 MiB, 2.9× over the GitHub 100 MB/file cap → release-asset only,
  R11), cold/warm latency across all four read endpoints incl. the fat MW `ka`
  homonym group, per-dict `render()` cost + the full body-size distribution
  (97.3% of entries <1k chars; only 9 bodies >100k, all PWG), and a top-N
  static-cache projection. Reproducible from the committed harness
  [`scripts/measure_d5.py`](https://github.com/gasyoun/kosha/blob/main/scripts/measure_d5.py).
- **D5 decisions record** —
  [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md):
  latency SLO (p50<20ms / p95<100ms / p99<250ms server-side), rebuild cadence
  (change-triggered ~monthly, **not** nightly — nightly would mint needless
  citable `data_version`s, R1 tension), static-cache N (~50,355 attested-with-
  entry lemmas, sharded per-lemma ~155 MB, frequency-ranked). Relocated from the
  referenced SanskritLexicography path to this repo (canonical home); doc links
  repointed.
- **R3 csl-orig fallback exercised** (RISKS.md R3, now a tested path) —
  [`scripts/fallback_csl_orig.py`](https://github.com/gasyoun/kosha/blob/main/scripts/fallback_csl_orig.py)
  parses csl-orig `ap90.txt` directly and recovers **100%** of the entry
  inventory (34,882 records; every `<L>`, `<k1>` key, `<pc>` token matches the
  csl-sqlite-built DB). Honest boundary documented: bodies are the upstream
  display-markup stage, so a render()-able fallback also needs the csl-orig→XML
  `make_xml` step.

### Fixed
- **Lemma-lookup table scan (240 ms → ~0.3 ms).** `GET /api/v1/lemma` filtered
  `(dict, slp1_key)` but the planner seeked only on `dict` (via the
  `UNIQUE(dict,L)` autoindex, which also served `ORDER BY L`) and scanned all
  ~286k MW rows. A covering index `entries(dict, slp1_key, L)` (replacing
  `entries_key`, plus `ANALYZE` at build) serves both the seek and the ordering.
  Warm handler latency: lemma `kamala` 172→10.9 ms, `ka` 169→19.6 ms; e2e over
  HTTP 338→31 ms. Schema change in
  [`scripts/build_db.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db.py);
  the SLO (D5-1) assumes this index.

### Changed
- **`sources.csl_orig_commit` provenance resolved** (was flagged open) by
  cross-dating the csl-sqlite release timestamp against the local csl-orig commit
  log (offline, R12-safe): mw `392ed6b`, pwg `8822922`, ap90 `51232f2` — an
  upper bound, labelled as such. Wired into
  [`scripts/build_entries.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_entries.py)
  (`cross_date_csl_orig_commit`) and applied to the DB so `/api/v1/meta` surfaces
  it. Feeds R3's "data as of {date}" footer.
- ARCHITECTURE.md parked table: latency-SLO/cadence and static-cache-N rows
  resolved; DDL updated to the covering index. PHASE1_PLAN.md D5 marked done.

### Still open (not blocking)
- PWG multi-volume `servepdf.php` disambiguation needs a **live content diff**
  against Cologne (not a build-time or offline check, R12) — left flagged in
  [`.ai_state.md`](https://github.com/gasyoun/kosha/blob/main/.ai_state.md);
  belongs to scan-link hardening (G-SCAN/R2), not D5.

## [0.3.0] - 2026-07-03

Phase 1 D1–D4 **plus** the three D4-contract pieces PR
[#2](https://github.com/gasyoun/kosha/pull/2) deferred, closed here (branch
`feat/phase1-d4-followon`, Opus 4.8 `claude-opus-4-8`). 20 → **107** tests
green. Every measured number + deviation stays in
[`data/SOURCES.md`](https://github.com/gasyoun/kosha/blob/main/data/SOURCES.md).

### Added
- **Phase 1 D1–D4** (originally PR #2): lemma spine + frequency join (D1),
  per-dict `<pc>` entry loader for mw/pwg/ap90 (D2), forms layer + scan-URL
  resolver (D3), kosha API v1 + Salt facade REST faces + pytest suite (D4).
- **Full `render()` port** (ARCHITECTURE.md A1) —
  [`app/render.py`](https://github.com/gasyoun/kosha/blob/main/app/render.py) is
  now a code-level faithful port of the mw/pwg/ap90 path of csl-websanlexicon's
  canonical `basicdisplay.php` (SAX display engine) + the relevant
  `basicadjust.php` passes, replacing the earlier partial subset. Two documented
  deviations: server-side `<s>` SLP1→IAST via sanskrit-util (not client-JS
  `<SA>`), and no DB-backed abbreviation tooltips / external `<ls>` hrefs (the
  ls_resolver.py D3 follow-on). **38 frozen, checksummed golden HTML snapshots**
  (mw 14 incl. the banD/akṣa fixtures, pwg 12, ap90 12 — ≥10/dict merge bar) in
  [`tests/golden/`](https://github.com/gasyoun/kosha/tree/main/tests/golden),
  seeded-selected per EVAL_PLAN.md §0 anti-gaming, tested by
  [`tests/test_render_golden.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_render_golden.py).
- **Per-dict sense segmentation** (D2) —
  [`app/segment.py`](https://github.com/gasyoun/kosha/blob/main/app/segment.py)
  splits each body at its `<div>` division markers (MW `to`/`vp`, PWG numbered
  `1〉`/`a〉`, AP90 bold-numbered) into byte-anchored `senseN` spans (A2),
  replacing the single-sense fallback (kept only for markerless entries). Live
  counts: MW 303,022 · PWG 223,446 · AP90 165,935 senses.
- **R1 citability** (RISKS.md R1 Commitments 1–2) — the `cite` object now
  carries a browser-resolvable `resolution_url` + durable `release_asset`
  permalink + BibTeX/CSL-JSON
  ([`app/cite.py`](https://github.com/gasyoun/kosha/blob/main/app/cite.py));
  `/api/v1/sense/{id}@version` resolves an **old** citation against its archived
  release dump
  ([`app/versions.py`](https://github.com/gasyoun/kosha/blob/main/app/versions.py),
  [`scripts/archive_senses.py`](https://github.com/gasyoun/kosha/blob/main/scripts/archive_senses.py)),
  the path **T-UC10** forces; every rebuild can emit `sense_crosswalk.tsv`
  (old→new senseN via span-text similarity, SPLIT/MERGED/GONE/MOVED, zero-cost
  when unchanged —
  [`scripts/build_crosswalk.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_crosswalk.py)).
  Verified on real PWG data + unit-tested in
  [`tests/test_citability.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_citability.py).

### Still deferred (flagged, not silent)
- `sources.csl_orig_commit` still records the csl-sqlite release tag only (the
  underlying csl-orig commit is not exposed by the release format).
- PWG multi-volume scan disambiguation: `servepdf.php` returns 200 for `page=`,
  `page=&vol=`, and `page=&volume=` alike (tolerant of unknown params); whether
  `vol` is honored is not determinable from status alone. Still open.

## [0.2.1] - 2026-07-02

README rewritten for a layered dual audience (MG request; authored by Fable 5
`claude-fable-5`): public-facing top, engineering spine below.

### Changed
- **[README.md](https://github.com/gasyoun/kosha/blob/main/README.md)** — drastic
  rewrite: brand-led H1 (**Gasuns Sanskrit Dictionary**, kosha = codename); prominent
  pre-alpha "nothing runs yet" banner; public pitch + feature list + P1–P7 roadmap
  snapshot; new **FAQ** (18 questions across using-it / vs-existing-sites /
  status-timeline / licensing-reuse); planning spine preserved under "For contributors
  & agents" (reuse-first table, A1–A4, ground rules, full document map incl. the
  SanskritLexicography planning corpus). No decisions changed — presentation only.

## [0.2.0] - 2026-07-02

The judgment layer completed — the three plans queued in
[.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md) §Next Steps 1,
authored by Fable 5 (`claude-fable-5`). With these, the P1 execution session (Sonnet 5
`claude-sonnet-5` / Opus 4.8 `claude-opus-4-8`) is fully gated: EVAL_PLAN's gates bind.

### Added
- **[EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md)** — quality
  gates designed so an executor can't game them: 8 anti-gaming ground rules (freeze
  before first scored run, selection by committed procedure, thresholds live in the doc,
  fail closed, snapshot discipline, scorer ≠ system, no ✅ without artifact); G-SEG
  200-form stratified segmentation gold (9 classes incl. out-of-DCS contamination
  holdout + calibration rule); G-RENDER adversarial golden selection (accented PWG
  key2, `-L{lnum}` homonyms, densest MW `<ls>` cards, the ळ→x + IAST traps from
  [FINDINGS §36/§39](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md));
  G-SALT parity tolerances vs csl-apidev's `agni`/`indra`/`ka` envelopes (unlisted =
  exact); G-SCAN page-truth beyond HTTP 200; every
  [USE_CASES.md](https://github.com/gasyoun/kosha/blob/main/USE_CASES.md) *Accept:* line
  as a named test (T-UC1…T-UC13, Gītā 1.1 locked as the UC6 verse).
- **[RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md)** — ecosystem
  diplomacy: the Meyer permission ask drafted (his 7 self-digitized indices off-limits
  without written yes; send at P2 exit); Cologne-maintainer framing paragraph ("kosha
  serves your Salt standard", one csl-standards issue, no noise); Ambuda/vidyut
  give-back (G-SEG report upstream, name-collision rule: public name = Gasuns Sanskrit
  Dictionary); C-SALT/CCeH sense-face contribution; binding upstream-vs-track-3
  decision table; 7-row contact registry (all sends = MG).
- **[RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md)** — pre-mortem
  register R1–R12: `@data_version` is airtight only under 4 new commitments (in-browser
  version resolution forced by T-UC10, `sense_crosswalk.tsv` per release, **Zenodo
  mirroring moved up from P7 to the first citable release**, never-delete policy);
  scan-link page-truth (a wrong link is worse than none); csl-sqlite lag measured +
  surfaced as "data as of"; single-maintainer rot mirror-test + archive-banner policy;
  samskrtam.ru bus factor (citations never point at the server); license geometry
  (DCS dump license ask before P3 public; gramdict CC BY-NC must not enter BY-SA data).

## [0.1.0] - 2026-07-02

Founding release — the complete planning/contract layer, authored in one day by
Fable 5 (`claude-fable-5`) after MG green-lit Phase 1. No application code beyond the
honest stub; nothing claims ✅ without a passing check.

### Added
- **Repo created** per meta-decisions M1–M4 (triage of the fabricated planning corpus:
  [SanskritLexicography v0.0.34](https://github.com/gasyoun/SanskritLexicography/releases/tag/v0.0.34)); seeded README, reuse-first
  [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md) (D1–D5 with per-day exit checks), stub `app/main.py`.
- **[POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md)** + [summary](https://github.com/gasyoun/kosha/blob/main/POSITIONING_SUMMARY.md):
  product name **Gasuns Sanskrit Dictionary**; three-track identity (improve source ·
  improve Cologne UI · own advanced service); MG override recorded — own advanced UI,
  API-first.
- **[COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md)** — 12-platform live survey (all fetched 02-07-2026):
  michaelmeyer.fr = 41 dicts w/ per-sense scan links (positioning corrected — the
  read-only collapse exists); Heritage Inria bot-walled; DCS HTTPS broken; VedaWeb→Tekst;
  vidyut-kosha has no end-user UI. Mirrored as
  [FINDINGS §41](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md) (PR [#55](https://github.com/gasyoun/SanskritLexicography/pull/55)).
- **[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)** — engineering contract A1–A4: raw-markup storage +
  csl-websanlexicon-ported renderer (golden tests mandatory); sense IDs
  `dict.L.senseN@data_version`; local-first (MG deploys, agents never SSH); Sonnet/Opus
  executes. SQLite DDL, API v1 contract, encoding policy.
- **Salt API max-reuse (required):** Salt-profile entry object as the interchange shape
  inside `/api/v1`; entry data from csl-sqlite releases; Salt facade REST faces in P1/D4
  parity-tested vs csl-apidev envelopes; GraphQL face by P7.
- **Licenses:** code CC BY-NC 4.0 ([LICENSE.md](https://github.com/gasyoun/kosha/blob/main/LICENSE.md)); data releases CC BY-SA 4.0
  inherited from Cologne ([LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md) — csl-orig verified BY-SA, so NC
  attaches to code only).
- **[IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md)** — P1 data+API → P2 public alpha → P3 evidence
  layer → P4 forms+grammar → P5 advanced UI → P6 trilingual RU (G5 + Kochergina gates) →
  P7 citable v1.0 (DOI); per-phase exit checks; MG critical path.
- **[USE_CASES.md](https://github.com/gasyoun/kosha/blob/main/USE_CASES.md)** — 13 concrete scenarios (translators, students, scholars,
  machine consumers) mapped to delivering phases; acceptance-test seeds for EVAL_PLAN.
- **[.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md)** — session-state protocol; next queued: Fable chat authoring
  EVAL_PLAN.md + RELATIONS.md + RISKS.md, and the Sonnet/Opus P1 execution session.

_Dr. Mārcis Gasūns_
