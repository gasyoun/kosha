"""kosha — Gasuns Sanskrit Dictionary.

The installable package half of the repo (W0B / H1944). `app/` and `scripts/`
stay as top-level compatibility entry points and import from here; nothing was
moved out of them, so `uvicorn app.main:app` and `python scripts/build_db.py`
keep working exactly as the runbooks document.
"""

__version__ = "0.96.1"

__all__ = ["__version__"]
