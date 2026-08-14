"""Shared pytest configuration (W0B, H1944).

D14 splits the suite into two tiers. The **fixture tier** runs on every PR
against the compact committed pack; the **full-data tier** needs
`data/db/kosha.db` built from the real feeds (~4 GB of sibling repos) and runs
on a workstation or the release gate.

Before W0B a fresh checkout simply failed 92 tests with
`sqlite3.OperationalError: no such table`, which is indistinguishable from a
real regression and is why CI could not be turned on at all. The modules below
are the measured full-data set; when the core DB is absent they are skipped
with a reason instead of failing.

Keep this list explicit. Auto-detecting "does this test touch the DB" would
hide a genuinely broken test behind a heuristic.
"""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app", ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

# CI / local pytest: join the committed slice only (H2670 / H2680).
# Production SSR leaves these unset and resolves the sibling trees.
os.environ.setdefault("KOSHA_RU_JOIN", str(ROOT / "tests" / "fixtures" / "ru_join"))
os.environ.setdefault(
    "KOSHA_SR_GLOSS", str(ROOT / "tests" / "fixtures" / "sanskritrussian")
)

#: Modules whose assertions are pinned to full-data counts (e.g. 323,425
#: lemmas) or to entries only present in the real dictionaries.
FULL_DATA_MODULES = {
    "test_api",
    "test_citability",
    "test_evidence",
    "test_heritage_default_off",
    "test_history",
    "test_inflections",
    "test_reverse_lookup",
    "test_static_cache",
}


def _core_db_present() -> bool:
    from kosha.settings import get_settings

    return get_settings().core_db.is_file()


def _amar_checkout() -> bool:
    """The Amarakośa text is a sibling repo, not a Python dependency."""
    for candidate in (ROOT.parent, ROOT.parent.parent):
        if (candidate / "AMAR" / "amar.txt").is_file():
            return True
    return False


def _importable(module: str) -> bool:
    import importlib.util

    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


#: Modules that need something this environment may simply not have — a sibling
#: checkout, or a library outside `requirements.txt`. Distinct from the
#: full-data tier: those need *data*, these need *the environment*.
ENVIRONMENT_REQUIREMENTS = {
    "test_thematic_vocabulary": (
        _amar_checkout,
        "needs the sibling AMAR checkout (../AMAR/amar.txt)",
    ),
    "test_wsd_two_witness": (
        lambda: _importable("indic_transliteration"),
        "needs indic_transliteration (used by scripts/wsd_core.py, not a "
        "declared kosha dependency)",
    ),
}


#: The compact DB `python scripts/build_db.py --profile fixture` promotes, and
#: the one CI builds twice on every PR.
FIXTURE_DB = ROOT / "data" / "db" / "kosha_fixture.db"


def _require_fixture_db():
    import pytest as _pytest

    if not FIXTURE_DB.is_file():
        _pytest.skip(
            "fixture DB absent — build it with "
            "`python scripts/build_db.py --profile fixture`",
            allow_module_level=False,
        )
    return FIXTURE_DB


@pytest.fixture()
def fixture_con():
    """A read-only connection to the fixture DB.

    W0C (H1945) added this because the contract work it introduced — Salt
    parity, the sanitizer, error shapes, citation resolution — has to be
    verified on the tier CI actually runs. The pre-existing API tests are
    pinned to full-data counts and skip in CI, so a gate written against them
    would have proved nothing on any pull request.

    W1A (H2341): opens through the storage facade so ATTACH behaviour matches
    production `get_db()`, not a bare sqlite3 open that would miss multi-DB.
    """
    from kosha.query.connection import open_query_connection

    path = _require_fixture_db()
    con = open_query_connection(core_path=path)
    try:
        yield con
    finally:
        con.close()


@pytest.fixture()
def fixture_client():
    """A `TestClient` whose routes read the fixture DB.

    The store is injected through FastAPI's dependency override rather than by
    re-pointing settings: `app/db.py` resolves `DB_PATH` at import, and pytest
    imports `app.main` once per session, so an environment variable set in a
    test would arrive too late — the same reason `mount_history` exists.

    The override opens a *fresh* connection per request, exactly as `get_db`
    does in production. Handing every request one shared connection would fail
    outright (`TestClient` dispatches routes on a worker thread and SQLite
    objects are thread-bound) and, worse, would test a concurrency shape the
    service never runs.
    """
    from fastapi.testclient import TestClient

    from app.main import app
    from db import get_db
    from kosha.query.connection import open_query_connection

    path = _require_fixture_db()

    def _fixture_db():
        # Same facade as production get_db() — multi-DB ATTACH when present.
        con = open_query_connection(core_path=path)
        try:
            yield con
        finally:
            con.close()

    app.dependency_overrides[get_db] = _fixture_db
    try:
        # `raise_server_exceptions=False` so the installed error handlers are
        # what the test observes — otherwise TestClient re-raises and the
        # response shape under test never gets built.
        yield TestClient(app, raise_server_exceptions=False)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def fixture_lemma(fixture_con):
    """An SLP1 headword that exists in the fixture pack, in every dictionary
    the pack covers. Discovered, not hardcoded: the pack is seven lemmas and
    may be regenerated."""
    row = fixture_con.execute(
        "SELECT slp1_key, COUNT(DISTINCT dict) AS n FROM entries "
        "GROUP BY slp1_key ORDER BY n DESC, slp1_key LIMIT 1"
    ).fetchone()
    return row["slp1_key"]


def pytest_collection_modifyitems(config, items):
    full_data_skip = None
    if not _core_db_present():
        full_data_skip = pytest.mark.skip(
            reason="full-data tier: core DB absent (build it with "
                   "`python scripts/build_db.py`, or run the fixture tier)"
        )

    unmet = {
        module: reason
        for module, (probe, reason) in ENVIRONMENT_REQUIREMENTS.items()
        if not probe()
    }

    for item in items:
        module = item.module.__name__.split(".")[-1]
        if full_data_skip is not None and module in FULL_DATA_MODULES:
            item.add_marker(full_data_skip)
        if module in unmet:
            item.add_marker(pytest.mark.skip(reason=unmet[module]))
