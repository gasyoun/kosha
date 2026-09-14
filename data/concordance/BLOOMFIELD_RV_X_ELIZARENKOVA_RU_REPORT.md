# Bloomfield 1906 RV citations × Elizarenkova Russian RV — citation-to-translation join

_Created: 15-09-2026 · H4731 (Census C4) · builder: `scripts/build_bloomfield_rv_elizarenkova_join.py`_

## What this is

Every direct Ṛgveda citation in [Bloomfield's *A Vedic Concordance*](https://github.com/gasyoun/kosha/blob/main/data/concordance/bloomfield_rv_citations.tsv) (36,680 pada-level citation rows,
10,374 distinct verse keys) joined to the **published Elizarenkova Russian translation**
(SamudraManthanam `Index/Updater/Data/01_rigveda.no_tags` + `02_rigveda.no_tags`, H2863)
and to the **addressable rvlinks per-verse anchor** ([sanskrit-lexicon/rvlinks](https://github.com/sanskrit-lexicon/rvlinks), `rvMM.SSS.VV`).

The join TSV is a **pointer layer**: references + anchors + match status only.
It deliberately does **not** bulk-copy the Elizarenkova translation text — the translation
is in copyright (Т.Я. Елизаренкова, М.: «Наука», 1989+), and every Elizarenkova-derived bulk
layer in the estate is `tier: restricted` (see `sa-ru-glossary`, `pwg-ru-mdf-export` in
`data/manifest/datasets.json`). Consumers resolve the pointer at render time.

## Join counts (36680 citation rows)

| match_status | rows | meaning |
|---|---:|---|
| `elizarenkova_out_of_samudra_coverage` | 27674 | |
| `joined` | 8988 | |
| `unjoined_no_surface` | 18 | |

- Distinct joined verse keys (Elizarenkova + anchor both present): **2415**
- Samudra Elizarenkova coverage: mandalas 1, 2 only
  (2435 verse keys after pair-block expansion = the two volumes digitized under H2863).
  Citations in mandalas 3–10 get the rvlinks anchor only — Elizarenkova volumes V–X exist in
  print but are not in the Samudra digitization; that is an honest coverage boundary, not a
  join failure.
- **Verse-pair blocks handled:** in the anuṣṭubh Agni hymns 1.65–1.84 Elizarenkova's edition
  prints verse PAIRS in one block (`id="65.1"` carries verses 1-2, range title "I. 65. 1-2");
  the range title is authoritative and every covered verse is indexed to its block, so even
  verses resolve instead of falsely reporting missing.
- pratika-vs-source substring check (H896 method, 8988 applicable): y 7866 (87.5%), n 1122. The `n` residue is the same genuine orthographic variance documented in
  [BLOOMFIELD_RV_CROSSREF_REPORT.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/BLOOMFIELD_RV_CROSSREF_REPORT.md)
  (anusvara-vs-homorganic-nasal spellings etc.), now measured against a third independent digitization.

## Own-data canary — two independent Elizarenkova digitizations agree

Samudra `0?_rigveda.no_tags` (H2863) and rvlinks `rvhymns/*.html` (M. Gasūns 2018 source)
are independent digitizations of the same published translation. On all 2415 joined
verse keys, normalized RU-vs-RU similarity: mean **0.973**, share ≥ 0.85:
**97.4%** (63 below 0.85 — line-break and punctuation
variants of the same text, spot-checked; neither digitization was mutated).

## Verification — 25-citation stratified sample (seed 42)

Human-eyeball table: pratīka (Bloomfield's citation incipit) against the resolved
Elizarenkova Russian at the anchor. Full RU text stays at the pointer; excerpts ≤160 chars.

| # | citation | pratika | rvlinks anchor | Samudra RU (excerpt ≤160) |
|---|---|---|---|---|
| 1 | RV.1.26.10a | viśvebhir agne agnibhiḥ | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv01.026.html#rv01.026.10 | Вместе со всеми Атли, о Агни, Прими благосклонно, о юный (сын) силы, Эту жертву, эту речь! I, 27.… |
| 2 | RV.1.132.1c | vanuyāma vanuṣyataḥ | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv01.132.html#rv01.132.01 | С тобою, о щедрый, в (борьбе) за первую ставку, Поддержанные тобою, Индрой, мы хотим одолеть нападающих, Победить (тех,) кто хочет победить нас! В этот ближайши… |
| 3 | RV.2.1.14a | tve agne viśve amṛtāso adruhaḥ | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv02.001.html#rv02.001.14 | В тебе, о Агни, все бессмертные, не поддающиеся обману Боги (твоими) устами вкушают возлитое жертвенное возлияние. С твоей помощью наслаждаются смертные выжатым… |
| 4 | RV.2.41.2c | gantāsi sunvato gṛham | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv02.041.html#rv02.041.02 | Правя упряжками, о Ваю, приезжай! Этот прозрачный (сома) поднесен тебе. Ты всегда ездишь в дом выжимающего сому.… |
| 5 | RV.3.30.20b | candravatā rādhasā paprathaś ca | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv03.030.html#rv03.030.20 | — |
| 6 | RV.3.32.9b | sadyo yaj jāto apibo ha somam | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv03.032.html#rv03.032.09 | — |
| 7 | RV.4.14.1d | imaṃ yajñam upa no yātam acha | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv04.014.html#rv04.014.01 | — |
| 8 | RV.4.21.5a | upa yo namo namasi stabhāyan | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv04.021.html#rv04.021.05 | — |
| 9 | RV.5.12.5d | ṛjūyate vṛjināni bruvantaḥ | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv05.012.html#rv05.012.05 | — |
| 10 | RV.5.39.2c | vidyāma tasya te vayam | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv05.039.html#rv05.039.02 | — |
| 11 | RV.5.68.2c | devā deveṣu praśastā | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv05.068.html#rv05.068.02 | — |
| 12 | RV.6.12.3c | adrogho na dravitā cetati tman | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv06.012.html#rv06.012.03 | — |
| 13 | RV.6.63.6b | śubhe puṣṭim ūhathuḥ sūryāyāḥ | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv06.063.html#rv06.063.06 | — |
| 14 | RV.7.3.8a | yā vā te santi dāśuṣe adhṛṣṭāḥ | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv07.003.html#rv07.003.08 | — |
| 15 | RV.7.60.1d | tava priyāso aryaman gṛṇantaḥ | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv07.060.html#rv07.060.01 | — |
| 16 | RV.8.2.37b | indraṃ satrācā manasā | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv08.002.html#rv08.002.37 | — |
| 17 | RV.8.7.33a | o ṣu vṛṣṇaḥ prayajyūn | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv08.007.html#rv08.007.33 | — |
| 18 | RV.9.32.1b | śravase no maghonaḥ (SV. maghonām) | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv09.032.html#rv09.032.01 | — |
| 19 | RV.9.45.6a | tayā pavasva dhārayā | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv09.045.html#rv09.045.06 | — |
| 20 | RV.9.49.3c | asmabhyaṃ vṛṣṭim ā pava | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv09.049.html#rv09.049.03 | — |
| 21 | RV.10.97.1c | manai nu babhrūṇām aham | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv10.097.html#rv10.097.01 | — |
| 22 | RV.10.114.10c | śramasya dāyaṃ vi bhajanty ebhyaḥ | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv10.114.html#rv10.114.10 | — |
| 23 | RV.10.135.1c | atrā no viśpatiḥ pitā | https://sanskrit-lexicon.github.io/rvlinks/rvhymns/rv10.135.html#rv10.135.01 | — |
| 24 | RV.16.36.1c | indraṃ huve marutaḥ parvatāṃ apa | — | — |
| 25 | RV.16.85.10a | mano asyā ana āsīt | — | — |

## Residue — citations no surface can answer (18 distinct verse keys)

These `unjoined_no_surface` keys are named, not silently dropped (status column keeps them
queryable in the TSV):

| key | class |
|---|---|
| RV.3.3.18 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.3.25.8 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.4.19.19 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.5.87.22 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.6.96.6 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.7.8.19 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.7.85.8 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.8.87.20 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.8.99.20 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.8.112.4 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.9.6.29 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.10.3.8 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.10.32.10 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.10.42.14 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.10.72.11 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.10.127.13 | verse number beyond the standard text's count for this hymn (edition-variant numbering) |
| RV.16.36.1 | outside the 10-maṇḍala canon (khila/parishiṣṭa or concordance-internal numbering) |
| RV.16.85.10 | outside the 10-maṇḍala canon (khila/parishiṣṭa or concordance-internal numbering) |

## Limitations

- Pada-granular RU line mapping (which Russian line answers pāda c of a quoted pair) is the
  separate H2850 judgment surface (PWG cards); this census join is verse-granular by design —
  the pada_letter column is carried through untouched for that downstream use.
- rvlinks anchors are verified to exist (10552 anchors parsed); anchor stability is
  upstream's (sanskrit-lexicon org), URL shape `rvhymns/rvMM.SSS.html#rvMM.SSS.VV`.
- Valakhilya hymns (RV 8.49–59) participate normally if cited; they are within rvlinks'
  1028-hymn layout.

## Reproduce

```
python scripts/build_bloomfield_rv_elizarenkova_join.py   # defaults resolve sibling repos
```

Deterministic (seed 42); inputs read-only; no network.
