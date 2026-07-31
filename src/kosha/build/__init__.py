"""kosha build layer — declarative stage DAG, source locks, atomic promotion.

W0B (H1944) replaces the conditional dispatch in `scripts/build_db.py` with a
declared graph. The three modules are deliberately separable:

- [`sources`](https://github.com/gasyoun/kosha/blob/main/src/kosha/build/sources.py) — every external input, its resolved path, and its digest;
- [`stages`](https://github.com/gasyoun/kosha/blob/main/src/kosha/build/stages.py) — the stage registry: dependencies, builder, postcondition;
- [`dag`](https://github.com/gasyoun/kosha/blob/main/src/kosha/build/dag.py) — expansion, execution into a temp target, validation, promotion.
"""
