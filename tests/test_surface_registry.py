"""Generated-surface registry gate (W1B / H2342).

Proves:
1. the live registry loads and validates clean;
2. every required field is enforced (missing/empty → fail);
3. builders must be owned paths or declared non-path prefixes;
4. acceptance_command is mandatory;
5. dictionary-payload surfaces must name the shared query/serializer;
6. the CLI exits non-zero on a broken registry.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from kosha.surfaces import (
    REQUIRED_FIELDS,
    default_registry_path,
    load_registry,
    validate_registry,
    validate_surface,
)

REPO = Path(__file__).resolve().parent.parent
REGISTRY = default_registry_path(REPO)


@pytest.fixture(scope="module")
def registry_data() -> dict:
    return load_registry(REGISTRY)


@pytest.fixture(scope="module")
def surfaces(registry_data) -> list[dict]:
    return registry_data["surfaces"]


def test_live_registry_validates_clean(registry_data):
    report = validate_registry(registry_data, path=REGISTRY, repo_root=REPO)
    assert report.ok, [str(e) for e in report.errors]
    assert report.surface_count >= 10, "registry must cover the live product surfaces"


def test_required_fields_are_complete():
    expected = {
        "id",
        "title",
        "audience",
        "source_datasets",
        "builder",
        "output_paths",
        "output_class",
        "rights_tier",
        "acceptance_command",
        "deploy_owner",
        "rollback_method",
    }
    assert set(REQUIRED_FIELDS) == expected


def test_ids_unique(surfaces):
    ids = [s["id"] for s in surfaces]
    assert len(ids) == len(set(ids)), "duplicate surface ids"


def test_dictionary_payload_surfaces_share_query_serializer(surfaces):
    dict_surfaces = [s for s in surfaces if s.get("kind") == "dictionary-payload"]
    assert dict_surfaces, "expected at least the API/static/SSR dictionary surfaces"
    for s in dict_surfaces:
        assert s["query_module"] == "kosha.api.repository"
        assert s["serializer_module"] == "kosha.api.serializer"


def test_missing_required_field_fails():
    good = {
        "id": "demo",
        "title": "Demo",
        "audience": "testers",
        "source_datasets": ["none"],
        "builder": "hand-maintained:demo.html",
        "output_paths": ["demo.html"],
        "output_class": "committed",
        "rights_tier": "public",
        "acceptance_command": "true",
        "deploy_owner": "test",
        "rollback_method": "revert",
    }
    assert not validate_surface(good, repo_root=REPO)

    for key in REQUIRED_FIELDS:
        broken = dict(good)
        del broken[key]
        errs = validate_surface(broken, repo_root=REPO)
        assert any(key in e.message for e in errs), f"expected failure for missing {key}"


def test_empty_acceptance_command_fails():
    row = {
        "id": "demo",
        "title": "Demo",
        "audience": "testers",
        "source_datasets": ["none"],
        "builder": "hand-maintained:demo.html",
        "output_paths": ["demo.html"],
        "output_class": "committed",
        "rights_tier": "public",
        "acceptance_command": "   ",
        "deploy_owner": "test",
        "rollback_method": "revert",
    }
    errs = validate_surface(row, repo_root=REPO)
    assert any("acceptance_command" in e.message for e in errs)


def test_unowned_builder_fails():
    row = {
        "id": "demo",
        "title": "Demo",
        "audience": "testers",
        "source_datasets": ["none"],
        "builder": "scripts/does_not_exist_xyz.py",
        "output_paths": ["demo.html"],
        "output_class": "committed",
        "rights_tier": "public",
        "acceptance_command": "true",
        "deploy_owner": "test",
        "rollback_method": "revert",
    }
    errs = validate_surface(row, repo_root=REPO)
    assert any("builder" in e.message for e in errs)


def test_dictionary_payload_without_shared_modules_fails():
    row = {
        "id": "demo-dict",
        "title": "Demo dict",
        "audience": "testers",
        "kind": "dictionary-payload",
        "source_datasets": ["core-db"],
        "builder": "app/main.py",
        "output_paths": ["/api/v1/demo"],
        "output_class": "runtime",
        "rights_tier": "public",
        "acceptance_command": "true",
        "deploy_owner": "test",
        "rollback_method": "revert",
    }
    errs = validate_surface(row, repo_root=REPO)
    assert any("query_module" in e.message for e in errs)
    assert any("serializer_module" in e.message for e in errs)


def test_registry_with_broken_row_fails(registry_data, tmp_path):
    data = copy.deepcopy(registry_data)
    data["surfaces"][0] = dict(data["surfaces"][0], acceptance_command="")
    broken_path = tmp_path / "surfaces.json"
    broken_path.write_text(json.dumps(data), encoding="utf-8")
    report = validate_registry(data, path=broken_path, repo_root=REPO)
    assert not report.ok
    assert any("acceptance_command" in e.message for e in report.errors)


def test_cli_exits_zero_on_live_registry():
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "validate_surfaces.py")],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "OK:" in proc.stdout


def test_cli_exits_nonzero_on_broken_registry(registry_data, tmp_path):
    data = copy.deepcopy(registry_data)
    data["surfaces"][0] = dict(data["surfaces"][0], builder="scripts/nope_missing.py")
    broken = tmp_path / "surfaces.json"
    broken.write_text(json.dumps(data), encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "validate_surfaces.py"),
            "--path",
            str(broken),
            "--repo-root",
            str(REPO),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode != 0
    assert "FAIL:" in proc.stderr


def test_core_dictionary_surfaces_present(surfaces):
    ids = {s["id"] for s in surfaces}
    for required in (
        "api-v1-lemma",
        "api-v1-datasets",
        "salt-dicts-facade",
        "ssr-word-page",
        "static-cards",
        "static-word-pages",
        "directory-page",
        "docs-site",
        "ui-svelte-spa",
    ):
        assert required in ids, f"missing live surface row: {required}"
