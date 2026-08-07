"""Load and validate the generated-surface registry.

A surface row is valid only when every required field is present and non-empty,
closed vocabularies hold, the builder is owned (resolves under the repo or is a
declared runtime module), and an acceptance command is declared. Dictionary
payload surfaces must name the shared query/serializer modules so a new surface
cannot reintroduce mirrored payload code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

REQUIRED_FIELDS: tuple[str, ...] = (
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
)

OUTPUT_CLASSES = frozenset({"committed", "out-of-band", "runtime"})
RIGHTS_TIERS = frozenset({"public", "restricted"})
# Surfaces that emit Salt/entry payloads must declare shared consumers.
DICTIONARY_KINDS = frozenset({"dictionary-payload"})
SHARED_QUERY = "kosha.api.repository"
SHARED_SERIALIZER = "kosha.api.serializer"

# Builder values that are not filesystem paths (runtime services / hand pages).
NON_PATH_BUILDER_PREFIXES = (
    "runtime:",
    "hand-maintained:",
    "external:",
)


@dataclass
class SurfaceError:
    surface_id: str
    message: str

    def __str__(self) -> str:
        return f"{self.surface_id}: {self.message}"


@dataclass
class RegistryReport:
    path: Path
    surface_count: int = 0
    errors: list[SurfaceError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def default_registry_path(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else _infer_repo_root()
    return root / "data" / "manifest" / "surfaces.json"


def _infer_repo_root() -> Path:
    # src/kosha/surfaces/registry.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def load_registry(path: Path | None = None) -> dict[str, Any]:
    reg_path = path if path is not None else default_registry_path()
    text = reg_path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"registry root must be an object: {reg_path}")
    return data


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_str_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) > 0
        and all(_nonempty_str(item) for item in value)
    )


def _builder_is_owned(builder: str, repo_root: Path) -> str | None:
    """Return an error message if the builder is not owned, else None."""
    b = builder.strip()
    if not b:
        return "builder is empty"
    if any(b.startswith(p) for p in NON_PATH_BUILDER_PREFIXES):
        return None
    # Repo-relative path (scripts/…, app/…, src/…, ui/…)
    candidate = repo_root / b
    if candidate.exists():
        return None
    # Allow a module path style "package.module:attr" for installable code.
    if ":" in b and not b.startswith(("http://", "https://")):
        module_part = b.split(":", 1)[0]
        if module_part.startswith("kosha.") or module_part == "kosha":
            return None
    return (
        f"builder '{builder}' is not a repo path that exists and is not a "
        f"declared runtime/hand-maintained/external builder"
    )


def validate_surface(
    surface: dict[str, Any],
    *,
    repo_root: Path,
    known_ids: Iterable[str] | None = None,
) -> list[SurfaceError]:
    errors: list[SurfaceError] = []
    sid = surface.get("id") if isinstance(surface.get("id"), str) else "<missing-id>"

    if not isinstance(surface, dict):
        return [SurfaceError(sid, "surface row must be an object")]

    for key in REQUIRED_FIELDS:
        if key not in surface:
            errors.append(SurfaceError(sid, f"missing required field '{key}'"))

    if "id" in surface and not _nonempty_str(surface.get("id")):
        errors.append(SurfaceError(sid, "id must be a non-empty string"))
    if "title" in surface and not _nonempty_str(surface.get("title")):
        errors.append(SurfaceError(sid, "title must be a non-empty string"))
    if "audience" in surface and not _nonempty_str(surface.get("audience")):
        errors.append(SurfaceError(sid, "audience must be a non-empty string"))

    if "source_datasets" in surface and not _nonempty_str_list(
        surface.get("source_datasets")
    ):
        errors.append(
            SurfaceError(
                sid,
                "source_datasets must be a non-empty list of non-empty strings",
            )
        )

    if "builder" in surface:
        builder = surface.get("builder")
        if not _nonempty_str(builder):
            errors.append(SurfaceError(sid, "builder must be a non-empty string"))
        else:
            msg = _builder_is_owned(str(builder), repo_root)
            if msg:
                errors.append(SurfaceError(sid, msg))

    if "output_paths" in surface and not _nonempty_str_list(surface.get("output_paths")):
        errors.append(
            SurfaceError(
                sid,
                "output_paths must be a non-empty list of non-empty strings",
            )
        )

    if "output_class" in surface:
        oc = surface.get("output_class")
        if oc not in OUTPUT_CLASSES:
            errors.append(
                SurfaceError(
                    sid,
                    f"output_class '{oc}' not in {sorted(OUTPUT_CLASSES)}",
                )
            )

    if "rights_tier" in surface:
        rt = surface.get("rights_tier")
        if rt not in RIGHTS_TIERS:
            errors.append(
                SurfaceError(
                    sid,
                    f"rights_tier '{rt}' not in {sorted(RIGHTS_TIERS)}",
                )
            )

    if "acceptance_command" in surface and not _nonempty_str(
        surface.get("acceptance_command")
    ):
        errors.append(
            SurfaceError(sid, "acceptance_command must be a non-empty string")
        )

    if "deploy_owner" in surface and not _nonempty_str(surface.get("deploy_owner")):
        errors.append(SurfaceError(sid, "deploy_owner must be a non-empty string"))

    if "rollback_method" in surface and not _nonempty_str(
        surface.get("rollback_method")
    ):
        errors.append(SurfaceError(sid, "rollback_method must be a non-empty string"))

    kind = surface.get("kind")
    if kind in DICTIONARY_KINDS:
        if surface.get("query_module") != SHARED_QUERY:
            errors.append(
                SurfaceError(
                    sid,
                    f"dictionary-payload surfaces must set query_module="
                    f"'{SHARED_QUERY}' (shared query; no mirrored SQL)",
                )
            )
        if surface.get("serializer_module") != SHARED_SERIALIZER:
            errors.append(
                SurfaceError(
                    sid,
                    f"dictionary-payload surfaces must set serializer_module="
                    f"'{SHARED_SERIALIZER}' (shared serializer; no mirrored payload)",
                )
            )

    return errors


def validate_registry(
    data: dict[str, Any] | None = None,
    *,
    path: Path | None = None,
    repo_root: Path | None = None,
) -> RegistryReport:
    reg_path = path if path is not None else default_registry_path(repo_root)
    root = repo_root if repo_root is not None else reg_path.resolve().parents[2]
    report = RegistryReport(path=reg_path)

    if data is None:
        try:
            data = load_registry(reg_path)
        except FileNotFoundError:
            report.errors.append(
                SurfaceError("<registry>", f"registry file missing: {reg_path}")
            )
            return report
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            report.errors.append(
                SurfaceError("<registry>", f"cannot load registry: {exc}")
            )
            return report

    surfaces = data.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        report.errors.append(
            SurfaceError("<registry>", "surfaces must be a non-empty list")
        )
        return report

    report.surface_count = len(surfaces)
    seen: set[str] = set()
    for surface in surfaces:
        if not isinstance(surface, dict):
            report.errors.append(
                SurfaceError("<registry>", "each surface must be an object")
            )
            continue
        sid = surface.get("id")
        if isinstance(sid, str) and sid:
            if sid in seen:
                report.errors.append(SurfaceError(sid, "duplicate id"))
            seen.add(sid)
        report.errors.extend(validate_surface(surface, repo_root=root, known_ids=seen))

    return report
