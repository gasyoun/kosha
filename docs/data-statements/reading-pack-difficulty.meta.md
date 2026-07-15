# Data statement — reading-pack difficulty scorer (W2a)

_Created: 15-07-2026 · Last updated: 15-07-2026_

**Datasets:** `reading-pack-difficulty` (the scored ordering) + `morph-signature-freq`
(the DCS morphological-form frequency signal it consumes), plus four new reading packs
(`dcs-reading-pack-nala-2`, `-nala-3`, `-hitopadesa-0`, `-kiratarjuniya-1`).

**Vendored files.**
[`data/difficulty/reading_pack_difficulty.tsv`](https://github.com/gasyoun/kosha/blob/main/data/difficulty/reading_pack_difficulty.tsv)
(+ `.json`), [`data/difficulty/morph_signature_freq.tsv`](https://github.com/gasyoun/kosha/blob/main/data/difficulty/morph_signature_freq.tsv),
[`data/difficulty/difficulty_weights.json`](https://github.com/gasyoun/kosha/blob/main/data/difficulty/difficulty_weights.json),
[`data/difficulty/METHODS.md`](https://github.com/gasyoun/kosha/blob/main/data/difficulty/METHODS.md),
and the graded page [`reading/difficulty/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/difficulty/index.html).
Regenerate: `python scripts/build_difficulty_signals.py` (once, needs the DCS DB) then
`python scripts/build_difficulty_scorer.py`.

**What it is.** A **text-difficulty scorer** (the field §3.4/§6 gap) that scores every
UD-annotated kosha reading pack on four corpus-grounded axes and orders them into a
graded reading sequence:

    difficulty = w_vocab·VOCAB + w_sandhi·SANDHI + w_morph·MORPH + w_compound·COMPOUND

- **VOCAB** — mean corpus-rarity of content lemmas (from `lemma_frequency.tsv`, the W1b signal).
- **SANDHI** — fraction of word-boundaries fused by sandhi, measured off the pack.
- **MORPH** — mean surprisal of each token's `upos|morph` form over the 840 corpus signatures.
- **COMPOUND** — share of tokens that are compound members (DCS `feat_case=Cpd`).

**This is ONE estimator, not "the" difficulty.** The weighting is a modelling choice
(VERIFICATION R5); the weights are tunable in `difficulty_weights.json` and **a human
should confirm** them. Defaults: vocab 0.40 · sandhi 0.20 · morphology 0.25 · compound 0.15.

**Honest limitations.** Frequency ≠ learnability (R6): this measures *text properties*,
not measured learning gain. Sandhi is a boundary-fusion proxy, not induced-rule density.
Ordering is relative to the packs scored. Packs without UD morphology (the 18 Gītā packs,
built from a non-UD source) are **skipped, not fabricated into a score**.

**Validation anchor.** On the 5 scored packs, Bhāravi's *Kirātārjunīya* (dense classical
kāvya) scores hardest (0.389) and the three Nala epic-narrative chapters + the Hitopadeśa
opening cluster near 0.32 — the expected register gradient, driven by the vocab and
compound axes.

**Author / credit.** Scorer design + build: **Dr. Mārcis Gasūns** (H949, Opus 4.8
`claude-opus-4-8[1m]`).

**License / rights.** Public tier, **MIT** pedagogy layer. Source corpus is the Digital
Corpus of Sanskrit (**CC BY 4.0**, Oliver Hellwig / DCS) — attribute DCS on any public
deck; a `/publish-safety-check` + `/data-release` gate applies before public distribution
(VERIFICATION R8).

_Dr. Mārcis Gasūns_
