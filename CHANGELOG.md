# Changelog

All notable changes to the Gasuns Sanskrit Dictionary (kosha) are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is
[SemVer](https://semver.org/). Keep upcoming work under [Unreleased], then **cut a new
version every time the changelog is updated** (promote [Unreleased] to the next `x.y.z`
with today's date, tag `vx.y.z`, publish a GitHub release — same pass).

Two version tracks, do not conflate: **repo releases** (`vX.Y.Z` tags, this file) cover
code + docs; **data releases** (`data_version` in `kosha.db` meta, shipped as release
assets from P1 on) are versioned separately per
[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md) §A2 —
sense citations pin to `data_version`, not to repo tags.

## [Unreleased]

### Added
- **P5 advanced UI — the word page** (H537, Opus 4.8 `claude-opus-4-8`), built
  from the locked design spec
  [`P5_ADVANCED_UI_DESIGN.md`](https://github.com/gasyoun/kosha/blob/main/P5_ADVANCED_UI_DESIGN.md)
  (MG rulings 10-07-2026: Tabs · all-3 view modes · full P5 scope · both render
  targets). One addressable word page per headword — every dictionary's entry,
  its evidence, its paradigm — reached by the crawlable `/w/{slp1}` permalink.
  - **Crawlable static prerender** — new
    [`app/word_page.py`](https://github.com/gasyoun/kosha/blob/main/app/word_page.py)
    shared template + [`scripts/build_word_pages.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_word_pages.py):
    every dict panel present in the DOM (active shown, rest hidden) with a
    `<noscript>` all-stacked fallback so a JS-less fetcher reads every entry
    (§5); progressive JS hydrates tabs (P5-1), the Gloss/Full/Adaptive view-mode
    toggle (P5-2, persisted to `localStorage`), and disclosures. Runs off the
    committed static card set (no DB); logs actual N + Pages budget + dropped
    tail (no silent caps). Plus a `/browse/<varṇa>` alphabetic spine linking
    every word page. Regenerable Pages output, gitignored like the cards.
  - **FastAPI SSR** — new `GET /w/{slp1}` route renders the long tail through the
    *same* `render_word_page()` template, so static ∥ SSR are byte-comparable
    (P5-4 parity); locked by
    [`tests/test_word_page.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_word_page.py)
    (15 no-DB structural/crawlability tests + a DB-gated SSR byte-parity check).
  - **SPA word page** — new `WordPage.svelte` interactive twin (MW/PWG/AP90 tabs,
    view-mode toggle sharing the same `localStorage` key, evidence + lazy
    paradigm + scan disclosures), reached by `#/w/{slp1}` hash routing; composes
    the existing `getEntry`/`getParadigm`/`ParadigmTable` (reuse ledger §7).
  - **Search operators** (§4) — `root:` and `sandhi:` in the search box (caught
    before transliteration), bare input auto-routes; `sandhi:` prefills the
    reverse analyser.
  - **Study tooling** — CSV (RFC-4180) and Anki (TSV) export of a session's word
    lookups (`lib/export.js`). *Gītā 1 / Nala 1 reading packs are data-gated —
    the DCS sentence-level lemmatised corpus is not present on disk
    (`VisualDCS/dcs_full.sqlite` is a 0-byte LFS placeholder); tracked as a
    follow-up, no verse tokenisation was fabricated.*
  - +34 tests green (19 vitest lib + 15 pytest template); the SPA word-page and
    `sandhi:` operator e2e flows verified in-browser. **Exit checks (MG sign-off
    on live staging · Lighthouse mobile ≥90 · Gītā-verse walkthrough) remain
    gated on MG's P2 `samskrtam.ru` deploy**, per the plan.
- **Type-D concordance record shape + `typed_link_lint.py`** (H539, Sonnet 5
  `claude-sonnet-5`) — extends
  [`scripts/concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py)
  per [`TYPED_LINK_ID_GRAMMAR.md`](https://github.com/gasyoun/Uprava/blob/main/TYPED_LINK_ID_GRAMMAR.md)
  §1 (H499) so every Type-D (grammar ↔ non-grammar) concordance builder imports
  one implementation instead of forking a schema: `RECORD_FIELDS`' `corpus_locus`/
  `corpus_text_id` renamed to `target_locus`/`source_dataset` (positions/semantics
  unchanged); `TYPE_D_RECORD_FIELDS` adds `link_type` + `date`;
  `normalize_record()` maps either shape into one shared view; two new
  `match_method` tiers above `exact` in trust — `id-link` (pure host-stable-id
  join) and `curated` (source concordance's own assertion). New
  [`scripts/typed_link_lint.py`](https://github.com/gasyoun/kosha/blob/main/scripts/typed_link_lint.py)
  validates a Type-D dataset's anchor/target-locus prefixes, tail syntax,
  `link_type`/`match_method`/`date` against the spec, exits non-zero per bad
  row; tested against the spec's §4a/§4b landed worked examples plus negative
  fixtures (URL-host locus, unknown prefix, bad date) in
  `tests/fixtures/typed_link/`. No Type-D dataset registered in the manifest
  (D2b parks that until Q2.1).
- **Pipeline operator runbook** ([docs/PIPELINE_OPERATOR_RUNBOOK.md](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.md),
  H501, Fable 5 `claude-fable-5`) — the single operational spine for the whole
  chain: the seven `build_db.py` stages in dependency order with rerun triggers,
  API serve, the two static-tier deploy classes (committed-goes-live vs
  gitignored-MG-deploys), the data-release citability ritual
  (`archive_senses` → `build_crosswalk` → release asset → manifest refresh),
  maintenance scripts, the verbatim never-touch list, and a failure-symptom
  decoder (the `unable to open database file` wave = DB-less checkout, not a
  regression). Every command/flag cross-checked against script source.
- **B1 dictionary ↔ corpus concordance + the shared concordance core (Q1 of
  [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md)).**
  Executor: Fable 5 (`claude-fable-5`), handoff H380.
  - [`scripts/concordance_core.py`](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py) —
    the Q1–Q4 shared core: canonical record schema, tiered matcher (exact →
    length-preserving `form_key` floor → lossy tiers, unique-bucket only) on the
    canonical `sanskrit-util` keys, host-independent `dcs:<sent_id>` citable loci.
  - [`scripts/build_dict_corpus_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_dict_corpus_concordance.py) →
    [`data/concordance/`](https://github.com/gasyoun/kosha/tree/main/data/concordance):
    **74,520 asserted links** (xref 12,836 · exact 61,373 · floor 311) joining the
    323,425-headword union to the 5.69M-token DCS corpus; coverage sidecar classes
    every headword (66,257 attested = 20.5%, the honest Zipf reality); manifest row
    `dict-corpus-concordance` added same pass.
  - **Golden-sample ruling** ([GOLDEN_SAMPLE.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/GOLDEN_SAMPLE.md)):
    mechanical checks 14/14, but the lossy `norm`-fold tier was 0/3 semantically
    correct (aṃśaka↔aṃsaka, vikarṣaṇa↔vikarśana) — its 2,171 links are
    **quarantined** to `dict_corpus_relaxed_candidates.tsv`, never asserted.
  - [`concordance/dict/`](https://github.com/gasyoun/kosha/tree/main/concordance/dict) —
    the reusable static concordance viewer (search → dict-provenance chips →
    tier-badged lemma links → KWIC with citable loci; 25 lazy shards, 32.9 MB;
    works on file://, trust block, CSV fallback; RISKS R12: no live service).
- **Static print co-location page (public Pages tier).** Executor: Opus 4.8
  (`claude-opus-4-8`), handoff H441.
  - [`scripts/build_colocation_page.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_colocation_page.py)
    renders [`colocation/`](https://github.com/gasyoun/kosha/tree/main/colocation)
    from `kosha.db` only (RISKS.md R12, no live service) — the static web
    counterpart of the `/api/v1/page` + `/api/v1/neighbors` endpoints (v0.15.0),
    live at [gasyoun.github.io/kosha/colocation](https://gasyoun.github.io/kosha/colocation/).
  - Self-contained `colocation/index.html` + lazy per-dict `colocation/data/<dict>.js`.
    Grouped on each dict's finest printed unit: PWG `(vol, page)` = Spalte;
    MW `(page, col)` cited `page,col`; Apte `(page, col)` cited `page+letter`.
    444,773 located entries.
  - **Paged two-column leaf view** — the book sets two columns per page, so the
    browser shows a whole leaf (left col `2P−1` + right col `2P` for PWG, all
    columns of the physical page for MW/Apte), with ← / → paging (and arrow keys),
    a column jump box, dictionary-wide head-word search, and per-head-word
    highlighting. Deep-linkable: `#<dict>/<col>?w=<slp1>` (the RU PWG article site
    links every column-mate in here). Honest caveat surfaced in the UI: the source
    records column numbers, not the book's printed page number, so left/right
    *column* is exact but recto/verso of the leaf is not derivable.

## [0.15.0] - 2026-07-09

### Added
- **Print co-location endpoints — "which words shared a printed page/column".**
  Executor: Opus 4.8 (`claude-opus-4-8`), handoff H434.
  - [`app/neighbors.py`](https://github.com/gasyoun/kosha/blob/main/app/neighbors.py)
    groups entries by the `(vol, page, col)` already parsed from each `<pc>`
    marker (for PWG, `page` is the Böhtlingk-Roth Spalte — the same value
    [`scan_resolver`](https://github.com/gasyoun/kosha/blob/main/app/scan_resolver.py)
    feeds to `servepdf.php`).
  - `GET /api/v1/page/{dict}?vol=&page=&merge=` — every entry sharing one printed
    column (`merge=1` folds the two columns of a physical leaf).
  - `GET /api/v1/neighbors/{dict}/{L}` — the column-mates of one entry, in
    printed order, query entry flagged `is_query`; each result carries its
    `headword` + `scan_url`.
  - `(dict, vol, page, L)` index in
    [`scripts/build_db.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db.py)
    for the group-filter + printed-order seek; 5 new tests
    ([`tests/test_api.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_api.py),
    25 green). Live PWG: 123,366 entries, 100 % `<pc>` coverage, 8,171 columns.
    Fail-closed on unparseable `<pc>` (G-PC gate). [PR #33](https://github.com/gasyoun/kosha/pull/33).

## [0.14.0] - 2026-07-09

### Added
- **Search-history retention purge.** Executor: Sonnet 5
  (`claude-sonnet-5`), handoff H416.
  - [`scripts/purge_search_events.py`](https://github.com/gasyoun/kosha/blob/main/scripts/purge_search_events.py)
    + [`history_db.purge_old_search_events()`](https://github.com/gasyoun/kosha/blob/main/app/history_db.py)
    delete raw `search_events` rows (per-visitor query log) older than
    `--days` (default 180). `daily_rollup` — the permanent anonymous
    per-day/per-term aggregate the `/api/v1/stats/*` charts read from — is
    never touched. `--dry-run` reports the count without deleting.
    MG-run maintenance script (A3 local-first: no agent cron).

## [0.13.0] - 2026-07-06

### Added
- **Sanskrit data-hub P-D3: public data + tools directory page.** Executor:
  Opus 4.8 (`claude-opus-4-8`), MG ruling D-HUB-7 (06-07-2026), handoff H236.
  - [`directory/index.html`](https://github.com/gasyoun/kosha/blob/main/directory/index.html)
    (live at [gasyoun.github.io/kosha/directory](https://gasyoun.github.io/kosha/directory/))
    — the first curated directory for Sanskrit computational linguistics: 9
    public datasets (downloadable), 6 restricted (listed "on request"), and 8
    external stacks (vidyut/Ambuda, Sanskrit Heritage/INRIA, Samsaadhanii/SCL,
    DharmaMitra, DCS, VedaWeb, Cologne CDSL) with what-it-does / how-to-call /
    license / our-relation.
  - [`scripts/build_directory.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_directory.py)
    renders it from [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
    + a new [`data/manifest/external_tools.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json)
    (single sources — no facts hand-copied into HTML). Carries schema.org
    `Dataset` JSON-LD per public asset on an Organization `@id` spine (SEO
    playbook P0) — the lever for Google/Yandex Dataset Search indexing.
  - `datasets.json` gained a `release_asset` field on the 7 released rows so the
    page can build 1-click download URLs from the manifest.
  - Test invariants: [`tests/test_directory.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_directory.py)
    (one Dataset node per public row, `@id` spine, no restricted-download or
    gitignored-path leak). Wired from the README + docs-site landing footer.

## [0.12.0] - 2026-07-06

### Added
- **Sanskrit data-hub P-D0/P-D1 (kosha becomes the org data-hub).** Executor: Fable 5
  (`claude-fable-5`), MG rulings 06-07-2026.
  - [`DATA_HUB_ROADMAP.md`](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md)
    — 8 locked decisions (D-HUB-1…8), two-tier architecture (public releases /
    restricted private backups), phases P-D0–P-D6.
  - [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
    — machine-readable manifest of 15 canonical derived datasets across the org
    (7 public released, 5 restricted, 3 already-public listed for discovery), with
    keying, rights tier, builder, consumers per row + the agent contract
    ([`data/manifest/README.md`](https://github.com/gasyoun/kosha/blob/main/data/manifest/README.md)).
  - First public data release
    [`data-v0.1.0`](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0):
    mw_roots · mw_etymology · dcs_cdsl_xref · union_headwords ·
    mw_heritage_crosswalk · lemma_frequency · headword_index (~29 MB, 718k rows,
    all already public in source repos; CC BY-SA 4.0).

## [0.11.0] - 2026-07-05

### Added
- **Search history + analytics (Phases A/B/C-frontend).** Executor: Sonnet 5
  (`claude-sonnet-5`).
  - Backend (Phases A/B): anonymous per-visitor search history
    ([`app/history.py`](https://github.com/gasyoun/kosha/blob/main/app/history.py),
    [`app/history_db.py`](https://github.com/gasyoun/kosha/blob/main/app/history_db.py),
    [`app/identity.py`](https://github.com/gasyoun/kosha/blob/main/app/identity.py))
    via a `kosha_anon_id` cookie, no login required; `GET`/`DELETE
    /api/v1/history`; public credential-free aggregate analytics
    (`GET /api/v1/stats/summary|timeseries|top`); a magic-link login stub
    (`/api/v1/auth/request-link|verify`) for cross-device history sync,
    email provider not yet chosen (@DECIDE). Writable history SQLite store
    kept separate from the read-only dictionary DB so the monthly dict
    rebuild never touches it. 13 new tests.
  - Frontend (Phase C): `History.svelte` (recent searches, clear button,
    magic-link request form) and `Stats.svelte` (summary cards, Chart.js
    daily-volume chart, top-terms table) added to the K2b inflection UI's
    tab bar, both hidden when no live API is configured (no static fallback
    exists for personal/live-aggregate data). First use of **Chart.js** in
    `ui/`. 4 new component tests.

### Notes
- Two items remain, both tracked in
  [Uprava/GTD_NEXT_ACTIONS.md](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md):
  MG `@DECIDE` (email provider + production `CORS_ORIGINS`, both deploy-time
  A3 steps) and an agent-doable `search_events` retention-purge script.

## [0.10.0] - 2026-07-05

### Added
- **Wave E1 (inflection roadmap) — dual-engine comparison, nominal pass.**
  Executor: Opus 4.8 (`claude-opus-4-8`).
  - [`scripts/compare_vidyut_cologne.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_cologne.py)
    diffs **vidyut-prakriya** (0.4.0, local library — R12-clean, no live call)
    against the ingested Cologne `inflections` tables, classifying every
    case×number cell (`AGREE`/`DIFF`/`VIDYUT_ONLY`/`COLOGNE_ONLY`) with DIFF
    sub-classification (ṇatva / pronominal / final-stop / superset / fork).
  - [`E1_DIVERGENCE_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md) —
    **90.5 % cell agreement** over 240k cells / 10k entry-bearing nominal stems.
    Findings: the ṇatva bug ([MWinflect#6](https://github.com/sanskrit-lexicon/MWinflect/issues/6))
    is confirmed with a **larger blast radius than the documented 69** (89 stems
    in the top-10k sample); pronominal stems (`sarva`) mis-modelled as nominals;
    cardinal numerals (`saptadaśan`) missing from Cologne but generated by
    vidyut; feminine consonant/monosyllabic-stem derivation forks. Continues Jim
    Funderburk's Cologne-vs-Huet line ([csl-inflect#10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10))
    with an independent third engine.
  - **Recommendation: hybridize** (keep Cologne base per D3, layer vidyut to
    auto-fix ṇatva + fill gaps + flag forks) — filed as an @DECIDE for MG.

### Notes
- E1 remainder is human-gated: the migrate/hybridize/stay **ruling** (MG
  @DECIDE) and the **give-back post** to csl-inflect#10 (diplomacy-gated,
  drafted not posted), plus the agent-doable **verb comparison** (answers
  csl-inflect#8) — all queued in
  [H185](https://github.com/gasyoun/Uprava/blob/main/handoffs/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md).
  E1 raw comparison output (`data/e1/`) is gitignored (regenerable).

## [0.9.0] - 2026-07-05

### Added
- **P4 Wave K2b** (H183) — the translator-first Sanskrit **inflection lookup
  UI**, the frontend half of the drastically-improved Cologne inflection tool.
  Executor: Opus 4.8 (`claude-opus-4-8`).
  - **Svelte 5 + Vite app** ([`ui/`](https://github.com/gasyoun/kosha/tree/main/ui))
    building into [`docs/inflect/`](https://github.com/gasyoun/kosha/tree/main/docs/inflect),
    served by the existing Pages deploy at `gasyoun.github.io/kosha/inflect/`
    (62 kB JS bundle). Four features (H183 K2b-3, roadmap Wave K3 folded in):
    **stem → paradigm** (auto-detect input → SLP1, Devanagari-default
    case×number / verb grids with an IAST/SLP1 toggle), **paste-anything
    reverse analysis** (wraps `/analyze`, shows `resolved_by` provenance),
    **autocomplete** (prefix range-seek over the shared 323k `lemmas.json`,
    live transliteration), and **dictionary cross-links** (every stem links to
    its in-app MW/PWG/AP90 entry; the entry has a "show all forms" control back
    to the paradigm — two silos, one tool).
  - **Data backend is "both"** (K2b-2, [`ui/src/lib/datasource.js`](https://github.com/gasyoun/kosha/blob/main/ui/src/lib/datasource.js)):
    static pre-generated JSON by default (works with **no live server** —
    RISKS.md R1/R5/R12-clean), and the live FastAPI `/api/v1/…` when
    `window.KOSHA_API` is set. Stage-3 vidyut segmentation degrades honestly to
    `segmentation_available:false` in the static tier (the live-API path
    resolves it).
  - **New `GET /api/v1/paradigm/{lemma}`** endpoint + shared
    [`app/paradigm.py`](https://github.com/gasyoun/kosha/blob/main/app/paradigm.py)
    grouping module, and
    [`scripts/build_paradigms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_paradigms.py)
    emitting parity-locked static paradigm + reverse-index shards
    (`--demo` committed, `--all` deployed by MG out-of-band per A3). Bridged
    stems fold (`Bagavant`→`Bagavat`).
  - **Auto-detect input** (Devanagari/IAST/SLP1) via the vendored **sanskrit-util**
    JS package (SHARED_CODE.md family #1 — no new transcoder); Devanagari
    rendering uses `slp1_to_devanagari` (composes matras/conjuncts) not the
    naive `iast_to_devanagari`.
  - **Tests:** 6 new pytest (`tests/test_paradigms.py`, endpoint + static-shard
    byte-parity) → **167 passed**; 17 vitest (translit auto-detect, token
    parity, prefix seek, static data-path integration, full App e2e).
  - **Data caveat surfaced verbatim** (D3): the Cologne m_a ṇatva bug
    (MWinflect#6) is shown as-is, not silently "fixed" in the frontend.

### Notes
- Roadmap Wave **K3 folded into K2b** per MG 05-07-2026 — the inflection roadmap
  now owes only Wave E1 (dual-engine vidyut comparison).
- Pages tier re-measured: `docs/inflect/` = 2.0 MB (app + committed demo data);
  total tier ~404 MB, ~60% headroom under the 1 GB soft limit unchanged.

## [0.8.0] - 2026-07-05

### Added
- **P4 Wave K2a** (H181) — reverse-lookup query pipeline, verb-form ingest,
  and the stem-normalization bridge. Executor: Opus 4.8 (`claude-opus-4-8`).
  - **Reverse-lookup cascade** ([`app/reverse_lookup.py`](https://github.com/gasyoun/kosha/blob/main/app/reverse_lookup.py))
    behind `GET /api/v1/forms/{form}/analyze`: `inflections` exact hit →
    `forms` witness → **vidyut-cheda segmentation** of a sandhied/compound
    string, each stage tagged with a `resolved_by` provenance field
    (`inflections`/`forms`/`segmentation`/`null`). Segmentation
    ([`app/segmenter.py`](https://github.com/gasyoun/kosha/blob/main/app/segmenter.py))
    runs vidyut 0.4.0 as a **local library over vendored data**
    (`data/vidyut/`, gitignored); no live third-party call at build or query
    (RISKS.md R12), and it degrades to an honest miss (`segmentation_available:
    false`) when the data isn't vendored.
  - **Verb conjugations ingested** — the upstream MWinflect Python-2 syntax
    bug in `verbs/pysanskritv2/inputs/clean.py` (parenthesized-tuple lambda
    parameter) that blocked `verbs/redo.sh` in K1 is fixed and prepared as an
    on-its-merits upstream PR. [`scripts/build_inflections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_inflections.py)
    now loads present-system conjugations (pre/ipf/ipv/opt × active/middle/
    passive) into `inflections` (**+67,140** rows; total 6,916,522) with new
    `person`/`tense`/`voice` columns (NULL for nominals). So `Bavati` now
    resolves as 3sg present of `BU`.
  - **Stem-normalization bridge** ([`scripts/build_stem_bridge.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_stem_bridge.py)
    → `stem_bridge` table, `--stage stem_bridge`) maps strong/weak stem-spelling
    variants across `inflections` (`Bagavat`) and `forms` (`Bagavant`) to one
    canonical lemma key. Narrow, data-gated rule (nt→t / drop-final-n, only
    when the two spellings share a surface form) — 380 mappings; the named exit
    case `Bagavant → Bagavat` unifies to one lemma.
  - Tests: new [`tests/test_reverse_lookup.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_reverse_lookup.py)
    (cascade, verb ingest, bridge, segmentation + graceful degradation); full
    suite **161 passed**. Documented in
    [`data/SOURCES.md`](https://github.com/gasyoun/kosha/blob/main/data/SOURCES.md)
    (incl. the ṇatva caveat and the honest `dharmakSetre`-resolves-at-stage-1
    deviation from the brief's assumption).

## [0.7.0] - 2026-07-03

Phase 3 (evidence layer) + Phase 4 Wave K1 (inflection data ingest), landed
together via [PR #9](https://github.com/gasyoun/kosha/pull/9) (branch
`feat/p3-evidence-p4-k1-inflect`, Sonnet 5 `claude-sonnet-5`) — both tracks
ran as parallel sessions against the same checkout and ended up
file-interleaved in `app/main.py`/`scripts/build_db.py`, so they ship as one
release. P3 builds on P1's frequency LEFT-JOIN rather than duplicating it in
a new table (the P3 plan's original spec is now redundant with what's
already on `lemmas`). Full suite green: 149 passed (26 new in
`tests/test_evidence.py`, 6 new in `tests/test_inflections.py`), 1
pre-existing unrelated failure (`test_docs_site.py::test_committed_output_is_current`,
docs-site staleness from the parallel Wave-3 docs-site work already in
flight, not caused by this release).

### Added
- **P4 Wave K1** (data ingest + JSON API) — new `inflections` sidecar table
  ([`scripts/build_db.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db.py)
  SCHEMA + `--stage inflections`) loaded by
  [`scripts/build_inflections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_inflections.py)
  from the sibling MWinflect checkout's Cologne csl-inflect nominal
  declension tables (`nominals/pysanskritv2/tables/calc_tables.txt`, engine =
  Cologne verbatim per
  [ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md)
  D3). 6,849,382 (form, lemma, model, gender, case, number) rows from
  288,844 stems, 3,267,305 distinct forms. New read-only
  `GET /api/v1/forms/{form}/analyze` endpoint
  ([`app/main.py`](https://github.com/gasyoun/kosha/blob/main/app/main.py))
  returns every grammatical parse for a form. Verb conjugations are **not**
  included — MWinflect's `verbs/` pipeline is blocked by a Python-2-only
  syntax bug in `verbs/pysanskritv2/inputs/clean.py` (upstream issue, not
  fixed here; see `.ai_state.md` for the exact trace). 6 new tests in
  [`tests/test_inflections.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_inflections.py)
  hand-verify the roadmap's exit-test forms (`bhagavAn`, `rAmeRa`,
  `dharmakSetre`) against `calc_tables.txt`.
- **P3 evidence layer** —
  [`scripts/build_evidence.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_evidence.py)
  (new `--stage evidence`, wired into the default full build) adds two things
  additively to `lemmas` via `ALTER TABLE`: a **frequency band** (1–5, over
  `rank_all`; thresholds chosen from the D5-measured fact that the top 10,000
  ranked lemmas already cover 95.4% of corpus token mass — full reasoning in
  the module docstring) and **one corpus example per lemma** (Sanskrit
  citation + aligned Russian, joined from the sibling
  [`SanskritLexicography/RussianTranslation/src/corpus_lexicon.jsonl`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/corpus_lexicon.jsonl)
  (1,091,528 rows) via the existing `forms.form_slp1 -> lemma_slp1` join —
  examples ship **per lemma, not per sense**: the corpus feed has no
  sense-level tagging, stated explicitly rather than silently downgraded.
  Band distribution on the live spine: 1=493, 2=1,441, 3=7,484, 4=51,922,
  5=262,085 (no DCS signal); 38,595 lemmas got a corpus example.
- **[`app/evidence.py`](https://github.com/gasyoun/kosha/blob/main/app/evidence.py)** —
  shapes the DB columns into the API's evidence block; `/api/v1/lemma`
  entries now carry `evidence: {band, band_label, rank_all, count_all,
  first_era, genre, example, badges}`, every `badges[]` item carrying its own
  `source` string (fail-closed per EVAL_PLAN.md rule 4: a lemma with no DCS
  signal gets `count_all: null` / `example: null`, never a fabricated `0` or
  invented citation; `genre` is honestly `null` — not derivable from the
  current DCS extraction, which stores only a chronological period vector).
  Mirrored into
  [`scripts/build_static_cache.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_static_cache.py)'s
  `entry_payload()` (same lockstep-mirror pattern as `sense_ids`) so the P2
  static tier stays byte-identical to the live API.
- **`/api/v1/search` frequency-weighted ranking** — results now order by
  exact-key-match-first, then `rank_all ASC` (nulls last), then `slp1 ASC`,
  replacing plain alphabetical.
- **[`tests/test_evidence.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_evidence.py)**
  (26 tests) — `dharma` band/count/example (T-UC4 positive), a fail-closed
  negative case (band-5 lemma: no fabricated 0, no invented example),
  provenance-label-on-every-badge, a frozen 20-headword sample spanning all 5
  bands checking both band assignment and that search ranking measurably
  differs from alphabetical order (>=50% of multi-result queries in the
  sample reorder; sortedness verified directly).

## [0.6.0] - 2026-07-03

### Added
- **H111: Heritage/INRIA forms as a third, low-trust `forms` witness.**
  `forms` gains a nullable `category` column (migrated in `scripts/build_db.py`
  for pre-existing `kosha.db`s) and `scripts/build_forms.py` now loads
  [`heritage_only_forms.tsv`](https://github.com/gasyoun/SanskritLexicography/blob/master/HeadwordLists/heritage_only_forms.tsv)
  as `source='heritage'`, purely additive and loaded last: **+951,991** rows
  (`dcs` 397,843 and `vidyut` 28,567 unchanged). Trust ordering
  `dcs > vidyut > heritage` — Heritage's declension engine over-generates
  grammatically-possible but unattested forms — documented in
  [ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md),
  `build_forms.py`, and
  [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md).
  `/api/v1/form` already returned `source` per result, so heritage-only hits
  are distinguishable client-side without an API change.

## [0.5.0] - 2026-07-03

Phase 2 (public alpha) first agent-doable slice: the **static-cache generator**
that emits the GitHub Pages tier from `kosha.db` (branch `feat/p2-static-cache`,
Opus 4.8 `claude-opus-4-8`), built to the fixed D5-3 targets. 107 → **115** tests
green. Enabling Pages / deploying stays MG's (A3).

### Added
- **P2 static-cache generator** —
  [`scripts/build_static_cache.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_static_cache.py)
  emits three deliverables from the local DB (never a live service, R12), each
  matching [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md)
  D5-3:
  1. **Sharded per-lemma cards** — one JSON per lemma (never one bundle; a single
     `lemmas.json` crosses the 100 MB/file cap at ~33k), for the **50,355**
     lemmas with both a dict entry and a corpus attestation, **frequency-ranked**
     so a partial/interrupted run front-loads value (top-10k = 95.4% of corpus
     token mass) and resumes idempotently (existing shards skipped). Each card is
     **byte-identical** to `GET /api/v1/lemma/<slp1>?in=slp1` (reuses `app/`
     render/scan/transliterate — no reimplementation). ~155 MB, ~3 KB/file.
  2. **Headword autocomplete index** — one ~13 MB columnar file, all 323,425
     lemmas (`slp1`+`iast`+`dicts`); this is what the gitignored
     `docs/js/data/lemmas.json` path holds (D5-3a: the INDEX, not the cards),
     plus a tiny `attested_keys.json` sidecar so the UI picks static-vs-dynamic
     without a 404 probe.
  3. **Full 222,179-lemma card set** as an opt-in `--full-tarball` release asset
     (R1c/R4 rebuildability), deterministic (`mtime=0`), not committed.
- **Card filename encoding** (`card_token`) — keeps `[a-z0-9]` verbatim, escapes
  every other UTF-8 byte (incl. uppercase — SLP1 is case-significant and would
  collide on a case-insensitive FS) as `_<hexbyte>`; lossless, URL/FS-safe, with
  a documented JS twin for the frontend.
- **[docs/README.md](https://github.com/gasyoun/kosha/blob/main/docs/README.md)** —
  the Pages static-tier layout, token scheme + JS twin, and regeneration/deploy
  commands.
- **[tests/test_static_cache.py](https://github.com/gasyoun/kosha/blob/main/tests/test_static_cache.py)**
  (8 tests) — locks card↔live-API byte parity, `card_token` case-safety and
  lossless round-trip, ranked-shard generation, and index/attested counts
  (323,425 / 50,355).

### Changed
- `.gitignore` — the generated Pages tier (`docs/cards/`,
  `docs/js/data/attested_keys.json`, alongside the already-ignored
  `docs/js/data/lemmas.json`) is regenerable and MG-deployed, so it is not
  committed.

## [0.4.0] - 2026-07-03

Phase 1 **D5 — measure, then decide** (branch `feat/phase1-d5-measure`, Opus 4.8
`claude-opus-4-8`). The last Phase-1 step: real numbers behind the parked SLO
items, the decisions they force, a fixed latency bug the measuring surfaced, and
the R3 fallback turned from a comment into a tested path. 107/107 tests still
green. Phase 1 is complete; P2 (public alpha) can start against fixed targets.

### Added
- **D5 measurement report** —
  [D5_MEASUREMENTS.md](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md):
  DB size (276.4 MiB, 2.9× over the GitHub 100 MB/file cap → release-asset only,
  R11), cold/warm latency across all four read endpoints incl. the fat MW `ka`
  homonym group, per-dict `render()` cost + the full body-size distribution
  (97.3% of entries <1k chars; only 9 bodies >100k, all PWG), and a top-N
  static-cache projection. Reproducible from the committed harness
  [`scripts/measure_d5.py`](https://github.com/gasyoun/kosha/blob/main/scripts/measure_d5.py).
- **D5 decisions record** —
  [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md):
  latency SLO (p50<20ms / p95<100ms / p99<250ms server-side), rebuild cadence
  (change-triggered ~monthly, **not** nightly — nightly would mint needless
  citable `data_version`s, R1 tension), static-cache N (~50,355 attested-with-
  entry lemmas, sharded per-lemma ~155 MB, frequency-ranked). Relocated from the
  referenced SanskritLexicography path to this repo (canonical home); doc links
  repointed.
- **R3 csl-orig fallback exercised** (RISKS.md R3, now a tested path) —
  [`scripts/fallback_csl_orig.py`](https://github.com/gasyoun/kosha/blob/main/scripts/fallback_csl_orig.py)
  parses csl-orig `ap90.txt` directly and recovers **100%** of the entry
  inventory (34,882 records; every `<L>`, `<k1>` key, `<pc>` token matches the
  csl-sqlite-built DB). Honest boundary documented: bodies are the upstream
  display-markup stage, so a render()-able fallback also needs the csl-orig→XML
  `make_xml` step.

### Fixed
- **Lemma-lookup table scan (240 ms → ~0.3 ms).** `GET /api/v1/lemma` filtered
  `(dict, slp1_key)` but the planner seeked only on `dict` (via the
  `UNIQUE(dict,L)` autoindex, which also served `ORDER BY L`) and scanned all
  ~286k MW rows. A covering index `entries(dict, slp1_key, L)` (replacing
  `entries_key`, plus `ANALYZE` at build) serves both the seek and the ordering.
  Warm handler latency: lemma `kamala` 172→10.9 ms, `ka` 169→19.6 ms; e2e over
  HTTP 338→31 ms. Schema change in
  [`scripts/build_db.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_db.py);
  the SLO (D5-1) assumes this index.

### Changed
- **`sources.csl_orig_commit` provenance resolved** (was flagged open) by
  cross-dating the csl-sqlite release timestamp against the local csl-orig commit
  log (offline, R12-safe): mw `392ed6b`, pwg `8822922`, ap90 `51232f2` — an
  upper bound, labelled as such. Wired into
  [`scripts/build_entries.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_entries.py)
  (`cross_date_csl_orig_commit`) and applied to the DB so `/api/v1/meta` surfaces
  it. Feeds R3's "data as of {date}" footer.
- ARCHITECTURE.md parked table: latency-SLO/cadence and static-cache-N rows
  resolved; DDL updated to the covering index. PHASE1_PLAN.md D5 marked done.

### Still open (not blocking)
- PWG multi-volume `servepdf.php` disambiguation needs a **live content diff**
  against Cologne (not a build-time or offline check, R12) — left flagged in
  [`.ai_state.md`](https://github.com/gasyoun/kosha/blob/main/.ai_state.md);
  belongs to scan-link hardening (G-SCAN/R2), not D5.

## [0.3.0] - 2026-07-03

Phase 1 D1–D4 **plus** the three D4-contract pieces PR
[#2](https://github.com/gasyoun/kosha/pull/2) deferred, closed here (branch
`feat/phase1-d4-followon`, Opus 4.8 `claude-opus-4-8`). 20 → **107** tests
green. Every measured number + deviation stays in
[`data/SOURCES.md`](https://github.com/gasyoun/kosha/blob/main/data/SOURCES.md).

### Added
- **Phase 1 D1–D4** (originally PR #2): lemma spine + frequency join (D1),
  per-dict `<pc>` entry loader for mw/pwg/ap90 (D2), forms layer + scan-URL
  resolver (D3), kosha API v1 + Salt facade REST faces + pytest suite (D4).
- **Full `render()` port** (ARCHITECTURE.md A1) —
  [`app/render.py`](https://github.com/gasyoun/kosha/blob/main/app/render.py) is
  now a code-level faithful port of the mw/pwg/ap90 path of csl-websanlexicon's
  canonical `basicdisplay.php` (SAX display engine) + the relevant
  `basicadjust.php` passes, replacing the earlier partial subset. Two documented
  deviations: server-side `<s>` SLP1→IAST via sanskrit-util (not client-JS
  `<SA>`), and no DB-backed abbreviation tooltips / external `<ls>` hrefs (the
  ls_resolver.py D3 follow-on). **38 frozen, checksummed golden HTML snapshots**
  (mw 14 incl. the banD/akṣa fixtures, pwg 12, ap90 12 — ≥10/dict merge bar) in
  [`tests/golden/`](https://github.com/gasyoun/kosha/tree/main/tests/golden),
  seeded-selected per EVAL_PLAN.md §0 anti-gaming, tested by
  [`tests/test_render_golden.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_render_golden.py).
- **Per-dict sense segmentation** (D2) —
  [`app/segment.py`](https://github.com/gasyoun/kosha/blob/main/app/segment.py)
  splits each body at its `<div>` division markers (MW `to`/`vp`, PWG numbered
  `1〉`/`a〉`, AP90 bold-numbered) into byte-anchored `senseN` spans (A2),
  replacing the single-sense fallback (kept only for markerless entries). Live
  counts: MW 303,022 · PWG 223,446 · AP90 165,935 senses.
- **R1 citability** (RISKS.md R1 Commitments 1–2) — the `cite` object now
  carries a browser-resolvable `resolution_url` + durable `release_asset`
  permalink + BibTeX/CSL-JSON
  ([`app/cite.py`](https://github.com/gasyoun/kosha/blob/main/app/cite.py));
  `/api/v1/sense/{id}@version` resolves an **old** citation against its archived
  release dump
  ([`app/versions.py`](https://github.com/gasyoun/kosha/blob/main/app/versions.py),
  [`scripts/archive_senses.py`](https://github.com/gasyoun/kosha/blob/main/scripts/archive_senses.py)),
  the path **T-UC10** forces; every rebuild can emit `sense_crosswalk.tsv`
  (old→new senseN via span-text similarity, SPLIT/MERGED/GONE/MOVED, zero-cost
  when unchanged —
  [`scripts/build_crosswalk.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_crosswalk.py)).
  Verified on real PWG data + unit-tested in
  [`tests/test_citability.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_citability.py).

### Still deferred (flagged, not silent)
- `sources.csl_orig_commit` still records the csl-sqlite release tag only (the
  underlying csl-orig commit is not exposed by the release format).
- PWG multi-volume scan disambiguation: `servepdf.php` returns 200 for `page=`,
  `page=&vol=`, and `page=&volume=` alike (tolerant of unknown params); whether
  `vol` is honored is not determinable from status alone. Still open.

## [0.2.1] - 2026-07-02

README rewritten for a layered dual audience (MG request; authored by Fable 5
`claude-fable-5`): public-facing top, engineering spine below.

### Changed
- **[README.md](https://github.com/gasyoun/kosha/blob/main/README.md)** — drastic
  rewrite: brand-led H1 (**Gasuns Sanskrit Dictionary**, kosha = codename); prominent
  pre-alpha "nothing runs yet" banner; public pitch + feature list + P1–P7 roadmap
  snapshot; new **FAQ** (18 questions across using-it / vs-existing-sites /
  status-timeline / licensing-reuse); planning spine preserved under "For contributors
  & agents" (reuse-first table, A1–A4, ground rules, full document map incl. the
  SanskritLexicography planning corpus). No decisions changed — presentation only.

## [0.2.0] - 2026-07-02

The judgment layer completed — the three plans queued in
[.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md) §Next Steps 1,
authored by Fable 5 (`claude-fable-5`). With these, the P1 execution session (Sonnet 5
`claude-sonnet-5` / Opus 4.8 `claude-opus-4-8`) is fully gated: EVAL_PLAN's gates bind.

### Added
- **[EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md)** — quality
  gates designed so an executor can't game them: 8 anti-gaming ground rules (freeze
  before first scored run, selection by committed procedure, thresholds live in the doc,
  fail closed, snapshot discipline, scorer ≠ system, no ✅ without artifact); G-SEG
  200-form stratified segmentation gold (9 classes incl. out-of-DCS contamination
  holdout + calibration rule); G-RENDER adversarial golden selection (accented PWG
  key2, `-L{lnum}` homonyms, densest MW `<ls>` cards, the ळ→x + IAST traps from
  [FINDINGS §36/§39](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md));
  G-SALT parity tolerances vs csl-apidev's `agni`/`indra`/`ka` envelopes (unlisted =
  exact); G-SCAN page-truth beyond HTTP 200; every
  [USE_CASES.md](https://github.com/gasyoun/kosha/blob/main/USE_CASES.md) *Accept:* line
  as a named test (T-UC1…T-UC13, Gītā 1.1 locked as the UC6 verse).
- **[RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md)** — ecosystem
  diplomacy: the Meyer permission ask drafted (his 7 self-digitized indices off-limits
  without written yes; send at P2 exit); Cologne-maintainer framing paragraph ("kosha
  serves your Salt standard", one csl-standards issue, no noise); Ambuda/vidyut
  give-back (G-SEG report upstream, name-collision rule: public name = Gasuns Sanskrit
  Dictionary); C-SALT/CCeH sense-face contribution; binding upstream-vs-track-3
  decision table; 7-row contact registry (all sends = MG).
- **[RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md)** — pre-mortem
  register R1–R12: `@data_version` is airtight only under 4 new commitments (in-browser
  version resolution forced by T-UC10, `sense_crosswalk.tsv` per release, **Zenodo
  mirroring moved up from P7 to the first citable release**, never-delete policy);
  scan-link page-truth (a wrong link is worse than none); csl-sqlite lag measured +
  surfaced as "data as of"; single-maintainer rot mirror-test + archive-banner policy;
  samskrtam.ru bus factor (citations never point at the server); license geometry
  (DCS dump license ask before P3 public; gramdict CC BY-NC must not enter BY-SA data).

## [0.1.0] - 2026-07-02

Founding release — the complete planning/contract layer, authored in one day by
Fable 5 (`claude-fable-5`) after MG green-lit Phase 1. No application code beyond the
honest stub; nothing claims ✅ without a passing check.

### Added
- **Repo created** per meta-decisions M1–M4 (triage of the fabricated planning corpus:
  [SanskritLexicography v0.0.34](https://github.com/gasyoun/SanskritLexicography/releases/tag/v0.0.34)); seeded README, reuse-first
  [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md) (D1–D5 with per-day exit checks), stub `app/main.py`.
- **[POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md)** + [summary](https://github.com/gasyoun/kosha/blob/main/POSITIONING_SUMMARY.md):
  product name **Gasuns Sanskrit Dictionary**; three-track identity (improve source ·
  improve Cologne UI · own advanced service); MG override recorded — own advanced UI,
  API-first.
- **[COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md)** — 12-platform live survey (all fetched 02-07-2026):
  michaelmeyer.fr = 41 dicts w/ per-sense scan links (positioning corrected — the
  read-only collapse exists); Heritage Inria bot-walled; DCS HTTPS broken; VedaWeb→Tekst;
  vidyut-kosha has no end-user UI. Mirrored as
  [FINDINGS §41](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md) (PR [#55](https://github.com/gasyoun/SanskritLexicography/pull/55)).
- **[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)** — engineering contract A1–A4: raw-markup storage +
  csl-websanlexicon-ported renderer (golden tests mandatory); sense IDs
  `dict.L.senseN@data_version`; local-first (MG deploys, agents never SSH); Sonnet/Opus
  executes. SQLite DDL, API v1 contract, encoding policy.
- **Salt API max-reuse (required):** Salt-profile entry object as the interchange shape
  inside `/api/v1`; entry data from csl-sqlite releases; Salt facade REST faces in P1/D4
  parity-tested vs csl-apidev envelopes; GraphQL face by P7.
- **Licenses:** code CC BY-NC 4.0 ([LICENSE.md](https://github.com/gasyoun/kosha/blob/main/LICENSE.md)); data releases CC BY-SA 4.0
  inherited from Cologne ([LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md) — csl-orig verified BY-SA, so NC
  attaches to code only).
- **[IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md)** — P1 data+API → P2 public alpha → P3 evidence
  layer → P4 forms+grammar → P5 advanced UI → P6 trilingual RU (G5 + Kochergina gates) →
  P7 citable v1.0 (DOI); per-phase exit checks; MG critical path.
- **[USE_CASES.md](https://github.com/gasyoun/kosha/blob/main/USE_CASES.md)** — 13 concrete scenarios (translators, students, scholars,
  machine consumers) mapped to delivering phases; acceptance-test seeds for EVAL_PLAN.
- **[.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md)** — session-state protocol; next queued: Fable chat authoring
  EVAL_PLAN.md + RELATIONS.md + RISKS.md, and the Sonnet/Opus P1 execution session.

_Dr. Mārcis Gasūns_
