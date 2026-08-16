# Kosha platform architecture

_Created: 30-07-2026 · Last updated: 13-08-2026_

This target architecture implements the decisions in the
[plan of record](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_ARCHITECTURE_ROADMAP_2026_2027.md).
Migration is incremental; current entry points remain compatibility shims until
their contract tests prove removal safe.

## Bounded modules

The installable package is rooted at `src/kosha/`:

| Module | Owns | Must not own |
|---|---|---|
| `domain` | typed IDs, provenance/trust rules, Salt-compatible Pydantic models | SQL, HTTP, filesystem |
| `query` | repository interfaces and application query services | FastAPI response construction |
| `rendering` | safe Cologne renderer, citations, shared serializers | route or build orchestration |
| `pipeline` | stage registry, dependency DAG, build lock, postconditions, atomic promotion | domain presentation |
| `settings` | typed environment and path configuration | import-time side effects |
| `api` | thin FastAPI routers, exception mapping, readiness (`GET /ready`), correlation + low-cardinality metrics (`GET /metrics`) | duplicated SQL/serialization; visitor analytics |

`app/` and `scripts/` initially import these modules. Direct `sys.path`
injection is removed as each consumer moves.

## API contract

`/api/v1` retains the envelope:

```json
{"data_version":"...","query":{},"results":[]}
```

Each dictionary result is the full kosha entry model built on the Cologne Salt entry described by
[SALT_API_PROFILE.md](https://github.com/sanskrit-lexicon/csl-standards/blob/main/docs/SALT_API_PROFILE.md).
Kosha-specific fields appear only below `kosha`:

```json
{
  "id": "lemma-...-L...",
  "headword": {},
  "csl": {},
  "kosha": {
    "sense_ids": [],
    "rendered_html": "...",
    "evidence": {},
    "heritage": {},
    "cite": {}
  }
}
```

The same model and serializer feed `/api/v1`, `/dicts/*`, static cards, and
SSR pages. `/dicts/*` then applies the strict Salt §9 projection (six C-SALT
fields plus `csl`); kosha-owned surfaces retain `kosha`. FastAPI exception handling emits the documented top-level error
object rather than `detail.error`. This is an intentional pre-public break.

## Configuration

One typed settings object reads:

- `KOSHA_CORE_DB_PATH`;
- `KOSHA_INFLECTIONS_DB_PATH`;
- `KOSHA_LAYERS_DB_PATH`;
- `KOSHA_ARCHIVE_DIR`;
- `KOSHA_PUBLIC_BASE`;
- `KOSHA_HISTORY_ENABLED`, default `false`;
- `KOSHA_EXPECTED_DATA_VERSION` (optional; readiness fails closed on mismatch).

`DATABASE_PATH` remains a deprecated alias for `KOSHA_CORE_DB_PATH` during W0
and emits a warning. Conflicting values fail startup. Production-only secrets
have no committed defaults.

## Storage facade

| File | Tables |
|---|---|
| `core.db` | meta, sources, lemmas, entries, senses, forms, stem bridge, Heritage anchors |
| `inflections.db` | inflections and generated paradigm metadata |
| `layers.db` | sense/roots frequency, coverage, roots, etymology, later public query layers |
| `history.db` | visitors, events, rollups, magic links; separate and disabled |

The repository attaches read-only databases with stable aliases and is the
only API/static query path. Physical placement never leaks into response
models. The split occurs only after parity tests cover existing monolith
queries.

**W1A (H2341) status:** the facade is implemented in
[`src/kosha/query/`](https://github.com/gasyoun/kosha/tree/main/src/kosha/query)
(`open_query_connection`, stable aliases `core` / `inflections` / `layers`,
TEMP VIEW projection for unqualified SQL, history never attached). Runtime
defaults still point at the monolith `data/db/kosha.db` until a later wave
performs the bulk physical move; multi-DB attach is exercised by the fixture
parity suite (`tests/test_storage_facade.py`).

**W1C (H2343) status:** readiness lives in
[`src/kosha/api/readiness.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/readiness.py)
and is exposed as `GET /ready` (distinct from liveness `GET /health`). Checks:
core open via the storage facade, optional attached layers, readable
`data_version` (+ optional expected-version match), citation archives via
`kosha.api.archive`, and history as `disabled` when the D10 flag is off.
HTTP: 200 when ready, 503 when not — never 500 for a correctly disabled
optional writable. Tests: `tests/test_readiness.py`.

**W2C (H2348) status:** request correlation and low-cardinality metrics live
in
[`src/kosha/api/observability.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/observability.py).
Every response carries `X-Request-ID` (echo or UUID4). `GET /metrics`
exports Prometheus text: request counts/durations by **route template**
(never headword/path), `kosha_ready` + `kosha_ready_check` using the
H2343 names, and `kosha_ready_failures_total` incremented only by
`GET /ready`. History/auth stay off. Operator notes:
[`docs/RELEASE_OBSERVABILITY.md`](https://github.com/gasyoun/kosha/blob/main/docs/RELEASE_OBSERVABILITY.md).
Tests: `tests/test_observability.py`.

## Build system

The canonical full target expands to:

`lemmas → entries → forms → inflections → hybrid → pronoun → stem_bridge → heritage → evidence → layers`.

Each stage declares inputs, immutable source identity/checksum, dependencies,
outputs, destructive scope, and postconditions. The build:

1. resolves and verifies the lock;
2. creates temporary database files;
3. runs stages once in topological order;
4. checks foreign keys, required tables, counts, provenance, logical checksums,
   and size thresholds;
5. atomically promotes the validated files.

Mutable `latest` sources are forbidden in a release build.

## Static surfaces

A machine-readable registry declares for each surface:

- identifier and audience;
- source datasets and builder;
- committed or out-of-band output paths;
- public/restricted classification;
- deterministic acceptance command;
- deployment owner and rollback method.

**W1B (H2342) status:** the registry is
[`data/manifest/surfaces.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/surfaces.json)
(`schema: kosha-generated-surfaces-v1`). Validation is
[`src/kosha/surfaces/`](https://github.com/gasyoun/kosha/tree/main/src/kosha/surfaces)
plus CLI [`scripts/validate_surfaces.py`](https://github.com/gasyoun/kosha/blob/main/scripts/validate_surfaces.py);
the required Python CI job runs the CLI before the fixture build. Dictionary-payload
surfaces must name `kosha.api.repository` and `kosha.api.serializer` (no mirrored
SQL or payload code).

Crawlable independent surfaces remain. They consume the shared query and
serializer services rather than mirroring payload code.

## Trust boundaries

- Cologne markup is parsed into an allowlisted HTML subset. Text and attribute
  values are escaped; event handlers, active content, unsafe URLs, and unknown
  attributes are dropped.
- A restrictive CSP is documented for both API/SSR and static hosting.
- History/auth/stats routers are not included unless the false-by-default
  feature flag is enabled.
- Restricted backup uses encrypted transport, temporary remote names, atomic
  rename, and digest verification. Claude Code never uploads.
- Historical citations resolve only through a configured public base and a
  locally mounted, checksummed immutable archive.

## Build-versus-reuse verdicts

| Concern | Verdict |
|---|---|
| Transliteration | reuse `sanskrit-util`; no new transcoder |
| Lemma spine | reuse `union_headwords.tsv`; no rebuild |
| Scan resolution | reuse existing Cologne resolver/serve endpoints |
| Dictionary interchange | reuse the Salt profile |
| Concordance matching | reuse `concordance_core.py` |
| Corpus/sense inputs | reuse existing manifests, crosswalks, and sidecars |
| Orchestration | build the small in-repo DAG; no external service |
| API/static serialization | extract one shared kosha service |
| Sanitization | use an established allowlist sanitizer behind a kosha policy wrapper |

---

_Dr. Mārcis Gasūns_
