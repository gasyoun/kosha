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
