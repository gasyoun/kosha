# Architecture contract — Gasuns Sanskrit Dictionary (kosha)

_Created: 02-07-2026 · Last updated: 02-07-2026_

The engineering contract for Phase 1, locking the four decisions M.G. took on
02-07-2026 (A1–A4 below) on top of the product meta-decisions M1–M4
([KOSHA_FOLDER_SETUP.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_FOLDER_SETUP.md)).
An execution session (Sonnet 5 `claude-sonnet-5` / Opus 4.8 `claude-opus-4-8`)
implements [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md)
against this document; deviations get recorded here first.

## Locked decisions (A1–A4, M.G. 02-07-2026)

| # | Decision |
|---|---|
| A1 | **Storage = raw csl-orig markup, verbatim; display = ported transforms.** Entry bodies stored exactly as in csl-orig (provenance-perfect); rendering is a pure Python function ported from csl-websanlexicon's `basicadjust.php`/`basicdisplay.php` (SHARED_CODE family #5 — port from the makotemplates *template*, not a per-dict copy). Rendering bugs are fixed in code, never by rebuilding data |
| A2 | **Sense IDs = `{dict}.{L}.{senseN}` + data-release version**, e.g. cite form `mw.142512.3@v0.2.0`. Anchored on Cologne's stable per-entry L-numbers; sense counter minted within the entry; the `@version` suffix makes citations survive Cologne corrections (old versions stay downloadable as release assets) |
| A3 | **Local-first; M.G. deploys manually.** Agents develop and test everything locally (SQLite + uvicorn + pytest). Server deployment to samskrtam.ru is M.G. running the documented steps in [KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_DEPLOYMENT.md). No agent holds SSH, ever |
| A4 | **Execution queued to Sonnet/Opus.** This contract is the judgment-tier deliverable; D1–D4 run in a cheaper session; D5's measurement-based decisions return to a judgment tier |

## Data model (SQLite, single file `kosha.db`)

```sql
-- Build provenance
CREATE TABLE meta    (key TEXT PRIMARY KEY, value TEXT);
-- keys: data_version (semver), built_at, builder
CREATE TABLE sources (dict TEXT PRIMARY KEY,          -- 'mw' | 'pwg' | 'ap90'
                      title TEXT, edition TEXT,
                      csl_orig_commit TEXT NOT NULL,  -- provenance per dict
                      source_path TEXT,
                      pc_format TEXT NOT NULL,        -- 'page,col' | 'vol-page' | 'page-col-letter'
                      pc_coverage REAL,               -- measured in D2, not assumed
                      entry_count INTEGER);

-- Lemma spine: vendored union_headwords.tsv (323,426 rows), unchanged
CREATE TABLE lemmas  (slp1 TEXT PRIMARY KEY, iast TEXT NOT NULL,
                      n_dicts INTEGER, dicts TEXT, gender TEXT);

-- One row per Cologne record; body is VERBATIM csl-orig markup (A1)
CREATE TABLE entries (id INTEGER PRIMARY KEY,
                      dict TEXT NOT NULL REFERENCES sources(dict),
                      L TEXT NOT NULL,                -- Cologne <L>; TEXT (suffixed L-numbers exist)
                      slp1_key TEXT NOT NULL,         -- <k1>
                      k2 TEXT,                        -- <k2> (print form)
                      pc_raw TEXT,                    -- <pc> verbatim
                      vol INTEGER, page INTEGER, col TEXT,  -- parsed per pc_format
                      body TEXT NOT NULL,
                      UNIQUE(dict, L));
CREATE INDEX entries_key ON entries(slp1_key);

-- Sense map for ID minting (A2): senseN -> byte span in body.
-- Segmentation rule is PER-DICT, defined and golden-tested in D2
-- (MW: numbered sense markers; PWG: dash/number dividers; AP90: numbered).
-- Fallback when segmentation is unclear: single sense 1 spanning the body —
-- an entry-level citation is always mintable.
CREATE TABLE senses  (entry_id INTEGER NOT NULL REFERENCES entries(id),
                      sense_n INTEGER NOT NULL,
                      span_start INTEGER NOT NULL, span_end INTEGER NOT NULL,
                      PRIMARY KEY (entry_id, sense_n));

-- Form -> lemma layer, imported from RussianTranslation/glossary (D3)
CREATE TABLE forms   (form_slp1 TEXT NOT NULL, lemma_slp1 TEXT NOT NULL,
                      source TEXT NOT NULL,           -- 'dcs' | 'vidyut' | ...
                      PRIMARY KEY (form_slp1, lemma_slp1, source));
CREATE INDEX forms_lemma ON forms(lemma_slp1);
```

Scan URLs are **computed, not stored**: the ls_resolver port is a
deterministic function of `(dict, vol, page, col)` — no table, no staleness.

**Versioning (A2):** every published rebuild bumps `meta.data_version` and
ships as a GitHub release with the SQLite file + per-table dumps as assets.
A citation `mw.142512.3@v0.2.0` resolves against that release forever, even
after Cologne corrects the entry and v0.3.0 renumbers senses. `sources`
records the exact csl-orig commit per dictionary per release.

## Rendering (A1)

`app/render.py`: pure function `render(dict, body) -> html`, ported from
[csl-websanlexicon `v02/makotemplates/web/webtc/`](https://github.com/sanskrit-lexicon/csl-websanlexicon)
`basicadjust.php` + `basicdisplay.php` (the canonical template — per
SHARED_CODE §5, never port one of the ~37 drifted per-dict copies).
Transliteration of `<s>` spans via **sanskrit-util** (no new transcoder).
**Golden tests**: ≥10 sample entries per dictionary with committed HTML
snapshots; the renderer cannot merge without them.

## API v1 contract

Prefix `/api/v1/`. JSON only. Every response carries the envelope:

```json
{ "data_version": "0.2.0", "query": { ... }, "results": [ ... ] }
```

| Endpoint | Behavior |
|---|---|
| `GET /api/v1/lemma/{key}?in=auto&out=iast&dicts=mw,pwg,ap90` | Entries across requested dicts for one lemma. `in`: `auto` (default; detect SLP1/IAST/HK/Devanagari — the sanskritdictionary.com lesson) or explicit. `out`: `iast` (default), `deva`, `slp1`, `hk`. Each entry: `sense_id`s, rendered HTML, raw body on `?raw=1`, scan URL + label |
| `GET /api/v1/form/{form}?in=auto` | Form→lemma(s) via `forms`, then as lemma lookup. Misses return `lemmas: []` plus fuzzy suggestions |
| `GET /api/v1/search?q=&mode=prefix&limit=50&offset=0` | Headword search over `lemmas`; `mode`: `exact`/`prefix`/`fuzzy`. Paginated: `limit` ≤ 200, `offset`, `total` in envelope |
| `GET /api/v1/sense/{dict}.{L}.{n}` | The citable unit: sense text (raw + rendered), parent entry, scan link, and a `cite` object (formatted string + BibTeX + CSL-JSON) pinned to `data_version` — the Gandhāri Cite button, versioned |
| `GET /api/v1/meta` | `data_version`, per-dict `sources` rows, counts |
| `GET /health` | `{"status":"ok"}` (unversioned, for probes) |

**Errors** (uniform): HTTP status + `{"error": {"code": "lemma_not_found",
"message": "...", "suggestions": [...]}}`. Codes: `bad_input_scheme`,
`lemma_not_found`, `form_not_found`, `sense_not_found`, `bad_request`.

**Encoding policy:** SLP1 is the internal key everywhere; IAST is the default
display; conversion at the boundary only, via sanskrit-util.

## Dev/deploy boundary (A3)

- **Local:** `pip install -r requirements.txt`; build DB with
  `scripts/build_db.py` (D1–D3); `uvicorn app.main:app`; `pytest` must be
  green incl. golden renders before anything is called done.
- **Deploy:** M.G. only, following KOSHA_DEPLOYMENT.md Part II (systemd
  `Type=exec`, nginx with explicit `proxy_pass` blocks). Agents prepare
  artifacts and instructions; they never touch the server.
- **Static tier (Phase 2):** generated into `docs/` from the same DB; size
  measured against the GitHub 100 MB file limit in D5 before enabling Pages.

## Explicitly still open (parked, with owner)

| Item | Owner / when |
|---|---|
| Latency SLO + rebuild cadence | D5, with measurements |
| Static-cache N (top lemmas) | D5, measured |
| ~~Code license~~ | ✅ Resolved 02-07-2026: code CC BY-NC 4.0 ([LICENSE.md](https://github.com/gasyoun/kosha/blob/main/LICENSE.md)); data releases CC BY-SA 4.0 inherited from Cologne ([LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md)) |
| Sense-segmentation rule details per dict | D2 (per-dict, golden-tested; fallback = single sense) |
| Etymology depth (links-first) | Phase 3 |

---

_Dr. Mārcis Gasūns_
