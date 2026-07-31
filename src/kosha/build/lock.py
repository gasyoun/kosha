"""The build lock — what actually ran, over which sources, and whether it held.

The lock sits next to the database it describes (`kosha.build-lock.json`) and is
promoted with it, so an artifact and its provenance can never be separated by a
half-finished build. It answers three questions that `scripts/build_db.py`
could not answer before W0B:

* **Did every declared stage run?** `stages` has a row per stage in the plan
  with `ok` / `skipped` / `failed` and, for a skip, the reason. A stage that is
  absent from the lock did not run, and the runner treats that as a failure
  rather than as a silent success (issue #210).
* **Over which inputs?** Every stage records a digest per source feed, taken
  before it ran and re-taken after. A feed that changes mid-build is a hard
  error: half the build would have read the old bytes.
* **Is a later single-stage run allowed to trust the earlier ones?** A
  prerequisite whose recorded source digests no longer match the files on disk
  is **stale**, and rebuilding only the dependent stage on top of it is exactly
  the "stale prerequisites reused silently" failure #210 asks to be closed
  against. `stale_prerequisites()` finds them; the runner refuses.
"""
from __future__ import annotations

import json
import platform
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .digest import SourceDigest, digest_path

SCHEMA = "kosha-build-lock/1"
LOCK_SUFFIX = ".build-lock.json"

STATUS_OK = "ok"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"

__all__ = [
    "SCHEMA",
    "LOCK_SUFFIX",
    "STATUS_OK",
    "STATUS_SKIPPED",
    "STATUS_FAILED",
    "StageRecord",
    "BuildLock",
    "lock_path_for",
    "utc_now",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def lock_path_for(target: Path) -> Path:
    """`data/db/kosha.db` -> `data/db/kosha.build-lock.json`."""
    return target.with_name(target.stem + LOCK_SUFFIX)


@dataclass
class StageRecord:
    name: str
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    duration_s: float | None = None
    reason: str | None = None
    sources: list[SourceDigest] = field(default_factory=list)
    postconditions: list[dict] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_s": self.duration_s,
            "reason": self.reason,
            "sources": [s.to_json() for s in self.sources],
            "postconditions": self.postconditions,
        }

    @staticmethod
    def from_json(data: dict) -> "StageRecord":
        return StageRecord(
            name=data["name"],
            status=data["status"],
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            duration_s=data.get("duration_s"),
            reason=data.get("reason"),
            sources=[SourceDigest.from_json(s) for s in data.get("sources", [])],
            postconditions=data.get("postconditions", []),
        )


@dataclass
class BuildLock:
    build_id: str
    target: str
    plan: list[str] = field(default_factory=list)
    stages: dict[str, StageRecord] = field(default_factory=dict)
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None
    data_version: str | None = None
    release: bool = False
    kosha_version: str = ""
    python: str = field(default_factory=platform.python_version)
    artifact: dict | None = None
    # Which feed set the build read: "default" (the sibling checkouts) or the
    # name of a sources manifest, e.g. the committed fixture pack. A lock that
    # does not say this cannot distinguish a real artifact from a fixture one.
    source_set: str = "default"

    # --- serialisation -------------------------------------------------------

    def to_json(self) -> dict:
        return {
            "schema": SCHEMA,
            "build_id": self.build_id,
            "target": self.target,
            "plan": self.plan,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "data_version": self.data_version,
            "release": self.release,
            "kosha_version": self.kosha_version,
            "python": self.python,
            "source_set": self.source_set,
            "stages": {name: rec.to_json() for name, rec in self.stages.items()},
            "artifact": self.artifact,
        }

    @staticmethod
    def from_json(data: dict) -> "BuildLock":
        if data.get("schema") != SCHEMA:
            raise ValueError(
                f"unsupported build-lock schema {data.get('schema')!r}; expected {SCHEMA!r}"
            )
        lock = BuildLock(
            build_id=data["build_id"],
            target=data["target"],
            plan=data.get("plan", []),
            started_at=data.get("started_at", ""),
            finished_at=data.get("finished_at"),
            data_version=data.get("data_version"),
            release=data.get("release", False),
            kosha_version=data.get("kosha_version", ""),
            python=data.get("python", ""),
            artifact=data.get("artifact"),
            source_set=data.get("source_set", "default"),
        )
        lock.stages = {
            name: StageRecord.from_json(rec) for name, rec in data.get("stages", {}).items()
        }
        return lock

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(self.to_json(), indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        tmp.replace(path)
        return path

    @staticmethod
    def read(path: Path) -> "BuildLock | None":
        if not path.exists():
            return None
        return BuildLock.from_json(json.loads(path.read_text(encoding="utf-8")))

    # --- queries -------------------------------------------------------------

    def record(self, rec: StageRecord) -> None:
        self.stages[rec.name] = rec

    def ran(self, name: str) -> bool:
        rec = self.stages.get(name)
        return rec is not None and rec.status == STATUS_OK

    def missing_from_plan(self) -> list[str]:
        """Planned stages with no record at all — the #210 signature."""
        return [name for name in self.plan if name not in self.stages]

    def incomplete(self) -> list[str]:
        """Planned stages that did not finish successfully."""
        return [name for name in self.plan
                if self.stages.get(name) is None
                or self.stages[name].status != STATUS_OK]

    def stale_prerequisites(self, prerequisites, configured=None) -> list[tuple[str, str]]:
        """`(stage, why)` for each prerequisite that must not be trusted.

        Three ways a prerequisite stops being trustworthy:

        1. it never ran successfully against this database;
        2. the bytes at a path it recorded are no longer those bytes;
        3. the build is now *configured* to read a different set of feeds for
           it than the set it recorded. This third case is the one a digest
           check alone misses — redirect `build_db.UNION_HEADWORDS` at a new
           file and the old one sits on disk unchanged, so every recorded
           digest still matches while the stage's real input has moved.

        `configured` maps a stage name to the feed paths currently resolved for
        it; pass it whenever the caller knows them (the runner always does).
        """
        problems: list[tuple[str, str]] = []
        for dep in prerequisites:
            rec = self.stages.get(dep)
            if rec is None:
                problems.append((dep, "never ran against this database"))
                continue
            if rec.status != STATUS_OK:
                problems.append((dep, f"last run was {rec.status}"
                                      + (f" ({rec.reason})" if rec.reason else "")))
                continue

            recorded_paths = [Path(s.path) for s in rec.sources]
            if configured is not None and dep in configured:
                current_paths = [Path(p) for p in configured[dep]]
                if current_paths != recorded_paths:
                    problems.append((
                        dep,
                        f"source set changed since that run: it read "
                        f"{[str(p) for p in recorded_paths]}, the build is now "
                        f"configured for {[str(p) for p in current_paths]}",
                    ))
                    continue

            changed = None
            for recorded in rec.sources:
                current = digest_path(Path(recorded.path))
                if recorded.matches(current):
                    continue
                if not current.exists:
                    changed = f"source disappeared: {recorded.path}"
                elif not recorded.exists:
                    changed = f"source appeared since that run: {recorded.path}"
                else:
                    changed = f"source changed since that run: {recorded.path}"
                break
            if changed:
                problems.append((dep, changed))
        return problems
