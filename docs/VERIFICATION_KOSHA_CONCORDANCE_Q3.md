# Verification — kosha Concordance Q3 (Pāṇinian sūtra ↔ corpus)

_Created: 18-07-2026 · Last updated: 18-07-2026_

Exit checks for every wave in
[IMPLEMENTATION_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_CONCORDANCE_Q3.md).
Each check states **how it is falsified**, not merely what "done" looks like — a
check that cannot fail is not a check.

---

## 0. Standing rules for every check

| Rule | Why |
|---|---|
| Every quantitative claim states its **denominator** and **measurement date** | The D5-3 "95.4%" / "94.32%" divergence was a denominator difference, not an error — undocumented denominators produce phantom contradictions |
| Every figure is reproducible from a **committed script** | A number nobody can re-derive is not shipped |
| A figure contradicting an earlier committed figure shows **both**, with the discrepancy explained | Worked examples: the Pages-budget and coverage corrections in [architecture §6](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md) |
| Failure classes are **counted and published**, never filtered | R-C3: the dark set is the deliverable's honesty surface |
| A wave states its input artefact **and build stamp**; mismatch **halts** the wave | R-Q4: a stale input produces silently wrong output, not an error |

**Anti-gaming.** Per [EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md),
a check may not be passed by narrowing what it measures. If coverage is achieved
by excluding hard cases, the exclusion is the finding and must be reported as
prominently as the coverage number.

---

## Wave 1

### W1a — Rights record

| # | Check | Falsified by |
|---|---|---|
| 1a-1 | `data/manifest/rights/vidyut_prakriya_derivation_2026-07.md` exists | file absent |
| 1a-2 | It states the **code** licence and the **bundled-data** licence **separately**, each with the file it was read from | either treated as covering both, or no source cited |
| 1a-3 | It states the composition ruling for A4 output with reasoning | ruling asserted without the input-licence chain |
| 1a-4 | The `vidyut` row in [external_tools.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json) matches what was read | manifest and record disagree |
| 1a-5 | If bundled-data terms are incompatible: an `@DECIDE` is surfaced and **no A4 dataset is published** | a release cut with the question open |
| 1a-6 | DCS's licence is resolved from **DCS's own published terms**, cited, and the contradicting kosha file corrected in the same pass | the record asserts a DCS licence citing only a kosha source, or `external_tools.json` and `CONCORDANCE_ROADMAP.md`:151 still disagree afterwards |

> **Hard gate.** 1a-1 is checked at the top of W3b. A4 does not publish without it.

### W1b — A3 attested-form join

| # | Check | Falsified by |
|---|---|---|
| 1b-1 | Three buckets emitted; counts sum to the input cardinality | totals do not reconcile |
| 1b-2 | Join used `form_key()`; **no** NFD+strip path anywhere | grep finds a normalisation that folds length or retroflexion |
| 1b-3 | Heritage forms **excluded** | a heritage-sourced form appears in AG |
| 1b-4 | Every published verb count carries its `tense_caveat=1` subtotal | an aggregate published without the caveated subtotal |
| 1b-5 | `A¬G` triaged into OCR/segmentation vs genuine gap, with counts | residue reported as one undifferentiated number |
| 1b-6 | `kosha.db` size measured before/after and recorded (R-Q1) | no measurement in the build report |
| 1b-7 | Manifest row added **in the same pass** | dataset exists with no row |
| 1b-8 | **Spot-check:** 20 random AG rows human-verifiable as genuine attestations | any row is a normalisation artefact |

**1b-8 is the check that matters.** The relaxed tier passed every mechanical check
and still scored 0/3 on human inspection. Mechanical reconciliation does not
establish correctness of a lexical join.

### W1c — Manifest schema + `data-v0.2.0`

| # | Check | Falsified by |
|---|---|---|
| 1c-1 | All 77 rows carry `in_release` from the closed vocabulary | any row outside it, or `null` surviving |
| 1c-2 | Every `public` + released row has `release_asset` | a released public row without one |
| 1c-3 | Schema test in [tests/test_directory.py](https://github.com/gasyoun/kosha/blob/main/tests/test_directory.py) **fails** on a deliberately broken row | test passes on bad input |
| 1c-4 | `data-v0.2.0` published; the 32 `unreleased` rows now name it | backlog count still non-zero without stated reason |
| 1c-5 | `/publish-safety-check` run and recorded **before** the release | no record |
| 1c-6 | **No restricted asset** appears in the release | any restricted-tier asset downloadable |
| 1c-7 | `heritage-forms-crosswalk-extras` still `restricted` | tier flipped while LGPLLR is open |
| 1c-8 | Rolling-cadence rule (D7) recorded in [DATA_HUB_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md) | absent |

**1c-6 is a rights check, not a hygiene check.** 32 rows is a large publish
surface; one restricted asset slipping in is an incident.

### W1d — Computed README count

| # | Check | Falsified by |
|---|---|---|
| 1d-1 | README states 77 / 63 / 11 / 3 | any stale figure |
| 1d-2 | The external-stacks count is computed, not hand-copied | hardcoded integer remains |
| 1d-3 | Invariant test **fails** when the manifest changes and the README does not | test passes on drift — this is the deliverable |
| 1d-4 | `--update-readme` is idempotent | second run produces a diff |

### W1e — Link-rot fix

| # | Check | Falsified by |
|---|---|---|
| 1e-1 | All 14 occurrences resolve | any 404 |
| 1e-2 | **Root cause** identified as scope or timing, and stated | a scanner added without diagnosing the mover |
| 1e-3 | A simulated archive move of a referenced handoff leaves **zero** dead links | simulation reproduces the original breakage |
| 1e-4 | H900's registry row reflects [PR #93](https://github.com/gasyoun/kosha/pull/93) merged | row still says "awaiting human merge" |
| 1e-5 | Org-wide link audit reports zero dead handoff links in kosha | any remain |

**1e-3 is the real check.** Repairing 14 links without fixing the mover recreates
the defect on the next sweep — which is exactly the history here.

### W1f — Relaxed-tier dead end

| # | Check | Falsified by |
|---|---|---|
| 1f-1 | `DEAD_ENDS` entry names the tier, **2,171** links, **0/3** vs **11/11**, and the three folding classes | entry lacks the evidence |
| 1f-2 | The transferable lesson is stated generally, not only as a kosha fact | recorded as a local quirk |
| 1f-3 | Review sheet marked **cancelled with reason**, row retained | row deleted |
| 1f-4 | [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md) says Q2 exit is strict-tier-only | still implies relaxed review is pending |
| 1f-5 | No manifest row markets the quarantined TSVs as usable | any row presents them as a dataset |

---

## Wave 2

### W2a — Derivation harness

| # | Check | Falsified by |
|---|---|---|
| 2a-1 | Pilot (10k forms) reported **before** the full run | full run with no pilot |
| 2a-2 | Every AG form has a `derivation_status` | any form silently absent |
| 2a-3 | `ok` requires an **exact `form_key()`** match to the attested form | a near-match counted as `ok` |
| 2a-4 | Status distribution published with counts and percentages | only successes reported |
| 2a-5 | No live third-party call at build time (R12) | any network call in the build path |
| 2a-6 | Chain sidecar round-trips: `chain_id` → the exact ordered chain | any chain unrecoverable |
| 2a-7 | **Sampled human verification:** 30 chains checked correct for their form | any chain wrong for its form |

**2a-7 is the correctness check the exit criteria require.** A concordance of
confidently wrong derivations is worse than none.

### W2b — Inversion

| # | Check | Falsified by |
|---|---|---|
| 2b-1 | Row count equals `Σ chain_length` over `ok`/`ambiguous` forms | mismatch |
| 2b-2 | Header equals `concordance_core.RECORD_FIELDS` + the A4 columns, **imported not retyped**; `target_locus` matches `^dcs:\d+$`; `anchor_id` matches `^sutra:\d+\.\d+\.\d+$` | any malformed row, or the pre-H539 names `corpus_locus`/`corpus_text_id` appearing anywhere |
| 2b-3 | `match_method` ∈ {`exact`, `floor`} on every row, and `confidence` equals `TIER_CONFIDENCE[match_method]` exactly (`exact`→0.95, `floor`→0.85) | any `relaxed`/`fuzzy` row (D6); **or** a constant `match_method` across all rows; **or** any `confidence` not drawn from `TIER_CONFIDENCE` — a `1.0` anywhere fails this check outright, no tier scores 1.0 |
| 2b-4 | Citations resolve **host-independently** (R1/R5) | any citation embeds the deployment host |
| 2b-5 | `tense_caveat` propagated from W1b | any caveated attestation loses its flag |
| 2b-6 | Ambiguity rate published per sūtra | ambiguity collapsed into a single figure |
| 2b-7 | A4 emits `kwic_<adhyāya>.js` shards in the `window.CONC_DATA` shape the Q1 viewer's loader consumes, and a forked `concordance/panini/index.html` renders them | shards absent or malformed; the fork left pointing at Q1's `data/kwic_<letter>.js` |

**Why 2b-7 is not "the viewer reads it unmodified".** It cannot be: the Q1 viewer
never reads a concordance TSV. It loads `concordance/dict/data/kwic_<letter>.js`
shards, and a grep over `concordance/` finds zero occurrences of any `RECORD_FIELDS`
name. The record schema and the viewer's data format are decoupled by construction,
so a shard-emission check is the only form of this check that can actually fail.
See [architecture §9](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md).

**Why 2b-3 does not read "`exact` on every row".** D6 quarantined `relaxed`/`fuzzy`;
it did not reduce the asserted set to `exact`. `build_dict_corpus_concordance.py`
asserts `("xref", "exact", "floor")`, and that set is what scored 11/11 on the
golden sample (4 xref · 4 exact · 3 floor). A4 joins on `form_key()` equality, which
*is* the `floor` tier — so demanding `exact` everywhere would either be unsatisfiable
or, worse, satisfied by mislabelling.

---

## Wave 3

### W3a — Sūtra-coverage map  ·  *the programme's exit check*

| # | Check | Falsified by |
|---|---|---|
| 3a-1 | Every sūtra in the stated enumeration has a row | any absent |
| 3a-2 | The enumeration is **named** and its **exact count** given | "~4,000" published as if exact |
| 3a-3 | Dark sūtras split into the **three** classes with counts | any collapse into one "dark" number |
| 3a-4 | `dark-out-of-scope` is justified per sūtra against vidyut's implemented rule set | class used as a catch-all |
| 3a-5 | `dark-engine-gap` is the **smallest** class, or the excess is explained | large gap class unexplained |
| 3a-6 | Every percentage cites its denominator | any bare percentage |
| 3a-7 | The map is reproducible from the committed script | not re-derivable |
| 3a-8 | Release notes state the **ratio** between lit and the three dark classes | headline coverage without the breakdown |

**3a-3 and 3a-8 are the honesty gates.** The easiest way to make this deliverable
look better than it is would be to report one "dark" figure. The three classes
mean entirely different things — a philological finding, an engine-coverage fact,
and a defect — and merging them destroys the deliverable's value.

### W3b — Release

| # | Check | Falsified by |
|---|---|---|
| 3b-1 | **W1a rights record verified present** before any publish step | release cut without it |
| 3b-2 | Manifest row uses the D8 vocabulary and names its release | non-conforming row |
| 3b-3 | Data statement exists under [docs/data-statements/](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/) | absent |
| 3b-4 | Licence recorded as CC BY-SA 4.0 with vidyut attributed | NC added atop ShareAlike, or attribution missing |
| 3b-5 | Release cut in the **same pass** as the manifest row (D7) | row without release |
| 3b-6 | `/publish-safety-check` recorded | no record |
| 3b-7 | Hubs updated per `/artifact-propagate` | dataset invisible cross-repo |
| 3b-8 | Every published aggregate carries its caveated subtotals | any headline without them |

---

## Wave 4

### W4a — Web surface

| # | Check | Falsified by |
|---|---|---|
| 4a-1 | `/concordance/panini/` live on the interim host | 404 |
| 4a-2 | Sūtra → exemplars → corpus loci navigable end to end | any dead leg |
| 4a-3 | Chain view shows the full ordered derivation | chain truncated or absent |
| 4a-4 | Coverage view shows dark classes **visibly distinguished** | dark sūtras filtered out of the UI |
| 4a-5 | Trust block present: source artefact, n, date | missing |
| 4a-6 | CSV fallback downloads and parses | broken |
| 4a-7 | Citations resolve host-independently | deployment host embedded |

### W4b — Budget

| # | Check | Falsified by |
|---|---|---|
| 4b-1 | N **re-measured at build time**, not hardcoded | constant in the build path |
| 4b-2 | Build log records N, coverage, byte total, share of cap | any missing |
| 4b-3 | Measured coverage ≥ 95% at the chosen N | below target |
| 4b-4 | Total Pages footprint measured **with** A4 pages | projection reported as measurement |
| 4b-5 | Total ≤ **75%** of cap, or head trimmed and reported | shipped at the ceiling silently |
| 4b-6 | Tail reachable via SSR `/w/{slp1}` for a sampled out-of-head lemma | tail 404s |
| 4b-7 | [.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md)'s **"~60% headroom" is left intact** (it is correct for the deployed card tier: 402 MB = 39% of 1,024 MB) and the post-A4 measurement is **appended beside it**, each labelled with its tier and date; only the false *"exceeds the ~1 GB cap"* claim is corrected to 879 MB = 86% **as a projection** for the un-headed card+word-page tier | the ~60% figure overwritten with ~14% — a correct deployed-state number replaced by a hypothetical one; or a projection recorded as a measurement |
| 4b-8 | D4 standing rule recorded in [ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md) | only in this plan |

---

## Migration M1

| # | Check | Falsified by |
|---|---|---|
| M1-1 | `canonical_base` **exists** in the manifest carrying `https://samskrtam.ru/kosha/data/`, and `canonical_base_future` is gone; `interim_release` still names a **release tag** and was not repointed at a Pages URL | `canonical_base` absent or still only `_future`; or `interim_release` rewritten to a Pages host, which it never held |
| M1-2 | Every wave exit check re-run against samskrtam.ru | any not re-run |
| M1-3 | **A citation minted pre-migration resolves unchanged post-migration** | any breaks — R1/R5 violated, `PUBLIC_BASE` leaked the host |
| M1-4 | README + directory page updated | stale host references |
| M1-5 | `CHANGELOG.md` entry | absent |

**M1-3 is the migration's whole point.** If citations break, the interim host was
not interim — it was baked in, and the citability contract failed.

---

## Programme-level definition of done

All five, each independently checkable:

| # | Criterion | Evidence |
|---|---|---|
| 1 | `paninian-corpus-concordance` published with a rights record | 3b-1 … 3b-8 |
| 2 | Sūtra-coverage map published, dark set classified in three classes | 3a-1 … 3a-8 |
| 3 | `morphology-attestation-audit` (A3) published | 1b-1 … 1b-8 |
| 4 | `/concordance/panini/` live with head/tail split applied | 4a-1 … 4b-8 |
| 5 | Four hygiene defects closed, standing rules recorded | 1c, 1d, 1e, 1f |

---

_Dr. Mārcis Gasūns_
