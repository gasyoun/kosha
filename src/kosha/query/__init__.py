"""kosha query layer — multi-DB storage facade (W1A, H2341).

Architecture D7 / Storage facade:

| File            | Tables |
|-----------------|--------|
| core.db         | meta, sources, lemmas, entries, senses, forms, stem_bridge, heritage_anchor |
| inflections.db  | inflections (+ paradigm metadata) |
| layers.db       | sense/roots frequency, coverage, roots, etymology, public layers |
| history.db      | visitors, events, rollups, magic links — **never** on this path by default |

The repository attaches read-only databases with stable aliases and is the only
API/static query path. Physical placement must not leak into response models.

[`connection`](https://github.com/gasyoun/kosha/blob/main/src/kosha/query/connection.py)
opens the facade; [`split`](https://github.com/gasyoun/kosha/blob/main/src/kosha/query/split.py)
builds multi-DB packs from a monolith for parity tests; [`samples`](https://github.com/gasyoun/kosha/blob/main/src/kosha/query/samples.py)
holds the frozen monolith query list.
"""

from .connection import (
    CORE_TABLES,
    HISTORY_ALIAS,
    INFLECTIONS_TABLES,
    LAYERS_TABLES,
    STABLE_ALIASES,
    attached_aliases,
    open_query_connection,
)
from .samples import GOLDEN_SAMPLE_QUERIES, run_sample_queries
from .split import split_monolith_to_facade

__all__ = [
    "CORE_TABLES",
    "GOLDEN_SAMPLE_QUERIES",
    "HISTORY_ALIAS",
    "INFLECTIONS_TABLES",
    "LAYERS_TABLES",
    "STABLE_ALIASES",
    "attached_aliases",
    "open_query_connection",
    "run_sample_queries",
    "split_monolith_to_facade",
]
