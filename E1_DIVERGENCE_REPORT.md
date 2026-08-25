# E1 — vidyut-prakriya vs Cologne csl-inflect: nominal divergence report

_Created: 05-07-2026 · Last updated: 25-08-2026_

Wave **E1** of the inflection roadmap
([ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md)
§ Evolution track, ruling **D3**): generate the same paradigms with a second,
independent engine — [vidyut-prakriya](https://github.com/ambuda-org/vidyut)
(rule-based Paninian derivation) — diff them against the ingested Cologne
[csl-inflect](https://github.com/sanskrit-lexicon/csl-inflect) tables, and
classify the divergences so MG can rule whether kosha's forms layer should
**migrate to vidyut, hybridize, or stay Cologne**. This continues Jim
Funderburk's own Cologne-vs-Huet comparison line
([csl-inflect #10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10),
[#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8)) with a **third**
engine (vidyut ≠ Huet — both Paninian, different implementations).

## Method

- **Engine:** [`scripts/compare_vidyut_cologne.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_cologne.py),
  vidyut 0.4.0 `vidyut.prakriya` as a **local library** — no live third-party
  call at build or query time (RISKS.md **R12**-clean), consistent with the D3
  guardrail. Nominals only (verbs are a larger dhātu+gaṇa+lakāra mapping,
  deliberately deferred — see § Verbs below).
- **Sample:** 10,000 frequency-ranked stems that have a dictionary entry
  (`inflections` ⋈ `entries`, ranked by `lemmas.rank_all`), **240,000**
  case×number cells across **87** Cologne declension models. The goal is to
  *characterise* divergence, not regenerate all 6.85 M cells.
- **Mapping:** Cologne `lemma_slp1` → vidyut `Pratipadika.basic`; `gender`
  m/n/f → `Linga` Pum/Napumsaka/Stri; case → `Vibhakti`; number → `Vacana`.
  Each cell's Cologne form-set is compared to vidyut's; cells are classified
  `AGREE` / `DIFF` / `VIDYUT_ONLY` / `COLOGNE_ONLY`, and every `DIFF` is
  sub-classified (below). Reproduce with
  `python scripts/compare_vidyut_cologne.py --limit 10000` (~7 s; raw stats →
  gitignored `data/e1/e1_divergence.json`).

## Headline

| Class | Cells | Share |
|---|---:|---:|
| **AGREE** | 217,226 | **90.5 %** |
| DIFF | 22,758 | 9.5 % |
| VIDYUT_ONLY (Cologne empty, vidyut fills) | 16 | 0.0 % |
| COLOGNE_ONLY (vidyut empty) | 0 | 0.0 % |

**Two independent engines — one 20-year hand-curated table set, one modern
Paninian derivation — agree on 90.5 % of cells.** That is the strong baseline
D3 anticipated: Cologne's data is trustworthy, so vidyut is a *check and
supplement*, not a replacement.

## Divergence taxonomy (the 9.5 % that differ)

| Sub-class | Cells | % of DIFF | Verdict |
|---|---:|---:|---|
| `other` (systematic derivation forks) | 13,666 | 60.0 % | ⚖️ **scholarly fork** — stem-specific |
| `final_stop` (`cāt` vs `cāt`/`cād`) | 7,454 | 32.8 % | 🟰 **representation choice** — neither wrong |
| `vidyut_superset` (vidyut adds valid variants) | 955 | 4.2 % | ➕ vidyut richer |
| `natva` (`nṛpena` vs `nṛpeṇa`) | 326 | 1.4 % | 🔴 **Cologne wrong** (MWinflect#6) |
| `cologne_superset` (Cologne adds variants) | 253 | 1.1 % | ➕ Cologne richer |
| `pronominal` (`sarvāya` vs `sarvasmai`) | 104 | 0.5 % | 🔴 **Cologne wrong** (mis-modelled) |

### 🔴 Cologne clearly wrong (vidyut wins)

- **ṇatva bug (MWinflect#6) — 326 cells / 89 stems in the sample.** Cologne's
  m_a table never applied the Pāṇini 8.4.1-2 retroflexion, so it emits
  `nṛpena`/`nṛpānām` where the attested / vidyut form is `nṛpeṇa`/`nṛpāṇām`.
  **The blast radius is larger than the 69 compounds
  [MWinflect#6](https://github.com/sanskrit-lexicon/MWinflect/issues/6)
  enumerates** — 89 affected stems in just the top-10k sample, so the full table
  count is materially higher. vidyut fixes every one automatically.
- **Pronominal stems declined nominally — 104 cells.** `sarva`, and other
  sarvanāmas, appear in Cologne's m_a/n_a rows declined as ordinary nouns
  (dat.sg `sarvāya`, abl.sg `sarvāt`, gen.pl `sarvāṇām`, nom.pl `sarvāḥ`) *as
  well as* in a correct `m_pron` row. vidyut declines them pronominally
  (`sarvasmai`, `sarvasmāt`, `sarveṣām`, `sarvasmin`, `sarve`) — the m_a/n_a
  copy is a mis-modelled duplicate.

### ⚖️ Genuine derivation forks (scholarly judgment — the `other` 60 %)

Concentrated in the feminine and consonant models (`f_A` 1,760, `m_a`/`n_a`
pronominal residue, `f_1_t`, and the monosyllabic/`-us`/`-is` stems):

- **Feminine of consonant/adjectival stems** — `mahat` (fem): Cologne declines
  the consonant stem (`mahat`, `mahatā`, `mahataḥ`…); vidyut forms the **-ī
  feminine** (`mahatī`, `mahatyā`, `mahatīm`…). The -ī feminine is the standard
  analysis, but which surface a dictionary *should list* is an editorial call.
- **Monosyllabic / irregular ā-stems** — `vā`: Cologne applies the regular
  `senā` template (`vayā`, `vāyai`, `vānām`); vidyut applies the monosyllabic
  feminine rules (`vā`, `vai`, `vām`). Genuinely different analyses of a rare
  stem.

These are exactly the cases D3 warned against discarding blind: some are Jim's
deliberate editorial choices, some are vidyut being more Paninian; **neither
engine is uniformly right**.

### 🟰 Representation choices & coverage (neither "wrong")

- **Final-stop voicing (33 % of DIFF)** — vidyut lists both pre-sandhi variants
  (`cāt` **and** `cād`) where Cologne lists one. Cosmetic; a display/citation
  convention, resolvable by normalising one way.
- **Optionality modelling** — `para`/`sva` (optional sarvanāmas): vidyut merges
  `parāḥ`+`pare` in one cell; Cologne splits them across m_a and m_pron rows.
- **Cologne richer (253 cells)** — Cologne lists optional neuter i/u-stem
  vocatives (`guro` beside `guru`) that vidyut omits. Cologne is *more*
  permissive here.
- **Coverage gaps vidyut fills (VIDYUT_ONLY)** — Cologne's `inflections` has **no
  rows** for some cardinal-number paradigms (`saptadaśan` = 17, `m_card`);
  vidyut generates the full declension. A real coverage win for vidyut on
  numerals.

## Answer to csl-inflect #10 / #8 (give-back)

[#10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10) set up a
Cologne-vs-Huet noun-declension comparison (`decline_one_huet.py`,
`readme_compare.txt`). This report adds an **independent third data point** — a
vidyut-prakriya comparison over 10k entry-bearing stems — that corroborates the
Huet line and quantifies where the three engines part ways. The drafted
give-back comment for #10 is in the E1 handoff
([H185](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md));
**it is not posted** — posting to the dormant, noise-averse upstream is
diplomacy-gated (RELATIONS.md §2/§7) and awaits MG's go-ahead.

[#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8) is verb-side. Its
answer is the § Verbs section above, and the **drafted give-back comment is in
the H3166 handoff body**
([H3166](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H3166-Opus_kosha_inflect-dhatu-identity-crosswalk_19.08.26.md),
25-08-2026) — **also not posted**, same diplomacy gate. The draft deliberately
leads with the 70.24 % figure *and* the finding that 85 % of the residue is a
resolution artifact rather than divergence: posting the raw 11,056 as "conflicts"
would hand the upstream a number we have since shown to be mostly ours, not
theirs.

## Recommendation → MG ruling (migrate / hybridize / stay)

**Recommended: hybridize.** Keep Cologne as the attested, hand-curated base
(D3 — do not discard Jim's 20 years), and layer vidyut to:

1. **auto-correct the ṇatva bug** (326+ cells; the single highest-value fix —
   surfaces today verbatim in the K2b UI per the D3 guardrail);
2. **fill coverage gaps** (cardinal numerals and any other VIDYUT_ONLY cells);
3. **flag — not silently overwrite — the pronominal mis-models and the
   feminine-stem forks** for editorial review (they are 60 % of DIFF and are
   *not* mechanical fixes).

A full **migrate** discards Cologne's richer optional forms (neuter vocatives)
and its editorial choices; a pure **stay** ships a known, now-quantified bug.
The @DECIDE is filed in
[Uprava/GTD_NEXT_ACTIONS.md](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md).

### ✅ Ruled HYBRIDIZE + implemented (H185, 12-07-2026)

MG **ruled HYBRIDIZE** (05-07-2026, reaffirmed 10-07-2026). The forms-layer pass
[`scripts/build_hybrid_forms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_hybrid_forms.py)
(`build_db.py --stage hybrid`) now applies it over `inflections`, reusing this
report's own classifier. The shipped `kosha.db` materialises **326 ṇatva-fix
rows / 55 stems**, **17 `m_card` gap-fill rows**, and **13,888 cells flagged
`disputed`** (the `pronominal` + `other` forks). These are the full-pass counts;
the top-10k characterization sample above reported 89 ṇatva-bearing stems / 16
gap-fills / 13,770 disputed — the drift is sample-vs-full-run, not a classifier
change (the 326 ṇatva **cell** count is stable across both):

- **ṇatva → auto-fix.** Each affected cell gets the vidyut-corrected form as a
  new `source='hybrid-natva-fix'` row; the display layer
  ([`app/paradigm.py`](https://github.com/gasyoun/kosha/blob/main/app/paradigm.py))
  prefers it and records the superseded Cologne form in `cell_notes`. The buggy
  Cologne row is **not deleted** — a reader who types `nfpena` still resolves it
  in reverse lookup (`source` tells them it is the Cologne base).
- **VIDYUT_ONLY → gap-fill.** New `source='vidyut-gap-fill'` rows (cardinals).
- **pronominal / `other` forks → `disputed=1`.** Cologne stays the display
  default; the flag surfaces an editorial-review affordance to the K2b UI, and
  in the `/analyze` reverse endpoint. Representation-only (`final_stop`) and pure
  coverage supersets are left untouched (neither engine wrong).

The full entry-bearing set (235,849 paradigms) is a longer offline pass MG runs
out-of-band via `--stage hybrid` (A3), exactly like `build_paradigms --all`.

## Verbs (H185 Task C + H855 dhātu-identity crosswalk — present-system comparison, answers #8)

The verb half runs
[`scripts/compare_vidyut_verbs.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_verbs.py):
Cologne's present-system rows (`v_<gana>`/`v_p`, ingested in K2a) → vidyut's
`Tinanta` API (gaṇa Bhvādi/Divādi/Tudādi/Curādi; lakāra Laṭ/Laṅ/Loṭ/Vidhiliṅ;
prayoga Kartari/Karmaṇi; dhātupada Parasmai/Ātmane), diffing the same four
classes as the nominal pass. Third-engine answer to
[#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8) (Jim's
Cologne-vs-Huet verb line).

**The first pass (v0.21.0, bare-root upadeśa) scored a misleading strict
agreement of 12.68 %** — because `Dhatu.mula(bare_root, gaṇa)` is ambiguous where
the nominal `Pratipadika.basic(stem)` was not: Cologne stores the bare SLP1
root, vidyut wants the *aupadeśika* dhātu (accent + anubandhas), so **259/683
roots derived nothing** and 29,268 cells fell to `COLOGNE_ONLY`. That low number
was a **dhātu-identity mapping artifact, not grammar disagreement** — the
report's named follow-on.

**H855 builds that crosswalk**
([`scripts/build_dhatu_crosswalk.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_dhatu_crosswalk.py)
→ committed [`data/e1/dhatu_crosswalk.json`](https://github.com/gasyoun/kosha/blob/main/data/e1/dhatu_crosswalk.json)):
each Cologne `(root, gaṇa)` is matched to the dhātupāṭha entry whose vidyut
present-3sg-active equals Cologne's (else the bare root already derives, else a
normalized-bare match) — **722/779 (92.7 %)** of the gaṇa-1/4/6/10 root-models
resolved (3sg 474 / direct 205 / bare 43; 57 unresolved, never guessed).
Example: `as` (div) now maps to the aupadeśika `asu~` (04.0106) → `asyati`,
matching Cologne, instead of the wrong `Ayati`.

**With the correct upadeśa, strict agreement rises 12.68 % → 70.24 %** — near the
nominal 90.5 %, confirming the low first number was mapping, not divergence. Over
47,340 cells where both engines now produce a form:

| Class | Cells (H855) | Before (bare-root) | Note |
|---|---:|---:|---|
| AGREE (strict) | 33,253 (70.24 %) | 4,320 (12.68 %) | clean once the dhātu resolves |
| COMPATIBLE (+ cosmetic) | 36,284 (76.65 %) | — | AGREE + final-stop + superset |
| DIFF genuine conflict | 11,056 | 29,452 | true divergence (accent/sandhi/gaṇa-shift) |
| DIFF final-stop (t/d) | 937 | 126 | citation-form choice |
| DIFF vidyut superset (`-tāt`) | 1,711 | 126 | vidyut richer |
| DIFF cologne superset | 383 | — | Cologne richer |
| COLOGNE_ONLY (vidyut empty) | 15,984 | 29,268 | residual: 110 still-underivable roots + 75 passives with no gaṇa to borrow |
| VIDYUT_ONLY | 4,680 | 3,852 | — |

Roots vidyut cannot derive dropped **259 → 110**. The crosswalk is a **committed
run-time input** carrying only aupadeśika strings, so the comparison needs only
bundled vidyut (`Dhatu.mula`); the external `vidyut-data` is a build-time-only
input for the crosswalk builder (R12).

### The 11,056 "genuine conflicts" are mostly NOT divergence (H3166, 25-08-2026)

H855 stopped at the headline. H3166 adjudicated the residue, and the sentence
this section used to carry — *"the remaining 11,056 genuine conflicts are real
accent/sandhi/gaṇa-assignment differences needing scholarly review"* — **does
not survive the measurement.** It is the same mapping artifact H855 diagnosed
for the 12.68 %, one level down.

**Where the conflicts sit.** Over all 11,056 cells
([`scripts/profile_verb_divergence.py`](https://github.com/gasyoun/kosha/blob/main/scripts/profile_verb_divergence.py)
→ [`data/e1/verb_divergence_profile.json`](https://github.com/gasyoun/kosha/blob/main/data/e1/verb_divergence_profile.json)):
**55.8 % are passive** (`v_p`), **66.9 % have vidyut's form shorter than
Cologne's**, and all of them come from just **192 of the 683 roots**. A genuine
grammatical disagreement would not concentrate like that.

**Why.** The crosswalk resolved 722/779 root-models, but its `direct` and `bare`
paths *choose the bare Cologne root as the seed* — **212 entries (27.2 %) still
feed `Dhatu.mula` an unmarked root** rather than an aupadeśika one. Those roots
carry **9,396 of the 11,056 conflicts — 85.0 %**
([`scripts/measure_passive_bare_root.py`](https://github.com/gasyoun/kosha/blob/main/scripts/measure_passive_bare_root.py)
→ [`data/e1/verb_conflict_bare_root_measure.json`](https://github.com/gasyoun/kosha/blob/main/data/e1/verb_conflict_bare_root_measure.json);
active 97.2 %, passive 77.6 %, middle 72.1 %). Without it-markers vidyut consumes
the root-final consonant, so `yat` → `yyate` where the passive is `yatyate`,
`kam` → `kyate`, `paṇ` → `pyate`, `kṣam` → `kṣyate`.

**The discriminating probe.**
[`scripts/probe_passive_conflict.py`](https://github.com/gasyoun/kosha/blob/main/scripts/probe_passive_conflict.py)
re-derives the same cell from the crosswalk's seed and from the bare root. For
`yat`/`kam`/`paṇ`/`ruc`/`kṣam` the two are **identical** — the crosswalk left
them bare, so the malformation is not a crosswalk mis-pick. For `pā`, where the
crosswalk *did* resolve (`pA\`), vidyut returns **`pīyate`** against Cologne's
`pāyate` — vidyut is right and Cologne is wrong. Resolution is the variable.

**Hand adjudication, 52 rows, class-weighted** (seed 3166,
[`scripts/sample_verb_divergence.py`](https://github.com/gasyoun/kosha/blob/main/scripts/sample_verb_divergence.py)
→ [`data/e1/verb_divergence_adjudication.tsv`](https://github.com/gasyoun/kosha/blob/main/data/e1/verb_divergence_adjudication.tsv);
adjudicator **Opus 5 (`claude-opus-5`)**, not a human sign-off). Of the 30
`DIFF_conflict` rows:

| Verdict | Rows | Example |
|---|---:|---|
| **bare-root truncation — artifact, not divergence** | 20 | `kāś` `kāśyāmahe` vs `kāyāmahe` |
| vowel-grade (guṇa/vṛddhi) — **real, needs review** | 5 | `śiṣ` `śiṣyeta` vs `śeṣyeta` |
| curādi vṛddhi fork — **real modelling fork** | 3 | `tul` `tolayethāḥ` vs `tāvayethāḥ` |
| genuinely different form — **real** | 1 | `kṣup` `akṣupat` vs `akṣuvat` |
| **Cologne is wrong**, vidyut right | 1 | `pā` `pāyate` vs `pīyate` |

The 67 % artifact share in the sample matches the 66.9 % shorter-form and 85 %
bare-seeded population figures. The three control classes adjudicated as their
labels claim: `DIFF_final_stop` is 100 % active citation-form `t`/`d`,
`DIFF_vidyut_superset` is 91.8 % active and is the loṭ `-tāt` forms plus
alternate curādi stems, `DIFF_cologne_superset` is 383 cells from **8 roots**
only (Cologne listing both vṛddhi and non-vṛddhi causative stems).
`COLOGNE_ONLY` is **77.3 % middle voice** — a pada-assignment fork, Cologne
tabulating ātmanepada that vidyut declines to derive, not a coverage bug.

**What the corrected number looks like.** If the bare-seeded 85 % is artifact,
true divergence is at most **~1,660 cells — 3.5 % of the 47,340 both-nonempty
cells**, not 23 %. The next rung is mechanical and named: resolve the 212
bare-seeded entries (the 57 `unresolved` first) and re-run. **Not done here** —
this pass measures, it does not re-tune the crosswalk.

**Conclusion for #8 / the forms layer (unchanged posture, D3).** The 70.24 %
agreement is a *comparison* result, not a licence to hybridize verbs, and the
posture does not change — but the *reason* does. The blocker is no longer "real
differences needing scholarly review"; it is that **85 % of the residue is still
a resolution artifact**, with only ~1,660 cells plausibly genuine and 110 roots +
75 passives unresolved. Cologne's verb tables remain the display base. Raw stats: gitignored
`data/e1/e1_verbs_divergence.json`; reproduce with `python
scripts/build_dhatu_crosswalk.py && python scripts/compare_vidyut_verbs.py`.

## Deferred (deliberately)

This pass is present-system verbs only (Laṭ/Laṅ/Loṭ/Vidhiliṅ). The non-present
lakāras (perfect, aorist, future) are future work.

*(Corrected 25-08-2026, H3166: this paragraph used to also list "the
dhātu-identity crosswalk that would make a full verb comparison meaningful" as
future work. It was already built — H855, above — and that stale line is what
sent H3166 out to build it a second time. A "Deferred" list is a claim about the
present, and it goes stale the moment the section above it ships.)*

The **remaining** crosswalk work is narrower and named: 212 of the 779
root-model entries still seed vidyut with a bare root, which the § above shows
carries 85 % of the surviving conflicts. Resolving those — the 57 `unresolved`
first — is the next rung, and it is mechanical.

## Optional paper

The three-engine (Cologne / Huet / vidyut) divergence table — especially the
ṇatva blast-radius quantification and the pronominal/feminine-fork taxonomy —
continues Jim's Cologne-vs-Huet line and is publishable. Scaffold via
`/paper-scaffold` only if MG wants it (roadmap E1 deliverable (c), optional).

_Dr. Mārcis Gasūns_
