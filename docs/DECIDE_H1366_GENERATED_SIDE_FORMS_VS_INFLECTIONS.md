# DECIDE (H1366) — which generated table is canonical for A4/W2a: `forms` vs `inflections`

_Created: 20-07-2026 · Last updated: 20-07-2026_

**Status: ✅ RULED 20-07-2026 — `forms` is canonical (accepted by MG).**
The recommendation below was accepted; the decision is recorded as kosha PLAN
[§2 `D13` + §3a](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md)
and [CONTRADICTIONS §3](https://github.com/gasyoun/SanskritLexicography/blob/master/CONTRADICTIONS.md)
has graduated to a ✅ tombstone. **W2a is unblocked to consume `forms`.** This file
is retained as the reasoned brief behind the ruling.

> **Why the agent briefed rather than ruled (pre-acceptance context).** W1b/A3
> ([H1262](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1262-Opus_kosha_a3_attested_form_join_morphology_audit_18.07.26.md))
> surfaced this as an explicit STOP-AND-SURFACE block and declared it had "no
> standing to settle it"; [H1366](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1366-Opus_kosha_generated-side-forms-vs-inflections-canonical-ruling_20.07.26.md)
> was scoped to **register + correct the mislabel + brief the choice**, not to rule.

---

## The question

The Concordance-Q3 plan set names two different `kosha.db` tables as the
"generated inflection side" of the A3→A4/W2a pipeline, and they are ~5× apart:

- the W1b deliverable text built on **`forms`** (1,378,401 rows);
- the ARCHITECTURE §1 diagram said **"6.9M generated"**, which is **`inflections`**
  (6,917,018 rows).

W2a (the derivation harness) consumes exactly this side as its denominator, so
the choice must be settled before W2a runs, or its coverage figures are silently
wrong.

## What the two tables actually are (measured 20-07-2026, Opus 4.8 `claude-opus-4-8`)

Queried directly against
`kosha.db` (gitignored local data file, not on GitHub)
(1.674 GB, gitignored; the canonical main clone's copy):

| | `forms` | `inflections` |
|---|---|---|
| rows | **1,378,401** | **6,917,018** |
| distinct `form_slp1` | 1,338,240 | 3,326,312 |
| columns | `form_slp1, lemma_slp1, source, category` | `form_slp1, lemma_slp1, model, gender, gcase, number, refs, source, person, tense, voice, disputed` |
| morphology (case/gender/number) | **none** — a form→lemma provenance index | model 100% · gender/case/number ~99% · person/tense/voice on 67,140 verb rows |
| `source` distribution | **heritage 951,991 · dcs 397,843 · vidyut 28,567** | `cologne_mwinflect` 6,916,522 · `hybrid-natva-fix` 326 · `curated-gita-pronoun` 153 · `vidyut-gap-fill` 17 |
| trust axis (`dcs > vidyut > heritage`, `include_heritage=False`) | **carries it** (the `source` column) | ~100% one engine — **cannot express it** |

**They are not two cardinalities of one dataset — they are different data
products.** On `(form_slp1, lemma_slp1)`:

- of the **426,410** non-heritage `forms` pairs, only **168,034 (39%)** also appear
  in `inflections`;
- `inflections` holds **3,246,914** `(form, lemma)` pairs that are **absent from
  `forms` entirely**.

So "pick the bigger/smaller of the same thing" is a false framing: `forms` is a
tri-source (dcs/vidyut/heritage) form↔lemma provenance map with a trust axis but
no morphology; `inflections` is the MW full-paradigm expansion (`cologne_mwinflect`)
with rich morphology but a single engine and no attestation/heritage split.

## Options

| Option | What A4/W2a would measure over | Consequence |
|---|---|---|
| **A. `forms` only** (recommended) | 426,410 non-heritage `forms` rows = the A3/W1b AG denominator | Continuous with A3; trust axis intact; W2a *generates* vidyut morphology, does not inherit another engine's. `inflections`'s 3.2M extra pairs are simply out of A4's stated scope (MW-only paradigm mass, mostly non-DCS-attested) |
| **B. `inflections` as a second generated side** | 6,917,018 rows | 5× the derivation work; no `source` trust split (heritage discipline unenforceable); silently mixes `cologne_mwinflect` morphology with vidyut-derived; A4 coverage becomes incommensurable with A3. R-Q1 storage projection worsens materially |
| **C. both, with separate denominators** | both, reported side-by-side | Honest but doubles the build and the reporting surface; only justified if a stakeholder wants an MW-paradigm coverage number *in addition to* the attestation-grounded one. Can be added later as a cross-check without blocking A4 |

## Recommendation — Option A (`forms`), high confidence

Three independent grounds, any one of which is sufficient:

1. **Pipeline continuity.** W2a's declared input is "each attested form **from
   W1b**"
   ([ROADMAP W2a](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026H2.md)),
   and W1b/A3 is defined over `forms` non-heritage (426,410 — the AG denominator,
   per the
   [morphology-attestation build report](https://github.com/gasyoun/kosha/blob/main/data/concordance/MORPHOLOGY_ATTESTATION_BUILD_REPORT.md)).
   Switching to `inflections` mid-pipeline orphans A3 and makes A4 coverage
   incommensurable with the join it stands on.
2. **Trust axis.** Only `forms` carries the `source` column
   (`dcs > vidyut > heritage`, `include_heritage=False` since H696) the trust
   discipline requires. `inflections` is ~100% one engine and cannot express it —
   adopting it silently drops the heritage guard the whole concordance rests on.
3. **Engine separation.** W2a *generates* morphology + the ordered sūtra chain via
   `vidyut.prakriya`. It must not silently inherit `cologne_mwinflect`'s
   morphology. The 168,034-pair overlap is a legitimate **cross-check** (does
   vidyut-derived `model`/`gcase` agree with `cologne_mwinflect`?), which is a
   *useful* future A4 validation step — but a cross-check is not a denominator.

**Confidence: high.** This is closer to a factual correction than a taste call:
the "5× apart, same side" premise dissolved on measurement (39% overlap, orthogonal
columns), so the two tables are not interchangeable candidates for one slot.

**`inflections` is not discarded** — it is reclassified as a distinct secondary
asset (the MW full-paradigm morphology table), available to A4 as the Option-A
cross-check and as its own future data-hub layer, never as the A4 generated
denominator.

## Accepted — done (20-07-2026)

1. ✅ Recorded as kosha PLAN §2 **`D13`** (settled) + §3a; this file flipped to ✅.
2. ✅ [CONTRADICTIONS §3](https://github.com/gasyoun/SanskritLexicography/blob/master/CONTRADICTIONS.md)
   graduated to a ✅ tombstone.
3. ✅ W2a unblocked — proceeds on the 426,410-row non-heritage `forms` AG set.

## Reproduce

Every figure re-derives from two `SELECT`s over
`kosha.db` (gitignored local data file, not on GitHub)
`forms` and `inflections` (schema, `source` `GROUP BY`, and an `INTERSECT`/`EXCEPT`
on `(form_slp1, lemma_slp1)`); no writeback, read-only.

---

_Dr. Mārcis Gasūns_
