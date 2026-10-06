# ISCLS9_B3_WSD_HYBRID_H6048.md — metadoc

_Created: 06-10-2026 · Last updated: 06-10-2026_

## Purpose

Companion record for
[ISCLS9_B3_WSD_HYBRID_H6048.md](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_HYBRID_H6048.md),
the H6048 MFS+LLM hybrid WSD attempt. The subject document answers one
question: **can a corpus-MFS floor plus an LLM on the ambiguous tail beat the
84.3% corpus-MFS baseline on the frozen B3 set with McNemar significance?**
(No: honest negative after 4 tries — best 83.0%, p=0.52; the same lane also
lands the H6047-prescribed context-join fix and re-measures the LLM arm
in-context at 62.3%.)

## Audience & use

- ISCLS-9 B3 paper (private): the LLM-vs-MFS comparison must quote 62.3%
  (true context), not H5877's frozen 54.3% (broken context); the hybrid
  negative + try ledger is the paper's "no cheap LLM lift" evidence.
- Successor work on WSD accuracy: §5 lists the three levers (full glosses,
  larger B3, override-precision calibration) with the measured ceilings.
- H5556 (DSPy lane): boundary statement in §6 — prompts vs decision
  architecture; no harness or gold overlap.

## Maintenance

- Regenerate: `python scripts/wsd_h6048_hybrid.py build && run-llm && tune &&
  score --try 3 --tail top2_sonnet5 --tail-model anthropic/claude-sonnet-5 &&
  validate` (validate = PASS, MFS continuity vs H5877 enforced). Tail lanes:
  `run-tail --tag … --model … [--prior-hint]`; try history in
  `data/eval/wsd_h6048_hybrid/tries_ledger.json`.
- Do not hand-edit `scores.json` / `per_item.tsv` / `tries_ledger.json`;
  regenerate via the script. H5877 artifacts in `data/eval/wsd_iscls9/`
  stay frozen (H1588 precedent).
- The H6047 taxonomy doc carries a dated banner pointing here; its 06-10
  numbers are historical, not to be rewritten.

## Related

- Baseline + frozen lane: [ISCLS9_B3_WSD_GOLD_EVAL.md](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_GOLD_EVAL.md)
- Error taxonomy input: [ISCLS9_B3_WSD_ERROR_TAXONOMY.md](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_ERROR_TAXONOMY.md)
- Handoffs: [H6048](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6048-GLM_kosha_wsd-hybrid-mfs-llm_04.10.26.md),
  [H6047](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6047-GLM_kosha_b3-wsd-error-analysis_04.10.26.md),
  [H5556](https://github.com/gasyoun/Uprava/blob/main/handoffs/H5556-OxAlpha_kosha_dspy-wsd-definitions_29.09.26.md)

_Гасунс_
