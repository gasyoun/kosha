# Data statement — Śiva Sūtras / pratyāhāra table (machine-readable)

_Created: 10-09-2026 · Last updated: 10-09-2026_

**Dataset:** `shiva-sutras-machine` — Pāṇini's 14 Māheśvara Sūtras plus the 42
named pratyāhāras (phoneme abbreviations, e.g. `aK`, `aC`, `yaṆ`, `haL`) built
from them, as a plain table instead of a spreadsheet where the actual content
lives in cell-fill colour.

**Vendored files:** [`data/shiva_sutras/sutras.tsv`](https://github.com/gasyoun/kosha/blob/main/data/shiva_sutras/sutras.tsv) (14 rows),
[`data/shiva_sutras/pratyaharas.tsv`](https://github.com/gasyoun/kosha/blob/main/data/shiva_sutras/pratyaharas.tsv) (42 rows),
[`data/shiva_sutras/shiva_sutras.json`](https://github.com/gasyoun/kosha/blob/main/data/shiva_sutras/shiva_sutras.json) (combined)
(regenerate: [`scripts/build_shiva_sutras.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_shiva_sutras.py)).

**Source.** `Panini/ShivaSutras.xlsx` + `.docx` (yadisk `09_Palsule`-adjacent
folder; MG's own explainer workbook, Russian). The xlsx never enters this
repo — raw source stays gitignored, local-only (H4471 mission). Its `Ranges`
sheet encodes each pratyāhāra as a *cell-fill-highlighted* contiguous span
over one fixed 57-token Māheśvara-sūtra sequence typed into every row; there
is no per-pratyāhāra text cell, only the highlight, so the sheet is not
machine-parseable by reading cell values alone. Extracted once with openpyxl
(`fill.patternType != 'none'` per cell) and pinned as the `PRATYAHARA_SPANS`
constant in the builder — the builder does not re-open the xlsx.

**Sūtra/marker split rule.** The 57-token master sequence is Pāṇini's 14
sūtras with their 14 anubandha (IT) markers still embedded. Every marker
token in the source carries a virāma (U+094D); every real phoneme token does
not — that single rule splits the sequence into exactly 14 sūtras and strips
markers out of each pratyāhāra's `letters_only` column.

**Fields.**
- `sutras.tsv`: `sutra_number` (1–14) · `devanagari` (full sūtra incl. its
  marker) · `letters_only` · `it_marker`.
- `pratyaharas.tsv`: `name` (ASCII-safe transliteration, e.g. `aTh` for aṬ,
  `aS` for aṤ) · `devanagari_span` (from the pratyāhāra's first letter
  through its terminal marker) · `letters_only` (markers stripped) ·
  `it_marker` · `length` (span length in tokens).

**Coverage.** 14/14 sūtras, 42/42 highlighted pratyāhāra rows in the source
sheet (0 dropped, 0 non-contiguous spans). Spot-checked against standard
Pāṇinian pratyāhāra tables: `aK` = a i u ṛ ḷ, `aC` = all vowels, `aṇ` (`aN1`
here) = a i u, `yaṆ` = y v r l, `haL` = all consonants — all match published
grammars.

**Not included.** The source workbook's `Pictures` sheet (visual
highlight-table renders of each pratyāhāra against the full phonetic-alphabet
grid — a rendering aid, not additional data) and `SandhiExamples` sheet
(worked sandhi examples using these pratyāhāras in Pāṇini's own sūtra
`इको यणचि` etc. — a pedagogy layer, out of scope for H4471; a future handoff
can lift it separately). The accompanying `.docx` is a Russian-language
explainer essay about *how* pratyāhāras work pedagogically, not itself a data
source — no rows derived from it.

**Prior-art check (H4471).** No existing machine-readable pratyāhāra / Śiva
Sūtra table found in `kosha` (`data/manifest/datasets.json`'s
`paninian-sutra-coverage-map` covers the 3,983-sūtra Aṣṭādhyāyī derivation
enumeration, a different and much larger object — the 14 Māheśvara Sūtras are
prerequisite grammar Aṣṭādhyāyī assumes, not part of it), `VisualDCS`,
`Sangram` (`SanskritGrammar/sangram/`), or the local `vidyut` 0.4.0 Python
build (`vidyut.prakriya.Sutra` is the Aṣṭādhyāyī sūtra type; no pratyāhāra
table is exposed to Python, though the Rust core likely has pratyāhāra-range
logic internally — that is code, not a shippable dataset). This is new.

**License.** Pāṇini's grammar is public domain (~5th c. BCE); no rights
question, unlike the Palsule dhātupāṭha XLS this yadisk folder sits beside.
MIT for the derived table; public. Credit **Dr. Mārcis Gasūns**.

_Dr. Mārcis Gasūns_
