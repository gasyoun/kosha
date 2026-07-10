# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

`kosha` (public brand: **Gasuns Sanskrit Dictionary**) is a translator-first
Sanskrit dictionary web service: fast lookup over the Cologne Digital Sanskrit
Dictionaries (MW, PWG, AP90 first), collapsing every dictionary's entry for a
headword onto one page, scan-anchored to the printed source, with citable
sense-level IDs. FastAPI backend + a static docs/cache site. **Status:
pre-alpha** — this is currently a locked, gated engineering plan (`v0.2.x`)
plus an honest FastAPI stub; coding starts with
[`PHASE1_PLAN.md`](PHASE1_PLAN.md). No lookup functionality works yet — don't
assume any endpoint returns real data until `PHASE1_PLAN.md`'s exit checks
say so.

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
| `ARCHITECTURE.md` | A1–A4 design, SQLite DDL, API v1 contract, Salt max-reuse rules |
| `IMPLEMENTATION_PLAN.md`, `PHASE1_PLAN.md` | The gated P1–P7 roadmap and exit checks — **the actual source of truth for what's buildable next**, not this file |
| `EVAL_PLAN.md` | Anti-gaming rules (G-SEG/G-RENDER/G-SALT/G-PC/G-SCAN/G-LAT gates) + UC1–UC13 test scenarios |
| `RISKS.md` | R1–R12 pre-mortem, incl. the citability commitments (citation URLs must never depend on the `samskrtam.ru` server host) |
| `KOSHA_DECISIONS_NEEDED.md` | Open @DECIDE items — check before assuming a design choice is settled |

No `.github/workflows/` exist yet — there is no CI in this repo currently.

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
