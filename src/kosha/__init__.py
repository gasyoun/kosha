"""kosha — installable runtime package (W0B, H1944).

D12 of the [architecture plan of record](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_ARCHITECTURE_ROADMAP_2026_2027.md)
adopts `pyproject.toml` plus a committed dependency lock, so the runtime stops
depending on `sys.path` injection. D11 keeps `app/` and `scripts/` working as
compatibility shims while the move happens incrementally — nothing in this
package may assume those shims are gone.

Import surface kept deliberately small: settings and the build DAG. Everything
else still lives under `app/` and `scripts/` until a later wave moves it.
"""

__version__ = "0.96.1"

__all__ = ["__version__"]
