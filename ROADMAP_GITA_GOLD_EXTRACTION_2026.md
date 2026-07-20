# Roadmap — Gītā gold source (`Gita.xlsm`) extraction & consumption

_Created: 13-07-2026 · Last updated: 13-07-2026_

Scope decisions locked with MG (13-07-2026 interview): **home = kosha**;
**vendor + cite** `Gita.xlsm` as a canonical source (credit the author);
extract **all** layers (18-adhyāya reader · sandhi · morphology+compound ·
Russian+etymology); and **inflection-engine QA is a committed workstream**, not
a nice-to-have.

> **Status (13-07-2026): the roadmap is COMPLETE — all of W0–W6 shipped.** W0 master (v0.26.0) · W1 reader-all-18 (v0.29.0) · W2 sandhi (v0.30.0) · W3 morphology+compound (v0.27.0) · W4 inflection-engine QA (v0.28.0) · W5 Russian+etymology (v0.31.0) · W6 upasarga semantics (v0.32.0). Follow-ups noted inline (gold recension check · the W4 pronoun-corrections `@DO`).

## 1. Context

The Bhagavadgītā is absent from the DCS gold corpus, so kosha's Gītā reading
pack ([H848](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H848-Sonnet_kosha_dcs_reading_packs_nala_gita_13.07.26.md),
[v0.25.0](https://github.com/gasyoun/kosha/releases/tag/v0.25.0)) was rebuilt
GOLD from **`SanskritGrammar/Concordance/Gita.xlsm`** — a hand-curated,
word-by-word analysis of the **whole Gītā**. Only chapter 1 (569 words) and only
the reader slice (form·lemma·root·morph·English gloss) have been consumed so far.
This roadmap covers the rest.

**The source is far richer than the pilot used.** `Gita.xlsm` carries **9,091
analysed words across all 18 adhyāyas**, and the **`Combined` sheet** is a clean,
24-column labelled master that is the single canonical export everything below
derives from:

| Combined col | field | example |
|---|---|---|
| A | Verse ref | `1.01` |
| D | lemma ("Original form") | `dhṛta-rāṣṭra` |
| E / F | Devanagari / Roman | `धृतराष्ट्रः` / `dhṛtarāṣṭraḥ` |
| G / X | Russian translit / **Russian gloss** | (font-encoded) / `царь Дхритараштра` |
| H / I / J | Form · Code · Tense | `nam` · `11` · `ppp` |
| K / L | P/A (pada) · verb class | |
| M / N | **Root · Root-translation** | `√dhṛ` · `to hold` |
| O / P / Q | Prefix · stem-End · **Gender** | `a` · `m` |
| R / S | **Compound type** · Mark | `BV` (bahuvrīhi) |
| T / U | Rule · **Sandhi transform** | `h1` · `ḥ u → Ø u` |
| V / W | verse IAST · **English gloss** | `by whom the kingdom is held` |

Supporting sheets: **`Grammar`** (the same, plus an **etymology-notes** column
`traditionally: pu-tra…` the Combined sheet drops), **`verbs`** (root +
preverb-modified senses), **`sandhi`** (45-rule frequency catalog), **`Encode`**
/ **`Tenses`** (morphology-code decoder + derivation-type stats),
**`Abbreviations`** (the `1n.1 = nom. sg.` legend), **`Prose`** (interlinear
paraphrase), **`Vocabulary`** (thematic word-families), **`Devanagari`** (701
verse-level Devanagari), **`BhagavadGītā`** (verse-count + word-address index).

**Caveat carried into every workstream:** `Gita.xlsm` is **not git-committed**
in SanskritGrammar (only `catalog.mdx` is) — so kosha must **vendor** the
extracted data (as W0 does) rather than read the workbook at build time.

## 2. Foundation

### W0 — Vendor the canonical master dataset ✅ DONE (13-07-2026)
Shipped: [`data/gita/gita_gold_master.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_gold_master.tsv)
(**9,092 words · 18 adhyāyas · 21 fields**) via
[`scripts/extract_gita_master.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_gita_master.py);
registered public/MIT in the manifest + data statement
[`docs/data-statements/gita-gold.meta.md`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/gita-gold.meta.md).
Everything below reads this file. _Original plan:_ extract the **full `Combined` sheet** (9,091 words × 18 adhyāyas × 24 fields,
+ the `Grammar` etymology-notes column) into a committed kosha dataset
`data/gita/gita_gold.tsv` (+ per-chapter JSON), generalising the ch-1 pilot
``scripts/extract_gita_gold.py``
(add `--sheet Combined --all-chapters`). Register it as a **citable dataset**:
kosha [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
row + a `docs/data-statements/gita-gold.meta.md` crediting the author +
[Uprava/DATA_LAYERS_CENSUS.md](https://github.com/gasyoun/Uprava/blob/main/DATA_LAYERS_CENSUS.md).
Every workstream below reads this vendored file, not the xlsm.
- Effort: **S–M** · gated on: nothing (pipeline proven on ch1).

## 3. Reader & linguistic-layer workstreams _(parallel after W0)_

### W1 — Full 18-adhyāya reader
Loop the gold reader build over all chapters → 18 packs + chapter/verse
navigation in [`reading/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/index.html)
(the ch-1 machinery already exists; this is mostly a loop + nav UI).
- Output: `reading/data/gita-{1..18}.js` + a chapter picker. Effort: **S**.

### W2 — Sandhi layer
Per-word sandhi transform (`Combined.Sandhi`, e.g. `ḥ u → Ø u`) + the 45-rule
**frequency catalog** (`sandhi` sheet) → a `gita-sandhi` dataset **and** a reader
affordance (hover a word → the sandhi rule that produced its surface form). A
genuine sandhi-teaching asset — the first corpus-attested, frequency-ranked
sandhi table in the ecosystem.
- Output: dataset + reader tooltip + a sandhi-rules page. Effort: **M**.

### W3 — Morphology + compound gold
`Combined` Form/Code/Tense/pada/End/Gender/**Cpd** decoded via the `Encode` +
`Abbreviations` sheets → a **gold morphology + samāsa-type dataset**: every word
tagged case·number·gender / tense·voice·person and every compound tagged
TP/BV/DV/KD… A reusable annotation layer + the input to W4.
- Output: `gita-morphology-gold` dataset. Effort: **M** (the code-decode is the work).

### W4 — Inflection-engine QA (E1 tie-in) _(gated on W3)_
Cross-check every Gītā word's **gold** case·number·gender against kosha's
`inflections`/`forms` (the Cologne + vidyut **hybrid** layer, [H185](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md)):
a **real-text gold evaluation** for E1 — agreement %, a divergence ledger
(where kosha's paradigm disagrees with an attested Gītā form), and candidate
`disputed=1` / gap-fill corrections. This is the first attested-corpus check of
the hybrid forms layer, complementing the synthetic
[E1_DIVERGENCE_REPORT.md](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md).
- Output: `GITA_MORPHOLOGY_QA_REPORT.md` + a corrections feed. Effort: **M–L**.

### W5 — Russian + etymology layer
`Combined.Russian` gloss + `Grammar` **etymology notes** + `Combined.Root-Tr`
(root translations) → an **RU reading layer** (kosha's Russian surface) + an
**etymology asset**. Ties to [RussianTranslation](https://github.com/gasyoun/SanskritLexicography/tree/master/RussianTranslation).
- **Risk:** the Russian *transliteration* column (`Combined.G` / `Grammar.F`)
  uses a **private-use font encoding** (`…`) — needs a transcode map or
  must be dropped; the Russian *gloss* column (`X`/`G`) is clean Cyrillic and is
  the usable one. Effort: **M**.

### W6 — Root & preverb semantics ✅ DONE (v0.32.0)
The `verbs` sheet (root + **preverb-modified senses** — √vac→speak, pra-√vac→
declare, sam-ni-√as→renounce) + `Combined.Root/Root-Tr` → an **upasarga-semantics
lexical dataset** feeding the `/w/` cards (a dimension kosha's dictionaries thin on).
- Output: `sanskrit-upasarga-semantics` dataset. Effort: **S–M**.

## 4. "What remains" — residual assets (W7, opportunistic)
Enumerated so nothing in the workbook is silently dropped:
- **`Encode` (~1M rows)** — the morphology-code → analysis **decoder**; not a
  standalone deliverable but the **key that unlocks W3** (decodes `Code`/`Tense`).
- **`Tenses` (~1M rows)** — derivation-type **frequency reference** (Praes 567,
  Imperat 108, caus./denom./pass. counts) + ending tables → a verb-morphology stats sidecar.
- **`Abbreviations`** — the notation **legend**; vendor as the human key for W3.
- **`Prose` (2,071)** — running **interlinear paraphrase** → an alternate
  "prose gloss" reading view (a second display mode in the reader).
- **`Vocabulary` (239)** — thematic **semantic-field families** (bhava/bhāva/…)
  → a semantic-domain asset (cf. the A58 semdom↔Amarakosha work).
- **`BhagavadGītā` sheet** — verse-count + **word-address index** (`ch.verse.word`)
  → concordance/citation metadata; a frequency concordance of the Gītā is derivable.
- **`Devanagari` (701)** — verse-level Devanagari (already partly used per-word in W0).

## 5. Sequencing & dependencies
```
W0 (master dataset) ──┬─ W1 reader (18 ch)
                      ├─ W2 sandhi
                      ├─ W3 morphology+compound ── W4 inflection QA
                      ├─ W5 Russian+etymology
                      └─ W6 root/preverb semantics
W7 (Encode/Abbrev decoders) feeds W3; other W7 items are independent.
```
W0 first (single extraction, everything derives). W1/W2/W3/W5/W6 parallel. W4
after W3. Mint each as its own `H###` at kickoff (see the metadoc backlog).

## 6. Provenance, citation & rights
- **Credit the author** of `Gita.xlsm` (the hand analysis is substantial scholarly
  work) in the data statement + manifest `notes` + CITATION where the derived
  datasets are released.
- **Not-committed source:** vendor the extracted TSV/JSON into kosha; keep a note
  that the upstream is the local `SanskritGrammar/Concordance/Gita.xlsm`.
- **Recension:** the pilot ch-1 had 47 verses (vulgate) vs GRETIL's 46 — record
  which Gītā recension the workbook follows before citing verse numbers.
- **License / public-tier:** confirm the derived datasets may ship public tier
  (the gloss/analysis is the author's) before any release.

## 7. Decisions (MG, 13-07-2026 — all resolved)
1. Russian **transliteration** font-encoding → **dropped** (garbled private-use bytes); the clean Cyrillic **gloss** is kept.
2. License → **MIT**; credit **Dr. Mārcis Gasūns** (co-authors of `Gita.xlsm` TBC on confirmation).
3. The `gita_gold` master → **ship public** (citable; Zenodo-DOI at a data release).
4. The workbook's method → **yes, a template for other texts** (a reusable gold-pack pipeline).

_Dr. Mārcis Gasūns_
