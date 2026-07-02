# Evaluation plan — quality gates the executor cannot game

_Created: 02-07-2026 · Last updated: 02-07-2026_

The judgment-tier gate design for the Gasuns Sanskrit Dictionary (kosha),
authored on Fable 5 (`claude-fable-5`, 02-07-2026) per the queue in
[.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md).
Execution sessions (Sonnet 5 `claude-sonnet-5` / Opus 4.8 `claude-opus-4-8`)
implement against
[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md) +
[PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md);
**this file owns the pass/fail criteria.** Every *Accept:* line in
[USE_CASES.md](https://github.com/gasyoun/kosha/blob/main/USE_CASES.md) becomes
a named test in §6. Companion risk analysis:
[RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md).

The design problem this file solves: an execution session is rewarded for
green checkmarks, and the 02-07-2026 audit showed how planning layers rot into
fiction. So every gate below is built so that **the cheapest way to pass is to
actually build the thing** — samples are drawn by committed procedure (not
executor taste), gold data is frozen before the first scored run, thresholds
live here (not in tunable config), and unknowns fail closed.

## 0. Anti-gaming ground rules (bind every gate)

1. **Freeze before first scored run.** Every gold file / fixture is committed
   under `eval/` with its SHA-256 recorded in `eval/GATES.lock`; scoring
   scripts verify the checksum and refuse to run on a mismatch. After the
   first scored run of the system under test, gold edits are allowed **only**
   to fix demonstrated gold *errors*, each logged in `eval/GOLD_CHANGELOG.md`
   with evidence; if >5 % of a sample needs relabeling, the sample is rebuilt
   by the original procedure, not patched.
2. **Selection by committed procedure, not by hand.** Every sample in this
   plan is produced by a deterministic, seeded script or SQL query committed
   next to the sample. An executor cannot swap hard items for easy ones
   without the diff showing in the procedure.
3. **Thresholds are in this file only.** Code never reads a configurable
   threshold for a gate. Changing a number here is a judgment-tier commit
   with a rationale, never part of an implementation PR.
4. **Fail closed.** Unparseable `<pc>` → no scan link. Lemma absent from DCS →
   "no attestation data", never a fabricated zero. Non-`approved` RU card →
   invisible. Each of these has a **negative test** below; silent guessing is
   the failure mode this project was founded against.
5. **Snapshot discipline.** A change to any committed golden (HTML render,
   Salt envelope, scan fixture) requires an entry in `eval/GOLD_CHANGELOG.md`
   naming what changed and why; CI fails if goldens changed in a PR without
   that entry. Regenerating snapshots to make a failing test pass, without a
   renderer-bug rationale, is the canonical gaming move — blocked by review.
6. **Scorer ≠ system.** Scoring/parity scripts live in `eval/`, import nothing
   from `app/`, and are themselves smoke-tested on a tiny committed toy input
   with a known score.
7. **No ✅ without committed evidence.** Each gate's output artifact (report,
   diff, screenshot) is committed; a checkbox with no artifact is void — the
   02-07-2026 audit lesson, now mechanical.
8. **Provenance on every report:** model tier + exact version, date, input
   checksums.

## 1. G-SEG — segmentation gold sample (gates P4)

**Gate:** top-1 exact lemma-sequence match ≥ 90 % on the frozen 200-form
sample, **and** the calibration rule below — otherwise the paste-anything
feature ships behind a `beta` flag
([IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md)
P4). Both candidate engines (vidyut-cheda; Heritage via the UoHyd mirror —
the Inria host is bot-walled) run on the same frozen sample; the winner is
wired.

**Stratification (200 forms, quotas fixed here):**

| Class | n | What it probes | Example shape | Gold source |
|---|---|---|---|---|
| C1 | 30 | Inflected form, no external sandhi | `rāmeṇa` | DCS |
| C2 | 25 | External vowel sandhi at word boundary | `-a + i- → -e-` types | DCS |
| C3 | 25 | Visarga / consonant sandhi | `rāmo gacchati` types | DCS |
| C4 | 30 | Two-member compounds | `dharmakṣetre` | DCS |
| C5 | 20 | 3+-member compounds | long tatpuruṣa chains | DCS |
| C6 | 20 | **Genuinely ambiguous** — ≥2 defensible analyses | `sthālī-pulāka`-style splits | DCS + judgment annotation of the alternative |
| C7 | 20 | Already-a-lemma controls — must NOT be split | `dharma` | union headwords |
| C8 | 10 | Trap characters: retroflex ḷ/ळ ([FINDINGS §39](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md) — the sanskrit-util ळ→`x` mis-route), avagraha, vowel-length minimal pairs ([§36](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md): naïve NFD+strip-Mn turns `ā`→`a`, `ṣ`→`s`) | `kṛṣṇaḷ…`, `te 'pi` | hand-built, judgment tier |
| C9 | 20 | **Out-of-DCS holdout** — contamination control | passage from a text absent from the DCS dump (e.g. a SamudraManthanam or Kossovich example set passage), verified absent | human/judgment annotation |

**Why C9 exists:** vidyut is trained on DCS-derived data, so a DCS-only sample
measures memorization as skill. C9 is scored separately; if the C9 score falls
more than 15 points below the C1–C6 aggregate, the headline number is reported
as the **C9 number**, not the aggregate — the gate then applies to that.

**Construction:** a seeded sampling script (`eval/build_seg_gold.py`, seed
recorded in the file) draws C1–C6 from the DCS CoNLL-U dump (5.46 M tokens,
human lemmatization = ground truth), stratifying by the dump's own analysis
(sandhi type from the token/lemma mismatch pattern; compound depth from lemma
count). C7 is drawn from
[union_headwords.tsv](https://github.com/gasyoun/SanskritLexicography/blob/master/HeadwordLists/union/union_headwords.tsv).
Output: `eval/gold/segmentation_gold_200.tsv` (form, class, gold lemma
sequence, gold split points, alternatives for C6), frozen per rule 1, then
**MG's 30-minute review** (the P4 critical-path item) before first scored run.

**Scoring rules (in `eval/score_seg.py`):**

- C1–C5, C8, C9: top-1 exact match of the full lemma sequence. Partial credit
  does not exist — a half-right split misleads a student.
- C6: **pass** = the correct analysis appears in an offered list of ≤5 splits;
  **fail** = a single confident wrong answer. Wrong-but-confident is scored
  worse than "no result": any C6 item answered single-headedly *and wrongly*
  is also counted into the calibration rule.
- C7: any split offered = fail (over-segmentation control).
- **Calibration rule:** ≤ 10 % of C6 items may be answered with a single
  unqualified split. The UI consequence is locked: below-margin analyses
  must render as pick-a-split, never as silent top-1.

**Artifacts:** `eval/reports/seg_gold_report.md` — per-class scores for both
engines, C9 delta, calibration count, error table, model/version provenance.

## 2. G-RENDER — golden renders, adversarially selected (gates D2/A1)

**Gate:** byte-exact HTML snapshot equality for every golden; the renderer
cannot merge without them
([ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)
A1). "≥10 sample entries per dictionary" is made adversarial here — random
entries would test the happy path only.

**Selection procedure (committed as `eval/select_goldens.sql`, run against the
imported `kosha.db`; results + rationale to `eval/gold/renders/MANIFEST.md`):**

| Dict | Must include | Why |
|---|---|---|
| MW | `L142512` (`banD`, `<pc>720,1`) and `L523` (`akza`, `<pc>3,2`) | the two known-good anchors from [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md) D2 |
| MW | top-3 entries by `<ls>` tag count (`ORDER BY` count desc) | densest citation apparatus — the hardest markup |
| MW | 1 homonym set with suffixed L-numbers | the `-L{lnum}` id rule feeds G-SALT |
| MW | 1 longest-body entry, 1 minimal one-liner | extremes |
| PWG | ≥3 entries with **accented key2** (`/` accent marks, `a/MSa`-style) | accent rendering; feeds Salt `csl.accentedKey` |
| PWG | entries spanning ≥3 different volumes incl. vol 7 (`vol-page` `<pc>`) | per-volume `<pc>` dispatch |
| PWG | 1 entry with dense German gloss (umlauts, ß) | gloss-language encoding |
| AP90 | entries covering `page-col-letter` `<pc>` variants; 1 dense numbered-senses entry | AP90's `<pc>` format + sense segmentation seed |
| all | ≥1 entry whose body contains Devanagari incl. ळ where the dict has it | the [§39](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md) ळ→`x` sanskrit-util trap must be visible, not latent |
| all | ≥1 entry rich in IAST combining-char traps (`ś`, `ṣ`, `ā`, `ṛ`, `ṝ`, `ḷ`) | [§36](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md) lossy-normalization trap |

**Extra asserts beyond snapshot equality** (they catch a *class* of bug even
when a snapshot is regenerated):

- Output is NFC; combining-character count of the rendered IAST equals that of
  a committed expected string — a lossy `ā`→`a` / `ṣ`→`s` strip cannot pass.
- Round-trip: for the ळ-bearing golden, the SLP1 key path must yield `L`, not
  `x` — this test **fails today by design** if the sanskrit-util bug is hit,
  forcing the executor to consume the `feat/deva-to-slp1` fix or pin a
  workaround, visibly.
- Sense-map sanity per golden: sense spans tile the body without overlap;
  fallback single-sense entries are labeled as such (feeds A2 minting).

Snapshots live in `eval/gold/renders/{dict}/{L}.html`; update discipline per
rule 5.

## 3. G-SALT — Salt facade parity (gates D4 / UC12)

**Gate:** kosha's facade faces `GET /dicts/{id}/restful/entries` and
`/restful/ids` reproduce csl-apidev's run-verified envelopes for **`agni`,
`indra`, `ka`** — including the `-L{lnum}` homonym id rule — within the
tolerance table below. Everything **not** listed as tolerated must be
value-exact.

**Fixtures:** the csl-apidev envelopes for the three headwords are captured
once from the run-verified implementation
([csl-apidev/api1/](https://github.com/sanskrit-lexicon/csl-apidev), the
Salt/[SALT_API_PROFILE](https://github.com/sanskrit-lexicon/csl-standards/blob/main/docs/SALT_API_PROFILE.md)
implementation verified against real MW) and committed under
`eval/fixtures/salt/`, with the MW data snapshot they were produced from
recorded in the fixture header. Parity runs pin `kosha.db` to the **same
csl-sqlite release**; if the releases differ, the run is invalid — re-capture,
don't hand-tolerate.

**Comparison:** structural, on parsed JSON (`eval/salt_parity.py`) — never a
text diff.

| Aspect | Tolerance |
|---|---|
| JSON key order | ignored (structural compare) |
| Entry ids, incl. `-L{lnum}` homonym suffixes | **exact** |
| `csl.{lnum,page,column,scanUrl,references,accentedKey}` | **exact**, field by field, types included |
| Entries array order | exact (profile order) |
| Headword/body strings | exact; if the pinned snapshots provably differ, the run is invalid (see above) — there is no "normalize whitespace and hope" path |
| Extra fields on facade faces | **forbidden** — `kosha.*` extensions exist only inside `/api/v1` responses, never on the facade |
| Server-identity fields (if the profile envelope carries host/timestamps) | tolerated, enumerated by name in `eval/salt_parity.py` |

**Artifact:** `eval/reports/salt_parity_report.md` — per-headword, per-field
diff table (must be empty outside enumerated tolerances).

## 4. G-PC + G-SCAN — `<pc>` truth and scan-link truth (gates D2/D3 / UC2)

- **G-PC (measure, don't assume):** `<pc>` coverage is measured per dict at
  import and written to `sources.pc_coverage` + `data/SOURCES.md`. There is no
  assumed 100 %. A synthetic bad-`<pc>` fixture asserts the fail-closed rule:
  unparseable `<pc>` → entry renders **without** a scan link (rule 4).
- **G-SCAN (200 OK is not the right page):** for 10 sampled entries per dict
  (seeded sample, committed), the resolved scan URL must (a) return HTTP 200
  and (b) pass a **page-truth check**: the entry's print form (`<k2>`) is
  actually visible on the fetched scan image — verified by a vision-model pass
  over the image with the headword as the probe, plus human spot-check of 3
  per dict recorded with screenshots in `eval/reports/scan_truth/`. Known
  anchors MW `banD`→p. 720 col. 1 and `akza`→3,2 are permanent members of the
  sample. Rationale: an off-by-one page mapping returns 200 all day; see
  [RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md) R2.

## 5. G-LAT — measurement method for D5 (so numbers can't be shopped)

D5 decides SLO / cadence / static-cache N **from measurements**; this section
fixes the method so the numbers are comparable and not selectable:

- Latency: warm p50/p95 of `GET /api/v1/lemma/{key}` over a fixed 20-lemma
  list (committed in `eval/latency_lemmas.txt`; includes `dharma`, `banD`,
  `agni`, `indra`, `ka`, plus long-tail picks) × 20 runs each, local uvicorn,
  same machine, DB warm. Cold-start measured separately, once.
- Size: `kosha.db` bytes; top-N cache size for N ∈ {1k, 5k, 20k, 50k} vs the
  GitHub 100 MB per-file limit.
- All numbers + the decisions go to
  [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_DECISIONS_NEEDED.md);
  the SLO itself is set at judgment tier, not by the session that produced
  the numbers.

## 6. Acceptance suite — every USE_CASES *Accept:* line as a named test

Method legend: **auto** = pytest in CI; **script** = committed script run
manually with committed output; **human** = MG/judgment-tier check with
committed evidence (screenshot/report). Nothing here is "trust me".

| Test | UC | Phase | Assertion (concrete) | Method | Anti-gaming note |
|---|---|---|---|---|---|
| T-UC1 | UC1 | P1 | `GET /api/v1/lemma/dharma?dicts=mw,pwg,ap90` → ≥1 entry per dict, each carrying dict label + L-number; warm p95 < 1 s per G-LAT method | auto (latency: script) | latency method fixed in §5, not per-run |
| T-UC2 | UC2 | P1 | MW `banD` (L142512) scan link resolves to p. 720 col. 1; G-SCAN sample passes 200 + page-truth | auto + G-SCAN | page-truth, not just HTTP 200 |
| T-UC3a | UC3 | P1 | `GET /api/v1/form/bhagavAn` → lemma `bhagavant-` via glossary import | auto | fixture-independent: queries the real `forms` table |
| T-UC3b | UC3 | P4 | `dharmakṣetre` returns an offered split incl. `dharma + kṣetra` (locative) | auto | member of G-SEG C4; gold frozen |
| T-UC4 | UC4 | P3 | `dharma` response carries evidence block: freq band + attestation count + ≥1 corpus example with source label. **Negative:** a lemma absent from DCS renders "no attestation data", never a numeric 0 or invented example | auto | the negative half is the gate (rule 4) |
| T-UC5 | UC5 | P6 | Fixture DB with one `approved` + one `ai_translated` pwg_ru card: approved renders with source + review-status label; **`ai_translated` appears nowhere** in API JSON or HTML | auto | negative test is primary; leak = hard fail |
| T-UC6 | UC6 | P5 | The designated verse is fixed **here**: Bhagavadgītā 1.1 (`dharmakṣetre kurukṣetre…`). Scripted walkthrough: every word resolves form→lemma→gloss with no dead end | script | verse locked in this file so an easy verse can't be substituted |
| T-UC7 | UC7 | P2 | `krsna` (typed, no diacritics) → `kṛṣṇa`; then airplane-mode repeat lookup succeeds on a phone | script + human | on-device evidence committed (screenshots) |
| T-UC8 | UC8 | P4 | Paradigm tables render for `deva` (a-stem m.), `nadī` (ī-stem f.), and √bhū cl. 1 present; cell values asserted against committed vidyut-prakriya output | auto | goldens from vidyut, not hand-typed |
| T-UC9 | UC9 | P5 | Gītā 1 and Nala 1 reading packs exist, open, carry ≥50 entries each, 5 spot-checked entries correct | script + human | count floor stops empty-shell packs |
| T-UC10 | UC10 | P7 | Build a next data release that **changes the cited entry**, then resolve the old citation `…@v0.2.0`-style in a fresh browser — it must return the old sense text | script | forces the version-resolution path to exist; see [RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md) R1 |
| T-UC11 | UC11 | P7 | On a clean machine: download release assets, rebuild, run API, T-UC1 passes against the rebuilt DB | script | end-to-end reproducibility, not a docs claim |
| T-UC12 | UC12 | P1/D4 | = G-SALT (§3), incl. `-L{lnum}` homonym ids | auto | tolerances enumerated, all else exact |
| T-UC13 | UC13 | P1→P4 | API docs page documents `form/{form}` + the Salt-shaped entry + `kosha.*` extensions; post-P4: SamudraManthanam performs a real word-click integration | human + script | dogfood integration is the proof, docs alone insufficient |

## 7. Gate registry

| Gate | Phase it blocks | Threshold / criterion | Evidence artifact |
|---|---|---|---|
| G-SEG | P4 exit (else `beta` flag) | ≥90 % top-1 on frozen 200-form gold (C9-adjusted headline) + calibration rule | `eval/reports/seg_gold_report.md` |
| G-RENDER | D2 / any renderer merge | byte-exact goldens + NFC/combining-char + ळ round-trip asserts | `eval/gold/renders/` + CI |
| G-SALT | D4 / P1 exit | parity on `agni`/`indra`/`ka` within §3 tolerances | `eval/reports/salt_parity_report.md` |
| G-PC | D2 | measured per-dict coverage recorded; fail-closed negative test green | `data/SOURCES.md` + CI |
| G-SCAN | D3 | 10/dict: HTTP 200 **and** page-truth; anchors fixed | `eval/reports/scan_truth/` |
| G-LAT | D5 | numbers produced by §5 method only | KOSHA_DECISIONS_NEEDED.md entry |
| T-UC5 | P6 exit | `ai_translated` never visible | CI negative test |
| T-UC10/11 | P7 exit | old citation resolves; clean-machine rebuild | committed run logs |

## 8. CI wiring

- `pytest` markers `p1`…`p7`; CI runs the markers for all phases claimed
  complete — a phase's tests never get skipped after its ✅.
- `eval/GATES.lock` checksums verified in CI; golden changes without a
  `GOLD_CHANGELOG.md` entry fail the build (rule 5).
- Red main = stop, per
  [IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md)
  cross-cutting rules.

---

_Dr. Mārcis Gasūns_
