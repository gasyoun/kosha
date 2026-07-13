# Data statement — Gītā gold (word-by-word analysis)

_Created: 13-07-2026 · Last updated: 13-07-2026_

**Dataset:** `gita-gold-master` — a word-by-word grammatical + lexical analysis of
the **whole Bhagavadgītā** (all 18 adhyāyas), one row per analysed word.

**Vendored file:** [`data/gita/gita_gold_master.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_gold_master.tsv)
(regenerate with [`scripts/extract_gita_master.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_master.py)).

**Upstream source.** The hand-curated workbook `SanskritGrammar/Concordance/Gita.xlsm`
(`Combined` sheet — the author's clean, column-labelled master). The workbook is a
local-only working artifact (not git-committed); this TSV vendors its `Combined`
sheet verbatim so kosha is self-contained.

**Author / credit.** The grammatical analysis, lemmatisation, morphology and
glosses are the scholarly work of **Dr. Mārcis Gasūns** (with any additional
contributors to `Gita.xlsm` to be named on confirmation). Cite as the author's
Bhagavadgītā word-analysis; this repository ships the derived tabular extract.

**License.** **MIT** (per MG, 13-07-2026). Public tier — cleared to ship publicly.

**Fields (per word).** `verse · lemma · devanagari · iast · form_type · code ·
tense · pada · vclass · root · root_tr · prefix · stem_end · gender · compound ·
mark · rule · sandhi · verse_iast · gloss_en · gloss_ru`.

**Deliberate omission.** The workbook's Russian **transliteration** column uses a
private-use font encoding (non-portable byte junk); per MG it is **dropped**. The
Russian **gloss** column (`gloss_ru`, clean Cyrillic) is retained.

**Coverage / caveats.**
- All 18 adhyāyas; **9,092 analysed words** (per-chapter counts range 248–984).
- **Recension:** the workbook follows a vulgate numbering (chapter 1 = 47 verses);
  record this before citing verse numbers against a critical edition.
- Morphology `code`/`tense` values decode via the workbook's `Encode` /
  `Abbreviations` sheets (roadmap W3/W7); shipped here as-is.

**Consumers.** kosha Gītā reading packs (all 18 adhyāyas), the sandhi /
morphology / root-preverb datasets, and the E1 inflection-engine QA — see
[`ROADMAP_GITA_GOLD_EXTRACTION_2026.md`](https://github.com/gasyoun/kosha/blob/main/ROADMAP_GITA_GOLD_EXTRACTION_2026.md).

**Reuse as a template.** Per MG, the workbook's per-word analysis method is a
**template for other texts** — future gold packs can follow the same
`Combined`-sheet → vendored-TSV → reader/datasets pipeline.

_Dr. Mārcis Gasūns_
