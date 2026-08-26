"""W2B / P-D6 — public dataset catalog over data/manifest/datasets.json.

Fixture-tier: no kosha.db. Proves restricted/intermediate rows never appear,
unknown and restricted ids share one 404, schema keys stay stable, and the
live manifest is not a silent empty catalog.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))

from kosha.api import catalog  # noqa: E402
from kosha.api.catalog import (  # noqa: E402
    EMPTY_REASON,
    RECORD_REQUIRED_KEYS,
    SCHEMA,
    get_public_record,
    list_payload,
    load_manifest,
    public_records,
)

from app.main import app  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "catalog" / "datasets.json"
RESTRICTED_LEAK = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
RESTRICTED_TOKEN = "LEAK-TOKEN-RESTRICTED-CHECKSUM"
INTERMEDIATE_HASH = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"

client = TestClient(app)


@pytest.fixture
def fixture_manifest() -> dict:
    return load_manifest(FIXTURE)


def test_fixture_list_contains_only_public_ids(fixture_manifest):
    records = public_records(fixture_manifest)
    ids = [r["id"] for r in records]
    assert ids == ["public-released", "public-unreleased"]
    assert "secret-restricted" not in ids
    assert "working-intermediate" not in ids


def test_fixture_public_record_has_required_fields(fixture_manifest):
    rec = get_public_record(fixture_manifest, "public-released")
    assert rec is not None
    for key in RECORD_REQUIRED_KEYS:
        assert key in rec, f"missing locked field {key}"
    assert rec["version"] == "data-v0.1.0"
    assert rec["license"].startswith("CC BY-SA 4.0")
    assert rec["rights"]["tier"] == "public"
    assert rec["rights"]["pointer"].startswith("http")
    assert rec["download"] == (
        "https://github.com/gasyoun/kosha/releases/download/"
        "data-v0.1.0/public_released.tsv"
    )
    assert rec["locator"]["release_asset"] == "public_released.tsv"
    assert rec["checksum"]["sha256"].startswith("aaaa")


def test_restricted_and_intermediate_resolve_to_none(fixture_manifest):
    assert get_public_record(fixture_manifest, "secret-restricted") is None
    assert get_public_record(fixture_manifest, "working-intermediate") is None
    assert get_public_record(fixture_manifest, "does-not-exist") is None


def test_empty_catalog_states_a_reason():
    empty = {
        "manifest_version": "0.0.0",
        "license_public_tier": "CC BY-SA 4.0",
        "datasets": [
            {
                "id": "only-restricted",
                "title": "hidden",
                "tier": "restricted",
                "in_release": "not-applicable",
            }
        ],
    }
    body = list_payload(empty, public_records(empty))
    assert body["count"] == 0
    assert body["datasets"] == []
    assert body["empty_reason"] == EMPTY_REASON


def test_http_list_and_get_use_the_fixture(monkeypatch):
    monkeypatch.setattr(catalog, "default_manifest_path", lambda: FIXTURE)

    listed = client.get("/api/v1/datasets")
    assert listed.status_code == 200
    body = listed.json()
    assert body["schema"] == SCHEMA
    assert body["count"] == 2
    assert [d["id"] for d in body["datasets"]] == [
        "public-released",
        "public-unreleased",
    ]
    dumped = json.dumps(body)
    assert RESTRICTED_LEAK not in dumped
    assert RESTRICTED_TOKEN not in dumped
    assert INTERMEDIATE_HASH not in dumped
    assert "secret-restricted" not in dumped

    found = client.get("/api/v1/datasets/public-released")
    assert found.status_code == 200
    rec = found.json()
    assert rec["id"] == "public-released"
    assert rec["checksum"]["sha256"].startswith("aaaa")


@pytest.mark.parametrize(
    "dataset_id",
    ["secret-restricted", "working-intermediate", "does-not-exist"],
)
def test_http_non_public_is_indistinguishable_404(monkeypatch, dataset_id):
    monkeypatch.setattr(catalog, "default_manifest_path", lambda: FIXTURE)
    r = client.get(f"/api/v1/datasets/{dataset_id}")
    assert r.status_code == 404
    err = r.json()["error"]
    assert err["code"] == "dataset_not_found"
    assert err["message"] == "No public dataset with that id"
    text = json.dumps(r.json())
    assert RESTRICTED_LEAK not in text
    assert RESTRICTED_TOKEN not in text
    assert INTERMEDIATE_HASH not in text


def test_restricted_and_unknown_404_bodies_are_identical(monkeypatch):
    monkeypatch.setattr(catalog, "default_manifest_path", lambda: FIXTURE)
    restricted = client.get("/api/v1/datasets/secret-restricted").json()
    unknown = client.get("/api/v1/datasets/does-not-exist").json()
    intermediate = client.get("/api/v1/datasets/working-intermediate").json()
    assert restricted == unknown == intermediate


def test_live_manifest_is_not_a_silent_empty_catalog():
    """Acceptance fail = empty catalog with no reason on the real file."""
    live = load_manifest()
    records = public_records(live)
    body = list_payload(live, records)
    assert body["count"] == len(records)
    assert body["count"] > 0, "live datasets.json has public rows; empty catalog is a bug"
    assert "empty_reason" not in body
    assert all(r["rights"]["tier"] == "public" for r in records)
    ids = {r["id"] for r in records}
    assert "mw-roots" in ids
    assert "corpus-lexicon" not in ids


def test_live_restricted_id_404s_without_leaking_checksum(monkeypatch):
    # Live default path — do not monkeypatch to the fixture.
    r = client.get("/api/v1/datasets/corpus-lexicon")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "dataset_not_found"
    text = json.dumps(r.json())
    assert "9f3d852f1f1424c275af2cc1823dab1b561e649320e597d3cab013068ccc4072" not in text


def test_live_public_id_round_trips():
    r = client.get("/api/v1/datasets/mw-roots")
    assert r.status_code == 200
    rec = r.json()
    assert rec["id"] == "mw-roots"
    assert rec["version"] == "data-v0.5.0"
    assert rec["download"].endswith("/data-v0.5.0/mw_roots.tsv")
    for key in RECORD_REQUIRED_KEYS:
        assert key in rec


def test_catalog_paths_are_in_openapi():
    paths = app.openapi()["paths"]
    assert "/api/v1/datasets" in paths
    assert "/api/v1/datasets/{dataset_id}" in paths


def test_schema_stability_rejects_a_dropped_required_field(fixture_manifest):
    rec = get_public_record(fixture_manifest, "public-released")
    assert rec is not None
    missing = dict(rec)
    del missing["locator"]
    assert any(key not in missing for key in RECORD_REQUIRED_KEYS)
