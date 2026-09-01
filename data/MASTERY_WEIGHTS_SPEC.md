# Mastery weight semantics — one shared meaning across kosha's five drill families

_Created: 01-09-2026 · Last updated: 01-09-2026_

H3742. Every drill family already had its own curriculum-order tunables
(`drill_weights.json` / `difficulty_weights.json` — what order to *teach*
items in). Those stay untouched; this doc adds a second, comparable layer:
**mastery ease**, the one number the combined scheduler (`scripts/build_mastery_schedule.py`)
uses to seed a new item's initial FSRS-style difficulty before any review
history exists, so items from different families can be mixed into one due
queue on a fair footing.

## The shared contract

Every family's weights file carries a `"mastery"` block:

```json
"mastery": {
  "bucket_field": "<item key this reads>",
  "bucket_ease": {"<bucket>": <float 0..1>, ...}   // OR "ease_formula" for rank-based families
  "family_default_ease": <float 0..1>
}
```

`ease` is always **0..1, higher = easier** (mirrors the sign convention
`difficulty_weights.json`'s sandhi `class_weight` already used). It is used
only to seed a new item's starting stability/difficulty in the FSRS-style
mixer — once a learner reviews an item, its own review history overrides the
seed. `family_default_ease` is the fallback for any item whose bucket value
is missing or unrecognized.

## Per-family mapping (why each one differs)

| Family | `bucket_field` | Method | Reused from |
|---|---|---|---|
| sandhi | `category` | table lookup | `difficulty_weights.json` `class_weight` (already 0..1, higher=easier) — copied, not re-tuned |
| samasa | `type` | table lookup | item **task** format (identify/member_side/member_recall/split) — the samāsa-*category* code (KD/TP/BV/DV) is not stored per-item in `samasa_drills.json`, only in `reference.tsv`/`provenance`, so the mastery layer approximates by task-generation cost instead: recognition easiest, free production hardest |
| morphology | `rank` | formula | `rank_frequency.tsv`-style corpus rank already on every item (1..464); low rank (frequent) → easier |
| vocab | `rank` | formula | frequency rank already on every item (1..7532) |
| thematic vocab | `rank` | formula | within-theme frequency rank already on every item (6..7528) |

Rank-based formula (documented once, applied identically in every rank-based
family): `ease = clamp(1.0 - (rank - 1) / max(rank_max - 1, 1) * 0.6, 0.4, 1.0)`
— rank 1 → 1.0, worst rank in that family → 0.4. The 0.6 span (not 1.0) keeps
the floor above sandhi's own hardest bucket (0.6) so no family's tail is
scheduled as radically harder than another family's hardest class.

## Cohort `start_chteniya` — deliberately excluded, not a gap

`data/cohort_start_chteniya/` is a **frozen** lesson≤3 subset of
`data/sandhi/sandhi_drills.json`, pinned by
[`scripts/freeze_cohort_start_chteniya.py`](https://github.com/gasyoun/kosha/blob/main/scripts/freeze_cohort_start_chteniya.py)
whose own fence reads *"No new analysis layers; no human-overlay overwrite;
freeze only"*. It shares item `id`s 1:1 with a subset of `sandhi_drills.json`,
so it already inherits sandhi's `mastery` block by `id` lookup — adding a
second `drill_weights.json` or `.apkg` there would (a) violate the freeze
fence and (b) double-count sandhi items in the combined schedule. H3742's own
title names **five** drill families (sandhi, samāsa, morphology, vocab,
thematic vocab); the mint-time parity table listed cohort as a sixth row in
error — corrected here rather than carried forward.

Two more parity-table cells were stale at mint time and are corrected the
same way: **vocab** (`data/frequency/vocab_curriculum.apkg`, built by
[`scripts/build_vocab_curriculum.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_vocab_curriculum.py),
H947) and **thematic vocab**
(`data/frequency/thematic_vocabulary.apkg`, built by
[`scripts/build_thematic_vocabulary.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_thematic_vocabulary.py),
H1462) both already existed on `origin/main` before this handoff — the real
parity gap was only the five `mastery` weight blocks, not any `.apkg` file.

## Not a second SRS engine

This is a **data layer for kosha's own static reading surfaces**
(SanskritKaraoke, SanskritGrammar readers) — it does not schedule reviews for
Systema-Sanscriticum's course delivery. `docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md`
already rules "not a new SRS engine — Systema 'Saraswati' (FSRS) + kosha Anki
export already exist; surfaces emit items, they do not schedule them" for
kosha↔Systema; that ruling is about the Anki-export path into Systema's paid
review pipeline, which this does not touch or duplicate. `build_mastery_schedule.py`
only orders kosha's own five item pools for a reader session; it emits no
export path into Systema and holds no per-learner review state.

## Combined schedule

[`scripts/build_mastery_schedule.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_mastery_schedule.py)
reads all five families' items + `mastery` blocks and writes
`data/mastery/combined_schedule.json`: one row per item (`family`, `id`,
`ease`, `stability_days`, `due`). `due_items(schedule, clock, n, seed)`
draws the `n` items with the earliest `due` (ties broken by a seeded,
deterministic shuffle) — same `(schedule, clock, n, seed)` always returns the
same list, and across a run the returned items span more than one family
(proved by `tests/test_mastery_schedule.py`).

_Dr. Mārcis Gasūns_
