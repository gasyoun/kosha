"""Compatibility shim (D11) — Salt serialization moved into the package.

W0C (H1945) replaced this module's hand-built entry dict with the single
serializer in
[`src/kosha/api/serializer.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/serializer.py),
which `/api/v1`, the `/dicts/*` faces, the static cards and SSR now all consume.
The strict Salt compatibility face is a projection of that full model.
What used to live here — the `salt_common.php` id-minting port and the entry
shape — lives there; this file keeps the old import surface working.

The one behavioural change worth naming: `salt_entry` used to emit `sense: []`
and `evidence: []` unconditionally, because it had no access to the sense spans
or the lemma spine. The shared serializer fills both.
"""

from kosha.api.repository import entries_for_key  # noqa: F401
from kosha.api.serializer import mint_salt_id as _mint, salt_face_entry_dict, serialize_entry


def mint_salt_id(dict_code: str, slp1_key: str, lnum: str, body: str, hom_count: int) -> str:
    """Pre-W0C signature (it took an unused `dict_code`), kept for callers."""
    return _mint(slp1_key, lnum, body, hom_count)


def salt_entry(con, row, hom_count: int, data_version_str: str) -> dict:
    """Row → Salt entry dict, via the shared serializer."""
    from kosha.settings import get_settings

    return salt_face_entry_dict(
        serialize_entry(
            con,
            row,
            hom_count=hom_count,
            data_version=data_version_str,
            public_base=get_settings().public_base,
        )
    )
