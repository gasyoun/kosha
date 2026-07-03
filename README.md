# Gasuns Sanskrit Dictionary

_Created: 02-07-2026 · Last updated: 02-07-2026_

> **Status: pre-alpha — nothing runs yet.** This repository currently contains
> a locked, gated engineering plan (released as
> [v0.2.0](https://github.com/gasyoun/kosha/releases/tag/v0.2.0)) and an honest
> FastAPI stub. No lookup works today. Coding starts with
> [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md);
> no file in this repo claims to be "ready" unless its check actually runs.

**A translator-first Sanskrit dictionary: every major dictionary on one page,
every sense anchored to the scanned print, every word findable as it actually
appears in a text — open, API-first, versioned, citable.**

*kosha* is the working codename and deployment path (`samskrtam.ru/kosha`);
the public brand is **Gasuns Sanskrit Dictionary** — which also sidesteps the
name collision with Ambuda's `vidyut-kosha`. Naming and identity review:
[POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md) ·
one-page distillation:
[POSITIONING_SUMMARY.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING_SUMMARY.md).

## What it will do

Fast lookup over the [Cologne Digital Sanskrit
Dictionaries](https://www.sanskrit-lexicon.uni-koeln.de/) — Monier-Williams
(MW), the large Petersburg lexicon (PWG), and Apte 1890 (AP90) first, with the
rest of the collection to follow. Primary audience: **translators**, then
learners, then scholars.

- **Multi-dictionary view** — one headword, all dictionaries collapsed onto
  one page.
- **Scan-anchored print truth** — per-entry links to the scanned page of the
  printed edition, so the digital text is always one click from its source.
- **Meet the form, not the lemma** — diacritic-free typing (`krsna` finds
  *kṛṣṇa*), inflected-form lookup, and eventually paste-anything: a sandhied,
  compounded verse segmented at query time.
- **Evidence-graded entries** — frequency bands and attestation from the
  [Digital Corpus of Sanskrit](http://www.sanskrit-linguistics.org/dcs/):
  what a second-year should memorise vs look up and forget.
- **Generated paradigms + a compact grammar token** modelled on Zaliznyak's
  index from the Russian lexicographic tradition.
- **Trilingual glosses** — English (MW) · German (PWG) · Russian (pwg_ru
  translation layer) side by side; unique worldwide.
- **Offline PWA** — the static cache tier makes offline lookup nearly free.
- **Citable, not just browsable** — persistent sense-level IDs
  (`dict.L.senseN@version`), versioned data releases mirrored on Zenodo with
  DOIs; a citation from 2026 still resolves in 2036.

The formula, distilled from a twelve-platform live survey
([COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md),
02-07-2026): **meyer's collapse + Heritage's morphology + DCS's evidence +
Logeion's sidebar + Cologne's corrections loop + the trilingual DE/EN/RU
layer.** No existing project occupies that intersection.

## Roadmap

Full plan with exit checks:
[IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md) ·
scenarios it must serve:
[USE_CASES.md](https://github.com/gasyoun/kosha/blob/main/USE_CASES.md) (UC1–UC13).

| Phase | Deliverable | State |
|---|---|---|
| **P1** Data + API | `kosha.db` (MW+PWG+AP90) + API v1 running locally, tests green | **next — specced in [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md)** |
| **P2** Public alpha | first live URLs: static lookup on GitHub Pages + API on samskrtam.ru | gated on P1 |
| **P3** Evidence layer | DCS frequency badges, corpus example per sense | gated on P1 |
| **P4** Forms & grammar | paste-anything segmentation, paradigm tables, grammar token | gated on P1 |
| **P5** Advanced UI | the project's own UI at samskrtam.ru/kosha | gated on P2–P4 |
| **P6** Trilingual RU | Russian gloss layer beside DE/EN | gated on human review + rights |
| **P7** v1.0 citable | DOI'd data release, dumps, "Cite" everywhere | gated on P2+P3 |

Optimistic elapsed total to v1.0 ≈ 4–6 weeks, dominated by human-side gates
(deploys, design sign-off, translation review), not coding time.

## Licenses

| What | License | Why |
|---|---|---|
| Code | CC BY-NC 4.0 — [LICENSE.md](https://github.com/gasyoun/kosha/blob/main/LICENSE.md) | attribution required, non-commercial |
| Data releases | CC BY-SA 4.0 — [LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md) | inherited from Cologne's ShareAlike, which does not permit adding a non-commercial restriction to derived data |

## FAQ

### Using it

**Which dictionaries are included?**
MW, PWG, and AP90 first — deliberately, because their page-reference formats
are the three hardest cases, so the pipeline generalises. The lemma spine
(the union headword index, 323,426 rows) already spans the whole Cologne
collection, so further dictionaries are an ingestion task, not a redesign.

**Do I need to type diacritics?**
No. `krsna` finds *kṛṣṇa*. IAST, SLP1, and Devanagari input are all planned,
with auto-detection of the input scheme — the bar set by
sanskritdictionary.com.

**Can I paste a whole sandhied verse?**
That is the P4 flagship: query-time segmentation of sandhied, compounded,
inflected text, turning the dictionary into a reading companion. Until P4,
lookup is by headword and inflected form.

**Will it work offline?**
Yes — from P2 the static cache tier ships as a progressive web app: repeat
lookups work with no connection.

**What about Russian?**
P6 adds a Russian gloss layer beside the German and English, built on the
pwg_ru translation project. It is explicitly gated on human review of the
translated cards and on rights clarification for the Kochergina layer — it
ships when those clear, not before.

**Can I cite an entry in a paper?**
That is a founding requirement, not an afterthought: every sense has a
persistent ID (`dict.L.senseN@version`), data releases are versioned and
mirrored on Zenodo with DOIs from the first citable release, and an old
citation resolves to the exact version it named — in a browser, no tooling.

**Why do entries link to page scans?**
Because the digital text is a transcription and transcriptions drift. Every
entry links to the scanned page of the printed edition, so the print remains
the court of appeal — the same discipline the Cologne project itself follows.

### Compared to what exists

**Why another Sanskrit dictionary site?**
Because the composite doesn't exist. Each ingredient exists somewhere —
multi-dictionary collapse (michaelmeyer.fr), form lookup
(sanskritdictionary.com), morphology (Heritage/Ambuda), corpus evidence (DCS)
— but no site combines them, and none is simultaneously open-source,
API-first, versioned, and citable. The full survey is in
[COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md).

**How is this different from [michaelmeyer.fr/sanskrit](https://michaelmeyer.fr/sanskrit)?**
Meyer's site is the closest thing to "Logeion for Sanskrit" — 41 dictionaries
on one page, per-sense scan links for 19 of them, remarkable speed. It is also
read-only, closed-source, and single-maintainer. This project adds the open
API, morphology, corpus evidence, the Russian layer, and citability — and
treats meyer's collapse as the bar to clear, not a rival to displace (see
[RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md)).

**How is this different from [sanskritdictionary.com](https://www.sanskritdictionary.com/)?**
That site is the feature benchmark: input auto-detection, `sandhi:`/`root:`
operators, per-sense permalinks. But it is closed to programmatic use
(Cloudflare-walled) and unversioned. This project is API-first and open by
construction.

**Is this competing with Cologne / CDSL?**
No — Cologne is the substrate, not a competitor. The work runs on three
tracks: (1) correcting the source texts upstream in
[csl-orig](https://github.com/sanskrit-lexicon/csl-orig), (2) improving the
shared Cologne tooling for everyone, (3) this project — the opinionated
integration layer that doesn't belong in Cologne's conservative frontend.
Corrections found here flow back upstream.

**What about Ambuda / vidyut?**
The strongest modern neighbour, and a dependency rather than a rival: this
project consumes the [vidyut](https://github.com/ambuda-org/vidyut) toolkit
(paradigms, form lookup fallback) and never re-implements it. The public
brand "Gasuns Sanskrit Dictionary" exists partly because `vidyut-kosha`
already owns the *kosha* name in that ecosystem.

### Status & timeline

**Can I use it today?**
No. The repo is planning documents plus a stub. The first usable URL arrives
at P2 (public alpha).

**Why is the repo all Markdown?**
Deliberately. An audit of this project's earlier planning corpus found
fabricated figures (invented latency numbers, wrong attributions), and the
lesson became policy: plan first, write the quality gates before the code
([EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md)),
enumerate the risks
([RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md)), and never
mark anything done without a runnable artifact. The planning layer was
finished and released as
[v0.2.0](https://github.com/gasyoun/kosha/releases/tag/v0.2.0) before the
first real line of application code.

**When will something be usable?**
P1 (data + API, local) is roughly five agent-days of work; the first public
URLs come with P2 immediately after. The optimistic path to a citable v1.0 is
4–6 weeks, and the long poles are human gates, not code.

### Licensing & reuse

**Can I use the data?**
Yes — data releases are CC BY-SA 4.0: use them, including commercially,
with attribution and share-alike. This is inherited from Cologne's own
licensing; a non-commercial restriction legally cannot be attached to data
derived from BY-SA sources.

**Why is the code non-commercial but the data isn't?**
Because the two have different ancestors. The data derives from Cologne
(BY-SA, share-alike is contagious); the code is original work and carries
CC BY-NC 4.0 — free for scholarship and teaching, commercial use by
permission.

**Can I self-host it?**
Yes — the architecture is local-first by contract (everything builds and runs
on one machine; deployment is a copy step). The server reference
(systemd/nginx/cron) is
[KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_DEPLOYMENT.md).

## For contributors & agents

Everything below is the engineering spine. All product and architecture
decisions are **locked — do not re-litigate**; the documents are the contract.

### Build rule: reuse-first

kosha is **glue over existing ecosystem assets**, not a rebuild. Canonical
inputs — consume, never regenerate:

| Concern | Owned by | What we consume |
|---|---|---|
| Lemma spine | [union_headwords.tsv](https://github.com/gasyoun/SanskritLexicography/blob/master/HeadwordLists/union/union_headwords.tsv) | 323,426 rows, `slp1/iast/n_dicts/dicts/gender` |
| Dict entry text | [csl-orig](https://github.com/sanskrit-lexicon/csl-orig) / CDSL downloads | per-dict source, `<L>`/`<k1>`/`<pc>` keyed; **csl-sqlite releases are the primary entry source**, text parse is fallback |
| Existing dict API | [csl-apidev](https://github.com/sanskrit-lexicon/csl-apidev) (C-SALT **Kosh** API, `api1/salt_*.php`) + [csl-websanlexicon](https://github.com/sanskrit-lexicon/csl-websanlexicon) (`getword`/`servepdf`/`serveimg`) | endpoints + patterns; kosha builds *on*, not beside — Salt reuse is **required** (facade REST in D4) |
| Scan links | [ls_resolver.py](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/ls_resolver.py) | Cologne scan URL resolution (port of csl-app `ls_service.dart`) |
| Form → lemma | [RussianTranslation/glossary/](https://github.com/gasyoun/SanskritLexicography/tree/master/RussianTranslation/glossary) | DCS + vidyut.kosha fallback, 86.6 % token coverage — no live Sanskrit Heritage calls |
| Transliteration | sanskrit-util (Py + JS) | IAST ⇄ SLP1 ⇄ Devanagari — no transcoder #63 |
| Corpus evidence | `corpus_lexicon.jsonl` (RussianTranslation/src) | 1.09 M aligned Sa→Ru pairs (Phase 4) |

Per-dict `<pc>` ground truth (02-07-2026 audit — a naive comma-split parser
fails on 2 of 3): MW `720,1` = page,column, single volume · PWG `1-0001` =
volume-page, hyphen, 7 volumes · AP90 `0001-a` = page-column-letter.

### Architecture (decided)

- **API tier**: FastAPI + SQLite (single `kosha.db`) on samskrtam.ru
  (`/kosha/api/…`).
- **Static tier**: precomputed top-N lemma cache on this repo's GitHub Pages,
  cache-first JS with API fallback.
- **A1–A4 contract** ([ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)):
  raw-markup storage + ported transforms · `dict.L.senseN@version` sense IDs ·
  local-first, M.G. deploys · execution by a Sonnet/Opus session.
- Builds never call live third-party services (RISKS R12); Heritage
  integration, when it comes, uses the UoHyd mirror (Inria host is
  bot-walled).
- Repo `vX.Y.Z` tags and `data_version` are **separate tracks**; sense
  citations pin to the latter.

### Ground rules

- **No ✅ without an artifact.** A phase or task is done when its exit check
  runs green, not when its code exists. Gates live in
  [EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md)
  (start at §0, the anti-gaming rules).
- **Model provenance**: every session records the model tier + exact version
  that did the work.
- **Changelog discipline**: SemVer, Keep-a-Changelog; every changelog edit
  promotes `[Unreleased]` to the next version + tag + GitHub release in the
  same pass.
- **Session state** lives in
  [.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md);
  open decisions (update cadence, latency SLO, etymology depth) get settled
  with real measurements at the end of Phase 1, recorded in
  [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md)
  (D5 settled the first three — see
  [D5_MEASUREMENTS.md](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md)).

### Document map

| In this repo | What it holds |
|---|---|
| [ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md) | A1–A4 contract, SQLite DDL, API v1, Salt max-reuse rules |
| [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md) | D1–D5 work order — **the next thing to execute** |
| [IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md) | P1–P7 full plan with exit checks |
| [EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md) | quality gates, anti-gaming rules, T-UC1…T-UC13 acceptance tests |
| [USE_CASES.md](https://github.com/gasyoun/kosha/blob/main/USE_CASES.md) | UC1–UC13 scenarios mapped to phases |
| [RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md) | R1–R12 pre-mortem, citability commitments |
| [RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) | ecosystem diplomacy — Meyer, Cologne, Ambuda, C-SALT |
| [POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md) · [POSITIONING_SUMMARY.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING_SUMMARY.md) | identity, audience, the UI decision |
| [COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md) | 12-platform live survey (02-07-2026) with feature matrix |
| [D5_MEASUREMENTS.md](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md) · [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md) | D5 measurement report + the SLO/cadence/cache-N decisions it settled |
| [CHANGELOG.md](https://github.com/gasyoun/kosha/blob/main/CHANGELOG.md) | SemVer history |

| In [SanskritLexicography](https://github.com/gasyoun/SanskritLexicography) | What it holds |
|---|---|
| [KOSHA_FOLDER_SETUP.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_FOLDER_SETUP.md) | post-audit truth doc, meta-decisions M1–M4 |
| [KOSHA_REFERENCE_ANALYSIS.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_REFERENCE_ANALYSIS.md) | feature-by-feature reference-site analysis |
| [KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_DEPLOYMENT.md) | samskrtam.ru deployment reference (systemd/nginx/cron) |

> The application deliberately lives outside SanskritLexicography (a
> data/research workspace whose charter forbids source code — meta-decision
> M2). This repo's GitHub Pages will host the static cache tier (M4). Treat
> the older planning docs' timeline/latency/cadence figures as historical;
> each carries a triage banner saying so — trust only the dated live survey.

### Lineage

Böhtlingk–Roth → Monier-Williams → Cologne digitization (1994–) → correction
infrastructure (csl-orig) → API-ification (Kosh/C-SALT) → **integration =
this project**. It writes no dictionary content and corrects nothing at
source; it adds the join + access layer — the public face of a decade of
private plumbing (union headwords, pwg_ru, frequency bands, the Zaliznyak
index, the scan resolver).

---

_Dr. Mārcis Gasūns_
