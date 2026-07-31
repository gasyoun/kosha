"""kosha — citation-archive validation (W0C item 7, H1945).

D9 mounts immutable citation archives locally, and R1 makes a promise about
them: a sense id minted in 2026 must still resolve in 2028, against the release
it names, in a browser. Everything that promise depends on is configuration —
where the archive is mounted, whether its bytes are the released bytes, and
what host the citation URL points at — and until W0C none of it was checked.
The archive was simply read if present and reported "not archived" if not, which
is the same answer a *misconfigured mount* gives.

This module turns each of those into a check with a verdict. It is deliberately
read-only and offline: it verifies what is on disk against what the release
metadata claims, and never fetches the release to compare. Reaching the network
to validate a citation would make the check unavailable exactly when the network
is (RISKS.md R12).

The metadata file is `release.json` beside the dump:

    {"version": "1.2.0", "sha256": "…", "senses": 12345}

Absent metadata is reported as `unverified`, not as a failure — most local
development archives have never had any — but a *present* file that disagrees
with the bytes is a hard failure, because that is corruption or a swap.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from kosha.cite import release_asset_url
from kosha.settings import Settings, get_settings

#: Hosts a citation URL must never be built on (RISKS.md R5). The deployment
#: host is where the service happens to run today; a citation minted against it
#: dies with the deployment. Kept as a check, not a comment, because the
#: comment already existed and the value still has to be set correctly by hand.
DEPLOYMENT_HOSTS = frozenset({"samskrtam.ru", "www.samskrtam.ru"})

METADATA_NAME = "release.json"
DUMP_NAME = "senses.sqlite"


@dataclass
class Check:
    """One verdict. `ok=False` is a failure; `ok=True` with a note is a pass
    that a human may still want to read."""

    name: str
    ok: bool
    detail: str


@dataclass
class ArchiveReport:
    archive_dir: Path
    versions: list[str] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    def failures(self) -> list[Check]:
        return [check for check in self.checks if not check.ok]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_public_base(public_base: str) -> Check:
    """R1/R5 — the citation host must be absolute, http(s), and not the
    deployment host."""
    parsed = urlparse(public_base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return Check(
            "public_base",
            False,
            f"{public_base!r} is not an absolute http(s) URL; citation URLs "
            "built on it would not resolve in a browser",
        )
    host = parsed.netloc.split(":")[0].lower()
    if host in DEPLOYMENT_HOSTS:
        return Check(
            "public_base",
            False,
            f"{host} is the deployment host — R5 forbids citations that depend "
            "on where the live server runs; point KOSHA_PUBLIC_BASE at the "
            "durable API mirror",
        )
    return Check("public_base", True, f"citations resolve against {public_base}")


def validate_release_asset(version: str) -> Check:
    """A citable version must mint a durable release-asset permalink; a `-dev`
    build must mint none. Both directions matter — a `-dev` build that produced
    an asset URL would be advertising a download that will never exist."""
    url = release_asset_url(version)
    if version.endswith("-dev"):
        if url is not None:
            return Check(
                "release_asset",
                False,
                f"dev build {version!r} minted {url!r}; dev builds ship no "
                "release and are explicitly not citable",
            )
        return Check("release_asset", True, f"{version} is a dev build, not citable")
    if not url or not url.startswith("https://"):
        return Check("release_asset", False, f"{version} minted no https asset URL")
    return Check("release_asset", True, url)


def validate_version(archive_dir: Path, version: str) -> list[Check]:
    """Structure, metadata agreement, and openability of one archived version."""
    checks: list[Check] = []
    dump = archive_dir / version / DUMP_NAME
    if not dump.is_file():
        return [Check(f"{version}/dump", False, f"missing {dump}")]

    metadata_path = archive_dir / version / METADATA_NAME
    if not metadata_path.is_file():
        checks.append(
            Check(f"{version}/metadata", True,
                  f"no {METADATA_NAME}; checksum unverified (local archive)")
        )
    else:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            checks.append(Check(f"{version}/metadata", False, f"unreadable: {exc}"))
            metadata = None
        if metadata is not None:
            declared = metadata.get("sha256")
            if not declared:
                checks.append(
                    Check(f"{version}/checksum", False,
                          f"{METADATA_NAME} declares no sha256")
                )
            else:
                actual = _sha256(dump)
                checks.append(Check(
                    f"{version}/checksum",
                    actual == declared,
                    "matches" if actual == declared
                    else f"declared {declared}, on disk {actual} — the archive "
                         "is not the released bytes",
                ))
            if metadata.get("version") not in (None, version):
                checks.append(Check(
                    f"{version}/metadata", False,
                    f"{METADATA_NAME} names version {metadata['version']!r} but "
                    f"sits in {version}/ — one of the two is wrong",
                ))

    # Openability is a separate fact from existence: a truncated or non-SQLite
    # file passes `is_file()` and fails every citation that reaches it.
    try:
        con = sqlite3.connect(f"file:{dump}?mode=ro", uri=True)
        try:
            count = con.execute("SELECT COUNT(*) FROM archive").fetchone()[0]
        finally:
            con.close()
    except sqlite3.Error as exc:
        checks.append(Check(f"{version}/readable", False, f"{dump}: {exc}"))
    else:
        checks.append(Check(
            f"{version}/readable", count > 0,
            f"{count} archived senses" if count else "archive table is empty",
        ))
    checks.append(validate_release_asset(version))
    return checks


def mounted_versions(archive_dir: Path) -> list[str]:
    if not archive_dir.is_dir():
        return []
    return sorted(
        child.name for child in archive_dir.iterdir()
        if child.is_dir() and (child / DUMP_NAME).is_file()
    )


def validate_archive(settings: Settings | None = None) -> ArchiveReport:
    """Validate the whole mount: path, public base, and every archived version.

    An *empty* mount is not a failure — a fresh checkout has archived nothing —
    but it is reported, because "no archived versions" and "archive mounted and
    healthy" are answers a release gate must be able to tell apart.
    """
    settings = settings or get_settings()
    report = ArchiveReport(archive_dir=settings.archive_dir)
    report.checks.append(validate_public_base(settings.public_base))

    if not settings.archive_dir.exists():
        report.checks.append(Check(
            "archive_dir", True,
            f"{settings.archive_dir} does not exist; no version is archived on "
            "this instance (citations fall back to the release-asset URL)",
        ))
        return report

    if not settings.archive_dir.is_dir():
        report.checks.append(Check(
            "archive_dir", False,
            f"{settings.archive_dir} exists but is not a directory",
        ))
        return report

    report.versions = mounted_versions(settings.archive_dir)
    report.checks.append(Check(
        "archive_dir", True,
        f"{settings.archive_dir}: {len(report.versions)} archived version(s)",
    ))
    for version in report.versions:
        report.checks.extend(validate_version(settings.archive_dir, version))
    return report
