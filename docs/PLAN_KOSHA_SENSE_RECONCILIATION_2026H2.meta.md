# META — PLAN_KOSHA_SENSE_RECONCILIATION_2026H2.md

_Created: 22-07-2026 · Last updated: 22-07-2026_

**Purpose.** The onboarding pack for the kosha sense-reconciliation initiative — the per-sense
corpus-attestation layer (wave-1) and the cross-dictionary reconciliation view (wave-2) — so a fresh
session need not re-derive the scope, the prior-art verdicts, or the interview rulings.

**Audience.** The execution agent for [H1455](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1455-Sonnet_kosha_corpus-attestation-per-sense-join_22.07.26.md)
(kosha) and [H1456](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1456-Sonnet_RussianTranslation_pwg-sense-loci-export_22.07.26.md)
(RussianTranslation); anyone triaging the kosha sense-layer backlog.

**Provenance.** Authored 22-07-2026 via `/ask` (Opus 4.8 `claude-opus-4-8`), grounded in the
[nagari-group नागदन्त thread](https://groups.google.com/g/nagari/c/NOWqiBQl1Xc/m/_R8O4-39CAAJ) and a
source verification of PWG `nāgadanta` (`csl-orig/v02/pwg/pwg.txt` L38150) vs MW. Two interview rounds
(scope/method, then verify-bar/autonomy); all forks ruled — see the plan's decisions table.

**Improvement backlog (ranked).**
1. Confirm the `<ls>`→DCS-locus normalisation spike result before scaling past the pilot (top risk).
2. Merge the wave-2 pwg_ru RU-sense-structure satellite into a proper handoff at wave-2 mint.
3. Reconcile the shared assignment table's schema with H1453's `data/frequency/` so both consume one file.
4. Decide the deferred human-sample cadence (currently "~6 months") against real drift once wave-1 ships.

**Limitations.** Wave-1 is a ~500-headword pilot, automatic-acceptance only (no human sample);
cross-dictionary reconciliation and full lemma-variant graph are explicitly wave-2; no WSD.

**Related.** Sibling: [PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md)
(H1453). Reuses [`build_dict_corpus_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_dict_corpus_concordance.py),
[`concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py),
[`RussianTranslation/src/microstructure.py`](https://github.com/sanskrit-lexicon/SanskritLexicography/blob/master/RussianTranslation/src/microstructure.py).

**Revision history.**
- 22-07-2026 — created with the five layer docs (Opus 4.8 `claude-opus-4-8`, `/ask`).

_Dr. Mārcis Gasūns_
