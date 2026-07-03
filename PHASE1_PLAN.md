# Phase 1 — reuse-first work order

_Created: 02-07-2026 · Last updated: 02-07-2026_

Replaces the original "2 weeks to extract + index dicts" plan
([KOSHA_IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_IMPLEMENTATION_PLAN.md),
now banner-flagged): with the union index, glossary, and scan resolver
consumed instead of rebuilt, Phase 1 is **day-scale glue**. Genuinely new code
is marked **NEW**; everything else is import/port.

> **Engineering contract:
> [ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)**
> (02-07-2026) — locked decisions A1–A4: raw-markup storage + ported
> csl-websanlexicon transforms; `dict.L.senseN@version` sense IDs; local-first
> (M.G. deploys manually, agents never SSH); execution queued to a Sonnet 5 /
> Opus 4.8 session. It carries the SQLite schema, the API v1 contract, and the
> golden-test requirements — implement against it, record deviations there
> first. D2 additionally delivers the per-dict sense-segmentation rule and the
> `render()` port with golden tests; D4 implements API v1 as specified
> (including `/api/v1/sense/{id}` with the versioned cite payload).

Nothing below is started. No ✅ appears in this file until the referenced code
exists and its check passes — that is the lesson of the 02-07-2026 audit.

## D1 — data inventory + spine

- Vendor the lemma spine: load
  [union_headwords.tsv](https://github.com/gasyoun/SanskritLexicography/blob/master/HeadwordLists/union/union_headwords.tsv)
  (323,426 rows) into `lemmas` (SQLite). Keep `slp1` as primary key; carry
  `iast`, `dicts`, `gender`.
- Locate per-dict sources for MW / PWG / AP90 (local csl-orig siblings or CDSL
  downloads). Record source commit/version per dict for provenance.
- **Check:** `SELECT COUNT(*) FROM lemmas` = 323,426; per-dict source paths +
  versions recorded in `data/SOURCES.md`.

## D2 — entry load + per-dict `<pc>` parser (NEW, small)

- **Primary source (max Salt reuse, 02-07-2026): the
  [csl-sqlite releases](https://github.com/sanskrit-lexicon/csl-sqlite/releases)**
  (`{dict}.zip` — e.g. `mw.sqlite`, 286,560 records; the same data layer
  csl-apidev's Salt implementation reads). Import into
  `entries(dict, L, slp1_key, pc_raw, body)`; parse csl-orig text directly
  only if a target dict has no csl-sqlite release. Record the release tag +
  underlying csl-orig commit in `sources`.
- **NEW:** per-dict `<pc>` dispatcher — MW `page,column` (single volume);
  PWG `vol-page` (hyphen, 7 vols); AP90 `page-col-letter`. No comma-split
  shortcut; measure actual `<pc>` coverage per dict instead of assuming 100 %.
- **Check:** spot-verify 10 known records incl. MW `<L>142512<pc>720,1<k1>banD`
  and L523 = `akza` at `3,2`; coverage numbers written into `data/SOURCES.md`.

## D3 — morphology + scan links (imports)

- Import the form→lemma layer from
  [RussianTranslation/glossary/](https://github.com/gasyoun/SanskritLexicography/tree/master/RussianTranslation/glossary)
  into `forms(form_slp1, lemma_slp1, source)`. No live Heritage calls.
- Port/wrap
  [ls_resolver.py](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/ls_resolver.py)
  for entry→scan-URL resolution (Cologne `serveimg`/`servepdf`).
- **Check:** `bhagavān → bhagavant-` resolves; 10 sampled scan URLs return
  HTTP 200.

## D4 — API endpoints + tests

- Implement `/api/lemma/{key}`, `/api/lemma/form/{form}`, `/api/search`,
  `/health` per the corrected contract in
  [KOSHA_DEPLOYMENT.md Appendix A](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_DEPLOYMENT.md)
  (SLP1 keys are SLP1 — `banD`, not `bandh`; MW responses carry page+column,
  never "volume").
- Transliteration via sanskrit-util; `encoding=` query param.
- **Salt interchange (required, per ARCHITECTURE §C-SALT):** per-dict entry
  objects inside `/api/v1` responses use the Salt-profile shape (`csl.{…}`
  block + `lemma-…-L{lnum}` ids) extended with namespaced `kosha.*` fields;
  plus the **Salt facade REST faces** `GET /dicts/{id}/restful/entries` and
  `/restful/ids` served from `kosha.db`.
- **Check:** pytest suite over the four kosha endpoints + the two Salt faces,
  green locally; Salt-face envelopes parity-checked against csl-apidev's
  run-verified outputs for `agni`, `indra`, `ka` (incl. `-L{lnum}` homonym
  ids).

## D5 — measure, then decide the open items

- Measure DB size, cold/warm lookup latency, top-N cache sizes vs the GitHub
  100 MB file limit.
- With real numbers, settle: latency SLO, update cadence (leaning nightly),
  static-cache N. Record in
  [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md).
- **Check:** numbers + decisions committed; Phase 2 (UI + Pages tier) can start
  against fixed targets.
- ✅ **Done 03-07-2026** (Opus 4.8 `claude-opus-4-8`): numbers in
  [D5_MEASUREMENTS.md](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md),
  decisions in
  [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md)
  (SLO / cadence / cache-N). D5 additionally: fixed a 240 ms→0.3 ms lemma-lookup
  index bug, exercised the R3 csl-orig fallback (100 % ap90 inventory parity),
  and resolved `sources.csl_orig_commit` provenance by cross-dating.

## Model-tier note

Planning/adjudication for this repo ran on Fable 5 (`claude-fable-5`,
02-07-2026). D1–D4 are execution-tier work (Sonnet 5 `claude-sonnet-5` or
Opus 4.8 `claude-opus-4-8` sessions); D5's decision step returns to a
judgment tier.

---

_Dr. Mārcis Gasūns_
