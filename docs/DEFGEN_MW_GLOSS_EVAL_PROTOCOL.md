# Definition-generation + gloss-grounded WSD eval over MW glosses — protocol + results

_Created: 11-07-2026 · Last updated: 15-07-2026_

**What this is.** The first definition-generation ("definition modeling") evaluation run on
Sanskrit lexicographic data from the CDSL side: a frozen 500-headword Monier-Williams sample,
four baseline arms, deterministic metrics + a gated LLM judge, and a gloss-grounded WSD
agreement pilot. Executes [H730](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H730-Fable_kosha_definition-generation-gloss-eval_11.07.26.md)
(= opportunity #3 of [ACL_METHOD_OPPORTUNITIES_SANSKRIT_2026.md](https://github.com/gasyoun/Uprava/blob/main/ACL_METHOD_OPPORTUNITIES_SANSKRIT_2026.md),
minted under [H667](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H667-Fable_Uprava_acl-method-mining-venue-watch_11.07.26.md)).
Venue targets: eLex 2027 · EURALEX 2028 · IJL.

**Prior art verdict (H730 step 1; Hellwig delta verified at paper level by the parked
rival H730 lane, grafted under
[H752](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H752-Fable_kosha_defgen-parked-lane-salvage_11.07.26.md)).**
No definition-generation or gloss eval exists in
[kosha](https://github.com/gasyoun/kosha) or
[csl-atlas](https://github.com/gasyoun/csl-atlas) (repo greps, 11-07-2026, zero hits;
kosha [EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md) covers
lookup-service gates only). The nearest published work,
[Hellwig et al. 2026 (ISCLS)](https://aclanthology.org/2026.iscls-1.2/), trains a
*supervised* WSD system over MW lexicographic definitions, with Sanskrit Sembank human
gold on DCS occurrences (343k connected tokens; code at
[OliverHellwig/sanskrit/papers/2026iscls](https://github.com/OliverHellwig/sanskrit/tree/master/papers/2026iscls))
— checked against the actual paper 11-07-2026 by the parked lane
([Uprava FINDINGS §67](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md)), which
closes the overlap check this section previously flagged as to-verify. Track (b) below is
therefore **not** novel as a task; the deltas are (a) zero-shot instruction LLMs instead
of a fine-tuned bi-encoder, (b) the CDSL/kosha data spine instead of Sanskrit Sembank,
and (c) inter-model agreement only — explicitly not an accuracy claim. Track (a),
definition generation for Sanskrit, has no prior art in the org or, to our knowledge,
the literature.

## Data (all pre-existing org assets — consumed, not rebuilt)

| Asset | Role | Source |
|---|---|---|
| A3 `mw_en_tm.json` (187,506 SLP1-keyed MW English glosses) | gold glosses + polysemy strata | [RussianTranslation/src](https://github.com/gasyoun/SanskritLexicography/tree/master/RussianTranslation/src) |
| E26 `lemma_frequency.tsv` (83,277 DCS lemmas, counts + rank) | frequency strata | [kosha data-v0.1.0 release](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0) |
| C15 `dcs_cdsl_xref.tsv` (DCS↔CDSL crosswalk, `in_cdsl=1` rows) | DCS lemma-id resolution | [csl-apidev/simple-search/dcs_xref](https://github.com/sanskrit-lexicon/csl-apidev/blob/main/simple-search/dcs_xref/dcs_cdsl_xref.tsv) |
| DCS 2026 `dcs_full.sqlite` (5.69M tokens, 754,726 sentences) | attestation sentences | [VisualDCS](https://github.com/gasyoun/VisualDCS) local mirror of the Digital Corpus of Sanskrit (Hellwig), CC BY 4.0 |

MW gloss text is public domain (1899); DCS sentences are CC BY 4.0 (attribution: Oliver
Hellwig, Digital Corpus of Sanskrit). The frozen sample is releasable under the kosha
public-tier data license (CC BY-SA 4.0) with those attributions.

## Frozen sample

Built by [scripts/defgen_build_sample.py](https://github.com/gasyoun/kosha/blob/main/scripts/defgen_build_sample.py)
(seed 730, deterministic): universe = SLP1 keys present in A3 ∩ E26 ∩ C15 (11,316 keys),
stratified 3×3:

- **frequency** by E26 `rank_all`: high ≤ 2,000 · mid 2,001–20,000 · low > 20,000
- **polysemy** by MW top-level sense-segment count (`' | '`-separated in A3): mono = 1 ·
  poly2_4 = 2–4 · poly5p ≥ 5

Target 56/cell (9 cells = 504); a candidate needs ≥ 3 usable DCS attestation sentences
(4–40 whitespace tokens, ≤ 2 sentences per work, shortest-first deterministic pick, max 5
kept). **Final n = 500** — the low/mono cell exhausts at 52 (157 candidates skipped for
< 3 usable sentences; every skip is logged in
[frozen_sample.meta.json](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/frozen_sample.meta.json)).
The meta also records **SHA-256 digests of all four inputs** (grafted under H752 from the
parked rival H730 lane, whose independently computed digests match the local input files
byte-for-byte — the two rival lanes provably consumed identical inputs).
The freeze is the committed files
[frozen_sample.tsv](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/frozen_sample.tsv) +
[attestations.jsonl](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/attestations.jsonl) —
scoring always runs against these, never against a re-derived join.

## Track (a): definition generation — four arms

[scripts/defgen_run_baselines.py](https://github.com/gasyoun/kosha/blob/main/scripts/defgen_run_baselines.py)
(temperature 0, resumable JSONL, DeepSeek caller adapted from the org-canonical
`build_corpus_lexicon.deepseek()`):

| Arm | Model | Input | Measures |
|---|---|---|---|
| A0_random_floor | none | seeded derangement of gold glosses | metric floor / judge discrimination |
| A1_chat_ctx | `deepseek-chat` | headword + grammar + ≤ 5 DCS attestations | grounded generation |
| A2_chat_noctx | `deepseek-chat` | headword + grammar only | parametric memorization of MW |
| A3_reasoner_ctx | `deepseek-reasoner` | same as A1 | second model baseline |
| F1_fable_ctx | `claude-fable-5` (in-session) | same as A1 | non-DeepSeek family (next-steps #6), H972 |

**Contamination caveat (load-bearing).** MW 1899 is public domain and certainly present in
LLM pretraining data. This eval therefore measures *reproduction + grounding*, not
generation from corpus evidence alone — that is exactly why A2 (no attestations) is an arm:
the A1−A2 delta isolates what corpus context adds on top of memorization. Any paper claim
must carry this framing.

**F1 arm methodology (H972, 15-07-2026).** The F1_fable_ctx arm adds the non-DeepSeek
model family called for by next-steps #6: candidate glosses were generated by the Claude
Code session itself (Fable 5, `claude-fable-5`), not via an API loop. To keep the gold
answer key structurally out of the generation context, the run implements the parked-lane
**gold-free inputs projection** (next-steps #7a, grafted under H752):
[scripts/defgen_fable_arm.py](https://github.com/gasyoun/kosha/blob/main/scripts/defgen_fable_arm.py)
`emit` writes batch files containing ONLY headword + grammar + attestations (the exact
`prompt_for(with_ctx=True)` text contract), the session writes glosses per batch, and
`assemble` validates 500/500 coverage and emits `gen_F1_fable_ctx.jsonl` in the standard
schema. No temperature control exists for an in-session arm (single greedy-ish pass, no
retries); the same MW-contamination caveat applies a fortiori — MW 1899 is certainly in
Claude's pretraining data, so F1 too measures reproduction + grounding, not pure
generation.

## Scoring

[scripts/defgen_score.py](https://github.com/gasyoun/kosha/blob/main/scripts/defgen_score.py):

- **Deterministic:** sacrebleu 2.6.0 corpus/sentence BLEU + chrF, plus bag-of-tokens F1.
  BERTScore deferred (no local torch stack) — chrF is the primary deterministic metric.
- **LLM judge (gated):** `deepseek-chat`, blinded to arm, adequacy 0–5 vs gold, instructed
  to judge meaning and ignore gold-side markup debris. Per the org guardrail and
  [JUDGE-BENCH](https://aclanthology.org/2025.acl-short.20/), judge scores never stand
  alone: gates are (1) Spearman ρ against chrF per arm, (2) separation of the A0 floor,
  and (3) a human-scored subsample before any paper-grade claim (not part of this run).
- **Gold-noise caveat:** A3 TM glosses carry markup-stripping artifacts (e.g. `catur` →
  "n. , 4 ( m.; and also ; & on and 98 ff. …"). Deterministic scores are depressed by gold
  noise for all arms equally; the judge is instructed around it. A gold-cleaning pass is a
  logged next step, not silently applied — the frozen gold is byte-stable.

## Track (b): gloss-grounded WSD — agreement pilot, by design not gold-scored

50 seeded poly5p headwords × ≤ 3 attestation sentences; `deepseek-chat` and
`deepseek-reasoner` each pick which numbered MW sense a sentence uses. Reported as
inter-model raw agreement + κ vs per-item uniform chance (1/k senses).

**Why no accuracy claim:** DCS carries per-token sense annotations (`m_wordsem`,
531,747 tokens in the 2026 dump) but the local `dcs_full.sqlite` has no table decoding
those numeric IDs to sense glosses, so no MW-sense gold can be derived here without an
external inventory. Recovering the DCS word-sense-ID inventory (from the DCS CoNLL-U
releases) and mapping it onto MW sense divisions is the concrete unlock for a gold-scored
WSD track — logged as a gap in the paper plan; adopting the
[Hellwig et al. 2026](https://aclanthology.org/2026.iscls-1.2/) eval split directly is the
alternative unlock (parked-lane observation, grafted under H752). Gold-scored sense
selection is therefore future work; this pilot establishes the harness + an agreement
ceiling.

## Results (11-07-2026 run)

All 500 items generated and judged in every arm (0 empty candidates after retries; one A2
item salvaged from a truncated JSON response, noted in-row).

| Arm | corpus BLEU | corpus chrF | mean token-F1 | judge adequacy 0–5 | judge~chrF Spearman ρ | mean words |
|---|---|---|---|---|---|---|
| A0_random_floor | 3.13 | 12.02 | 0.097 | 0.186 | 0.117 | 41.5 |
| A1_chat_ctx | 3.05 | 19.57 | 0.297 | 4.322 | 0.391 | 17.2 |
| A2_chat_noctx | 3.43 | 17.30 | 0.294 | 4.084 | 0.466 | 22.7 |
| A3_reasoner_ctx | 0.50 | 13.70 | 0.256 | 4.208 | 0.423 | 9.2 |
| F1_fable_ctx (15-07) | 5.14 | 24.35 | 0.340 | 4.600 | 0.415 | 17.1 |

Gold glosses average 41.5 words (median 26); every system under-generates senses relative
to gold.

**Judge gates.** (1) Floor separation: PASS — the judge scores the derangement floor 0.19
vs 4.1–4.3 for systems, so it is not fooled by register-matched random MW text.
(2) Judge~chrF: moderate positive (ρ 0.39–0.47 within system arms) — consistent with a
noisy gold reference; neither signal is degenerate. (3) Human-scored subsample: NOT yet
run — required before any paper-grade claim (next-steps #1).

**Findings.**

1. **BLEU is non-informative here** — the floor matches the systems (3.13 vs 3.05) because
   any MW-register English shares enough n-grams with a 40-word gold; chrF and token-F1
   both separate floor from systems cleanly. Drop BLEU in follow-ups.
2. **Corpus context adds little over parametric memorization**: A1 − A2 = +2.3 chrF,
   +0.003 token-F1, +0.24 judge. DeepSeek already "knows" MW (contamination caveat above);
   attestations mostly sharpen sense selection, not content. The paper claim must be framed
   as reproduction+grounding, and a post-1899 / non-MW-attested headword subset is the
   clean way to isolate real generation ability.
3. **Terseness is punished by surface metrics, not by the judge**: the reasoner writes the
   shortest glosses (9.2 words mean), scores lowest on chrF (13.7 — recall against long
   gold), yet the blinded judge puts it between the two chat arms (4.21). Metric choice
   changes the system ranking — exactly the JUDGE-BENCH scenario the gates exist for.
4. **Polysemy hurts, in every frequency band** (A1 per-cell chrF): poly5p is the worst
   polysemy band within high (18.9), mid (19.4) and low (22.4) frequency. The frequency
   gradient is inverted (low-frequency cells score *higher*, e.g. low/mono 33.5 vs
   high/mono 21.3) because high-frequency MW entries have much longer, more complex gold
   glosses — a stratification effect to keep in mind, not model skill at rare words.

Per-cell chrF, arm A1 (freq/polysemy):

| cell | chrF | cell | chrF | cell | chrF |
|---|---|---|---|---|---|
| high/mono | 21.30 | mid/mono | 27.51 | low/mono | 33.54 |
| high/poly2_4 | 20.62 | mid/poly2_4 | 28.47 | low/poly2_4 | 30.04 |
| high/poly5p | 18.91 | mid/poly5p | 19.42 | low/poly5p | 22.35 |

**F1 addendum (H972 run, 15-07-2026).** All 500 items generated and judged (0 empty).
F1 leads every arm on every metric, deterministic and judged alike: +4.78 corpus chrF
and +0.043 token-F1 over the best baseline (A1), and the blinded judge puts it first
(4.60 vs 4.21–4.32), with judge~chrF ρ 0.415 inside the healthy band and the A0 floor
still cleanly separated — the ranking agreement between surface metrics and judge that
the DeepSeek arms lacked (finding 3) holds here. Gloss length (17.1 words mean) sits at
A1's terseness, so the lead is content, not verbosity. The frequency-gradient inversion
and polysemy penalty replicate exactly (poly5p worst in every band):

Per-cell chrF, arm F1 (freq/polysemy):

| cell | chrF | cell | chrF | cell | chrF |
|---|---|---|---|---|---|
| high/mono | 26.82 | mid/mono | 34.82 | low/mono | 38.14 |
| high/poly2_4 | 27.08 | mid/poly2_4 | 35.31 | low/poly2_4 | 37.42 |
| high/poly5p | 21.76 | mid/poly5p | 23.73 | low/poly5p | 28.47 |

Caveat for any capability claim: the generating session authored this very protocol's
lane (same org), and in-session generation cannot be temperature-pinned or exactly
re-run — treat F1 as a strong-model reference point, not a reproducible baseline arm;
the reproducible path for a third family remains an API-called model.

**WSD agreement pilot** (50 poly5p lemmas × ≤3 sentences; 135/150 items with a valid pick
from both models): raw inter-model agreement **0.748**, per-item uniform chance 0.142,
**κ vs chance 0.706** — substantial agreement between independent models picking among a
mean ~7 MW senses. This bounds the task as well-posed for models; gold accuracy remains
unmeasurable until the DCS `m_wordsem` inventory is recovered (next-steps #2).

Full numbers: [scores_summary.json](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/scores_summary.json) ·
per-item: [scores_per_item.tsv](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/scores_per_item.tsv).

## Limitations + next steps (ranked)

1. **Human-scored subsample** — judge gate (3) above; blocked on operator time, sheet via
   `/review-sheet` when scheduled.
2. **DCS `m_wordsem` inventory recovery** → gold-scored WSD (the Hellwig-comparable track).
3. **Gold cleaning pass** over A3 artifacts (frozen sample v2; keep v1 byte-stable for
   comparability).
4. **Second reference** — D20 `heritage_dico_gloss.tsv` French glosses as a multi-reference
   or cross-lingual arm.
5. **BERTScore / embedding metric** once a local torch stack is justified.
6. **More models** — the arms are two DeepSeek variants + floor; adding a non-DeepSeek
   model family removes a same-vendor blind spot.
7. **Parked-lane design upgrades for the paper phase** (grafted from the rival H730 lane
   under [H752](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H752-Fable_kosha_defgen-parked-lane-salvage_11.07.26.md);
   the branch itself is deleted): (a) a **gold-free inputs projection** — generation
   agents read a derived inputs file (headword, grammar tag, attestation texts only),
   never the frozen sample itself, so the gold answer key is structurally out of the
   generation context rather than merely unprompted; (b) a **3-rater WSD re-run** (two
   baseline models + an independent judge-tier model as third rater) reporting pairwise
   Cohen's κ, 3-rater Fleiss κ and unanimity rate, upgrading the current 2-model
   agreement pilot.

## Reproduction

```
python scripts/defgen_build_sample.py          # rebuilds the join; the freeze is the committed files
python scripts/defgen_run_baselines.py --arm A0_random_floor
python scripts/defgen_run_baselines.py --arm A1_chat_ctx
python scripts/defgen_run_baselines.py --arm A2_chat_noctx
python scripts/defgen_run_baselines.py --arm A3_reasoner_ctx
python scripts/defgen_score.py metrics && python scripts/defgen_score.py judge
python scripts/defgen_score.py wsd && python scripts/defgen_score.py report
```

Requires local siblings `SanskritLexicography`, `csl-apidev`, `VisualDCS` (DCS sqlite) and
`DEEPSEEK_API_KEY` in `RussianTranslation/src/.env`.

## Provenance

Harness + protocol authored by Fable 5 (`claude-fable-5`), 11-07-2026, under H730.
F1_fable_ctx arm generated in-session and scored 15-07-2026 by Fable 5 (`claude-fable-5`)
under [H972](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H972-Fable_kosha_definition-generation-gloss-eval_15.07.26.md);
judge for F1: `deepseek-chat`, same blinded protocol.
Generation/judge models: `deepseek-chat` and `deepseek-reasoner` (DeepSeek API, temperature
0, 11-07-2026). Deterministic metrics: sacrebleu 2.6.0. Parked-lane salvage (this
section's canonical-sample ruling, the verified Hellwig delta, input SHA-256 digests,
next-steps #7) grafted by Fable 5 (`claude-fable-5`), 11-07-2026, under
[H752](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H752-Fable_kosha_defgen-parked-lane-salvage_11.07.26.md).

**Canonical frozen sample — exactly one.** H730 was executed by two racing sessions
([Uprava FINDINGS §67](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md)); the
rival lane parked a *different* 520-headword sample (also seed 730, different builder →
different membership) on a no-PR branch. Ruling (H752, 11-07-2026): **this 500-headword
sample ([frozen_sample.tsv](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/frozen_sample.tsv) +
[attestations.jsonl](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/attestations.jsonl),
seed 730, scored results above) is the single frozen sample of record.** The parked
520-headword sample was never scored, is NOT a second frozen set, and its branch
(`h730-defgen-eval-fable-lane`) was deleted after salvage. Any future sample is a v2
superseding v1 in writing, never a parallel alternative.

_Dr. Mārcis Gasūns_
