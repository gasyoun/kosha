# Data statement — grammar-lab-derivation-gaps

_Created: 19-09-2026 · Last updated: 19-09-2026_

Data statement for the H4795 join of SanskritGrammar `grammar-lab-g1` topic
graph × kosha `panini-derivation-status` by root/lemma. Manifest:
[`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
`id: grammar-lab-derivation-gaps`. Not a release asset (analysis table).

## Composition & counts

32 rows (one per g1 topic), columns: topic · title_ru · cluster · roots ·
verbal_rows · ok · ambiguous · engine_error · no_derivation · fail_weight ·
root_class · missing_roots. Full method, headline findings and caveats:
[`data/concordance/GRAMMAR_LAB_VIDYUT_GAPS_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/GRAMMAR_LAB_VIDYUT_GAPS_REPORT.md).

## Source provenance

[`scripts/grammar_lab_vidyut_gaps.py`](https://github.com/gasyoun/kosha/blob/main/scripts/grammar_lab_vidyut_gaps.py)
(read-only join over `derivation_status.tsv` + `lemma_frequency.tsv` + the
SanskritGrammar grammar_lab export + the VisualDCS M9 class lists, IAST→SLP1
via `src/kosha/transliterate.py`). No network (R12).

## Known biases & limitations

- One whitney-root exemplar per g1 topic — the topic ranking double-counts
  roots shared by several topics (de-duplicated in the report).
- `not-in-dcs-class-list` rows = absent from the 443-root M9 lists, not
  classless.
- `fail_weight` is a frequency ranking signal (exact-form match with root
  fallback), not a corpus total.

## License

CC BY-SA 4.0 — same composition tier as `panini-derivation-status`
(vidyut MIT + DCS CC BY 4.0 attribution inherited through the join).

## Deprecation status

`active`.

_Гасунс_
