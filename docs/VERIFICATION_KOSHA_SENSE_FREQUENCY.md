# VERIFICATION & RISKS — kosha sense-frequency layer

_Created: 22-07-2026 · Last updated: 22-07-2026_

Index: [PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md).

## Acceptance criteria (wave-1 — the exact check that proves each deliverable)

| # | Deliverable | Passes when |
|---|---|---|
| 1 | `wordsem_inventory.tsv` | Distinct decoded synset count **> the ~531k-token / 9.3% sqlite baseline**; every corpus-seen synset id is decoded or explicitly listed as un-decodable; no empty glosses on decoded rows. |
| 2 | `wn_to_mw_map.tsv` | Every synset has a `match_type`; `unresolved` fraction is reported (not hidden); a 30-row hand-sample verifies `exact` matches are correct (spot-check via `/spot-check-sample`). |
| 3 | `sense_frequency.tsv` | Per lemma, Σ(sense `count_all`) over the **wn** layer ≤ that lemma's `lemma_frequency.count_all` (senses can't out-count the lemma); all three layers present; `sense_rank`/`lemma_share` internally consistent; `provenance=attested` on every row. |
| 4 | `dcs_mw_sense_order_delta.md` | Mismatch count + a rate; ≥5 worked examples showing frequency-dominant sense vs MW sense-1; canonical `senses` provably untouched (`git diff` clean on the DB/sense files). |
| 5 | manifest + data-statement | `datasets.json` validates; `kosha-sense-frequency` row resolves; data-statement carries the WordSem-coverage + aorist/perfect caveats. |
| 6 | kosha-cards UI | Browser preview shows "N in this sense · M for the lemma" on a known polysemous lemma; two-tier badge present with the `attested` chip populated and `estimated` chip empty; no console errors; `sense_frequency` LEFT-JOIN never drops a lemma that has a card. |

**Sanity anchor.** Pick a textbook polysemous lemma (e.g. `pada` foot/word/verse-quarter, `artha`
meaning/wealth/purpose) and confirm its sense distribution is plausible against a Sanskritist's
expectation — a smoke test before trusting the whole table.

## Wave-2 acceptance gate (recorded now, enforced later)

Extended (`estimated`) counts ship only where **both**: (a) SCL-scrape and LLM gloss-grounded WSD agree on
the sense, **and** (b) the LLM method clears **≥70% accuracy on held-out WordSem gold**. Disagreements →
no estimated count for that token (left un-sensed, counted only at the lemma level). This gate is why
wave-1 keeps `provenance`/`confidence` columns even though every wave-1 row is `attested`.

## Risks & spikes register

| Risk | Likelihood | Impact | Mitigation / spike |
|---|---|---|---|
| **WordSem decode not recoverable** from the CoNLL-U releases (synset ids without a shipped WordNet gloss table) | Medium | High — Layer 1 has ids but no meanings | **Spike Step 1 first.** If it fails, park it, ship Steps 2–3 scaffolding + the WN→MW map on the decodable subset; escalate a request to Hellwig/DCS via GTD. This is the plan's one real stop-condition. |
| WN→MW crosswalk sparse (`unresolved` high) | Medium | Medium — Layer 2 (MW) thin | Report the resolved fraction honestly in the data-statement; Layer 1 (WN) stays lossless regardless; overlap-scoring fallback raises coverage. |
| semdom-amarakosha xwalk doesn't cover a synset's domain | Medium | Low | Layer 3 is best-effort; missing → null domain, counted at layers 1–2. |
| WordSem coverage gap (51 texts, incl. new Vedic) read as "sense-tagged" | Low (documented) | Medium | Filter on the WordSem MISC key per text; state coverage in `.meta.json`. [SL FINDINGS §11 addendum.](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md) |
| Homonym/polysemy conflation inflates a "sense" that is really a separate lemma | Low | Medium | Cross-check against WhitneyRoots [`token_attribution.json`](https://github.com/gasyoun/WhitneyRoots/blob/main/crosswalk/token_attribution.json) for the 26 split homonym groups; keep the axes distinct (Architecture §traps). |
| SCL scrape licence (wave-2) | — | High if mishandled | Witness-flags only, never redistribute; gated on outreach [H057](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H057-Opus_Uprava_OUTREACH_2026-07-02_amba_kulkarni_scl_02.07.26.md). Not a wave-1 concern. |

## What "done" means for wave-1

All six acceptance rows green, PR merged, manifest row live, H1453 flipped in the registry, kosha
`.ai_state.md` Next-Steps pointing at wave-2. No WSD accuracy number is claimed anywhere in wave-1 output
(the gold-only layer makes no accuracy claim — it *is* the gold).

_Dr. Mārcis Gasūns_
