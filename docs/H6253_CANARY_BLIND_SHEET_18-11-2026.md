# H6253 canary — blind MG review sheet (18-11-2026)

_Created: 18-11-2026 · Last updated: 18-11-2026_

_Dr. Mārcis Gasūns_

Built under [H8433](https://github.com/gasyoun/Uprava/blob/main/handoffs/H8433-OxAlpha_kosha_h6253-mg-canary-blind-sheet_18.11.26.md) as the human-facing instrument for the [H6253](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6253-OxAlpha_kosha_llm-lexicographer-eval_08.10.26.md) canary gate (`human:MG`). The agent does **not** supply gold labels: doing so would make the reproduction check circular.

## What was built

- [`tools/build_h6253_canary_blind_sheet.py`](https://github.com/gasyoun/kosha/blob/main/tools/build_h6253_canary_blind_sheet.py) — regenerates the sheet via the canonical `csl_pyutil.render_review_sheet` emitter.
- [`tools/h6253_canary_decisions_to_labels.py`](https://github.com/gasyoun/kosha/blob/main/tools/h6253_canary_decisions_to_labels.py) — converts the exported `decisions.json` into `data/eval/articlegen/canary/mg_labels.tsv`.
- Output (gitignored, local-only): `review/kosha-h6253-mg-canary-blind_18-11-26_review.html` — **15 cards**: 5 held-out slp1 headwords × 3 criteria (gloss / examples / citations).

Each card shows the frozen Cologne MW v02 gold and both generated articles (GLM 5.3 Flash, DeepSeek 4.1 Flash) verbatim. The 15 labels are then compared by the existing scorer against its own per-model predictions → 30 scored comparisons, ≥80% (24/30) required.

## Blindness — what was deliberately withheld

The generator never reads `scores_per_item.tsv`, `scores_summary.json`, or the decision thresholds in `scripts/articlegen_score.py`. A post-generation grep of the 105 KB HTML found **0** occurrences of `gloss_token_f1`, `example_recall`, `citation_gold_match`, `0.15`, `0.34`, `agent_ready` or `predicted`. The string `scores_per_item.tsv` appears only inside the note saying it is withheld. This is recorded as `EvidenceManifest.declare_omitted` entries in the generator, not left implicit.

## Screening (review-sheet Phase 0-bis)

| Class | Count | Detail |
| --- | --- | --- |
| (a) deterministic | 0 | no card follows from its own structure |
| (b) dataset lookup | 0 | no dataset decides a gold label |
| (c) agent adjudication | 0 | an agent label would be circular/false-green |
| (d) human | 15 | gold calibration **is** the deliverable (H6253 gate `human:MG`) |

## Publication decision

**Not published to `gasyoun.github.io/vote`.** The standing Phase 3-bis default is overridden here because the five rows are held-out canary items: exposing their gold text on a public hub would contaminate the eval this sheet exists to protect. The sheet and its exported decisions stay local, like the H2839 personal-data exception, but for contamination rather than privacy.

## Consumer contract — what happens after MG votes

1. Open `review/kosha-h6253-mg-canary-blind_18-11-26_review.html`, record all 15 decisions (`1 — верно` / `0 — неверно`; `не знаю` leaves a cell unlabeled), download `kosha-h6253-mg-canary-blind_18-11-26_decisions.json` into the same folder.
2. `python3 tools/h6253_canary_decisions_to_labels.py review/kosha-h6253-mg-canary-blind_18-11-26_decisions.json`
   — refuses if any cell is unlabeled or if `mg_labels.tsv` already exists (override only with an explicit MG ruling). The `notes` column records the sheet id and `reviewedAt` stamp.
3. `python3 scripts/articlegen_score.py --canary` — the gate opens only on exit 0 / ≥80% agreement. Until then the verdict stays **INCONCLUSIVE**.

Verified offline: all-approve synthetic decisions produce a well-formed 5×3 TSV; one `defer` produces `REFUSE: 1 of 15 decisions unlabeled` (exit 2). Both test artifacts were removed.
