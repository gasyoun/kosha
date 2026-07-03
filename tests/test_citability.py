"""kosha — R1 citability tests (RISKS.md R1, EVAL_PLAN.md §6 T-UC10).

Covers Commitment 1 (an old `@version` citation resolves in-browser against its
archived release, not the live DB) and Commitment 2 (the crosswalk detects
SPLIT / MERGED / GONE / MOVED renumbering). The version-resolution path is what
T-UC10 forces to exist.
"""
import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

from app.main import app  # noqa: E402
import versions  # noqa: E402
from cite import cite_object, release_asset_url  # noqa: E402
import importlib.util  # noqa: E402

# import scripts/build_crosswalk.py by path (scripts is not a package)
_spec = importlib.util.spec_from_file_location(
    "build_crosswalk", ROOT / "scripts" / "build_crosswalk.py")
build_crosswalk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_crosswalk)

client = TestClient(app)


# --- Commitment 1: cite object shape -------------------------------------

def test_cite_object_carries_browser_resolution_url():
    c = cite_object("mw", "142512", 3, "0.2.0", "https://api.example.org")
    assert c["text"] == "mw.142512.3@0.2.0"
    assert c["resolution_url"] == "https://api.example.org/api/v1/sense/mw.142512.3@0.2.0"
    assert c["release_asset"].endswith("data-0.2.0/senses.sqlite")
    assert c["bibtex"].startswith("@misc")
    assert c["csl_json"]["version"] == "0.2.0"


def test_dev_version_is_not_citable():
    assert release_asset_url("0.1.0-dev") is None
    assert cite_object("mw", "1", 1, "0.1.0-dev", "http://x")["release_asset"] is None


def test_live_sense_cite_has_resolution_url():
    lemma = client.get("/api/v1/lemma/agni").json()["results"][0]
    sid = lemma["sense_ids"][0]
    r = client.get(f"/api/v1/sense/{sid}").json()["results"][0]
    assert r["resolved_from"] == "live"
    assert r["cite"]["resolution_url"].endswith(f"/api/v1/sense/{sid}")


# --- Commitment 1 / T-UC10: old citation resolves against the archive -----

def test_t_uc10_old_citation_resolves_to_archived_text(tmp_path, monkeypatch):
    monkeypatch.setenv("KOSHA_RELEASES_DIR", str(tmp_path))
    old_version = "0.0.9-uc10test"
    # Archive one sense whose text differs from whatever the live entry says.
    versions.write_archive(old_version, [{
        "sense_id": "mw.523.1", "dict": "mw", "L": "523", "sense_n": 1,
        "headword": "akza", "text_raw": "ARCHIVED-OLD text of akza as of the cited release",
    }])
    # Resolve the OLD citation — must return the archived text, not the live DB.
    r = client.get(f"/api/v1/sense/mw.523.1@{old_version}")
    assert r.status_code == 200
    result = r.json()["results"][0]
    assert result["resolved_from"] == "archive"
    assert result["text_raw"] == "ARCHIVED-OLD text of akza as of the cited release"
    assert r.json()["data_version"] == old_version


def test_unarchived_version_404s_with_release_pointer(tmp_path, monkeypatch):
    monkeypatch.setenv("KOSHA_RELEASES_DIR", str(tmp_path))  # empty dir
    r = client.get("/api/v1/sense/mw.523.1@9.9.9")
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "version_not_archived"
    assert any("releases/download/data-9.9.9" in s
               for s in r.json()["detail"]["error"]["suggestions"])


# --- Commitment 2: crosswalk SPLIT / MERGED / GONE / MOVED ----------------

def _statuses(rows):
    return sorted({r[2] for r in rows})


def test_crosswalk_zero_cost_when_unchanged():
    same = {1: "alpha beta", 2: "gamma delta"}
    assert build_crosswalk.diff_entry(same, dict(same), 0.6) == []


def test_crosswalk_detects_split():
    old = {1: "the quick brown fox jumps over the lazy dog"}
    new = {1: "the quick brown fox", 2: "jumps over the lazy dog"}
    rows = build_crosswalk.diff_entry(old, new, 0.6)
    assert "SPLIT" in _statuses(rows)
    split_targets = {r[1] for r in rows if r[2] == "SPLIT"}
    assert split_targets == {1, 2}


def test_crosswalk_detects_merged():
    old = {1: "the quick brown fox", 2: "jumps over the lazy dog"}
    new = {1: "the quick brown fox jumps over the lazy dog"}
    rows = build_crosswalk.diff_entry(old, new, 0.6)
    assert "MERGED" in _statuses(rows)


def test_crosswalk_detects_gone():
    old = {1: "aardvark buffalo cheetah dolphin elephant"}
    new = {1: "xylophone yacht zeppelin quilt"}
    rows = build_crosswalk.diff_entry(old, new, 0.6)
    # old sense 1 vanishes (GONE); the unrelated new sense 1 is legitimately NEW.
    assert (1, None) in {(r[0], r[1]) for r in rows if r[2] == "GONE"}
    assert "GONE" in _statuses(rows)


def test_crosswalk_detects_moved():
    old = {1: "alpha beta gamma", 2: "delta epsilon zeta"}
    new = {1: "delta epsilon zeta", 2: "alpha beta gamma"}
    rows = build_crosswalk.diff_entry(old, new, 0.6)
    assert _statuses(rows) == ["MOVED"]
    assert {(r[0], r[1]) for r in rows} == {(1, 2), (2, 1)}
