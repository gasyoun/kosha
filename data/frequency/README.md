# kosha frequency layer

_Created: 02-07-2026 · Last updated: 02-07-2026_

A per-lemma corpus-frequency **sidecar feed** for kosha, keyed by `lemma_slp1`
(SLP1, `sanskrit-util`-normalised) so it joins directly onto the kosha lemma spine
([`lemmas.slp1`](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md), D1) with
no re-transcoding. Built by
[`build_frequency_layer.py`](https://github.com/gasyoun/kosha/blob/main/data/frequency/build_frequency_layer.py)
from the VisualDCS **M9** archive
([`archive.sqlite`](https://github.com/gasyoun/VisualDCS/blob/main/src/DCS-data-2026/import_archive.py),
gitignored — download the `archive-2026-07`
[Release asset](https://github.com/gasyoun/VisualDCS/releases) or rebuild with
`python import_archive.py freq`).

## Why a sidecar, not a column

kosha's data layer is not built yet (D1–D4 unstarted as of 02-07-2026), so there are
no lookup entries to carry a frequency column. The feed is emitted now as an
independently-rebuildable asset; kosha's D1/D2 load **LEFT-JOINs**
[`lemma_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv)
onto its `lemmas` table at build time (a lemma with no frequency row simply carries
nulls). This also lets the same feed drive the pwg_ru slice ordering
([`build_pwg_freq_order.py`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/build_pwg_freq_order.py)).

## Columns (`lemma_frequency.tsv`, 83,277 rows)

| column | meaning | source in archive.sqlite |
|---|---|---|
| `lemma_slp1` | join key (SLP1) | — |
| `count_all` | whole-corpus token count (SUMMED across POS rows) | `period_freq` `period='ALL-corpus'` (`Leonchenko/Прил3`) |
| `grammar_all` | dominant part-of-speech tag | same row with the largest single count |
| `rank_all` | dense rank over `count_all`, descending (1 = most frequent) | derived |
| `periods` | compact per-period vector, `period=count` pipe-joined, chronological | `period_freq` `source='QL/FRQ_P'` |
| `periods_sum` | sum of the per-period counts (a second, independent DCS extraction) | `period_freq` `source='QL/FRQ_P'` |
| `coverage_pct` | Leonchenko per-lemma corpus-coverage weight (blank if absent) | `core_vocab` `source='Leonchenko/Сборное'` |
| `core_rank` | Leonchenko learn-these-first rank (blank if absent) | `core_vocab` `source='Leonchenko/Сборное'` |

`count_all` is the canonical single frequency number. 59,282 rows carry it; the
remaining rows have only a period vector (a lemma present in the DCS-coded period
table but not the whole-corpus `Прил3` list) and are ranked by `periods_sum` **after**
all counted lemmas so nothing with a real signal is unranked. 7,120 rows carry
`coverage_pct`.

> `coverage_pct` is a per-lemma coverage **weight**, not a running cumulative — the
> rank-1 lemma has the largest weight and it decreases down the list. Carry it as-is;
> do not read it as "cumulative % of corpus covered so far".

## Lemma-key overlap (validation)

- **73.7 %** of the 83,277 archive freq-lemmas match the kosha spine
  ([`union_headwords.tsv`](https://github.com/gasyoun/SanskritLexicography/blob/master/HeadwordLists/union/union_headwords.tsv),
  323,425 SLP1 keys); they are **19.0 %** of the spine (frequency data is inherently
  sparser than the headword union — most dictionary headwords never occur in the DCS
  corpus).
- **26.3 %** (21,937) of archive freq-lemmas are **not** in the spine: DCS stores
  preverb-compound and causative-derivative lemmas as single tokens
  (`ABaraRAy`, `ABAsay`, `ABAzin`, …) that are not dictionary headwords. This is the
  known DCS-granularity mismatch documented in
  [`build_dcs_freq.py`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/build_dcs_freq.py);
  such rows are harmless — a LEFT JOIN on `lemmas.slp1` never surfaces them.
- **40.7 %** of the 94,074 PWG headwords carry a freq signal — the high-frequency
  ones, which is exactly what the slice ordering needs first.

## Rebuild

```
python build_frequency_layer.py            # -> lemma_frequency.tsv (+ .meta.json)
python build_frequency_layer.py --selftest
```

Consumes `archive.sqlite` read-only; never rebuilds it. Model provenance for this
build: **Opus 4.8 (`claude-opus-4-8`)**, 02-07-2026.

_Dr. Mārcis Gasūns_
