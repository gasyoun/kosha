# changelog_queue — tamil-fold (H4178 flip 2), 06-09-2026

Consumed by cut_release.py at the next release cut (H3355 flow).

## [Unreleased] → Added

- **H4178 (OxAlpha `zai-coding-plan/glm-5.3-flash`) — csl-santam Tamil/Capeller/MW
  corpus fold landed in kosha (Wave-4 edge queued → live).**
  [scripts/ingest_tamil_fold.py](https://github.com/gasyoun/kosha/blob/main/scripts/ingest_tamil_fold.py)
  folds the sibling's combined `tamil(id, st, en)` corpus (325,838 rows; mwd
  166,434 / cap 37,413 / otl 117,773 / cpd 4,218 Pahlavi) into a lexicon-tagged,
  provenance-pinned fold (`data/raw_sqlite/tamil_fold.sqlite`, gitignored,
  regenerable; committed stats
  [data/tamil/fold_stats.json](https://github.com/gasyoun/kosha/blob/main/data/tamil/fold_stats.json)
  + manifest row `tamil-fold` +
  [data statement](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/tamil-fold.meta.md)).
  The mwd+cap+otl band = **321,620 entries, exactly the 08-07-2026 interlinks
  snapshot**; source pinned file-level (commit `e94ca05`, sha256). Encoding
  honesty: H1513 normalized only the TEXT export — the shipped sqlite still
  carries cp1252 cells behind the PHP runtime `iconv` workaround; the fold
  decodes per-cell UTF-8→cp1252 (12,330/651,676 cells, 6 latin-1 strays) and
  retires that workaround for kosha-side consumers. Scheme kept verbatim HK
  (otl HK-like, never auto-converted); scheme normalization + static-cache tier
  remain later Wave-4 steps this fold de-risks. `--check` mode verifies an
  existing fold against the committed stats.
