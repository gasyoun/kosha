_Created: 14-07-2026 · Last updated: 14-07-2026_

# The sandhi programme — corpus-attested sandhi for Sanskrit pedagogy

**One line:** turn the Digital Corpus of Sanskrit's gold word-splits into
corpus-attested, frequency-ranked **sandhi teaching data** — then into
learner-facing tools. Shipped end to end across kosha
[v0.36.0 → v0.48.0](https://github.com/gasyoun/kosha/releases).

This is the **"what exists & how to use it"** companion to the plan,
[ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md).

---

## The pipeline

```
DCS CoNLL-U (gold Unsandhied)  ──▶  junction-rule inducer (method A)
                                        │  reproduces the hand notation:  aḥ a → o ',  m p → ṃ p,  a a → ā
                                        ▼
                              per-text sandhi tables  ──▶  merged corpus_sandhi.tsv (17 texts)
                                        │
              ┌───────────────┬─────────┴────────┬────────────────┐
              ▼               ▼                  ▼                ▼
     graded curriculum  per-class reference  reader hover     drills ✅
     (learn N → read X%) (look-up by class)  (hover a junction) (join/split/identify)
```

The **junction-rule inducer** is the core novelty: DCS gives each token its
sandhied surface (FORM) and its pre-sandhi form (`Unsandhied=`), but **no rule**.
The inducer derives the rule notation (`X Y → Z`) automatically, so it
generalises to any DCS text — where the Bhagavadgītā's 161 rules were originally
a *hand-annotated* column.

---

## Headline results

| Measure | Value |
|---|---|
| Inducer accuracy (Gītā-gold frequency-mass coverage, method A) | **96.3 %** |
| Corpus | **17 texts · ~580,000 sandhi junctions · ~9,840 distinct rules** |
| Graded-curriculum reach | **learn 23 rules → read 50 %; 79 → 80 %; 132 → 90 %** of all corpus sandhi |
| Splitter bake-off (for GRETIL, no gold) | **method C ≫ B** — neural (DharmaMitra) F1 **0.795** vs vidyut-cheda **0.282** |

---

## Phases (all data + validation shipped)

| Phase | What | Status |
|---|---|---|
| **0** — inducer | method-A junction-rule inducer over DCS `Unsandhied=` | ✅ v0.36.0 (H882) |
| **1** — coalescence | vowel-coalescence mode (MWT-aware) | ✅ v0.38.0 (H888) |
| **1.1** — MWT edge | MWT right-edge visarga | ✅ v0.39.0 (H894) |
| **1.2** — notation | spaced-notation fix → **96.3 %** Gītā-gold | ✅ v0.41.0 (H897) |
| **2** — corpus sweep | per-text + merged `corpus_sandhi.tsv` | ✅ v0.42.0 (H900) |
| **2b** — broaden | grown to 17 texts (Rāmāyaṇa, full Mahābhārata, kāvya) | ✅ v0.43.0 (H901) |
| **A/B/C** — splitters | method B (vidyut) + method C (DharmaMitra) bake-off | ✅ v0.43.0 / v0.44.0 (H903, H908) |
| **4** — pedagogy | **all four surfaces shipped** — graded curriculum + per-class reference ([H902](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H902-Opus_kosha_sandhi-phase4-pedagogy-surfaces_14.07.26.md)) · reader hover ([H917](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H917-Opus_SanskritGrammar_sandhi-reader-hover-collider_14.07.26.md), in SanskritGrammar) · drills/flashcards ([H918](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H918-Sonnet_kosha_sandhi-drills-flashcards-anki-quiz_14.07.26.md)) | ✅ v0.45.0 / v0.46.0 / v0.48.0 |
| **3** — GRETIL | extend beyond DCS using method C | planned |

---

## The A/B/C splitter bake-off (which splitter for texts with no gold)

For GRETIL and any non-DCS text there is no `Unsandhied=` gold, so the inducer
needs a splitter. Three were compared on the same texts (mode-1-only F1 vs DCS gold):

| Method | What | F1 vs gold | Precision |
|---|---|---|---|
| **A** | DCS gold splits | 1.00 (ceiling) | — |
| **B** | vidyut-cheda (offline, finite-state) | 0.22–0.28 | 0.21–0.36 |
| **C** | DharmaMitra neural (`--allow-network`) | **0.70–0.80** | **0.90–0.97** |

**Verdict: use method C for the GRETIL path (Phase 3).** Full detail:
[`scripts/compare_sandhi_methods.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_sandhi_methods.py).

---

## Datasets (public/MIT; source DCS is CC BY-SA 4.0, Oliver Hellwig / DCS)

Registered in [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json):

| id | file | what |
|---|---|---|
| `gita-sandhi` | [`data/gita/gita_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_sandhi.tsv) | Bhagavadgītā, 161 hand rules (the validation gold) |
| `corpus-sandhi` | [`data/sandhi/corpus_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/corpus_sandhi.tsv) | merged, 17 texts, global frequency ranks |
| `sandhi-curriculum` | [`data/sandhi/sandhi_curriculum.tsv`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/sandhi_curriculum.tsv) | graded syllabus (2,181 rules, 10 lessons) |
| per-text | `data/sandhi/<id>_sandhi.tsv` | one table per swept text (17) |
| weights | [`data/sandhi/difficulty_weights.json`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/difficulty_weights.json) | tunable curriculum weights (MG ruling 14-07-2026) |

---

## Scripts

| script | builds |
|---|---|
| [`dcs_sandhi_induce.py`](https://github.com/gasyoun/kosha/blob/main/scripts/dcs_sandhi_induce.py) | **method A** inducer → per-text `<id>_sandhi.tsv` |
| [`build_corpus_sandhi.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_corpus_sandhi.py) | the corpus sweep → `corpus_sandhi.tsv` |
| [`score_gita_gold.py`](https://github.com/gasyoun/kosha/blob/main/scripts/score_gita_gold.py) | Gītā-gold scoring (the 96.3 % number) |
| [`compare_sandhi_methods.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_sandhi_methods.py) | the A/B/C bake-off (`--methods ABC --allow-network`) |
| [`build_sandhi_curriculum.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_curriculum.py) | graded curriculum TSV + page |
| [`build_sandhi_reference.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_reference.py) | per-class reference page |
| [`build_gita_sandhi.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_gita_sandhi.py) | the original Gītā table (the seed, H872) |

**Rebuild everything** (needs `dcs-conllu` locally; C needs `--allow-network`):

```
python scripts/build_corpus_sandhi.py       # per-text + merged table
python scripts/build_sandhi_curriculum.py   # syllabus + curriculum page
python scripts/build_sandhi_reference.py     # per-class reference page
python scripts/score_gita_gold.py            # re-measure inducer accuracy
```

---

## Teaching pages (theme-aware, self-contained)

- [`reading/sandhi/`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/index.html) — Bhagavadgītā sandhi, frequency-ranked
- [`reading/sandhi/curriculum/`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/curriculum/index.html) — the graded syllabus
- [`reading/sandhi/reference/`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/reference/index.html) — corpus reference by class
- [`reading/sandhi/drills/`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/drills/index.html) — the practice quiz (join / split / identify)

---

## Cross-repo — who this feeds

The data is meant to be consumed elsewhere; see
[Uprava/PROJECT_INTERLINKS.md](https://github.com/gasyoun/Uprava/blob/main/PROJECT_INTERLINKS.md):

- **SanskritGrammar** — the [`SandhiCollider.jsx`](https://github.com/gasyoun/SanskritGrammar/blob/main/src/components/talmud/SandhiCollider.jsx) teaching widget + Talmud grammar sandhi chapter → the **reader-hover** surface ✅ shipped: hovering the collided result shows the induced rule + corpus frequency + a "#N most common sandhi" badge, data-driven from `corpus_sandhi.tsv` ([H917](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H917-Opus_SanskritGrammar_sandhi-reader-hover-collider_14.07.26.md), [PR #183](https://github.com/gasyoun/SanskritGrammar/pull/183)).
- **csl-guides** — hosts the sandhi-quiz; natural consumer of the curriculum + drills + reference.
- **VisualDCS / SamudraManthanam** — share the DCS source; a sandhi layer now exists over the same corpus.

---

## Next

**Phase 4 is complete — all four teaching surfaces are shipped.** The last two landed
14-07-2026: reader hover in SanskritGrammar (`SandhiCollider.jsx`, data-driven from
`corpus_sandhi.tsv` — [H917](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H917-Opus_SanskritGrammar_sandhi-reader-hover-collider_14.07.26.md),
[PR #183](https://github.com/gasyoun/SanskritGrammar/pull/183)) and drills/flashcards here
(396 items over the 132 curriculum rules, JSON/TSV + Anki + web quiz —
[H918](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H918-Sonnet_kosha_sandhi-drills-flashcards-anki-quiz_14.07.26.md),
[PR #102](https://github.com/gasyoun/kosha/pull/102)).

The open direction is now **Phase 3 (GRETIL)** — extend coverage beyond DCS using method C.

Full handoff history: [Uprava/handoffs](https://github.com/gasyoun/Uprava/blob/main/handoffs/README.md) (H882, H888, H894, H897, H900, H901, H903, H908, H902, H917, H918).

---

_Dr. Mārcis Gasūns_
