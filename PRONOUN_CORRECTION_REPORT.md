# Pronoun-paradigm correction — closing the W4 QA finding

_Created: 13-07-2026 · Last updated: 13-07-2026_

The Gītā inflection-engine QA (H874,
[`GITA_MORPHOLOGY_QA_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/GITA_MORPHOLOGY_QA_REPORT.md))
found that kosha's Cologne+vidyut hybrid `inflections` layer **mis-models Sanskrit
pronouns**: **71 % of the 360 divergences were pronoun forms** (`asmākam`, `me`,
`idam`, `ye`, `te` …) left untagged (`None.None.None`) or given a wrong cell. MG
ruled: **do the correction** (a curated pronoun layer, not just a `disputed` flag).

## What was done

[`scripts/build_pronoun_corrections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_pronoun_corrections.py)
takes the **GOLD attested pronoun analyses** from the Gītā
([`data/gita/gita_morphology_gold.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_morphology_gold.tsv),
`pos=pronoun`) — **208 distinct (form · lemma · case · number · gender) analyses**
over the core sarvanāman (asmad, yuṣmad, tad, etad, yat, idam, kim …) — and:

1. emits the committed correction set
   [`data/gita/pronoun_corrections.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/pronoun_corrections.tsv);
2. inserts them into `inflections` as **`source='curated-gita-pronoun'`** rows
   (`INSERT OR IGNORE`; non-destructive — nothing Cologne is overwritten). **153
   new rows** were added (55 analyses Cologne already held).

Wired as **`build_db.py --stage pronoun`** so a full DB rebuild re-applies it —
avoiding the regress-on-rebuild trap the H345 heritage table hit.

## Result — re-running the QA on the corrected engine

| metric | before | after | Δ |
|---|--:|--:|--:|
| **AGREE** (attested cell in the paradigm) | 4,779 = **93.0 %** | 5,397 = **98.7 %** | **+5.7 pts** |
| **DIVERGE** (wrong/absent cell) | 360 | **73** | −287 |
| **GAP** (form absent) | 919 | **588** | −331 |

The pronoun divergences the QA flagged are largely closed; residual DIVERGE (73)
and GAP (588) are now dominated by long **compounds**, not pronouns — a
compound-splitter (vidyut-cheda) is the next lever, not a paradigm fix.

## Scope & honesty

- **Attested-forms correction:** covers the pronoun forms attested in the Gītā,
  not every cell of every pronoun paradigm — a data-driven fix from real usage.
  Generating full pronoun paradigms is a further enhancement.
- **Non-destructive:** wrong Cologne pronoun rows still exist alongside the curated
  correct ones (the QA is set-membership, so agreement rises regardless).
- Public/MIT, credit Dr. Mārcis Gasūns (the gold analyses).

## Phase 2 — flagging the wrong Cologne rows `disputed=1`

The same `--stage pronoun` step then marks the wrong Cologne pronoun rows
`disputed=1` — a **review flag** (the mechanism E1 already uses for pronominal
forks), never a deletion. Scoped to the exact `(form_slp1, lemma_slp1)` pairs the
gold attests: a Cologne row is flagged when its case is **untagged (NULL)** or its
**(case, number)** is **not gold-attested** for that form+lemma (gender is
ignored to avoid flagging gender-ambiguous valid rows).

Of the 161 Cologne rows over the gold pronoun (form,lemma) pairs:

| | count |
|---|--:|
| gold-consistent (left untouched) | 79 |
| already `disputed` (from E1) | 9 |
| **newly flagged `disputed=1`** | **73** |

10 pronoun lemmas touched (sarva, etad, idam, kim, anya, eka, ubha, sva, pūrva,
sama). Some flags may be valid non-attested cells → that is exactly what
`disputed` (editorial review) is for; nothing is removed.

> **Applied on a full DB read.** The shared `kosha.db` was under a concurrent
> rebuild this session (the flag is reset by `--stage inflections`' repopulate);
> because phase 2 is part of the idempotent `--stage pronoun`, a clean rebuild
> re-applies it deterministically.

_Dr. Mārcis Gasūns_
