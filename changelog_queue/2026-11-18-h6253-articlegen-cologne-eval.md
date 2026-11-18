# 2026-11-18 — H6253 article-generation eval against Cologne MW gold

_Created: 18-11-2026 · Last updated: 18-11-2026_

- **H6253 — Cologne-gold article-generation eval:** new public dataset
  `articlegen-cologne-gold` (manifest row registered) and the reproducible
  harness behind it: 105 frozen A55-union headwords (100 main + 5 MG-canary),
  two model arms — GLM 5.3 Flash and DeepSeek 4.1 Flash — scored against
  Cologne MW v02 gold on gloss, examples, citations and inferred root.
  Deterministic metrics plus a hallucination taxonomy (unattested citations,
  wrong roots, unsupported examples, empty fields, parse failures). The
  5-article canary is an MG human act: `articlegen_score.py --canary` refuses
  without MG's labels, so the verdict stays INCONCLUSIVE rather than borrowing
  a PASS. Prior art respected: the existing defgen line (H730/H752/H972/H2408)
  scores gloss-only outputs; this unit is article-level with citations as a
  first-class field and the Cologne entry itself as gold, so no existing
  artifact was duplicated or overwritten. Protocol + results of record:
  [docs/ARTICLEGEN_COLOGNE_EVAL_PROTOCOL.md](docs/ARTICLEGEN_COLOGNE_EVAL_PROTOCOL.md).
  Executed by Hy4 flash Free (`opencode-go/hy4-flash-free`), OxAlpha retained as
  handoff filename provenance (H3688).

_Dr. Mārcis Gasūns_
