# ROADMAP — kosha sense-reconciliation layer (2026 H2)

_Created: 22-07-2026 · Last updated: 02-09-2026_

Index: [PLAN_KOSHA_SENSE_RECONCILIATION_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_RECONCILIATION_2026H2.md).
Origin: the [नागदन्त thread](https://groups.google.com/g/nagari/c/NOWqiBQl1Xc/m/_R8O4-39CAAJ) — a
polysemous word split by translators because per-sense loci were dropped.

**Truth-pass verdict (31-08-2026, H3786):** still live. Wave 1's mechanics are shipped
(`scripts/build_sense_corpus_concordance.py`, `sense-corpus-concordance` manifest row) and Wave
2 slice 1 shipped today (H3744); Wave 2 slice 2 (Sa→Sa dictionary columns) and Wave 3
(frequency fusion) are the unticked residual — see those sections below.

**Update 02-09-2026 (H3862):** Wave 2 slice 2 has shipped. The unticked residual is now Wave
2's acceptance pass, the lemma-variant graph, and Wave 3.

## Wave 1 — per-sense corpus attestation (this plan)

Deliverables, each stating what unblocks it:

1. **PWG sense→loci export** ([H1456](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1456-Sonnet_RussianTranslation_pwg-sense-loci-export_22.07.26.md), RussianTranslation)
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

## Wave 2 — cross-dictionary reconciliation view

- **Aligned-sense table** — ✅ **slice 1 shipped 31-08-2026 (H3744, Opus 5 `claude-opus-5`)**:
  PWG↔MW↔Apte senses grouped into meanings by shared `<ls>` literary witness weighted `1/df`
  within the lemma, the tusk↔Pflock rows linked as one meaning. Staged behind
  `ux={"sense_align": True}`, **not** on the 2,324 live pages
  ([NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md](https://github.com/gasyoun/kosha/blob/main/docs/NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md));
  compare page for the human ruling:
  [gasyoun.github.io/h3744-sense-align/](https://gasyoun.github.io/h3744-sense-align/).
  Packet + limits:
  [H3744_SENSE_ALIGNMENT_PACKET_31.08.26.md](https://github.com/gasyoun/kosha/blob/main/docs/H3744_SENSE_ALIGNMENT_PACKET_31.08.26.md).
  **Slice 2 — ✅ shipped 02-09-2026 (H3862, Opus 5 `claude-opus-5`)**: ŚKDR and VCP as further
  columns, `shape` extended to five positions. Two of the four dictionaries asked for do not
  exist as CDSL sources and are recorded as absences with their reason — **Medinī is not in
  CDSL** (the `md` code in csl-orig/csl-sqlite is Macdonell), and neither is Amara. The kośas
  carry **zero `<ls>`**, so the witness bridge does not point at them; what ships is the reverse
  direction, PWG's own citations *of* them (`ŚKDR.` 1,227×, `MED.` 1,824× on the pilot) as the
  `attrib` method — same `1/df`, same τ, no new constant, ranked below `ls` because it is
  one-directional. Slice 1's numbers are unchanged, verified row by row against `--no-sasa`:
  aligned 2,957 → 3,013 (56 kośa-only meanings + 11 existing meanings that gained a kośa cell),
  clean `1-1-1` still 262. Smoke 31/31:
  [H3862_SENSE_ALIGNMENT_SMOKE_LOG_02.09.26.md](https://github.com/gasyoun/kosha/blob/main/docs/H3862_SENSE_ALIGNMENT_SMOKE_LOG_02.09.26.md).
  **Still open in Wave 2:** the acceptance pass (sample + judge + human vote — no precision
  figure may be quoted until it runs) and the lemma-variant/homonym graph, which is what would
  fix the known `attrib` false-positive class (a lemma-level join onto a ŚKDR verbal-root entry:
  `kaṭa`, `bhū`).
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
