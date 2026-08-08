"""Versioned deployment-bundle recipe validation and local assembly (W1D).

A **recipe** (`data/manifest/deploy_bundle.json`) declares what files, env
keys, DB paths, and archive mounts belong in a deployable unit. Assembly
copies (or hard-links when possible) those paths into an output directory and
writes a digests manifest. Nothing here opens a network connection or reads
production credentials.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA = "kosha-deploy-bundle-v1"
REQUIRED_TOP = (
    "manifest_version",
    "schema",
    "bundle_id",
    "components",
    "env",
    "runtime",
    "rollback",
)
REQUIRED_COMPONENT = ("id", "kind", "paths", "required")
COMPONENT_KINDS = frozenset(
    {
        "code",
        "data",
        "static",
        "config-template",
        "docs",
        "script",
    }
)
ENV_SCOPES = frozenset({"required", "optional", "production-only-secret"})


class AssembleError(RuntimeError):
    """Recipe invalid or a required component is missing on disk."""


@dataclass
class BundleReport:
    """Result of validate + optional assemble."""

    recipe_path: Path
    bundle_id: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    component_count: int = 0
    files_hashed: int = 0
    out_dir: Path | None = None
    digests: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def _infer_repo_root() -> Path:
    # src/kosha/deploy/bundle.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def default_recipe_path(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else _infer_repo_root()
    return root / "data" / "manifest" / "deploy_bundle.json"


def load_recipe(path: Path | None = None) -> dict[str, Any]:
    recipe_path = path if path is not None else default_recipe_path()
    text = recipe_path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise AssembleError(f"recipe root must be an object: {recipe_path}")
    return data


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_recipe(
    data: Mapping[str, Any],
    *,
    recipe_path: Path | None = None,
) -> BundleReport:
    """Structural validation only — does not require files on disk."""
    path = recipe_path if recipe_path is not None else default_recipe_path()
    report = BundleReport(
        recipe_path=path,
        bundle_id=str(data.get("bundle_id") or ""),
    )

    for key in REQUIRED_TOP:
        if key not in data:
            report.errors.append(f"missing top-level field: {key}")
    if data.get("schema") != SCHEMA:
        report.errors.append(
            f"schema must be {SCHEMA!r}, got {data.get('schema')!r}"
        )
    if not _nonempty_str(data.get("manifest_version")):
        report.errors.append("manifest_version must be a non-empty string")
    if not _nonempty_str(data.get("bundle_id")):
        report.errors.append("bundle_id must be a non-empty string")

    components = data.get("components")
    if not isinstance(components, list) or not components:
        report.errors.append("components must be a non-empty list")
        return report

    report.component_count = len(components)
    seen_ids: set[str] = set()
    for i, comp in enumerate(components):
        prefix = f"components[{i}]"
        if not isinstance(comp, dict):
            report.errors.append(f"{prefix}: must be an object")
            continue
        for field_name in REQUIRED_COMPONENT:
            if field_name not in comp:
                report.errors.append(f"{prefix}: missing {field_name}")
        cid = comp.get("id")
        if not _nonempty_str(cid):
            report.errors.append(f"{prefix}: id must be non-empty")
        elif cid in seen_ids:
            report.errors.append(f"{prefix}: duplicate id {cid!r}")
        else:
            seen_ids.add(str(cid))
        kind = comp.get("kind")
        if kind not in COMPONENT_KINDS:
            report.errors.append(
                f"{prefix}: kind must be one of {sorted(COMPONENT_KINDS)}, "
                f"got {kind!r}"
            )
        paths = comp.get("paths")
        if not isinstance(paths, list) or not paths:
            report.errors.append(f"{prefix}: paths must be a non-empty list")
        elif not all(_nonempty_str(p) for p in paths):
            report.errors.append(f"{prefix}: every path must be a non-empty string")
        if not isinstance(comp.get("required"), bool):
            report.errors.append(f"{prefix}: required must be a boolean")

    env = data.get("env")
    if not isinstance(env, dict):
        report.errors.append("env must be an object of key → scope")
    else:
        for key, scope in env.items():
            if not _nonempty_str(key):
                report.errors.append("env keys must be non-empty strings")
            if scope not in ENV_SCOPES:
                report.errors.append(
                    f"env[{key!r}]: scope must be one of "
                    f"{sorted(ENV_SCOPES)}, got {scope!r}"
                )

    runtime = data.get("runtime")
    if not isinstance(runtime, dict):
        report.errors.append("runtime must be an object")
    else:
        for need in ("serve_command", "health_path", "ready_path", "port"):
            if need not in runtime:
                report.errors.append(f"runtime missing {need}")

    rollback = data.get("rollback")
    if not isinstance(rollback, dict):
        report.errors.append("rollback must be an object")
    else:
        for need in ("previous_bundle_identity", "restore_steps", "verify_after"):
            if need not in rollback:
                report.errors.append(f"rollback missing {need}")

    return report


def sha256_of(path: Path, *, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _iter_files(root: Path, rel: str) -> Iterable[Path]:
    target = root / rel
    if target.is_file():
        yield target
        return
    if target.is_dir():
        for path in sorted(target.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                if path.suffix == ".pyc":
                    continue
                yield path
        return
    # missing path — caller decides required vs optional


def assemble_bundle(
    *,
    repo_root: Path | None = None,
    recipe_path: Path | None = None,
    out_dir: Path | None = None,
    profile: str = "fixture",
    copy_mode: str = "copy",
) -> BundleReport:
    """Assemble a local bundle directory with digests.

    ``profile``:
      * ``fixture`` — rewrite data DB paths to the fixture DB under data/db/
      * ``staged`` — use recipe paths as written (local non-prod stage)

    Never contacts production hosts. Credentials are never copied: only the
    committed ``.env.example`` template may appear under config-template.
    """
    root = repo_root if repo_root is not None else _infer_repo_root()
    rpath = recipe_path if recipe_path is not None else default_recipe_path(root)
    data = load_recipe(rpath)
    report = validate_recipe(data, recipe_path=rpath)
    if not report.ok:
        return report

    if profile not in {"fixture", "staged"}:
        report.errors.append(f"unknown profile {profile!r}; use fixture|staged")
        return report

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if out_dir is None:
        out_dir = root / "data" / "deploy_bundles" / f"{data['bundle_id']}-{stamp}"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    digests: dict[str, str] = {}
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for comp in data["components"]:
        cid = comp["id"]
        required = bool(comp["required"])
        for rel in comp["paths"]:
            # Fixture profile: map production-shaped core DB path to fixture.
            use_rel = rel
            if profile == "fixture" and rel in {
                "data/db/kosha.db",
                "data/db/core.db",
            }:
                use_rel = "data/db/kosha_fixture.db"

            target = root / use_rel
            if not target.exists():
                msg = f"{cid}: missing path {use_rel}"
                if required:
                    missing_required.append(msg)
                else:
                    missing_optional.append(msg)
                    report.warnings.append(msg)
                continue

            for src in _iter_files(root, use_rel):
                rel_out = src.relative_to(root).as_posix()
                dest = out_dir / "payload" / rel_out
                dest.parent.mkdir(parents=True, exist_ok=True)
                if copy_mode == "copy":
                    shutil.copy2(src, dest)
                else:
                    # hardlink when same filesystem, else copy
                    try:
                        os.link(src, dest)
                    except OSError:
                        shutil.copy2(src, dest)
                digest = sha256_of(dest)
                digests[rel_out] = digest
                report.files_hashed += 1

    if missing_required:
        report.errors.extend(missing_required)
        # Leave a partial tree for debugging but mark failure.
        report.out_dir = out_dir
        report.digests = digests
        return report

    manifest = {
        "schema": SCHEMA,
        "bundle_id": data["bundle_id"],
        "assembled_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "recipe_manifest_version": data["manifest_version"],
        "repo_root_note": "payload paths are relative to the kosha repo root",
        "component_ids": [c["id"] for c in data["components"]],
        "file_count": len(digests),
        "digests_sha256": digests,
        "env": data["env"],
        "runtime": data["runtime"],
        "rollback": data["rollback"],
        "fence": {
            "production_credentials": False,
            "production_deploy": False,
            "agent_may_ssh": False,
        },
    }
    man_path = out_dir / "BUNDLE_MANIFEST.json"
    man_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    digests["BUNDLE_MANIFEST.json"] = sha256_of(man_path)

    # Rewrite digests into the written manifest so the identity file is
    # self-describing (manifest hash of itself is excluded — identity is the
    # digests map of payload files + top-level identity stamp).
    identity = {
        "bundle_id": data["bundle_id"],
        "assembled_at": manifest["assembled_at"],
        "profile": profile,
        "payload_file_count": report.files_hashed,
        "payload_digests_sha256": {
            k: v for k, v in digests.items() if k != "BUNDLE_MANIFEST.json"
        },
        "previous_bundle_identity": data["rollback"].get(
            "previous_bundle_identity"
        ),
    }
    id_path = out_dir / "BUNDLE_IDENTITY.json"
    id_path.write_text(
        json.dumps(identity, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report.out_dir = out_dir
    report.digests = digests
    report.warnings.extend(missing_optional)
    return report
