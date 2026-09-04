# H4034 — Hitopadeśa per-text concordance pilot (Caturakarati wave C)

**Date:** 04-09-2026 · **Tier:** OxAlpha `zai-coding-plan/glm-5.3-flash` · **Box:** Mac

The Tamilex "corpus dictionary" pattern over a Sanskrit text: a full word
concordance of the Hitopadeśa (DCS text_id 189 — Hitop, 0–4, 3,432 sentences,
25,040 tokens, CC BY 4.0), each form linked back into the kosha dictionary.
The INVERSE view of the H1455 sense-attestation layer — no new join invented:
the H380 `dict_corpus_concordance` lemma join (95.5% of 7,857 distinct
(surface, lemma) forms linked to a kosha headword), the H1455
`sense_corpus_concordance` per-sense layer (1,024 forms carry numbered PWG
sense ids; absence = H1455 frame width, reported honestly), the house
`human_locus` format, the `card_token` URL encoder and the H4026 `.ls-era`
badge (early-medieval via the Dharmamitra join in `work_dates.json`) — all
consumed, not re-derived. New builder
[scripts/build_text_concordance_hitopadesa.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_text_concordance_hitopadesa.py)
writes an additive fold only:
[data/concordance/text_hitopadesa/](https://github.com/gasyoun/kosha/tree/main/data/concordance/text_hitopadesa)
— `concordance.tsv` (every occurrence, document order), a filterable
`index.html` page carrying the era badge, `MANIFEST.json` (license +
provenance, license-gated ingest discipline), `BUILD_REPORT.md` (coverage
memo: forms, occurrences, linked-vs-unlinked, residue = 4.5% DCS `-ay`
causative stems + indeclinables with no headword join) and a 10-form
hand-verified spot check against an independent per-form SQL recount —
**10/10 PASS**. H4034 gate respected: no printed-order change, no existing
surface touched. Manifest row `hitopadesa-text-concordance` added.
