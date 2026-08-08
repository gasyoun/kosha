# W2A DOI checklist (MG-minted — agent does not mint)

_Created: 08-08-2026 · Last updated: 08-08-2026_

Companion to [H2346](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2346-Grok_kosha_architecture-roadmap-w2a-immutable-sense-archives_07.08.26.md)
(immutable sense archives). The engineering half ships archives + checksums +
historical-resolution tests. **DOI mint remains MG.**

## After MG mints a concept + version DOI for a data release

- [ ] Record concept DOI and version DOI in this table
- [ ] Update [CITATION.cff](https://github.com/gasyoun/kosha/blob/main/CITATION.cff)
      `identifiers` / `doi` slots if the release is the citable data snapshot
- [ ] Point `data/manifest/datasets.json` release rows at the Zenodo landing page
      when the deposit covers those assets
- [ ] Confirm `release_asset_url` / GitHub `data-{version}/senses.sqlite` still
      matches the deposited bytes (sha256 from `release.json`)
- [ ] One-line note in CHANGELOG under the data-release section

| Field | Value |
|---|---|
| Concept DOI | _(MG fills)_ |
| Version DOI | _(MG fills)_ |
| Data version pin | _(e.g. data-vX.Y.Z)_ |
| Zenodo URL | _(MG fills)_ |
| Date minted | |

## Agent fence

Agents must **not** claim a DOI was minted, invent Zenodo IDs, or mark this
checklist done. Empty cells are correct until MG fills them.

_Dr. Mārcis Gasūns_
