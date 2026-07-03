# Data sources — provenance per feed (Phase 1)

_Created: 02-07-2026 · Last updated: 03-07-2026_

Tracks the source, version, and measured count for every feed loaded into
`data/db/kosha.db` by [`scripts/build_db.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db.py),
per [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md) D1's
requirement to record source paths + versions here — not assumed, measured.

## D1 — lemma spine

| Field | Value |
|---|---|
| Source | [`SanskritLexicography/HeadwordLists/union/union_headwords.tsv`](https://github.com/gasyoun/SanskritLexicography/blob/master/HeadwordLists/union/union_headwords.tsv) (sibling repo, consumed not rebuilt) |
| Loaded rows | **323,425** data rows (file has 323,426 lines incl. header; header row is not data) |
| Deviation from plan | [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md) D1 states "323,426 rows" for the `SELECT COUNT(*)` check — that number is off by one against the measured file (323,425 data rows after the header). The correct check value is **323,425**; PHASE1_PLAN's stated figure appears to be a stray off-by-one (possibly counting the header). Recorded here per the anti-gaming rule (measure, don't assume) rather than silently matching the wrong number. |
| Frequency join | LEFT JOIN [`data/frequency/lemma_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv) onto `lemmas.slp1`. **61,340** lemma rows (18.9 %) overlap the frequency feed by key — consistent with the README's "73.7 % of the 83,277 freq-lemmas match the spine" (61,340 / 83,277 = 73.6 %). Of those, **51,773** carry a `count_all` value (the frequency README's own split: 59,282 of the 83,277 freq rows have `count_all`; the remaining rows are ranked by `periods_sum` only — 9,567 of the overlapping lemmas fall in that periods-only bucket). Both counts reconciled exactly against a standalone key-diff; no discrepancy. |

## D2 — entries (per dict)

Recorded by [`scripts/build_entries.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_entries.py)
into the `sources` table at build time (dict, title, edition,
csl_orig_commit, source_path, pc_format, pc_coverage, entry_count). See that
table (`SELECT * FROM sources`) for the live values; this file is not
duplicated per rebuild — query the DB. Measured 02-07-2026 against
[csl-sqlite release `2026-06-28-08-27-31`](https://github.com/sanskrit-lexicon/csl-sqlite/releases):

| dict | entries | pc_format | pc_coverage |
|---|---|---|---|
| mw | 286,525 | `page,col` | 100.0 % |
| pwg | 123,366 | `vol-page` | 100.0 % |
| ap90 | 34,882 | `page-col` (col is usually a letter a/b/c, 246 records carry a bare digit) | 100.0 % |

**Deviations from plan:** PHASE1_PLAN.md D2 states MW = 286,560 records; the
measured release (`2026-06-28-08-27-31`) has **286,525** — normal upstream
drift between the plan's authoring date and this build (Cologne publishes
weekly csl-sqlite releases). AP90's `<pc>` shape is `page-col`
(e.g. `0001-a`), not the plan's "page-col-letter" — there is no separate
letter component beyond the column value itself; `col` already carries the
letter (or, in 246 records, a bare digit). `csl_orig_commit` is **not**
resolvable from the csl-sqlite release format (only a `key, lnum, data`
sqlite ships) — recorded as the release tag with that limitation noted
inline in `sources.csl_orig_commit`; resolving the exact underlying
csl-orig commit per release is flagged as a D2 follow-on, not blocking.

**Spot-verify (10 records, PHASE1_PLAN.md D2 check):** MW L142512 = `banD` @
`720,1` ✅; MW L523 = `akza` @ `3,2` ✅; plus 8 more across mw/pwg/ap90 at
scattered L-numbers, all pc-parsed correctly by `parse_pc()`.

**Sense segmentation (D2/ARCHITECTURE `senses` table) — DONE 03-07-2026
([`app/segment.py`](https://github.com/gasyoun/kosha/blob/main/app/segment.py)).**
Every body is split at its `<div>` division markers — the same boundaries
`basicdisplay.php` renders as separate visual divisions, and empirically the
one consistent signal across all three dicts: MW `<div n="to"/>`/`<div
n="vp"/>` (meaning + verb-paradigm breaks), PWG `<div n="1|2|3">` (numbered
senses `1〉` / sub-senses `a〉`), AP90 `<div n="1"/>` before bold `1`/`2`/`—`.
Sense 1 spans the head up to the first `<div>`; each subsequent `<div>` opens
a new sense; markerless entries keep the single-sense fallback ("always
mintable"). Spans with no visible text are dropped and survivors renumbered
1..N. Measured live counts: **MW 303,022 · PWG 223,446 · AP90 165,935**
senses (multi-sense entries: 4,695 / 28,680 / 19,828). senseN is a *stable
within-entry division counter* per A2, not necessarily the printed sense
number. Golden-tested via the render golden set (which renders segmented
spans) and the sense round-trip test.

## D3 — forms + scan resolver

| Field | Value |
|---|---|
| Source | [`gasyoun/SanskritRussian`](https://github.com/gasyoun/SanskritRussian) `dcs_form2lemma.tsv` (408,660 pairs) + `vidyut_form2lemma.tsv` (28,567 pairs) — the committed copies of the [`RussianTranslation/glossary/`](https://github.com/gasyoun/SanskritLexicography/tree/master/RussianTranslation/glossary) pipeline output (that dir's own README: data is git-ignored there, lives in this sibling repo) |
| Loaded rows | **426,410** form→lemma pairs (437,228 raw rows minus 10,818 exact-duplicate `(form,lemma,source)` triples, `INSERT OR IGNORE` on the `forms` PK) |
| Check | `bhagavān → bhagavant` ✅ (SLP1 `BagavAn → Bagavant`, DCS source, top-ranked by count against 2 lower-ranked alternates `Bagavat`/`yogin` — the join's documented "attribute to highest-count lemma" rule) |
| Scan resolver | **Deviation from PHASE1_PLAN.md D3 wording** — [`ls_resolver.py`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/ls_resolver.py) (1226 lines) is a port of csl-app's `LsService`, resolving `<ls>` **citation cross-references** embedded in entry prose (RV./MBh./Pāṇini sūtra numbers → *external* corpus viewers) — it has no `serveimg`/`servepdf` logic and cannot answer "what's the scan of this entry's own dictionary page". That's a separate, documented Cologne mechanism ([`COLOGNE/api/servepdf.md`](https://github.com/sanskrit-lexicon/COLOGNE/blob/master/api/servepdf.md)): `https://sanskrit-lexicon.uni-koeln.de/scans/{DICT}Scan/2020/web/webtc/servepdf.php?page={page}`. Implemented directly as [`app/scan_resolver.py`](https://github.com/gasyoun/kosha/blob/main/app/scan_resolver.py) (small, NEW, per PHASE1_PLAN's own allowance for D2/D3 glue). `ls_resolver.py`'s actual citation-link porting is out of scope for D3 (belongs with the `render()` port, D4) — flagged as follow-on, not silently dropped. |
| Check | 10 sampled `scan_url()` outputs across mw/pwg/ap90 (seeded random, `RANDOM() LIMIT 4` per dict) — **10/10 HTTP 200**, live-verified 02-07-2026 |
| Known gap | No documented volume parameter for multi-volume PWG in `servepdf.php` — `page` is passed as PWG's own per-volume `<pc>` page component; cross-volume disambiguation is unresolved server-side. Probed 03-07-2026: `servepdf.php` returns HTTP 200 for `page=1-0037`, `page=37&vol=1`, and `page=37&volume=1` alike (tolerant of unknown query params), so status code alone does **not** reveal whether a volume param is honored — a content diff would be needed. Still open, not blocking (the URL resolves to *a* page). |

## D4 — API v1 + Salt facade + tests

| Field | Value |
|---|---|
| Coverage | Full [ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md) API v1 contract: `/api/v1/{lemma,form,search,sense,meta}` + `/health`, plus the two Salt facade REST faces (`/dicts/{id}/restful/{entries,ids}`). GraphQL face is explicitly P7-scoped, not attempted. |
| `render()` | **Full port DONE 03-07-2026.** [`app/render.py`](https://github.com/gasyoun/kosha/blob/main/app/render.py) is now a **code-level faithful** port of the mw/pwg/ap90 path of [csl-websanlexicon](https://github.com/sanskrit-lexicon/csl-websanlexicon)'s canonical `v02/makotemplates/web/webtc/basicdisplay.php` (the ~1,000-line SAX display engine, reimplemented branch-for-branch with Python expat) + the relevant `basicadjust.php` pre-display passes. Returns basicdisplay's `row` (entry prose HTML); the `row1`/`row1x` metadata line (record ID, printed-page link, Whitney/Westergaard links) is intentionally excluded — kosha surfaces those as structured fields. **Two documented deviations** (in the module docstring): (1) `<s>` transliterated server-side SLP1→IAST via sanskrit-util, not the PHP's client-JS `<SA>` + accent stripped per the display default; (2) DB-backed abbreviation tooltips (`Xab.sqlite`) and external `<ls>` scan-viewer hrefs are NOT resolved (no local DB, RISKS.md R12; the `<ls>` citation-link resolution is the separately-owned ls_resolver.py D3 follow-on). **Golden merge bar met**: 38 frozen, checksummed HTML snapshots (mw 14 incl. banD L142512 + akṣa L523, pwg 12, ap90 12 — ≥10/dict) under [`tests/golden/`](https://github.com/gasyoun/kosha/tree/main/tests/golden), seeded-selected (EVAL_PLAN §0), tested by [`tests/test_render_golden.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_render_golden.py). NB the snapshots lock render() against **regression**; they are the frozen output of THIS port, not diffed against the live PHP web stack (which needs dal DBs + servers kosha never calls). |
| `cite` / version resolution | **R1 Commitments 1–2 DONE 03-07-2026.** `cite` now carries `resolution_url` (browser-resolvable, pins `@version`), durable `release_asset` permalink, BibTeX + CSL-JSON ([`app/cite.py`](https://github.com/gasyoun/kosha/blob/main/app/cite.py)). `/api/v1/sense/{id}@version` (or `?v=`) resolves an **old** citation against its archived release dump ([`app/versions.py`](https://github.com/gasyoun/kosha/blob/main/app/versions.py) + [`scripts/archive_senses.py`](https://github.com/gasyoun/kosha/blob/main/scripts/archive_senses.py)) — the path T-UC10 forces; unarchived versions 404 with the release-asset pointer. Rebuilds emit `sense_crosswalk.tsv` (old→new senseN via span-text similarity; SPLIT/MERGED/GONE/MOVED; zero-cost when unchanged — [`scripts/build_crosswalk.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_crosswalk.py)). Commitments 3–4 (Zenodo, DOI) remain P7-scoped. |
| **Salt id-minting** | Implemented directly from `csl-apidev/api1/salt_common.php`'s real logic (read via research pass, no live csl-apidev instance exists to hit — dev-only source, confirmed in that repo's own `doc/salt_api_handoff.md`): `homCount>1` → `-{hui}` from the entry's own `<info hui="N"/>` attribute if present, else `-L{lnum}`; `homCount==1` → bare id. **Correction made during implementation:** an early draft matched any `<hom>N</hom>` *text* tag anywhere in the body, which false-positived on decimal-lnum sub-entries quoting another headword's homonym number in running prose (MW `ka` L41336.1/.3) — collisions on `lemma-ka-1`/`lemma-ka-2`. Fixed to match only the entry's own `<info hui="N"/>` attribute; re-verified distinct across all 31 real `ka` records. |
| **Check (PHASE1_PLAN.md D4):** Salt-face parity vs csl-apidev for agni/indra/ka | Measured against real MW data (no live csl-apidev/C-SALT endpoint reachable — parity is against the documented ground truth in `doc/salt_api_handoff.md` + the PHP id-minting logic, not a live diff): **agni = 10 records** (all `-L{lnum}`, no `hui`); **indra = 17 records** (matches the doc's stated count exactly); **ka = 31 records**, ids include the doc-cited `lemma-ka-1..4` (the 4 `hui`-marked primary homonyms) and `lemma-ka-L41336.05` (doc-cited decimal-lnum fallback example) — **exact match** on every doc-cited id. `lemma-agni-L890`'s `csl` block (`page="5"`, `column="1"`, `accentedKey="agni/"`, `references=["Uṇ."]`) matches the doc's worked example field-for-field. **Known open divergence (not introduced by this build, already documented upstream):** `csl-standards/docs/SALT_API_PROFILE.md` records a live C-SALT service returning only 4 ids for `ka` (`lemma-ka-1..4`, no `-L` fallback) — a different id *set* than this CSL-side 31-record implementation. That divergence predates this session and is C-SALT's own open item, not a kosha bug. |
| pytest | **107/107 green** locally (03-07-2026): [`tests/test_api.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_api.py) (20, all 5 kosha endpoints + both Salt faces + 3 parity checks) + [`tests/test_render_golden.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_render_golden.py) (77: coverage + 38 checksum + 38 render reproduction) + [`tests/test_citability.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_citability.py) (10: cite shape, T-UC10 archive resolution, crosswalk SPLIT/MERGED/GONE/MOVED). |
| `data_version` | Set to `0.1.0-dev` (`meta` table) — this is a **local dev build, not a citable release** (A3: local-first; RISKS.md R1c: Zenodo mirroring starts at the *first citable release*, which this isn't). Sense `cite` payloads correctly pin to this value today; a real `data_version` bump is a P2/D5-gated decision, not made here. |

---

_Dr. Mārcis Gasūns_
