# ISCLS9_B3_WSD_GOLD_EVAL.md — metadoc

_Created: 04-10-2026 · Last updated: 04-10-2026_

## Purpose

Companion record for
[ISCLS9_B3_WSD_GOLD_EVAL.md](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_GOLD_EVAL.md),
the gold-scored completion of the WSD track. The subject document answers one question:
**how does a gloss-grounded LLM arm score against a deterministic, in-data gold
(DCS WordSem → MW), and does it beat the corpus-frequency MFS baseline?** (It does not —
54.3 % vs 84.3 %, p < 0.0001 — a load-bearing negative result for the ISCLS-9 B3 paper.)
It also documents the pinned crc32 fold and the fold-randomization integrity finding
against the H1588 spine.

## Audience

The ISCLS-9 B3 paper lane first ([H5877](https://github.com/gasyoun/Uprava/blob/main/handoffs/H5877-OxAlpha_kosha_iscls9-b3-full-paper_04.10.26.md)
— the paper's §5 WSD numbers and §6 fold note come from here), then anyone continuing the
defgen/WSD eval line. Read
[DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md)
first: same frozen headword universe, and this track consumes its outcomes (the 500-lemma
restriction) and its judge-gate discipline.

## Provenance

- **Handoff:** [H5877](https://github.com/gasyoun/Uprava/blob/main/handoffs/H5877-OxAlpha_kosha_iscls9-b3-full-paper_04.10.26.md)
  (**OxAlpha** lane) — ISCLS-9 B3 full paper. WSD track executed 04-10-2026.
- **Model:** GLM-5.3-Flash (ZCode session) — harness, run, analysis, write-up.
- **LLM arm:** `deepseek/deepseek-chat` via OpenRouter, temperature 0 (300/300 parsed).
- **Predecessors:** [H730](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H730-Fable_kosha_definition-generation-gloss-eval_11.07.26.md)
  (eval design, frozen sample), [H1588](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/)
  (WordSem→MW gold spine — its `hash()` fold nondeterminism is corrected here, not rewritten),
  [H2408](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2408-Fable_kosha_definition-gen-gloss-wsd-pilot_07.08.26.md)
  (Heritage second reference).

## Status

Active — results of record for the B3 paper; regenerate only via the listed reproduction
commands (seed 5877, committed input digests in `data/eval/wsd_iscls9/items.meta.json`).

_Гасунс_
