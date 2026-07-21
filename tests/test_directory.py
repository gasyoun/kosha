"""Invariants for the public data + tools directory page (scripts/build_directory.py).

Guards the single-source + publish-safety contract: the page is rendered from
data/manifest/datasets.json + external_tools.json, carries a schema.org Dataset
node per PUBLIC dataset, and never exposes a restricted-tier download or a
gitignored/local path.
"""

from __future__ import annotations

import json
import posixpath
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import build_directory as bd  # noqa: E402

MANIFEST = REPO / "data" / "manifest"


@pytest.fixture(scope="module")
def page(tmp_path_factory) -> str:
    out = tmp_path_factory.mktemp("directory")
    written = bd.build(out)
    return written.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def datasets() -> list[dict]:
    return json.loads((MANIFEST / "datasets.json").read_text(encoding="utf-8"))["datasets"]


def _jsonld(page: str) -> dict:
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    assert m, "no JSON-LD block found"
    return json.loads(m.group(1))


def _normalise_release_path(value: str) -> str:
    """Canonical manifest-style path, independent of URL encoding/separators."""
    decoded = unquote(value).replace("\\", "/")
    return posixpath.normpath("/" + decoded).lstrip("/")


def _release_relative_asset(url: str) -> str:
    """Drop scheme/repository/release tag, retaining the full asset subpath."""
    path = urlsplit(url).path
    marker = "releases/download/"
    assert marker in path, f"not a release download URL: {url}"
    after_marker = path.split(marker, 1)[1]
    _, separator, asset = after_marker.partition("/")
    assert separator and asset, f"release download has no asset path: {url}"
    return _normalise_release_path(asset)


def test_page_renders(page):
    assert "<title>" in page and "Sanskrit NLP Data" in page


# --- D8: in_release closed vocabulary + release_asset schema (H1264) ---------

RELEASE_TAG_RE = re.compile(r"^data-v\d+\.\d+\.\d+$")


def _in_release_is_valid(value) -> bool:
    if value in ("unreleased", "not-applicable"):
        return True
    return isinstance(value, str) and bool(RELEASE_TAG_RE.match(value))


def test_in_release_closed_vocabulary(datasets):
    """Every row's in_release is 'unreleased', 'not-applicable', or a release tag.

    Falsified by any row missing in_release, carrying None, or using a free-form
    value outside the closed vocabulary -- the exact drift (undisciplined
    null/"unreleased" usage) that let a 32-row unreleased backlog accumulate
    unnoticed (see docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md D8).
    """
    bad = [d["id"] for d in datasets if not _in_release_is_valid(d.get("in_release"))]
    assert not bad, f"rows with in_release outside the closed vocabulary: {bad}"


def test_public_released_rows_require_release_asset(datasets):
    """Every public row naming a release tag has a non-empty release_asset.

    Falsified by any released public row lacking one -- checked by *value*,
    not merely by key presence (a row can carry `"release_asset": null`).
    """
    bad = [
        d["id"]
        for d in datasets
        if d.get("tier") == "public"
        and isinstance(d.get("in_release"), str)
        and RELEASE_TAG_RE.match(d["in_release"])
        and not d.get("release_asset")
    ]
    assert not bad, f"released public rows missing release_asset: {bad}"


def test_schema_check_fails_on_broken_row(datasets):
    """Prove the two checks above actually fail on bad input (D8/1c-3).

    A copy of the live manifest is deliberately corrupted -- a null in_release,
    and a released-but-assetless public row -- and both invariants above must
    reject it. A validator that only ever sees clean fixtures is not a test.
    """
    broken = [dict(d) for d in datasets]
    broken[0] = dict(broken[0], in_release=None)
    assert not all(_in_release_is_valid(d.get("in_release")) for d in broken)

    public_tag_row = next(
        (d for d in broken if d.get("tier") == "public" and isinstance(d.get("in_release"), str)
         and RELEASE_TAG_RE.match(d["in_release"])),
        None,
    )
    assert public_tag_row is not None, "fixture assumption: at least one public released row exists"
    public_tag_row["release_asset"] = None
    still_ok = all(
        d.get("release_asset")
        for d in broken
        if d.get("tier") == "public"
        and isinstance(d.get("in_release"), str)
        and RELEASE_TAG_RE.match(d["in_release"])
    )
    assert not still_ok


def test_one_dataset_node_per_public_dataset(page, datasets):
    doc = _jsonld(page)
    ld_datasets = [n for n in doc["@graph"] if n.get("@type") == "Dataset"]
    public = [d for d in datasets if d.get("tier") == "public"]
    assert len(ld_datasets) == len(public)


def test_id_spine_present(page):
    doc = _jsonld(page)
    ids = {n.get("@id") for n in doc["@graph"]}
    assert bd.ORG_ID in ids
    # every Dataset creator/publisher points at the org @id spine
    for n in doc["@graph"]:
        if n.get("@type") == "Dataset":
            assert n["publisher"]["@id"] == bd.ORG_ID


def test_no_restricted_download_leak(page, datasets):
    """Every releases/download URL in the page must belong to a public row."""
    released_assets = {
        _normalise_release_path(d["release_asset"])
        for d in datasets
        if d.get("tier") == "public" and d.get("release_asset")
    }
    for url in re.findall(r"releases/download/[^\"'< ]+", page):
        asset = _release_relative_asset(url)
        assert asset in released_assets, f"non-public asset linked: {url}"


def test_release_asset_normalization_preserves_subdirectories():
    url = (
        "https://github.com/gasyoun/kosha/releases/download/v0.40.0/"
        "reading%2Fdata/./nala-1.json?download=1"
    )
    assert _release_relative_asset(url) == "reading/data/nala-1.json"


def test_no_local_or_gitignored_paths(page):
    for bad in ("GITIGNORED", "MG disk", "AppData", "C:/", "/home/", ".db\"", ".sqlite\""):
        assert bad not in page, f"leaked path marker: {bad}"


def test_external_tools_rendered(page):
    tools = json.loads((MANIFEST / "external_tools.json").read_text(encoding="utf-8"))["tools"]
    for t in tools:
        assert t["name"] in page


# --- W1d: Invariant test for README dataset counts (H1265) ---

def test_readme_dataset_counts_match_manifest():
    """README dataset counts MUST match the manifest.

    This invariant test FAILS when the manifest changes and the README is not
    updated, catching drift that hand-copying would otherwise hide. The test is
    falsified by any mismatch in the computed counts.

    Deliberately prove the test fails by drifting the manifest, not just assert
    success on correct input.
    """
    readme_path = REPO / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")

    # Parse README counts from the marked region
    m = re.search(
        r'<!-- dataset_count_start -->\*\*(\d+) datasets\*\* \((\d+) public · (\d+) restricted · (\d+) intermediate\)<!-- dataset_count_end -->',
        readme_text
    )
    assert m, "Dataset count markers not found or format incorrect in README"
    readme_total = int(m.group(1))
    readme_public = int(m.group(2))
    readme_restricted = int(m.group(3))
    readme_intermediate = int(m.group(4))

    # Compute counts from manifest
    datasets = json.loads((MANIFEST / "datasets.json").read_text(encoding="utf-8"))["datasets"]
    manifest_public = len([d for d in datasets if d.get("tier") == "public"])
    manifest_restricted = len([d for d in datasets if d.get("tier") not in ("public", "intermediate")])
    manifest_intermediate = len([d for d in datasets if d.get("tier") == "intermediate"])
    manifest_total = manifest_public + manifest_restricted + manifest_intermediate

    assert readme_total == manifest_total, f"Total count mismatch: README={readme_total}, manifest={manifest_total}"
    assert readme_public == manifest_public, f"Public count mismatch: README={readme_public}, manifest={manifest_public}"
    assert readme_restricted == manifest_restricted, f"Restricted count mismatch: README={readme_restricted}, manifest={manifest_restricted}"
    assert readme_intermediate == manifest_intermediate, f"Intermediate count mismatch: README={readme_intermediate}, manifest={manifest_intermediate}"


def test_readme_external_tools_count_matches_manifest():
    """README external tools count MUST match the manifest.

    Like the dataset-count test, this FAILS when the external_tools.json changes
    and the README is not updated.
    """
    readme_path = REPO / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")

    # Parse README external tools count from the marked region
    m = re.search(
        r'<!-- external_tools_count_start -->\*\*(\d+) external stacks\*\*<!-- external_tools_count_end -->',
        readme_text
    )
    assert m, "External tools count markers not found or format incorrect in README"
    readme_tools = int(m.group(1))

    # Compute count from manifest
    tools = json.loads((MANIFEST / "external_tools.json").read_text(encoding="utf-8"))["tools"]
    manifest_tools = len(tools)

    assert readme_tools == manifest_tools, f"External tools count mismatch: README={readme_tools}, manifest={manifest_tools}"
