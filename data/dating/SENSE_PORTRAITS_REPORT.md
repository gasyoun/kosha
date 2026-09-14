_Created: 15-09-2026 · Last updated: 15-09-2026_

# Diachronic sense portraits — sense-frequency × sense-dating (H4735)

Join of `data/frequency/sense_frequency.tsv` (DCS per-sense counts, MW layer)
with `data/dating/sense_dating.tsv` (first-attestation
era buckets, PWG v1 500-headword sample, H4019), bridged through the H3744
crossdict pilot's MW inventory column. Output: `sense_portraits.tsv` —
7349 rows, one per dated sense, lossless LEFT JOIN.

## Preface caveats (carried from both inputs)

> **first_era = first attestation among the works PWG itself cites — NOT the
> origin of the meaning** (H4019). The printed PWG sense order is never
> reordered.

> **The bridge is the pilot's MW *inventory* column, not a sense alignment**
> (H3744 note verbatim: "MW/Apte columns are inventory not sense-aligned").
> A joined row means "this PWG concordance sense's inventory MW sense has a
> DCS frequency row", nothing stronger.

## Era-bucket census (recount = verify target)

| era | dated senses | of which freq-joined |
|---|---|---|
| vedic | 1342 | 146 |
| epic-sutra | 2184 | 83 |
| classical | 1107 | 20 |
| early-medieval | 1039 | 9 |
| late-medieval | 652 | 4 |
| null-undateable | 1025 | 11 |

## Join coverage (bridge provenance)

| bridge_status | rows |
|---|---|
| bridge_unaligned | 6853 |
| joined | 273 |
| bridge_no_freq | 223 |

- `joined` — pilot inventory MW sense has a frequency row; freq payload filled.
- `bridge_no_freq` — pilot carries an MW inventory id but the frequency sidecar
  has no matching (lemma, sense) row (sense unattested / numbering drift).
- `bridge_unaligned` — pilot row exists, MW inventory column empty.
- `no_pilot_row` — no pilot row for the key.

## Era × frequency (joined rows only)

| era | dated senses | freq-joined | median count_all | total count_all |
|---|---|---|---|---|
| vedic | 1342 | 146 | 17.0 | 9910 |
| epic-sutra | 2184 | 83 | 7 | 2335 |
| classical | 1107 | 20 | 27.5 | 971 |
| early-medieval | 1039 | 9 | 5 | 194 |
| late-medieval | 652 | 4 | 3.0 | 17 |
| null-undateable | 1025 | 11 | 15 | 527 |

## Lemma rollup — earliest dated sense per lemma (500 lemmas with ≥1 dateable sense; sample = 500)

| earliest era | lemmas |
|---|---|
| vedic | 393 |
| epic-sutra | 101 |
| classical | 5 |
| early-medieval | 1 |

## Top joined portraits (by DCS count_all)

| lemma | sense | first_era | count_all | sense_rank | bridge_mw_sense |
|---|---|---|---|---|---|
| rasa | 1a | vedic | 985 | 2 | mw:175486:1 |
| yad | 2a | vedic | 983 | 1 | mw:170148:1 |
| vana | 1a | vedic | 976 | 1 | mw:185717:1 |
| nara | 1a | vedic | 533 | 1 | mw:104026:1 |
| mUla | 10 | epic-sutra | 430 | 1 | mw:166324:1 |
| guru | 1a | vedic | 357 | 1 | mw:65987:1 |
| bARa | 1 | vedic | 352 | 1 | mw:144242:1 |
| Sveta | 1 | vedic | 327 | 1 | mw:224516:1 |
| rUpa | 1a | vedic | 327 | 1 | mw:179062:1 |
| vIra | 1a | vedic | 295 | 1 | mw:203565:1 |

## Feeds

Sense-resolved LSC (A57 next): era buckets give the diachronic axis, joined
count_all the frequency weight per sense. Per-sense frequency coverage is
bounded by the pilot inventory fill (273/7349
= 3.7%); widening it is the
concordance→MW alignment programme, not this join.

Rebuild + parity gate:

```bash
python scripts/build_sense_portraits.py           # rebuild
python scripts/build_sense_portraits.py --check   # era-bucket recount, exit 0
```

_Гасунс_
