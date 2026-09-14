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
| null-undateable | 1025 | 0 |

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
| vedic | 1342 | 146 | 88.0 | 156119 |
| epic-sutra | 2184 | 83 | 14 | 26027 |
| classical | 1107 | 20 | 67.5 | 14967 |
| early-medieval | 1039 | 9 | 21 | 683 |
| late-medieval | 652 | 4 | 3.0 | 119 |

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
| yad | 2a | vedic | 61116 | 1 | mw:170148:1 |
| ka | 2 | vedic | 13754 | 1 | mw:41332:1 |
| rUpa | 1a | vedic | 8352 | 1 | mw:179062:1 |
| yadi | 1a | epic-sutra | 6440 | 1 | mw:170219:1 |
| puruza | 1b | classical | 6159 | 1 | mw:126438:1 |
| soma | 1a | vedic | 5335 | 1 | mw:252716:1 |
| yatra | 1a | vedic | 4733 | 1 | mw:169635:1 |
| guru | 1a | vedic | 4522 | 1 | mw:65987:1 |
| nara | 1a | vedic | 4520 | 1 | mw:104026:1 |
| maDya | 1a | vedic | 3849 | 1 | mw:156344:1 |

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
