_Created: 24-08-2026 · Last updated: 05-09-2026_

# H3455 lane A — akshara.ru bounded scrape pilot: coverage report

_Created: 24-08-2026 · OxAlpha (`opencode/x-preview-f-free`) · RESTRICTED tier, benchmark-only_

## Crawl facts

| Pass | URLs | OK | Fail | Bytes |
|---|---|---|---|---|
| 1 · `dict=all` (originals) | 304 | 304 | 0 | 47,500,955 |
| 2 · `dict=mw_ru/apte_ru/pwg_ru` (MT) | 912 | 912 | 0 | (see crawl_manifest_ru.jsonl) |

- Sample manifest FROZEN before crawling: [data/akshara_pilot/sample_manifest.jsonl](https://github.com/gasyoun/kosha/blob/main/data/akshara_pilot/sample_manifest.jsonl) — **254 c1-TM roots (complete promoted census, NOT a subsample) + 50 control** (seed 730), 304 rows.
  - Plan said "~300 stratified"; reality: the whole c1 promoted set is 254 distinct roots, so stratum A is a census. 254+50=304.
- Politeness: identified UA with contact, 2.0 s throttle + ≤1 s jitter, exponential backoff, checkpointed JSONL manifests with resume ([crawl_manifest.jsonl](https://github.com/gasyoun/kosha/blob/main/data/akshara_pilot/crawl_manifest.jsonl), [crawl_manifest_ru.jsonl](https://github.com/gasyoun/kosha/blob/main/data/akshara_pilot/crawl_manifest_ru.jsonl)).
- Robots conformance: URL allow-list regex guard inside [`scripts/akshara_pilot_crawl.py`](https://github.com/gasyoun/kosha/blob/main/scripts/akshara_pilot_crawl.py); fenced endpoints (`/kosha/card|words|suggest`, `/showasset`, `/internal-scans/`) never requested. Owner outreach DONE by MG pre-crawl.
- Probe row: Uprava [SERVER_OUTAGES.md](https://github.com/gasyoun/Uprava/blob/main/SERVER_OUTAGES.md) (akshara.ru UP, 200/246 ms, 24-08-2026).

## Yield (parsed corpus, one row per headword)

| Block | Heads | Note |
|---|---|---|
| any original | 299/304 | 5 honest no-entry misses (below) |
| mw / mw_ru | 276 / 276 | MT = 100% of MW presence |
| apte / apte_ru | 162 / 162 | MT = 100% of Apte presence |
| pwg / pwg_ru | 193 / **149** | **MT covers 77.2%** of PWG presence |
| mac | 129 | originals only (no MT exists on site) |
| likh (Likhushina) | 87 | originals only — captured as advisors, rights-restricted, NEVER publishable |
| `have_any_mt` | 288 | benchmark-usable rows |
| pwg ∩ pwg_ru | **149** | the core H-B comparison set (DE original + their MT) |

## Honest misses (not parser defects)

1. **5 zero-article `dict=all` pages** (`SudDavidyA`, `dvAdaSAnta`, `hiDmA`, `kaNguRI`, `durg_a~~h0_zz_sch`) — HTTP 200 «Не найдено» pages: these keys are absent from their kosha. All control-stratum. Caveat: Cologne `pwg.sqlite` DISTINCT keys include non-headword artifacts (`durg_a~~h0_zz_sch`); control sampling inherits that noise by design.
2. **44 PWG originals without pwg_ru MT** (e.g. `Adika`, `ahar`, `anukampa`) — verified against live site: lowercase retry also «Не найдено»; their MT store genuinely lacks them. Recorded as null, never fabricated.

## Capture-fidelity spot checks (acceptance: ≥10)

Byte-level sha256 match between stored raw and a fresh polite re-fetch, plus article-extraction assertions:

- `gam` — hand-read full card during planning (24-08-2026, webfetch): all five dicts + RU blocks confirmed live.
- `Ap` — parser output asserted: 5 originals + 3 MT blocks, Cyrillic tokens present.
- `AmarSa` — selftest fixture: mw/pwg/mac articles extracted.
- `Adika` — negative-path verified live twice (found in pwg, absent in pwg_ru).
- Re-fetch sha256 spot check: **first 10 manifest heads re-fetched politely, 10/10 byte-identical** to stored raws — [data/akshara_pilot/refetch_check.json](https://github.com/gasyoun/kosha/blob/main/data/akshara_pilot/refetch_check.json).

## Rights posture

Raw HTML lives gitignored under `data/raw_akshara_pilot/`; parsed text corpus `data/akshara_pilot/parsed_corpus.jsonl` is gitignored (RESTRICTED). Nothing scraped may reach any public surface without a fresh @DECIDE. Registered in [datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) as `akshara-mt-benchmark-pilot`.

_Dr. Mārcis Gasūns_
