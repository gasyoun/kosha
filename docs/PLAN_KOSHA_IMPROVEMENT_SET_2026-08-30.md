# Plan — kosha improvement set, three Claude Code handoffs (30-08-2026)

_Created: 30-08-2026 · Last updated: 30-08-2026_

The design record of a grilling session that settled, in four rounds, **which** kosha work goes to
Claude Code lanes now and **why the rest does not**. Every decision below was voted in chat; this
file is the durable form, and the three handoff bodies carry the executable missions.

## The three handoffs

| Handoff | Tier · effort | What it does | Runnable |
|---|---|---|---|
| [H3743](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3743-Sonnet_kosha_akshara-full-corpus-mt-benchmark_30.08.26.md) | Sonnet 5 · 🟡2 medium | akshara full-corpus blinded pwg_ru-vs-MT benchmark — drain-gated precondition, automatic metrics over the whole intersection, preregistered ~400-head judged sample | after the akshara crawl drains (~1 Sept); declines to run early by itself |
| [H3744](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3744-Opus_kosha_sense-recon-w2-aligned-sense-table_30.08.26.md) | Opus 5 · 🔴3 hard | Sense-reconciliation W2 slice 1 — PWG/MW/Apte aligned-sense table, staged behind `ux=` plus a published compare page | now |
| [H3745](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3745-Sonnet_kosha_a4-w4a-panini-surface-w4b-pages-budget_30.08.26.md) | Sonnet 5 · 🟡2 medium | A4 W4a panini coverage+chain surface + W4b Pages budget re-measure with a 70 % (717 MB) fail gate, plus two doc truth-fixes | now |

All three are `{launch-box: any}` and self-verifying: no human vote inside any run.

## The decisions behind them

1. **Axis.** Improvement means data becoming visible, not a fourth parallel programme. Code
   hardening, citability and DOI work are deliberately out of this set.
2. **Count.** Three, each a successor to work already shipped or in flight — no new fronts.
   kosha had only three open handoffs when this was decided, so the constraint was never a
   shortage of specs.
3. **Lane.** Claude Code takes judgment and repo-editing work: Opus 5 for design-shaped missions,
   Sonnet 5 for mechanical ones. Long-running crawl and ops supervision stays with the OxAlpha
   lane, which already owns the watchdog.
4. **Source of specs.** Adopt-first. Two of the three quote existing roadmap units; only the
   benchmark needed a newly written mission, because no roadmap covered it.
5. **Effort.** Two medium, one hard — the aligned-sense table takes the hard light because it is
   the only unit whose shape is unknown before someone starts.

## The rights fence that shaped half of it

Both akshara manifest rows
([data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json))
are `tier: restricted`, `in_release: not-applicable` — third-party AI machine translation of
Cologne originals, raw and parsed forms gitignored. **The 51,663 harvested heads can never appear
as text on the public `/w/` pages.** The harvest is therefore a measurement asset only: H3743
commits scores, statistics and the blinding map, and nothing else. A head-inventory gap table was
considered as a second, publishable derivative and was **not** taken in this set.

## Why the benchmark is worth re-running at all

The pilot verdict
([docs/PWGRU_VS_AKSHARA_MT_BENCHMARK_24.08.26.md](https://github.com/gasyoun/kosha/blob/main/docs/PWGRU_VS_AKSHARA_MT_BENCHMARK_24.08.26.md))
was **no significant difference** — bootstrap 95 % CI **[−0.12, +0.53]**, crossing zero — on a true
three-way intersection of only **101 heads**, with 40 pairs judged. Its own next-steps say to
re-run only if a publish decision needs it. The full corpus makes the intersection an order of
magnitude larger, so the CI can narrow to a real answer; that, and not repetition, is the reason.
The judging is the cost, which is why the sample is preregistered at ~400 heads with a budget cap
while the automatic metrics run over the entire intersection.

## Sequencing against the crawl

[H3597](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3597-OxAlpha_kosha_akshara-full-scrape_27.08.26.md)
(OxAlpha, 🔴3 hard — akshara.ru FULL kosha crawl) finishes around 1 September, owes a case-twin
repair pass, and freezes its worktree until drain. H3743 does not wait on a human and does not
read prose to know it is early: its first step verifies both crawl passes report DONE and the
parsed row count matches the frozen 51,663-head census, then exits clean with `NOT YET DRAINED`
if not. A partial corpus would produce a benchmark number that has to be thrown away. Folding the
benchmark into the drain was rejected for the opposite reason: the drain is an ops job, and
merging them lets a slow crawl hide a failed measurement.

## Gates that can actually fail

- **W4b Pages budget.** Fail if the projection for the D4 static head of N = 11,148 with A4 pages
  included exceeds **717 MB (70 % of the 1,024 MB cap)**. Today's deployed static tier is
  **402 MB = 39 %** and ships **2,324** static pages. A gate at the cap itself would pass today's
  402 MB and equally pass a build that ships nothing, so the threshold sits well below it.
- **H3744 publication.** Staged behind `ux=`, as every prior word-page surface wave shipped, plus
  a before/after compare page on the vote hub so the publication call is made by looking. A
  cross-dictionary sense alignment asserts that three dictionaries' senses correspond, and that
  can be scholarly wrong in a way page chrome cannot.

## Explicit exclusions

- **Sa→Sa dictionaries** (ŚKDR / Medinī / VCP / Amara) in the aligned-sense table — second slice.
- **Lemma-variant graph** — normalisation infrastructure with no visible output.
- **Wave 2's second acceptance pass** — needs a review sheet and a human vote, which contradicts
  `{launch-box: any}`.
- **pwg_ru RU-sense-structure deliverable** — the plan already assigns it its own handoff.
- **DOI minting** — belongs to a citability pass. H3745 only corrects the roadmap line that still
  calls it a human gate, superseded by standing policy on 16-08-2026.
- **A publishable akshara head-gap table** — considered, not taken.

## Truth-fixes found while scoping (they ride inside H3745)

1. [.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md) Next Steps lists H3549
   and H3565 as "🟡 queued, not started"; both are ✅ and archived on `origin/main` (28-08-2026 and
   27-08-2026).
2. The live portfolio roadmap's W2 DOI line still reads "human gate — MG mints".

_Dr. Mārcis Gasūns_
