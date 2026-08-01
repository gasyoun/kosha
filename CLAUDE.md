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
[v0.97.0](https://github.com/gasyoun/kosha/releases/tag/v0.97.0) — but the
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
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000     # run the FastAPI dev server (needs .env, see below)
pytest                                        # full test suite (tests/test_api.py, test_citability.py, test_render_golden.py, test_static_cache.py, test_docs_site.py)
python scripts/build_db.py                    # build unified_dict.db from source dictionaries
python scripts/build_crosswalk.py             # build the union headword crosswalk
python scripts/build_entries.py               # build rendered entries
python scripts/build_forms.py                 # build inflected-form index
python scripts/build_static_cache.py          # generate the P2 static-cache JSON (Pages deploy input)
python scripts/build_word_pages.py --coverage 0.95 --force  # P5 D4 static head (H1590); gitignored docs/w/ + docs/browse/
python scripts/build_docs_site.py             # build the docs-site (ZettelkastenWiki Wave-3 pilot)
python scripts/gen_golden.py                  # regenerate golden render fixtures for test_render_golden.py
python scripts/measure_d5.py                  # D5 latency/perf measurement run
```

Copy `.env.example` → `.env` before running the API — sets `DATABASE_PATH`,
`LOG_LEVEL`, `CORS_ORIGINS`, and `COLOGNE_SCAN_BASE` (the csl-websanlexicon
`serveimg`/`servepdf` host used for scan-anchored citations).

## Key directories / files

| Path | Purpose |
|---|---|
| `app/` | FastAPI service: `main.py` (entry point/routes), `db.py`, `render.py` (entry rendering), `salt.py` (Salt facade REST — see Conventions), `scan_resolver.py`, `segment.py`, `transliterate.py`, `versions.py`, `cite.py` (citation-ID minting) |
| `scripts/` | One script per data-build stage (crosswalk → entries → forms → db → static cache → docs site); `measure_d5.py` and `archive_senses.py` are maintenance/measurement, not part of the main build chain |
| `data/` | Data assets, incl. `data/frequency/` (DCS frequency sidecar joined against `union_headwords`, see `.ai_state.md`) — `data/raw*/`, `data/releases/`, and D5 measurement outputs are gitignored/regenerable |
| `tests/` | `test_api.py`, `test_citability.py`, `test_render_golden.py` (golden fixtures in `tests/golden/`), `test_static_cache.py`, `test_docs_site.py` |
| `docs/`, `docs-site/`, `wiki/` | Static site output / docs-site pilot / wiki content |
| `docs/SANDHI_METHODS_DEEP_MANUAL.md` | Sandhi **methods** deep manual (induce / score / method A·B·C / failure taxonomy) — H2069; hub inventory stays in `SANDHI_PROGRAMME.md` |
| `SANDHI_PROGRAMME.md` | Sandhi programme hub — what exists, pedagogy surfaces, curriculum TSVs (not methods depth) |
| `ARCHITECTURE.md` | A1–A4 design, SQLite DDL, API v1 contract, Salt max-reuse rules |
| `IMPLEMENTATION_PLAN.md`, `PHASE1_PLAN.md` | The gated P1–P7 roadmap and exit checks — **the actual source of truth for what's buildable next**, not this file |
| `EVAL_PLAN.md` | Anti-gaming rules (G-SEG/G-RENDER/G-SALT/G-PC/G-SCAN/G-LAT gates) + UC1–UC13 test scenarios |
| `RISKS.md` | R1–R12 pre-mortem, incl. the citability commitments (citation URLs must never depend on the `samskrtam.ru` server host) |
| `KOSHA_DECISIONS_NEEDED.md` | Open @DECIDE items — check before assuming a design choice is settled |

**CI (updated 31-07-2026, H1944):** `.github/workflows/` carries
`python-ci.yml` (fixture build from zero, twice, then the fixture-tier test
suite), `ui-ci.yml` (vitest + vite build), `changelog-lint.yml`, and
`dependabot-auto-merge.yml` — the last now gated on a successful `workflow_run`
of both CI workflows and restricted to GitHub's queued auto-merge, so a
dependency bump cannot bypass the required checks.

**Build (H1944):** stage order is declared in
[`src/kosha/build/stages.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/build/stages.py),
not in an `if` chain.
`python scripts/build_db.py` with no flag runs **all ten** stages
(`lemmas → entries → forms → inflections → hybrid → pronoun → stem_bridge →
heritage → evidence → layers`); `--plan` prints the order without building;
`--profile fixture` builds the whole graph from the committed public pack in
seconds. Prerequisites are checked before the first write, the target is
promoted atomically, and `<target>.lock.json` records the sha256 of every
input. Do not add a stage by editing the CLI — add it to the registry.

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
- **Data build order matters**: crosswalk → entries → forms → db → static
  cache, per `scripts/`' naming; running a later stage against a stale earlier
  one produces silently wrong output, not an error.
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
