# ROADMAP — kosha sense-frequency layer

_Created: 22-07-2026 · Last updated: 22-07-2026_

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

## Wave 2 — full-corpus WSD extension (deferred handoffs)

- **W2.1** SCL Reading-Aid scrape harness (validation-witness only, licence-gated on H057) →
  `data/frequency/scl_sense_witness.tsv`.
- **W2.2** LLM gloss-grounded WSD over untagged tokens, reusing the DEFGEN protocol; held-out WordSem gold
  as the test set.
- **W2.3** Two-witness fusion + acceptance gate (≥70% held-out accuracy, SCL+LLM agree) → extend
  `sense_frequency.tsv` with `provenance=estimated` rows + confidence.
- **W2.4** Light up the `estimated` tier in the kosha-cards badge.

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
