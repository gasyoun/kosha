# DEFGEN_HERITAGE_SECOND_REFERENCE_EVAL.md — metadoc

_Created: 09-08-2026 · Last updated: 09-08-2026_

## Purpose

Companion record for
[DEFGEN_HERITAGE_SECOND_REFERENCE_EVAL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_HERITAGE_SECOND_REFERENCE_EVAL.md),
the second-reference arm of the definition-generation eval. The subject document answers
one question: **does the arm ranking from the MW-only eval survive a change of reference
dictionary?** (It does.) Everything else in it — the divergence table, the premium
measurement, the per-cell replication — exists to bound how far that answer can be pushed.

## Audience

Anyone continuing the defgen/WSD eval line, or drafting the eLex/EURALEX/IJL paper from
it. Read the parent
[DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md)
first — this document is a follow-up arm, not a standalone study, and it assumes the frozen
sample, the five arms and the judge-gate discipline are already understood.

## Provenance

- **Handoff:** [H2408](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2408-Fable_kosha_definition-gen-gloss-wsd-pilot_07.08.26.md)
  (**Fable 5**) — Definition generation + gloss-grounded WSD pilot. Executed 09-08-2026.
- **Model:** Fable 5 (`claude-fable-5`) in Claude Code — harness, run, analysis, write-up.
- **Judge:** `deepseek-chat` (temperature 0), cross-lingual system prompt.
- **Predecessors:** [H730](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H730-Fable_kosha_definition-generation-gloss-eval_11.07.26.md)
  (original eval), [H752](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H752-Fable_kosha_defgen-parked-lane-salvage_11.07.26.md)
  (parked-lane salvage, canonical-sample ruling),
  [H972](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H972-Fable_kosha_definition-generation-gloss-eval_15.07.26.md)
  (F1 Fable arm).
- **Scope note:** H2408's goal line reads "pilot definition-gen **or** gloss-WSD eval on
  MW/Heritage sample with metrics table". The MW half had already shipped under
  H730/H752/H972, so executing it again would have duplicated shipped work. The Heritage
  half — the parent protocol's own ranked next-step #4 — was the genuine open residual, and
  is what this pass built.

## Ranked improvement backlog

1. **Human-scored subsample** across both references — validates the cross-lingual judge
   and the MW premium at once; the standing blocker on any paper claim.
2. **Second judge family** — removes the shared-judge confound that is currently the
   biggest threat to the premium number.
3. **Post-1899 headword subset** — the only clean isolation of generation-vs-memorisation;
   neither reference alone gets there.
4. **Heritage sense divisions for the WSD pilot** — a second sense inventory, still
   agreement-only until DCS `m_wordsem` is recovered.
5. **Third reference (PW/PWG German or a Russian layer)** — turns a two-point delta into a
   reference-family trend.
6. **Per-cell judge scores** — currently only chrF is broken out per stratum cell; the
   judge is the load-bearing metric here, so per-cell judge means would be more useful
   than per-cell chrF.

## Limitations to keep in view

- n = 333 (Heritage coverage), high-frequency-skewed; not comparable to the 500-item table.
- One judge model scores both references — clean for pairing, confounded for the premium.
- Heritage is not causally independent of the 19th-c. tradition MW belongs to.
- Cross-lingual surface metrics are near-degenerate and must not be quoted as quality.
- No Heritage gloss text is committed (LGPLLR, `tier=restricted`); reproduction requires
  the local `SanskritLexicography` sibling. The digest gate refuses to score a drifted join
  rather than silently scoring different text.

## Revision history

| Date | Change | By |
|---|---|---|
| 09-08-2026 | Created with the 333-item run: subset build, metrics, cross-lingual judge (5×333, 0 nulls), paired MW−FR premium with bootstrap CI + sign test, 5 findings | Fable 5 (`claude-fable-5`), H2408 |

_Dr. Mārcis Gasūns_
