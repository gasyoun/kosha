# Data statement — csl-santam Tamil/Capeller/MW corpus fold (`tamil-fold`)

_Created: 06-09-2026 · Last updated: 06-09-2026_

Data statement for the `tamil-fold` dataset of the kosha data-hub. Manifest
row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
The fold itself is regenerable working data (`data/raw_sqlite/tamil_fold.sqlite`,
gitignored) — the committed artifact is the stats pin
[data/tamil/fold_stats.json](https://github.com/gasyoun/kosha/blob/main/data/tamil/fold_stats.json)
plus the builder
[scripts/ingest_tamil_fold.py](https://github.com/gasyoun/kosha/blob/main/scripts/ingest_tamil_fold.py).
Not in any release (regenerable from the pinned source).

## Composition & counts

325,838 rows, one per entry of the csl-santam combined search corpus, tagged
by source lexicon:

| Lexicon | Rows | What it is |
|---|---|---|
| `mwd` | 166,434 | Cologne Digital Sanskrit Lexicon (Monier-Williams) |
| `cap` | 37,413 | Capeller's Sanskrit-English Dictionary |
| `otl` | 117,773 | Cologne Online Tamil Lexicon |
| `cpd` | 4,218 | Pahlavi dictionary (excluded from csl-santam's own "all" searches) |

The mwd+cap+otl band = **321,620 entries — exactly the 08-07-2026
interlinks-edge snapshot** (csl-santam → kosha Wave-4 queued edge; landed live
by H4178 flip 2). Fold schema: `tamil_fold(id, lexicon, st, en)` with
`lexicon`/`st` indexes + `fold_meta(key, value)` provenance (source commit,
sha256, counts, encoding stats, scheme notes).

## Source provenance

Producer:
[gasyoun/csl-santam](https://github.com/gasyoun/csl-santam)
`sqlite/tamil.sqlite` (single combined table `tamil(id, st, en)` where `id`
is the lexicon number; Cologne MWScan/tamil lineage). Folded read-only from
the sibling checkout by `scripts/ingest_tamil_fold.py`. Pin at fold time:
file-level commit `e94ca0559c449b7f5fa14b7de933c88f84bba8fa`, sha256
`627cc830de9618e76467d74bf1eb9118a7e9ec178dae51f8ce79fb975f16ae82`.

License: **CC BY-NC-SA 3.0** — the Cologne scan data (per csl-santam
LICENSE.md §1), stricter than kosha's public-tier default; carried in the
manifest row. Keep downstream uses non-commercial.

## Encoding & scheme honesty

- **Encoding:** the shipped sqlite still carries Windows-1252 cells behind
  csl-santam's PHP runtime `iconv` workaround (H1513/92d1670 normalized only
  the text export `sqlite/ganz_utf8.txt`). The fold decodes per-cell UTF-8
  with cp1252 fallback: 12,330/651,676 cells (1.9%) needed the fallback, 6
  strays fell to latin-1. This retires the PHP workaround for every kosha-side
  consumer.
- **Scheme:** `st`/`en` kept verbatim Kyoto-Harvard (HK); `otl` uses an
  HK-like scheme csl-santam itself never auto-converts
  (php/js/hk-input.js lines 14–17). Scheme normalization and the static-cache
  tier remain later Wave-4 steps — this fold de-risks them by landing the
  corpus queryable in kosha with provenance.

_Dr. Mārcis Gasūns_
