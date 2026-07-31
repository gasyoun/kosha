"""Source fingerprints for the build lock.

Honesty over convenience: the algorithm used is stored *next to* every digest,
so a reader can tell a whole-file hash from a sampled one. The sampled variant
exists because several source feeds are gigabyte-scale sqlite dumps, and
re-hashing them in full on every stage would dominate build time — but a digest
whose method is unrecorded is a digest you cannot reason about later.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

# Whole-file sha256 up to this size; sampled beyond it.
FULL_HASH_LIMIT = 256 * 1024 * 1024
_SAMPLE = 8 * 1024 * 1024
_CHUNK = 4 * 1024 * 1024

__all__ = ["SourceDigest", "digest_path", "digest_paths"]


@dataclass(frozen=True)
class SourceDigest:
    path: str
    exists: bool
    size: int | None = None
    algorithm: str | None = None
    digest: str | None = None

    def to_json(self) -> dict:
        return {
            "path": self.path,
            "exists": self.exists,
            "size": self.size,
            "algorithm": self.algorithm,
            "digest": self.digest,
        }

    @staticmethod
    def from_json(data: dict) -> "SourceDigest":
        return SourceDigest(
            path=data["path"],
            exists=data["exists"],
            size=data.get("size"),
            algorithm=data.get("algorithm"),
            digest=data.get("digest"),
        )

    def matches(self, other: "SourceDigest") -> bool:
        """Same file, same content — by the same method.

        Two digests taken with different algorithms are NOT comparable and
        report a mismatch rather than a false match: that is the conservative
        direction (a needless rebuild, not a silently stale one).
        """
        if self.exists != other.exists:
            return False
        if not self.exists:
            return True
        return (
            self.size == other.size
            and self.algorithm == other.algorithm
            and self.digest == other.digest
        )


def digest_path(path: Path) -> SourceDigest:
    """Fingerprint one file or directory.

    A directory is fingerprinted from the sorted (relative path, size) list of
    the files under it — enough to notice an added, removed or resized feed
    without reading gigabytes of dictionary dumps.
    """
    path = Path(path)
    if not path.exists():
        return SourceDigest(path=str(path), exists=False)

    if path.is_dir():
        h = hashlib.sha256()
        entries = sorted(p for p in path.rglob("*") if p.is_file())
        total = 0
        for entry in entries:
            size = entry.stat().st_size
            total += size
            h.update(str(entry.relative_to(path)).replace("\\", "/").encode("utf-8"))
            h.update(b"\0")
            h.update(str(size).encode("ascii"))
            h.update(b"\0")
        return SourceDigest(str(path), True, total, "sha256-dirlist", h.hexdigest())

    size = path.stat().st_size
    h = hashlib.sha256()
    if size <= FULL_HASH_LIMIT:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(_CHUNK), b""):
                h.update(chunk)
        return SourceDigest(str(path), True, size, "sha256", h.hexdigest())

    # Sampled: head + tail + size. Catches replacement and truncation, which
    # are the realistic drift modes for a released data dump; it would not
    # catch a surgical middle-of-file edit, and says so by its name.
    h.update(str(size).encode("ascii"))
    with open(path, "rb") as fh:
        h.update(fh.read(_SAMPLE))
        fh.seek(max(0, size - _SAMPLE))
        h.update(fh.read(_SAMPLE))
    return SourceDigest(str(path), True, size, "sha256-sampled", h.hexdigest())


def digest_paths(paths) -> list[SourceDigest]:
    return [digest_path(p) for p in paths]
