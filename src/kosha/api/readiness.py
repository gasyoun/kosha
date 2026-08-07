"""kosha — readiness checks (W1C, H2343).

Ops probe distinct from liveness (`GET /health` always answers "process up").
This module answers "is this instance fit to serve dictionary traffic?" by
checking the four surfaces the public product needs:

1. **core database** — must open through the multi-DB storage facade;
2. **attached layers** — inflections / layers report present or absent
   (absence is not a hard fail while the monolith remains the default);
3. **data version** — readable from `meta`; fails closed when an expected
   version is configured and the store disagrees;
4. **citation archives** — reuses `kosha.api.archive.validate_archive`
   (empty mount is unconfigured, not fail; corrupt mounted release is fail);
5. **optional writables** — history/auth report `disabled` when the D10 flag
   is off, never look "ready" while unmounted.

The HTTP layer stays thin: one function builds a JSON-serialisable report;
the route only maps `ready → 200 / 503`. No SQL and no Salt serialization
live here — those stay in `repository` / `serializer`.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from kosha.api.archive import validate_archive
from kosha.api.repository import data_version as read_data_version
from kosha.feature_gates import history_enabled
from kosha.query.connection import (
    StorageFacadeError,
    attached_aliases,
    open_query_connection,
)
from kosha.settings import Settings, get_settings

CheckStatus = Literal["ok", "fail", "disabled", "absent", "unconfigured"]


@dataclass
class ReadinessCheck:
    """One named probe result. `required=True` failures flip overall ready."""

    name: str
    status: CheckStatus
    detail: str
    required: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "required": self.required,
        }


@dataclass
class ReadinessReport:
    ready: bool
    data_version: str | None
    checks: list[ReadinessCheck] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "ready" if self.ready else "not_ready"

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "status": self.status,
            "data_version": self.data_version,
            "checks": [c.as_dict() for c in self.checks],
        }

    def http_status(self) -> int:
        """200 when ready; 503 when not — never 500 for a correctly disabled
        optional subsystem."""
        return 200 if self.ready else 503


def _check_core_and_layers(
    settings: Settings,
) -> tuple[list[ReadinessCheck], sqlite3.Connection | None, str | None]:
    """Open the facade; return checks, open connection (caller closes), version."""
    checks: list[ReadinessCheck] = []
    core = settings.core_db

    if not core.is_file():
        checks.append(
            ReadinessCheck(
                name="core_db",
                status="fail",
                detail="core database file is missing",
                required=True,
            )
        )
        # Optional attaches are still reportable without opening.
        checks.extend(_layer_file_checks(settings, aliases={}))
        return checks, None, None

    try:
        con = open_query_connection(settings)
    except StorageFacadeError as exc:
        checks.append(
            ReadinessCheck(
                name="core_db",
                status="fail",
                detail=f"storage facade refused to open: {exc}",
                required=True,
            )
        )
        checks.extend(_layer_file_checks(settings, aliases={}))
        return checks, None, None
    except sqlite3.Error as exc:
        checks.append(
            ReadinessCheck(
                name="core_db",
                status="fail",
                detail=f"sqlite error opening core: {exc}",
                required=True,
            )
        )
        checks.extend(_layer_file_checks(settings, aliases={}))
        return checks, None, None

    checks.append(
        ReadinessCheck(
            name="core_db",
            status="ok",
            detail="core database openable via storage facade",
            required=True,
        )
    )

    aliases = attached_aliases(con)
    checks.extend(_layer_file_checks(settings, aliases=aliases))

    try:
        version = read_data_version(con)
    except sqlite3.Error as exc:
        checks.append(
            ReadinessCheck(
                name="data_version",
                status="fail",
                detail=f"meta.data_version unreadable: {exc}",
                required=True,
            )
        )
        return checks, con, None

    if not version or version == "0.0.0-dev":
        # Fixture / empty meta: still report the value; only fail when an
        # expected version is configured (checked separately).
        checks.append(
            ReadinessCheck(
                name="data_version",
                status="ok",
                detail=f"store reports {version!r}",
                required=True,
            )
        )
    else:
        checks.append(
            ReadinessCheck(
                name="data_version",
                status="ok",
                detail=f"store reports {version!r}",
                required=True,
            )
        )
    return checks, con, version


def _layer_file_checks(
    settings: Settings, *, aliases: dict[str, str]
) -> list[ReadinessCheck]:
    """Inflections and layers are optional until the physical split lands.

    Presence of the file without attach (wrong schema) is still `absent` —
    the facade only attaches when expected tables exist. Hard fail is reserved
    for a future gate that requires the split; W1C only reports state.
    """
    out: list[ReadinessCheck] = []
    for name, path, alias in (
        ("inflections_db", settings.inflections_db, "inflections"),
        ("layers_db", settings.layers_db, "layers"),
    ):
        if alias in aliases:
            out.append(
                ReadinessCheck(
                    name=name,
                    status="ok",
                    detail=f"{alias} attached",
                    required=False,
                )
            )
        elif path.is_file():
            out.append(
                ReadinessCheck(
                    name=name,
                    status="absent",
                    detail=(
                        f"{alias} file present but not attached "
                        "(no expected tables, or same path as core)"
                    ),
                    required=False,
                )
            )
        else:
            out.append(
                ReadinessCheck(
                    name=name,
                    status="absent",
                    detail=f"{alias} not present (monolith / optional layer)",
                    required=False,
                )
            )
    return out


def _check_expected_version(
    settings: Settings, actual: str | None
) -> ReadinessCheck | None:
    """When KOSHA_EXPECTED_DATA_VERSION is set, mismatch is a hard fail."""
    expected = settings.expected_data_version
    if expected is None:
        return None
    if actual is None:
        return ReadinessCheck(
            name="data_version_match",
            status="fail",
            detail=f"expected {expected!r} but store version is unreadable",
            required=True,
        )
    if actual != expected:
        return ReadinessCheck(
            name="data_version_match",
            status="fail",
            detail=f"expected {expected!r}, store has {actual!r}",
            required=True,
        )
    return ReadinessCheck(
        name="data_version_match",
        status="ok",
        detail=f"matches expected {expected!r}",
        required=True,
    )


def _check_archives(settings: Settings) -> ReadinessCheck:
    """Citation archives: unconfigured OK; corrupt mounted release fails closed."""
    report = validate_archive(settings)
    if not settings.archive_dir.exists():
        return ReadinessCheck(
            name="citation_archives",
            status="unconfigured",
            detail="archive mount does not exist; citations fall back to release-asset URLs",
            required=False,
        )
    if not settings.archive_dir.is_dir():
        return ReadinessCheck(
            name="citation_archives",
            status="fail",
            detail="archive mount path exists but is not a directory",
            required=True,
        )
    if not report.versions:
        return ReadinessCheck(
            name="citation_archives",
            status="unconfigured",
            detail="archive mount is empty; no version is archived on this instance",
            required=False,
        )
    failures = report.failures()
    if failures:
        first = failures[0]
        return ReadinessCheck(
            name="citation_archives",
            status="fail",
            detail=f"{first.name}: {first.detail}",
            required=True,
        )
    return ReadinessCheck(
        name="citation_archives",
        status="ok",
        detail=f"{len(report.versions)} archived version(s) validated",
        required=False,
    )


def _check_history(settings: Settings) -> ReadinessCheck:
    """Optional writable: disabled when flag off — never looks ready unmounted."""
    if not history_enabled(settings):
        return ReadinessCheck(
            name="history",
            status="disabled",
            detail="KOSHA_HISTORY_ENABLED is false; history/auth/stats not mounted",
            required=False,
        )

    # Flag on: history must be openable as a writable SQLite file. We do not
    # create it here — production mounts a prepared store.
    path = settings.history_db
    if not path.is_file():
        return ReadinessCheck(
            name="history",
            status="fail",
            detail="history enabled but history database file is missing",
            required=True,
        )
    try:
        con = sqlite3.connect(str(path.resolve()))
        try:
            con.execute("SELECT 1").fetchone()
        finally:
            con.close()
    except sqlite3.Error as exc:
        return ReadinessCheck(
            name="history",
            status="fail",
            detail=f"history enabled but database unreadable: {exc}",
            required=True,
        )
    return ReadinessCheck(
        name="history",
        status="ok",
        detail="history enabled and database openable",
        required=True,
    )


def assess_readiness(settings: Settings | None = None) -> ReadinessReport:
    """Run every readiness probe and assemble the report.

    Fail-closed: any *required* check with status ``fail`` yields ``ready=False``.
    Optional absences and ``disabled`` / ``unconfigured`` never flip readiness.
    """
    settings = settings or get_settings()
    checks, con, version = _check_core_and_layers(settings)
    try:
        match = _check_expected_version(settings, version)
        if match is not None:
            checks.append(match)
        checks.append(_check_archives(settings))
        checks.append(_check_history(settings))
    finally:
        if con is not None:
            con.close()

    # Fail-closed: any required check with status fail → not ready.
    ready = not any(c.required and c.status == "fail" for c in checks)
    return ReadinessReport(ready=ready, data_version=version, checks=checks)


def readiness_payload(settings: Settings | None = None) -> tuple[dict[str, Any], int]:
    """JSON body + HTTP status for the thin route handler."""
    report = assess_readiness(settings)
    return report.as_dict(), report.http_status()
