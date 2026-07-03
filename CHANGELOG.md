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
