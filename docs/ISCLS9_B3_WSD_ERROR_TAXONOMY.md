# ISCLS-9 B3 — LLM error taxonomy vs corpus-MFS: a wrong-context finding

> **Update 06-10-2026 (H6048):** the context-join fix has landed and the LLM
> arm was re-run on true contexts — the in-context score is **62.3%**
> (vs the 54.3% measured here under broken context; MFS 84.3% unchanged).
> The tables below are the historical pre-fix analysis; see
> [ISCLS9_B3_WSD_HYBRID_H6048.md](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_HYBRID_H6048.md).

_Created: 06-10-2026 · Last updated: 06-10-2026_

**What this is.** The error analysis of every LLM miss on the frozen 300-item B3
WSD set ([ISCLS9_B3_WSD_GOLD_EVAL.md](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_GOLD_EVAL.md):
gloss-grounded LLM 54.3% vs corpus-MFS 84.3%, exact McNemar p<0.0001), executed as
[H6047](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6047-GLM_kosha_b3-wsd-error-analysis_04.10.26.md).
Deliverables: this report, the reproducible notebook
[error_taxonomy.ipynb](https://github.com/gasyoun/kosha/blob/main/data/eval/wsd_iscls9/error_taxonomy.ipynb)
with committed outputs, [error_taxonomy.tsv](https://github.com/gasyoun/kosha/blob/main/data/eval/wsd_iscls9/error_taxonomy.tsv)
(one row per miss) and [taxonomy_summary.json](https://github.com/gasyoun/kosha/blob/main/data/eval/wsd_iscls9/taxonomy_summary.json).
Every rule below is deterministic and re-runnable; nothing was hand-classified.

## Headline finding — the LLM arm saw the wrong sentence in 298/300 items

`scan_join` in [scripts/wsd_iscls9_eval.py](https://github.com/gasyoun/kosha/blob/main/scripts/wsd_iscls9_eval.py)
records `token.sentence_id` — the **internal INTEGER** key of `token` — as the item
sentence id, but `cmd_build` attaches the context text with
`SELECT text_sandhied FROM sentence WHERE sent_id = ?` — the **external TEXT** id.
The two key spaces are unrelated numberings, so every item was paired with the
text of a *different* sentence.

Verified against `dcs_full.sqlite` (exact `lemma_id` join, no string heuristics):

| check | result |
|---|---|
| TRUE sentence (`sentence.id = token.sentence_id`) contains the target lemma | **300 / 300** |
| SHOWN sentence (`sentence.sent_id = <internal int>`) contains the target lemma | **2 / 300** |
| shown text == true text | **0 / 300** |

Worked example — item `101437|pitf` (gold `pitf#2` "father and mother, parents"):
shown to the model: *nāgajā ca kapālikā upari bhavati* (no pitṛ-token anywhere);
true sentence: *alaṃ sundari kranditvā jīvataḥ **pitarau** tava*.

**Consequence.** The measured 54.3% is a **context-free** gloss-prior score, not
in-context WSD. The corpus-MFS baseline (84.3%) and the floor (31.9%) are unaffected
— neither ever reads sentence text. The one-line fix (for H6048, not applied here —
H5877 artifacts stay frozen per the H1588 precedent): attach text with
`WHERE id = ?` (or key both sides on `sent_id`), then re-run the LLM arm.

## Taxonomy — primary classes (mutually exclusive, verifiable sum)

Precedence rules (first match wins; parameters in `taxonomy_summary.json`):
`ctx_mismatch` → `sandhi_fusion` → `homoglossia` → `gloss_deficit` → `rare_sense`
→ `context_ambiguous` (residual).

| class | n | share | rule |
|---|---|---|---|
| `ctx_mismatch` | 136 | 99.3% | target lemma absent from the sentence the LLM was shown |
| `sandhi_fusion` | 1 | 0.7% | target present but its surface form is not a standalone word (fused) |
| `homoglossia` / `gloss_deficit` / `rare_sense` / `context_ambiguous` | 0 | 0.0% | starved by the ctx_mismatch dominance |
| **sum check** | **137** | **100%** | `assert` in the notebook; Σ = n_misses = 137 |

Under a broken context the four mission classes (sandhi junctions, homoglossia,
gloss deficit, rare senses) cannot express themselves as primary causes; they are
measured instead as **soft diagnostic tags** below, and become primary-capable
only after the context fix + re-run.

## Soft diagnostic tags over all 137 misses (multi-label)

| tag | n | share | rule |
|---|---|---|---|
| `gold_top1_missed` | 100 | 73.0% | gold was corpus-rank-1; the model picked rank ≥ 2 |
| `gloss_deficit` | 61 | 44.5% | gold gloss as shown < 3 content words, < 40 chars, or truncated at the 100-char storage cap mid-word |
| `prior_bias` | 30 | 21.9% | model picked a rank-1/2 gloss while gold ranks lower |
| `rare_sense` | 19 | 13.9% | gold rank ≥ 4 or corpus share (`sense_frequency.tsv:lemma_share`) < 10% |
| `homoglossia` | 0 | 0.0% | gold↔picked gloss content-word Jaccard ≥ 0.5 (sensitivity: 7 at ≥ 0.2; median Jaccard 0.071) |
| MFS right where LLM missed | 100 | 73.0% | both wrong on 37 |

**Reading.** With no usable context the model fell back to a *prototypical-gloss*
policy: in 102/137 misses the gold was the corpus-most-frequent (rank-1) sense —
i.e. frequency priors alone would have recovered most of them — yet the model
preferred dictionary-adjacent rank-2/3 glosses (63 + 38 picks). Homoglossia is
**not** a driver in this set (median gloss Jaccard 0.071): MW sense glosses are
lexically distinct, so the mission's "омоглоссия" class is measured honestly at 0
at the pre-declared 0.5 threshold. Gloss truncation at the 100-char storage cap
marks 44.5% of misses — a fixable prompt-side deficit for the re-run.

## Consequences and wiring

1. **H6048 (MFS+LLM hybrid)** must land the context-join fix and re-run the LLM
   arm *before* tuning any hybrid threshold — the current 54.3% understates what
   an in-context LLM leg can contribute, and the honest-negative framing of the
   paper currently conflates "LLM loses to MFS" with "LLM had no context".
2. **ISCLS-9 B3 paper** (`papers/iscls9_b3/`, private; deadline 20-10-2026 AoE):
   the 54.3%-vs-84.3% comparison and its McNemar claim need re-measurement after
   the fix; MFS/floor/k-strata on the MFS side stand. This report is the input the
   paper's error-analysis section and the new paper-ID (ruled A2=+2) build on.
3. **Precedent discipline**: as with H1588 (FINDINGS §1569), the frozen H5877
   artifacts are NOT rewritten; the fix lands forward in H6048 with a fresh,
   byte-reproducible fold pin.

_Гасунс_
