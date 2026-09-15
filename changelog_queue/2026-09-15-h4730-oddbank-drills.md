- **H4730 (OxAlpha `opencode/z-ai/glm-5.3-flash`) — census C3 closed: the
  dcs-nominal-class-split(-adj) verdict banks have their first consumer, a new
  zaliznyak-oddbank-drills dataset.**
  [`build_zaliznyak_oddbank_drills.py`](scripts/build_zaliznyak_oddbank_drills.py)
  reads the H3984/H4011 pooled-class verdicts (VisualDCS, at build time, never
  vendored) and emits 1,722 drill items — 1,464 `classify-verdict` (one per
  resolved verdict row: is the -ant/-at pair one lexeme with two stem
  spellings, like bhagavant/bhagavat?) + 258 `odd-one-out` (three alternants
  + one `at_only`/`ant_only` oddball that does not alternate). Every item
  carries `verdict_refs` → {source_dataset, lemma_id, lemma, verdict}; the
  builder's `--check` re-resolves all of them against the live source JSONs,
  so an untraceable drill item is a build failure. 695 `unresolved` verdict
  rows are excluded, not guessed. Consumers flipped on both producer rows:
  [datasets.json](data/manifest/datasets.json).
  [Report](docs/H4730_ODDBANK_DRILLS_REPORT_15.09.26.md).
