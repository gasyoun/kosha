"""kosha — one shared bounded-parameter dependency (H6906).

Every public list/size/offset/ids parameter goes through here, so no route can
reach SQLite with `LIMIT -1` (SQLite reads any negative as "no limit"), a
10^9 limit, an unbounded OFFSET or an unbounded id collection. The class dies
at the type layer, not at six scattered call sites.

Why not `Query(ge=, le=)` alone: FastAPI answers an out-of-range value with
422, and the C-SALT profile §3 / W0C contract mandates 400. So the bounds are
declared to OpenAPI (minimum/maximum/maxItems via `json_schema_extra`) but the
rejection is ours — the house `error(..., 400)` shape, which the installed
handlers render per face (kosha object on `/api/v1/*`, C-SALT bare string on
`/dicts/*`).

`tests/test_bounded_params.py` introspects `app.routes` and fails on any
fenced parameter that does not declare its bounds here, so a new unbounded
parameter cannot ship silently.
"""
from fastapi import Query

from kosha.api.errors import raise_error

#: Documented caps. LIMIT/SIZE share the 1..200 window the search face has
#: published since BH-K2; UI pagination depends on the 200 ceiling staying.
LIMIT_MIN = 1
LIMIT_MAX = 200
#: OFFSET starts at 0; the cap exists so a crawler cannot walk the whole table
#: one row at a time with invisible cost per hop.
OFFSET_MIN = 0
OFFSET_MAX = 10_000_000
#: `ids` is one query per id — a hard cap keeps a 10^5-element query string
#: from turning into a sequential scan of the entries table.
IDS_MAX = 100


def bounded_int(name: str, *, default: int, minimum: int, maximum: int):
    """A FastAPI dependency validating one bounded query integer.

    The bounds travel in `json_schema_extra` — documentation, not enforcement,
    because schema-level constraints would 422 before this body ever ran. The
    enforcement here raises the house 400.
    """
    def dep(
        value: int = Query(
            default,
            alias=name,
            description=f"integer in [{minimum}, {maximum}]",
            json_schema_extra={"minimum": minimum, "maximum": maximum},
        ),
    ):
        if not minimum <= value <= maximum:
            raise_error(
                "bad_request", f"{name} must be between {minimum} and {maximum}", 400
            )
        return value

    return dep


def bounded_ids(*, maximum: int = IDS_MAX):
    """A FastAPI dependency capping a repeated `ids` query collection."""
    def dep(
        ids: list[str] = Query(
            None,
            alias="ids",
            description=f"at most {maximum} ids",
            json_schema_extra={"maxItems": maximum},
        ),
    ):
        if ids is None:
            ids = []
        if len(ids) > maximum:
            raise_error(
                "bad_request", f"ids must contain at most {maximum} values", 400
            )
        return ids

    return dep


#: The shared instances. Same shape as the defaults they replace, so callers
#: change only the parameter line, not their semantics.
limit_bounded = bounded_int("limit", default=50, minimum=LIMIT_MIN, maximum=LIMIT_MAX)
size_bounded = bounded_int("size", default=25, minimum=LIMIT_MIN, maximum=LIMIT_MAX)
offset_bounded = bounded_int(
    "offset", default=0, minimum=OFFSET_MIN, maximum=OFFSET_MAX
)
ids_bounded = bounded_ids()
