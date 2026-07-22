# VERIFICATION & RISKS — kosha sense-reconciliation, wave 1

_Created: 22-07-2026 · Last updated: 22-07-2026_

Index: [PLAN_KOSHA_SENSE_RECONCILIATION_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_RECONCILIATION_2026H2.md).

## Acceptance criteria (wave-1 = automatic, no human gate)

Per ruling #5, the wave-1 bar is machine-checkable; the human sample pass is deferred ~6 months.

| # | Deliverable | Proof (exact check) |
|---|---|---|
| A1 | PWG sense→loci export (H1456) | `pwg_sense_loci.tsv` exists; ≥1 row per pilot leaf sense; `nAgadanta` has rows `1a` (gloss ⊇ "Elephantenzahn") and `1b` (gloss ⊇ "Pflock"), each with ≥1 `<ls>` locus |
| A2 | Locus resolution | **`<ls>`-locus-resolution rate ≥ 60%** on pilot senses (marked default floor — log if adjusted); rate printed in the build report. This is THE wave-1 acceptance metric |
| A3 | Smoke test — `nāgadanta` | MBH-12,3630 attestation → sense `1a` (tusk); PAÑCAT-116,19 attestation → sense `1b` (peg). A mis-assignment here fails the wave |
| A4 | Variant corroboration | `nāgadantaka` HIT-27,12 recorded as `variant_of nāgadanta` supporting the `1b` peg sense |
| A5 | Coverage honesty | every attestation row has a `method ∈ {locus,overlap,llm}` + `confidence`; `confidence<τ` rows present in `sense_review_queue.tsv`, none silently dropped |
| A6 | Sidecar integrity | MW / kosha `senses` byte-unchanged after the build (diff = empty); layer is LEFT-JOIN only |
| A7 | Rights | every row carries `rights`; public viewer shards contain **zero** `evidence-only` rows (grep proof in report) |
| A8 | Determinism | re-run of steps 1–3+5 (deterministic tiers) is byte-identical; only the LLM-residue tier may vary, and it is bounded + logged |
| A9 | Manifest + release | `sense-corpus-concordance` row in `datasets.json`; `CHANGELOG` `[Unreleased]` entry; `/cut-release` run |
| A10 | Publish gate | `/publish-safety-check` verdict recorded in the PR; public viewer shipped only on GO |

## Risks & spikes register

| Risk | Likelihood | Mitigation / spike |
|---|---|---|
| `<ls>` abbrev → DCS locus normalisation lossy (MBH book/verse numbering differs between B&R and DCS) | **High** | **Spike before step 3**: hand-map 20 pilot loci end-to-end; if <60% normalise cleanly, the locus tier degrades to a weaker signal and gloss-overlap+LLM carry more — acceptance floor A2 stays the honest gate. Reuse `pwg_sources.py` (already 98.9% on abbrev resolution — the residual risk is the numbering, not the abbrev) |
| DCS `WordSem` gloss vocabulary ≠ PWG German gloss vocabulary (overlap tier weak cross-language) | Med | Overlap tier keys on the **RU/EN gloss** side of the sense (kosha already has MW EN + pwg_ru RU), not the German, so overlap is same-language; German kept only for the LLM prompt context |
| LLM residue hallucinates a sense id | Low | Hard out-of-set guard (reject+re-ask); residue is a minority tier; `confidence` + `method=llm` make every LLM row auditable |
| Overlap with H1453 double-builds the assignment | Med | Ruling #9: shared `data/concordance/` assignment table, built once; H1453's WordSem projection is consumed here as a candidate, not recomputed |
| Modern-copyright gloss leaks into public viewer | Low | A7 grep + the mandatory `/publish-safety-check`; `corpus_gate.RIGHTS` stamps at build time |
| Pilot too small to be representative | Low (bounded by design) | Wave-1 is explicitly a pilot; full run + human sample are wave-2/deferred; the build report `log()`s the pilot size and selection query (no silent cap) |

## What proves the whole thing worked

The one-line proof a human can eyeball: open `concordance/senses/` on `nāgadanta` and see **two
sense rows** — *слоновий бивень* with its MBH attestation and *колышек в стене* with its
Pañcatantra attestation — the exact split the [नागदन्त thread](https://groups.google.com/g/nagari/c/NOWqiBQl1Xc/m/_R8O4-39CAAJ)
argued about, now resolved by the data instead of by three disagreeing translators.

_Dr. Mārcis Gasūns_
