# PLAN — kosha sense-frequency layer (частотность значений)

_Created: 22-07-2026 · Last updated: 22-07-2026_

**One-paragraph goal.** kosha ships a per-**lemma** frequency layer today; it has no per-**sense**
frequency ("частотность значений") — how often each numbered meaning of a word is actually
attested. This plan builds that layer on top of a fact the org already owns but had written off:
DCS's per-token `WordSem` annotation **is Sanskrit-WordNet synset gold**, present on 219/270 texts
corpus-wide ([SL FINDINGS §11 addendum](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md),
[INTERLINKS §277](https://github.com/gasyoun/Uprava/blob/main/PROJECT_INTERLINKS.md)). Wave-1
recovers the WordSem→gloss decode inventory, counts sense frequency at **three cross-linked layers**
(WordNet synset → MW numbered sense → SIL semantic domain), publishes it as a kosha
`data/frequency/` sidecar with a manifest row, and wires ONE UI surface (kosha cards) showing
"N in this sense · M for the lemma" with an honest **attested-vs-estimated** two-tier badge. WSD
extension past the gold and the other three UI surfaces are wave-2.

Layered docs (read in this order):

- **Roadmap** — [ROADMAP_KOSHA_SENSE_FREQUENCY_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_SENSE_FREQUENCY_2026H2.md)
- **Architecture** — [ARCHITECTURE_KOSHA_SENSE_FREQUENCY.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_SENSE_FREQUENCY.md)
- **Implementation (wave-1, file-level)** — [IMPLEMENTATION_KOSHA_SENSE_FREQUENCY_WAVE1.md](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_SENSE_FREQUENCY_WAVE1.md)
- **Verification & risks** — [VERIFICATION_KOSHA_SENSE_FREQUENCY.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_SENSE_FREQUENCY.md)

Execution handoff: [H1453](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1453-Opus_kosha_sense-frequency-wordsem-3layer-wave1_22.07.26.md) (Opus 4.8 `claude-opus-4-8`).

---

## Decisions taken (interview, 22-07-2026)

| # | Fork | Ruling | Rationale |
|---|---|---|---|
| 1 | Ambition | **Full-corpus WSD** is the ultimate target; **wave-1 stops at 3-layer gold + one UI** | Bounded, verifiable first slice; the WSD extension is the risk-bearing part and is deferred to wave-2 |
| 2 | Primary sense unit | **3 parallel layers**: WordNet synset (native gold) → MW numbered sense → SIL semantic domain, all cross-linked | Matches "MW basis + semantic domains (Kulkarni)"; counting on the native synset first is lossless, projections carry the loss explicitly |
| 3 | MW sense-order defect | **MW's own order is sound; DCS's MW-*derived* sense order is broken.** Frequency attaches to MW's correct numbered senses; the DCS WordSem→sense projection is *validated against* MW, and disagreements are surfaced as a **DCS** finding (feeds M01 Ch6 "Senses: Inheritance and Order") | User correction — the defect is in DCS's derivation, not in MW; we never reorder MW |
| 4 | WSD engine (wave-2) | **Two witnesses: SCL scrape + LLM gloss-grounded**, must agree | User choice; WordSem gold now makes accuracy measurable, not just agreement |
| 5 | Deliverable | **Frequency dataset/layer + UI display** (no paper this wave) | User dropped the paper option; a publishable finding (decision #3) is logged to GTD, not forced |
| 6 | Decode prerequisite | **Agent recovers WordSem→gloss inventory from the DCS CoNLL-U releases first**; park as blocker only if that fails | The `WordSem` MISC key + Sanskrit WordNet synset inventory is the decode key; the stub sqlite's 9.3% is an undercount of the CoNLL-U coverage |
| 7 | Acceptance bar (wave-2 WSD) | **Two-witness + held-out gold accuracy** (SCL+LLM agree AND method clears ≥70% on held-out WordSem gold) | Strongest honesty gate for extended counts |
| 8 | UI honesty | **Two-tier badge**: every count split into *attested* (WordSem gold) vs *estimated* (WSD) — never silently blended | Learner-facing; provenance must be visible |
| 9 | Wave-1 UI surface | **kosha cards** only; pwg_ru article site + Cologne dict-web + VisualDCS are wave-2 | kosha cards already consume the lemma-frequency layer — smallest wiring |
| 10 | Dataset home | **kosha `data/frequency/`**, parallel to `lemma_frequency.tsv`; consumes VisualDCS WordSem — not a new repo | Audit-answered; mirrors the existing lemma-frequency sidecar exactly |

---

## Autonomy contract (verbatim — governs the unattended wave-1 agent)

- **On unplanned ambiguity:** apply the marked default in the relevant doc and **log it** (one line in
  `.ai_state.md` Dev Notes + a `LOG:` comment at the decision site), then keep going. Do **not** stall
  waiting for a human.
- **Stop conditions:** halt and hand back only if (a) the WordSem decode inventory cannot be recovered
  from the CoNLL-U releases after a genuine attempt (park as blocker, do the crosswalk-scaffolding parts
  that don't need it), or (b) the acceptance gate in
  [VERIFICATION](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_SENSE_FREQUENCY.md)
  cannot be met by any wave-1 step.
- **Commit authority:** per the handoff-scoped autonomy rule, wave-1 is authorized to commit → PR → merge
  without a further human ask. kosha is a guarded main-tree repo — **work in a worktree**, never the main
  checkout.
- **The fence (must NOT touch):**
  - Never overwrite human-reviewed MW / kosha `senses` / app_data — the sense-frequency layer is a
    **sidecar**, LEFT-JOINed at build time, exactly like `lemma_frequency`.
  - The SCL scrape (wave-2) is a **validation witness only** — never redistribute SCL/GPL content into
    kosha; store derived agreement flags, not scraped text. Licence (outreach
    [H057](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H057-Opus_Uprava_OUTREACH_2026-07-02_amba_kulkarni_scl_02.07.26.md))
    is still unresolved — treat as rights-gated.
  - Never auto-correct a DCS-vs-MW sense-order disagreement **into** canonical data; record it as a
    finding, leave the canonical senses untouched.

---

## Autonomy-readiness gate (Phase 4 verdict)

**PASS for wave-1.** Every wave-1 deliverable has an architecture spec, ordered implementation steps,
an acceptance criterion, and a named risk (see the four layer docs). No blocking fork remains inside a
wave-1 path — the one genuine prerequisite (WordSem decode recovery) has a marked default (recover from
CoNLL-U) and a logged park-fallback. The prior-art verdicts (below) are recorded; nothing wave-1
schedules duplicates an existing asset.

## Build-vs-reuse verdicts (prior-art, evidence-cited)

| Piece | Verdict | Evidence |
|---|---|---|
| Per-lemma frequency spine | **Reuse** | kosha [`lemma_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv) + `build_frequency_layer.py` |
| Per-token sense gold | **Reuse** | VisualDCS `WordSem` layer, 219/270 texts ([INTERLINKS §277](https://github.com/gasyoun/Uprava/blob/main/PROJECT_INTERLINKS.md)) |
| MW numbered-sense inventory | **Reuse** | kosha DB `senses` table, 692,403 senses ([manifest `kosha-full-db`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)) |
| semantic-domain layer | **Reuse** | [`semdom-amarakosha-crosswalk`](https://github.com/gasyoun/Uprava/blob/main/REUSE_INDEX.md) (A58) |
| MW→WordNet bridge | **Reuse** | FEATURES_INDEX C19 MW→WordNet→semdom bridge |
| MFS baseline consumer | **Reuse** | [`mfs_baseline.py`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/mfs_baseline.py) — explicitly waits for a corpus MFS |
| WSD engine (wave-2) | **Build thin + reuse witnesses** | kosha [`DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md`](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md) + SCL Reading Aid |

_Dr. Mārcis Gasūns_
