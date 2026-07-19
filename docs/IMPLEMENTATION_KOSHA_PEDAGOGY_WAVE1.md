_Created: 14-07-2026 · Last updated: 14-07-2026_

# Implementation — kosha pedagogy Wave 1 (file-level steps)

Cover: [`PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md`](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md).
Contract: [`docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md).
Acceptance: [`docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md`](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md).

Wave 1 = the three data-ready builds (H946/H947/H948). Each is independent (no cross-build
barrier) and follows the six-stage contract. Every build: author in a `git worktree` off
`origin/main`, add a `datasets.json` row in the same pass, edit `CHANGELOG.md` then
`/cut-release`, PR → merge. Windows convention:
`sys.stdout/stderr.reconfigure(encoding='utf-8')` in every script.

---

## W1a — Morphology drills ([H946](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H946-Sonnet_kosha_pedagogy-w1-morphology-drills_14.07.26.md), Sonnet 5)

**Idea:** the paradigm engine already generates the tables; this build turns them into
*graded, frequency-filtered, answer-keyed* drills. The novel move is stage ② — **drill only
forms the corpus actually attests**, in frequency order (field §3.2 RQ1: "stop drilling forms
that never appear").

1. **`scripts/build_morphology_drills.py`** (new). Read the paradigm data via the existing
   builder path ([`scripts/build_paradigms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_paradigms.py)
   output / `paradigm` shards). For each `(lemma, stem-class)` emit paradigm-cell drill items
   in the shared schema (ARCHITECTURE §item schema): `type=fill` (given lemma+case/number+gender
   or person/number/tense → produce the form), `type=match` (form → cell). Attach `evidence`
   = the DCS attestation for that form (join on `form_key()` against the attested-forms table);
   **drop any cell whose form is unattested** unless a `--include-generated` flag is set (default
   off — the honest-residue rule, mirrors the heritage `default-off` decision).
2. **Rank (stage ②).** Order lemmas by `core_rank` from
   [`data/frequency/lemma_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv);
   within a lemma, order cells by attested-form frequency. Weights (per-class, per-cell) in a
   new `data/morphology/drill_weights.json` (tunable, per the MG difficulty-weights ruling —
   never hard-code).
3. **Curriculum + reference (stage ③).** Emit `data/morphology/morphology_curriculum.tsv`
   (ordered lessons: a-stems → other vowel stems → consonant stems → pronouns → present-class
   verbs → other classes) with the coverage metric ("learn these N paradigms → cover X % of
   attested nominal/verbal tokens"). Emit `data/morphology/drills.json`.
4. **Page (stage ④).** `reading/morphology/{curriculum,drills}/index.html` — copy the
   [`reading/sandhi/curriculum/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/curriculum/index.html)
   layout; embed the ParadigmTable rendering idiom from
   [`ui/src/components/ParadigmTable.svelte`](https://github.com/gasyoun/kosha/blob/main/ui/src/components/ParadigmTable.svelte)
   as static HTML (Devanāgarī default, IAST/SLP1 toggle).
5. **Export (stage ⑥).** Extend [`ui/src/lib/export.js`](https://github.com/gasyoun/kosha/blob/main/ui/src/lib/export.js)
   (or a small script) to emit an Anki `.apkg` of the drill deck.
6. **Manifest + tests.** `morphology-drills` row in [`datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json);
   `tests/test_morphology_drills.py` (every item has verified `evidence`; no unattested form
   in default mode; coverage metric monotone).

**Prior-art fence:** reuse the paradigm engine and `ParadigmTable`; do **not** rebuild
paradigm generation, and do **not** duplicate the SanskritGrammar Talmud morphophonology
widgets (AblautMachine/SetTree) — link to them from the page instead.

---

## W1b — Vocabulary frequency curriculum ([H947](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H947-Sonnet_kosha_pedagogy-w1-vocabulary-frequency-curriculum_14.07.26.md), Sonnet 5)

**Idea:** the sandhi curriculum's exact method, applied to words. The frequency layer already
carries `core_rank` + `coverage_pct`; this build is mostly stages ③–⑥.

1. **`scripts/build_vocab_curriculum.py`** (new) — model it directly on
   [`scripts/build_sandhi_curriculum.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_curriculum.py).
   Read [`data/frequency/lemma_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv),
   sort by `core_rank`, bucket into lessons of N (default 50), emit
   `data/frequency/vocab_curriculum.tsv` (lemma · gloss · core_rank · cumulative coverage_pct ·
   lesson). Each lemma links to its kosha `/w/` dictionary card and its Anki front/back.
2. **Coverage headline.** Compute + print the "learn N lemmas → read X %" table (the analogue
   of "23 rules → 50 %"), from `coverage_pct`. This is the surface's measurable claim.
3. **Page (stage ④).** `reading/vocabulary/curriculum/index.html` (sandhi-curriculum layout);
   each lesson a card list with gloss + example + dictionary link.
4. **Drills + export.** `data/frequency/vocab_drills.json` (recognition + recall items,
   distractors from same-frequency-band lemmas); Anki export via stage ⑥.
5. **Manifest + tests.** `vocab-curriculum` row in `datasets.json`;
   `tests/test_vocab_curriculum.py` (monotone cumulative coverage; every lemma resolves to a
   card; lesson sizes correct).

**Prior-art fence:** reuse `core_rank` (do not re-derive frequency); do **not** build an SRS
scheduler (Systema "Saraswati" owns scheduling) — emit deck items only.

---

## W1c — Samāsa (compound) trainer ([H948](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H948-Sonnet_kosha_pedagogy-w1-samasa-compound-trainer_14.07.26.md), Sonnet 5)

**Idea:** teach compound analysis (tatpuruṣa / bahuvrīhi / dvandva / karmadhāraya) from the
compound data that already exists. "Data ready to be integrated" (MG).

1. **`scripts/build_samasa_trainer.py`** (new). Source: the `dcs-compound-dictionary`
   (`CompDic.csv` headwords + `cmps.csv` member breakdown, per
   [`datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json))
   for the corpus-scale item pool, and
   [`data/gita/gita_morphology_gold.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_morphology_gold.tsv)
   (hand-verified `compound` column TP/BV/DV/KD) as the **gold** item seed. Emit drill items:
   `type=identify` (compound → its type), `type=split` (compound → member breakdown), each with
   `evidence` = the attestation. Gold-seeded items carry the verified type; corpus-derived items
   carry the DCS-supplied split, flagged by provenance.
2. **Rank (stage ②).** Order by attested compound frequency (`names.csv` frequency vector);
   weights in `data/samasa/drill_weights.json`.
3. **Curriculum + reference (stage ③).** `data/samasa/samasa_curriculum.tsv` (KD/TP first —
   the transparent types — then BV/DV); `data/samasa/reference.tsv` per type with a ranked
   attested example each.
4. **Page (stage ④).** `reading/samasa/{curriculum,drills,reference}/index.html`
   (sandhi layout).
5. **Cross-link, don't duplicate.** The csl-guides `samasa-quiz`
   ([`docs/users/samasa-quiz.mdx`](https://github.com/sanskrit-lexicon/csl-guides/blob/main/docs/users/samasa-quiz.mdx))
   already exists — link to it as the hosted quiz; kosha supplies the corpus-scale graded data
   it lacks.
6. **Manifest + tests.** `samasa-trainer` row in `datasets.json`;
   `tests/test_samasa_trainer.py` (gold items match the Gītā gold column; every item has
   `evidence`; type distribution sane).

**Prior-art fence:** the empty [SamasaChakram](https://github.com/gasyoun/SamasaChakram) stub
is **not** revived here; the trainer lives in kosha with the data. Do not re-author the
csl-guides quiz.

---

## Cross-wave build discipline

- **Order within Wave 1:** none required — H946/H947/H948 are independent; run in any order or in parallel worktrees.
- **Each build is one PR**, one release, one manifest row, per the kosha agent contract.
- **The coverage metric is mandatory** on every surface (stage ②) — a surface that ships without its "learn N → cover X %" number is incomplete, not merely unpolished.
- **Honest residue** everywhere: unattested/ungold items are dropped or flagged, never silently fabricated (the field's evidence-graded principle; kosha's standing "honest residue" convention).

---

_Dr. Mārcis Gasūns_
