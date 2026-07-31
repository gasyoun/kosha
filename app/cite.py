"""Compatibility shim (D11) — this module now lives in the installed package.

W0C (H1945) moved it to
[`src/kosha/cite.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/cite.py)
so `kosha.api.serializer` can import it without a `sys.path` insert. The
bare-name import (`from cite import …`) that `app/` and `scripts/` have used
since Phase 1 keeps working through this re-export; new code should import
`kosha.cite` directly.
"""

from kosha.cite import *  # noqa: F401,F403
