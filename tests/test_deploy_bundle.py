"""W1D deployment bundle recipe + local assemble (H2344)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from kosha.deploy.bundle import (  # noqa: E402
    AssembleError,
    assemble_bundle,
    default_recipe_path,
    load_recipe,
    validate_recipe,
)


def test_committed_recipe_validates():
    path = default_recipe_path(ROOT)
    assert path.is_file(), "data/manifest/deploy_bundle.json must be committed"
    data = load_recipe(path)
    report = validate_recipe(data, recipe_path=path)
    assert report.ok, report.errors
    assert report.component_count >= 5
    assert data["schema"] == "kosha-deploy-bundle-v1"
    assert "serve_command" in data["runtime"]
    assert "restore_steps" in data["rollback"]


def test_invalid_schema_fails():
    data = load_recipe(default_recipe_path(ROOT))
    data = dict(data)
    data["schema"] = "wrong"
    report = validate_recipe(data)
    assert not report.ok
    assert any("schema" in e for e in report.errors)


def test_assemble_fixture_profile(tmp_path: Path):
    """Assemble against whatever code tree is present; fixture DB optional.

    Required code/docs paths always exist in the checkout. The core DB is
    required — create a tiny placeholder when the real fixture is absent so
    the unit test does not depend on a prior build_db run.
    """
    fixture = ROOT / "data" / "db" / "kosha_fixture.db"
    if not fixture.is_file():
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_bytes(b"SQLite format 3\x00fixture-placeholder-for-hash\n")
        created = True
    else:
        created = False

    try:
        out = tmp_path / "bundle"
        report = assemble_bundle(
            repo_root=ROOT,
            out_dir=out,
            profile="fixture",
        )
        assert report.ok, report.errors
        assert report.files_hashed > 0
        identity = out / "BUNDLE_IDENTITY.json"
        manifest = out / "BUNDLE_MANIFEST.json"
        assert identity.is_file()
        assert manifest.is_file()
        ident = json.loads(identity.read_text(encoding="utf-8"))
        assert ident["bundle_id"] == "kosha-public-api-v1"
        assert ident["profile"] == "fixture"
        assert ident["payload_file_count"] == report.files_hashed
        # Fixture rewrite: payload must not require production kosha.db name.
        man = json.loads(manifest.read_text(encoding="utf-8"))
        assert man["fence"]["production_deploy"] is False
        assert man["fence"]["agent_may_ssh"] is False
        # At least one digest under app/ or src/
        assert any(
            k.startswith("app/") or k.startswith("src/")
            for k in man["digests_sha256"]
        )
    finally:
        if created and fixture.is_file() and fixture.stat().st_size < 200:
            fixture.unlink(missing_ok=True)


def test_production_secret_env_keys_are_labelled():
    data = load_recipe(default_recipe_path(ROOT))
    env = data["env"]
    assert env["FTP_PASS"] == "production-only-secret"
    assert env["HISTORY_IP_SALT"] == "production-only-secret"
    assert env["KOSHA_CORE_DB_PATH"] == "required"


def test_load_recipe_rejects_non_object(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("[]\n", encoding="utf-8")
    with pytest.raises(AssembleError):
        load_recipe(bad)
