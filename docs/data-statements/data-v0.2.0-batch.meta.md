# Data statement — `data-v0.2.0` batch (33 datasets)

_Created: 19-07-2026 · Last updated: 19-07-2026_

Consolidated data statement (Bender & Friedman 2018 / Gebru et al. 2021 form,
batched) for the 33 datasets entering the
[`data-v0.2.0`](https://github.com/gasyoun/kosha/releases/tag/data-v0.2.0)
catch-up release, cut by H1264 (W1c, 19-07-2026). Full per-field schema for
each dataset already lives in its own manifest row
([`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) —
`keying`/`builder`/`notes`/`consumers`); this document covers what the manifest
row does not: the batch-level composition, provenance and licensing summary.

**Scope decision, stated rather than silently applied.** Existing released
rows (`data-v0.1.0`) each carry an individual `docs/data-statements/<id>.meta.md`.
Writing 33 individual statements for this catch-up batch was out of proportion
to H1264's scope (a schema-hardening handoff, not a per-dataset documentation
project) and its own 6-turn stop condition. This single consolidated document
is the deliberate substitute; splitting any row out into its own statement
later (mirroring the `mw-roots` pattern) remains open follow-on work, not a
gap hidden by this batching.

## Composition

| id | title | format | rows | asset |
|---|---|---|---|---|
| `dict-corpus-concordance` | CDSL headword ↔ DCS corpus concordance (B1) | tsv | 74,520 | `dict_corpus_concordance.tsv` |
| `parallel-passage-concordance` | Bloomfield-style parallel-passage concordance (B3) | tsv | 153,045 | `parallel_passage_concordance.tsv` |
| `bloomfield-rv-citations` | Bloomfield 1906 Vedic Concordance — Ṛgveda pratīka index | tsv | 36,680 | `bloomfield_rv_citations.tsv` |
| `mw-defgen-eval-sample` | MW definition-generation eval — frozen sample + scored baselines (H730) | tsv+jsonl | 500 | `data/eval/defgen/frozen_sample.tsv` |
| `dcs-reading-pack-nala-1/2/3` | DCS reading packs — Nalopākhyāna 1–3 (MBh 3.50–3.52) | json | 65/61/51 | `reading/data/nala-{1,2,3}.json` |
| `dcs-reading-pack-hitopadesa-0` | DCS reading pack — Hitopadeśa, Prāstāvika | json | 125 | `reading/data/hitopadesa-0.json` |
| `dcs-reading-pack-kiratarjuniya-1` | DCS reading pack — Kirātārjunīya 1 (Bhāravi) | json | 92 | `reading/data/kiratarjuniya-1.json` |
| `kosha-srs-deck-b1-demo` | SRS deck — Rung B1 demo (Nala-1 vocabulary) | json | 164 | `data/srs/srs-deck-b1-demo.json` |
| `gita-gold-master` | Bhagavadgītā gold word-by-word analysis (18 adhyāyas) | tsv | 9,092 | `data/gita/gita_gold_master.tsv` |
| `gita-morphology-gold` | Bhagavadgītā gold morphology + compound dataset | tsv | 9,091 | `data/gita/gita_morphology_gold.tsv` |
| `gita-inflection-qa` | Gita inflection-engine divergence ledger (E1) | tsv | 1,279 | `data/gita/gita_inflection_divergences.tsv` |
| `gita-reading-pack` | Bhagavadgītā reading packs (18 adhyāyas, gold) | js | 701 | `reading/data/gita-1.js … gita-18.js` |
| `gita-sandhi` | Bhagavadgītā sandhi, frequency-ranked | tsv | 161 | `data/gita/gita_sandhi.tsv` |
| `gita-etymology` | Bhagavadgītā etymology notes | tsv | 101 | `data/gita/gita_etymology.tsv` |
| `sanskrit-upasarga-semantics` | Root × preverb (upasarga) semantics | tsv | 214 | `data/gita/upasarga_semantics.tsv` |
| `pronoun-corrections` | Curated pronoun-paradigm corrections (E1/W4) | tsv | 208 | `data/gita/pronoun_corrections.tsv` |
| `sandhi-curriculum` | Graded sandhi teaching syllabus | tsv | 2,181 | `data/sandhi/sandhi_curriculum.tsv` |
| `sandhi-drills` | Sandhi join/split/identify drills | json | 396 | `data/sandhi/sandhi_drills.json` |
| `corpus-sandhi` | Corpus sandhi, frequency-ranked across 17 texts | tsv | 9,840 | `data/sandhi/corpus_sandhi.tsv` |
| `vocab-curriculum` | Frequency-graded vocabulary syllabus | tsv | 6,667 | `data/frequency/vocab_curriculum.tsv` |
| `vocab-drills` | Vocabulary recognition/recall drills | json | 13,334 | `data/frequency/vocab_drills.json` |
| `morphology-curriculum` | Corpus-attested paradigm syllabus | tsv | 7,134 | `data/morphology/morphology_curriculum.tsv` |
| `morphology-drills` | Morphology fill/match drills, corpus-evidence-linked | json | 12,000 | `data/morphology/drills.json` |
| `roots-frequency-curriculum` | Root frequency + attestation curriculum (W2b) | tsv | 629 | `data/roots/roots_frequency.tsv` |
| `samasa-trainer` | Samāsa (compound) analysis trainer | tsv | 759 | `data/samasa/samasa_curriculum.tsv` |
| `reading-pack-difficulty` | Reading-pack difficulty scores (W2a) | tsv | 5 | `data/difficulty/reading_pack_difficulty.tsv` |
| `gita-reading-pack-difficulty` | Gita difficulty, reduced 3-axis ordering (W2a follow-up) | tsv | 18 | `data/difficulty/gita_reading_pack_difficulty.tsv` |
| `reading-pack-metre` | Per-verse metre annotation (W3a) | tsv | 1,095 | `data/metre/reading_pack_metre.tsv` |
| `vidyut-chandas-meters` | vidyut-chandas metre definitions (vendored) | tsv | 144 | `data/vidyut/chandas/meters.tsv` |
| `morph-signature-freq` | DCS morphological-form frequency table | tsv | 840 | `data/difficulty/morph_signature_freq.tsv` |
| `morphology-attestation-audit` | Generated↔attested morphology audit (A3, W1b, H1262) | tsv | 401,368 | `morph_attest_AG.tsv` |

## Provenance

Three source families:

1. **DCS corpus derivatives** (concordances, reading packs, sandhi/morphology
   frequency tables) — built from Oliver Hellwig's Digital Corpus of Sanskrit.
2. **Bhagavadgītā gold layer** (`gita-*`) — kosha's own hand/LLM-curated gold
   annotation over the public-domain Gītā text, cross-checked against the DCS
   corpus (E1 series) and Vidyut-derived morphology.
3. **Vendored/derived reference tables** (`vidyut-chandas-meters`,
   `bloomfield-rv-citations`) — `vidyut-chandas` (MIT-licensed, code+data) and
   Bloomfield's 1906 *Vedic Concordance* (public domain, pratīka index only,
   no verse text bundled).

Builders and per-row curation history are in each row's manifest `builder` /
`notes` field — not duplicated here.

## Licensing

- Ancient-text-derived content (Gītā gold layer, Bloomfield index) rests on a
  public-domain source text; kosha's own annotation/curation layer is
  **CC BY-SA 4.0** (kosha's standing data-release default, inherited from
  Cologne's ShareAlike per `LICENSE-DATA.md`).
- DCS-sourced rows (concordances, reading packs, DCS-derived frequency
  tables): treated as **CC BY-SA 4.0**, the conservative default this plan set
  already applies pending W1a's resolution of the DCS BY-vs-BY-SA
  self-contradiction (`docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md` §3 — "until
  then A4 is treated as BY-SA — safe under either answer"). The same
  conservative default is applied here for the same reason; W1a's finding, once
  landed, may relax this to BY 4.0 for these rows.
- `vidyut-chandas-meters` — MIT (matches `vidyut`'s own code license per
  [`data/manifest/external_tools.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json)).
- No row in this batch touches Heritage/LGPLLR-gated content —
  `heritage-forms-crosswalk-extras` is confirmed still `restricted` and is not
  part of this release (see the accompanying
  [publish-safety-check record](https://github.com/gasyoun/kosha/blob/main/docs/publish-safety-checks/data-v0.2.0_19.07.26.md)).

## Known caveats

- `dcs-reading-pack-*` / `gita-reading-pack` / `sandhi-*` / `morphology-*`
  rows are pedagogical derivations, not independently peer-reviewed corpora —
  treat difficulty scores and drill items as curriculum-design artifacts, not
  ground truth.
- `morphology-attestation-audit` (H1262) — a generated-vs-attested join; read
  its own build report for false-positive/false-negative rates before citing
  match rates from it directly.
