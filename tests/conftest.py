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

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app", ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

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


def pytest_collection_modifyitems(config, items):
    if _core_db_present():
        return
    skip = pytest.mark.skip(
        reason="full-data tier: core DB absent (build it with "
               "`python scripts/build_db.py`, or run the fixture tier)"
    )
    for item in items:
        if item.module.__name__.split(".")[-1] in FULL_DATA_MODULES:
            item.add_marker(skip)
