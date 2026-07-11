# kosha.db completeness audit vs the csl-orig dictionary inventory

_Created: 11-07-2026 · Last updated: 11-07-2026_

Produced by [H687](https://github.com/gasyoun/Uprava/blob/main/handoffs/H687-Fable_kosha_kosha-db-completeness-audit_11.07.26.md)
(Fable 5, `claude-fable-5`), answering the
[DATA_LAYERS_CENSUS.md](https://github.com/gasyoun/Uprava/blob/main/DATA_LAYERS_CENSUS.md)
§3 row "kosha.db (1.6 GB): rows per table · dicts loaded · index coverage".
Regenerate every number here with
[scripts/audit_db_completeness.py](https://github.com/gasyoun/kosha/blob/main/scripts/audit_db_completeness.py)
(read-only vs the DB; compares against a live sibling `csl-orig/v02` clone).

## Verdict

**The service is complete for its declared scope, and its declared scope is
3 of 44 csl-orig dictionaries.** Every loaded dictionary (mw, pwg, ap90)
matches the live csl-orig `<L>` count **exactly — zero drift, no shortfall**
(threshold was >1%; actual is 0.000% on all three). The 41 unloaded
dictionaries are a scope boundary, not data loss: full-text `entries` carry
29.7% of the org-wide entry mass (444,773 of 1,496,157 live `<L>` entries),
while the union-headword `lemmas` layer already spans 15 dictionary codes.
The 06-07-2026 census baseline counts re-verified live with no change.

## 1. Tables and row counts (measured 11-07-2026)

`data_version = 0.1.0-dev` · file size 1,654,849,536 bytes (~1.65 GB)

| table | rows | matches 06-07-2026 baseline |
|---|---:|---|
| entries | 444,773 | yes |
| forms | 1,378,401 | yes |
| inflections | 6,916,522 | yes |
| lemmas | 323,425 | yes |
| meta | 1 | — |
| senses | 692,403 | yes |
| sources | 3 | — |
| sqlite_stat1 | 13 | — (ANALYZE stats) |
| stem_bridge | 760 | — |

## 2. Loaded dictionaries vs live csl-orig `<L>` counts

Source counts are live `<L>`-marker counts from the sibling
[csl-orig](https://github.com/sanskrit-lexicon/csl-orig) `v02/<code>/<code>.txt`
files at audit time — not the frozen counts in the `sources` table (which
also agree). `sources.csl_orig_commit` pins each load to the
csl-sqlite release of 2026-06-28.

| dict | source `<L>` (live) | db entries | delta | senses | pc coverage | status |
|---|---:|---:|---:|---:|---:|---|
| mw | 286,525 | 286,525 | +0 (0.000%) | 303,022 | 100.0% | OK |
| pwg | 123,366 | 123,366 | +0 (0.000%) | 223,446 | 100.0% | OK |
| ap90 | 34,882 | 34,882 | +0 (0.000%) | 165,935 | 100.0% | OK |
| **total** | **444,773** | **444,773** | **+0** | **692,403** | | |

No dictionary is *partially* loaded: `COUNT(DISTINCT L) = COUNT(*)` for all
three (no duplicate or dropped `L` ids).

## 3. The 41 unloaded dictionaries (of the 44-dict inventory)

The live `csl-orig/v02` tree holds **44** dictionary directories (the
handoff's "43-dict inventory" undercounts by one; `etymology_stats` is
excluded as a non-dictionary). Per-dict live `<L>` counts, largest first:

| dict | source `<L>` | dict | source `<L>` | dict | source `<L>` |
|---|---:|---|---:|---|---:|
| pw | 170,556 | bor | 24,609 | ieg | 7,932 |
| ap | 90,843 | stc | 24,574 | armh | 7,907 |
| mw72 | 55,390 | md | 20,749 | gst | 6,780 |
| lrv | 53,441 | bur | 19,776 | lan | 4,944 |
| vcp | 50,135 | bhs | 17,839 | vei | 3,834 |
| acc | 49,833 | pui | 17,512 | mci | 2,643 |
| shs | 47,326 | ben | 17,310 | krm | 2,061 |
| yat | 45,206 | inm | 12,647 | abch | 1,965 |
| wil | 44,577 | gra | 12,785 | nmmb | 506 |
| skd | 42,531 | ae | 11,359 | pgn | 485 |
| cae | 40,069 | bop | 8,961 | snp | 453 |
| mwe | 32,378 | pe | 8,799 | acph | 163 |
| ccs | 30,010 | fri | 8,155 | acsj | 240 |
| sch | 29,125 | pwkvn | 24,976 | | |

Largest absences by mass: **pw** (170,556 — the biggest single gap),
**ap** (90,843), **mw72** (55,390), **lrv** (53,441), **vcp** (50,135).
Note `data/raw_sqlite/` already holds rebuildable per-dict SQLite for
mw, pwg **and ap90** (all three loaded ones), so the next candidates would
enter via the same csl-sqlite path.

## 4. Union-headword layer (`lemmas`) — broader than the full-text layer

`lemmas.dicts` records membership across **15** dictionary codes — the
union headword spine covers many dictionaries whose full text is *not*
loaded (PWK, SKD, VCP, CAE, CCS, SCH, BUR, MD, BHS, INM, GRA, VEI):

| code | lemmas | code | lemmas | code | lemmas |
|---|---:|---|---:|---|---:|
| MW | 193,852 | SKD | 40,703 | MD | 20,095 |
| PWK | 151,314 | CAE | 38,476 | BUR | 19,135 |
| PWG | 106,054 | CCS | 28,743 | BHS | 17,761 |
| AP | 88,744 | SCH | 28,431 | INM | 9,431 |
| VCP | 48,583 | GRA | 11,108 | VEI | 3,702 |

All 323,425 lemmas carry at least one dict code.

## 5. Forms and inflections — provenance

| layer | source | rows |
|---|---|---:|
| forms | heritage (7 categories: nominal 402,126 · participle 337,271 · finite-verb 178,886 · indeclinable 13,367 · iic-compound 9,534 · iiv-compound 7,692 · verbal-indecl 3,115) | 951,991 |
| forms | dcs | 397,843 |
| forms | vidyut | 28,567 |
| inflections | cologne_mwinflect (MW-derived only) | 6,916,522 |

## 6. Index / lookup-path coverage

| lookup path | index | dict coverage |
|---|---|---|
| entry body by dict + headword | `entries_dict_key (dict, slp1_key, L)` | mw, pwg, ap90 (3/44) |
| senses per entry | `senses` PK (entry_id, sense_n) | mw, pwg, ap90 |
| union headword (lemma) | `lemmas` PK (slp1) | 15 codes (§4) |
| form → lemma | `forms` PK + `forms_lemma (lemma_slp1)` | source-based (heritage/dcs/vidyut), dict-independent |
| inflection by surface form | `inflections_form (form_slp1)` | MW-derived only |
| inflection by lemma | `inflections_lemma (lemma_slp1)` | MW-derived only |
| stem-bridge canonicalization | `stem_bridge_canonical (canonical_slp1)` | 760 rows |

Every declared lookup path is index-backed; there is no unindexed hot path.
The asymmetry to know about: **form/inflection lookups resolve to lemmas
from any of the 15 union codes, but a full entry body renders only for the
3 loaded dicts** — beyond those, the UI falls back to csl-orig links
([scripts/fallback_csl_orig.py](https://github.com/gasyoun/kosha/blob/main/scripts/fallback_csl_orig.py)).

_Dr. Mārcis Gasūns_
