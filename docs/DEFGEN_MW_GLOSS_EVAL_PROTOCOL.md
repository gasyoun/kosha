# Definition-generation + gloss-grounded WSD eval over MW glosses — protocol + results

_Created: 11-07-2026 · Last updated: 11-07-2026_

**What this is.** The first definition-generation ("definition modeling") evaluation run on
Sanskrit lexicographic data from the CDSL side: a frozen 500-headword Monier-Williams sample,
four baseline arms, deterministic metrics + a gated LLM judge, and a gloss-grounded WSD
agreement pilot. Executes [H730](https://github.com/gasyoun/Uprava/blob/main/handoffs/H730-Fable_kosha_definition-generation-gloss-eval_11.07.26.md)
(= opportunity #3 of [ACL_METHOD_OPPORTUNITIES_SANSKRIT_2026.md](https://github.com/gasyoun/Uprava/blob/main/ACL_METHOD_OPPORTUNITIES_SANSKRIT_2026.md),
minted under [H667](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H667-Fable_Uprava_acl-method-mining-venue-watch_11.07.26.md)).
Venue targets: eLex 2027 · EURALEX 2028 · IJL.

**Prior art verdict (H730 step 1).** No definition-generation or gloss eval exists in
[kosha](https://github.com/gasyoun/kosha) or
[csl-atlas](https://github.com/gasyoun/csl-atlas) (repo greps, 11-07-2026, zero hits;
kosha [EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md) covers
lookup-service gates only). The nearest published work,
[Hellwig et al. 2026](https://aclanthology.org/2026.iscls-1.2/), does WSD *from* lexicographic
definitions on the DCS side; per the H667 mining pass the CDSL side of the crosswalk is
untouched. The ACL Anthology landing page exposes no abstract; a PDF-level overlap check
against their data release is a flagged to-verify for the paper phase, not for this protocol.

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

**Contamination caveat (load-bearing).** MW 1899 is public domain and certainly present in
LLM pretraining data. This eval therefore measures *reproduction + grounding*, not
generation from corpus evidence alone — that is exactly why A2 (no attestations) is an arm:
the A1−A2 delta isolates what corpus context adds on top of memorization. Any paper claim
must carry this framing.

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
WSD track — logged as a gap in the paper plan. Hellwig-style sense selection *with gold*
is therefore future work; this pilot establishes the harness + an agreement ceiling.

## Results (11-07-2026 run)

RESULTS_TABLES_PLACEHOLDER

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
Generation/judge models: `deepseek-chat` and `deepseek-reasoner` (DeepSeek API, temperature
0, 11-07-2026). Deterministic metrics: sacrebleu 2.6.0.

_Dr. Mārcis Gasūns_
