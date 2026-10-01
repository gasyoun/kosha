# Data statement — Zaliznyak -ant/-at oddball drills (`zaliznyak-oddbank-drills`)

_Created: 15-09-2026 · Last updated: 15-09-2026_

Data statement for the `zaliznyak-oddbank-drills` dataset. Manifest row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
Committed assets:
[`data/zaliznyak/zaliznyak_oddbank_drills.json`](https://github.com/gasyoun/kosha/blob/main/data/zaliznyak/zaliznyak_oddbank_drills.json)
+ `.tsv` flat fallback. Built by
[`scripts/build_zaliznyak_oddbank_drills.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_zaliznyak_oddbank_drills.py)
(H4730).

## Composition & counts

1,722 multiple-choice items over the 2,159 -ant/-at pooled-class lemma rows of
the kosha-registered verdict banks `dcs-nominal-class-split` (NOUN, 279 rows,
H3984) and `dcs-nominal-class-split-adj` (ADJ, 1,880 rows, H4011). The 695
`unresolved` verdict rows are excluded — no teachable verdict, never guessed.

| Field | Content |
|---|---|
| `id` | `ZOD-####` |
| `type` | `classify-verdict` (1,464 — one per resolved verdict row) or `odd-one-out` (258 — 3 alternants + 1 oddball) |
| `question` / `answer` / `choices` | 4-way MCQ; words render Devanāgarī + IAST |
| `verdict_refs` | per-choice `{source_dataset, lemma_id, lemma, verdict}` — 1:1 traceability into the verdict banks |
| `source_dataset`, `tags` | provenance + facet tags |

The pedagogic question: words that **look** like -ant/-at present participles
but whose MW+PWG verdict says the -ant/-at pair is (or is not) ONE lexeme with
two stem spellings. `odd-one-out` spots the word that does NOT alternate
(`at_only`/`ant_only` oddballs vs `one_lexeme_two_spellings` alternants);
`classify-verdict` drills the verdict itself (e.g. bhagavant/bhagavat →
one lexeme, two spellings).

## Source provenance

Derived in [gasyoun/kosha](https://github.com/gasyoun/kosha) by reading, at
build time only (never vendored), the tracked VisualDCS verdict files
`visual/paradigm_nominal_class_split.json` and
`visual/paradigm_nominal_class_split_adj.json` (H3984/H4011). No new lexical
claims are made: every answer IS the source verdict row.

## Verifiability

`python3 scripts/build_zaliznyak_oddbank_drills.py --check` re-resolves every
`verdict_refs` entry against the live source JSONs (lemma_id + lemma +
verdict must match) and validates id uniqueness, choice uniqueness and
answer-in-choices. A drill item that no longer traces to its verdict row is a
build failure, not a diff to accept.

## Known biases & limitations

- **Verdict-scoped, not form-scoped:** items test dictionary adjudication of
  the -ant/-at lemma pair, not corpus-attested inflected forms (contrast
  morphology-drills / H1296).
- **Distractor pairing is frequency-nearest, not sense-matched:** odd-one-out
  distractors are the (tokens-desc, lemma_id-asc) neighbours of the oddball in
  the same verdict bank; no semantic confusability control.
- **Unresolved majority:** 695 of 2,159 rows (mostly productive -vat/-mat
  formations and hapaxes, per H4011's residual note) carry no dictionary
  witness and are absent from the bank by design.
- **PWG+MW epistemology inherited:** verdicts are entry-id-set comparisons
  (H3984/H4011 signal B), so 19th-century lexicographic gaps propagate as
  `at_only`/`ant_only` verdicts, not as errors.

## Intended use / known misuse

**For:** oddball practice inside the zaliznyak declension-class programme —
when a -ant/-at-looking word does not decline like a participle.
**Misuse:** reading an `at_only` verdict as "the -ant form does not exist"
(it means the dictionaries unite no -ant/-at pair under one entry-id set).

## License

Source verdicts CC BY-SA 4.0 (VisualDCS); this derived asset follows kosha's
public-tier terms ([LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md));
builder code public/MIT.

## Maintenance & sunset plan

Rebuild by re-running the builder whenever H3984/H4011 regen the verdict
files; `--check` is the regression gate. Sunset: superseded in place.

## Deprecation status

`active`.

## Provenance of this statement

Authored 15-09-2026 by OxAlpha (`opencode/z-ai/glm-5.3-flash`) under handoff
[H4730](https://github.com/gasyoun/Uprava/blob/main/handoffs/H4730-OxAlpha_SanskritGrammar_xwalk-c3-classsplit-zaliznyak-drills_14.09.26.md).

_Гасунс_
