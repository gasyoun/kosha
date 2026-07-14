_Created: 14-07-2026 · Last updated: 14-07-2026_

# Roadmap — kosha pedagogy surfaces (2026–2027)

Waves for kosha's learner-facing pedagogy build layer. Cover + decisions:
[`PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md).
Field definition (consumed, never restated):
[`DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md`](https://github.com/gasyoun/SanskritGrammar/blob/main/DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md).
Each deliverable states what unblocks it and its build-vs-reuse verdict.

The unifying shape every wave follows is the **pedagogy-surface contract** in
[`docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md):
a kosha data asset → frequency/difficulty ranking → graded curriculum + drills + reference
page → manifest row + tests → Anki/JSON export. The sandhi programme already runs it
end-to-end; every wave below instantiates it for one more aspect.

## Wave 0 — Sandhi ✅ (shipped, the reference implementation)

The corpus-sandhi pedagogy programme
([`SANDHI_PROGRAMME.md`](https://github.com/gasyoun/kosha/blob/main/SANDHI_PROGRAMME.md),
[`ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md))
is done end-to-end: junction-rule inducer (96.3 % Gītā-gold), 17-text corpus table,
graded curriculum ("learn 23 rules → read 50 %"), per-class reference, drills/flashcards.
It **is** the template — Wave 1 copies its scripts' shape. *Unblocked by:* nothing; done
(H882–H918).

## Wave 1 — data-ready surfaces (2026 H2)

| Deliverable | Verdict | Unblocked by | Handoff |
|---|---|---|---|
| **W1a — Morphology drills.** Graded declension/conjugation drill + answer-keyed quiz + Anki export over the shipped paradigm engine; drilled forms **prioritised by attested frequency** (stop drilling forms the corpus never shows — field §3.2 RQ1) | 🟢 BUILD | paradigm engine + [`ParadigmTable.svelte`](https://github.com/gasyoun/kosha/blob/main/ui/src/components/ParadigmTable.svelte) + [`build_paradigms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_paradigms.py) + Anki [`export.js`](https://github.com/gasyoun/kosha/blob/main/ui/src/lib/export.js) + DCS form-frequency (all exist) | [H946](https://github.com/gasyoun/Uprava/blob/main/handoffs/H946-Sonnet_kosha_pedagogy-w1-morphology-drills_14.07.26.md) |
| **W1b — Vocabulary frequency curriculum.** "Learn the N most frequent lemmas → read X % of the corpus" — a graded syllabus TSV + theme-aware page, the sandhi-curriculum method applied to words | 🟢 BUILD | [`lemma_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv) (`core_rank` + `coverage_pct`) + [`build_sandhi_curriculum.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_curriculum.py) as the shape (exist) | [H947](https://github.com/gasyoun/Uprava/blob/main/handoffs/H947-Sonnet_kosha_pedagogy-w1-vocabulary-frequency-curriculum_14.07.26.md) |
| **W1c — Samāsa (compound) trainer.** Graded compound-analysis surface (TP/BV/DV/KD) over the compound data + Gītā gold; identify-type + split drills; cross-links the csl-guides `samasa-quiz` rather than re-authoring it | 🟢 BUILD | `dcs-compound-dictionary` (37,333, manifest) + [`gita_morphology_gold.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_morphology_gold.tsv) compound column (exist) | [H948](https://github.com/gasyoun/Uprava/blob/main/handoffs/H948-Sonnet_kosha_pedagogy-w1-samasa-compound-trainer_14.07.26.md) |

## Wave 2 — the difficulty spine + roots (2027 H1)

| Deliverable | Verdict | Unblocked by | Handoff |
|---|---|---|---|
| **W2a — Graded-reader expansion + difficulty scorer.** Build the **difficulty scorer** (the gap field §3.4/§6 names — score any text on vocab-frequency × sandhi-density × morphology-rarity × compound-load) then scale reading packs beyond Nala 1, ordered by it | 🟢 BUILD | [`build_reading_pack.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_reading_pack.py) (Nala shipped) + W1a/W1b rarity signals + corpus_sandhi density | [H949](https://github.com/gasyoun/Uprava/blob/main/handoffs/H949-Opus_kosha_pedagogy-w2-graded-reader-difficulty-scorer_14.07.26.md) |
| **W2b — Roots frequency + corpus attestation.** Do **not** rebuild a roots app — [WhitneyRoots](https://github.com/gasyoun/WhitneyRoots) owns the 935-root explorer + quiz. kosha's contribution: frequency-rank the roots and link each to its attested corpus forms (concordance A1/A3), export a "learn roots in this order" layer WhitneyRoots/Systema can consume | 🟡 REUSE/INTEGRATE | `mw-roots` + `dcs-verb-roots-by-class` (manifest) + [`CONCORDANCE_ROADMAP.md`](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md) A1/A3 | [H950](https://github.com/gasyoun/Uprava/blob/main/handoffs/H950-Sonnet_kosha_pedagogy-w2-roots-frequency-corpus-integration_14.07.26.md) |

## Wave 3 — metre-in-reading + script (2027 H2)

| Deliverable | Verdict | Unblocked by | Handoff |
|---|---|---|---|
| **W3a — Metre-ID wired into reading.** Do **not** rebuild a metre trainer — [SanskritKaraoke](https://github.com/gasyoun/SanskritKaraoke) owns it (wave notation + quizzes + Apte prosody). kosha's contribution: annotate the reading packs with per-verse metre (the field §3.9 gap: "metre-ID as a graded drill wired into reading") using vidyut-chandas `meters.tsv` | 🟡 REUSE/INTEGRATE | `data/vidyut/chandas/meters.tsv` + reading packs (W2a) | [H951](https://github.com/gasyoun/Uprava/blob/main/handoffs/H951-Sonnet_kosha_pedagogy-w3-metre-in-reading-integration_14.07.26.md) |
| **W3b — Script / Devanāgarī** | ⚪ REUSE (roadmap only) | [csl-guides](https://github.com/sanskrit-lexicon/csl-guides) already owns the devanāgarī/transliteration quizzes + "name-in-devanāgarī" tool; kosha adds no surface. Revisit only if a kosha-specific onboarding need appears | — |

## Wave 4 — audio (2028, external-gated agenda)

**Audio / recitation** is the ecosystem's biggest gap (field §3.7) but needs external
content (a recorded reciter or a TTS decision) and is owned at the field/Systema level
(H912 Wave 4). kosha builds **no** audio this plan; if audio data lands, kosha's role is
only to align it to the reading packs. Left as an agenda pointer, not a wave.

## Non-goals (explicit — do not re-propose)

- **Not** a second field metadoc — [the field doc](https://github.com/gasyoun/SanskritGrammar/blob/main/DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md) is the single org-wide one; this plan cross-links it.
- **Not** a new SRS engine — Systema "Saraswati" (FSRS) + kosha Anki export already exist; surfaces emit items, they do not schedule them.
- **Not** rebuilding roots (WhitneyRoots), metre (SanskritKaraoke), or script (csl-guides) surfaces — integrate via their data/API.
- **Not** producing audio in-house; **not** a course/LMS — Systema owns delivery.
- **Not** papers this cycle — surfaces + measurement instrumentation only (the field's paper track lives in H912/A62/A32/A60).
- **Not** touching csl-orig, the shipped sandhi data, or sibling-repo source (the fence).

---

_Dr. Mārcis Gasūns_
