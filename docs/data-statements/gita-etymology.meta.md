# Data statement — Gītā etymology notes

_Created: 13-07-2026 · Last updated: 13-07-2026_

**Dataset:** `gita-etymology` — the hand-written etymological / explanatory notes
attached to selected Bhagavadgītā words (e.g. `putra – one who saves from hell`;
`uttama – uppermost, superlative of ud`).

**Vendored file:** [`data/gita/gita_etymology.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_etymology.tsv)
(regenerate: [`scripts/extract_gita_etymology.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_etymology.py)).

**Source.** The `Grammar` sheet of `SanskritGrammar/Concordance/Gita.xlsm`,
column AG — a column the `Combined` master (W0) drops. Aligned to each word by
`(verse, word-index)`.

**Fields.** `verse · widx · form · lemma · root · etymology`.

**Coverage.** **101 notes** (sparse by design — only where the author annotated an
etymology). Not every word has one; this is a curated highlight layer, not a full
etymological dictionary.

**License.** **MIT**; public. Credit **Dr. Mārcis Gasūns**.

**Relation.** Roadmap **W5**, alongside the Russian gloss layer (the master's
`gloss_ru`, now toggleable in the Gītā reader). Part of the Gītā-gold programme —
[`ROADMAP_GITA_GOLD_EXTRACTION_2026.md`](https://github.com/gasyoun/kosha/blob/main/ROADMAP_GITA_GOLD_EXTRACTION_2026.md).

_Dr. Mārcis Gasūns_
