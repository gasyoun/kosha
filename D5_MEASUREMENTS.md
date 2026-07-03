# D5 — measurements, then the decisions they inform

_Created: 03-07-2026 · Last updated: 03-07-2026_

Phase 1 D5 ([PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md)):
**measure the real system, then settle the SLO items
[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)
parked for D5.** Every number here is reproducible from the committed harness
[`scripts/measure_d5.py`](https://github.com/gasyoun/kosha/blob/main/scripts/measure_d5.py)
against the local `data/db/kosha.db` — all local, no live third-party calls
([RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md) R12). The
decisions those numbers drive are recorded in
[KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md).

Measured by Opus 4.8 (`claude-opus-4-8`), 03-07-2026, on the Windows dev box
(Python 3.14.4, SQLite via stdlib `sqlite3`). **Honesty caveats up front,**
per [EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md)
anti-gaming rules:

- This is a **shared desktop, not an isolated benchmark host**: run-to-run
  variance from CPU-frequency scaling and background processes is real
  (one render micro-bench read 3× high under transient load and was
  re-measured clean). Numbers are reported as median + p95 over N iterations
  and cross-checked against the end-to-end HTTP figures; where a figure is
  noisy it is called out, not smoothed.
- "warm" = OS file-cache hot, the steady state a running server sees. "cold"
  = first call on a freshly-opened read-only connection — which is the **real
  per-request start state**, because the app opens a new SQLite connection per
  request ([`app/db.py`](https://github.com/gasyoun/kosha/blob/main/app/db.py)
  `get_db`); only the OS file cache carries across requests. True cold-*disk*
  (OS cache dropped) is not simulated (no portable Windows drop-caches) and is
  labelled where relevant.
- **A latency bug was found and fixed mid-D5** (see §3). D5 is "measure *then*
  decide"; an SLO set on top of a 240 ms table-scan bug would have been
  meaningless, so the fix landed first and the SLO is set against the corrected
  baseline. Both before/after numbers are shown.

---

## 1. Database size on disk (RISKS.md R11)

| Metric | Value |
|---|---|
| `kosha.db` file | **289,820,672 B = 276.4 MiB** (289.8 MB decimal) |
| SQLite pages | 70,757 × 4,096 B |
| Rows | entries 444,773 · forms 426,410 · lemmas 323,425 · senses 692,403 · sources 3 |
| vs GitHub **100 MB per-file** limit | **2.9× over** → ships as a **release asset**, never in-repo (R11 confirmed) |
| vs **2 GB release-asset** ceiling | 14.5% — ample headroom for growth |

The 276.4 MiB reflects the D5 index change (§3: +3.4 MiB for the covering
index + ANALYZE stats vs the pre-D5 273.0 MiB). `dbstat` is not compiled into
this SQLite build, so a per-object page breakdown was unavailable; the logical
driver is `entries.body` (verbatim csl-orig markup, A1) at 444,773 records.

**Decision input:** R11's "data via release assets only" is not optional — the
file is unconditionally over the in-repo limit. The static Pages tier (§5) is
sized separately below.

## 2. Row / coverage facts

`data_version` = `0.1.0-dev` (no citable release yet — first bump is P2, A2).
Per-dict entries: mw 286,525 · pwg 123,366 · ap90 34,882; `<pc>` coverage 100%
all three ([`data/SOURCES.md`](https://github.com/gasyoun/kosha/blob/main/data/SOURCES.md)).

## 3. Latency — a table-scan bug, found and fixed

The parked SLO cannot be set without knowing where the time goes. Profiling
`/api/v1/lemma` showed **SQLite `execute` dominating (3.27 s of 4.30 s across
760 calls)**, not rendering. `EXPLAIN QUERY PLAN` on the entry lookup:

```
SELECT * FROM entries WHERE dict=? AND slp1_key=? ORDER BY L
  -> SEARCH entries USING INDEX sqlite_autoindex_entries_1 (dict=?)
```

The planner seeked only on `dict=?` (via the `UNIQUE(dict, L)` autoindex, which
also served the `ORDER BY L` for free) and then **scanned all ~286k MW rows**
filtering `slp1_key` in memory — **~240 ms per lemma lookup**. The existing
`entries_key(slp1_key)` index was *not* chosen: adding `ORDER BY L` made the
planner prefer the ordered autoindex-scan, and without `ANALYZE` it had no
selectivity stats to know `slp1_key` is highly selective.

**Fix:** a covering index `entries(dict, slp1_key, L)` — it satisfies the
equality seek *and* the ordering, so no scan and no sort. Chosen immediately,
even without `ANALYZE`. Landed in
[`scripts/build_db.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db.py)
(replacing `entries_key`; `ANALYZE` added at end of build). Verified 107/107
tests still green (results identical, only speed changed).

### Effect (handler = real endpoint functions; e2e = live uvicorn + httpx, warm)

| Request | before (handler) | **after (handler)** | after (e2e HTTP) |
|---|---:|---:|---:|
| lemma `kamala` (mw, 18 entries) | 172 ms | **10.9 ms** | 22 ms |
| lemma `ka` (mw, 31 homonyms — the fat group) | 169 ms | **19.6 ms** | 31 ms |
| lemma `agni` (pwg, 4) | 112 ms | **7.2 ms** | — |
| lemma `deva` (ap90, 1) | 38 ms | **14.2 ms** | — |
| lemma `sTA` (pwg, 190 KB mega-body) | 188 ms (e2e) | — | **64 ms** |
| search `ka` prefix (12,495 hits) | — | **61.8 ms** | 51 ms |
| search `agni` exact | — | **0.24 ms** | — |
| form `bhagavAn` | — | **0.16 ms** | 3.9 ms |
| sense `mw.142512.1` (banD) | — | **0.84 ms** | 4.5 ms |
| meta | — | — | 57 ms |

**~8–16× on the common path; the 240 ms scan is gone.** Cold (new-connection)
tracks warm within ~1.5× — expected, since every request already opens a fresh
connection, so there is no cross-request SQLite cache to lose.

**What remains the slow path, honestly:**
- **`search` prefix/fuzzy ≈ 50–70 ms** (p95 ~96 ms). `slp1 LIKE 'ka%'` scans
  the 323k-row `lemmas` covering index because `LIKE` (case-insensitive by
  default) cannot use a range seek. Flagged, not fixed here (scope: D5 is
  measure+decide, and one justified perf fix already landed). The fix — rewrite
  prefix search to a case-sensitive range `slp1 >= 'ka' AND slp1 < 'kb'` — is
  an easy P2/P5 win when autocomplete UX wants <20 ms, and it also removes a
  latent SLP1 correctness wrinkle (SLP1 is case-significant: `K`≠`k`, so
  case-insensitive `LIKE` over-matches). Recorded for the search-UI phase.
- **Mega-card lemma render** (a headword whose PWG entry is one of the 9 bodies
  >100k chars): ~50–64 ms e2e. Rare (§4) but real; the tail the SLO must cover.

## 4. render() cost + body-size distribution

Clean isolated render (25 iters, quiet machine) of the densest cards:

| Dict | densest card | body chars | render median | p95 |
|---|---|---:|---:|---:|
| pwg | `sTA` L113928 | 190,797 | **50.1 ms** | 60.8 ms |
| pwg | `vart` L88503 | 170,864 | 53.7 ms | 93.4 ms |
| mw | `kf` L54148 | 16,225 | 5.5 ms | 9.6 ms |
| ap90 | `su` L30353 | 54,179 | 25.6 ms | 54.4 ms |

Render cost scales ~linearly with body size (≈0.25–0.35 ms per 1k chars).
**But fat cards are vanishingly rare:**

| body chars | # entries | cumulative % |
|---|---:|---:|
| 0–1,000 | 432,632 | **97.27%** |
| 1,000–5,000 | 10,831 | 99.71% |
| 5,000–20,000 | 1,176 | 99.97% |
| 20,000–50,000 | 97 | 99.992% |
| 50,000–100,000 | 28 | 99.998% |
| >100,000 | **9** (all PWG) | 100% |

Per-dict body p99: mw 544 · pwg 4,607 · ap90 3,628 chars. So **at p99 an entry
renders in <2 ms**; the heavy tail is p99.9+ and it is PWG's longest verbal
roots (`sTA`, `vart`, `DA`, …). A typical multi-dict lemma card renders in
single-digit ms; only a lemma that resolves to one of the ~37 bodies >50k chars
reaches the tens of ms.

## 5. Static-cache size projection (R11, Phase-2 Pages tier)

Per-lemma static card (merged cross-dict view: rendered HTML + headword +
scan URL + sense IDs), sampled over 400 real lemmas:

- avg payload **3.07 KB**, median 1.0 KB, p95 10.7 KB, avg 3.85 entries/lemma
- 222,179 lemmas have ≥1 dict entry (of 323,425 union headwords).

| N lemmas | as ONE bundled JSON | vs 100 MB/file | sharded (per-lemma) |
|---|---:|---:|---:|
| 10,000 | 30.7 MB | ok | 10k files × ~3 KB |
| 50,000 | 153.5 MB | **OVER** | 50k files |
| 100,000 | 306.9 MB | OVER | — |
| all 222,179 | 681.9 MB | OVER | 682 MB total |

**A single bundled `lemmas.json` crosses the 100 MB per-file limit at ~33k
lemmas** — so full rendered cards must be **sharded** (one file per lemma), never
one blob. Sharded, the per-file limit is a non-issue (each ~3 KB) and total
size is the only budget.

**Frequency makes the cutoff principled, not arbitrary.** 50,355 lemmas have
*both* a dict entry *and* a corpus attestation (`count_all`), and the
distribution is Zipfian:

| top-N attested-with-entry | corpus token-mass coverage | sharded size |
|---|---:|---:|
| 1,000 | 68.2% | 3 MB |
| 5,000 | 89.9% | 15 MB |
| 10,000 | 95.4% | 31 MB |
| 50,355 (all attested-with-entry) | 100% | 155 MB |

→ see the cache-N decision in
[KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md).

## 6. R3 fallback exercised (RISKS.md R3 — tested, not a comment)

[`scripts/fallback_csl_orig.py`](https://github.com/gasyoun/kosha/blob/main/scripts/fallback_csl_orig.py)
parses **csl-orig `ap90.txt` directly** (the documented fallback for when a dict
is absent from csl-sqlite or a release lags a needed correction) and compares
the recovered inventory against the csl-sqlite-built DB:

```
parsed 34,882 csl-orig records
L-numbers in both: 34,882   only-in-fallback: 0   only-in-db: 0
<k1> SLP1 key matches DB slp1_key: 34,882/34,882 (100.00%)
<pc> token matches DB pc_raw:      34,882/34,882 (100.00%)
VERDICT: fallback recovers the entry inventory YES (>=99% L + key parity)
```

**Honest boundary:** the fallback recovers the **entry inventory** (every `<L>`
record, its `<k1>` SLP1 key, its `<pc>` page/column) byte-for-byte, but the
csl-orig `.txt` body is the *upstream* display-markup stage (`{#slp1#}`, `¦`,
bare `<ls>`), whereas csl-sqlite ships the *downstream* `make_xml`-converted
record (`<H1><h>…`, `<s>…</s>`, `<div>`). A render()-able fallback therefore
also needs the csl-orig→XML `make_xml` step (owned by csl-pywork). So R3's
fallback is proven at the inventory level; the markup-conversion dependency is
named rather than glossed.

## 7. Provenance resolved — `sources.csl_orig_commit` (was flagged open)

The csl-sqlite release format (`key,lnum,data`) does not embed the csl-orig
commit. Resolved in D5 by **cross-dating** against the local csl-orig checkout
(offline `git log`, R12-safe): the latest commit touching each dict's source at
or before the release timestamp `2026-06-28-08-27-31`:

| dict | csl-orig commit (≤ release) | commit date |
|---|---|---|
| mw | `392ed6b` | 2026-06-27 |
| pwg | `8822922` | 2026-06-27 |
| ap90 | `51232f2` | 2026-06-24 |

This is an **upper bound** (commit ≤ release cut time), not a build-exact
mapping — labelled as such in the stored value. Wired into
[`scripts/build_entries.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_entries.py)
(`cross_date_csl_orig_commit`, graceful fallback when no csl-orig checkout) and
applied to the live DB, so `/api/v1/meta` now surfaces real provenance. This
also feeds R3's "data as of {date}" UI footer.

## 8. Still open (not resolved in D5)

- **PWG multi-volume `servepdf.php` disambiguation.** Determining whether a
  `vol=`/`volume=` parameter is honored needs a **live content diff** against
  Cologne (the endpoint returns 200 for unknown params regardless, measured
  03-07). That is a live third-party fetch and a judgment call about which page
  should differ by volume — not cheap, and not blocking (the URL still resolves
  to a servepdf page). Left flagged in
  [`.ai_state.md`](https://github.com/gasyoun/kosha/blob/main/.ai_state.md);
  belongs to the scan-link hardening (G-SCAN, R2), not D5.

---

_Dr. Mārcis Gasūns_
