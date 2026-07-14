_Created: 14-07-2026 · Last updated: 14-07-2026_

# Architecture — the kosha pedagogy-surface contract

Cover: [`PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md).
Roadmap: [`docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md).

The whole plan rests on one observation: **the shipped sandhi programme is not one tool —
it is a repeatable pattern.** Every pedagogy aspect kosha can teach reduces to the same
six-stage pipeline. Naming that pipeline is the architecture; each wave is a fresh
instantiation, so the marginal cost of aspect N+1 is small.

## The six-stage contract

```
 ①  SOURCE            a kosha data asset, manifest-registered
        │             (paradigms · lemma_frequency · compound dict · reading packs · roots)
        ▼
 ②  RANK              order every item by frequency / difficulty
        │             → the coverage metric:  "learn N items → cover X% of real text"
        ▼
 ③  GRADED SURFACE    curriculum.tsv (ordered syllabus, lessons)
        │             + drills.json  (answer-keyed items: identify / split / fill / match)
        │             + reference.tsv (look-up-by-class, ranked, attested example each)
        │             weights exposed in a JSON config (tunable, not hard-coded — the MG ruling)
        ▼
 ④  WEB PAGE          self-contained theme-aware HTML under  reading/<aspect>/
        │             (curriculum/ · drills/ · reference/ — the sandhi layout, copied)
        ▼
 ⑤  MANIFEST + TESTS  datasets.json row (same pass) + invariant tests
        │
        ▼
 ⑥  EXPORT / LAST MILE   Anki .apkg + a stable JSON item shape the Systema LMS
                          and csl-guides Quiz component consume (the showroom hop)
```

## Why this shape (grounded in what shipped)

Stages ②–⑥ are exactly the sandhi programme's own scripts, which every wave reuses **by
shape** (not by copy-paste of sandhi logic):

| Stage | Sandhi reference script | Reused as the shape for |
|---|---|---|
| ② rank | [`build_sandhi_curriculum.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_curriculum.py) (freq × class × environment, weights in [`difficulty_weights.json`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/difficulty_weights.json)) | every wave's ranking step |
| ③ curriculum | same → `sandhi_curriculum.tsv` (2,181 rules, 10 lessons) | W1a/W1b/W1c curricula |
| ③ drills | [`build_sandhi_drills.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_drills.py) | every wave's drill generator |
| ③ reference | [`build_sandhi_reference.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_reference.py) | every wave's reference page |
| ④ page | [`reading/sandhi/{curriculum,drills,reference}/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/curriculum/index.html) | every wave's `reading/<aspect>/` pages |
| ⑤ manifest | `corpus-sandhi` / `sandhi-curriculum` rows in [`datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) | every new dataset row |
| ⑥ export | [`ui/src/lib/export.js`](https://github.com/gasyoun/kosha/blob/main/ui/src/lib/export.js) (CSV/Anki) | every wave's deck export |

## The shared item schema (stage ③ drills)

Every drill item, whatever the aspect, is one JSON object so the Systema/csl-guides
quiz components need learn only one shape:

| field | meaning |
|---|---|
| `aspect` | `sandhi` · `morphology` · `vocabulary` · `samasa` · `metre` |
| `type` | `identify` · `split` · `join` · `fill` · `match` |
| `prompt` | the surface shown to the learner (Devanāgarī default, IAST/SLP1 toggle) |
| `answer` | the gold answer (verified, never fabricated) |
| `distractors` | plausible wrong options (for multiple-choice), corpus-attested where possible |
| `rank` | the item's frequency/difficulty rank (drives lesson ordering) |
| `evidence` | corpus locus / dictionary cite backing the answer (the evidence-graded principle) |
| `source_dataset` | the manifest id the item derives from (provenance) |

`answer` is **verified or the item is dropped** — the field's §6 gap #5 ("answer keys /
auto-verification for drill banks") is closed *inside* this schema by making an unverifiable
item inexpressible: no `evidence`, no item.

## The coverage metric (stage ② — the learning-outcome instrument)

Every ranked surface reports the same headline the sandhi curriculum did — *learn the
top N → cover X % of attested occurrences* — computed from the source asset's frequency
mass. This is the field's RQ4 instrument made concrete and uniform across aspects: it is
what lets "this ordering teaches faster" become a measurable claim (even though this cycle
ships the surfaces, not the papers).

## Data-flow boundaries (what derives from what)

```
 DCS CoNLL-U ─┬─▶ lemma_frequency ─────▶ W1b vocabulary curriculum ─┐
              │                                                     │
              ├─▶ paradigm engine ─────▶ W1a morphology drills ─────┤
              │   (6.9M forms)          (freq-filtered)             ├─▶ W2a difficulty scorer ─▶ graded readers
              ├─▶ compound dict ───────▶ W1c samāsa trainer ────────┤        (vocab × sandhi × morph × compound)
              ├─▶ corpus_sandhi ────────(sandhi density signal)─────┤
              └─▶ mw-roots ────────────▶ W2b roots layer ───────────┘
              vidyut-chandas ──────────▶ W3a metre-in-reading
```

W2a (difficulty scorer) is the **join point**: it consumes the rarity signals every W1
surface produces, so it is sequenced after Wave 1, and it in turn unblocks graded-reader
generation and auto-levelling. This dependency is load-bearing — the kosha data rule
("a later stage against a stale earlier one produces silently wrong output, not an error")
applies across waves, not just within one build.

## Integration surfaces (the reuse/integrate waves)

W2b (roots) and W3a (metre) do **not** own a UI. They emit a data layer (a ranked/annotated
TSV + manifest row + JSON export) and stop at stage ⑥ — the consuming UI is WhitneyRoots
and SanskritKaraoke respectively. This is the architectural expression of the prior-art
verdict: kosha contributes the *corpus-grounded ranking/annotation* those apps lack, not a
competing surface.

---

_Dr. Mārcis Gasūns_
