# PLAN — kosha sense-reconciliation layer (сведение значений)

_Created: 22-07-2026 · Last updated: 22-07-2026_

**Origin.** This plan crystallises a single lexicographic lesson from the
[nagari-group नागदन्त thread](https://groups.google.com/g/nagari/c/NOWqiBQl1Xc/m/_R8O4-39CAAJ):
translators (Сыркин «гвоздь в стене» vs Лихушина «слоновый бивень») split on a polysemous
headword precisely because thin bilingual glossaries drop what PWG already encodes — a **connected
sense hierarchy with a locus per sense**. Verified against source (`csl-orig/v02/pwg/pwg.txt`
L38150): PWG `nāgadanta` keeps ONE homonym, senses ordered `a) Elephantenzahn → b) Pflock in der
Wand` (derivation visible), each with its own `<ls>` loci — a) MBH 12,3630; **b) PAÑCAT 116,19;
252,10** — and links the `-ka` variant `nāgadantaka` (L38151, cites HIT 27,12). MW splits the same
word into two records with vague refs; the Russian glossaries flatten it. The gap is generic:
**kosha links a headword to its DCS attestations, but not to the correct numbered SENSE.**

**One-paragraph goal.** Build the per-**sense** corpus-attestation layer on top of the existing
headword-level [`build_dict_corpus_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_dict_corpus_concordance.py)
+ [`concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py)
(REUSE, do not rebuild). Wave-1: (1) consume a PWG per-sense `<ls>`-locus map exported from
[`RussianTranslation/src/microstructure.py`](https://github.com/sanskrit-lexicon/SanskritLexicography/blob/master/RussianTranslation/src/microstructure.py)
(handoff [H1456](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1456-Sonnet_RussianTranslation_pwg-sense-loci-export_22.07.26.md));
(2) resolve those `<ls>` loci to DCS/Samudra passages; (3) a **hybrid** aligner assigns each
headword's DCS attestations to a numbered sense (deterministic locus-match + gloss-overlap
candidates, LLM only on the residue), flagging `confidence<τ` to a review queue; (4) emit
`data/concordance/sense_corpus_concordance.tsv` + a sense-sharded KWIC viewer, published in full.
Cross-dictionary reconciliation (PWG↔MW↔Apte↔Sa→Sa senses side-by-side) is wave-2.

**Sibling initiative — read first, do not overlap.** [H1453 sense-frequency layer](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md)
counts *how often* each sense is attested (WordSem synset gold → MW sense → SIL domain). This plan
supplies *which passages* attest each sense and *how senses map across dictionaries*. They share the
**same "attestation → numbered sense" assignment** and are **two witnesses** to it: H1453's
WordSem→MW-sense projection is a deterministic candidate signal for this aligner; this plan's
`<ls>`-locus resolution is a second witness for H1453's counts. Build the shared assignment table
once, in `data/concordance/`, consumed by both. Neither reorders or overwrites MW/kosha `senses`.

Layered docs (read in order):

- **Roadmap** — [ROADMAP_KOSHA_SENSE_RECONCILIATION_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_SENSE_RECONCILIATION_2026H2.md)
- **Architecture** — [ARCHITECTURE_KOSHA_SENSE_RECONCILIATION.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_SENSE_RECONCILIATION.md)
- **Implementation (wave-1, file-level)** — [IMPLEMENTATION_KOSHA_SENSE_RECONCILIATION_WAVE1.md](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_SENSE_RECONCILIATION_WAVE1.md)
- **Verification & risks** — [VERIFICATION_KOSHA_SENSE_RECONCILIATION.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_SENSE_RECONCILIATION.md)

Execution handoffs: [H1455](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1455-Sonnet_kosha_corpus-attestation-per-sense-join_22.07.26.md) (kosha, Sonnet 5 `claude-sonnet-5`) · [H1456](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1456-Sonnet_RussianTranslation_pwg-sense-loci-export_22.07.26.md) (RussianTranslation, Sonnet 5, the `<ls>`-loci export it depends on).

---

## Decisions taken (interview, 22-07-2026)

| # | Fork | Ruling | Rationale |
|---|---|---|---|
| 1 | Scope | **Both repos** (kosha display+join, RussianTranslation the PWG sense→loci export) | User choice; the join lives in kosha (concordance infra), its per-sense input in RT (microstructure) |
| 2 | Wave-1 deliverable | **Corpus-attestation-per-sense** — assign DCS attestations to numbered senses + sense-sharded KWIC. Cross-dict reconciliation view = wave-2 | User choice; the attestation join is the load-bearing substrate the reconciliation view later renders |
| 3 | Alignment method | **Hybrid** — deterministic candidate-gen (`<ls>` locus-match + gloss/synset overlap) + LLM adjudication only on the residue | User choice; mirrors pwg_ru's corpus_gate (cheap on the obvious, judge on the hard) |
| 4 | Dictionary scope | **Petersburg chain + MW + Apte** (PWG/PW/SCH/PWKVN/NWS + MW + Apte) | User choice; the bilingual anchors translators use, all already extracted in RussianTranslation/src |
| 5 | Acceptance bar (wave-1) | **Automatic: `<ls>`-locus-resolution rate + coverage.** Sample + LLM-judge + review-sheet deferred ~6 months | User choice; no human gate in wave-1 → fully autonomous |
| 6 | Attestation source | **Reuse SamudraManthanam FTS + DCS AND resolve PWG `<ls>` loci** to real passages | User choice; never rebuild the corpus — query it; `<ls>` gives the per-sense signal for free |
| 7 | On aligner uncertainty | **Assign best sense + flag `confidence<τ`** to a review queue (never silently drop) | User choice; maximises coverage, keeps doubtful rows visible |
| 8 | Publication | **Full publication** — with a mandatory [/publish-safety-check](https://github.com/gasyoun/claude-config/blob/main/commands/publish-safety-check.md) gate; modern-copyright material (Кочергина/Смирнов/DCS-modern glosses) stays **evidence-only** even under full publish (legal constraint, not a preference) | User choice + the standing rights gate `corpus_gate.RIGHTS` |
| 9 | Relationship to H1453 | **Shared assignment table** in `data/concordance/`, built once, two witnesses; neither plan reorders MW | Audit — H1453 exists and is a sibling sense-layer; overlap resolved by sharing the substrate |
| 10 | Build-vs-reuse | **Extend** `build_dict_corpus_concordance.py`/`concordance_core.py`; **reuse** microstructure's sense parser, Samudra FTS, dcs-cdsl-xref | Prior-art check — headword↔attestation link and PWG sense parse both already exist |

---

## Autonomy contract (verbatim — governs the unattended wave-1 agent)

- **On unplanned ambiguity:** apply the marked default in the relevant doc and **log it** (one line
  in `.ai_state.md` Dev Notes + a `LOG:` comment at the decision site), then keep going. Never stall
  for a human — there is none for 5–8 h.
- **Stop conditions:** halt and hand back only if (a) the PWG `<ls>`-locus map (H1456) is unavailable
  and cannot be regenerated from `microstructure.py` after a genuine attempt — then do the
  reuse-only parts (gloss/synset-overlap candidates) that don't need it and park the rest; or (b) the
  acceptance gate in [VERIFICATION](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_SENSE_RECONCILIATION.md)
  (locus-resolution rate floor) cannot be met by any wave-1 step.
- **Commit authority:** per the handoff-scoped autonomy rule, wave-1 may commit → PR → merge with no
  further human ask. kosha and SanskritLexicography are guarded main-tree repos — **work in a
  worktree**, never the main checkout.
- **Publish gate is NOT autonomous:** the full-publication step (public sense-KWIC viewer) requires a
  passing `/publish-safety-check` run recorded in the PR before anything goes live; if it flags
  modern-copyright leakage, downgrade those rows to evidence-only and re-run — do not publish through
  a red gate.
- **The fence (must NOT touch):**
  - Never overwrite human-reviewed MW / kosha `senses` / app_data — the sense-attestation layer is a
    **sidecar**, LEFT-JOINed at build time, exactly like `lemma_frequency` and the H1453 layer.
  - Never re-derive the DCS corpus, the dcs-cdsl-xref, or the Samudra corpus — consume them.
  - Never commit modern-copyright bulk (Кочергина/Смирнов) — evidence-only, gitignored, per `corpus_gate.RIGHTS`.
  - Never edit `csl-orig` (read-only PWG layer source).

_Dr. Mārcis Gasūns_
