_Created: 19-07-2026 · Last updated: 19-07-2026_

# Implementation — kosha pedagogy Wave RU (Russian-learner surfaces, file-level steps)

The Russian-learner extension of the shipped pedagogy engine. Parent plan:
[`PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md);
wave definition:
[`docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md)
§ Wave RU; acceptance criteria:
[`docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md)
§ Wave RU. Both deliverables follow the six-stage pedagogy-surface contract in
[`docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md)
unchanged — Wave RU adds a *gloss-language* layer and a *new source-text pack*, not a new
contract stage.

Staged 19-07-2026 via [`/ask-batch`](https://github.com/gasyoun/claude-config/blob/main/commands/ask-batch.md)
by Fable 5 (`claude-fable-5`); interview rulings recorded in
[`ASK_BATCH_STAGING_PEDAGOGY_2026-07.md`](https://github.com/gasyoun/Uprava/blob/main/ASK_BATCH_STAGING_PEDAGOGY_2026-07.md)
(private hub).

**The standing rights gate for this whole wave:** every published Russian gloss must come
from the **public site-tier subset** of the
[SanskritRussian](https://github.com/gasyoun/SanskritRussian) three-layer glossary. The
restricted bulk layers (aligned to published Russian translations) and `corpus_lexicon`
stay local-only inputs — nothing derived from them ships in a public page or dataset
without an explicit rights review. Run `/publish-safety-check` before any Pages/site
deploy from this wave.

---

## W-RU-a — Inline Sa→Ru gloss layer in reading packs ([H1278](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1278-Opus_kosha_pedagogy-wave-ru-inline-gloss-reader_19.07.26.md), Opus)

**What ships:** every token in a kosha reading pack can carry a Russian gloss triple
(surface rendering · lemma gloss · root gloss), so a Russian-speaking learner hovers a
word and reads its meaning without leaving the text. English glossing, where present,
is untouched — this is an additive layer keyed by gloss language.

1. **Prior-art check first (30 min, hard gate).** Read the reading build report
   ([`reading/BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/reading/BUILD_REPORT.md))
   and the Systema reader-pipeline handoffs (H955/H959/H965) to confirm what per-token
   gloss fields the pack schema already carries. If a gloss-language mechanism already
   exists, extend it; do not add a parallel one.
2. **Source layer.** From the [SanskritRussian](https://github.com/gasyoun/SanskritRussian)
   repo take the three ranked public site-tier layers (surface ≈190k / lemma ≈40k /
   root ≈2k entries; layout per its README). Build
   `scripts/build_ru_gloss_layer.py` that joins pack tokens (SLP1 lemma + surface) to the
   three layers and emits `data/ru_gloss/ru_gloss_layer.tsv` — one row per (pack, token
   position): `surface_ru`, `lemma_ru`, `root_ru`, plus a `layer_hit` provenance column.
3. **Pack integration.** Extend the pack builder
   ([`scripts/build_reading_pack.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_reading_pack.py))
   with an optional `--gloss-lang ru` pass that inlines the joined glosses into pack JSON
   under a `gloss.ru` key; regenerate the Gītā packs (all 18 adhyāyas, H871) and the Nala
   pack with the layer on.
4. **UI.** Wire the existing hover/popover used by the sandhi reader layer (H917 pattern)
   to show the RU triple when present; a language toggle defaults to RU when the browser
   locale is Russian.
5. **Coverage metric (stage ② of the contract).** Report per-pack token-coverage: % of
   tokens with a lemma-layer RU gloss, and the top-20 uncovered lemmas, appended to
   [`reading/BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/reading/BUILD_REPORT.md).
   This is the measurable output that tells us whether the public subset suffices or a
   rights unlock is worth pursuing.
6. **Manifest + tests.** New row `ru-gloss-layer` in
   [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
   (public tier, provenance = SanskritRussian public subset) + a data statement under
   [`docs/data-statements/`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/README.md);
   joiner unit-tested on a 50-token fixture with known expected hits/misses.

## W-RU-b — Graded beginner subhāṣita reader ([H1279](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1279-Fable_kosha_pedagogy-wave-ru-subhashita-reader_19.07.26.md), Fable)

**What ships:** a new reading-pack *family* built from Böhtlingk's Indische Sprüche —
short, famous, self-contained sayings — difficulty-graded so an absolute beginner meets
real Sanskrit from day one: each saying sandhi-split, RU-glossed, metre-tagged.

1. **Source.** The Indische Sprüche JSONL (7,537 sayings, public domain) lives in
   [SanskritLexicography](https://github.com/gasyoun/SanskritLexicography) — locate the
   exact path via its
   [`FEATURES_INDEX.md`](https://github.com/gasyoun/SanskritLexicography/blob/master/FEATURES_INDEX.md)
   row F33. Consume it in place (path pinned in the build script header); never copy the
   corpus into kosha wholesale.
2. **Difficulty grading.** Score every saying with the shipped W2a difficulty scorer
   (vocab-frequency × sandhi-density × morphology-rarity × compound-load, per
   [`data/difficulty/METHODS.md`](https://github.com/gasyoun/kosha/blob/main/data/difficulty/METHODS.md));
   emit `data/subhashita/subhashita_difficulty.tsv` with the full score decomposition.
3. **Curation (the Fable judgment step).** Select the beginner band: the ~100 lowest-difficulty
   sayings that are also *quotable* — prefer sayings whose lemmas sit inside the W1b
   top-frequency vocabulary bands. Selection criteria and the reject log go in
   `data/subhashita/CURATION_NOTES.md` so the band is auditable, not vibes.
4. **Pack build.** Run the selected band through the standard pack pipeline: sandhi-split
   against [`data/sandhi/corpus_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/corpus_sandhi.tsv)
   junctions, metre-tag via the W3a path
   ([`data/vidyut/chandas/meters.tsv`](https://github.com/gasyoun/kosha/blob/main/data/vidyut/chandas/meters.tsv)),
   RU-gloss via the W-RU-a layer (soft dependency: if H1278 has not shipped yet, build
   the pack without `gloss.ru` and note the re-run; do not block).
5. **Page + export.** A `reading/` index page section "Subhāṣita (beginner)" ordered by
   difficulty; Anki/JSON export of the band via the existing exporter (one saying per
   card: front = sandhied verse, back = split + RU gloss + metre).
6. **Manifest + tests.** Manifest row `subhashita-reader-pack` (public tier — base text is
   public domain; RU glosses from the public subset only) + data statement; the grading
   step regression-tested on 10 hand-checked sayings.

---

## Cross-wave build discipline

Identical to Wave 1 (see
[`docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE1.md`](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE1.md)
§ Cross-wave build discipline): stdlib-only scripts with UTF-8 reconfigure, byte-stable
regeneration, one PR per deliverable, changelog + release per ship, manifest row in the
same PR as the data, and the fence — no csl-orig writes, no sibling-repo source edits,
integrate via data only.

_Dr. Mārcis Gasūns_
