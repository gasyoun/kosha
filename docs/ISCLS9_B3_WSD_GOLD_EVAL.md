# ISCLS-9 B3 — gold-scored gloss-grounded WSD over the DCS WordSem fold: protocol + results

_Created: 04-10-2026 · Last updated: 04-10-2026_

**What this is.** The gold-scored completion of the WSD track that
[DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md)
left as a 2-model agreement pilot: sense selection scored against a deterministic
gold derived purely from committed data — the DCS `m_wordsem` token annotations
(531,747 tagged tokens) resolved onto MW sense divisions via
[data/frequency/wn_to_mw_map.tsv](https://github.com/gasyoun/kosha/blob/main/data/frequency/wn_to_mw_map.tsv)
(exact|overlap rows only). No manual annotation anywhere. Executes the WSD half of
[H5877](https://github.com/gasyoun/Uprava/blob/main/handoffs/H5877-OxAlpha_kosha_iscls9-b3-full-paper_04.10.26.md)
(ISCLS-9 full paper B3, deadline 20-10-2026 AoE); the definition-generation half
reuses the verified H730/H972/H2408 results unchanged.

**Headline (honest negative for prompting):** on 300 held-out polysemous items from the
500-headword frozen-sample universe, a gloss-grounded `deepseek/deepseek-chat` arm scores
**54.3 %** accuracy against a corpus-frequency MFS baseline of **84.3 %** on identical items
(uniform floor 31.9 %; exact McNemar two-sided p < 0.0001, 100 vs 10 discordant pairs).
The gap widens with inventory size: 0.700 → 0.183 from k = 2 to k ≥ 6 for the LLM while
MFS degrades only 0.940 → 0.676. Prompting is not the path to this task; the contribution
is the deterministic gold + reproducible harness, and the paper reports the negative result
per the H5877 refutation clause (no inflated claims).

## Gold construction (deterministic, in-data only)

An **item** = one DCS sentence × one lemma. From the WordSem join
(`token.m_wordsem` ≠ ∅, `lemma_id` → SLP1 via the `lemma` table, `(synset, lemma)` present in the
resolved wn→mw map), the held-out fold keeps items where:

- the fold test — `crc32(sent_id) % 5 == 0` (≈20 %), **pinned** (see integrity note);
- the lemma has ≥ 2 attested MW senses in
  [sense_frequency.tsv](https://github.com/gasyoun/kosha/blob/main/data/frequency/sense_frequency.tsv)
  (mw layer, attested rows) — polysemous only; inventories > 15 senses skipped (none hit);
- the WordSem gold sense lies inside that attested inventory (filter never fired).

Gold = `wn_to_mw_map` row's `lemma#ord`. Universe restricted to the 500 defgen
frozen-sample lemmas — the paper's two tracks share one headword universe.
Pool funnel: 531,747 tagged → 26,570 gold-mapped (frozen-lemma, all folds) → 5,115 test
items → 4,100 eligible polysemous (1,015 mono skipped, 0 gold-outside, 7 same-sentence
gold conflicts kept-first and counted) → seed-5877 sample **n = 300** (82 unique lemmas;
k: min 2 / median 3 / max 12; gold is the rank-1 sense in only 33.7 % of items — the
sample is not trivially MFS).

**Fold integrity note (data-integrity finding).** `wsd_core.fold_of_sentence` keys on
Python `hash(str)`, which CPython randomizes per process (`PYTHONHASHSEED` unset): every
rerun of the H1588 held-out eval sees a *different* 20 % split, so its published
`wsd_heldout_eval.json` accuracy (0.8396, n 71,892) is stable in expectation but **not
reproducible byte-for-byte**, despite its own docstring claiming determinism. This script
pins its own fold (`zlib.crc32`) and re-derives the MFS baseline under it — it does not
silently rewrite H1588 artifacts. Anonymised [integrity] issue filed; H1588 artifacts
stand as computed under one process seed.

## Arms

| Arm | Method | n | Accuracy |
|---|---|---|---|
| llm | `deepseek/deepseek-chat` (OpenRouter), temperature 0, JSON pick among numbered glosses given IAST context sentence | 300 | **0.5433** |
| mfs | train-fold (crc32) majority sense per lemma, paired items only | 300 | **0.8433** |
| floor | uniform 1/k | 300 | 0.3194 (mean 1/k) |

Paired: LLM-right/MFS-wrong 10, LLM-wrong/MFS-right 100 — exact McNemar two-sided
p < 0.0001. Zero API failures (300/300 parsed in range).

Accuracy by inventory size k (LLM / MFS):

| k | n | llm | mfs |
|---|---|---|---|
| 2 | 100 | 0.700 | 0.940 |
| 3 | 55 | 0.545 | 0.855 |
| 4–5 | 74 | 0.676 | 0.865 |
| 6+ | 71 | 0.183 | 0.676 |

**Error classes** (manual eyeball of wrong items, to be systematised only if a human-scored
pass is scheduled): fine-granularity near-misses inside one gloss family (pitṛ-
"father+mother (du.)" vs "the Fathers/ancestors"), literal-vs-metaphorical splits (phala-
"fruit" vs "fruit = retribution"), and cross-POS homonymy (mad- pronoun base vs mad- "to
gladden"). Consistent with the gold's corpus-usage grounding: MFS exploits the usage prior
the WordSem tagging itself encodes, while one-sentence gloss matching cannot.

**Comparison anchor.** H1588's unpinned MFS number (0.8396 over all mapped test tokens,
mono included) sits where the pinned re-derivation lands (0.8433 poly-only on this
sample) — the fold randomization moved the estimate, not the conclusion.

## Reproduction

```sh
python scripts/wsd_iscls9_eval.py build --frozen-only --n 300   # deterministic (seed 5877)
python scripts/wsd_iscls9_eval.py run-llm                       # needs OpenRouter key (opencode auth store)
python scripts/wsd_iscls9_eval.py score
python scripts/wsd_iscls9_eval.py validate                      # PASS = scores.json byte-recomputes
```

Inputs hashed in [items.meta.json](https://github.com/kosha/blob/main/data/eval/wsd_iscls9/items.meta.json)
(dcs_full.sqlite 5.7 GB included). Requires local sibling `VisualDCS` (DCS 2026 dump).
One-command score-only validation: `python scripts/wsd_iscls9_eval.py validate`.

## Provenance

Harness + run by GLM-5.3-Flash (ZCode session), 04-10-2026, under H5877. LLM arm:
`deepseek/deepseek-chat` via OpenRouter, temperature 0, max_tokens 30, 4 workers,
2026-10-04T07:48–07:52Z. Gold/inventory data: pre-existing committed kosha assets
(H1588 spine), consumed not rebuilt.

_Гасунс_
