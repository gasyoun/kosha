# dcs_upasarga_prefixus.tsv — DCS prefixed-verb decomposition (MG 2014 workbook)

_Created: 11-09-2026 · Last updated: 11-09-2026_

**Dataset:** [dcs_upasarga_prefixus.tsv](dcs_upasarga_prefixus.tsv) · 6,425 rows · 192,987 bytes · sha256 `6d2f2ff2519d6ab6700be9f13741be74a1833226fa896c9c0ea9a403f37749b3`
**Handoff:** [H4534](https://github.com/gasyoun/Uprava/blob/main/handoffs/H4534-OxAlpha_kosha_dcs-upasarga-praefixus-dataset_11.09.26.md) (OxAlpha) · class: data
**Regen:** `python scripts/extract_dcs_upasarga_prefixus.py --xlsx <DCS-upasarga-analysis.xlsx>` (rerun byte-identical — H4534 parity PASS)

## Provenance

- Source: yadisk `Sanskrityatina/05_Sanskrit-Lexicon/upasarga-stat/DCS-upasarga-analysis.xlsx` — Dr. Mārcis Gasūns' own working workbook, file dated 28-09-2014. Sheet `praefixus`, 6,425 data rows × 6 columns (dims as censused by [H4477 §5](https://github.com/gasyoun/SanskritLexicography/blob/master/YADISK_05_SANSKRIT_LEXICON_TREES_CENSUS_10-09-2026.md)).
- **Derived-only:** the xlsx stays on yadisk (MG ruling 07-09-2026) and is not committed anywhere in this repo.

## Columns

| TSV column | Source column | Filled | Meaning |
|---|---|---|---|
| `in_form` | `IN` | 6,425 (100%) | prefixed verb form as found in DCS |
| `prefix_guess` | `Praefixus вообще какие бывают` | 38 | naive allomorph-inventory match; demonstrably wrong where it disagrees with `prefix` (e.g. `abhigā` → guess `prati`, resolved `abhi`) — kept for faithfulness, not for use |
| `dhatu` | `OUT DHATU` | 6,425 (100%) | extracted dhātu (1,839 distinct strings) |
| `palsule_no` | `Найдено соответствие с № в Palsule` | 1,099 (321 distinct, № 27–3659) | match № into the Palsule root list; all 321 distinct №s validate 100% against the workbook's own `dhatu` sheet numbering |
| `prefix` | `Praefixus` | 5,059 | MG's resolved prefix parse — the working column |
| `dhatu_check` | `OUT DHATU` (2nd) | 6,425 (100%) | MG's own QA duplicate; equals `dhatu` exactly (case-sensitive) in 100% of rows |

1,350 rows carry no prefix resolution in either column (dhātu extracted, prefix undetermined).

## Sheets NOT derived (available on yadisk, out of H4534 scope)

- `dhatu` (3,688×8) — three root+«№ в списке» column groups (Palsule root lists; yellow pairs hand-added by MG)
- `replace` (40×2) — sandhi/vowel-grade normalization pairs used while matching
- `Лист2` (39×2) — prefix frequency tally

## Join view vs the Gita compositional dataset ([sanskrit-upasarga-semantics](../gita/upasarga_semantics.tsv), 214 rows)

H4477 census §5 verdict holds: **zero source overlap** — this dataset is the DCS *dictionary* dimension (frequency of prefixed forms in the parsed corpus), the Gita set is the *compositional* dimension (how preverbs shift root sense in one fixed text). The key spaces nevertheless intersect, which makes the join real:

- praefixus resolved `(dhatu, prefix)` pairs: **5,007**
- gita `(root, preverb)` pairs: **69**
- shared keys: **34** — e.g. `bhū + pra-`, `dā + pra-`, `gam + ā-`, `vṛt + pra-/ati-/ni-/anu-/ā-`, `dhā + abhi-/vi-`, `īkṣ + sam-`, `han + abhi-/upa-`

A consumer can therefore join sense shift (Gita side) onto corpus attestation (DCS side) for those 34 keys; the remaining 4,973 praefixus pairs and 35 gita pairs are each side's unique complement.

## Licence

CC BY-SA 4.0, credit Dr. Mārcis Gasūns — mirrors sibling [`sanskrit-upasarga-semantics`](../gita/upasarga_semantics.tsv) (DCS underlying data is CC BY 4.0).

_Dr. Mārcis Gasūns_
