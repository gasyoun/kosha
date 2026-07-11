# Data statements — kosha public-tier datasets

_Created: 11-07-2026 · Last updated: 11-07-2026_

One data statement (Bender & Friedman 2018 data-statement / Gebru et al. 2021
datasheet form, extended with the org metadoc-v2 fields: intended use & known
misuse, maintenance & sunset plan, deprecation status) per dataset served via
the kosha [`data-v*` releases](https://github.com/gasyoun/kosha/releases).
Each statement is wired into its row in
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
via the `data_statement` field.

## Covered (release data-v0.1.0, all 7 public assets)

| Dataset | Rows | Statement |
|---|---|---|
| MW verbal-root inventory | 2,113 | [mw-roots.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/mw-roots.meta.md) |
| Headword→root derivation table | 9,377 | [mw-etymology.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/mw-etymology.meta.md) |
| DCS ↔ CDSL crosswalk | 15,902 | [dcs-cdsl-xref.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/dcs-cdsl-xref.meta.md) |
| Union headword index | 323,425 | [union-headwords.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/union-headwords.meta.md) |
| MW ↔ Heritage crosswalk | 185,803 | [mw-heritage-crosswalk.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/mw-heritage-crosswalk.meta.md) |
| DCS lemma frequency sidecar | 83,277 | [kosha-lemma-frequency.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/kosha-lemma-frequency.meta.md) |
| Zaliznyak grammar-token index | 98,639 | [zaliznyak-grammar-index.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/zaliznyak-grammar-index.meta.md) |

## Out of scope this pass (queued backlog)

Per [H665](https://github.com/gasyoun/Uprava/blob/main/handoffs/H665-Fable_kosha_dataset-data-statements_11.07.26.md),
statements were authored for the **kosha-served public tier** only. Queued for
a later pass, each citing this backlog as owner until a handoff is minted:

- **Public, repo-internal rows** ("listed for discovery", `in_release: null`):
  `indische-sprueche`, `dcs-grapheme-frequency`, `varga-series-diachrony`,
  `dcs-sintagmatic-appendix7`, `dcs-parallel-passages-full`,
  `dcs-verb-roots-by-class`, `dcs-verb-class-prefix-frequency`,
  `dcs-sintagmatic-appendix6-periods`, `stopovye-parallel-passages`,
  `dcs-verb-form-frequency-prelim`, `dcs-compound-dictionary`,
  `dcs-stem-cooccurrence-full`, `which-dictionary-routing-benchmark` (already
  has a data card at csl-guides /developers/data-cards — statement would
  cross-link, not duplicate), `correction-loci`.
- **Restricted tier** (rights-encumbered or local-only; statements would need
  the rights question settled first): `corpus-lexicon`, `sa-ru-glossary`,
  `kosha-db`, `dcs-full-sqlite`, `samudra-corpus-db`, `heritage-mirror`,
  `heritage-forms-crosswalk-extras`.
- **Intermediate tier** (not standalone-citable, statements not owed):
  `russiantranslation-src-raw-ingests`, `dcs-verb-example-ids` — explicit
  not-applicable verdict, not a backlog item.

## Provenance

Programme: metadoc census
[METADOCS_INDEX.md](https://github.com/gasyoun/Uprava/blob/main/METADOCS_INDEX.md)
item 3. Authored 11-07-2026 by Fable 5 (`claude-fable-5`) under H665.

_Dr. Mārcis Gasūns_
