"""H6979 — the data-layer sidecar gate, proven on kosha's own manifest.

Two jobs:

1. the library gate (`sanskrit_util.write_sidecar`) really REFUSES a bad
   sidecar — negative cases are the point (decision #18: a gate with only a
   passing fixture has not been tested);
2. every row of `data/manifest/datasets.json` carries machine provenance, the
   16 dormant rows carry an owner and a review date, and the 2 zero-consumer
   rows that have a real consumer are closed as `active` (decision #6).

The manifest contract is documented in `docs/LAYER_SIDECAR_SPEC.md`. No
kosha.db, no network: fixture-tier.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "data" / "manifest" / "datasets.json"
BACKFILL = REPO / "scripts" / "backfill_sidecars.py"

#: `sanskrit-util` is pinned in requirements.txt; a workstation also has the
#: sibling checkout (`SANSKRIT_UTIL_PY` names a linked worktree of it), which is
#: what a session uses before the pin bump lands.
_SIBLING_CANDIDATES = tuple(
    Path(candidate) for candidate in (
        os.environ.get("SANSKRIT_UTIL_PY"),
        REPO.parent / "sanskrit-util" / "py",
        Path.home() / "Documents" / "GitHub" / "sanskrit-util" / "py",
    ) if candidate
)


def _import_sidecar_api():
    import sanskrit_util  # noqa: PLC0415

    if hasattr(sanskrit_util, "write_sidecar"):
        return sanskrit_util
    for candidate in _SIBLING_CANDIDATES:
        if (candidate / "sanskrit_util" / "sidecar.py").exists():
            sys.path.insert(0, str(candidate))
            for name in [m for m in sys.modules
                         if m == "sanskrit_util" or m.startswith("sanskrit_util.")]:
                del sys.modules[name]
            import sanskrit_util as sibling  # noqa: PLC0415
            if hasattr(sibling, "write_sidecar"):
                return sibling
    pytest.fail("sanskrit-util < 0.13.0: the sidecar helper is not importable "
                "(bump the requirements.txt pin to a commit that has it)")


su = _import_sidecar_api()


@pytest.fixture(scope="module")
def rows():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["datasets"]


def payload(**over):
    base = {
        "layer": "test-layer",
        "made_by": "ai",
        "model": "claude-sonnet-5",
        "handoff": "H6979",
        "consumers": [{"kind": "repo", "id": "kosha", "use": "fixture"}],
        "status": "active",
        "novelty": "fixture novelty: distinct from the fixture baseline",
    }
    base.update(over)
    return base


# ---------- the gate: negative cases ----------

def test_gate_refuses_missing_made_by():
    body = payload()
    del body["made_by"]
    with pytest.raises(su.SidecarError):
        su.write_sidecar("/nonexistent/x.meta.json", body)


def test_gate_refuses_no_consumers_on_active():
    with pytest.raises(su.SidecarError):
        su.write_sidecar("/nonexistent/x.meta.json", payload(consumers=[]))


def test_gate_refuses_dormant_without_owner_and_date():
    with pytest.raises(su.SidecarError):
        su.write_sidecar("/nonexistent/x.meta.json",
                         payload(consumers=[], status="dormant"))


def test_gate_refuses_empty_novelty():
    with pytest.raises(su.SidecarError):
        su.write_sidecar("/nonexistent/x.meta.json", payload(novelty=""))


def test_gate_refuses_human_gold_without_roundtrip():
    with pytest.raises(su.SidecarError):
        su.write_sidecar("/nonexistent/x.meta.json", payload(human_gold=True))


def test_gate_write_leaves_no_file_on_refusal(tmp_path):
    target = tmp_path / "layer.meta.json"
    with pytest.raises(su.SidecarError):
        su.write_sidecar(target, {"layer": "x", "consumers": []})
    assert not target.exists()


def test_gate_accepts_a_complete_sidecar(tmp_path):
    written = su.write_sidecar(tmp_path / "layer.meta.json", payload())
    body = json.loads(written.read_text(encoding="utf-8"))
    assert body["made_by"] == "ai" and body["status"] == "active"


def test_gate_accepts_dormant_with_owner_and_date(tmp_path):
    written = su.write_sidecar(tmp_path / "layer.meta.json", payload(
        consumers=[], status="dormant", owner="MG", review_after="2027-01-18"))
    assert json.loads(written.read_text(encoding="utf-8"))["owner"] == "MG"


# ---------- the manifest: 150 rows (H6841 added sandhikosh-tsv, 27-10-2026) ----------
# Current count: 152 rows after H7316 added two KoshaSHRI fixtures, 29-10-2026.

REQUIRED = ("made_by", "model", "handoff", "layer_status", "provenance_source")


def test_manifest_has_152_rows(rows):
    assert len(rows) == 152


def test_every_row_carries_machine_provenance(rows):
    missing = [(r["id"], key) for r in rows for key in REQUIRED if key not in r]
    assert missing == [], "rows without machine provenance: %r" % (missing,)


def test_layer_status_vocabulary(rows):
    assert {r["layer_status"] for r in rows} <= {"active", "dormant", "retired"}


def test_made_by_vocabulary(rows):
    assert {r["made_by"] for r in rows} <= set(su.MADE_BY_VALUES)


def test_dormant_rows_have_owner_and_review_after(rows):
    dormant = [r for r in rows if r["layer_status"] == "dormant"]
    assert len(dormant) == 16, "decision #6 fixes the dormant set at 16 rows"
    for row in dormant:
        assert row.get("owner"), "%s: dormant without owner" % row["id"]
        assert row.get("review_after"), "%s: dormant without review_after" % row["id"]


def test_active_rows_have_consumers(rows):
    bad = [r["id"] for r in rows
           if r["layer_status"] == "active" and not r.get("consumers")]
    assert bad == [], "active rows without a consumer: %r" % (bad,)


def test_zero_consumer_rows_closed_as_active(rows):
    by_id = {r["id"]: r for r in rows}
    for rid in ("dcs-compound-dictionary", "morphology-giveback-candidates"):
        assert by_id[rid]["layer_status"] == "active"
        assert by_id[rid]["consumers"], "%s must name its consumer" % rid


def test_backfill_check_is_green():
    result = subprocess.run([sys.executable, str(BACKFILL), "--check"],
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "152/152" in result.stdout
