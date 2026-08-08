"""kosha — versioned deployment bundle assembly (W1D, H2344).

Local-first packaging only. Agents assemble digests, runbooks, and local
rehearsals; production deploy stays human-only (A3).
"""

from kosha.deploy.bundle import (
    AssembleError,
    BundleReport,
    assemble_bundle,
    default_recipe_path,
    load_recipe,
    validate_recipe,
)

__all__ = [
    "AssembleError",
    "BundleReport",
    "assemble_bundle",
    "default_recipe_path",
    "load_recipe",
    "validate_recipe",
]
