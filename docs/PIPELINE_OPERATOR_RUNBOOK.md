# kosha — pipeline operator runbook

_Created: 10-07-2026 · Last updated: 31-07-2026_

The one document that says what to run, in what order, how to know each stage
worked, and what breaking looks like — for the whole chain: **DB build → API →
static cache → Pages → inflection ingest**. Written for an operator on a fresh
machine or a fresh session after context loss (H501, Fable 5 `claude-fable-5`;
every command and flag below was cross-checked against the script source on
10-07-2026, not recalled). Deeper design context lives in
[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md),
[PHASE1_PLAN.md](https://github.com/gasyoun/kosha/blob/main/PHASE1_PLAN.md) and each
script's docstring; this file is the operational spine only.

**The one dangerous property to internalize first:** the data build is
order-sensitive and fails *silently* — running a later stage against a stale
earlier one produces wrong output, not an error
([CLAUDE.md](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md) convention). When in
doubt, rebuild from the first affected stage down.

---

## 0. The map

```
sibling repos + release feeds                 gasyoun.github.io/kosha (Pages,
(csl-sqlite, glossary TSVs, MWinflect,        legacy builder = main branch root)
 VisualDCS, Heritage, sanskrit-util)                  ▲ committed pages go live on merge
        │                                             │
        ▼                                             │
scripts/build_db.py  ──►  data/db/kosha.db  ──►  static generators
  --stage lemmas · entries · forms ·             build_static_cache (docs/js/data + docs/cards — GITIGNORED, MG deploys)
  evidence · inflections · stem_bridge ·         build_paradigms    (docs/inflect/  — committed)
  heritage                                       build_colocation_page (colocation/ — committed)
        │                                        build_directory    (directory/     — committed)
        ▼                                        build_docs_site    (wiki/ → docs-site/ — committed)
uvicorn app.main:app   (live API tier)
        │
        ▼
release rituals: archive_senses → build_crosswalk → data-vX.Y.Z release assets
```

Two independent tiers consume the same `kosha.db`: the **live API** (FastAPI)
and the **static Pages tier** (pre-rendered JSON/HTML; RISKS R12 — the static
tier never calls a live service). Deploy is asymmetric: everything *committed*
under the repo root is live on Pages as soon as it merges to `main` (legacy
Pages builder serves the branch root); the two *gitignored* static-cache
outputs (`docs/js/data/`, `docs/cards/`) are deployed **out-of-band by M.G.**

## 1. Prerequisites

- **Env:** `Copy-Item .env.example .env` — sets `DATABASE_PATH`, `CORS_ORIGINS`
  (explicit origin list in production — credentialed CORS refuses wildcards),
  `COLOGNE_SCAN_BASE`, `HERITAGE_DICO_BASE`, `HISTORY_DB_PATH`,
  `HISTORY_IP_SALT` (set a real salt in production).
- **Python deps:** `pip install -r requirements.txt`.
- **Sibling checkouts under `GitHub/`** (the build resolves them by relative
  path): `sanskrit-util` (canonical transliteration/keys),
  `SanskritLexicography` (glossary form→lemma TSVs consumed by the forms
  stage), `MWinflect` (csl-inflect `calc_tables.txt` for the inflections
  stage), `VisualDCS` (DCS frequency/corpus feeds), `csl-orig` (only for the
  R3 fallback path).
- **Network on first run:** the entries stage downloads per-dict zips from the
  [csl-sqlite releases](https://github.com/sanskrit-lexicon/csl-sqlite/releases)
  into `data/raw_sqlite/` (cached thereafter).

## 2. The DB build (monthly rebuild, or after any upstream feed moves)

One script, ten stages, dependency-ordered. **No flag runs all stages in
order** — the safe default after any upstream change:

```sh
python scripts/build_db.py                # everything, in order → data/db/kosha.db
python scripts/build_db.py --plan         # print the order, build nothing
```

> **This line was aspirational until 31-07-2026.** The pre-W0B script
> dispatched on `if args.stage in (None, "x")`, and only `lemmas`, `pronoun`,
> `heritage`, `evidence`, and `layers` carried the `None` case — a no-flag
> build silently skipped `entries`, `forms`, `inflections`, `hybrid`, and
> `stem_bridge`, producing a plausible-looking database missing most of its
> content ([integrity issue #210](https://github.com/gasyoun/kosha/issues/210)).
> H1944 replaced the dispatch chain with the declared graph in
> [`src/kosha/build/stages.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/build/stages.py):
> the default build is now the topological expansion of the whole registry, a
> stage cannot be omitted by forgetting an `if`, and the finished database
> records which stages ran in `meta.build_stage_manifest`.

What the DAG adds beyond ordering:

- **Prerequisites are checked before the first write.** A missing feed fails
  the *plan*; it can no longer abort a half-built database.
- **Temporary target + atomic promotion.** Stages build into
  `data/db/.build/…`; the real path is replaced only after every
  postcondition and `PRAGMA foreign_key_check` pass. A failed build leaves
  the previous database untouched.
- **Immutable source lock.** `data/db/kosha.db.lock.json` records the sha256
  of every input, the executed order, and the resolved csl-sqlite release tag.
  A later build whose sources changed underneath refuses to run until you
  pass `--relock`.
- **`--release` refuses `latest`.** A release build needs a pinned csl-sqlite
  tag, otherwise the lock would not identify the bytes it was built from.
- **Skips are recorded, never silent.** An optional stage whose feed or local
  library is absent (`inflections` without MWinflect, `hybrid` without
  `vidyut`) is logged as skipped, with the reason, in both the run output and
  the lock.

Individual stages (`--stage`, repeatable — prerequisites are pulled in
automatically), in their canonical order:

| # | Stage | What it loads | Typical rerun trigger |
|---|---|---|---|
| # | Stage | Reads | What it loads | Typical rerun trigger |
|---|---|---|---|---|
| 1 | `lemmas` | — | the lemma spine + DCS frequency columns | new VisualDCS/frequency drop |
| 2 | `entries` | `lemmas` | per-dict csl-orig records from csl-sqlite zips (`--dicts mw,pwg,ap90`) | new csl-sqlite release / new dict |
| 3 | `forms` | `lemmas` | form→lemma TSVs (dcs 408,660 · vidyut 28,567 · heritage 992,194) from the glossary pipeline | glossary regen |
| 4 | `inflections` | `lemmas` | csl-inflect case/number/gender tables (MWinflect `calc_tables.txt`) | MWinflect update |
| 5 | `hybrid` | `inflections` | vidyut-prakriya overlay: ṇatva auto-fix, gap-fill, disputed flags (E1/H185) | vidyut update |
| 6 | `pronoun` | `inflections` | curated Gītā pronoun paradigm corrections (W4 QA) | gold regen |
| 7 | `stem_bridge` | `inflections`, `forms` | strong/weak-stem crosswalk unifying `forms` ↔ `inflections` lemmas | after 3+4 |
| 8 | `heritage` | `entries` | Heritage anchor/coverage witness (H345) | Heritage TSV regen |
| 9 | `evidence` | `lemmas`, `forms` | frequency band (1–5) + one corpus example per lemma | after 1+3 |
| 10 | `layers` | `entries` | **P-D5 public join layers** — `sense_frequency`, `roots_frequency`, `dict_corpus_coverage` (+ optional `mw_roots` / `mw_etymology` from sibling csl-orig) | new sense-freq / roots / coverage / mw_roots drop |

```sh
python scripts/build_db.py --stage entries --dicts mw,pwg,ap90
python scripts/build_db.py --stage layers     # P-D5 only (additive; safe re-run)
python scripts/check_g_size.py                # D5-4 G-SIZE tripwire (FAIL >1.8 GB)
```

### The fixture profile (seconds, no sibling repos, no network)

```sh
python scripts/build_db.py --profile fixture  # → data/db/kosha_fixture.db
```

Builds the same ten stages against the committed pack in
[`tests/fixtures/build/sources/`](https://github.com/gasyoun/kosha/tree/main/tests/fixtures/build/sources)
— seven lemmas, three dictionaries, hand-written paradigm tables. This is what
Python CI runs on every PR, and it is the fastest way to check a change to the
graph without a full-data workstation. It carries no restricted bytes.

### P-D5 query surface (agent SQL)

After `--stage layers`, an agent opens `data/db/kosha.db` and can join:

```sql
-- sense frequency for dharma (SLP1 Darma)
SELECT layer, sense_id, sense_rank, count_all, provenance
FROM sense_frequency WHERE lemma_slp1 = 'Darma' ORDER BY layer, sense_rank;

-- corpus attestation of a union headword
SELECT status, best_tier, evidence_count
FROM dict_corpus_coverage WHERE slp1 = 'nAga';

-- root curriculum rank for kṛ
SELECT rank, attested_count, coverage_pct
FROM roots_frequency WHERE dcs_lemma = 'kṛ';

-- cross-asset: lemmas × coverage × sense-freq
SELECT l.slp1, l.rank_all, c.status, c.evidence_count,
       COUNT(s.sense_id) AS n_sense_rows
FROM lemmas l
LEFT JOIN dict_corpus_coverage c ON c.slp1 = l.slp1
LEFT JOIN sense_frequency s ON s.lemma_slp1 = l.slp1 AND s.layer = 'mw'
WHERE l.slp1 IN ('Darma', 'nAga', 'kf')
GROUP BY l.slp1;
```

**Not loaded (by design):** restricted-tier assets (`corpus-lexicon`,
`sa-ru-glossary`, …); full locus dumps (`dict_corpus_concordance`,
`paninian_concordance`) — use the **coverage summary** tables instead (R-N7).
No new public API routes expose these tables; agent/SQL only until a rights-
cleared endpoint is designed.

**Verify after a full build:**

```sh
pytest                                    # 185 tests green as of 10-07-2026
python scripts/gen_golden.py              # regenerate frozen render fixtures if renderer changed
```

`pytest` is the load-bearing check: `test_render_golden.py` catches renderer
drift against frozen, seeded, non-hand-picked snapshots; `test_citability.py`
guards the citation contract; `test_paradigms.py` locks static/API paradigm
parity. **Failure symptom decoder:** `sqlite3.OperationalError: unable to open
database file` from any script or test = no `data/db/kosha.db` in *this*
checkout (fresh clone or worktree — the DB is gitignored; build it or run in
the DB-bearing checkout). A wave of `test_static_cache` failures with the same
error means the same thing, not a regression.

## 3. The live API

```sh
uvicorn app.main:app --reload --port 8000
```

Reads `.env`; serves `/api/v1/*` (lookup, sense citation resolution incl.
`@version` archives, paradigms, page/neighbors, personal history). The history
store is a **separate** SQLite (`HISTORY_DB_PATH`) precisely so the monthly
dict rebuild never touches user data.

## 4. The static tier (Pages)

All generators render **from the local `kosha.db` only** (RISKS R12). Two
deploy classes — this distinction is the most common operator confusion:

**(a) Committed → live on merge** (legacy Pages builder serves `main` root):

```sh
python scripts/build_paradigms.py         # → docs/inflect/ (paradigm shards + UI data)
python scripts/build_colocation_page.py   # → colocation/  (printed-leaf browser)
python scripts/build_directory.py         # → directory/   (datasets+tools directory, JSON-LD)
python scripts/build_docs_site.py         # → docs-site/   (wiki/ rendered)
```

Commit the regenerated output with the change that caused it; merging = deploying.

**(b) Gitignored → M.G. deploys out-of-band** (never commit these):

```sh
python scripts/build_static_cache.py      # → docs/js/data/{lemmas,attested_keys}.json + docs/cards/*.json
# P5 static word-page head (D4 / H1590) — after cards exist; gitignored docs/w/ + docs/browse/
python scripts/build_word_pages.py --coverage 0.95 --force
# optional pin after re-measure:  python scripts/build_word_pages.py --head 11148 --force
```

~50,355 attested per-lemma cards, sharded one-file-per-lemma (a single bundle
would cross GitHub's 100 MB file cap), generated in frequency-rank order so an
interrupted run front-loads the highest-value cards and resumes without
redoing work. Word pages (H1590) take the **D4 static head** only — N measured
at ~95% corpus token mass from `lemma_frequency.tsv` (today N=11,148; only
lemmas with cards are prerendered). The SSR route `GET /w/{slp1}` covers the
long tail. Exit packet:
[docs/P5_WORD_PAGE_EXIT_PACKET.md](https://github.com/gasyoun/kosha/blob/main/docs/P5_WORD_PAGE_EXIT_PACKET.md).

## 5. Release rituals (citability — RISKS R1)

When cutting a **data release** (`data-vX.Y.Z`):

```sh
python scripts/archive_senses.py                       # freeze senses → data/releases/<version>/senses.sqlite
python scripts/build_crosswalk.py                      # old→new sense_crosswalk audit trail
python scripts/update_manifest.py refresh              # re-stat manifest rows (mechanical, safe unattended)
```

The archive is gitignored and ships as a **GitHub release asset** — that asset
URL is what `app/cite.py` embeds in citations, so a missing upload breaks the
"2026 citation resolves in a 2028 browser" commitment. `*-dev` data versions
are deliberately **not citable** (no release asset). Remember the **two
version tracks**: repo tags (`vX.Y.Z`, [CHANGELOG.md](https://github.com/gasyoun/kosha/blob/main/CHANGELOG.md))
version code+docs; `data_version` (in the DB meta + release assets) versions
data — do not conflate them.

## 6. Maintenance / occasional

```sh
python scripts/measure_d5.py              # latency/size SLO measurement (local only)
python scripts/purge_search_events.py --days 180   # M.G.-run retention purge; rollups never touched
python scripts/deploy_guhya.py            # restricted-tier FTP backup (needs .env.deploy — M.G. creds)
python scripts/fallback_csl_orig.py       # R3 fallback exercise (csl-orig direct parse), ap90 witness
python scripts/compare_vidyut_cologne.py  # dual-engine paradigm diff (vidyut vs csl-inflect)
python scripts/build_dict_corpus_concordance.py    # B1 concordance regen (needs VisualDCS sqlite; see data/concordance/BUILD_REPORT.md)
```

## 7. Never touch / never commit

Verbatim policy from [CLAUDE.md](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md) —
an operator manual that omitted these would be worse than none:

- `docs/js/data/lemmas.json`, `docs/js/data/attested_keys.json`, `docs/cards/`
  — generated by `build_static_cache.py`, deployed to Pages **out-of-band by
  M.G.**; never commit.
- `*.db` / `*.sqlite` (`data/db/kosha.db`, `unified_dict.db`) — regenerated,
  never committed.
- `data/raw/`, `data/raw_sqlite/`, `data/releases/` — source/release inputs,
  gitignored, regenerable or fetched.
- `data/d5_*.log`, `data/d5_measurements.json` — machine-specific measurement
  outputs.
- Citation URLs must never depend on the `samskrtam.ru` host (RISKS R5) — do
  not hardcode it in any citation-minting path.
- Licensing is two-tier: code CC BY-NC 4.0, data releases CC BY-SA 4.0 — the
  ShareAlike side does **not** permit adding a non-commercial restriction.

## 8. Quick reference

| I want to… | Run |
|---|---|
| Rebuild everything after upstream data moved | `python scripts/build_db.py` then `pytest` |
| Refresh one dict's entries | `python scripts/build_db.py --stage entries --dicts mw` |
| Re-ingest inflections (csl-inflect) | `python scripts/build_db.py --stage inflections` then `--stage stem_bridge` |
| Serve the API locally | `uvicorn app.main:app --reload --port 8000` |
| Refresh the committed Pages pages | `build_paradigms.py` / `build_colocation_page.py` / `build_directory.py` / `build_docs_site.py`, commit + merge |
| Regenerate the card cache for M.G. to deploy | `python scripts/build_static_cache.py` |
| Cut a citable data release | `archive_senses.py` → `build_crosswalk.py` → upload `senses.sqlite` as the `data-vX.Y.Z` release asset → `update_manifest.py refresh` |
| Check nothing regressed | `pytest` (185 green in the DB-bearing checkout) |

_Dr. Mārcis Gasūns_
