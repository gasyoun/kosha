"""kosha build chain — declarative stages, source locks, atomic promotion.

Before W0B (H1944) `scripts/build_db.py` dispatched with a ladder of
`if args.stage in (None, "x")` conditionals. Five of the ten declared stages —
`entries`, `forms`, `inflections`, `hybrid`, `stem_bridge` — were written
`if args.stage == "x"`, so a **no-flag build ran neither them nor any warning**
and still stamped `data_version` and exited 0. That is
[integrity issue #210](https://github.com/gasyoun/kosha/issues/210): the build
looked complete and was not.

The replacement is declarative. A stage is data (`stages.py`): its
dependencies, the external feeds it consumes, the entry point that runs it, and
the postcondition that proves it did something. The runner (`runner.py`) plans
a topological order, refuses to start when a declared stage cannot run, checks
each stage's postcondition, and records everything in a build lock
(`lock.py`) — so "this stage did not run" is a build failure or an explicit,
recorded skip, never silence.
"""

__all__ = ["stages", "lock", "runner", "digest"]
