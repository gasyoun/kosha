"""Fail-closed source guard for ``scripts/deploy_guhya.py`` (A05 drain, 01-10-2026).

A missing or 0-byte source must land in the SKIP ledger, never in the upload
plan: uploading a 0-byte stub mints a false backup artifact — the 23-08-2026
corpus.db incident behind the AGENTS danger fact ("deploy_guhya.py uploads
whatever exists — no size>0 guard"). Fake tmp_path sources only; no test in
this repo contacts a live server or reads a credential.
"""

from pathlib import Path

from deploy_guhya import plan_targets


def _make(root: Path, rel: str, size: int) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    return path


def test_present_source_is_ready(tmp_path):
    _make(tmp_path, "repo/data.bin", 10)
    ready, skipped = plan_targets([("repo/data.bin", "data.bin")], root=tmp_path)
    assert [remote for _, remote, _ in ready] == ["data.bin"]
    assert ready[0][2] == tmp_path / "repo" / "data.bin"
    assert skipped == []


def test_missing_source_is_skipped(tmp_path):
    ready, skipped = plan_targets([("repo/ghost.bin", "ghost.bin")], root=tmp_path)
    assert ready == []
    assert len(skipped) == 1
    remote, reason = skipped[0]
    assert remote == "ghost.bin"
    assert "missing on disk" in reason


def test_zero_byte_stub_is_refused(tmp_path):
    _make(tmp_path, "repo/stub.db", 0)
    ready, skipped = plan_targets([("repo/stub.db", "stub.db")], root=tmp_path)
    assert ready == []
    assert len(skipped) == 1
    remote, reason = skipped[0]
    assert remote == "stub.db"
    assert "0-byte stub" in reason


def test_mix_keeps_manifest_order_and_ledgers_gaps(tmp_path):
    _make(tmp_path, "a.bin", 5)
    _make(tmp_path, "c.bin", 6)
    ready, skipped = plan_targets(
        [("a.bin", "a"), ("ghost.bin", "g"), ("empty.bin", "e"), ("c.bin", "c")],
        root=tmp_path,
    )
    assert [remote for _, remote, _ in ready] == ["a", "c"]
    assert [remote for remote, _ in skipped] == ["g", "e"]


def test_absolute_path_bypasses_root(tmp_path):
    real = tmp_path / "abs.bin"
    real.write_bytes(b"abc")
    ready, skipped = plan_targets([(str(real), "abs")], root=tmp_path / "elsewhere")
    assert [remote for _, remote, _ in ready] == ["abs"]
    assert ready[0][2] == real
    assert skipped == []
