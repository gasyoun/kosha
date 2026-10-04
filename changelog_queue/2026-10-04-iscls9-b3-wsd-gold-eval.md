- **ISCLS-9 B3 — gold-scored gloss-grounded WSD eval + full-paper draft landed (H5877, OxAlpha lane executed by GLM-5.3-Flash `zai-coding-plan/glm-5.3-flash` via ZCode).** The WSD track left open by
  [DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md)
  next-steps #2 is closed with a fully deterministic, in-data gold: DCS `m_wordsem`
  annotations (531,747 tagged tokens) resolved onto MW sense divisions via the committed
  WordSem→MW map, held out by a **pinned crc32 fold** — the H1588 spine's `hash()`-keyed
  split is process-randomised under CPython and not byte-reproducible (integrity finding
  recorded in the protocol doc; H1588 artifacts stand, not rewritten). On 300 polysemous
  held-out items from the same 500-headword frozen universe as the defgen track, the
  gloss-grounded `deepseek/deepseek-chat` arm scores **54.3 % vs the corpus-frequency MFS
  baseline's 84.3 %** (floor 31.9 %; exact McNemar p < 0.0001, 10 vs 100 discordant) — an
  honest negative that locates the difficulty in sense granularity and usage priors, and
  the load-bearing result for the ISCLS-9 full paper. New:
  [scripts/wsd_iscls9_eval.py](https://github.com/gasyoun/kosha/blob/main/scripts/wsd_iscls9_eval.py)
  (build/run-llm/score/**validate** — validate recomputes every committed score and PASSES
  only on exact match),
  [data/eval/wsd_iscls9/](https://github.com/gasyoun/kosha/tree/main/data/eval/wsd_iscls9)
  (items + meta with SHA-256 of all inputs incl. the 5.7 GB DCS dump, LLM outputs 300/300
  parsed, scores, per-item),
  [docs/ISCLS9_B3_WSD_GOLD_EVAL.md](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_GOLD_EVAL.md)
  (+ `.meta.md`) and the paper draft
  [papers/iscls9_b3/](https://github.com/gasyoun/kosha/tree/main/papers/iscls9_b3)
  (ISCLS template `iscls.tex`/`scl.sty`/`acl.bst` + fonts, 6-page xelatex build clean,
  visual gate 6/6; numbers verified against artifacts by the standing DeepSeek verifier —
  one rounding-mode false-fail on A2 token-F1: raw 0.2935 → paper 0.294 half-up per the
  of-record protocol). Track-1 defgen numbers reused unchanged from H730/H972/H2408.
  SIGNOFF_B3_author_pass.md prepared — MG gates: abstract 10-10, read-and-sign 17-10,
  CMT3 submission 20-10 (GTD ISCLS-9).
