# Plan — kosha Concordance Q3: Pāṇinian sūtra ↔ corpus (2026 H2)

_Created: 18-07-2026 · Last updated: 20-07-2026_

The index doc for kosha's next programme. It records **what was decided and by
whom**, states the **autonomy contract** an agent operates under, and links the
four documents that carry the actual content.

> **Scope in one line.** Build the first corpus-grounded Pāṇinian concordance —
> `sūtra → {attested corpus forms exemplifying it}` — over the DCS corpus, with a
> **sūtra-coverage map** (which of ~4,000 sūtras have real exemplars, which are
> dark) as the exit check.

| Doc | What it answers |
|---|---|
| [ROADMAP_KOSHA_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026H2.md) | Wave order, dependencies, what is deliberately out of scope |
| [ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md) | Record schema, the two joins, licence composition, Pages/SSR split |
| [IMPLEMENTATION_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_CONCORDANCE_Q3.md) | Step-by-step build, script by script, manifest row by manifest row |
| [VERIFICATION_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_CONCORDANCE_Q3.md) | Exit checks, gates, and how each claim can be falsified |
| [PLAN_KOSHA_CONCORDANCE_Q3_2026H2.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.meta.md) | Provenance, improvement backlog, limitations of this plan |

---

## 1. Naming reconciliation — read this before anything else

The ruling names the next programme **"Concordance Q3 (Pāṇini / derivation
chains)"**. [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md)
numbers the Pāṇinian workstream **A4 / Q4**, and reserves **Q3** for **A3**, the
generated-vs-attested morphology audit. Both labels are in circulation and they
disagree.

**This plan resolves it as:** the *calendar slot* is Q3 (the next quarter); the
*workstream* is **A4**, promoted ahead of A3. Everywhere below, "Q3" means the
quarter and "A4" means the Pāṇinian concordance. The roadmap's own A4 section
should be re-labelled in the same pass that this plan lands, so a third naming
does not appear.

**The promotion has a cost, and it is not cosmetic.** CONCORDANCE_ROADMAP states
plainly that *"Q4 depends on Q3's attested-form join"* and that *"running a later
stage against a stale earlier one produces silently wrong output, not an error."*
A4's declared input is A3's attested-form join. **A3 has not been built** — there
is no `morphology-attestation-audit` row in
[datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
and no such artefact anywhere in the repo (verified 18-07-2026). Promoting A4
therefore does not skip A3; it **absorbs A3's join into A4's wave 1** as a
prerequisite. That is the shape of the roadmap below, and it is the single
largest structural consequence of the ruling.

---

## 2. Decisions taken

Every row is settled. The `Source` column distinguishes a human ruling (do not
re-litigate) from a default this plan applied on the dominant option, and flags
the two places where a ruling **overturned** the batch recommendation.

| # | Decision | Source | Note |
|---|---|---|---|
| D1 | Next programme = **Concordance Q3 / A4, Pāṇinian sūtra ↔ corpus**; exit check is a sūtra-coverage map | Human ruling 17-07-2026 | **Overturned the batch recommendation**, which proposed P-D5 (data-hub work) instead. Ruling stands; P-D5 is not dropped, it is re-queued behind this programme (see [roadmap §5](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026H2.md)) |
| D2 | Derivation-metadata licence is **confronted first, not assumed** — wave 1 opens with a written rights record; nothing publishes before it exists | Human ruling 17-07-2026 (scope), evidence-resolved here | See §3 — the evidence points to a clean composition, but the record must be written, not inferred |
| D3 | Deploy gate: samskrtam.ru remains canonical, expected ~25-07-2026; **[gasyoun.github.io/kosha](https://gasyoun.github.io/kosha/) is the explicit interim host** | Human ruling 18-07-2026 | Interim **with a named migration step** (M1, §4), not a permanent route-around. Manifest URLs and exit checks run against Pages now |
| D4 | Pages budget: **static head chosen by corpus token coverage, SSR tail via `/w/{slp1}`** — recorded as a **standing rule** | Human ruling 18-07-2026 | Measured N below (D5). Standing so it does not reopen a third time; D5-3 already settled the same question once for cards |
| D5 | Static head **N = 11,148 lemmas** = 95.00% of DCS corpus token mass | Measured 18-07-2026 from [lemma_frequency.tsv](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv) | Not a guessed round number. 59,282 lemmas carry `count_all`, 4,550,704 tokens total. Curve in [architecture §6](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md) |
| D6 | Relaxed concordance tier **dropped entirely**; 2,171-item review sheet cancelled; recorded as a documented dead end | Human ruling 18-07-2026 | **Overturned** any plan to review the tier. Q2 exit ships **strict-tier-only**. Dead-end record routes to [Uprava/DEAD_ENDS.md](https://github.com/gasyoun/Uprava/blob/main/DEAD_ENDS.md) per the epistemic-registry convention |
| D7 | Data-release cadence = **rolling** (every wave adding a public dataset cuts a data release in the same pass) **plus** one catch-up `data-v0.2.0` clearing the 32-row backlog | Default applied | Mirrors the existing code-release rule. 32 rows currently sit at `in_release: "unreleased"` (verified) |
| D8 | Manifest schema fix: `in_release` becomes **required with a closed vocabulary**; `release_asset` required for every `public` row | Default applied, **premise corrected** | The brief's premise ("38 rows carry no `in_release` field") is **false** — see §3. The real defect is different and is stated there |
| D9 | README dataset count = **computed from datasets.json at build time**, with a test invariant | Default applied | README claims 57 (43 public); actual is **77 (63 public · 11 restricted · 3 intermediate)**. Restricted and intermediate counts are correct; the entire drift is in the public count |
| D10 | DICO French-gloss layer = **manifest dataset row only, no UI** | Default applied, **blocked on evidence** | Cannot execute as written — the row already exists and is rights-blocked. See §3 |
| D11 | Handoff/link hygiene = **fix the mover, not the symptoms**, plus a one-time catch-up | Default applied | 7 handoffs moved to `archive/` in one sweep → **14 dead link occurrences** in [PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md) (7 unique targets × 2 occurrences each — verified exactly) |
| D12 | A3 (generated-vs-attested join) is **absorbed into A4 wave 1** as a prerequisite, not skipped | Derived from D1 | See §1. Without it A4 has no attested-form input |
| D13 | The A3→A4/W2a **generated side is `forms`** (1,378,401 rows / 426,410 non-heritage), **not `inflections`** (6,917,018) | Ruling 20-07-2026 (H1366, Opus 4.8 `claude-opus-4-8`), **accepted by MG** | Resolves [CONTRADICTIONS §3](https://github.com/gasyoun/SanskritLexicography/blob/master/CONTRADICTIONS.md). See §3a. `inflections` is a distinct single-engine (`cologne_mwinflect`) paradigm asset — an optional cross-check, never the denominator. **W2a is unblocked to consume `forms`** |

---

## 3a. D13 — which generated table is canonical (`forms`, ruled)

CONTRADICTIONS §3 stood 🟡 provisional: the Concordance-Q3 plan set named two
different kosha tables as the generated inflection side, "5× apart" — `forms`
(1,378,401) in the W1b deliverable text vs `inflections` (6,917,018) in the §1
diagram. **Ruled 20-07-2026 (H1366, accepted by MG): `forms` is canonical**, and
the "5× apart, same side" framing was itself a conflation — the two tables are
different data products, not two cardinalities of one.

Measured 20-07-2026 (Opus 4.8 `claude-opus-4-8`) directly against
[`kosha.db`](https://github.com/gasyoun/kosha/blob/main/data/db/kosha.db):

| | `forms` | `inflections` |
|---|---|---|
| rows | **1,378,401** | 6,917,018 |
| columns | `form_slp1, lemma_slp1, source, category` | `form, lemma, model, gender, gcase, number, person, tense, voice, refs, source, disputed` |
| morphology (case/gender/number) | **none** | model 100%, case/gender/number ~99% |
| `source` split | **heritage 951,991 · dcs 397,843 · vidyut 28,567** | 99.99% `cologne_mwinflect` (+ 496 curated) |
| relationship | shares **only 168,034 of 426,410** non-heritage `(form, lemma)` pairs with `inflections` | holds **3,246,914** `(form, lemma)` pairs absent from `forms` |

**Why `forms`, on three independent grounds:**

1. **Pipeline continuity.** W2a's declared input is "each attested form **from
   W1b**" ([roadmap W2a](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026H2.md)),
   and W1b/A3 is defined over `forms` non-heritage (426,410 — the AG denominator).
   Switching to `inflections` mid-pipeline orphans A3 and makes A4 coverage
   incommensurable with it.
2. **Trust axis.** Only `forms` carries the `source` column
   (`dcs > vidyut > heritage`, `include_heritage=False`) the H696 discipline
   requires. `inflections` is ~100% one engine with no heritage/attestation split
   and cannot express it.
3. **Engine separation.** W2a *generates* morphology + the sūtra chain via
   `vidyut.prakriya`; it must not silently inherit `cologne_mwinflect`'s morphology
   from `inflections`. The overlap (168,034 pairs) is a legitimate **cross-check**
   (does vidyut-derived `model`/`case` agree with `cologne_mwinflect`?), not a
   denominator.

**`inflections` reclassified:** the MW full-paradigm morphology table
(`cologne_mwinflect`), a distinct secondary asset — not the A4 generated side.
The §1 diagram's former "6.9M generated" label was a documentation bug (corrected
in [ARCHITECTURE §1](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md)).
Full brief + options A/B/C:
[DECIDE_H1366_GENERATED_SIDE_FORMS_VS_INFLECTIONS.md](https://github.com/gasyoun/kosha/blob/main/docs/DECIDE_H1366_GENERATED_SIDE_FORMS_VS_INFLECTIONS.md).

---

## 3. Where the briefed premises did not survive contact

Four premises this plan was handed do not match the repository. They are stated
here rather than quietly worked around, because each changes what wave 1 must do.

| Premise as briefed | What the repo actually shows | Consequence |
|---|---|---|
| "38 of 77 rows carry no `in_release` field at all" | **All 77 rows have `in_release`.** The field missing from 38 rows is `release_asset` (39 present / 38 absent). `in_release` values: `null` ×38, `"unreleased"` ×32, `"data-v0.1.0"` ×7 | The drift vector is not a *missing* field but an **undefined one**: `null` and `"unreleased"` are used interchangeably with no documented distinction. D8 fixes the real defect — a closed vocabulary (`released:<tag>` · `unreleased` · `not-applicable`), plus `release_asset` required on public rows |
| "Cross-check the ~478MB/~402MB figures" — implying the Pages budget is already exceeded | 402 MB cards is a **measured** figure (03-07-2026, 50,355 cards). Full word-page set recomputes to **477.0 MB** at 9.7 KB/page × 50,355 — the ~478 MB figure is sound. But **402 + 477 = 879 MB = 86% of the 1,024 MB soft cap** — it does **not** exceed it, contrary to [.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md) | The ruling (D4) still holds, on **headroom** grounds rather than overflow: 86% with zero room for the next ingest is not shippable. The corrected framing goes into the standing rule so the next reader is not told a false thing |
| "DICO French-gloss layer ships as a manifest dataset row only" | The layer **is already a manifest row** — `heritage_dico_gloss` inside [`heritage-forms-crosswalk-extras`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) — at **`tier: restricted`**, because Heritage is **LGPLLR rights-@DECIDE pending** | D10 is **not executable as written**. Publishing it means resolving the LGPLLR question first — a rights decision a human takes, not a default an agent applies. Wave 1 prepares the rights brief; it does not flip the tier. This is a second licence blocker of the same class as D2 |
| A4's input is "the Q3 attested-form join" | **A3 does not exist** — no `morphology-attestation-audit` artefact or manifest row | D12: A3's join becomes wave-1 work (W1b), not an assumed input |

**On D2, the derivation-metadata licence.** The evidence is better than the
`@DECIDE` implies, but the record still has to be written. Per
[external_tools.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json),
**vidyut is MIT**; the Aṣṭādhyāyī sūtra text is public domain; DCS attestations are
recorded there as **CC BY-SA 4.0**. MIT composes into a BY-SA work cleanly, so the
expected ruling is *"output is CC BY-SA 4.0, vidyut attributed"*.

**Open question W1a must settle — the repo contradicts itself on DCS.**
`external_tools.json` (`id: dcs`) says **CC BY-SA 4.0**;
[CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md)
line 151 — this programme's own parent doc — says *"B1/B3 join DCS (CC BY 4.0)"*,
and the `reading-pack-*` rows in
[datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
repeat "DCS is CC BY 4.0". This plan does **not** silently pick one. What is *not*
at stake is the output licence: **CDSL dictionary data is CC BY-SA 4.0 and is an A4
input regardless**, so ShareAlike binds under either DCS answer (the repo's own
`CLAUDE.md`: data releases are BY-SA, "inherited from Cologne's ShareAlike"). What
the answer *does* change is the attribution and provenance record, and the fact that
one of kosha's own files is currently wrong about a primary input. W1a resolves it
against **DCS's own published terms**
(Hellwig's repository and site, not a kosha secondary source), records the finding,
and corrects whichever kosha file is wrong in the same pass. Until then A4 is treated
as **BY-SA** — safe under either answer. This is a **third** open licence question
alongside vidyut's bundled data and Heritage LGPLLR.

What is **not** yet verified on the vidyut side is
whether vidyut's **bundled derivation data** (dhātupāṭha, rule tables) carries
the same MIT terms as its code — that is the one open question, and it is a
file-reading task, not a judgement call. W1a resolves it and writes the record in
the shape of the existing
[Franceschini permission record](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/franceschini_hos9_permission_2026-07-13.md).
**No A4 dataset publishes until that file exists.**

---

## 4. The interim-host migration step (D3)

Recorded here so it is one grep away, not buried in an architecture section.

| ID | Step | Trigger | Owner |
|---|---|---|---|
| **M1** | Add a top-level `canonical_base` in [datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) carrying `canonical_base_future`'s value (`https://samskrtam.ru/kosha/data/`), retire the `_future` key, leave `interim_release` untouched, and re-run every exit check in [VERIFICATION_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_CONCORDANCE_Q3.md) against `https://samskrtam.ru/kosha/` | samskrtam.ru deploy opens (~25-07-2026) | Agent, on MG's word that the host is live |

Two invariants make M1 cheap and keep it from becoming a rewrite:

- **Citation URLs never carry the deployment host.** This is
  [RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md) R1/R5 and the
  repo's own [CLAUDE.md](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md)
  rule: `PUBLIC_BASE` is deliberately not the deployment host. A4 citations
  inherit this — a sūtra-exemplar citation minted against Pages must resolve
  unchanged after the migration, or the migration has broken citability.
- **The manifest half-models this — know the actual fields before touching them.**
  What exists today is `canonical_base_future` (`https://samskrtam.ru/kosha/data/`)
  and `interim_release`
  (`https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0`). **`canonical_base`
  does not exist**, so M1 *creates* it rather than flipping a pair. And
  `interim_release` is a **GitHub release tag, not a Pages URL** — the Pages host
  `gasyoun.github.io` appears in **no** manifest field whatsoever. The two interim
  surfaces are independent: Pages is the interim host for *web pages* (D3), the
  release tag is where *datasets* are fetched from until samskrtam.ru serves them.
  M1 migrates the first and leaves the second alone. Anyone who reads M1 as
  "repoint `interim_release` away from Pages" is acting on a field that never held
  a Pages URL.

---

## 5. Autonomy contract

What an agent executing this programme may do without asking, and where it must
stop.

| May proceed without asking | Must stop and surface |
|---|---|
| Build, measure, and report any join, coverage map, or budget figure | Publishing **any** A4 dataset before the W1a rights record exists (D2) |
| Cut a data release for a wave that added a public dataset (D7) | Flipping `heritage-forms-crosswalk-extras` from `restricted` to `public` — LGPLLR is a human decision (D10) |
| Mint the wave's handoff, commit, open the PR, merge it | Re-litigating D1, D3, D4, D6 — settled human rulings |
| Fix the manifest schema, README count, link rot, registry staleness | Confirming `Polnorazmernye/` as the canonical parallel-passage variant — R-C2, still an open `@DECIDE` |
| Record a dead end, a contradiction, or a gap in the epistemic registries | Widening scope beyond the waves in the roadmap |

**Honest-reporting clause.** Every quantitative claim in this programme is
reported with its denominator and its measurement date. Where a figure
contradicts an earlier committed figure, both are shown and the discrepancy is
explained — the D5-3 coverage figure in §2 D5 and the Pages-budget figure in §3
are worked examples of the required form. A number that cannot be reproduced from
a committed script is not shipped.

**Dependency discipline.** Per CONCORDANCE_ROADMAP: a later stage run against a
stale earlier one produces silently wrong output, not an error. Every wave in
[IMPLEMENTATION_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_CONCORDANCE_Q3.md)
therefore states its input artefact **and that artefact's expected build stamp**;
a mismatch halts the wave.

---

## 6. Definition of done for the programme

The quarter is done when all five hold:

1. `paninian-corpus-concordance` exists as a manifest row **and** a public-tier
   data release, with a written rights record backing it.
2. A **sūtra-coverage map** is published: for each of the ~4,000 Aṣṭādhyāyī
   sūtras, the count of attested corpus exemplars, with the dark set named and
   counted rather than hidden.
3. `morphology-attestation-audit` (A3, the absorbed prerequisite) exists as a
   manifest row and release.
4. A web surface at `/concordance/panini/` is live on the interim host, with the
   D4 static-head/SSR-tail split applied and the budget re-measured.
5. The four hygiene defects (D6, D8, D9, D11) are closed, and the standing rules
   they produced are recorded where the next session will read them.

---

_Dr. Mārcis Gasūns_
