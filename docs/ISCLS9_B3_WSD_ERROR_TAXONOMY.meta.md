# ISCLS9_B3_WSD_ERROR_TAXONOMY.md — metadoc

_Created: 06-10-2026 · Last updated: 06-10-2026_

## Purpose

Companion record for
[ISCLS9_B3_WSD_ERROR_TAXONOMY.md](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_ERROR_TAXONOMY.md),
the H6047 error taxonomy of every LLM miss on the frozen B3 WSD set. The subject
document answers one question: **why does the gloss-grounded LLM arm trail
corpus-MFS — and is the 54.3% number even measuring in-context WSD?** (It is not:
a sentence-id key-space mismatch showed the LLM the wrong context sentence in
298/300 items; the score measures a context-free gloss-prior policy.)

## Audience & use

- H6048 (MFS+LLM hybrid): precondition list — fix the join, re-run the LLM arm
  before hybrid tuning; soft tags define the measurable headroom classes
  (gold_top1_missed 73%, gloss_deficit 44.5%).
- ISCLS-9 B3 paper (private repo): error-analysis section input; the
  54.3-vs-84.3 comparison needs re-measurement post-fix.
- New paper-ID (ruled A2=+2): the wrong-context finding + taxonomy tables are the
  citable internal evidence base.

## Maintenance

- Regenerate: run `data/eval/wsd_iscls9/error_taxonomy.ipynb` top-to-bottom with
  `KOSHA_DCS_SQLITE` pointing at `dcs_full.sqlite` (stdlib only; outputs are
  committed). Rewrites `error_taxonomy.tsv` + `taxonomy_summary.json` in place.
- Do not hand-edit the taxonomy outputs; thresholds live in
  `taxonomy_summary.json → parameters` and changing them is an analysis decision,
  not a copy-edit.
- After H6048 re-runs the LLM arm on fixed contexts, this doc's primary-class
  table becomes historical (ctx_mismatch collapses); add a dated banner then,
  do not rewrite the 06-10 numbers.

## Related

- Protocol + first results: [ISCLS9_B3_WSD_GOLD_EVAL.md](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_GOLD_EVAL.md)
- Frozen inputs: `data/eval/wsd_iscls9/` (items.jsonl, per_item.tsv, scores.json — H5877)
- Handoffs: [H6047](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6047-GLM_kosha_b3-wsd-error-analysis_04.10.26.md),
  [H6048](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6048-GLM_kosha_wsd-hybrid-mfs-llm_04.10.26.md)

_Гасунс_
