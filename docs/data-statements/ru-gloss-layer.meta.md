# Data statement — inline Sanskrit→Russian gloss layer (`ru-gloss-layer`)

_Created: 19-07-2026 · Last updated: 19-07-2026_

Data statement for the `ru-gloss-layer` dataset served by the kosha reading packs.
Manifest row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
Built by
[scripts/build_ru_gloss_layer.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_ru_gloss_layer.py)
(W-RU-a / [H1278](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1278-Opus_kosha_pedagogy-wave-ru-inline-gloss-reader_19.07.26.md)).

## Composition & counts

2,958 rows in
[`data/ru_gloss/ru_gloss_layer.tsv`](https://github.com/gasyoun/kosha/blob/main/data/ru_gloss/ru_gloss_layer.tsv),
one per (reading pack, sentence, token index) across the five built packs (nala 1–3,
hitopadeśa, kirātārjunīya). TSV, UTF-8, 9 columns:

| Column | Content |
|---|---|
| `pack` | reading-pack slug |
| `sent_n` / `sent_sub` | sentence counter / sub-counter within the pack |
| `tok_idx` | 0-based token index in the sentence |
| `form_slp1` | the token surface form in SLP1 |
| `surface_ru` | Russian rendering of the attested **surface form** |
| `lemma_ru` | Russian rendering of the **lemma / stem** |
| `root_ru` | Russian rendering of the **verbal root** (verbs only) |
| `layer_hit` | which layers resolved (`surface+lemma+root` … `none`) |

The same three glosses are inlined additively into each pack token as
`gloss_ru: {surface, lemma, root}`; the English `gloss` field is left untouched.
Measured **lemma-layer coverage: 95.6%** (report:
[reading/RU_GLOSS_COVERAGE.md](https://github.com/gasyoun/kosha/blob/main/reading/RU_GLOSS_COVERAGE.md)).

## Source provenance & rights

Joined from the **public site-tier** layers of
[gasyoun/SanskritRussian](https://github.com/gasyoun/SanskritRussian) — the
`surface_glossary.tsv` (190,838 forms), `lemma_glossary.tsv` (40,370 lemmas) and
`root_glossary.tsv` (2,021 roots) that are tracked and served on that repo's GitHub
Pages site, plus its public `dcs_lemma2root.tsv` map.

**Rights gate (PLAN decision 14).** Only that public subset is read. The restricted
upstream alignment it derives from —
``RussianTranslation/src/corpus_lexicon.jsonl``
(1,091,528 word-aligned tokens) — is **not** an input here and stays local-only.
Run [/publish-safety-check](https://github.com/gasyoun/claude-config/blob/main/commands/publish-safety-check.md)
before any site deploy.

SanskritRussian's glossaries are themselves DCS-derived (CC BY 4.0) with Russian
renderings from the aligned corpus; this derivative ships under the public tier's
**CC BY-SA 4.0**, consistent with the rest of the kosha public data hub.

## Limitations

- Coverage is a lemma-layer join, not a per-passage disambiguation: a homograph is
  attributed to its highest-count lemma (SanskritRussian's own homograph handling).
- The uncovered ~4.4% is the rare long tail — proper names (naiṣadha, kaunteya),
  sandhi-altered stems, and causatives — matching SanskritRussian's failure typology.
- The Bhagavadgītā packs the wave anticipated are **parked**: the BhG is absent from
  the DCS full corpus (Mahābhārata book 6 skips adhyāyas 23–40), so the layer applies
  to the five packs that exist.

_Dr. Mārcis Gasūns_
