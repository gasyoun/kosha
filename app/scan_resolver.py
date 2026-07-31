"""Compatibility shim (D11) — this module now lives in the installed package.

W0C (H1945) moved it to
[`src/kosha/scan_resolver.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/scan_resolver.py)
so `kosha.api.serializer` can import it without a `sys.path` insert. The
bare-name import (`from scan_resolver import …`) that `app/` and `scripts/` have used
since Phase 1 keeps working through this re-export; new code should import
`kosha.scan_resolver` directly.
"""

from kosha.scan_resolver import *  # noqa: F401,F403
