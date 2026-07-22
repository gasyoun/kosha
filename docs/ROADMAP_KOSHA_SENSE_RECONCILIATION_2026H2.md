# ROADMAP — kosha sense-reconciliation layer (2026 H2)

_Created: 22-07-2026 · Last updated: 22-07-2026_

Index: [PLAN_KOSHA_SENSE_RECONCILIATION_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_RECONCILIATION_2026H2.md).
Origin: the [नागदन्त thread](https://groups.google.com/g/nagari/c/NOWqiBQl1Xc/m/_R8O4-39CAAJ) — a
polysemous word split by translators because per-sense loci were dropped.

## Wave 1 — per-sense corpus attestation (this plan)

Deliverables, each stating what unblocks it:

1. **PWG sense→loci export** ([H1456](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1456-Sonnet_RussianTranslation_pwg-sense-loci-export_22.07.26.md), RussianTranslation)
   — `pwg_sense_loci.tsv` from `microstructure.py`. *Unblocks everything below.* Ships first.
2. **`<ls>`-locus resolver** — each sense's `<ls>` strings → citable DCS/Samudra passages, reusing
   `pwg_sources.py` + `concordance_core.citable_locus`. *Unblocks step 3's high-confidence tier.*
3. **Hybrid sense-aligner** — `build_sense_corpus_concordance.py`: locus-match + gloss/synset-overlap
   candidates, LLM only on the residue; assign best sense, flag `confidence<τ`. *Needs 1+2 + the
   existing headword↔attestation link.*
4. **Sense-sharded KWIC viewer** — fork of `concordance/dict/` keyed on `(headword, sense_id)`;
   full publication behind a passing `/publish-safety-check`. *Needs step 3 output.*
5. **Build report + manifest row** — `sense-corpus-concordance` in
   [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json),
   coverage + locus-resolution rate logged.

**Wave-1 exit** = the acceptance gate in
[VERIFICATION](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_SENSE_RECONCILIATION.md)
(locus-resolution rate ≥ floor on the pilot set; `nāgadanta` a/b senses each carry their correct
attestation; deterministic round-trip green).

## Wave 2 — cross-dictionary reconciliation view (planned, not built here)

- **Aligned-sense table** — PWG↔MW↔Apte↔Sa→Sa (ŚKDR/Medinī/VCP/Amara) senses side-by-side per
  headword, the tusk↔Pflock↔гвоздь rows linked as one meaning. The user-facing render of the
  substrate wave-1 builds.
- **Lemma-variant graph** — full `nāgadanta`↔`nāgadantaka`-class normalisation across all dictionaries.
- **Second acceptance pass** — the deferred (~6-month) sample + LLM-judge + `/review-sheet` human vote.
- **pwg_ru RU-sense-structure deliverable** — carry PWG's ordered a)/b) hierarchy + per-sense loci
  into the Russian output verbatim (don't flatten), so pwg_ru reproduces the reconciliation PWG
  already encodes. (Satellite of this initiative; its own handoff at wave-2 mint.)

## Wave 3 — corpus-frequency fusion (planned)

- Fuse this layer's per-sense attestation set with [H1453](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md)'s
  per-sense counts → a single "sense N: X attestations, Y% of lemma, top loci …" card block.
- Feed disagreements (this layer's `<ls>`-locus witness vs H1453's WordSem witness) into the
  M01 Ch6 "Senses: Inheritance and Order" finding.

## Non-goals (explicit)

- **No WSD** past what the `<ls>` loci + gloss-overlap + LLM-residue give — full word-sense
  disambiguation is H1453 wave-2 territory, not this plan's.
- **No reordering of MW or kosha senses** — sidecar only.
- **No new corpus** — Samudra + DCS are queried, never rebuilt.
- **No paper this wave** — a publishable methodological finding (per-sense loci resolve the
  translator-split problem) is logged to GTD, not forced into a manuscript.

_Dr. Mārcis Gasūns_
