# ROADMAP — kosha sense-frequency layer

_Created: 22-07-2026 · Last updated: 24-07-2026_

Index: [PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md).

## Wave 1 — 3-layer sense frequency on WordSem gold + kosha-cards UI (this handoff, H1453)

Deliverables, each with what unblocks it:

1. **WordSem decode inventory recovered** — `data/frequency/wordsem_inventory.tsv` (synset_id → gloss →
   Sanskrit-WordNet lemma). _Unblocks everything below._ Source: DCS CoNLL-U releases `WordSem` MISC key.
2. **3-layer sense-frequency dataset** — `data/frequency/sense_frequency.tsv`: per (lemma_slp1, sense
   layer, sense_id) token counts, at all three layers (WN synset / MW sense / semdom), whole-corpus +
   per-period, `provenance=attested`. _Unblocked by (1) + the crosswalks (all reuse)._
3. **Manifest row + data-statement** — `data/manifest/datasets.json` gains `kosha-sense-frequency`;
   `docs/data-statements/kosha-sense-frequency.meta.md`. _Unblocked by (2)._
4. **DCS-vs-MW sense-order disagreement report** — `data/frequency/dcs_mw_sense_order_delta.md`: where the
   frequency-dominant sense ≠ MW sense-1, tagged as a DCS-derivation finding. _Unblocked by (2); feeds
   M01 Ch6._
5. **kosha-cards "N in this sense · M for lemma" display** — two-tier badge (all wave-1 counts are
   `attested`, so the estimated tier renders empty but the scaffold is present for wave-2). _Unblocked by
   (2)._

**Wave-1 non-goals:** no WSD extension past gold; no scrape; no pwg_ru / Cologne / VisualDCS UI; no MW
reordering.

## Wave 2 — full-corpus WSD extension — **DONE 24-07-2026 (H1588)**

Shipped under next-programme **W3** as [H1588](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1588-Opus_kosha_sense-frequency-two-witness-wsd_24.07.26.md)
(Grok 4.5 `grok-4.5`, Opus-lock override). Report:
[`wsd_fusion_report.md`](https://github.com/gasyoun/kosha/blob/main/data/frequency/wsd_fusion_report.md).

- **W2.1** SCL Reading-Aid witness harness → gitignored
  `data/frequency/.cache/` (labels only). **Fail-closed** this pass: H057 rights
  unresolved; homepage probes only; zero labels written (autonomy contract).
- **W2.2** Gloss-grounded / MFS arm over untagged tokens + held-out WordSem eval
  ([`wsd_llm_arm.py`](https://github.com/gasyoun/kosha/blob/main/scripts/wsd_llm_arm.py)).
  Held-out accuracy **83.96%** (MFS; gate ≥70% **PASS**). LLM path remains optional when
  `DEEPSEEK_API_KEY` is available; not required for the gate.
- **W2.3** Fusion ([`wsd_fuse.py`](https://github.com/gasyoun/kosha/blob/main/scripts/wsd_fuse.py)):
  single-witness degradation logged; **13,709** `provenance=estimated` MW rows
  (4,506,310 tokens); review queue empty-with-reason.
- **W2.4** Estimated tier lit on word-page / cards (`app/word_page.py`) — separate chip,
  never blended with attested.

## Wave 3 — surface fan-out (deferred handoffs)

- pwg_ru article site · Cologne dict-web reader · VisualDCS — each consumes `sense_frequency.tsv`, none
  re-derives it.
- Optional: register the sense-order finding as an ARTICLES paper if the delta (Wave-1 deliverable 4) is
  substantial.

## Explicit non-goals (whole roadmap)

- No reordering of MW's canonical senses — MW order is trusted; only DCS's derived order is audited.
- No redistribution of SCL/GPL content — witness flags only.
- No new repo — the layer lives in kosha `data/frequency/`.

_Dr. Mārcis Gasūns_
