# Definition-generation + gloss-grounded WSD eval over MW glosses (H730 protocol)

_Created: 11-07-2026 · Last updated: 11-07-2026_

Executable brief: [H730](https://github.com/gasyoun/Uprava/blob/main/handoffs/H730-Fable_kosha_definition-generation-gloss-eval_11.07.26.md)
(opportunity #3 in [ACL_METHOD_OPPORTUNITIES_SANSKRIT_2026.md](https://github.com/gasyoun/Uprava/blob/main/ACL_METHOD_OPPORTUNITIES_SANSKRIT_2026.md)).
Run by Fable 5 (`claude-fable-5`), 11-07-2026. Venue targets: eLex 2027 · EURALEX 2028 · IJL.

## 1. What is evaluated, and why

Two tasks from the 2025–2026 definition-modeling literature, run for the first time on the
CDSL side of the Sanskrit lexicographic ecosystem:

- **Track A — definition generation.** Given a Sanskrit headword and up to 3 corpus
  attestation sentences, a model produces a concise English dictionary gloss; scored
  against the Monier-Williams (1899) gold gloss.
- **Track B — gloss-grounded WSD (agreement pilot).** Given one attestation sentence and
  MW's own numbered sense divisions for the headword, a model selects the sense realized
  in that occurrence.

**Relation to prior art.** [Hellwig et al. 2026 (ISCLS)](https://aclanthology.org/2026.iscls-1.2/)
already train a *supervised* WSD system over MW lexicographic definitions, with Sanskrit
Sembank human gold on DCS occurrences (343k connected tokens; code at
[OliverHellwig/sanskrit/papers/2026iscls](https://github.com/OliverHellwig/sanskrit/tree/master/papers/2026iscls)).
Track B here is therefore **not** novel as a task; the delta is (a) zero-shot instruction
LLMs instead of a fine-tuned bi-encoder, (b) the CDSL/kosha data spine instead of SSB,
and (c) — since no human gold exists on our side yet — an **inter-model agreement pilot**,
explicitly not an accuracy claim. Track A (definition generation for Sanskrit) has no
prior art in the org or, to our knowledge, in the literature
(prior-art sweep 11-07-2026: no gloss-generation eval in
[kosha](https://github.com/gasyoun/kosha) /
[csl-atlas](https://github.com/gasyoun/csl-atlas) / csl-standards; the nearest asset is
the Sa→Ru translation bake-off harness
[h178_eval_bakeoff.py](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/h178_eval_bakeoff.py),
whose sampling / κ / ρ discipline this protocol reuses).

## 2. Data sources (consumed in place, never copied)

| Asset | File | Role |
|---|---|---|
| A3 | [mw_en_tm.json](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/mw_en_tm.json) (187,506 SLP1-keyed MW glosses, senses `\|`-separated) | gold glosses + sense inventory + polysemy stratum |
| C15 | [dcs_cdsl_xref.tsv](https://github.com/sanskrit-lexicon/csl-apidev/blob/master/simple-search/dcs_xref/dcs_cdsl_xref.tsv) (DCS↔CDSL crosswalk) | headword → DCS lemma id |
| E26 | [lemma_frequency.tsv](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv) (DCS-derived frequency layer) | frequency stratum |
| — | `dcs_full.sqlite` (local data layer of [VisualDCS](https://github.com/gasyoun/VisualDCS), DCS 2026 CoNLL-U → SQLite; 755k sentences, 5.7M tokens) | attestation sentences |

MW gloss text is public domain (1899); the frozen sample (which embeds gold senses and
DCS attestation sentences) is released under the kosha data license (CC BY-SA 4.0,
[LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md)).

## 3. Frozen sample

Built once by [scripts/build_defgen_sample.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_defgen_sample.py)
(seed 730) and **frozen** as
[data/eval/defgen/frozen_sample_v1.jsonl](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/frozen_sample_v1.jsonl)
with input SHA-256 provenance in the sibling
[frozen_sample_v1.meta.json](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/frozen_sample_v1.meta.json).
The builder exists for provenance/reproduction; re-running it must never silently shift
the sample under scored outputs (MWSA-style frozen-gold discipline, after
[HUMAN_GOLD_PROTOCOL.md](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/gold/HUMAN_GOLD_PROTOCOL.md)).

- **Universe:** SLP1 keys present in A3 ∩ C15 (`in_cdsl=1`) ∩ E26, with ≥3 distinct DCS
  attestation sentences (counted live from the DB — C15's own `token_count` column
  undercounts against DCS-2026 and is not used).
- **Strata:** 3 frequency terciles (E26 `count_all`) × 4 polysemy bands (A3 sense count:
  1 / 2–3 / 4–6 / 7+), equal quotas over 12 strata, target 520; shortfalls redistributed
  deterministically to the best-attested remaining candidates.
- **Attestations:** per headword, the 3 lowest-`sent_id` sentences of 4–60 whitespace
  words containing the lemma (relaxed to any length only if fewer than 3 survive the
  filter). Selection is model-independent and deterministic.

## 4. Models

| Role | Model | Access |
|---|---|---|
| Baseline A | Haiku 4.5 (`claude-haiku-4-5-20251001`) | Claude Code Workflow agents |
| Baseline B | Sonnet 5 (`claude-sonnet-5`) | Claude Code Workflow agents |
| Judge + 3rd WSD rater | Fable 5 (`claude-fable-5`) | session model |

The judge is deliberately **excluded from the baseline pool** (no self-judging). Known
limitation: all three are Anthropic models — a cross-vendor baseline (e.g. DeepSeek) is
queued as follow-up work, as is a human-scored subsample, before any paper-grade claim.

## 5. Track A — definition generation

**Prompt (pinned).** Per item the model receives: headword (IAST), grammar tag, up to 3
attestation sentences (IAST, sandhied), and the instruction:

> Write a concise English dictionary gloss for this Sanskrit headword, in the style of a
> 19th-century Sanskrit–English dictionary: short sense phrases, not sentences. Separate
> distinct senses with " | "; within a sense, comma-separate synonyms. At most 25 words
> total. Output the gloss only — no etymology, no commentary.

Attestations ground the generation; the model is not told the MW gloss — generation
agents read a **gold-free inputs projection**
([data/eval/defgen/defgen_inputs_v1.jsonl](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/defgen_inputs_v1.jsonl):
`slp1`, `iast`, `grammar`, attestation texts only), never the frozen sample itself, so
the gold answer key is structurally out of their context. **Contamination
caveat:** MW is public domain and certainly in every model's pretraining data, so Track A
measures *reconstruction* (memory + inference), not pure inference from attestations; the
frequency × polysemy strata exist precisely so the memorization-vs-generalization gradient
(high-frequency memorized vs rare-headword inferred) is visible in the breakdown.

**Deterministic metrics** ([scripts/score_defgen.py](https://github.com/gasyoun/kosha/blob/main/scripts/score_defgen.py) `defgen`):
corpus chrF2 (primary — glosses are short, BLEU is brittle there), corpus BLEU
(secondary, comparability), per-item best-sense chrF (max sentence-chrF over individual
gold senses — "did it nail at least one sense"), all broken down by stratum. BERTScore is
deferred (no local `bert_score` install; queued as follow-up).

**LLM-judge** (gated per [JUDGE-BENCH](https://aclanthology.org/2025.acl-short.20/)):
Fable 5 scores every item 0–2 against the gold senses (2 = at least one gold sense
meaning-equivalently captured · 1 = related but imprecise · 0 = wrong/hallucinated), with
a pinned rubric prompt. Judge scores are **never reported alone**: Spearman ρ against
chrF per item accompanies them, and any paper-grade use requires a human-scored subsample
(guardrail inherited from H730).

## 6. Track B — gloss-grounded WSD (agreement pilot)

Subsample: 100 polysemous headwords (sense count ≥4) drawn deterministically (seed 731)
from the frozen sample; one attestation each (the first frozen one). Each rater (Haiku
4.5, Sonnet 5, Fable 5) sees the sentence, the target form, the headword and MW's
numbered senses, and returns the sense number realized in that occurrence (0 = none
fits). Reported ([scripts/score_defgen.py](https://github.com/gasyoun/kosha/blob/main/scripts/score_defgen.py) `wsd`):
pairwise exact agreement, pairwise Cohen's κ, 3-rater Fleiss κ, unanimity rate. **No
accuracy is reported** — there is no human gold on this side yet; agreement bounds how
far the task is from well-posed, nothing more. Accuracy claims require either SSB-style
annotation of our sample or adoption of the Hellwig 2026 eval split.

## 7. Results

Filled in the same pass as the runs — see
[data/eval/defgen/RESULTS_DEFGEN_WSD_MW_2026.md](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/RESULTS_DEFGEN_WSD_MW_2026.md)
for the scored tables (kept beside the outputs so numbers and artifacts travel together).

## 8. Reproduction

```sh
python scripts/build_defgen_sample.py        # frozen — do NOT re-run under scored outputs
# generation + judging run as Claude Code Workflow fan-outs (prompts pinned above);
# raw model outputs land in data/eval/defgen/outputs/
python scripts/score_defgen.py defgen --hyp data/eval/defgen/outputs/defgen_haiku45.jsonl \
    --judge data/eval/defgen/outputs/judge_haiku45.jsonl
python scripts/score_defgen.py defgen --hyp data/eval/defgen/outputs/defgen_sonnet5.jsonl \
    --judge data/eval/defgen/outputs/judge_sonnet5.jsonl
python scripts/score_defgen.py wsd --files data/eval/defgen/outputs/wsd_haiku45.jsonl \
    data/eval/defgen/outputs/wsd_sonnet5.jsonl data/eval/defgen/outputs/wsd_fable5.jsonl
```

## 9. Known limitations (honest list)

1. Same-vendor baselines (three Anthropic models) — cross-vendor run queued.
2. Pretraining contamination on MW (mitigated analytically via strata, not eliminated).
3. No human gold for either track yet — Track A leans on gold-reference metrics + gated
   judge; Track B reports agreement only.
4. BERTScore deferred; chrF2/BLEU only.
5. D20 Heritage glosses (French) are **not** used in v1 — the eval is MW-only; the
   Heritage track needs a French-gloss protocol of its own.
6. Single generation per item (no self-consistency sampling); temperature is whatever the
   harness default is — not independently pinned.

_Dr. Mārcis Gasūns_
