# Data statement — Unified upasarga atlas (decomposition × semantics × class frequencies)

_Created: 15-09-2026 · Last updated: 15-09-2026_

**Dataset:** `upasarga-atlas` — one row per `(root, preverb)` key joining the
three registered upasarga datasets: the DCS prefixed-verb **decomposition**
(MG 2014 workbook), the Gītā root × preverb **semantics**, and the DCS
**per-class verb-form frequencies**.

**File:** [`data/upasarga/upasarga_atlas.tsv`](https://github.com/gasyoun/kosha/blob/main/data/upasarga/upasarga_atlas.tsv)
(13,436 data rows; regenerate: [`scripts/build_upasarga_atlas.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_upasarga_atlas.py),
verify: `python scripts/build_upasarga_atlas.py --verify`).

**Source legs.**

1. [`dcs-upasarga-prefixus`](https://github.com/gasyoun/kosha/blob/main/data/upasarga/dcs_upasarga_prefixus.tsv)
   (H4534) — 6,425 workbook rows; keyed on the **resolved `prefix` column only**
   (5,059 rows → 5,007 pairs). The naive `prefix_guess` column (38 rows,
   demonstrably wrong where it disagrees) never keys the atlas. The 1,366
   no-prefix rows (1,350 unresolved + 16 guess-only) collapse to root-level keys.
2. [`sanskrit-upasarga-semantics`](https://github.com/gasyoun/kosha/blob/main/data/gita/upasarga_semantics.tsv)
   (H876 W6) — 214 Gītā rows; `√` stripped on join; `preverb` kept **verbatim** —
   comma-lists (`abhi-,pra-,vi-`) are alternative readings and are NOT exploded
   (this reproduces the H4477 census join exactly).
3. `dcs-verb-class-prefix-frequency` (VisualDCS
   `derived-data/Glagolnye-formy/Klassy/Spisok-form-s-prefiksami-8444/Cl_Frq/1..10.csv`)
   — per-class `root;count` frequencies, joined at **root level only** (the
   dataset has no preverb dimension), non-zero classes as `1:30478|3:22`. Ten
   unkeyed bare-number lines (one per file — the class's own total) are excluded
   from the join and reported by the builder.

**Fields.** `root · preverb · sense · gita_count · prefixus_forms ·
prefixus_sample_form · class_freqs · sources` (`preverb` empty = root-level
row; `sources` = sorted `+`-join of {classfreq, prefixus, semantics}).

**Census shape.** 13,436 keys = classfreq-only 7,020 / prefixus-only 5,037 /
prefixus+classfreq 1,165 / all-three 108 / semantics-only 52 /
prefixus+semantics 34 / semantics+classfreq 20. Shared nonempty-preverb keys
prefixus × semantics: **34** — the H4477 census anchor, reproduced exactly
(`bhū+pra-`, `dā+pra-`, `gam+ā-`, `vṛt+pra-/ati-/ni-/anu-/ā-`, …). Root-match
rates against the class-frequency leg: dhātu side 1,313/1,839; Gita-root side
131/148 (both joins are exact-string — no transliteration normalization).

**Verification.** `python scripts/build_upasarga_atlas.py --verify` re-reads the
emitted TSV and cross-checks: key-set parity vs a fresh recompute, the H4477
34-shared-key anchor, a deterministic 5-key root/preverb parity sample
(sense + form counts on both sides), and a full class-frequency round-trip.
Rerun is byte-identical (sha256 `97f3b975…1503`, regen-checked 2026-09-15).

**License.** **CC BY-SA 4.0**, credit **Dr. Mārcis Gasūns** — mirrors the three
sources (DCS underlying data CC BY 4.0; Gita workbook MIT; both ship BY-SA on
the public tier).

**Relation.** Census **C2** — first consumer of `dcs-upasarga-prefixus`, second
consumer of `sanskrit-upasarga-semantics` and of
`dcs-verb-class-prefix-frequency` (handoff H4729).

_Гасунс_
