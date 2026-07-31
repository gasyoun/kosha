"""kosha feature gates (W0B item 3, H1944).

D10: history, magic-link auth, and analytics stay off for public v1. The gate
is not a per-handler `if` — the routers are simply not mounted, so the paths
404 and never appear in the OpenAPI schema. That is the difference between a
feature that is *disabled* and one that is *absent*, and only the second is
defensible for a public deployment that stores visitor data when enabled.

`mount_history` exists for the tests that must exercise the surface. It is a
context manager that attaches the router to a live app and detaches it again,
because `app/main.py` builds its `FastAPI` instance at import time and pytest
imports that module once per session — an environment variable set inside a
test would arrive far too late.
"""

from __future__ import annotations

from contextlib import contextmanager

from .settings import Settings, get_settings


def history_enabled(settings: Settings | None = None) -> bool:
    """Is the history/auth/stats surface switched on for this process?"""
    return (settings or get_settings()).enable_history


@contextmanager
def mount_history(app, router=None):
    """Temporarily mount the history router on `app`.

    Restores the exact route list on exit, including the cached OpenAPI
    schema, so a test that enables history cannot leak the surface into the
    next test that asserts it is absent.
    """
    if router is None:
        from history import router as history_router  # noqa: PLC0415

        router = history_router

    before = list(app.router.routes)
    schema = app.openapi_schema
    app.openapi_schema = None
    app.include_router(router)
    try:
        yield app
    finally:
        app.router.routes[:] = before
        app.openapi_schema = schema
