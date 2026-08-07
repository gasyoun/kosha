# Dataset + surface manifests — machine-readable kosha indices

_Created: 06-07-2026 · Last updated: 07-08-2026_

## Datasets

[`datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
is the ONE machine-readable list of canonical derived Sanskrit datasets across the ~85
sibling repos, in three tiers: **public** (downloadable from
[GitHub Releases `data-v*`](https://github.com/gasyoun/kosha/releases), later
`samskrtam.ru/kosha/data/`), **restricted** (rights-encumbered or local-only assets
that exist but are not published), and **intermediate** (raw/working data that feeds
another registered dataset — not standalone-citable, not rights-gated, just not a
finished asset in its own right; excluded from the rendered public directory page).

Rules, architecture, and phase plan:
[`DATA_HUB_ROADMAP.md`](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md).
Human-readable catalogues this file serves the bytes for:
[`REUSE_INDEX.md`](https://github.com/gasyoun/Uprava/blob/main/REUSE_INDEX.md) ·
[`FEATURES_INDEX.md`](https://github.com/gasyoun/SanskritLexicography/blob/master/FEATURES_INDEX.md).

**Agent contract (datasets):** before deriving any alignment / frequency / headword /
crosswalk asset, check this manifest. A session that creates or changes a derived
dataset must add/update its row here in the same pass — a deliverable without a
manifest row does not exist for reuse purposes.

## Generated surfaces (W1B / D15)

[`surfaces.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/surfaces.json)
lists every committed and out-of-band public surface that ships with kosha (API,
SSR, static cards, Pages tools, reading/concordance viewers). Each row declares
id, audience, source datasets, builder, output paths, rights tier, acceptance
command, deploy owner, and rollback method. Validate with:

```text
python scripts/validate_surfaces.py
```

**Agent contract (surfaces):** a session that adds or materially changes a shipping
surface must update this registry in the same pass. Dictionary-payload surfaces must
consume `kosha.api.repository` + `kosha.api.serializer` (no mirrored payload code).

Public-tier data license: [CC BY-SA 4.0](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md).

_Dr. Mārcis Gasūns_
