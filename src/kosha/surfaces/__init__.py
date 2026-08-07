"""Generated-surface registry (W1B, H2342).

Architecture D15 / Static surfaces: every committed and out-of-band public
surface that ships with kosha declares inputs, builder, outputs, rights tier,
deploy owner, rollback method, and a deterministic acceptance command.

The machine-readable source is
[`data/manifest/surfaces.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/surfaces.json).
Validation lives here so CI and the CLI share one implementation.
"""

from .registry import (
    REQUIRED_FIELDS,
    RegistryReport,
    SurfaceError,
    default_registry_path,
    load_registry,
    validate_registry,
    validate_surface,
)

__all__ = [
    "REQUIRED_FIELDS",
    "RegistryReport",
    "SurfaceError",
    "default_registry_path",
    "load_registry",
    "validate_registry",
    "validate_surface",
]
