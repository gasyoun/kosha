# Versioning and citation policy — kosha

_Created: 01-09-2026 · Last updated: 01-09-2026_

The W2 "citable v1" rung of
[ROADMAP_KOSHA_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026_2027.md)
names four things a citer needs: a DOI, citation metadata, a frozen dataset
manifest, and **a stated versioning policy**. The first three existed and were
undocumented; this file is the fourth. Minted under
[H3788](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3788-Opus_kosha_kosha-2026-2027-w2-citable-v1_31.08.26.md).

Written because the rules below were already in force implicitly — in
[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)
§A2, in `.gitattributes`, in the shape of the release tags — and an implicit
rule cannot be cited, tested, or shown to have been broken. Two of them had
been broken without anyone noticing.

## 1. Three version lines, deliberately independent

| Line | Tag form | What it versions | Bumped by |
|---|---|---|---|
| Code | `vX.Y.Z` | the FastAPI service, UI, build scripts, docs | every merged release PR ([/cut-release](https://github.com/gasyoun/claude-config/blob/main/commands/cut-release.md)) |
| Data release | `data-vX.Y.Z` | the published public-tier dataset assets | a deliberate data cut, not a code release |
| Sense/citation base | `data_version` (e.g. `0.1.0-dev`) | the sense numbering a citation resolves against | a rebuild that renumbers senses |

These are **not** kept in step and must not be. A code release that changes a
template must not invalidate a citation; a sense renumbering must not wait for a
UI fix. `data_version` is the one that carries citation semantics:
`mw.142512.3@0.1.0-dev` resolves against the sense numbering of that base
forever, live from the database while the base is current and from the archived
`senses.sqlite` afterwards.

`CITATION.cff`'s `version` tracks the **code** line, because Zenodo archives
GitHub tags and the software record is what the concept DOI points at.

## 2. DOIs — one concept, one per version, minted automatically

- **Concept DOI `10.5281/zenodo.21965599`** resolves to the latest archived
  version, always. This is the DOI to cite when the citer means "kosha", not a
  specific state. It is the only DOI hardcoded anywhere in this repo.
- **Version DOIs are minted by Zenodo, never by hand.** The GitHub–Zenodo
  webhook was wired 14-08-2026 and has archived every tag pushed since; as of
  01-09-2026 that is 21 deposits, the newest being `v0.117.1` →
  `10.5281/zenodo.22231444`.
- The webhook archives **every** tag, so `data-v*` tags get version DOIs under
  the same concept as the code tags. `data-v0.4.0` → `10.5281/zenodo.22102090`,
  `data-v0.5.0` → `10.5281/zenodo.22105641`. This is intended: one concept
  record for the whole artifact family.
- Tags pushed **before** 14-08-2026 have no DOI and cannot retroactively get
  one. `data-v0.1.0` through `data-v0.3.0` are in that band; where a DOI was
  needed the content was re-cut under a new tag (that is what `data-v0.4.0` and
  `data-v0.5.0` are — re-cuts of identical `data-v0.1.0` content).
- Agents may mint DOIs and cut public releases (standing ruling 16-08-2026).
  [/publish-safety-check](https://github.com/gasyoun/claude-config/blob/main/commands/publish-safety-check.md)
  still gates, and repository-visibility flips remain human.

**Do not hand-pick a version DOI into `CITATION.cff`.** The concept DOI belongs
there; a version DOI written by hand is stale the moment the next tag is pushed,
which is exactly how the file came to name `v0.115.1` as "latest" while
`v0.117.1` was live.

## 3. A released tag is immutable

Once a tag is pushed it is never moved, re-pointed, or deleted and recreated.

This is not a style preference. Zenodo mints a **new version DOI on every
release event**, so moving a tag does not correct the record — it adds a second,
contradictory one under the same version string. That happened on 27-08-2026:

| Deposit | DOI | Archived | Asset size |
|---|---|---|---|
| first | `10.5281/zenodo.22131151` | 2026-08-27T15:43Z | 187,386,121 B |
| second | `10.5281/zenodo.22132415` | 2026-08-27T17:37Z | 187,389,165 B |

Both are titled `v0.116.0` and both point at
`https://github.com/gasyoun/kosha/tree/v0.116.0`, with 3,044 bytes between them.
A citation reading "kosha v0.116.0" is therefore ambiguous, permanently — Zenodo
deposits cannot be withdrawn. `10.5281/zenodo.22132415` is the one that matches
the tag as it now stands; the earlier deposit is superseded and should not be
cited.

If a release is wrong, cut the next patch version. Never move the tag.

## 4. Release bytes are LF-canonical

`.gitattributes` declares `* text=auto eol=lf`: the LF form of every text asset
is this repository's canonical byte sequence. Every published dataset asset, and
every checksum asserted about one, is over that form.

The trap this rule exists for: **git does not renormalize files already in a
working tree when `.gitattributes` changes.** A Windows checkout made before the
rule landed keeps CRLF indefinitely, `git status` stays clean because git
normalizes on the fly when comparing, and a release cut from that checkout
uploads assets one byte per line larger than the canonical file. Nothing warns.

H3788 found the consequences on 01-09-2026:

- **28 manifest rows** recorded a `size_bytes` exactly one byte per line above
  the canonical file — the signature of a `refresh` run in a CRLF checkout.
  Rows in `data-v0.2.0`, `data-v0.3.0` and `data-v0.5.0` were affected, i.e.
  three DOI-archived releases.
- `kosha-lemma-frequency` is the worked case: canonical 4,827,466 B, CRLF
  4,910,744 B, delta 83,278 = exactly the line count. The **published**
  `data-v0.5.0` asset is 4,910,744 B, so the release carries the CRLF variant.
  Both forms have identical content; only one is reproducible from a clean
  checkout.

Consequences that are now rules:

1. A checksum is asserted over the **LF-canonical** form, so a citer on any
   platform can reproduce it.
   [scripts/freeze_release_manifest.py](https://github.com/gasyoun/kosha/blob/main/scripts/freeze_release_manifest.py)
   computes digests that way and records `sha256_form: lf-canonical`.
2. A release is **never cut from a CRLF working tree**. The freezer refuses,
   naming the offending rows; `git add --renormalize .` or a fresh
   clone/worktree is the fix. The `--allow-crlf-checkout` escape is for
   inspection only and stamps `checkout_warnings` into the output so the caveat
   travels with the artifact.
3. Scripts that write repository JSON open with `newline="\n"` explicitly —
   `Path.write_text` emits CRLF on Windows, which is how the manifest itself
   kept being written non-canonically.

## 5. The frozen release manifest

Each published `data-v*` release gets one frozen manifest under
[data/manifest/frozen/](https://github.com/gasyoun/kosha/tree/main/data/manifest/frozen),
generated by
[scripts/freeze_release_manifest.py](https://github.com/gasyoun/kosha/blob/main/scripts/freeze_release_manifest.py)
and attached to the release as `datasets.json`.

It is a **public-tier slice** of
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json),
selected on `in_release == <tag>`, carrying per-row id, title, asset name,
format, row count, canonical size, LF-canonical sha256, source repo/path, and
data statement — plus the tag, the commit it was cut from, the concept DOI, and
the version DOI once minted.

Two fences are load-bearing:

- **`tier != public` refuses the freeze rather than dropping the row.** A
  release asset is a publication, and the restricted tier holds rights-encumbered
  material (LGPLLR Heritage gloss text, unpublished corpora, teaching
  glossaries). A silent drop would look identical to a correct run. The fence
  currently catches 19 such rows if pointed at the wrong selector.
- **Working notes are not carried.** `consumers`, `consumer_candidates` and
  `rebuild` change after the release is cut; a frozen artifact that changes is
  not frozen.

`freeze_release_manifest.py check` re-derives the selection and diffs it against
the committed frozen file, exiting non-zero on drift, so a release gate can
refuse a stale asset.

**Known gap, stated rather than hidden:** the assets already published on
`data-v0.2.0`, `data-v0.3.0` and `data-v0.5.0` carry a `datasets.json` from
before this scheme — 5 rows at `manifest_version` 0.1.0 with no checksums for
`data-v0.5.0`, against 114 rows at 0.2.0 in the repo at the same moment. Those
deposits are archived and are not being rewritten. The frozen manifests
committed now are the record of what those tags contained; the scheme binds from
the next data release forward.

## 6. What a citer should do

- Citing the software or the project as a whole → the concept DOI
  `10.5281/zenodo.21965599`, plus
  [CITATION.cff](https://github.com/gasyoun/kosha/blob/main/CITATION.cff).
- Citing a specific state → the version DOI of that tag, listed in
  [docs/CITABLE_V1_RECORD_KOSHA_01.09.26.md](https://github.com/gasyoun/kosha/blob/main/docs/CITABLE_V1_RECORD_KOSHA_01.09.26.md).
- Citing a dictionary sense → the pinned form `{dict}.{L}.{n}@{data_version}`,
  which resolves independently of where the service happens to run (RISKS R1/R5;
  `KOSHA_PUBLIC_BASE` is deliberately never the deployment host).
- Citing a dataset → its row in the frozen manifest of the release that carries
  it, and its data statement under
  [docs/data-statements/](https://github.com/gasyoun/kosha/tree/main/docs/data-statements).
  Verify bytes by LF-normalising first.
- Data is CC BY-SA 4.0 ([LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md),
  inherited from Cologne); code is CC BY-NC 4.0
  ([LICENSE.md](https://github.com/gasyoun/kosha/blob/main/LICENSE.md)). The two
  tiers are not interchangeable — ShareAlike does not permit adding a
  non-commercial restriction on top of the data.

_Dr. Mārcis Gasūns_
