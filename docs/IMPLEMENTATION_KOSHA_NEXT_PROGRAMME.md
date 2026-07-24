# Implementation — kosha next programme

_Created: 24-07-2026 · Last updated: 24-07-2026_

Index: [PLAN_KOSHA_NEXT_PROGRAMME_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_NEXT_PROGRAMME_2026H2.md).
File-level steps for each wave. Agents work in a **worktree** off `origin/main`.

## Handoff map

| Wave | Scope | Model | Handoff |
|---|---|---|---|
| W1a | H1265 + H1267 hygiene | Haiku | existing staged |
| W1b | H1461 + H1492 (+ opt H1493) | Sonnet | existing staged |
| W1c | Panini W4a surface | Sonnet | [H1585](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1585-Sonnet_kosha_w4a-panini-surface-chain-trust-block_24.07.26.md) |
| W1d | Pages budget re-measure | Haiku | [H1586](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1586-Haiku_kosha_w4b-pages-budget-remeasure-a4_24.07.26.md) |
| W2 | Pilot cross-dict view | Opus | [H1587](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1587-Opus_kosha_sense-recon-pilot-crossdict-view_24.07.26.md) |
| W3 | Two-witness WSD | Opus | [H1588](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1588-Opus_kosha_sense-frequency-two-witness-wsd_24.07.26.md) |
| W4 | P-D5 DB layers | Opus | [H1589](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1589-Opus_kosha_data-hub-pd5-queryable-db-layers_24.07.26.md) |
| W5 | P5 SSR + static head + exit | Opus | [H1590](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1590-Opus_kosha_p5-ssr-static-head-exit-packet_24.07.26.md) |

---

## Wave 1c — panini W4a surface

1. Read [`ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md`](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md) §9 and [`SUTRA_COVERAGE_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/data/concordance/SUTRA_COVERAGE_BUILD_REPORT.md).
2. Extend shard builder or add `scripts/build_panini_coverage_shards.py` emitting JS (or JSON) the existing panini page can load for the **coverage map** (status per sūtra, exemplar counts).
3. Edit [`concordance/panini/index.html`](https://github.com/gasyoun/kosha/blob/main/concordance/panini/index.html):
   - Coverage tab/panel with four status classes styled distinctly
   - Chain panel for lit exemplars (reuse existing chain fields if already in KWIC shards; else join from derivation artefacts at build time)
   - Trust block: artefact, n=3983 enumeration, date, report links
   - CSV download link for `sutra_coverage_map.tsv`
4. Tests: at least one pure test that the coverage shard/HTML contains all four status strings and does not collapse dark classes.
5. CHANGELOG `[Unreleased]` + manifest consumer note if new builder outputs.

## Wave 1d — Pages budget re-measure

1. Measure current deployed/generated footprint (cards + concordance + reading + any word-page head).
2. Project static head N=11,148 word pages at measured KB/page.
3. Append dated row to budget log (prefer existing D5 / architecture §6 table or `.ai_state` Dev Notes + architecture doc) — **append, do not overwrite** prior figures.
4. If projection exceeds ~90% of 1 GB soft cap with A4 pages included, document the D4 head bound as the control (already standing).

## Wave 1a / W1b — existing handoffs

Execute the staged files as written. Do not expand scope. H1493 is optional if time-boxed out — log skip.

## Wave 2 — pilot cross-dict view

1. Load pilot headword list from H1455 artefacts (`select_sense_pilot` output / build report).
2. Join PWG sense rows + MW senses (read-only from kosha.db or cards) + Apte if extract exists.
3. Emit `data/concordance/sense_crossdict_pilot.tsv` + slim JS for viewer.
4. Page under `concordance/senses/` (or sibling) with three columns + loci.
5. Manifest row `sense-crossdict-pilot` (public if publish-safety GO; else intermediate).
6. Tests: pilot size stable, `nāgadanta` row present with distinct PWG a/b if still in pilot, no MW sense file rewritten.

## Wave 3 — two-witness WSD

1. Add gitignore path for SCL label cache; document in data-statement.
2. `scripts/scl_sense_witness.py` — fetch labels only; write cache; idempotent.
3. `scripts/wsd_llm_arm.py` — gold-free projection + held-out eval split from WordSem.
4. `scripts/wsd_fuse.py` — agree → estimated rows; disagree → review TSV.
5. Extend `sense_frequency.tsv` schema with `provenance` already scaffolded; fill estimated.
6. Cards UI: light estimated badge tier.
7. Gate: ≥70% held-out accuracy on WordSem gold; if SCL blocked, LLM-only with logged degradation.
8. `/publish-safety-check` before any public release of estimated layer.

## Wave 4 — P-D5

1. Pick public join assets from `datasets.json` with clear local paths.
2. Additive `build_db.py --stage layers` (or sibling script) creating tables + indexes.
3. Tests for join integrity on smoke lemmas (`dharma`, `nAga`, `kR`).
4. Operator note in [`PIPELINE_OPERATOR_RUNBOOK.md`](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.md).

## Wave 5 — P5 SSR + static head + exit

1. Run `build_word_pages.py` with `--head 11148` (or equivalent) from `lemma_frequency` rank.
2. Confirm gitignore of full `docs/w/` if regenerable; commit only what the repo already commits for other static tiers (match cards policy).
3. Verify SSR route byte-parity tests green.
4. Write exit packet markdown: Lighthouse target, walkthrough steps, deploy checklist — MG signs live staging.
5. If server not yet live: ship static head + packet with **blocked** live checks explicitly listed (do not fake green).

---

_Dr. Mārcis Gasūns_
