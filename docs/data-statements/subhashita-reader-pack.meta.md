# Data statement — beginner subhāṣita reader pack (W-RU-b)

_Created: 19-07-2026 · Last updated: 19-07-2026_

**Dataset:** `subhashita-reader-pack` — the graded beginner subhāṣita reading pack, plus
its grading spine `subhashita_difficulty.tsv` (all 7,537 sayings scored).

**Vendored files.**
[`data/subhashita/subhashita_difficulty.tsv`](https://github.com/gasyoun/kosha/blob/main/data/subhashita/subhashita_difficulty.tsv)
(the full 7,537-saying difficulty table),
[`data/subhashita/beginner_band.tsv`](https://github.com/gasyoun/kosha/blob/main/data/subhashita/beginner_band.tsv)
(the 106 curated picks),
[`data/subhashita/CURATION_NOTES.md`](https://github.com/gasyoun/kosha/blob/main/data/subhashita/CURATION_NOTES.md)
(criteria + the full 144-row reject log — no unlogged picks),
[`data/subhashita/subhashita_beginner_pack.json`](https://github.com/gasyoun/kosha/blob/main/data/subhashita/subhashita_beginner_pack.json)
(the pack: split + junction rules + metre per saying),
[`data/subhashita/subhashita_beginner_anki.apkg`](https://github.com/gasyoun/kosha/blob/main/data/subhashita/subhashita_beginner_anki.apkg)
(Anki deck: front = sandhied verse, back = split + rules + metre + translation),
and the reader page [`reading/subhashita/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/subhashita/index.html).
Regenerate: `python scripts/build_subhashita_difficulty.py` then
`python scripts/build_subhashita_pack.py` (offline once the committed DharmaMitra cache
is present); regression: `python scripts/test_subhashita_difficulty.py`.

**What it is.** A new reading-pack *family* (kosha pedagogy Wave RU, surface W-RU-b,
[H1279](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1279-Fable_kosha_pedagogy-wave-ru-subhashita-reader_19.07.26.md)):
the 106 easiest, quotable, textually sound sayings of Böhtlingk's *Indische Sprüche*
(7,537 public-domain sayings, SanskritLexicography
[F33](https://github.com/gasyoun/SanskritLexicography/blob/master/FEATURES_INDEX.md)),
difficulty-ordered so an absolute beginner meets real Sanskrit from day one. Each saying
carries: sandhi-split (DharmaMitra `unsandhied`, validated; offline vidyut-cheda
fallback), per-junction `X Y → Z` rules with corpus attestation counts from
[`data/sandhi/corpus_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/corpus_sandhi.tsv),
metre tag (vidyut-chandas strict vṛtta, else the anuṣṭubh syllable heuristic — the W3a
two-tier method), Böhtlingk's German translation, and source attribution.

**Grading.** The W2a difficulty scorer applied as a documented REDUCED variant (the H977
precedent): `difficulty = 0.5333·VOCAB + 0.4667·FUSION`, morphology axis dropped (no gold
UD analysis exists for the sayings), sandhi + compound absorbed into one FUSION axis
(a morphology-less splitter cannot tell a compound member from a sandhi fusion — one
signal, not two names). Not comparable to the 4-axis pack table or the reduced Gītā
table; it orders the 7,537 sayings among themselves only.

**Honest limitations.** A displayed split exists only where a splitter's output
rebuilds the surface via corpus-attested junction rules (the "no fabricated signal"
gate) — 56 of 1,263 chunks stay unsplit rather than guessed. `gloss.ru` is ABSENT:
the W-RU-a layer ([H1278](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1278-Opus_kosha_pedagogy-wave-ru-inline-gloss-reader_19.07.26.md))
had not shipped at build time — the pack meta records this and the pack is scheduled
for a re-run once it lands (logged re-run TODO, not a silent gap). The Anki `.apkg` is
not byte-stable across regenerations (sqlite timestamps), same as the other decks; the
TSV/JSON are. The curation reject log's 50 R1 rows double as an OCR to-fix list for
the IndischeSprueche source layer.

**Author / credit.** Grading pipeline + curation + pack build: **Dr. Mārcis Gasūns**
(H1279, Fable 5 `claude-fable-5`). Splits: DharmaMitra `unsandhied` API (cached,
committed) with vidyut-cheda fallback (Arun Prasad's vidyut).

**License / rights.** Public tier. Base text: Böhtlingk, *Indische Sprüche* (2nd ed.
1870–73) — **public domain**. Junction-rule attestation counts derive from the Digital
Corpus of Sanskrit (**CC BY 4.0**, Oliver Hellwig / DCS) — attribute DCS on any public
deck. No SanskritRussian material is included in this build (the standing Wave-RU
rights gate is therefore not triggered); `/publish-safety-check` before any site deploy.

_Dr. Mārcis Gasūns_
