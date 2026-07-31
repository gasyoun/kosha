# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

`kosha` (public brand: **Gasuns Sanskrit Dictionary**) is a translator-first
Sanskrit dictionary web service: fast lookup over the Cologne Digital Sanskrit
Dictionaries (MW, PWG, AP90 first), collapsing every dictionary's entry for a
headword onto one page, scan-anchored to the printed source, with citable
sense-level IDs. FastAPI backend + a static docs/cache site. **Status:
pre-alpha** — corrected 30-07-2026 (H1943; this line was stale since
24-07-2026 and understated real progress). The lookup API + UI run locally
against real MW/PWG/AP90 data (Phase 1 complete), the static-cache/data-hub
tier is live on GitHub Pages, and the current release is
[v0.96.0](https://github.com/gasyoun/kosha/releases/tag/v0.96.0) — but the
public `samskrtam.ru` dictionary URL is not yet deployed (MG deploy-gated),
and W0 (see [`docs/ROADMAP.md`](docs/ROADMAP.md)) is a hard feature freeze
until the reproducible-substrate and contract/trust-boundary work lands. See
[README.md](README.md)'s status banner and
[`.ai_state.md`](.ai_state.md) for the exact current state; don't assume any
endpoint behavior beyond what the live tests in `tests/` verify.

## Common commands

> **Operator's view of the whole chain** — stage order, per-stage verification,
> failure symptoms, deploy classes, release rituals:
> [docs/PIPELINE_OPERATOR_RUNBOOK.md](docs/PIPELINE_OPERATOR_RUNBOOK.md) (H501).

```bash
pip install -r requirements.lock              # the pinned set CI installs (W0B/H1944)
pip install -e .                              # installable package (src/kosha/)
uvicorn app.main:app --reload --port 8000     # run the FastAPI dev server (needs .env, see below)
pytest                                        # full test suite — needs the local data/db/kosha.db
pytest -m fixture                             # the subset CI runs: no big DB, fixture pack only
python scripts/build_db.py                    # build data/db/kosha.db — ALL ten stages, in order
python scripts/build_db.py --plan             # the resolved plan + what each stage must prove
python scripts/build_db.py --verify           # check the artifact against its build lock
python scripts/build_db.py --sources tests/fixtures/pack/sources.json --db /tmp/fx.db  # from-zero fixture build
python scripts/build_crosswalk.py             # build the union headword crosswalk
python scripts/build_entries.py               # build rendered entries
python scripts/build_forms.py                 # build inflected-form index
python scripts/build_static_cache.py          # generate the P2 static-cache JSON (Pages deploy input)
python scripts/build_word_pages.py --coverage 0.95 --force  # P5 D4 static head (H1590); gitignored docs/w/ + docs/browse/
python scripts/build_docs_site.py             # build the docs-site (ZettelkastenWiki Wave-3 pilot)
python scripts/gen_golden.py                  # regenerate golden render fixtures for test_render_golden.py
python scripts/measure_d5.py                  # D5 latency/perf measurement run
```

Copy `.env.example` → `.env` before running the API. Settings are typed and
validated in [`src/kosha/settings.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/settings.py) (W0B/H1944):
`KOSHA_CORE_DB`, `KOSHA_ARCHIVE_DIR`, `KOSHA_PUBLIC_BASE`,
`KOSHA_ENABLE_HISTORY` (off by default), plus `LOG_LEVEL`, `CORS_ORIGINS` and
`COLOGNE_SCAN_BASE` (the csl-websanlexicon `serveimg`/`servepdf` host used for
scan-anchored citations). `DATABASE_PATH` survives as a **deprecated alias** for
`KOSHA_CORE_DB` — it used to be advertised while nothing read it; it now works,
warns, and setting both to different paths is a hard error.

## Key directories / files

| Path | Purpose |
|---|---|
| `src/kosha/` | The installable package (W0B/H1944): `settings.py` (typed settings + the deprecated `DATABASE_PATH` alias) and `build/` — `stages.py` (the ONE stage registry: dependencies, source feeds, postconditions), `runner.py`, `lock.py`, `cli.py`. `app/` and `scripts/` stay as compatibility entry points and import from here |
| `app/` | FastAPI service: `main.py` (`build_app()` + routes; history/auth/stats are OFF unless `KOSHA_ENABLE_HISTORY`), `db.py`, `render.py` (entry rendering), `salt.py` (Salt facade REST — see Conventions), `scan_resolver.py`, `segment.py`, `transliterate.py`, `versions.py`, `cite.py` (citation-ID minting) |
| `tests/fixtures/pack/` | Committed slice of the real source feeds (748 KB, derived by `scripts/build_fixture_pack.py`) that drives a full from-zero build of every stage without the sibling checkouts — what CI builds against |
| `scripts/` | One script per data-build stage (crosswalk → entries → forms → db → static cache → docs site); `measure_d5.py` and `archive_senses.py` are maintenance/measurement, not part of the main build chain |
| `data/` | Data assets, incl. `data/frequency/` (DCS frequency sidecar joined against `union_headwords`, see `.ai_state.md`) — `data/raw*/`, `data/releases/`, and D5 measurement outputs are gitignored/regenerable |
| `tests/` | `test_api.py`, `test_citability.py`, `test_render_golden.py` (golden fixtures in `tests/golden/`), `test_static_cache.py`, `test_docs_site.py` |
| `docs/`, `docs-site/`, `wiki/` | Static site output / docs-site pilot / wiki content |
| `ARCHITECTURE.md` | A1–A4 design, SQLite DDL, API v1 contract, Salt max-reuse rules |
| `IMPLEMENTATION_PLAN.md`, `PHASE1_PLAN.md` | The gated P1–P7 roadmap and exit checks — **the actual source of truth for what's buildable next**, not this file |
| `EVAL_PLAN.md` | Anti-gaming rules (G-SEG/G-RENDER/G-SALT/G-PC/G-SCAN/G-LAT gates) + UC1–UC13 test scenarios |
| `RISKS.md` | R1–R12 pre-mortem, incl. the citability commitments (citation URLs must never depend on the `samskrtam.ru` server host) |
| `KOSHA_DECISIONS_NEEDED.md` | Open @DECIDE items — check before assuming a design choice is settled |

**CI (updated 31-07-2026, H1944):** four workflows —
[`python-ci.yml`](https://github.com/gasyoun/kosha/blob/main/.github/workflows/python-ci.yml)
(job `pytest (fixture pack)`: installs `requirements.lock`, resolves the build
plan, runs `pytest -m fixture` including a full from-zero build of all ten
stages),
[`ui-ci.yml`](https://github.com/gasyoun/kosha/blob/main/.github/workflows/ui-ci.yml)
(job `vitest + vite build`), `changelog-lint.yml` (duplicate-entry guard) and
`dependabot-auto-merge.yml` — the last now waits for both test jobs to report
SUCCESS on the PR head before it approves or enables auto-merge, so a
dependency bump cannot land on an unbuilt PR. **Those two job names are the
contexts to require in branch protection** (a human still has to set that;
`tests/test_packaging.py` pins the names to the gate so a rename cannot
silently orphan them).

## Conventions

- **"Maximum-reuse rules"**: this repo is meant to reuse existing Sanskrit
  Lexicon infrastructure rather than reimplement it — the crosswalk, scan
  resolver, and Salt facade REST design in `app/salt.py` exist specifically to
  avoid duplicating work already done elsewhere (`sanskrit-util`,
  `csl-websanlexicon` scan-serving, the union headword index). Check
  `../SHARED_CODE.md` and `../PROJECT_INTERLINKS.md` before adding a new
  transcoder/normalizer/crosswalk builder here.
- **Citation durability (RISKS.md R1/R5):** `PUBLIC_BASE` (citation URL host)
  is deliberately never the `samskrtam.ru` deployment host — citations must
  resolve independent of where the live server happens to run. Don't hardcode
  `samskrtam.ru` into any citation-minting path.
- **Licensing is two-tier, don't conflate them:** code is CC BY-NC 4.0
  (`LICENSE.md`, non-commercial); data releases are CC BY-SA 4.0
  (`LICENSE-DATA.md`, inherited from Cologne's ShareAlike — which does **not**
  permit adding a non-commercial restriction on top).
- **Data build order matters**, and since W0B (H1944) the build enforces it
  rather than trusting you: stage dependencies, source-feed digests and
  per-stage postconditions live in
  [`src/kosha/build/stages.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/build/stages.py),
  and `python scripts/build_db.py --stage X` **refuses** to run on prerequisites
  that never ran or whose feeds have changed since (`--force` to override).
  Running a later stage against a stale earlier one used to produce silently
  wrong output; it now produces a named error. The build lock beside the
  database (`kosha.build-lock.json`) is the record of what actually ran.
- **P5 static head (D4 / H1590):** after cards exist, regenerate word pages with
  `python scripts/build_word_pages.py --coverage 0.95` (or `--head N` after
  re-measure). N is measured at build time from `lemma_frequency.tsv` — never
  hardcode 11,148 without re-measuring. Output `docs/w/` + `docs/browse/` is
  **gitignored** (like cards); MG deploys out-of-band. Exit packet / live-check
  residual:
  [docs/P5_WORD_PAGE_EXIT_PACKET.md](docs/P5_WORD_PAGE_EXIT_PACKET.md). Changing
  the head selector or page template ⇒ re-run head build + refresh the budget
  log row in `docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md` §6 in the same PR.
- Windows encoding convention (`sys.stdout.reconfigure(encoding='utf-8')`,
  `sys.stderr.reconfigure(...)`) is already applied in `app/main.py` — follow
  it in any new script per the org-wide `../CLAUDE.md` convention.

## What not to touch

- `docs/js/data/lemmas.json`, `docs/js/data/attested_keys.json`, `docs/cards/`
  — generated by `scripts/build_static_cache.py`, deployed to Pages
  out-of-band by MG; never commit these in-repo (see `.gitignore`).
- `*.db` / `*.sqlite` (e.g. `unified_dict.db`) — regenerated by
  `scripts/build_db.py`, never committed.
- `data/raw/`, `data/raw_sqlite/`, `data/releases/` — source/release inputs,
  gitignored, regenerable or fetched separately.
- `data/d5_run*.log`, `data/d5_profile.log`, `data/d5_measurements.json` —
  machine-specific measurement outputs from `scripts/measure_d5.py`.

## Operational hazard notes

Destructive-risk facts for this repo (do-not-rerun scripts, decoys, traps) are
registered centrally in an org-private hub
([Uprava DANGER_FACTS.md](https://github.com/gasyoun/Uprava/blob/main/DANGER_FACTS.md),
org members only); the public-safe subset is mirrored in the generated block of
[AGENTS.md](https://github.com/gasyoun/kosha/blob/main/AGENTS.md). Check them
before running anything that writes.
