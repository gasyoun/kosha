# Metadoc — DECISION_H2768_SALT_FACE_EXTENSION_CONTRACT

_Created: 16-08-2026 · Last updated: 16-08-2026_

## Purpose

Provenance and maintenance contract for the decision that separates kosha's
full entry model from its strict C-SALT compatibility projection.

## Audience

Maintainers changing `/dicts/*`, `/api/v1`, entry serialization, or Salt
compatibility claims.

## Provenance

| Field | Value |
|---|---|
| Handoff | [H2768 archive](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2768-Codex_kosha_salt-face-kosha-extension-contract_14.08.26.md) |
| Delivery | [kosha PR #404](https://github.com/gasyoun/kosha/pull/404) |
| Release | [v0.110.13](https://github.com/gasyoun/kosha/releases/tag/v0.110.13) |
| Executor | Codex Sol (`gpt-5.6-sol`) |
| Normative source | CSL Salt API Profile v0.1.0 §8–9 at `csl-standards` commit `490e062` |
| Verification | targeted Salt/parity 29 passed; full Python 572 passed / 165 skipped; UI 42 passed + build |

## Maintenance rule

The decision record is authoritative. Any change to the public-face split must
update the profile-derived key fixture and shared-field parity test in the same
PR. Historical H1945 prose yields to this decision where it claimed full-entry
equality on `/dicts/*`.

## Revision history

| Date | Change |
|---|---|
| 16-08-2026 | Initial metadoc after strict-face delivery and release |

---

_Dr. Mārcis Gasūns_
