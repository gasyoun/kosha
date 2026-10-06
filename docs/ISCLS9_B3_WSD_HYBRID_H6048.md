# ISCLS-9 B3 — MFS+LLM hybrid WSD: an honest negative (H6048)

_Created: 06-10-2026 · Last updated: 06-10-2026_

**What this is.** The MFS+LLM hybrid attempt over the frozen 300-item B3 WSD
set, executing [H6048](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6048-GLM_kosha_wsd-hybrid-mfs-llm_04.10.26.md)
on the [H6047 error taxonomy](https://github.com/gasyoun/kosha/blob/main/docs/ISCLS9_B3_WSD_ERROR_TAXONOMY.md)
as input. Mission test: beat corpus-MFS **84.3%** on the same B3 split with
exact two-sided McNemar **p<0.05**, or record an honest negative with
dissection. **Verdict: honest negative after 4 tries** (stop cap 8). All
artifacts in [data/eval/wsd_h6048_hybrid/](https://github.com/gasyoun/kosha/blob/main/data/eval/wsd_h6048_hybrid/),
reproducible via `scripts/wsd_h6048_hybrid.py` (`validate` = PASS, MFS
continuity vs H5877 byte-confirmed).

## 1. The context-join fix landed and lifted the LLM arm +8.0 pts

Per H6047's prescription, the H5877 items were inherited **verbatim** (same
300 items, gold, candidates — sha256-pinned in `items.meta.json`) and the
context sentence re-attached with the corrected join
(`sentence WHERE id = token.sentence_id`). Verified on rebuild:
context differs from the broken text **300/300**; true sentence contains the
target lemma **300/300**.

Re-run of the identical deepseek/deepseek-chat arm (temp 0, JSON pick) with
true contexts:

| arm | accuracy |
|---|---|
| LLM, broken context (H5877, frozen) | 54.3% |
| **LLM, true context (this lane)** | **62.3%** |
| corpus-MFS (unchanged, continuity-checked) | **84.3%** |
| floor | 31.9% |

McNemar LLM-vs-MFS (true context): b=21, c=87, p<0.0001 — the in-context LLM
still loses by 22 points. The fix validates H6047's diagnosis (the 54.3% was
context-free) but does not close the gap; the paper's LLM-vs-MFS comparison
should quote **62.3%**, not 54.3%.

## 2. Hybrid routing — pre-registered, train-side justified

Rule (locked before test scoring): route an item to the LLM iff the train-fold
corpus-share gap of its top-2 senses is < 0.20 **or** the lemma has < 10
train-fold tokens; otherwise take MFS. The train-fold leave-one-out profile
(`tune_loo_profile.json`, 291,755 train tokens) justifies the stratum: LOO-MFS
accuracy collapses to **40.3%** at gap<0.20 vs **87.2%** at gap≥0.20. On the
B3 sample the rule routes **39/300 items (13%)**.

## 3. Try ledger — no configuration beat MFS

| try | tail arm (routed items only) | hybrid | b (hyb✓MFS✗) | c (hyb✗MFS✓) | McNemar p |
|---|---|---|---|---|---|
| 1 | deepseek-chat, full candidate list | 81.7% | 9 | 17 | 0.169 |
| 2 | deepseek-chat, top-2 restricted | 82.3% | 8 | 14 | 0.286 |
| 3 | **claude-sonnet-5, top-2 restricted** | **83.0%** | 9 | 13 | 0.523 |
| 4 | sonnet-5, top-2 + rank1-as-DEFAULT instruction | 82.7% | 7 | 12 | 0.359 |

Committed final = try 3 (best). A 24-cell post-hoc sensitivity sweep over
(delta_gap, min_train) with the deepseek arm contains **no winning cell**
(best 83.3% at 0.10/10, c>b everywhere) — reported in `scores.json` as
analysis, not selection.

## 4. Why it loses — dissection

- **The tail is MFS's home turf after all.** Although train-fold LOO-MFS
  collapses at gap<0.20 (40.3%), on the frozen-lemma B3 sample MFS holds
  **56%** on the routed stratum (22/39) — the defgen lemma filter makes test
  MFS far stronger than the train average. The LLM arms manage only ~36-41%
  there.
- **Gold structure of the tail:** rank-1 23, rank-2 10, rank-3+ 6. Top-2
  restriction makes the 6 rank-3+ items unwinnable, capping b at ~10-11.
  Significance (p<0.05) required b≈10 with c≤2 — i.e. near-perfect override
  precision.
- **Sonnet's override precision is the binding constraint.** On the tail,
  sonnet-5 (try 3) picks rank-2 on 27/39 items: it converts **9/10 true
  gold-rank-2 items** (excellent recall) but commits **18 false rank-2
  overrides**, 13 of which break items MFS had right. The rank-1-as-DEFAULT
  instruction (try 4) did not suppress them (c only 13→12, and b fell 9→7).
  This is the taxonomy's `prior_bias`/prototypical-gloss failure mode
  persisting in context, now measured against a strong MFS rather than
  alongside a broken context.
- **Gloss deficit carries forward:** 44.5% of H5877 misses had glosses
  truncated at the 100-char storage cap (taxonomy soft tag); the hybrid tail
  inherits those same truncated glosses (candidates are byte-identical for
  comparability). Sense discrimination between close top-2 senses is exactly
  where truncated glosses hurt most.

## 5. What would move it (successor inputs)

1. **Full-length glosses** on the tail (repair the 100-char storage cap from
   the live MW layer) — attacks the dominant evidence deficit; requires
   widening the item definition beyond the frozen candidates.
2. **A larger B3 sample**: at n=300 the discordant mass caps at ~26 items;
   even a perfect top-2 discriminator barely clears the significance bar
   (b=10, c=0 → p≈0.002).
3. **Override-precision training/calibration** (the decision the prompt could
   not make: when *not* to leave rank-1) rather than better raw WSD.

## 6. Boundary with H5556 (DSPy lane)

H5556 optimizes *prompts* (instructions + few-shot demos) via DSPy over the
A3 definition-generation gold. This lane changes the *decision architecture*
(MFS floor + routed LLM tail) over the frozen B3 WSD fold with fixed prompts;
no DSPy runtime, no A3 gold, no definition generation. No overlap in
harnesses or golds; both feed the ISCLS-9 B3 paper from different sides.

_Гасунс_
