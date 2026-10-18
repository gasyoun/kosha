# Data-layer sidecar — spec

_Created: 18-10-2026 · Last updated: 18-10-2026_

**Status:** ruling of the 18-10-2026 grill, decisions [#3](https://github.com/gasyoun/kosha/blob/main/reports/DATA_CONSUMER_PROVENANCE_DECISIONS_18.10.26.md) (fields), #5 (sidecar as the carrier), #9 (round-trip), #10 (novelty), #13 (ownership), #15 (order), #18 (acceptance). Executed by **H6979**.

## Why

The estate's own diagnosis **D-HUB-2c** is *"one-shot deliverables never wired to consumers"*: a layer gets built, registered in `data/manifest/datasets.json`, and then nobody consumes it. The Xena Project correspondence (2026-10-16) states the norm we were already failing: **a formal artifact is worth what its use is, not what its correctness is**. So the fix is not "build fewer layers" and not "review more"; it is that every derived layer must carry, at build time, the name of the thing that consumes it — or say out loud that it has none.

Correctness is a *stronger* claim than provenance, and a sidecar does not assert it. A wrong layer is worse than a missing one (decision #7); the sidecar is the carrier of the *use* fact, not a quality badge.

## Where it lives

Beside the layer, written by the builder, one JSON file per layer:

- layer-per-directory / layer id known → `<dir>/<layer>.meta.json`
- artifact-per-file builder → `<artifact>.meta.json` (the convention `SanskritSpellCheck/tools/build_spellcheck_dict.py` and several kosha builders already use)

Write it with the helper — **never by hand, never by copying the rule**:

```python
from sanskrit_util import sidecar_path_for, write_sidecar

write_sidecar(sidecar_path_for(artifact, layer="union-headwords"), {
    "layer": "union-headwords",
    "made_by": "ai",
    "model": "claude-sonnet-5",
    "handoff": "H6068",
    "consumers": [{"kind": "repo", "id": "kosha",
                   "use": "spellcheck dictionary source"}],
    "status": "active",
    "novelty": "adds MWderivations key2 spellings the 15-dict key1 union misses",
})
```

Helper: `sanskrit-util` ≥ 0.13.0, `py/sanskrit_util/sidecar.py`. Contract tests live in `py/tests/test_sidecar.py`; the kosha-side negative test is `tests/test_layer_sidecar.py`.

## Fields

| Field | Req. | Values | Meaning |
|---|---|---|---|
| `layer` | yes | bare id | layer id; equals the `datasets.json` `id` when the layer is registered |
| `made_by` | **yes** | `human` · `ai` · `human+ai` · `upstream` · `unknown` | who produced the layer |
| `model` | no (null ok) | exact id, e.g. `claude-sonnet-5`, `glm-5.3` | the model that ran the builder; a family name alone is not an id |
| `handoff` | no (null ok) | `H####` | the handoff that executed the build |
| `consumers` | yes unless dormant | `[{"kind": "repo"·"paper"·"surface", "id": "...", "use": "..."}]` | WHO uses this layer |
| `status` | **yes** | `active` · `dormant` · `retired` | lifecycle |
| `owner` | iff dormant | a name | who is responsible for the dormant layer |
| `review_after` | iff dormant | `YYYY-MM-DD` | the date the dormancy is re-decided |
| `novelty` | **yes** | one paragraph | what this layer adds over what already exists |
| `roundtrip` | iff `human_gold` | `{"checked": bool, "rows_in": int, "rows_out": int}` | length/round-trip evidence |
| `human_gold` | no | bool (default false) | the layer feeds a human-gold set |
| `built_at` | no | `YYYY-MM-DD` | build date |
| `builder` | no | script path or provenance text | what produced it |

Unknown extra keys are preserved — a builder may keep its own counts/sources block beside the contract fields (that is how the SanskritSpellCheck builder keeps `counts` and `sources`).

## What counts as a consumer

A **consumer** is a place where the layer is actually read, and the read is named in the entry:

- a **repo** (the code path that loads it, e.g. `kosha` → `names.csv` join);
- a **paper** (`A##` in `Uprava/ARTICLES.md`) that cites it as data;
- a **public surface** (a release asset, an API projection, a page).

**Not** a consumer: an agent session that read the layer once, a `grep` in a report, "someone might want it". If the only honest answer is "nobody yet", the layer is `dormant` — that is a legitimate state, not a failure.

## The gate (refusals)

`write_sidecar()` refuses to write (raising `SidecarError` listing **every** problem at once) when:

1. **no `made_by`** — who made the layer is never optional;
2. **no consumers and status ≠ `dormant`** — an unused layer must be declared dormant, not quietly registered as an asset;
3. **`dormant` without `owner` + `review_after`** — a dormant layer with no name and no date is a black hole;
4. **`human_gold: true` without a `roundtrip` block**, or `rows_in != rows_out` (decision #9: the length check is mandatory exactly for layers feeding human gold — elsewhere it is optional);
5. **empty `novelty`** (decision #10: "what does this add over what exists?" is the paragraph that stops a re-derivation of a known result).

Plus shape rules: `status`/`made_by` must be one of the enumerations, `consumers[].kind` one of `repo|paper|surface`, `handoff` an `H####`, `review_after` a real date.

A gate with only a passing fixture is not tested (decision #18). `py/tests/test_sidecar.py` is 17 refusals out of 23 cases; `kosha/tests/test_layer_sidecar.py` re-proves the gate on kosha's own fixtures so a kosha-side regression cannot hide behind the library's tests.

## Dormant rule

`dormant` requires `owner` **and** `review_after` (default review horizon used by the 18-10-2026 backfill: 90 days — `2027-01-18`). Re-decide at that date: wire a consumer (`active`), keep it dormant with a new date, or `retired` (decision #6 keeps Sanskrityatina-trio as dormant, **not** deleted).

## Manifest mapping (`data/manifest/datasets.json`)

The manifest row is the registration record; the sidecar file is the layer's own record. Where both exist they must agree, and the row carries the machine-readable subset:

| sidecar | `datasets.json` | note |
|---|---|---|
| `layer` | `id` | the row is keyed by it |
| `made_by` | `made_by` | same vocabulary |
| `model` | `model` | exact id or `null` |
| `handoff` | `handoff` | `H####` or `null` |
| `consumers` | `consumers` | manifest keeps its existing **string list** (the public API projection is frozen, decision #7); the sidecar file uses the object form |
| `status` | **`layer_status`** | ⚠️ see below |
| `owner` / `review_after` | same keys | dormant rows only |
| `roundtrip` | same key | only when the layer is `human_gold` |
| — | `provenance_source` | how this row's fields were derived: `builder` · `provenance_verified` · `path+first-commit` · `manual` |
| — | `built_at` | build/first-commit date where derivable |

⚠️ **`status` is already taken in the manifest.** Six rows carry the *planning* vocabulary (`awaiting-consumer`, `diff-then-decide`, `internal-tooling`) and `scripts/build_dataset_disciplines.py` reads it. The lifecycle triad therefore lands as **`layer_status`**; the planning `status` values are preserved untouched. This is the one deliberate deviation from the decision's field name, and it exists so the decision does not silently corrupt an existing report.

`RECORD_REQUIRED_KEYS` in `src/kosha/api/catalog.py` and the public API projection are **not** touched: the new keys are internal manifest fields, never serialised to `/api/v1/datasets`.

## Backfill (18-10-2026, H6979)

All 149 rows got machine provenance, derived in this precedence:

1. `provenance_verified` text (10 rows) — it already carries date + handoff + exact model id;
2. `builder` text (63 rows carry `H####`, 7 carry a model family) — parsed;
3. neither → the source path's **first commit** in the sibling clone (`git log --diff-filter=A`) — date becomes `built_at`, an `H####`/model in the commit subject is harvested;
4. still nothing → left `null` and listed in the triage section of
   [`reports/DATA_LAYER_PROVENANCE_BACKFILL_18.10.26.md`](https://github.com/gasyoun/kosha/blob/main/reports/DATA_LAYER_PROVENANCE_BACKFILL_18.10.26.md). **Disputed values are never guessed into a field.**

`novelty` is **not** backfilled: it is a judgment paragraph about a layer's distinctness, and inventing 149 of them would be exactly the "отписка" the decision warns about. It is required at the next write of each layer's sidecar (the helper enforces it); the report counts the residual.

The 18 rows with no consumers (decision #6) close as: **2 `active`** — `dcs-compound-dictionary` (`kosha` names.csv), `morphology-giveback-candidates` (`csl-inflect`) — and **16 `dormant`** with `owner: MG` and `review_after: 2027-01-18`.

Verify: `python scripts/backfill_sidecars.py --check` → `149/149`.

## Non-goals

- No overlay guard here (decision #8 — that is the next handoff, keyed by protected **paths**, list in the layer registry, not in the guard code).
- No public API/schema change (decision #7), no `RECORD_REQUIRED_KEYS` change.
- No mass re-wiring of foreign builders outside the three pilot repos (kosha, SanskritSpellCheck, SanskritLexicography).
- No skill-layer or handoff-discipline work (decision #19 — deferred until the data is closed).

_Dr. Mārcis Gasūns_
