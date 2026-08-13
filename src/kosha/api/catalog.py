"""Public dataset catalog over the one datasets.json manifest (W2B / P-D6).

This is the **dataset catalog** lane, not the Salt dictionary-entry API.
It reads [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
and projects only `tier=public` rows. Restricted and intermediate rows are
invisible: they do not appear in the list, and resolving their id is the
same 404 as an unknown id. Checksums and locators on non-public rows are
never copied into a response.

Rights uncertainty does not invent an open license. The public-tier license
string is the one already recorded on the manifest header
(`license_public_tier`); a row-level `license` is used only when the row
itself already carries one.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kosha.settings import ROOT

SCHEMA = "kosha-dataset-catalog-v1"
PUBLIC_TIER = "public"
LICENSE_DATA_URL = (
    "https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md"
)
GITHUB = "https://github.com/gasyoun/kosha"

#: Locked public-record keys. Tests pin this set so a silent field drop is a
#: failure, not a surprise for catalog clients.
RECORD_REQUIRED_KEYS: tuple[str, ...] = (
    "id",
    "title",
    "version",
    "license",
    "rights",
    "download",
    "locator",
)

EMPTY_REASON = "no public-tier rows in manifest"


def default_manifest_path() -> Path:
    return ROOT / "data" / "manifest" / "datasets.json"


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    """Load the canonical datasets manifest. Fail loud on a missing/broken file."""
    manifest_path = path if path is not None else default_manifest_path()
    if not manifest_path.is_file():
        raise FileNotFoundError(f"datasets manifest not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("datasets"), list):
        raise ValueError(f"datasets manifest is not a catalog object: {manifest_path}")
    return data


def is_public_row(row: dict[str, Any]) -> bool:
    return isinstance(row, dict) and row.get("tier") == PUBLIC_TIER


def download_url(row: dict[str, Any]) -> str | None:
    """Public released dataset -> release-asset URL; else source repo.

    Matches [`scripts/build_directory.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_directory.py)
    `download_url` so the HTML directory and this API do not invent two locators.
    Non-public rows return None (the caller must already have filtered).
    """
    if not is_public_row(row):
        return None
    rel = row.get("in_release")
    asset = row.get("release_asset")
    if (
        isinstance(rel, str)
        and rel not in {"unreleased", "not-applicable"}
        and isinstance(asset, str)
        and asset
        and " " not in asset
    ):
        return f"{GITHUB}/releases/download/{rel}/{asset}"
    source = row.get("source_repo")
    return source if isinstance(source, str) and source else None


def _license_for(row: dict[str, Any], manifest: dict[str, Any]) -> str:
    row_license = row.get("license")
    if isinstance(row_license, str) and row_license.strip():
        return row_license.strip()
    header = manifest.get("license_public_tier")
    if isinstance(header, str) and header.strip():
        return header.strip()
    return "CC BY-SA 4.0 (see LICENSE-DATA.md)"


def _rights_pointer(row: dict[str, Any]) -> str:
    statement = row.get("data_statement")
    if isinstance(statement, str) and statement.startswith("http"):
        return statement
    return LICENSE_DATA_URL


def _checksum(row: dict[str, Any]) -> dict[str, Any] | None:
    raw = row.get("sha256")
    if raw is None:
        return None
    if isinstance(raw, str) and raw.strip():
        return {"sha256": raw.strip()}
    if isinstance(raw, dict) and raw:
        return {"sha256": raw}
    return None


def project_public_record(row: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Project one public manifest row into the stable catalog schema."""
    if not is_public_row(row):
        raise ValueError("refusing to project a non-public manifest row")
    record: dict[str, Any] = {
        "id": row["id"],
        "title": row.get("title") or row["id"],
        "version": row.get("in_release"),
        "license": _license_for(row, manifest),
        "rights": {
            "tier": PUBLIC_TIER,
            "pointer": _rights_pointer(row),
        },
        "download": download_url(row),
        "locator": {
            "source_repo": row.get("source_repo"),
            "source_path": row.get("source_path"),
            "release_asset": row.get("release_asset"),
            "in_release": row.get("in_release"),
        },
    }
    checksum = _checksum(row)
    if checksum is not None:
        record["checksum"] = checksum
    if row.get("format") is not None:
        record["format"] = row["format"]
    if row.get("rows") is not None:
        record["rows"] = row["rows"]
    if row.get("size_bytes") is not None:
        record["size_bytes"] = row["size_bytes"]
    if row.get("data_statement"):
        record["data_statement"] = row["data_statement"]
    return record


def public_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        project_public_record(row, manifest)
        for row in manifest.get("datasets", [])
        if is_public_row(row) and row.get("id")
    ]


def get_public_record(manifest: dict[str, Any], dataset_id: str) -> dict[str, Any] | None:
    for row in manifest.get("datasets", []):
        if not isinstance(row, dict) or row.get("id") != dataset_id:
            continue
        if not is_public_row(row):
            return None
        return project_public_record(row, manifest)
    return None


def list_payload(manifest: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "manifest_version": manifest.get("manifest_version"),
        "license_public_tier": manifest.get("license_public_tier"),
        "count": len(records),
        "datasets": records,
    }
    if not records:
        body["empty_reason"] = EMPTY_REASON
    return body
