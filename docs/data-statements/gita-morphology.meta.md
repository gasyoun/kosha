# Data statement — Gītā morphology + compound gold

_Created: 13-07-2026 · Last updated: 13-07-2026_

**Dataset:** `gita-morphology-gold` — every analysed word of the Bhagavadgītā
tagged with structured morphology (case·number·gender for nominals;
person·number·tense·voice for finite verbs; non-finite / derivation tags) and
its **compound type** (tatpuruṣa / bahuvrīhi / dvandva / karmadhāraya).

**Vendored file:** [`data/gita/gita_morphology_gold.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_morphology_gold.tsv)
(regenerate: [`scripts/extract_gita_morphology.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_morphology.py)).

**Method.** The `Grammar` sheet of `SanskritGrammar/Concordance/Gita.xlsm` carries
a hand-curated morphology shorthand per word (col AB, e.g. `1n.1 m.` = nom. sg.
masc.; `Perf. P 1v.1` = perfect, parasmaipada, 3rd sg.). This dataset **decodes**
that shorthand into explicit fields using the workbook's own `Abbreviations`
legend — reproduced verbatim in the extractor's decode maps (`1–8 n` = the eight
cases; `1–3 v` = 3rd/2nd/1st person; tense/mood, voice P/Ā, derivation
caus./des./pass., participles PP/PPr/PF, gender, compound TP/BV/DV/KD).

**Fields.** `verse · widx · form · lemma · root · pos · case · number · gender ·
person · tense · voice · nonfinite · derivation · compound · raw_morph`
(`raw_morph` preserves the original shorthand for audit).

**License.** **MIT**; public. Credit **Dr. Mārcis Gasūns** (the analysis is the
author's; co-authors TBC).

**Provenance / relation.** Derives from the same workbook as the W0 master
[`gita-gold`](gita-gold.meta.md); roadmap **W3**
([`ROADMAP_GITA_GOLD_EXTRACTION_2026.md`](https://github.com/gasyoun/kosha/blob/main/ROADMAP_GITA_GOLD_EXTRACTION_2026.md)).

**Consumer.** The inflection-engine QA workstream **W4**
([H874](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H874-Opus_kosha_gita_inflection_engine_qa_13.07.26.md))
— the gold case·number·gender here is cross-checked against kosha's Cologne+vidyut
hybrid `inflections`/`forms` as the first attested-corpus test of the E1 layer.

**Caveats.** The shorthand parse is faithful to the `Abbreviations` legend; a
handful of rare/compound tags may leave a field blank (`raw_morph` always holds
the source). Recension: vulgate numbering (see the W0 data statement).

_Dr. Mārcis Gasūns_
