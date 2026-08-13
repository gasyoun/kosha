"""kosha API contract layer (W0C, H1945).

The typed boundary every public surface serializes through:

* [`models`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/models.py)
  — the Salt-profile entry, envelope and error objects (D6/D13);
* [`repository`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/repository.py)
  — the one entry-reading query layer;
* [`serializer`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/serializer.py)
  — rows → Salt entries, shared by the API, the Salt faces, the static cards
  and SSR;
* [`sanitize`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/sanitize.py)
  — the rendered-HTML allowlist every one of those crosses;
* [`errors`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/errors.py)
  — one documented error shape per contract;
* [`archive`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/archive.py)
  — citation-archive validation;
* [`readiness`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/readiness.py)
  — DB / version / archive / optional-writable readiness (W1C);
* [`catalog`](https://github.com/gasyoun/kosha/blob/main/src/kosha/api/catalog.py)
  — public dataset catalog over `data/manifest/datasets.json` (W2B / P-D6).
"""

from kosha.api.models import (
    CiteObject,
    CslBlock,
    Envelope,
    ErrorDetail,
    ErrorResponse,
    HeritageWitness,
    KoshaBlock,
    SaltEntry,
)
from kosha.api.sanitize import sanitize_html
from kosha.api.serializer import (
    entry_dict,
    mint_salt_id,
    serialize_entry,
    serialize_lemma_card,
)

__all__ = [
    "CiteObject",
    "CslBlock",
    "Envelope",
    "ErrorDetail",
    "ErrorResponse",
    "HeritageWitness",
    "KoshaBlock",
    "SaltEntry",
    "entry_dict",
    "mint_salt_id",
    "sanitize_html",
    "serialize_entry",
    "serialize_lemma_card",
]
