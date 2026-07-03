# kosha — D5 decisions record

_Created: 03-07-2026 · Last updated: 03-07-2026_

The three items
[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)
"Explicitly still open" parks for **D5, with measurements** — latency SLO,
rebuild/update cadence, static-cache N. These are engineering decisions the
judgment tier settles from data (not MG-gated @DECIDE items); the data is in
[D5_MEASUREMENTS.md](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md).
Decided by Opus 4.8 (`claude-opus-4-8`), 03-07-2026.

> **Location note (MG can reverse):** the plan
> ([PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md) D5,
> ARCHITECTURE.md) referenced this file at the *SanskritLexicography* path, but
> it never existed there and that repo's kosha planning corpus is the
> banner-flagged/deprecated one
> ([v0.0.34](https://github.com/gasyoun/SanskritLexicography/releases/tag/v0.0.34)).
> kosha is now the canonical home and the only repo this D5 branch can PR off
> `main`, so the record lives here and the two doc links were repointed. Reverse
> if you want it back in SanskritLexicography.

---

## D5-1 — Latency SLO

**Decision.** Server-side read-endpoint SLO, single instance, local SQLite,
warm (steady-state OS cache):

| percentile | target (server-side, excludes client↔server network RTT) |
|---|---|
| p50 | **< 20 ms** |
| p95 | **< 100 ms** |
| p99 | **< 250 ms** |

Applies to `/api/v1/{lemma, form, search, sense}`. `/health` is exempt (probe).
The **static Pages tier** (D5-3) has its own target: **< 50 ms** (flat-file
serve) for cached lemmas.

**Basis (post-index-fix, §3 of the report).** Measured warm handler latency:
form/sense < 1 ms; typical lemma 7–20 ms; the fat `ka` homonym group 19.6 ms;
worst realistic cases — prefix/fuzzy search (~62–70 ms, p95 ~96 ms) and a lemma
resolving to a >100k-char PWG mega-card (~50–64 ms e2e). End-to-end over real
HTTP adds ~10–40 ms of ASGI+JSON framing. So p95 < 100 ms holds today **with
headroom on every endpoint**, and the SLO is honest rather than aspirational.
The number is stated server-side deliberately (R5: client-observed latency adds
network RTT that kosha does not control).

**Guardrails wired to the SLO.** (a) The covering index
`entries(dict, slp1_key, L)` is now part of the schema — the SLO assumes it;
a rebuild that drops it regresses lemma latency ~10×. (b) The **G-LAT gate**
([EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md)) should
assert these percentiles via `scripts/measure_d5.py` at each release, so a
regression fails CI rather than a user. (c) Known headroom-eater flagged for
P2/P5: prefix search rewrite to a range seek (report §3).

## D5-2 — Rebuild / update cadence

**Decision.** **Change-triggered, not clock-triggered.** Check the upstream
data version **weekly**; rebuild + publish a new `data_version` **only when the
source data actually changed** (a new csl-sqlite release tag, or a csl-orig
correction we shipped that a new csl-sqlite release now carries). In practice
this is ~monthly, gated by csl-sqlite's own release rhythm and our monthly
csl-orig batch-PR cadence.

**Rationale — why not nightly** (RISKS.md R3 leaned "nightly-to-weekly").
Every published rebuild bumps `meta.data_version` and, per A2 / R1, must ship as
a **citable release** with the archived sense dumps + `sense_crosswalk.tsv`.
Rebuilding on a nightly clock would mint hundreds of citable versions a year
whose data is byte-identical to the last — citation churn and release-asset
bloat for zero content change, in direct tension with R1's citability contract.
Tying the rebuild to an actual source-version change bounds staleness to ≤1
week of *detection* while keeping one citable version per real data change. A
full rebuild is minutes (not a constraint), so the cadence is chosen for
citation hygiene, not build cost.

**Surface staleness (R3).** `/api/v1/meta` and the UI footer show
`data as of {csl-orig commit date}` from the now-resolved
`sources.csl_orig_commit` (report §7). Staleness a user can see is a property;
staleness they can't is a defect. **Never** hot-patch `kosha.db` to catch up —
corrections flow through csl-orig only
([RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) §5);
the R3 direct-csl-orig fallback (report §6, now a tested path) is the escape
hatch if csl-sqlite's rhythm ever lags a needed correction.

## D5-3 — Static-cache N (Phase-2 Pages tier)

**Decision.** Precompute static per-lemma cards for the **~50,355 lemmas that
have both a dictionary entry and a corpus attestation** (`count_all IS NOT
NULL` ∧ ≥1 entry), **sharded one JSON file per lemma** (never one bundle),
generated in frequency-rank order. Everything else (the ~172k rare/unattested
entry-bearing headwords) is served by the now-fast dynamic API. A single
~16 MB all-headword index (323k × `slp1`+`iast`+`dicts`) ships alongside for
search-as-you-type autocomplete.

**Basis (report §5).** avg card 3.07 KB → sharded total **~155 MB** for the
full attested set — comfortably under the GitHub Pages ~1 GB site soft limit,
and the 100 MB **per-file** cap is a non-issue once sharded (each file ~3 KB).
A single bundled `lemmas.json` was rejected: it crosses 100 MB at ~33k lemmas.
The cutoff is principled, not arbitrary — frequency is Zipfian, so the attested
set covers 100% of corpus token mass, and even a partial generation front-loads
value (top-10k = 95.4% coverage at 31 MB; top-5k = 89.9% at 15 MB). Generating
in rank order means an interrupted or incremental build always has the
highest-value cards first.

**Consequences.** (a) The gitignored `docs/js/data/lemmas.json` path should be
the **headword autocomplete index** (small, one file), *not* full cards —
rename/clarify in the P2 static-generator. (b) Full 222k-lemma card set (682 MB)
is available as a **release-asset tarball** for offline/mirror use (R1c, R4
rebuildability), not committed. (c) The static tier's <50 ms target (D5-1) is
met trivially by flat-file serving.

---

## Status

All three D5-parked items **resolved** and reflected in
[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)
(parked table) and
[PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md)
(D5 check). Phase 1 is complete; P2 (public alpha, MG deploys) can start against
these fixed targets.

_Dr. Mārcis Gasūns_
