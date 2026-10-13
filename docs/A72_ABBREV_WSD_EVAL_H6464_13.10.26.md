# A72 E5 — abbreviation-disambiguation eval, WSD-shaped (H6464)

_Handoff: H6464 · Eval date: 13-10-2026 · Executor: OxAlpha (opencode/z-ai/glm-5.3-flash)_

**What this is.** A WSD-shaped eval for grammatical-abbreviation homographs in
dictionary entries, built from the csl-atlas abbreviation census payload
([abbrev_census.json](https://github.com/gasyoun/csl-atlas/blob/main/data/abbrev/abbrev_census.json),
448 polysemous legend strings, CC-BY-SA-4.0, sha256
`8af859fa…8718eddd`) + in-entry occurrences extracted from the local
csl-orig v02 corpus. Executes
[H6464](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6464-OxAlpha_kosha_a72-abbrev-disambiguation-eval_11.10.26.md)
per the A59 ([H5877](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_GOLD_EVAL.md)) /
A71 ([H6048](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_HYBRID_H6048.md))
protocol: deterministic in-data gold, pinned crc32 fold, honest negatives,
exact McNemar vs MFS. All artifacts in
[data/eval/abbrev_wsd_h6464/](https://github.com/gasyoun/kosha/blob/main/data/eval/abbrev_wsd_h6464/),
reproducible via `scripts/abbrev_wsd_h6464_eval.py`.

**Headline (context alone does not disambiguate; the dictionary identity is
the missing variable):** on 184 held-out in-entry occurrences of 23
grammatical-homograph legends, a context-blind-to-host `deepseek/deepseek-chat`
arm scores **60.3 %** accuracy (macro-F1 0.404) vs corpus-prior baselines
MFS **65.8 %** and census-majority **73.4 %** (uniform floor 29.4 %). LLM vs
MFS: b=26, c=36, exact two-sided McNemar **p = 0.253 — not significant**;
majority vs MFS p = 0.020. Zero API failures, zero parse failures (184/184
in range). No number is hand-tuned; the honest finding for the A72 teaser is
that per-dictionary deterministic gold is only partially recoverable from
entry context alone — near-duplicate cross-language senses
(`adjective/adjectif/adjektiv`) are unidentifiable without knowing the host
dictionary's legend language, which is exactly the legend-conditional
information a real reader has.

## Gold construction (deterministic, in-data only)

An **item** = one in-entry occurrence (`<ab>` or `<lex>` channel; `<lang>`
excluded) of a qualifying homograph legend inside a dictionary whose own
legend lists **exactly one** expansion for that label — the gold. Qualifying
legend = in the census collisionMatrix, has ≥ 2 deterministic
(dictionary → single expansion) legend rows with ≥ 2 distinct normalized
expansions among them, and ≥ 1 grammatical-category legend row (the
handoff's grammatical-homograph scope). 221 of 448 polysemous legends
qualify; the eval samples the **top 24 by occurrence mass** (stated scope
cap, `top_k_legends` in [items.meta.json](https://github.com/gasyoun/kosha/blob/main/data/eval/abbrev_wsd_h6464/items.meta.json)).

Candidates per item = the distinct normalized expansions across ALL
dictionaries' legends for that label (the full homograph inventory,
canonical `sorted()` order); normalization = casefold + punctuation strip +
whitespace collapse (so `Parasmaipada.`/`Parasmai-pada` collapse into one
sense; cross-language renderings like `masculine/masculin/masculinum` stay
distinct senses — see Unbuildable/Near-duplicates below). Gold matched iff
normalized pick == normalized gold.

- **Fold** — `crc32(f'{dict}:{file}:{line_no}:{occ_idx}') % 5 == 0` → test,
  else train (pinned, H5877 precedent; per-item fold recorded in
  [items.jsonl](https://github.com/gasyoun/kosha/blob/main/data/eval/abbrev_wsd_h6464/items.jsonl)).
- **Sampling** — per legend × fold, seeded `random.Random(6464)`: ≤ 12
  train + ≤ 8 test instances. Pool funnel: 24 legends × 18 deterministic
  dictionaries → 588,203 extracted in-corpus occurrences → sampled
  **460 items** (276 train / 184 test; 23 legends have test items).
- **Denominators** — every sense row in
  [scores.json](https://github.com/gasyoun/kosha/blob/main/data/eval/abbrev_wsd_h6464/scores.json)
  carries `n_gold` / `n_pred` / `tp`; macro-F1 averages only senses with
  `n_gold > 0` in the test fold.

**Unbuildable ledger.** Legends/dictionary-pairs where the host legend lists
> 1 expansion for the label have no deterministic gold and are recorded, never
hand-labelled —
[unbuildable.json](https://github.com/gasyoun/kosha/blob/main/data/eval/abbrev_wsd_h6464/unbuildable.json)
covers all 221 qualifying legends; e.g. `P.` in AP90 (2 expansions:
"Parasmaipada." / "Pāṇini's Aṣṭādhyāyī.") and in BOP (compound expansion,
2 spelling variants) are excluded from the gold pool. No manual annotation
happened anywhere in this eval, so the cross-family second-annotator / κ
clause is **N/A** (channel labels `<ab>` 336 / `<lex>` 124 are recorded per
item instead).

## Arms

| Arm | Method | n_scored / 184 | Accuracy | macro-F1 |
|---|---|---|---|---|
| llm | `deepseek/deepseek-chat` (OpenRouter), temperature 0, JSON pick among numbered candidates, entry context with occurrence marked, blind to host dictionary | 184 | **0.6033** | 0.4042 |
| mfs | per-legend train-fold majority sense (crc32 train instances only) | 184 | **0.6576** | 0.3173 |
| majority | per-legend census-wide majority: the deterministic dictionary with the most recorded occurrences, its expansion (census `labelTable.tags` weights) | 184 | **0.7337** | 0.3562 |
| floor | deterministic round-robin uniform draw over the candidate inventory | 184 | 0.2935 | 0.2643 |

McNemar vs MFS (exact two-sided, paired on the 184 items; skipped/unparsable
predictions count as wrong — none occurred):

| arm vs mfs | b (arm✓ mfs✗) | c (arm✗ mfs✓) | p |
|---|---|---|---|
| llm | 26 | 36 | 0.252854 |
| majority | 23 | 9 | 0.020062 |
| floor | 16 | 83 | < 0.0001 |

**Reading.** The corpus prior beats context-only prompting, replicating the
A59/A71 direction on a new surface; unlike H5877 the LLM-vs-MFS gap is not
significant at n=184 (discordant mass 62). The per-sense table localizes the
LLM's loss: `adjektiv` (n_gold 8, R 0.0), `accusatif`/`accusative` splits,
and `accusative case or according` (n_gold 3, 0/3) — the model picks the
English-legend rendering where the host dictionary is German/French. That is
not a prompting failure but an identifiability bound of the context-only
task shape: the disambiguating signal (host dictionary identity) is
deliberately withheld from every arm, and MFS exploits it as a frequency
prior. The A72 teaser should quote this as motivation for legend-conditional
(i.e. dictionary-aware) disambiguation, not as an LLM quality verdict.

## Reproduction

```sh
python scripts/abbrev_wsd_h6464_eval.py build     # deterministic (seed 6464, crc32 fold)
python scripts/abbrev_wsd_h6464_eval.py run-llm   # needs OpenRouter key (opencode auth store)
python scripts/abbrev_wsd_h6464_eval.py score
python scripts/abbrev_wsd_h6464_eval.py validate  # PASS = scores.json byte-recomputes
```

Inputs pinned in
[items.meta.json](https://github.com/gasyoun/kosha/blob/main/data/eval/abbrev_wsd_h6464/items.meta.json):
census payload sha256, corpus root, the 18 corpus files read (csl-orig v02,
`<dict>/<dict>.txt` entry lines), fold rule, seeds, caps. Requires the
csl-atlas census payload + csl-orig v02 checkout (read-only external
siblings; no corpus bytes committed beyond the derived sampled items).

## Two-gates note

Research metrics only; nothing here relaxes any shipping gate.

## Provenance

Harness + run by GLM-5.3-Flash (opencode, ZCode session), 13-10-2026, under
H6464 (claim 2026-10-13T00:14Z). LLM arm: `deepseek/deepseek-chat` via
OpenRouter, temperature 0, max_tokens 30, 6 workers, 2026-10-13, 83 s wall,
0 errors. Census payload + csl-orig corpus consumed, not rebuilt.

_Гасунс_
