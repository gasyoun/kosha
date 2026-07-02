# kosha — translator-first Sanskrit dictionary lookup

_Created: 02-07-2026 · Last updated: 02-07-2026_

**Product name: Gasuns Sanskrit Dictionary** (M.G., 02-07-2026); *kosha* is
the working codename and deployment path (`samskrtam.ru/kosha`). The public
brand also sidesteps the `vidyut-kosha` name collision. Positioning review:
[POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md) ·
distillation:
[POSITIONING_SUMMARY.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING_SUMMARY.md).

Fast lookup over the Cologne Digital Sanskrit Dictionaries (MW + PWG + AP90
first), with inflected-form search, multi-dictionary view, and per-entry links
to the scanned print pages. Primary audience: **translators**, then learners,
then scholars — with **its own advanced UI** at samskrtam.ru (decision
recorded in POSITIONING.md §2: API-first, the UI is a client of the same
public API).

## Reference sites — the original bar

The project was scoped against two existing Sanskrit dictionary sites,
analysed feature-by-feature in
[KOSHA_REFERENCE_ANALYSIS.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_REFERENCE_ANALYSIS.md):

- **[michaelmeyer.fr/sanskrit](https://michaelmeyer.fr/sanskrit)** — far more
  than a speed benchmark (02-07-2026 live survey): **41 dictionaries on one
  page per headword, per-sense scan links for 19 of them**, phoneme-wildcard +
  fuzzy search, no-framework server speed. The closest existing "Logeion for
  Sanskrit" — read-only, closed-source, single-maintainer.
- **[sanskritdictionary.com](https://www.sanskritdictionary.com/)** — the
  **feature benchmark**: input auto-detection across 5 schemes, `sandhi:` /
  `root:` search operators, per-sense permalinks (currently Cloudflare-walled
  to programmatic use).

Full twelve-platform survey with feature matrix:
[COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md).
The revised formula: **meyer's collapse + Heritage's morphology + DCS's
evidence + Logeion's sidebar + Cologne's corrections loop + the trilingual
DE/EN/RU layer — open, API-first, versioned, citable.** (Caveat from the
02-07-2026 audit stands: the pre-triage analysis doc's latency numbers and
author attributions were unsupported; the live survey supersedes them.)

**Status: pre-code.** This repo was created 02-07-2026 after the planning
corpus was audited and four meta-decisions locked
([SanskritLexicography v0.0.34](https://github.com/gasyoun/SanskritLexicography/releases/tag/v0.0.34)).
Nothing is built yet; [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md)
is the work order. No file in this repo claims to be "ready" unless it runs.

## Why this repo

The application deliberately lives outside
[SanskritLexicography](https://github.com/gasyoun/SanskritLexicography) (a
data/research workspace whose charter forbids source code) — meta-decision M2.
Its GitHub Pages will host kosha's static cache tier (M4); SanskritLexicography's
own Pages stays with the PWG article site.

## Build rule: reuse-first (M3)

kosha is **glue over existing ecosystem assets**, not a rebuild. Canonical
inputs — consume, never regenerate:

| Concern | Owned by | What we consume |
|---|---|---|
| Lemma spine | [union_headwords.tsv](https://github.com/gasyoun/SanskritLexicography/blob/master/HeadwordLists/union/union_headwords.tsv) | 323,426 rows, `slp1/iast/n_dicts/dicts/gender` |
| Dict entry text | [csl-orig](https://github.com/sanskrit-lexicon/csl-orig) / CDSL downloads | per-dict source, `<L>`/`<k1>`/`<pc>` keyed |
| Existing dict API | [csl-apidev](https://github.com/sanskrit-lexicon/csl-apidev) (C-SALT **Kosh** API, `api1/salt_*.php`) + [csl-websanlexicon](https://github.com/sanskrit-lexicon/csl-websanlexicon) (`getword`/`servepdf`/`serveimg`) | endpoints + patterns; kosha builds *on*, not beside |
| Scan links | [ls_resolver.py](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/ls_resolver.py) | Cologne scan URL resolution (port of csl-app `ls_service.dart`) |
| Form → lemma | [RussianTranslation/glossary/](https://github.com/gasyoun/SanskritLexicography/tree/master/RussianTranslation/glossary) | DCS + vidyut.kosha fallback, 86.6 % token coverage — no live Sanskrit Heritage calls |
| Transliteration | sanskrit-util (Py + JS) | IAST ⇄ SLP1 ⇄ Devanagari — no transcoder #63 |
| Corpus evidence | `corpus_lexicon.jsonl` (RussianTranslation/src) | 1.09 M aligned Sa→Ru pairs (Phase 4) |

Per-dict `<pc>` ground truth (02-07-2026 audit — a comma-split parser fails on
2 of 3): MW `720,1` = page,column, single volume · PWG `1-0001` = volume-page,
hyphen, 7 volumes · AP90 `0001-a` = page-column-letter.

## Architecture (decided)

- **API tier**: FastAPI + SQLite on samskrtam.ru (`/kosha/api/…`).
- **Static tier**: precomputed top-N lemma cache on this repo's GitHub Pages,
  cache-first JS with API fallback.
- Deployment reference (systemd/nginx/cron, defects already fixed):
  [KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_DEPLOYMENT.md).

**Open decisions** (settle with real measurements at the end of Phase 1):
update cadence (leaning nightly), latency SLO, etymology depth (links-first),
code license (data outputs are headed for CC BY 4.0; code license TBD).

## Strategy docs

The full planning corpus lives in SanskritLexicography — entry point
[KOSHA_FOLDER_SETUP.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_FOLDER_SETUP.md)
(the post-audit truth doc), decisions in
[KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_DECISIONS_NEEDED.md).
Treat the older docs' timelines/latency/cadence figures as historical; each
carries a triage banner saying so.

---

_Dr. Mārcis Gasūns_
