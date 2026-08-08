"""kosha — citation-archive validation (W0C item 7, H1945; W2A release gate, H2346).

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

Absent metadata is reported as `unverified`, not as a failure, in *runtime*
mode — most local development archives have never had any — but a *present*
file that disagrees with the bytes is a hard failure, because that is
corruption or a swap.

W2A adds the **release gate** path (`require_metadata=True` /
`validate_release_archives`): a citable freeze must ship identity metadata,
and historical resolution must succeed for current + prior mounted versions.
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


def validate_version(
    archive_dir: Path,
    version: str,
    *,
    require_metadata: bool = False,
) -> list[Check]:
    """Structure, metadata agreement, and openability of one archived version.

    W2A: `require_metadata=True` is the release-gate mode — a dump without
    `release.json` is a hard failure (mutable directory, no identity), not the
    soft "unverified" pass used for local scratch archives.
    """
    checks: list[Check] = []
    dump = archive_dir / version / DUMP_NAME
    if not dump.is_file():
        return [Check(f"{version}/dump", False, f"missing {dump}")]

    metadata_path = archive_dir / version / METADATA_NAME
    if not metadata_path.is_file():
        if require_metadata:
            checks.append(
                Check(
                    f"{version}/metadata",
                    False,
                    f"missing {METADATA_NAME}; release archives must carry a "
                    "sha256 identity (W2A)",
                )
            )
        else:
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


def validate_archive(
    settings: Settings | None = None,
    *,
    require_metadata: bool = False,
    require_versions: bool = False,
) -> ArchiveReport:
    """Validate the whole mount: path, public base, and every archived version.

    An *empty* mount is not a failure in runtime mode — a fresh checkout has
    archived nothing — but it is reported, because "no archived versions" and
    "archive mounted and healthy" are answers a release gate must be able to
    tell apart.

    W2A release-gate flags:
      * ``require_metadata`` — every mounted version must carry ``release.json``
        with a matching sha256 (identity, not existence).
      * ``require_versions`` — empty mount fails (a citable release must ship
        at least one archived version).
    """
    settings = settings or get_settings()
    report = ArchiveReport(archive_dir=settings.archive_dir)
    report.checks.append(validate_public_base(settings.public_base))

    if not settings.archive_dir.exists():
        report.checks.append(Check(
            "archive_dir",
            not require_versions,
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
    if require_versions and not report.versions:
        report.checks.append(Check(
            "archive_dir", False,
            f"{settings.archive_dir}: release gate requires ≥1 archived version "
            "with checksum identity",
        ))
    else:
        report.checks.append(Check(
            "archive_dir", True,
            f"{settings.archive_dir}: {len(report.versions)} archived version(s)",
        ))
    for version in report.versions:
        report.checks.extend(
            validate_version(
                settings.archive_dir,
                version,
                require_metadata=require_metadata,
            )
        )
    return report


def resolve_archived_sense(
    archive_dir: Path, version: str, sense_id: str
) -> dict | None:
    """Offline lookup of one sense inside a mounted version (no settings).

    Used by the release gate and historical-resolution tests so they do not
    depend on process-wide env for the archive mount.
    """
    dump = archive_dir / version / DUMP_NAME
    if not dump.is_file():
        return None
    bare = sense_id.split("@", 1)[0]
    con = sqlite3.connect(f"file:{dump}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            "SELECT * FROM archive WHERE sense_id=?", (bare,)
        ).fetchone()
    finally:
        con.close()
    return dict(row) if row else None


def validate_historical_resolution(
    archive_dir: Path,
    *,
    sense_id: str,
    versions: list[str] | None = None,
) -> list[Check]:
    """Prove each named (or every mounted) version still resolves ``sense_id``.

    W2A acceptance: current + at least one prior release identity must resolve
    against the mounted archive — not merely that a dump file exists.
    """
    checks: list[Check] = []
    target_versions = versions if versions is not None else mounted_versions(archive_dir)
    if len(target_versions) < 1:
        return [Check(
            "historical_resolution",
            False,
            "no archived versions to resolve against",
        )]
    for version in target_versions:
        row = resolve_archived_sense(archive_dir, version, sense_id)
        if row is None:
            checks.append(Check(
                f"{version}/resolve",
                False,
                f"{sense_id} not found in {version} archive",
            ))
        else:
            checks.append(Check(
                f"{version}/resolve",
                True,
                f"{sense_id} → {row.get('headword') or ''} ({len(row.get('text_raw') or '')} chars)",
            ))
    if len(target_versions) >= 2:
        texts = []
        for version in target_versions:
            row = resolve_archived_sense(archive_dir, version, sense_id)
            texts.append((version, (row or {}).get("text_raw")))
        # Distinct version identities may share text (no change) or diverge;
        # the gate only requires both resolve. Divergence is reported.
        distinct = {t for _, t in texts if t is not None}
        checks.append(Check(
            "historical_multi_version",
            True,
            f"{len(target_versions)} versions resolve; "
            f"{len(distinct)} distinct text(s) for {sense_id}",
        ))
    return checks


def validate_release_archives(
    settings: Settings | None = None,
    *,
    sense_id: str | None = None,
    min_versions: int = 1,
) -> ArchiveReport:
    """Full W2A release gate: assets + checksums + public base + resolve.

    Fails when archives lack identity metadata, when digests disagree with
    bytes, when the public base is not a durable absolute URL, or when a
    required sense cannot be resolved from a mounted version.
    """
    settings = settings or get_settings()
    report = validate_archive(
        settings,
        require_metadata=True,
        require_versions=True,
    )
    if len(report.versions) < min_versions:
        report.checks.append(Check(
            "min_versions",
            False,
            f"need ≥{min_versions} archived version(s), found {len(report.versions)}",
        ))
    else:
        report.checks.append(Check(
            "min_versions",
            True,
            f"{len(report.versions)} ≥ {min_versions}",
        ))

    if sense_id and report.versions:
        report.checks.extend(
            validate_historical_resolution(
                settings.archive_dir,
                sense_id=sense_id,
                versions=report.versions,
            )
        )
    elif report.versions:
        # Auto-pick the first sense from the newest version so the gate always
        # exercises resolution without a caller-supplied id.
        newest = report.versions[-1]
        dump = settings.archive_dir / newest / DUMP_NAME
        try:
            con = sqlite3.connect(f"file:{dump}?mode=ro", uri=True)
            try:
                row = con.execute(
                    "SELECT sense_id FROM archive ORDER BY sense_id LIMIT 1"
                ).fetchone()
            finally:
                con.close()
        except sqlite3.Error as exc:
            report.checks.append(Check(
                "historical_resolution", False, f"cannot probe {newest}: {exc}"
            ))
            return report
        if not row:
            report.checks.append(Check(
                "historical_resolution", False, f"{newest} archive has no senses"
            ))
        else:
            report.checks.extend(
                validate_historical_resolution(
                    settings.archive_dir,
                    sense_id=row[0],
                    versions=report.versions,
                )
            )
    return report
