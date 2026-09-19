# Data statement — amarakosa-mw-pwg-sense-crosswalk

_Created: 19-09-2026 · Last updated: 19-09-2026_

Data statement for the H4806 structural join of Amarakośa varga/synsets (H4746
AK lemma layer, consumed as-is) × MW/PWG sense units (csl-orig Cologne `<L>`
records) by exact SLP1 lemma key. Manifest:
[`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
`id: amarakosa-mw-pwg-sense-crosswalk`. Not a release asset (analysis table).

## Composition & counts

Synset table 5,590 rows (`data/xwalk/ak_synset_mw_pwg_senses.tsv`): varga ·
eid · n_members · n_lemmas_distinct · mw_lemmas_covered · mw_sense_units ·
pwg_lemmas_covered · pwg_sense_units · total_sense_units. Lemma detail 14,036
rows (`ak_lemma_mw_pwg_senses.tsv`). Stats sidecar
(`ak_synset_dict_senses_stats.json`). Full method + findings:
[`docs/AK_SYNSET_MW_PWG_SENSES_H4806_19.09.26.md`](https://github.com/gasyoun/kosha/blob/main/docs/AK_SYNSET_MW_PWG_SENSES_H4806_19.09.26.md).

## Source provenance

[`scripts/ak_synset_dict_senses.py`](https://github.com/gasyoun/kosha/blob/main/scripts/ak_synset_dict_senses.py)
(read-only over SanskritLexicography `data/ak_lemma_cdsl_crosswalk.tsv` +
csl-orig `v02/mw/mw.txt` + `v02/pwg/pwg.txt`; no network). Selftest: 30-synset
seed-42 sample re-verified via independent line-scan, PASS + 3 canaries.

## Known biases & limitations

- Measure = coverage/split envelope: units-per-synset conflates semantic
  split with member-lemma polysemy/homonymy and proper-noun entry mass
  (Śiva/Kṛṣṇa lead the 11+ bucket).
- Exact-key only; H4746 union misses (449 distinct) contribute zero units and
  are never promoted — zero false joins by design.
- NOT a sense alignment: no gloss text is read or emitted (language fence,
  sense-alignment-pilot trap); candidate-generator axis only.

## License

CC BY-SA 4.0 — keys + counts only (facts), no AK prose, no dictionary gloss
text redistributed.

## Deprecation status

`active`.

_Гасунс_
