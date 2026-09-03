# Full-data-tier suite repaired on MSI: 60 failed -> 0 (isolation / gate / Salt fixes)

**Date:** 04-09-2026 · **Tier:** OxAlpha `zai-coding-plan/glm-5.3-flash` · **Box:** MSI (Windows)

The H4019 GTD row's final census left 60 failures confined to the full-data
tier (modules that run only where the 1.7 GB `kosha.db` exists - CI/Mac skip
them), pre-existing and orthogonal to the pin work. This pass repairs all of
it; **full suite on the MSI box: 737 passed, 107 skipped, 0 failed** (fixture
tier without the core DB: 623 passed, 221 skipped - CI parity green).

Three root causes, three fixes:

1. **Salt-contract staleness** (`test_evidence` 24, `test_api` 4,
   `test_citability` 2): the tests still read the pre-W0C shapes -
   top-level `entry["evidence"]` / `entry["sense_ids"]` / `entry["dict"]`
   (moved under `entry["kosha"]` in #224) and the pre-W0C error envelope
   `body["detail"]["error"]["code"]` (now top-level `body["error"]["code"]`).
   The files predate the contract change and only ever ran on a
   full-data box, so nothing on CI flagged them.
2. **Feature-gate** (`test_history` 11): D10 keeps history/auth/stats
   unmounted unless `KOSHA_HISTORY_ENABLED` is truthy, and the box does not
   set it - every route 404'd. The module now uses the documented
   `kosha.feature_gates.mount_history` runtime mount plus the env flag and
   `get_settings(refresh=True)` in one autouse fixture, instead of depending
   on a box-local variable.
3. **Test-order isolation** (`test_reverse_lookup` 11, `test_static_cache` 5,
   `test_api`/`test_paradigms`/`test_citability` remainder in mixed runs):
   `test_readiness` (and friends) refresh `kosha.settings._cached` under
   `monkeypatch`; after teardown the environ is restored but the cache keeps
   `KOSHA_CORE_DB_PATH` pointing into a deleted `tmp_path`, so every later
   `get_settings()` consumer dies with `sqlite3.OperationalError`. Proven by
   pair-run (`test_readiness` + `test_reverse_lookup` -> 9 failed). Fix: an
   autouse `conftest` fixture resets the settings cache around every test.

Plus one robustness follow-through: `test_paradigms` / `test_static_cache`
resolved the core DB via a hardcoded repo-relative path; both now read
`get_settings().core_db`, the same source of truth
`tests/conftest.py::_core_db_present` uses, so the tier also runs from a
worktree with `KOSHA_CORE_DB_PATH` set.
