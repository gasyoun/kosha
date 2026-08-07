"""kosha — typed runtime settings (W0B item 2, H1944).

One typed object replaces the scattered `os.getenv` reads in `app/main.py`,
`app/db.py`, `app/history_db.py`, and the build scripts. It covers the five
storage locations D7 splits the store into (core, attached inflections,
attached public layers, the citation archive, and the writable history DB),
the public citation base (D9/R1), and the D10 feature flags that keep history,
auth, and analytics off for public v1.

W1A (H2341): `kosha.query.open_query_connection` consumes `core_db` /
`inflections_db` / `layers_db` and ATTACHes the latter two with stable aliases
when the files exist. History stays a separate writable store — never attached
on the dictionary query path.

Two rules this module exists to enforce mechanically:

1. **`DATABASE_PATH` is a deprecated alias for the core DB**, kept because
   `.env.example` has shipped it since Phase 1 and existing local `.env` files
   still carry it. It still works, it emits a `DeprecationWarning`, and a
   *conflicting* pair (`DATABASE_PATH` and `KOSHA_CORE_DB_PATH` naming different
   files) is a hard error rather than a silent winner — the exact
   configuration contradiction the freeze-exit checklist forbids.
2. **History/auth/stats default to off.** `KOSHA_HISTORY_ENABLED` must be
   explicitly truthy for those routers to be mounted at all (D10).

Local-first (A3): every path default stays inside the repo, nothing here
reaches a network service, and no credential is read.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Mapping

from pydantic import BaseModel, ConfigDict, field_validator

# Repo root = the directory holding this package's `src/` parent.
ROOT = Path(__file__).resolve().parents[2]

#: `.env` keys that were read directly before W0B, mapped to their typed name.
#: `DATABASE_PATH` is a genuine rename; `KOSHA_RELEASES_DIR` is the citation
#: archive's pre-W0C name (see `archive_dir` below).
DEPRECATED_ALIASES = {
    "DATABASE_PATH": "KOSHA_CORE_DB_PATH",
    "KOSHA_RELEASES_DIR": "KOSHA_ARCHIVE_DIR",
}

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}


class SettingsError(RuntimeError):
    """Raised for a configuration contradiction that must not be papered over."""


def _as_bool(raw: str | None, *, key: str, default: bool = False) -> bool:
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise SettingsError(
        f"{key}={raw!r} is not a boolean; use one of {sorted(_TRUE | _FALSE - {''})}"
    )


class Settings(BaseModel):
    """Typed view of the runtime configuration.

    Frozen: settings are resolved once per process. Anything that needs a
    different store (the fixture build, a test) constructs its own instance
    rather than mutating the shared one.
    """

    model_config = ConfigDict(frozen=True)

    # --- storage (D7: core / attached inflections / attached layers) --------
    core_db: Path
    inflections_db: Path
    layers_db: Path
    #: Writable search-history store. Separate file so a dictionary rebuild
    #: never touches visitor data; only opened when `enable_history` is true.
    history_db: Path
    #: Immutable citation archive mount (D9). Absence is not an error here —
    #: the release gate checks it, not the runtime.
    #:
    #: W0C (H1945) made this the *only* name for that mount. W0B introduced
    #: `archive_dir` (default `data/archive`) while `app/versions.py` went on
    #: reading its own `KOSHA_RELEASES_DIR` (default `data/releases`) — two
    #: settings for one directory, defaulting to two different places, so
    #: pointing the documented knob at a mounted release archive moved nothing
    #: and every citation kept resolving against the old path. The default is
    #: now `data/releases`, the directory the mechanism actually reads, and the
    #: old name is accepted as a deprecated alias.
    archive_dir: Path

    # --- public surface -----------------------------------------------------
    #: Citation URL host. Deliberately NOT the samskrtam.ru deployment host
    #: (RISKS.md R1/R5): citations must resolve independent of where the live
    #: server runs.
    public_base: str

    # --- feature gates (D10: off for public v1) -----------------------------
    enable_history: bool = False

    @field_validator("public_base")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        root: Path | None = None,
    ) -> "Settings":
        """Build settings from a mapping (defaults to `os.environ`).

        Raises `SettingsError` when a deprecated alias contradicts its typed
        replacement. Deprecated-but-consistent use only warns.
        """
        env = os.environ if env is None else env
        root = ROOT if root is None else root

        core = env.get("KOSHA_CORE_DB_PATH")
        legacy = env.get("DATABASE_PATH")
        if legacy is not None:
            warnings.warn(
                "DATABASE_PATH is deprecated; use KOSHA_CORE_DB_PATH "
                "(it names the core dictionary DB under the D7 split).",
                DeprecationWarning,
                stacklevel=2,
            )
            if core is not None and _norm(core, root) != _norm(legacy, root):
                raise SettingsError(
                    "conflicting core-DB configuration: "
                    f"KOSHA_CORE_DB_PATH={core!r} and DATABASE_PATH={legacy!r} "
                    "resolve to different files. Remove DATABASE_PATH."
                )
            core = core if core is not None else legacy

        data_db = root / "data" / "db"
        return cls(
            core_db=_norm(core, root) if core else data_db / "kosha.db",
            inflections_db=(
                _norm(env["KOSHA_INFLECTIONS_DB_PATH"], root)
                if env.get("KOSHA_INFLECTIONS_DB_PATH")
                else data_db / "kosha_inflections.db"
            ),
            layers_db=(
                _norm(env["KOSHA_LAYERS_DB_PATH"], root)
                if env.get("KOSHA_LAYERS_DB_PATH")
                else data_db / "kosha_layers.db"
            ),
            history_db=(
                _norm(env["HISTORY_DB_PATH"], root)
                if env.get("HISTORY_DB_PATH")
                else data_db / "kosha_history.db"
            ),
            archive_dir=_resolve_archive_dir(env, root),
            public_base=env.get("KOSHA_PUBLIC_BASE", "http://localhost:8000"),
            enable_history=_as_bool(
                env.get("KOSHA_HISTORY_ENABLED"), key="KOSHA_HISTORY_ENABLED"
            ),
        )


def _resolve_archive_dir(env: Mapping[str, str], root: Path) -> Path:
    """The citation-archive mount, from either name (W0C, H1945).

    Same contract as the `DATABASE_PATH` alias above: the deprecated name still
    works and warns, but a *contradicting* pair is a hard error rather than a
    silent winner — a deployment that mounts release assets at one path and
    resolves citations from another would answer "not archived" for citations
    it is in fact serving, and nothing would say why.
    """
    typed = env.get("KOSHA_ARCHIVE_DIR")
    legacy = env.get("KOSHA_RELEASES_DIR")
    if legacy is not None:
        warnings.warn(
            "KOSHA_RELEASES_DIR is deprecated; use KOSHA_ARCHIVE_DIR "
            "(it names the immutable citation archive mount, D9).",
            DeprecationWarning,
            stacklevel=3,
        )
        if typed is not None and _norm(typed, root) != _norm(legacy, root):
            raise SettingsError(
                "conflicting citation-archive configuration: "
                f"KOSHA_ARCHIVE_DIR={typed!r} and KOSHA_RELEASES_DIR={legacy!r} "
                "resolve to different directories. Remove KOSHA_RELEASES_DIR."
            )
        typed = typed if typed is not None else legacy
    if typed:
        return _norm(typed, root)
    return root / "data" / "releases"


def _norm(value: str | Path, root: Path) -> Path:
    """Resolve a configured path against the repo root when it is relative."""
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = root / path
    # `resolve()` without strict=True so a not-yet-built target still normalizes.
    return Path(os.path.normpath(path))


_cached: Settings | None = None
_dotenv_loaded = False


def _load_dotenv_once() -> None:
    """Fold `.env` into the environment before the first settings read.

    `app/main.py` used to call `load_dotenv()` *after* importing `app/db.py`,
    so a `DATABASE_PATH` in `.env` never reached the module that needed it.
    Doing it here makes the load order irrelevant: whoever asks for settings
    first triggers it.
    """
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    _dotenv_loaded = True
    try:
        from dotenv import load_dotenv
    except ImportError:  # dotenv is optional for pure build usage
        return
    load_dotenv()


def get_settings(*, refresh: bool = False) -> Settings:
    """Process-wide settings, resolved once.

    `refresh=True` re-reads the environment — used by tests that patch env
    vars, never by request handling.
    """
    global _cached
    if _cached is None or refresh:
        _load_dotenv_once()
        _cached = Settings.from_env()
    return _cached
