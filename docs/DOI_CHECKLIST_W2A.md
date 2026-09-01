# W2A DOI checklist — superseded by an automated mint

_Created: 08-08-2026 · Last updated: 01-09-2026_

Companion to [H2346](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2346-Grok_kosha_architecture-roadmap-w2a-immutable-sense-archives_07.08.26.md)
(immutable sense archives). **This checklist described a world that no longer
exists.** As written on 08-08-2026 it said DOIs were minted by hand by MG, that
an agent "must not claim a DOI was minted", and that empty cells were correct.
Two things then changed and this file was not updated for either:

1. **14-08-2026 — the GitHub–Zenodo webhook was wired.** DOIs are no longer
   minted by anyone; Zenodo mints one automatically per pushed tag. 21 deposits
   exist as of 01-09-2026.
2. **16-08-2026 — standing ruling.** Agents may mint DOIs and cut public
   releases. [/publish-safety-check](https://github.com/gasyoun/claude-config/blob/main/commands/publish-safety-check.md)
   still gates, and repository-visibility flips stay human.

Kept rather than deleted because the agent fence it asserted is quoted
elsewhere, and a reader who finds only silence cannot tell whether the fence
lapsed or was forgotten. It lapsed, on the dates above (H3788).

The live contract is
[VERSIONING_AND_CITATION_POLICY_KOSHA.md](https://github.com/gasyoun/kosha/blob/main/docs/VERSIONING_AND_CITATION_POLICY_KOSHA.md);
the current state is
[CITABLE_V1_RECORD_KOSHA_01.09.26.md](https://github.com/gasyoun/kosha/blob/main/docs/CITABLE_V1_RECORD_KOSHA_01.09.26.md).

## Current DOI state (01-09-2026, verified against the Zenodo API)

| Field | Value |
|---|---|
| Concept DOI | [`10.5281/zenodo.21965599`](https://doi.org/10.5281/zenodo.21965599) — always resolves to the latest archived version |
| Latest version DOI | [`10.5281/zenodo.22231444`](https://doi.org/10.5281/zenodo.22231444) (`v0.117.1`, 01-09-2026) |
| Latest data-release DOI | [`10.5281/zenodo.22105641`](https://doi.org/10.5281/zenodo.22105641) (`data-v0.5.0`, 26-08-2026) |
| Archived deposits | 21 |
| First archived release | `v0.110.13`, 16-08-2026 |
| Minting | automatic, per pushed tag, since the webhook of 14-08-2026 |

## What is still owed after a data release is cut

The DOI arrives on its own; these do not.

- [ ] Freeze the release manifest and attach it as the release's `datasets.json`:
      `python scripts/freeze_release_manifest.py freeze --tag data-vX.Y.Z --out data/manifest/frozen/data-vX.Y.Z.datasets.json --version-doi <minted>`
- [ ] Record the minted version DOI in the frozen manifest's `version_doi`
      (rerun the freeze once Zenodo has archived the tag) and in the affected
      manifest rows' `notes`.
- [ ] Point `interim_release` in
      [data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
      at the new tag and bump `generated` — `update_manifest.py refresh`
      deliberately leaves both to a human.
- [ ] Confirm the uploaded asset bytes match the frozen manifest's LF-canonical
      `sha256`. **Cut from a clean checkout**: the freezer refuses a CRLF
      working tree precisely because assets uploaded from one cannot match.
- [ ] One-line note in [CHANGELOG.md](https://github.com/gasyoun/kosha/blob/main/CHANGELOG.md)
      under the data-release section.

## What must not happen

- **Never hand-pick a version DOI into `CITATION.cff`.** The concept DOI belongs
  there. A hand-written version DOI is stale at the next tag — that is precisely
  how the file came to advertise `v0.115.1` as the latest archived release while
  `v0.117.1` was live.
- **Never move a released tag.** Zenodo mints a *new* DOI on every release
  event, so moving a tag adds a contradictory deposit rather than correcting
  one. `v0.116.0` carries two DOIs for this reason, and deposits cannot be
  withdrawn.

_Dr. Mārcis Gasūns_
