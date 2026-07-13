# parallel-passage-concordance (B3) -- build report

_Created: 13-07-2026 · Last updated: 13-07-2026_

Built by [scripts/build_parallel_passage_concordance.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_parallel_passage_concordance.py) (H836, Sonnet 5 `claude-sonnet-5`), from [VisualDCS/derived-data/Paralleli-v-tekstah-korpusa-SRC/PARA/Polnorazmernye/](https://github.com/gasyoun/VisualDCS) (245 CSV files, the corrected/regenerated 2026 full-text-match pass).

## R-C2 -- canonical-variant decision (surfaced, not self-ruled)

Per `CONCORDANCE_ROADMAP.md` risk R-C2, this build used `Polnorazmernye/` (the 2026 full-size/meter-to-meter pass) as the working default -- the folder's *own* README already labels it “canonical” against `Polnorazmernye-2022-archive/` (“not canonical”, differs in 140/245 files per prior audit) and `Stopovye/` (a **different unit of comparison** -- per-pada/foot matching, not meter-to-meter, and only a partial 113-of-245-text run). This build does **not** independently re-content-diff the three variants row-by-row (no new evidence beyond the existing README audit) -- a human should confirm `Polnorazmernye/` as the released canonical before the dataset ships as "final", since the org convention is not to self-rule R-C2. `@DECIDE`: confirm `Polnorazmernye/` as canonical (or direct otherwise).

## Bloomfield RV cross-reference -- NOT built this pass

Roadmap Q2 asks for a Bloomfield *Vedic Concordance* (1906) pratika cross-reference for the RV subset. No digitization of Bloomfield's concordance was found anywhere in the org (checked: no repo under `GitHub/` mentions it outside this handoff and H731's bibliography note). Per roadmap open `@DECIDE` #3, which digitization to key against is a human call -- this is shipped as an honest gap, not fabricated. Once a source is chosen, the RV-subset rows in `parallel_passage_verses.tsv` (source_text_name matching the DCS Rgveda text) are ready to receive a `bloomfield_pratika` column in a follow-up pass.

## Counts

| metric | value |
|---|---|
| source files (Polnorazmernye/*.csv) | 245 |
| source verses parsed | 501231 |
| source verses with >=1 parallel | 15164 (3.0%) |
| total parallel links (GOOD+PARTLY) | 153045 |
| — GOOD (exact) | 13862 |
| — PARTLY (partial, word-diff attached) | 139183 |
| distinct source texts represented | 245 |
| source texts with >=1 linked verse | 144 |
| duplicate anchor_ids (col1+col2 collision within a file) | 114 |

**Note on the roadmap's prior “506,787 alignments” estimate:** that figure (from `CONCORDANCE_ROADMAP.md`, sourced from the export's own README, which itself states it was “not independently sampled”) does not match this build's directly-parsed counts (501231 source verses / 153045 actual GOOD+PARTLY links). This build's numbers come from parsing every row of every `Polnorazmernye/*.csv` file directly and are the authoritative count going forward; the discrepancy is flagged here rather than silently reconciled.

## Schema notes (confirmed against the folder's own RTF documentation)

- `target_locus` is stored **verbatim** from column 4 of the source CSV -- the RTF states this column already IS the full self-describing locus (work name + book + chapter + verse + pada), so it is not re-decomposed.
- `anchor_id` = `para:<textId>:<col1>|<col2>` -- a synthetic but stable key combining the source PARA text id (own namespace -- **confirmed NOT the same as `dcs_full.sqlite.text.text_id`**, spot-checked on ids 104/107/10) with the verse/pada locus columns.
- `match_method` carries the source verdict (`GOOD`/`PARTLY`) directly, rather than the Q1 SLP1-tier vocabulary (`exact`/`floor`/`relaxed`/`fuzzy`) -- these are a different axis (textual-parallel-quality, not lexical-match-confidence) and deliberately not conflated. `confidence` maps GOOD=0.95, PARTLY=0.55 for cross-concordance sortability.


_Dr. Mārcis Gasūns_
