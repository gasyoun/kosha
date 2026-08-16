# H2768 decision — strict Salt compatibility face

_Decided: 16-08-2026 · Executor: Codex Sol (`gpt-5.6-sol`)_

## Decision

`/dicts/{id}/restful/entries` and `/dicts/{id}/restful/ids` use the
**strict-face** contract. Each entry exposes only the six C-SALT fields from
Salt profile §8.1 plus the `csl` extension permitted by §8.2/§9. The
top-level `kosha` object is not emitted on these compatibility routes.

`/api/v1`, static cards, and SSR keep the full kosha contract, including the
namespaced `kosha` object. This preserves kosha data and does not change the
normative Salt profile.

## Implementation boundary

One repository query and one `SaltEntry` serializer remain authoritative.
`serializer.salt_face_entry_dict()` is a terminal wire projection, not a
second serializer: it selects the normative top-level keys from the already
validated full entry. Shared Salt and `csl` values therefore remain identical
between `/api/v1` and `/dicts/*`, while the public contracts no longer claim
full-object equality.

## Normative evidence

- CSL Salt API Profile v0.1.0 §9: `xml` may be null and an entry may add
  `csl`; no other structural divergence is permitted.
- Machine-readable companion at `csl-standards` commit `490e062`,
  `data/schema/salt-api.openapi.yaml`, defines the six C-SALT properties and
  `csl` on `Entry`.
- `tests/contracts/salt-entry-v0.1.0.json` freezes that normative top-level key
  set and its source commit for offline CI.

## Rejected alternative

A profile amendment allowing a `kosha` extension was rejected. `kosha` is a
derivative application's namespace, not an extension every conforming CSL Salt
host needs. Strict projection is smaller, preserves C-SALT clients, and keeps
all kosha data on kosha-owned surfaces.

## Regression contract

`tests/test_salt_profile.py` compares actual `/dicts/*` HTTP entry keys to the
profile-derived fixture without validating through the full Pydantic model.
`tests/test_contract_parity.py` independently compares each strict face entry
to the same key projection of its `/api/v1` entry.

---

_Dr. Mārcis Gasūns_
