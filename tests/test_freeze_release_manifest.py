"""Tests for the frozen release manifest (H3788).

The three behaviours worth pinning are the ones that make a release either
citable or quietly wrong: the public-tier fence, the LF-canonical digest, and
drift detection. Each corresponds to a defect actually found on 01-09-2026.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name):
    """Import a scripts/ module by path -- scripts/ is not a package."""
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


frm = _load("freeze_release_manifest")


def _manifest(rows):
    return {
        "manifest_version": "0.2.0",
        "hub": "test hub",
        "license_public_tier": "CC BY-SA 4.0",
        "datasets": rows,
    }


def _row(id_, tier="public", **kw):
    row = {
        "id": id_,
        "title": id_,
        "tier": tier,
        "in_release": "data-v9.9.9",
        "release_asset": f"{id_}.tsv",
        "format": "tsv",
        "rows": 1,
        "size_bytes": 1,
        "source_repo": "https://github.com/gasyoun/kosha",
        "source_path": f"data/{id_}.tsv",
    }
    row.update(kw)
    return row


def test_restricted_tier_refuses_rather_than_dropping_the_row():
    """A release asset is a publication; a silent drop looks like a clean run."""
    manifest = _manifest([_row("public-one"), _row("secret-one", tier="restricted")])
    with pytest.raises(SystemExit) as exc:
        frm.build(manifest, "data-v9.9.9")
    message = str(exc.value)
    assert "REFUSING" in message
    assert "secret-one" in message
    # The refusal must name the offender, not just the count.
    assert "not tier=public" in message


def test_digest_is_lf_canonical_so_crlf_and_lf_agree(tmp_path, monkeypatch):
    """The defect: a CRLF checkout produced digests no clean checkout could match."""
    lf = tmp_path / "lf.tsv"
    crlf = tmp_path / "crlf.tsv"
    body = "a\tb\nc\td\ne\tf\n"
    lf.write_bytes(body.encode("utf-8"))
    crlf.write_bytes(body.replace("\n", "\r\n").encode("utf-8"))

    assert lf.stat().st_size != crlf.stat().st_size

    lf_digest, lf_size, lf_had_crlf = frm.canonical_digest(lf, "tsv")
    crlf_digest, crlf_size, crlf_had_crlf = frm.canonical_digest(crlf, "tsv")

    assert lf_digest == crlf_digest
    assert lf_size == crlf_size == len(body.encode("utf-8"))
    assert lf_had_crlf is False
    assert crlf_had_crlf is True


def test_crlf_working_tree_is_reported_so_the_caveat_travels(tmp_path, monkeypatch):
    manifest = _manifest([_row("dirty")])
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "dirty.tsv").write_bytes(b"a\tb\r\nc\td\r\n")
    monkeypatch.setattr(frm, "REPO", tmp_path)
    monkeypatch.setattr(frm, "REPO_URL_TO_LOCAL", {})

    doc, crlf_rows = frm.build(manifest, "data-v9.9.9")

    assert crlf_rows == ["dirty"]
    # Stamped into the artifact, not only printed to a terminal nobody kept.
    assert doc["checkout_warnings"]["crlf_working_tree_rows"] == ["dirty"]
    assert doc["datasets"][0]["sha256_form"] == "lf-canonical"


def test_check_detects_drift_and_a_clean_freeze_round_trips(tmp_path, monkeypatch):
    manifest = _manifest([_row("alpha"), _row("beta")])
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "alpha.tsv").write_bytes(b"x\ty\n")
    (tmp_path / "data" / "beta.tsv").write_bytes(b"p\tq\n")
    monkeypatch.setattr(frm, "REPO", tmp_path)
    monkeypatch.setattr(frm, "REPO_URL_TO_LOCAL", {})

    manifest_path = tmp_path / "datasets.json"
    with manifest_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    monkeypatch.setattr(frm, "DATASETS_JSON", manifest_path)

    frozen_path = tmp_path / "frozen.json"
    doc, _ = frm.build(manifest, "data-v9.9.9")
    with frozen_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")

    args = type("A", (), {"frozen": str(frozen_path), "tag": None})()
    assert frm.cmd_check(args) == 0

    # Change the underlying bytes: the frozen file must now be rejected.
    (tmp_path / "data" / "beta.tsv").write_bytes(b"p\tq\nr\ts\n")
    assert frm.cmd_check(args) == 1


def test_working_notes_are_not_carried_into_a_frozen_artifact(tmp_path, monkeypatch):
    """`consumers` changes after a release is cut; a frozen file must not."""
    manifest = _manifest([_row("alpha", consumers=["someone"], rebuild="run me")])
    monkeypatch.setattr(frm, "REPO", tmp_path)
    monkeypatch.setattr(frm, "REPO_URL_TO_LOCAL", {})

    doc, _ = frm.build(manifest, "data-v9.9.9")

    assert "consumers" not in doc["datasets"][0]
    assert "rebuild" not in doc["datasets"][0]
    assert doc["datasets"][0]["sha256_source"] == "unavailable"
