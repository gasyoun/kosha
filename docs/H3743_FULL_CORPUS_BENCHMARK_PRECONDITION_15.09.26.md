_Created: 15-09-2026 · Last updated: 15-09-2026_

# H3743 — full-corpus pwg_ru-vs-MT benchmark: precondition check, NOT YET DRAINED

Sonnet 5 (`claude-sonnet-5`) executing
[H3743](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3743-Sonnet_kosha_akshara-full-corpus-mt-benchmark_30.08.26.md).
This handoff is `{launch-box: any}` and self-checks its own gate (step 1 of the
mission) rather than needing a human to hold it back — this run's job was to
run that check. Result: the gate is **not** satisfied, so per the handoff's
own design the two measurement halves (auto metrics over the full
intersection, preregistered 400-head judged sample) do not run this pass.

## Precondition gate

New script:
[scripts/akshara_benchmark_precondition.py](https://github.com/gasyoun/kosha/blob/main/scripts/akshara_benchmark_precondition.py)
checks, against the frozen 51,663-head census
([data/akshara_full/census.json](https://github.com/gasyoun/kosha/blob/main/data/akshara_full/census.json)):

1. pass 1 (originals) and pass 2 (`mw_ru`/`apte_ru`/`pwg_ru`) crawl manifests
   report `http==200` for every census head;
2. the case-twin repair pass covers every twin key in
   `data/akshara_full/parity/casefold_twins.tsv`;
3. the **parsed** corpus (`data/akshara_full/parsed_corpus.jsonl` +
   `parsed_corpus_ru.jsonl`, gitignored/RESTRICTED — the actual benchmark
   input) has a row per census head.

Live run (this pass, worktree `kosha-h3743-drain`, based off `origin/main`):

```
NOT YET DRAINED
census target: 51663 heads (frozen 2026-08-27T17:55:49+00:00)
  - pass 1 PARSED corpus incomplete: 0/51663 rows in data\akshara_full\parsed_corpus.jsonl (file absent)
  - pass 2 PARSED corpus incomplete: 0/154989 rows in data\akshara_full\parsed_corpus_ru.jsonl (file absent)
```

Checks 1 and 2 pass — the crawl **manifests** (metadata, committed to
`main`) already report `http==200` for all 51,663 heads across pass 1
(`crawl_manifest.jsonl`, 51,669 rows) and pass 2
(`crawl_manifest_ru.jsonl`, 154,996 rows: 51,663 each of `mw_ru`/`apte_ru`/
`pwg_ru`, only 7 total failures), and the repair pass
(`crawl_manifest_repair.jsonl`, 9,375 rows) covers the twin keys. Check 3
fails outright: **no parsed corpus exists anywhere** — `scripts/akshara_full_parse.py`
was never run to completion against locally-present raw HTML.

## Why: the raw HTML backing the manifests is gone or incomplete

- `data/raw_akshara_full/` (gitignored raw card HTML) does not exist in this
  worktree, nor in any worktree off `origin/main` — it lived in worktree
  `kosha-h3597-14872`, GC'd before H3743 could parse it
  ([Uprava FINDINGS §660](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md#660)).
- The `.ai_state.md` WIP row (02-09-2026) records a `pwg_ru`-only recrawl
  launched to recover from that loss (MG ruling: recrawl `pwg_ru` only, not
  all three MT dicts). That recrawl lives in worktree
  `kosha-h3743-807629` (**not** this one — untouched by this run per the
  "never touch the frozen crawl worktree" instruction, extended here to the
  recrawl worktree since `.ai_state.md` also says "do not GC"):
  - `data/raw_akshara_full/` there holds **15,268** `pwg_ru` raw cards —
    matches the crawler's own `ok=15268` log line.
  - The crawl **stalled at 22,400/51,663 attempted** (≈43%) with a rising
    SSL-EOF/connection-reset failure rate (32% of attempts failed by that
    point) and stopped advancing after **2026-09-06T15:18** — 9 days before
    this run (2026-09-15).
  - Its process (PID 2480) is no longer running; its supervising scheduled
    task `kosha-h3743-pwgru-recrawl-watchdog` is now **Disabled**.
  - Even a complete `pwg_ru` recrawl would not be sufficient alone — pass 1
    (originals) and `mw_ru`/`apte_ru` raw HTML would still need to exist
    somewhere to reach parse target 3 above; this run did not check whether
    a copy survived at `D:\ClaudeTools\evidence\` (out of scope for a
    read-only precondition check).

## What this run did NOT do

Per the mission's own design ("print `NOT YET DRAINED` ... and exit 0
without doing anything else"): no scoring, no LLM-judge calls, no changes to
the crawl/recrawl worktrees, no raw or parsed corpus data touched or
committed (rights posture: RESTRICTED inputs stay gitignored — this run
never read any actual card text). Only the manifest **metadata** (already
committed, already public-safe scores/counts) was read.

## Manifest

`data/manifest/datasets.json` `akshara-mt-benchmark-full` row already
documents the crawl-manifest-level counts (51,663 + 154,989 = 206,652 `ok`
fetches) and already lists H3456/H3743 as a consumer; no change needed
there — the row describes fetch counts, not the (still-empty) parsed
corpus, and continues to hold accurately.

## Next actual next step (for whoever restarts the recrawl — human call, not this run's job)

Resume/relaunch the `pwg_ru` recrawl (resumable from
`data/akshara_full/crawl_manifest_pwgru_recrawl.jsonl`, 28,923 rows already
logged) in worktree `kosha-h3743-807629`, re-arm the watchdog scheduled
task, and once genuinely `http==200` for all 51,663 `pwg_ru` heads: run
`scripts/akshara_full_parse.py` (all three passes) to produce the actual
parsed corpus, THEN re-run this handoff's step 1 — it will report `DRAINED`
and the two measurement halves can proceed.

## Verdict

**Gate not met. No benchmark run this pass.** This is the handoff's designed
clean-exit outcome, not a blocker for this execution — the precondition
check itself is now a durable, reusable artifact
([scripts/akshara_benchmark_precondition.py](https://github.com/gasyoun/kosha/blob/main/scripts/akshara_benchmark_precondition.py))
so the next attempt (any launch box, any session) can re-check cheaply
instead of re-deriving crawl state by hand.

_Dr. Mārcis Gasūns_
