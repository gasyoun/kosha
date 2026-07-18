# Implementation — kosha Concordance Q3 (Pāṇinian sūtra ↔ corpus)

_Created: 18-07-2026 · Last updated: 18-07-2026_

Step-by-step build for the waves in
[ROADMAP_KOSHA_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026H2.md),
against the design in
[ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md).
Exit checks live in
[VERIFICATION_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_CONCORDANCE_Q3.md).

---

## 0. Preconditions — verified 18-07-2026

Every wave-1 input is present on this machine. An executing agent should re-verify
before starting, because these are gitignored and machine-local.

| Input | Path | Size | Check |
|---|---|---|---|
| `vidyut` 0.4.0 | site-packages | — | `python -c "import vidyut; print(vidyut.__version__)"` |
| `kosha.db` | `data/db/kosha.db` (main tree) | **1.67 GB** | present |
| DCS full corpus | [`VisualDCS/src/DCS-data-2026/dcs_full.sqlite`](https://github.com/gasyoun/VisualDCS) | 920 MB | present |
| DCS archive | `VisualDCS/src/DCS-data-2026/archive.sqlite` | 168 MB | present |
| Frequency layer | [`data/frequency/lemma_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv) | 83,277 rows | committed |
| **`sanskrit-util` sibling checkout** | `GitHub/sanskrit-util/py/` | — | **hard import-time dependency** — `python -c "import sys; sys.path.insert(0,'../sanskrit-util/py'); from sanskrit_util import form_key; print(form_key('rāma'))"` |

> **Why `sanskrit-util` is a precondition and not a package.** `form_key()` is
> defined **nowhere in kosha** — [`scripts/concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py)
> does `sys.path.insert(0, <repo-parent>/sanskrit-util/py)` and then
> `from sanskrit_util import form_key, norm, normalize_sanskrit, to_slp1`. The path
> is resolved as `Path(__file__).resolve().parent.parent.parent / "sanskrit-util" / "py"`
> — three levels up from the script, i.e. the repo's **parent directory** — so the
> sibling must sit beside the checkout that runs the script. In a worktree at
> `GitHub/kosha-<slug>/` that resolves to `GitHub/sanskrit-util/` — the same place
> the main tree finds it, so a worktree needs no copy. Every A4 script that joins on
> `form_key()` fails at **import time**, not at run time, if this is missing.

> **Worktree note.** `data/db/` is gitignored, so a fresh worktree has **no**
> databases. Point `DATABASE_PATH` at the main tree's `kosha.db` **read-only**, or
> rebuild locally. Do not commit from the shared main tree — the `.githooks`
> pre-commit guard blocks it, and correctly so.

**Build-stamp discipline (R-Q4).** Before consuming an artefact, record its
`mtime` and row count in the wave's build report. If a downstream wave's recorded
input stamp does not match the artefact it finds, **halt** — a stale input
produces silently wrong output, not an error.

> **Stale-clone warning — read before W1c or W1d.** The shared main tree
> `GitHub/kosha` showed `M data/manifest/datasets.json` at authoring time. That is
> **not** an in-flight session: the diff is exactly the `handoff-lifecycle-gold`
> row, which is already **committed on `origin/main`** as
> [`1bd3c566`](https://github.com/gasyoun/kosha/commit/1bd3c5661) *"docs(manifest):
> register handoff-lifecycle-gold dataset (H1251) (#127)"* (PR #127, merged). The
> main tree is simply **3 commits behind `origin/main`** and carrying a stale
> working copy of already-merged content.
>
> Consequences: (a) the **77-row** census throughout this plan set is measured
> against `origin/main` and **already includes** `handoff-lifecycle-gold` — there is
> no 78th row and no pending count change; (b) W1c/W1d still work in a **fresh
> worktree off `origin/main`** and still `git fetch origin` first — standard
> discipline, and the only way to avoid inheriting that 3-commit lag; (c) the row
> already uses `in_release: "unreleased"` correctly, so the D8 migration covers it
> without special handling; (d) do **not** "rescue" the main tree's diff as though
> it were unsaved work — `git checkout -- data/manifest/datasets.json` after
> fetching is the correct disposal, and a session that instead re-commits it will
> author a duplicate row.

---

## Wave 1

### W1a — Derivation-metadata rights record  ·  Opus

Gates every A4 publication (D2). Small, but nothing ships without it.

1. Locate the installed vidyut distribution and read **every** licence file:
   the top-level `LICENSE`, any per-directory licence, and the package metadata.
2. Determine separately: (a) the **code** licence, (b) the licence and provenance
   of **bundled derivation data** — dhātupāṭha, rule tables, any sūtra
   enumeration shipped with the package. These are frequently not the same, and
   assuming they are is the failure mode this step exists to prevent.
3. Cross-check against the upstream [ambuda-org/vidyut](https://github.com/ambuda-org/vidyut)
   repository and against the `vidyut` row in
   [external_tools.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json)
   (currently records `MIT`). If the manifest row is incomplete, correct it.
4. Write `data/manifest/rights/vidyut_prakriya_derivation_2026-07.md` in the shape
   of the [Franceschini record](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/franceschini_hos9_permission_2026-07-13.md):
   what is licensed, by whom, under what terms, what it permits, and the
   composition ruling for A4 output.
5. **Resolve DCS's licence against Hellwig's own published terms** (the DCS
   repository and site — *not* a kosha secondary source, since kosha contradicts
   itself: [external_tools.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json)
   says `CC BY-SA 4.0` while [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md)
   line 151 and the `reading-pack-*` rows say `CC BY 4.0`). Correct whichever
   kosha file is wrong **in the same pass** — leaving the contradiction in place
   is a failure of this step, not a deferral.
6. State the composition explicitly, marking each input's licence as *cited* or
   *resolved in step 5*: CDSL CC BY-SA 4.0 + public-domain sūtra text + vidyut
   (per step 2) + DCS (per step 5) ⇒ **output CC BY-SA 4.0, vidyut attributed**.
   The output licence does not depend on the DCS answer — CDSL's ShareAlike binds
   either way — so record BY-SA as inherited from CDSL, and let step 5 fix the
   provenance line rather than the licence. Note the repo's two-tier rule and that
   NC may not be added atop Cologne's ShareAlike.

**Stop condition.** If the bundled data carries terms incompatible with a BY-SA
release, **do not choose** — write findings, mark the item `@DECIDE`, surface it,
and let A4 build but not publish.

**Output:** one rights file · possibly one corrected manifest row.

---

### W1b — A3 attested-form join  ·  Opus  ·  the long pole

Builds `morphology-attestation-audit`, the input A4 cannot start without (D12).

1. New script `scripts/build_morphology_attestation_audit.py`. Follow the repo's
   Windows encoding convention (`sys.stdout/stderr.reconfigure(encoding='utf-8')`).
2. Read generated forms from `kosha.db` `forms`, **excluding heritage**
   (`include_heritage=False` — hypergenerated and untrusted, per H696 default-off
   and the D5-3/H111 trust ordering `dcs > vidyut > heritage`).
3. Read attested forms + loci from `dcs_full.sqlite`.
4. Join on `form_key()` — the length-preserving normaliser. **Never** NFD +
   strip-combining-marks: it destroys vowel length and retroflexion, which is
   precisely what killed the relaxed tier (0/3 correct, D6).
5. Emit three buckets: `AG` (attested ∧ generated), `G¬A` (over-generation),
   `A¬G` (engine/grammar gap).
6. Carry the **R-C4 caveat**: any verb row whose bucket depends on DCS
   `Tense=Past` gets `tense_caveat=1`. Every published count reports the caveated
   subtotal beside the total.
7. Triage `A¬G`: classify each row as OCR/segmentation artefact vs genuine engine
   gap. Route genuine gaps to the csl-inflect give-back (H185).
8. **Measure `kosha.db` size before and after** and record it — R-Q1 needs the
   number, and if A4 metadata would push the file past ~1.9 GB, derivation tables
   ship as a separate release asset. Decide from the measurement.
9. Write `data/concordance/MORPHOLOGY_ATTESTATION_BUILD_REPORT.md`: per-bucket
   counts, caveated subtotals, triage distribution, runtime, input build stamps.
10. Add the `morphology-attestation-audit` manifest row **in the same pass**
    (agent contract), with the D8 vocabulary.

**Scale note.** 6.9M × 5.7M is a hash join on a normalised key, not a cross
product — hold the smaller side in memory keyed by `form_key()` and stream the
larger. Report peak memory in the build report.

**Output:** script · 3 bucket TSVs · build report · manifest row.

---

### W1c — Manifest schema hardening + `data-v0.2.0`  ·  Sonnet

1. Migrate `in_release` to the D8 closed vocabulary across all 77 rows:
   `"<release-tag>"` · `"unreleased"` · `"not-applicable"`. Each current `null`
   becomes `not-applicable` (kosha does not host it) or `unreleased` (kosha hosts
   it, not yet released) — decide **per row** from `tier` and `source_repo`, not
   by a blanket rule.
2. Make `release_asset` required where `tier == "public"` and `in_release` names
   a tag; fill the gaps.
3. Add schema validation to
   [tests/test_directory.py](https://github.com/gasyoun/kosha/blob/main/tests/test_directory.py):
   every row has `in_release` from the vocabulary; every public released row has
   `release_asset`. **Fail CI on violation** — an optional field is how 32 rows
   drifted unnoticed.
4. Cut the catch-up **`data-v0.2.0`** release clearing the 32-row `unreleased`
   backlog, via `/data-release` (safety-check gate → licence → provenance → DOI).
   Run [`/publish-safety-check`](https://github.com/gasyoun/claude-config/blob/main/commands/publish-safety-check.md)
   first — 32 rows is a large publish surface and a restricted asset slipping in
   would be a rights incident.
5. Update `interim_release` to the new tag; flip the released rows' `in_release`.
6. Record the **rolling cadence rule (D7)** in
   [DATA_HUB_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md):
   every wave adding a public dataset cuts a data release in the same pass.
7. `CHANGELOG.md` entry + `/cut-release`.

**Do not** flip `heritage-forms-crosswalk-extras` to public — LGPLLR is unresolved
(D10).

**Output:** migrated manifest · schema test · `data-v0.2.0` · cadence rule.

---

### W1d — Computed README dataset count  ·  Haiku

README claims **57 datasets (43 public · 11 restricted · 3 intermediate)**; actual
is **77 (63 · 11 · 3)**. Restricted and intermediate are correct — the whole drift
is the public count. A commit titled "fix stale dataset count" landed 14-07 and
was stale again in four days, which is the argument for computing it.

1. [`scripts/build_directory.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_directory.py)
   already computes `len(public)`, `len(restricted)`, `len(tools)` from the
   manifest. Extend it with a `--update-readme` mode that rewrites the counts
   sentence in [README.md](https://github.com/gasyoun/kosha/blob/main/README.md)
   between stable marker comments.
2. Also recompute the **"8 external stacks"** claim from `external_tools.json`
   in the same sentence-rewrite — it is the same class of hand-copied fact.
3. Add to [tests/test_directory.py](https://github.com/gasyoun/kosha/blob/main/tests/test_directory.py):
   parse the README counts and assert they equal the manifest counts. **This test
   is the actual deliverable** — the rewrite is convenience, the invariant is what
   stops the drift.
4. Run it; commit the corrected README.

**Output:** `--update-readme` mode · README invariant test · corrected README.

---

### W1e — Link-rot mover fix + catch-up  ·  Sonnet

Fix the mover, not the symptoms (D11). Seven handoffs moved to `archive/` in one
sweep, breaking **14 link occurrences** (7 unique targets × 2 each) in
[PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md).
Two org-wide link audits ran in the window and missed all 14, because they run on
the wrong side of the move.

1. **Root cause first.** `/handoff-archive` moves files and updates
   cross-references, but the breakage shows the sweep does not catch references in
   *other repos'* markdown. Establish whether the gap is scope (only the handoff
   repo is scanned) or timing (the audit runs before the move). Fix the actual
   cause — do not add a post-hoc scanner on top of a mover that should not break
   links.
2. Extend the mover: for every moved handoff, rewrite referring links
   **org-wide**, or emit a machine-readable move manifest the link audit consumes.
3. **One-time catch-up:** repair the 14 occurrences — `handoffs/H94[5-9]`,
   `handoffs/H95[0-1]` → `handoffs/archive/…`. All 7 targets confirmed present
   under `archive/`.
4. Flip the stale registry row: **H900** still reads *"DELIVERED, PR open awaiting
   human merge 14-07-2026"* in
   [Uprava/handoffs/README.md](https://github.com/gasyoun/Uprava/blob/main/handoffs/README.md);
   [kosha PR #93](https://github.com/gasyoun/kosha/pull/93) merged 14-07. Use
   `/handoff-close`.
5. Re-run the link audit and show zero dead handoff links in kosha.

> Uprava edits go through a worktree off `origin/main`, never the shared main
> tree, and the registry is edited with `Uprava/tools/registry_edit.py` — never a
> blind rewrite, which races concurrent sessions.

**Output:** mover fix · 14 links repaired · H900 row corrected · clean audit.

---

### W1f — Relaxed-tier dead-end record  ·  Haiku

Close D6 as a documented dead end rather than a silent deletion.

1. Append to [Uprava/DEAD_ENDS.md](https://github.com/gasyoun/Uprava/blob/main/DEAD_ENDS.md):
   the relaxed concordance matching tier, **2,171 candidate links**, rejected
   because the golden sample scored **0/3 correct** while the strict tier scored
   **11/11**. Cause: `norm()` folds vowel length and sibilant distinctions —
   `ram`/`rāṃ` (a/ā), `vikarṣaṇa`/`vikarśana` (ṣ/ś), `aṃśaka`/`aṃsaka` (ś/s).
   Evidence: [GOLDEN_SAMPLE.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/GOLDEN_SAMPLE.md).
2. State the transferable lesson: **length- and sibilant-folding normalisation is
   not a viable relaxed-match tier for Sanskrit lexical joins.** That is the
   reusable finding — it should stop the next repo from rebuilding this.
3. Cancel the 2,171-item review sheet in
   [Uprava/REVIEW_SHEETS_INDEX.md](https://github.com/gasyoun/Uprava/blob/main/REVIEW_SHEETS_INDEX.md);
   mark cancelled with the reason, do not delete the row.
4. Update [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md):
   Q2 exit ships **strict-tier-only**; relaxed tier dropped, R-C1 narrowed.
5. Keep the quarantined TSVs in place as evidence — they are a record, not
   shipped data. Confirm no manifest row markets them as usable.

**Output:** `DEAD_ENDS` entry · sheet cancelled · roadmap updated.

---

## Wave 2

### W2a — Derivation harness

1. `scripts/build_panini_derivations.py`, modelled on
   [`compare_vidyut_cologne.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_cologne.py)
   (proven local-library driving of `vidyut.prakriya`, R12-clean).
2. Input: W1b's **AG bucket** — verify its build stamp.
3. Per form: map to a derivation request; run; capture the **ordered sūtra chain**.
   The nominal mapping is proven in E1; the **verbal** mapping (dhātu + gaṇa +
   lakāra) is new work and the expected source of most `engine-error`.
4. Accept a derivation only on **`form_key()` equality** with the attested form.
   Landing on a different form is `ambiguous`, not `ok`. **Record the tier
   honestly:** `form_key()` equality is `concordance_core`'s **`floor`** tier
   (confidence **0.85**), *not* `exact` — `exact` means byte-identical SLP1
   (0.95) and applies only to the subset where the SLP1 keys also match verbatim.
   Emit both where they occur; never a constant. `confidence` is always
   `TIER_CONFIDENCE[tier]`, never a literal, and never `1.0` (no tier scores 1.0).
5. Record `derivation_status` per form: `ok` · `no-derivation` · `ambiguous` ·
   `engine-error`. Never drop a failure.
6. Emit `data/concordance/derivation_chains.tsv` (`chain_id` → ordered sūtra list)
   and a per-form status table.
7. **Start with a bounded pilot** (10k frequency-ranked forms, the E1 sample
   shape) to characterise runtime, failure distribution, and ambiguity rate
   before the full run. Report the pilot before scaling.

### W2b — Invert to the concordance

1. `scripts/build_panini_concordance.py`.
2. Invert to `sūtra → {attested forms}`, emitting one row per
   `(sūtra, form, locus)` in the §2 schema. Import `RECORD_FIELDS` from
   `concordance_core` — **do not retype the field names**: the canonical set is
   `anchor_type · anchor_id · anchor_key_slp1 · target_locus · source_dataset ·
   match_method · confidence · evidence_count`. `corpus_locus`/`corpus_text_id`
   are the **pre-H539 names** and must not appear. Then append the A4 columns
   `form_key_slp1`, `dcs_text`, `chain_position`, `chain_length`, `chain_id`,
   `derivation_status`, `tense_caveat`, exactly as
   `build_dict_corpus_concordance.py` appends its four.
   `target_locus` is `citable_locus(sent_id)` ⇒ `dcs:<sent_id>`; `anchor_id` is
   `sutra:<a.p.n>`; `anchor_key_slp1` is empty for a sūtra anchor.
3. Mint citations via [`app/cite.py`](https://github.com/gasyoun/kosha/blob/main/app/cite.py)
   — `PUBLIC_BASE`, never the deployment host (R1/R5).
4. Write `data/concordance/PANINI_BUILD_REPORT.md`: row counts, distinct sūtras
   touched, chain-length distribution, status distribution, ambiguity rate,
   caveated subtotals, input stamps.

---

## Wave 3

### W3a — Sūtra-coverage map

1. `scripts/build_sutra_coverage_map.py`.
2. Per sūtra: `exemplar_forms`, `exemplar_loci`, `texts`, `mean_chain_position`,
   `status`.
3. Classify dark sūtras into **`dark-unattested`** (implemented, fires, no
   attested landing), **`dark-out-of-scope`** (vidyut does not implement it), and
   **`dark-engine-gap`** (implemented, all derivations errored). Collapsing these
   is forbidden — see architecture §5.
4. **State the enumeration and its exact count.** "~4,000" is approximate;
   recensions differ on sūtra division. Every percentage cites the stated
   denominator.
5. Emit the map as TSV + a summary table in the build report.

### W3b — Manifest row + public release

1. **Verify the W1a rights record exists.** If absent, halt — this is the D2 gate.
2. Add the `paninian-corpus-concordance` manifest row with the D8 vocabulary and
   a `data_statement` under
   [docs/data-statements/](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/).
3. `/publish-safety-check`, then `/data-release` (licence → provenance → DOI).
4. Cut the release **in the same pass** (rolling cadence, D7).
5. `CHANGELOG.md` + `/cut-release`.
6. Register the dataset in the cross-repo hubs per `/artifact-propagate`.

---

## Wave 4

### W4a — `/concordance/panini/`

1. **Fork** the Q1 viewer — see architecture §9 for what that costs. It is not a
   drop-in: `concordance/dict/index.html` reads `data/kwic_<letter>.js`
   (`window.CONC_DATA`) shards, **not** the concordance TSV, and contains zero
   references to any `RECORD_FIELDS` name. Concretely: (a) add a shard emitter to
   `build_panini_concordance.py`, modelled on `build_dict_corpus_concordance.py`'s
   KWIC pass but sharded by **adhyāya** (1–8) since sūtra IDs are numeric;
   (b) extend the shard payload with the resolved chain and the coverage `status`;
   (c) copy the viewer to `concordance/panini/index.html` and retarget its
   anchor-list labels, shard-key function, and trust block.
2. Add **chain view** (full derivation from `chain_id`) and **coverage view**
   (dark classes visibly distinguished, never filtered out).
3. House `/viz-page` pattern: trust block (source artefact, n, date) + data-table
   fallback with CSV download.
4. Deploy to the interim host, [gasyoun.github.io/kosha](https://gasyoun.github.io/kosha/) (D3).

### W4b — Static head + budget re-measure

1. Apply the **D4 standing rule**: static head at the **measured** N, SSR tail via
   `/w/{slp1}`. Re-measure N from current frequency data at build time — do not
   hardcode 11,148; today's measurement is the expected answer, not the input.
2. Build logs N, coverage achieved, byte total, and share of the Pages cap.
3. Re-measure the **total** Pages footprint with A4 pages included. Expected
   ~507.6 MB + A4; budget A4 at ≤ 100 MB. If the total exceeds **75%** of the cap,
   trim the head and report — do not silently ship at the ceiling.
4. **Do not overwrite `.ai_state.md`'s "~60% headroom".** That figure is
   **correct**: it describes the **deployed** tier — cards at 402 MB against the
   1,024 MB soft cap = 39%, so ~61% free — and the full 50,355-page word set has
   never shipped (README gates P5's public URL on the P2 deploy). The **~14%** is a
   *projection* for the hypothetical card + full-word-page tier (402 + 477 =
   879 MB = 86%), which is the scenario D4's head/tail split exists to avoid.
   Replacing a correct deployed-state number with a hypothetical one would be a
   regression. What W4b *should* do: **append** the newly measured post-A4 deployed
   footprint beside the existing figure, each labelled with its tier and date, and
   correct only the genuinely wrong claim — that the total *"exceeds the ~1 GB
   cap"*, which it does not (879 MB is 86% of it).
5. Record the D4 standing rule in
   [ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)
   so it is found without this plan.

---

## Migration M1 — on deploy (~25-07-2026)

1. In [datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json),
   **add** a top-level `canonical_base` carrying the value currently in
   `canonical_base_future` (`https://samskrtam.ru/kosha/data/`), then retire the
   `_future` key. Note the actual state: `canonical_base` **does not exist yet** —
   only `canonical_base_future` does — so M1 *creates* the field, it does not
   rename an existing pair.
   **Leave `interim_release` alone.** It is
   `https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0` — a **GitHub release
   tag**, not a Pages URL. The Pages host (`gasyoun.github.io`) appears in **no**
   manifest field at all; it is the interim host for the *web pages*, which is a
   separate surface from where *datasets* are fetched. Nothing about the Pages
   deploy migrates through this field. After W1c, `interim_release` names
   `data-v0.2.0`; M1 does not touch it.
2. Re-run every exit check in
   [VERIFICATION_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_CONCORDANCE_Q3.md)
   against `https://samskrtam.ru/kosha/`.
3. **Assert citation stability:** a citation minted against Pages must resolve
   unchanged after migration. If it does not, `PUBLIC_BASE` leaked the deployment
   host and R1/R5 is violated — fix that before anything else.
4. Update README and the directory page; `CHANGELOG.md` entry.

---

_Dr. Mārcis Gasūns_
