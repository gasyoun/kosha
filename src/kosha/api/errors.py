"""kosha — top-level error normalization (W0C item 5, H1945).

Three different error shapes used to leave `/api/v1`:

1. `{"detail": {"error": {code, message, suggestions}}}` — the deliberate ones,
   raised through `main.error()`, with the real object buried one level inside
   FastAPI's `detail` wrapper;
2. `{"detail": [{"loc": …, "msg": …, "type": …}]}` — FastAPI's own request
   validation, a completely different schema;
3. `{"detail": "Internal Server Error"}` — anything unhandled.

A client therefore had to know three shapes to read one API. This module
installs handlers so exactly one shape leaves the service:

    {"error": {"code": "...", "message": "...", "suggestions": [...]}}

**The Salt faces are deliberately exempt.** `/dicts/*` is wire-compatible with
C-SALT, whose documented error form is a bare string
(`{"error": "Missing or invalid parameter: 'field'"}`, profile §3.2).
Normalizing those into kosha's richer object would break the compatibility
those routes exist to provide, so `install_error_handlers` leaves any response
a `/dicts/*` route produced alone. Two shapes, each documented, each owned by a
contract — as against three, owned by none.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from kosha.api.models import ErrorDetail, ErrorResponse

#: Path prefix whose error shape belongs to the Salt profile, not to kosha.
SALT_FACE_PREFIX = "/dicts/"


def error_response(
    code: str, message: str, status: int, suggestions: list[str] | None = None
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetail(code=code, message=message, suggestions=suggestions or [])
    )
    return JSONResponse(status_code=status, content=payload.model_dump(mode="json"))


def raise_error(
    code: str, message: str, status: int, suggestions: list[str] | None = None
):
    """Raise a kosha API error.

    The structured object travels as the `HTTPException.detail` because that is
    the only channel FastAPI offers, and `http_exception_handler` below unwraps
    it back to the top level on the way out — so route code keeps raising and
    clients still see a flat `error` key.
    """
    raise HTTPException(
        status_code=status,
        detail={"code": code, "message": message, "suggestions": suggestions or []},
    )


def _is_salt_face(request: Request) -> bool:
    return request.url.path.startswith(SALT_FACE_PREFIX)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if _is_salt_face(request):
        # C-SALT form: a bare string. `detail` may already be a dict from
        # `raise_error`; reduce it to its message so the face stays compatible.
        message = detail.get("message") if isinstance(detail, dict) else str(detail)
        return JSONResponse(status_code=exc.status_code, content={"error": message})
    if isinstance(detail, dict) and "code" in detail:
        return error_response(
            detail["code"],
            detail.get("message", ""),
            exc.status_code,
            detail.get("suggestions"),
        )
    # A bare `HTTPException(404)` from Starlette's own routing (an unknown path,
    # a method mismatch) still has to come out in the documented shape.
    return error_response(
        _CODE_BY_STATUS.get(exc.status_code, "http_error"),
        detail if isinstance(detail, str) else str(detail),
        exc.status_code,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Query/path validation failures, flattened into one readable message.

    FastAPI's default nests a list of `{loc, msg, type}` objects under `detail`;
    the profile and kosha's own contract both want a single message, so the
    field locations are folded into it rather than dropped.
    """
    parts = []
    for err in exc.errors():
        location = ".".join(str(piece) for piece in err.get("loc", ()) if piece != "body")
        parts.append(f"{location}: {err.get('msg', 'invalid')}" if location else err.get("msg", "invalid"))
    message = "; ".join(parts) or "invalid request"
    if _is_salt_face(request):
        return JSONResponse(status_code=400, content={"error": message})
    # 400, not FastAPI's 422: the Salt profile fixes 400 for a bad parameter,
    # and having kosha's own routes answer the same class of mistake with a
    # different status would be a contradiction inside one service.
    return error_response("bad_request", message, 400)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last resort. Deliberately says nothing about `exc`.

    An unhandled error is the one place a stack frame, a file path or a SQL
    fragment could reach a client; the log gets the detail, the response gets a
    code.
    """
    if _is_salt_face(request):
        return JSONResponse(status_code=500, content={"error": "internal error"})
    return error_response(
        "internal_error",
        "the server failed to handle this request",
        500,
    )


_CODE_BY_STATUS = {
    400: "bad_request",
    404: "not_found",
    405: "method_not_allowed",
    422: "bad_request",
    500: "internal_error",
}


def install_error_handlers(app: FastAPI) -> FastAPI:
    # Registered on Starlette's *base* class, not FastAPI's subclass. The
    # router raises the base one for an unknown path (404) and a method
    # mismatch (405), and a handler bound to the subclass never sees those —
    # so those two, the errors a client is most likely to hit first, would have
    # kept escaping as `{"detail": "Not Found"}` while every deliberate error
    # was normalized. Registering the base covers both, since FastAPI's
    # `HTTPException` inherits from it.
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    return app
