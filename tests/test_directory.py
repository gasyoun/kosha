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
