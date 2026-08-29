# H3597 — akshara.ru FULL kosha crawl: census + run report

_Created: 27-08-2026 · Last updated: 28-08-2026 · OxAlpha (`z-ai/glm-5.3-flash`) · RESTRICTED tier, benchmark-only_

MG ruling 27-08-2026: **NO volume stop** — census first, then a full run regardless of
volume; volume reported at checkpoint milestones (every 1000 URLs in the crawl manifest
log), never aborting because it got big. This report is written at LAUNCH; the yield
tables fill at drain (residual GTD @DO row, owner OxAlpha).

## 1. Census — FROZEN before the first card fetch

The site's own index is the cheap enumeration path the handoff hoped for:
`sitemap-kosha-001.xml` + `sitemap-kosha-002.xml` enumerate `/kosha/w/<slp1>` — the
site's own declared head inventory.

| Fact | Value |
|---|---|
| **Unique heads (census)** | **51,663** (dedup of 40,000 + 11,663 sitemap locs) |
| Frozen at | 2026-08-27T17:55:49+00:00, before any card fetch |
| Manifest | `data/akshara_full/head_manifest.jsonl` (committed) |
| Census record | `data/akshara_full/census.json` (committed) |
| Source sha256 | `2c87bfa9…f7fddf` (sitemap-001, 5,230,674 B) · `3e1d3089…f85` (sitemap-002, 1,537,588 B) |
| Robot status of the enumeration path | sitemaps + bare `/kosha/w/<head>` (no query string) are robots-allowed for `User-agent: *`; the Disallow pattern `/kosha/w/*?` matches only query-string forms, which are never requested |
| Builder | `scripts/akshara_census.py` (`--check` re-verifies manifest↔census parity) |

Caveat recorded: the sitemap is the SITE's own head set; Cologne-side artifact keys
(the pilot's `durg_a~~h0_zz_sch` class) are not part of it — the full-crawl universe is
what the site itself declares.

## 2. Volume reality (reported, not obeyed as a stop)

51,663 heads × (1 × `dict=all` + 3 × MT variants) = **206,652 URLs**. Single polite
stream measured ~0.29–0.35 URLs/s → ~11–12 days. **MG ruling 28-08-2026: parallel
streams approved** — the crawler now runs **2 polite streams** (each worker keeps its
own 2.0 s throttle + ≤1 s jitter; per-connection behavior unchanged, global rate
doubled to ~0.69 URLs/s measured live) → revised ETA: pass 1 ≈ 13–14 h from the
28-08 switch, pass 2 ≈ +2.9 days; **full crawl done ≈ 1 September** (was 3–4 Sept).
Proceeding per ruling; every 1000 URLs appends a milestone record with ok/fail/rate/ETA
to `data/akshara_full/milestones.jsonl`.

## 3. Contract — unchanged from H3455

- Card pages only: `/kosha?q=<slp1>&dict=(all|mw_ru|apte_ru|pwg_ru)&script=slp1`.
  Robots-fenced endpoints (`/kosha/card|words|suggest|chips`, `/kosha/w/*?`, `/search?`,
  `/showasset`, `/internal-scans/`, `/prakriya`, `/reader/*`) NEVER requested —
  the guard is imported verbatim from [`scripts/akshara_pilot_crawl.py`](https://github.com/gasyoun/kosha/blob/main/scripts/akshara_pilot_crawl.py)
  (`guarded_fetch`; import, not fork) into [`scripts/akshara_full_crawl.py`](https://github.com/gasyoun/kosha/blob/main/scripts/akshara_full_crawl.py).
- Identified UA with contact; robots.txt re-probed 27-08-2026 (fences unchanged from the
  H3455 24-08-2026 reading); owner outreach DONE by MG pre-pilot, no objection posted since.
  28-08-2026 amendment (MG): 2 polite parallel streams — per-connection politeness
  (≥2.0 s + jitter, backoff, retry class) is per-worker and unchanged.
- 2.0 s throttle + ≤1 s jitter, exponential backoff (4/8/16 s, cap 60 s), one retry class.
- Checkpointed append-only JSONL manifests with **resume-from-log** (`done_keys` counts
  only http-200 rows): a crash never restarts from zero — LOAD-BEARING at 206k URLs.
  Progress live log: `data/akshara_full/run_pass1.log` (+ `.err`), gitignored.
- Raw HTML under `data/raw_akshara_full/` — gitignored (RESTRICTED).

## 4. Launch + smoke evidence

- Census `--check` parity: OK (51,663 = manifest rows = unique keys).
- Crawler smoke `--limit 3`: 3/3 OK; parser contract verified on smoke pages
  (`A`→5 originals, `ABARaka`→mw+pwg partial card — honest shape, not a parse defect).
- Launched pass 1 detached 27-08-2026 ~17:58 UTC; crawl manifest grows, 0 fails,
  0 duplicate keys (single-crawler verified — no double-launch).
- 28-08-2026: live switch to the 2-stream build under the watchdog — killed the old
  process, watchdog relaunched from the exact checkpoint (`workers=2` in the run log,
  rate 0.69/s, 0 fail). Two transient local-DNS fetch failures (`getaddrinfo failed`,
  09:22–09:23 UTC — machine-side, not site-side) were re-fetched 200 OK within the
  hour via the crawler's own code path; their ok-records complete the keys in the log.

## 5. NEW site-level finding: cold-fetch mis-resolution (drain gate)

The launch-time 10/10 sha256 re-fetch spot check (acceptance asked ≥10) returned **9/10**:

- `ABA` stored raw ≠ fresh fetch. Diff shows the stored page is the **`ABa`** card
  (`<link rel="canonical" href="…/kosha/w/ABa">`, `data-q-slp1="ABa"`) — the site
  resolved the cold `?q=ABA` to the near-miss `ABa`; minutes later the same URL serves
  the correct `ABA` card (80,135 B vs 39,127 B stored).
- Classification: **site-side cold-cache resolution quirk**, not corruption and not a
  parser defect (H3455's warm-set 10/10 remains valid for its scope).
- **Drain gate (mandatory before parse):** validate every stored card — assert
  `data-q-slp1` == requested manifest key; re-fetch mismatches once (warm cache), then
  classify any residue as honest anomalies. Never parse a wrong-head page silently.

## 5b. INCIDENT 28-08-2026: case-twin filename collision + repair plan

The site **distinguishes SLP1 case** (verified live: `dvipAd` vs `dvipad` serve
different cards — different sha256/sizes; `BA`/`Ba`/`ba` — three distinct cards), and
the census contains **case twins**: 51,663 keys = 46,488 casefold-distinct, i.e.
**5,175 keys are case-variants of another key**. Windows NTFS is case-insensitive, so
the crawler's original flat `<safe>.html` names made each twin pair share one physical
file — the second fetch silently overwrote the first. The 28-08 parse+delete run then
consolidated it: one (possibly mislabeled) row per pair, no row for the twin
(3,810 keys affected at incident time; ~7,1k twin keys total once pass 1 ends).

Two distinct site behaviors must not be conflated (both preserved as data, both
classified at drain):

- **Case-normalization fallback**: when the exact key has no entry, the site serves
  the casefold-twin's card and says so (`data-q-slp1="a"` for `?q=A`; sample 300: 27/27
  mismatches were exactly this class) — a legitimate answer, recorded via `q_slp1`.
- **True distinct cards**: twin keys that both exist serve different content — the
  collision class above.

**Fix (landed 28-08):**
1. Crawler filenames now carry a case-sensitive hash: `<safe>__<sha1-8>.html`
   (`raw_filename()`) — collision-proof; `--manifest`/`--log` overrides added for
   repair passes. Live crawler restarted on the fix.
2. [`scripts/akshara_repair_twins.py`](https://github.com/gasyoun/kosha/blob/main/scripts/akshara_repair_twins.py)
   — builds the repair manifest (`--build`), reports progress (`--status`), purges
   tainted rows (`--purge`).
3. Repair sequence (part of drain, after pass 1 prints DONE — see GTD @DO row):
   `--build` → crawler over the repair manifest (~7,1k URLs, ~3 h) → `--purge` →
   parse the repair log with `--delete-raw`.    Non-twin parsed rows are trustworthy:
   their files were never overwritten.

## 6. Known site-level gaps (expected at scale, encoded as nulls — never fabricated)

- pwg_ru MT inherently missing on ~22.8% of PWG heads (H3455, verified live) — the full
  census version of this number lands in the drain report.
- Zero-article `«Не найдено»` 200-pages exist (pilot: 5/304) — the full crawl will hit
  more; classified as honest misses at parse, not failures.

## 7. Rights posture — RESTRICTED, unchanged

Raw HTML + parsed corpus gitignored, benchmark-only; NOTHING public without a fresh
@DECIDE. `likh` (Likhushina) captured as advisors, NEVER publishable. Registered in
`data/manifest/datasets.json` as `akshara-mt-benchmark-full` (sibling of the H3455
pilot entry).

## 8. Supervision + resume (self-healing since 28-08-2026)

The crawl is supervised by the scheduled task **`kosha-akshara-crawl-watchdog`**
([`scripts/akshara_crawl_watchdog.ps1`](https://github.com/gasyoun/kosha/blob/main/scripts/akshara_crawl_watchdog.ps1),
every 10 min, StartWhenAvailable + WakeToRun, IgnoreNew, 10-min exec limit, log:
`data/akshara_full/watchdog.log`). Contract: healthy → no-op; wedged (alive, no
manifest write >10 min) → taskkill + relaunch; dead → relaunch the incomplete pass;
both passes exhausted (done+failed == total) → log + **self-disable** (no orphaned
task). The crawler itself (since the 28-08 patch) holds Windows
`SetThreadExecutionState(ES_CONTINUOUS|ES_SYSTEM_REQUIRED)` while alive — the
machine stays awake while crawling — and validates every stored card inline
(`data-q-slp1` parity; warm re-fetch once on mis-resolution, `resolved_fix` /
`misresolved` fields in the crawl log).

- End-to-end proof (28-08, §223 rule — a guard that never ran is not a guard):
  healthy no-op kept 1 process; controlled `taskkill` → watchdog restarted pass 1
  from the exact checkpoint (13,495/51,663 done, resume gap `brahmakalA → brahmatIrTa`,
  0 fail) under the patched code.
- Manual path (if the task is gone): the crawler is fully resume-safe —
  1. `python scripts/akshara_full_crawl.py` — resumes pass 1 from the log.
  2. When pass 1 prints `DONE`, run `python scripts/akshara_full_crawl.py --ru` for pass 2.
  3. At drain: §5 gate → full parse (extend `akshara_pilot_parse.py`, don't fork) →
     per-dict coverage table → final §9 acceptance tick + Uprava GTD close.

## 9. Acceptance (locked at launch; drain ticks the boxes)

- **Done looks like:** census frozen (done) + both passes `DONE` at 206,652/206,652 urls
  with 0 unexplained fails + §5 gate green + parsed one-row-per-headword corpus +
  per-dict coverage table in this file + ≥10 byte-level re-fetch checks (incl. the §5
  anomaly class resolved) + registries (datasets.json, SERVER_OUTAGES, CHANGELOG) landed.
- **Prove with:** `python scripts/akshara_census.py --check`; `milestones.jsonl` final
  record; `wc -l crawl_manifest*.jsonl` = 206,652; parse report json; `refetch_check.json`.
- **On our data:** H3455 pilot (304 heads, 1216 fetches, 10/10 refetch) as the golden
  contract baseline; launch-time 9/10 + §5 diagnosis as the honest delta.
- **Fail =:** any unexplained crawl manifest fail >0.1%, a guard exception, a wrong-head
  page parsed silently, or a resume that restarts from zero. Watchdog addendum: an
  interruption NOT healed within ~10 min (task disabled/removed early, or the worktree
  path gone) is also a fail — do not unregister the task before drain.
