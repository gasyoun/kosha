# Implementation plan — Gasuns Sanskrit Dictionary

_Created: 02-07-2026 · Last updated: 03-07-2026_

Full-project plan from first line of code to the citable v1.0. Supersedes the
banner-flagged pre-triage plan in SanskritLexicography. Ground rules inherited
from [ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)
(A1–A4) and [POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md);
per-day detail for Phase 1 lives in
[PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md).
Discipline: **no phase is ✅ until its exit check passes** (the 02-07-2026
audit lesson); every session records its model tier + version.

**Licenses (locked 02-07-2026):** code = CC BY-NC 4.0
([LICENSE.md](https://github.com/gasyoun/kosha/blob/main/LICENSE.md)); data
releases = CC BY-SA 4.0 inherited from Cologne
([LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md) —
NB: Cologne is BY-**SA**, not NC; our non-commercial restriction attaches to
the code only).

## Phase map

| Phase | Deliverable | Executor | Agent effort | Gates (blockers) |
|---|---|---|---|---|
| **P1** Data + API | `kosha.db` (MW+PWG+AP90) + API v1 local, tests green | Sonnet 5 / Opus 4.8 | ~5 days | none — **start now** |
| **P2** Public alpha | Static tier on Pages + PWA shell; API on samskrtam.ru | agent + **MG deploy** | ~3 days | P1; MG enables Pages + runs deploy |
| **P3** Evidence layer | DCS frequency badges, attestation sidebar, corpus example per sense | Sonnet/Opus | ~3 days | P1 (P2 not required) |
| **P4** Forms & grammar | Paste-anything segmentation; vidyut paradigm tables; Zaliznyak token | Sonnet/Opus + judgment QA | ~4–5 days | P1; segmentation quality gate |
| **P5** Advanced UI | The own UI at samskrtam.ru/kosha (MG override, API-first) | design: judgment tier · build: Sonnet/Opus | ~1–2 wks elapsed | P2–P4; MG design sign-off |
| **P6** Trilingual RU | Russian gloss layer beside DE/EN | Sonnet/Opus | ~2–3 days | **G5 human review** of pwg_ru cards; **Kochergina rights (MG)** |
| **P7** v1.0 citable | DOI'd data release, dumps, Cite everywhere, announcement | agent + MG | ~2 days | P2+P3; MG: Zenodo DOI |

Sequencing: P1 → (P2 ∥ P3) → P4 → P5 → P7; P6 slots in whenever its two gates
clear. Elapsed optimistic total to v1.0 ≈ 4–6 weeks, dominated by MG-side
gates (deploys, G5 review, design sign-off), not agent coding time.

## P1 — Data + API (specced; start immediately)

Exactly [PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md)
D1–D5 against the ARCHITECTURE contract. **Exit:** pytest green incl. golden
renders; `<pc>` coverage measured per dict in `sources`; D5 numbers recorded
and SLO + cadence decided in
[KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md).

## P2 — Public alpha (the first URL)

- `scripts/build_static_cache.py`: top-N lemma cards (rendered HTML + freq
  band placeholder) into `docs/js/data/`, N sized to Pages limits from D5
  measurements.
- Minimal lookup page (`docs/index.html` + vanilla JS): autocomplete box,
  cache-first / API-fallback (pattern in
  [KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_DEPLOYMENT.md)),
  service worker for offline (the PWA is this tier plus a manifest).
- Server-rendered permalink pages for SEO/archivability come with P5; the
  alpha is JS-first and honest about it.
- **MG actions:** enable Pages on this repo; run the samskrtam.ru deploy
  (systemd + nginx per KOSHA_DEPLOYMENT.md).
- **Exit:** both URLs live; lookup of `banD`/`bhagavān`/`kṛṣṇa` (typed as
  `krsna`) works on a phone; offline repeat-lookup works.

## P3 — Evidence layer (the flagship differentiator)

**Status: ✅ done 03-07-2026 (Sonnet 5 `claude-sonnet-5`).** See
[`.ai_state.md`](https://github.com/gasyoun/kosha/blob/main/.ai_state.md)
Completed and [`CHANGELOG.md`](https://github.com/gasyoun/kosha/blob/main/CHANGELOG.md).
Deviation from the bullets below, recorded honestly: no new `evidence`
table was created (P1's frequency LEFT-JOIN already put `count_all`,
`rank_all`, `periods`, `coverage_pct`, `core_rank` on `lemmas` before P3
started, so band/example columns were added there instead — see
[`scripts/build_evidence.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_evidence.py)
module docstring); examples are per-**lemma**, not per-sense (`corpus_lexicon.jsonl`
has no sense-level tagging — same file, "Scope note"); genre sketch is
honestly reported as not derivable from the current DCS extraction (only a
chronological period vector is stored) rather than fabricated.

- Import DCS-derived bands already computed in-house (`dcs_freq` 1–5, hapax,
  core-80, genre/era profile — from the pwg_ru pipeline) keyed by lemma;
  schema: new `evidence` table, additive.
- Per-entry sidebar block: attestation count, first-era, genre sketch —
  the Logeion-sidebar pattern with DCS data.
- One corpus example per sense where available: DCS citation (Sa) +
  corpus_lexicon aligned RU where it exists; labeled with source.
- Result ranking: frequency-weighted ordering in `/api/v1/search`.
- **Exit:** `dharma` shows band + counts + ≥1 attested example; ranking
  measurably changes for a 20-query sample; provenance label on every badge.

## P4 — Forms & grammar (the student unlock)

> Fully specified 03-07-2026 in
> [ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md)
> (MG rulings D1–D6: hybrid venue, full scope, Cologne tables first with a
> vidyut evolution path, probe-first upstream cadence). The bullets below
> stay authoritative for the exit checks.

- **Paste-anything:** query pipeline = forms table → (miss) → segmentation.
  Evaluate vidyut-cheda vs Heritage (UoHyd mirror — Inria host is bot-walled,
  verified 02-07-2026) on a 200-form gold sample; wire the winner; show
  pick-a-split UI only when ambiguous.
- **Paradigms:** vidyut-prakriya-generated declension/conjugation table per
  entry, on demand; compact Zaliznyak-style token (`m·8n*`) displayed at the
  headword — import from the WhitneyRoots/reverse-index work (98,639
  headwords already indexed).
- **Quality gate (judgment tier):** segmentation ≥90 % top-1 on the gold
  sample or the feature ships behind a "beta" flag; wrong-but-confident
  splits are worse than none.
- **Exit:** `bhagavān` (form), `rāmeṇa` (inflected), `dharmakṣetre` (sandhied
  compound, split offered) all resolve; paradigm table renders for a-stems,
  ī-stems, and one verb class; gold-sample report committed.

## P5 — The advanced UI (MG's own way)

- **Design session first (judgment tier + MG):** one wireframe pass locking
  progressive disclosure (plain gloss + badge + token → full apparatus →
  scan), multi-dict presentation (tabs vs stacked — test both against the
  meyer one-page and Wisdom-Library stacked patterns), `<abbr>` tooltips,
  `#`-browse mode, `sandhi:`/`root:` operators.
- Build as **server-rendered permalink pages** (`/w/{slp1}`) + progressive JS
  — the crawlability lesson from the 02-07 survey (only Wisdom Library was
  readable to a fetcher).
- Student take-aways: CSV/Anki export of session lookups; first two
  "reading packs" (Gītā 1, Nala 1) generated from DCS lemmatization.
- **Exit:** MG sign-off on live staging; Lighthouse mobile ≥90; a Gītā-verse
  walkthrough (paste verse → read every word) succeeds end-to-end.

## P6 — Trilingual RU layer (gated)

- **Gate 1 (human, MG):** G5 review flips pwg_ru cards `ai_translated` →
  `approved`; only approved cards are exported. **Gate 2 (rights, MG):**
  Kochergina 1987 is in copyright — decide include/exclude; Kossovich 1854 is
  public domain and safe.
- Implementation once gated: RU gloss column in the multi-dict view; RU
  corpus examples from corpus_lexicon; UI strings i18n (EN/RU).
- **Exit:** a lemma with approved RU cards shows DE/EN/RU side by side, each
  gloss labeled with source + review status.

## P7 — v1.0: the citable resource

- First versioned data release per ARCHITECTURE (DB + dumps as GitHub release
  assets, CC BY-SA 4.0 attribution block from LICENSE-DATA.md); **MG mints
  the Zenodo DOI**; `/api/v1/sense/{id}` cite payloads carry it.
- CITATION.cff, API docs page, announcement (csl-newsletter + INDOLOGY);
  positioning docs updated from aspiration to shipped-state.
- **Salt GraphQL face (required here):** completes the Salt facade whose REST
  faces shipped in P1/D4 — `POST /dicts/{id}/graphql` per the csl-standards
  [SALT_API_PROFILE](https://github.com/sanskrit-lexicon/csl-standards/blob/main/docs/SALT_API_PROFILE.md)
  (port reference: `csl-apidev/api1/salt_graphql*.php`). With it, kosha is a
  complete drop-in C-SALT provider and the second independent implementation
  of the org standard; kosha's working sense IDs are offered upstream for
  Salt's TODO `sense` face. See ARCHITECTURE §"Relation to the C-SALT / Salt
  API" for the interchange rules (Salt entry object inside /api/v1, csl-sqlite
  as data source, L-number addressing).
- **Exit:** a sense citation with DOI + version resolves in a fresh browser;
  the release is independently downloadable and rebuildable.

## Cross-cutting (every phase)

- **CI from P1:** GitHub Actions — pytest + golden renders + ruff + markdown
  link check. Red main = stop.
- **Provenance:** every build stamps `data_version` + per-dict csl-orig
  commits; every session logs model tier + exact version.
- **No silent caps:** any sampling/top-N/coverage limit is logged and
  documented, never implied as "everything".
- **Upstream loyalty:** corrections discovered in dictionary text go through
  the csl-orig correction queue (never patched locally); renderer fixes go
  upstream to csl-websanlexicon when they apply there too.

## MG's personal action list (the real critical path)

1. ~~License decision~~ ✅ 02-07-2026 (code BY-NC, data BY-SA inherited).
2. After P1: enable GitHub Pages; run the first samskrtam.ru deploy.
3. P4: 30-minute review of the segmentation gold-sample verdict.
4. P5: design sign-off session.
5. P6 gates: G5 review of pwg_ru cards; Kochergina rights decision.
6. P7: Zenodo account + DOI mint; announcement send.

---

_Dr. Mārcis Gasūns_
