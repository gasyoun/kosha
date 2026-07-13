# Data statement — curated pronoun corrections

_Created: 13-07-2026 · Last updated: 13-07-2026_

**Dataset:** `pronoun-corrections` — curated correct analyses for Sanskrit pronoun
(sarvanāman) forms, applied to kosha's inflection layer to fix the pronominal
mis-modelling the W4 QA (H874) found.

**Vendored file:** [`data/gita/pronoun_corrections.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/pronoun_corrections.tsv)
(regenerate / apply: [`scripts/build_pronoun_corrections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_pronoun_corrections.py),
or `scripts/build_db.py --stage pronoun`).

**Source.** The GOLD attested pronoun analyses of the Bhagavadgītā
([`data/gita/gita_morphology_gold.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_morphology_gold.tsv),
`pos=pronoun`) — **208 distinct (form · lemma · case · number · gender)** over the
core pronouns (asmad, yuṣmad, tad, etad, yat, idam, kim, sarva, anya …).

**Fields.** `form_slp1 · lemma_slp1 · gcase · number · gender · source`
(`source='curated-gita-pronoun'`).

**How it is applied.** A `build_db.py --stage pronoun` step inserts these into
`inflections` as `source='curated-gita-pronoun'` rows (`INSERT OR IGNORE`,
idempotent, **non-destructive** — no Cologne row is overwritten). Wired as a
stage so a full rebuild re-applies it (the H345 regress-on-rebuild lesson).

**Effect (measured on a stable DB).** Re-running the W4 QA: nominal agreement
**93.0 % → 98.7 %**, divergences **360 → 73**, gaps **919 → 588** — see
[`PRONOUN_CORRECTION_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/PRONOUN_CORRECTION_REPORT.md).

**Scope.** Attested Gītā pronoun forms, not every paradigm cell; wrong Cologne
rows remain alongside the curated correct ones (flagging them `disputed` is a
further step). **License MIT**; public. Credit **Dr. Mārcis Gasūns**.

_Dr. Mārcis Gasūns_
