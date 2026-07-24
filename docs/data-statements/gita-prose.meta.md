# Data statement — Gītā interlinear prose paraphrase

_Created: 24-07-2026 · Last updated: 24-07-2026_

**Dataset:** `gita-prose` — running interlinear paraphrase of the Bhagavadgītā
(form + parenthetical gloss), one row per prose *block* (a verse or verse-range).

**Vendored file:** [`data/gita/gita_prose.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_prose.tsv)
(regenerate: [`scripts/extract_gita_prose.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_prose.py)).
JS shard for the reader: [`reading/data/gita_prose.js`](https://github.com/gasyoun/kosha/blob/main/reading/data/gita_prose.js).

**Upstream source.** The hand-curated workbook
`SanskritGrammar/Concordance/Gita.xlsm`, **`Prose` sheet** (2,071 lines → 653
blocks after grouping continuation rows). The workbook is a local-only working
artifact (not git-committed in SanskritGrammar); this TSV vendors the Prose
sheet so kosha is self-contained.

**Author / credit.** Interlinear paraphrase is the scholarly work of
**Dr. Mārcis Gasūns** (same authorship as the Combined-sheet word analysis). Cite
as the author's Bhagavadgītā interlinear prose; this repository ships the
derived tabular extract.

**License.** **MIT** (same public-tier ruling as `gita-gold-master`, MG 13-07-2026).

**Fields (per block).**

| Column | Content |
|---|---|
| `verse_label` | Sheet label — single (`1.12`) or range (`1.4-6`, `1.15-16`) |
| `verse_keys` | Pipe-joined expanded keys (`1.4\|1.5\|1.6`) for join to reader verses |
| `n_lines` | Number of Prose-sheet rows folded into this block |
| `text` | Joined interlinear text (NBSP normalised to space) |

**Relation to word-by-word gold.** This is a **display-mode sidecar**, not a
replacement for [`gita_gold_master.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_gold_master.tsv).
The reader (`reading/index.html`) keeps word-by-word as default and offers a
**Prose** toggle (H1493) when `window.GITA_PROSE` has a match for the verse.

**Coverage / caveats.**

- 653 blocks covering **703** expanded verse keys (ranges expand).
- Recension: same vulgate numbering as the Combined sheet (chapter 1 = 47 verses).
- Prose blocks may span multiple ślokas; the reader de-duplicates identical range
  text so a 1.4–6 block is not reprinted three times.

**Consumers.** kosha Gītā reading packs Prose view (`reading/index.html`).

_Dr. Mārcis Gasūns_
