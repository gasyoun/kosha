# Rights record — vidyut prakriyā derivation metadata (A4 gate) + DCS licence resolution

_Created: 18-07-2026 · Last updated: 18-07-2026_

This record **gates every A4 publication** (plan D2, wave W1a / [H1263](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1263-Opus_kosha_vidyut_derivation_metadata_rights_record_18.07.26.md)).
No A4 dataset ships until it exists. It answers two rights questions in one file:
the licence of the **vidyut derivation metadata** kosha embeds in the Pāṇinian
concordance, and the **DCS licence contradiction** kosha's own manifests carried.

## What this covers

The right to embed, in kosha's A4 "Pāṇinian concordance of the DCS" datasets and
web surface, the **derivation metadata produced by vidyut** — the prakriyā (rule-by-rule
derivation) output, the dhātupāṭha/sūtra identifiers it resolves against — together with
the **DCS attestation loci** those derivations are indexed to.

The vidyut **code** and the vidyut **derivation data** are two separate artifacts with
two separately-verified licences, stated below each with the file it was read from —
treating them as one licence is the exact failure this record exists to prevent.

## vidyut — code licence

- **Licence: MIT** (Copyright © 2022 ambuda.org).
- **Read from:** the installed distribution, `vidyut-0.4.0.dist-info/licenses/LICENSE.md`
  (site-packages, vidyut 0.4.0), verbatim MIT text; the package `METADATA` declares
  `License-File: LICENSE.md`. Confirmed against upstream
  [ambuda-org/vidyut](https://github.com/ambuda-org/vidyut) — the only `LICENSE` file in
  the entire source tree is [`bindings-python/LICENSE.md`](https://github.com/ambuda-org/vidyut/blob/main/bindings-python/LICENSE.md)
  (the same MIT text), and the repository declares `License: MIT`.
- **What we use it for:** we call vidyut as a code engine (declension/conjugation
  paradigms, PPP validation, prakriyā derivation), per the `vidyut` row in
  [external_tools.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json).

## vidyut — bundled/derivation-data licence

- **Licence: MIT**, with the underlying source texts being classical **public-domain**
  works.
- **Read from:** [`vidyut-prakriya/data/README.md`](https://github.com/ambuda-org/vidyut/blob/main/vidyut-prakriya/data/README.md)
  (read 18-07-2026), which states verbatim:

  > Most of the data files here were sourced from ashtadhyayi.com, and the author of
  > ashtadhyayi.com has graciously agreed to share thse files with us under an MIT license.

  The data files it governs are the derivation sources kosha's A4 metadata depends on:
  `dhatupatha.tsv` (a superset of the Siddhāntakaumudī, Bṛhaddhātukusumākaraḥ,
  Mādhavīyadhātuvṛttiḥ, Kṣīrataraṅgiṇī and Dhātupradīpaḥ dhātupāṭhas, source JSON from
  [ashtadhyayi-com/data](https://github.com/ashtadhyayi-com/data/blob/master/dhatu/data.txt),
  svaras cross-checked against [SanskritVerb](https://github.com/drdhaval2785/SanskritVerb)),
  `sutrapatha.tsv` (the Aṣṭādhyāyī itself), `dhatupatha-ganasutras.tsv`,
  `linganushasanam.tsv`, `phit-sutras.tsv`, `unadipatha.tsv` — the sūtra/dhātu texts
  encoded in SLP1. The compositions themselves (Pāṇini's Aṣṭādhyāyī, the Phiṭ-sūtras, the
  gaṇa-sūtras) are ancient and out of copyright; the MIT grant covers the digital encoding.
- **Provenance detail — the data is NOT in the pip wheel.** vidyut 0.4.0's wheel bundles
  only code (`RECORD` lists 46 entries: `.py`/`.pyi`/`vidyut.pyd`/`docs/requirements.txt`
  and dist-info metadata — **no** `.tsv`/`.csv`/`.json` data). The linguistic data is a
  **separate download** — [`data-0.4.0.zip`](https://github.com/ambuda-org/vidyut/releases/download/py-0.4.0/data-0.4.0.zip)
  from the ambuda-org/vidyut releases, or rebuildable via `make create_all_data` in the
  `vidyut-data` crate — and vidyut's API loads it from a caller-supplied path
  (`Dhatupatha(path)`). So the code-vs-data licence split is real, not notional.

## DCS — licence resolved from the primary source, and the kosha contradiction fixed

kosha contradicted itself on DCS's licence: [external_tools.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json)
(`id: dcs`) recorded **CC BY-SA 4.0**, while
[CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md):151
and 14 assertions in [datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
said **CC BY 4.0**.

- **Resolved: DCS data is CC BY 4.0** — from Hellwig's **own published terms**, not a
  kosha secondary source. Read from the DCS repository's
  [`dcs/data/conllu/readme.md`](https://github.com/OliverHellwig/sanskrit/blob/master/dcs/data/conllu/readme.md)
  (read 18-07-2026; file last committed 2024-10-29), which states verbatim:

  > ## License
  >
  > The data in this directory are licensed under the Creative Commons BY 4.0 (CC BY 4.0) license.

  This is the licence of the CoNLL-U attestation data kosha actually ingests (the
  `dcs-cdsl-xref` crosswalk and `kosha-lemma-frequency` sidecar), which is exactly the
  directory the DCS row's `api_url` points at.
- **Which kosha file was wrong, and corrected in this same pass:**
  [external_tools.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json)
  was the outlier — its `dcs.license` is changed **CC BY-SA 4.0 → CC BY 4.0** (with a
  `license_source` field citing the readme). `CONCORDANCE_ROADMAP.md`:151 and the 14
  `datasets.json` assertions were already correct and are left unchanged. The unrelated
  15th "CC BY 4.0" mention in `datasets.json` (Gita Supersite, line 629) is **not** DCS
  and was deliberately not touched.

## Composition ruling for A4 output

Input chain, each input marked *cited* (verified above / in the manifest) or *resolved
in this record*:

| Input | Licence | Basis |
|---|---|---|
| CDSL dictionary data | CC BY-SA 4.0 | *cited* — Cologne's ShareAlike; kosha's own two-tier rule |
| Aṣṭādhyāyī / dhātupāṭha sūtra text | public domain (ancient) | *cited* — classical compositions |
| vidyut code | MIT | *resolved* — installed `LICENSE.md` + upstream |
| vidyut derivation data | MIT | *resolved* — `vidyut-prakriya/data/README.md` |
| DCS attestations | CC BY 4.0 | *resolved* — DCS `conllu/readme.md` |

**Ruling: A4 output is CC BY-SA 4.0, with vidyut attributed.** MIT and CC BY 4.0 are both
permissive and compose into a ShareAlike work without conflict; **BY-SA is inherited from
the CDSL dictionary data and is not optional** — it binds regardless of the DCS answer,
which is why A4 was already safe under either branch of the contradiction. Per kosha's
two-tier rule ([CLAUDE.md](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md)): code is
CC BY-NC 4.0, data releases are CC BY-SA 4.0, and the **non-commercial restriction may not
be added on top of Cologne's ShareAlike** — A4, a data release, ships BY-SA (not BY-NC-SA).

**Attribution required in the A4 release:**

- vidyut (code + derivation data), MIT — "Derivation metadata generated with
  [vidyut](https://github.com/ambuda-org/vidyut) (Ambuda, Arun Prasad), MIT; derivation
  data via ashtadhyayi.com, MIT."
- DCS, CC BY 4.0 — "Attestation loci from the Digital Corpus of Sanskrit (Oliver Hellwig
  et al.), CC BY 4.0."
- CDSL, CC BY-SA 4.0 — the ShareAlike source.

## Human gate — not triggered

Both branches the handoff flagged for a `@DECIDE` (vidyut bundled data incompatible with
BY-SA; DCS turning out to impose a ShareAlike obligation that changes the record) **did not
occur**: vidyut data is MIT (compatible), DCS is CC BY 4.0 (permissive, no ShareAlike of
its own). Nothing here is a rights decision a human must take, so no `@DECIDE` is raised and
A4 may both build and publish once its own wave (W1b) completes. Verification check 1a-5 is
satisfied by the absence of an incompatibility, not by deferral.

## Open follow-up

- The vidyut data licence rests on the `vidyut-prakriya/data/README.md` statement (author
  of ashtadhyayi.com granted MIT); there is **no standalone `LICENSE` file inside the
  `data-*.zip` release** itself. The README statement is Ambuda's own published provenance
  note and is treated as sufficient; worth a one-line confirmation if ever queried at scale.
- If a future vidyut release changes its data provenance or licence, re-verify before the
  next A4 release — this record is pinned to vidyut 0.4.0 / `data-0.4.0.zip`.

_Dr. Mārcis Gasūns_
