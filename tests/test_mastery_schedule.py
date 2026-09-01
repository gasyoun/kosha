"""H3742 combined mastery schedule selftest.

Locks the handoff's definition-of-done: the union of kosha's five drill
families' items is scheduled with a deterministic due-item draw for a fixed
seed+clock, and a draw actually mixes families rather than always returning
one family's items first.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_mastery_schedule as bms  # noqa: E402

SCHEDULE = ROOT / "data" / "mastery" / "combined_schedule.json"

pytestmark = pytest.mark.skipif(not SCHEDULE.exists(), reason="combined_schedule.json not built")


def _schedule():
    return json.loads(SCHEDULE.read_text(encoding="utf-8"))


def test_five_families_present():
    sched = _schedule()
    assert len(sched["families"]) == 5
    assert all(n > 0 for n in sched["families"].values())
    assert sched["total_items"] == sum(sched["families"].values())


def test_ease_in_range():
    sched = _schedule()
    for row in sched["rows"]:
        assert 0.0 <= row["ease"] <= 1.0
        assert row["stability_days"] > 0


def test_due_items_deterministic_for_fixed_seed_and_clock():
    sched = _schedule()
    clock = datetime(2026, 9, 2, tzinfo=timezone.utc)
    a = bms.due_items(sched, clock, 50, seed=42)
    b = bms.due_items(sched, clock, 50, seed=42)
    assert a == b


def test_due_items_draws_across_multiple_families():
    sched = _schedule()
    clock = datetime(2026, 9, 2, tzinfo=timezone.utc)
    drawn = bms.due_items(sched, clock, 200, seed=42)
    families = {row["family"] for row in drawn}
    assert len(families) > 1


def test_due_items_respects_clock():
    sched = _schedule()
    before_epoch = datetime(2026, 8, 1, tzinfo=timezone.utc)
    drawn = bms.due_items(sched, before_epoch, 50, seed=42)
    assert drawn == []


def test_check_passes_on_committed_schedule():
    assert bms.check(_schedule()) == 0
