"""kosha — typed settings (W0B / H1944).

Before this module every path was a module-level constant computed at import
time (`app/db.py` DB_PATH, `app/versions.py` releases_dir(),
`app/history_db.py` HISTORY_DB_PATH, `scripts/build_db.py` DB_PATH), each with
its own env-var spelling or none at all. `.env.example` advertised
`DATABASE_PATH`, which **nothing read** — setting it changed nothing and no
error said so.

What this fixes, and the contract callers can rely on:

* One typed, validated settings object for the five paths the service and the
  build chain share — core DB, inflections DB, layers DB, archive dir, public
  citation base — plus the history feature flag.
* `DATABASE_PATH` is preserved as a **deprecated alias** for the core DB. It
  now genuinely takes effect, and emits a `DeprecationWarning` naming its
  replacement.
* **Conflicts fail loudly.** Setting both `KOSHA_CORE_DB` and `DATABASE_PATH`
  to different paths raises `SettingsConflict` at load time rather than
  silently honouring one of them. Setting both to the *same* path is fine.

`inflections_db` and `layers_db` default to the core DB: the physical DB split
is an explicit H1944 non-goal, so today all three point at one file. They exist
as separate settings so the split, when it happens, is a config change rather
than a code change — and so the build chain can already address them by role.
"""
from __future__ import annotations

import os
import warnings
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
    "KoshaSettings",
    "SettingsConflict",
    "get_settings",
    "reload_settings",
    "repo_root",
]

# Canonical env var -> legacy/deprecated spelling(s) that still work.
# `deprecated=True` adds a DeprecationWarning when the legacy name is the one
# that supplied the value.
_ALIASES: dict[str, tuple[tuple[str, bool], ...]] = {
    "KOSHA_CORE_DB": (("DATABASE_PATH", True),),
    "KOSHA_ARCHIVE_DIR": (("KOSHA_RELEASES_DIR", False),),
    "KOSHA_HISTORY_DB": (("HISTORY_DB_PATH", False),),
}

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


class SettingsConflict(RuntimeError):
    """A canonical env var and one of its aliases disagree."""


def repo_root() -> Path:
    """The checkout root. `KOSHA_ROOT` wins; otherwise walk up from this file.

    Walking up rather than hardcoding `parents[2]` keeps the answer correct
    when the package is imported from an installed distribution whose layout
    differs from the checkout's.
    """
    env = os.environ.get("KOSHA_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "pyproject.toml").is_file() and (candidate / "app").is_dir():
            return candidate
    # Installed without the checkout: fall back to the working directory, so
    # relative defaults stay meaningful instead of pointing into site-packages.
    return Path.cwd()


def _read_env(canonical: str) -> tuple[str | None, str]:
    """Resolve one setting from the environment, honouring aliases.

    Returns (value, source-var-name). Raises SettingsConflict when a canonical
    and an alias are both set to different values.
    """
    values: list[tuple[str, str]] = []
    canonical_value = os.environ.get(canonical)
    if canonical_value is not None:
        values.append((canonical, canonical_value))
    for alias, deprecated in _ALIASES.get(canonical, ()):
        alias_value = os.environ.get(alias)
        if alias_value is None:
            continue
        values.append((alias, alias_value))
        if deprecated and canonical_value is None:
            warnings.warn(
                f"{alias} is deprecated; use {canonical} instead. "
                f"{alias} still takes effect and will keep working, but it is "
                f"no longer the documented name.",
                DeprecationWarning,
                stacklevel=3,
            )
    if not values:
        return None, canonical
    distinct = {v for _, v in values}
    if len(distinct) > 1:
        detail = ", ".join(f"{name}={value!r}" for name, value in values)
        raise SettingsConflict(
            f"conflicting settings for {canonical}: {detail}. "
            f"Set one of them, or set both to the same value."
        )
    return values[0][1], values[0][0]


def _env_path(canonical: str, default: Path) -> Path:
    raw, _ = _read_env(canonical)
    if raw is None:
        return default
    path = Path(raw).expanduser()
    return path if path.is_absolute() else (repo_root() / path)


def _env_bool(canonical: str, default: bool) -> bool:
    raw, source = _read_env(canonical)
    if raw is None:
        return default
    lowered = raw.strip().lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    raise SettingsConflict(
        f"{source}={raw!r} is not a boolean; use one of "
        f"{sorted(_TRUE | _FALSE)}"
    )


class KoshaSettings(BaseModel):
    """Validated settings. Construct via `KoshaSettings.from_env()`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    core_db: Path
    inflections_db: Path
    layers_db: Path
    archive_dir: Path
    history_db: Path
    public_base: str
    enable_history: bool = False

    @field_validator("public_base")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        # Citation URLs are built by concatenation (app/cite.py); a trailing
        # slash here produced `//api/v1/...` in minted, durable citation ids.
        return value.rstrip("/")

    @classmethod
    def from_env(cls) -> "KoshaSettings":
        root = repo_root()
        core = _env_path("KOSHA_CORE_DB", root / "data" / "db" / "kosha.db")
        return cls(
            core_db=core,
            inflections_db=_env_path("KOSHA_INFLECTIONS_DB", core),
            layers_db=_env_path("KOSHA_LAYERS_DB", core),
            archive_dir=_env_path("KOSHA_ARCHIVE_DIR", root / "data" / "releases"),
            history_db=_env_path("KOSHA_HISTORY_DB", root / "data" / "db" / "kosha_history.db"),
            public_base=os.environ.get("KOSHA_PUBLIC_BASE", "http://localhost:8000"),
            enable_history=_env_bool("KOSHA_ENABLE_HISTORY", False),
        )


_cached: KoshaSettings | None = None


def get_settings() -> KoshaSettings:
    """Process-wide settings, resolved once."""
    global _cached
    if _cached is None:
        _cached = KoshaSettings.from_env()
    return _cached


def reload_settings() -> KoshaSettings:
    """Re-read the environment. For tests and for `--env`-style CLI reloads."""
    global _cached
    _cached = None
    return get_settings()
