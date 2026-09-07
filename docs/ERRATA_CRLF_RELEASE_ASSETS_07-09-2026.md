# Errata — CRLF-inflated bytes in three DOI-archived data release assets

_Created: 07-09-2026 · Last updated: 07-09-2026_

## What happened

[FINDINGS §654](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md#654) (H3788,
01-09-2026): `.gitattributes` pins `* text=auto eol=lf`, but git never
renormalizes a working tree populated before that rule landed, and
`git status` reports such a tree as clean forever. The checkout that uploaded
these three data releases held CRLF line endings for the affected files at
upload time. The **content** is identical to the canonical LF form — only the
line-ending bytes differ — but the **published asset bytes** are not what a
clean checkout produces, so a citer who downloads the asset and hashes it gets
a digest the frozen manifest (`data/manifest/frozen/<tag>.datasets.json`) does
not record.

## Why this note, not a re-upload

Zenodo mints one immutable deposit per pushed tag
([DOI_CHECKLIST_W2A.md](https://github.com/gasyoun/kosha/blob/main/docs/DOI_CHECKLIST_W2A.md) —
"never move a released tag... deposits cannot be withdrawn"). Overwriting the
GitHub release asset under the same tag would not retroactively re-archive it
at Zenodo — the already-minted DOI's snapshot would keep the old bytes while
the GitHub-hosted copy changed underneath it, producing two disagreeing
"authoritative" copies instead of one documented one. This note records both
byte sequences and the LF-canonical checksum instead, so a citer on any
platform can reproduce the digest without either copy being silently
rewritten.

## How to verify

For any TSV asset below: download it, then compute the SHA-256 of its bytes
with `\r\n` replaced by `\n` (what
[`scripts/freeze_release_manifest.py`](https://github.com/gasyoun/kosha/blob/main/scripts/freeze_release_manifest.py)'s
`canonical_digest()` does):

```python
raw = open(path, "rb").read()
canon = raw.replace(b"\r\n", b"\n")
import hashlib; hashlib.sha256(canon).hexdigest()
```

The result matches `lf_canonical_sha256` below and the corresponding row's
`sha256` in the frozen manifest for that tag — confirmed by re-deriving all
nine independently from the live GitHub release assets on 07-09-2026 (script:
`audit_crlf_release_assets.py`, run against `gh release view/download`, not
committed — ad hoc verification, not a build stage).

## data-v0.2.0

| dataset id | asset | published bytes | LF-canonical bytes | delta (= line count) | LF-canonical sha256 |
|---|---|---:|---:|---:|---|
| `bloomfield-rv-citations` | `bloomfield_rv_citations.tsv` | 2,790,672 | 2,753,991 | 36,681 | `f41e5bddabe4588a69135c3f8d8564a5c1c55f051d977ba8019d6ec713d6a6b0` |
| `dict-corpus-concordance` | `dict_corpus_concordance.tsv` | 6,738,653 | 6,664,132 | 74,521 | `566e1ee473421c59361071e90c2976046f328f1f8412ed26d890a62c83a42bfc` |
| `morphology-attestation-audit` | `morph_attest_AG.tsv` | 34,088,655 | 33,687,286 | 401,369 | `8401350619ccc14075903cd6b76762aea306ec8ffbc128cd35a43e9fd4ee5321` |
| `parallel-passage-concordance` | `parallel_passage_concordance.tsv` | 32,224,842 | 32,071,796 | 153,046 | `1c931dc18c68cdd80e764ca1417d010e4f4b800d03051d80f2797c3d8f739a9f` |

## data-v0.3.0

| dataset id | asset | published bytes | LF-canonical bytes | delta (= line count) | LF-canonical sha256 |
|---|---|---:|---:|---:|---|
| `panini-derivation-status` | `derivation_status.tsv` | 27,135,881 | 26,734,512 | 401,369 | `3950a01ea21d902817b387e8f01e8ce5d34358779b8e7f5027938efa438ad1ed` |
| `paninian-corpus-concordance` | `paninian_concordance.tsv` | 86,867,887 | 85,974,404 | 893,483 | `633cd506c2fcdb20564fc129cb4c313ff8bf2d34d5ad89584891306f71a84028` |
| `paninian-sutra-coverage-map` | `sutra_coverage_map.tsv` | 1,062,544 | 1,058,560 | 3,984 | `a00a8f7e2b029b1b995f75dbe35423e4130cf045502b1a7f42027bb6958628e4` |

## data-v0.5.0

Only two of the five assets in this release are affected — `dcs_cdsl_xref.tsv`,
`mw_etymology.tsv` and `mw_roots.tsv` were already byte-identical to their
LF-canonical form (delta 0), confirmed by the same audit.

| dataset id | asset | published bytes | LF-canonical bytes | delta (= line count) | LF-canonical sha256 |
|---|---|---:|---:|---:|---|
| `kosha-lemma-frequency` | `lemma_frequency.tsv` | 4,910,744 | 4,827,466 | 83,278 | `c07f6a0229067267d2bf18ba79f43f5081f05fef8875a352cc18f5e157ceccef` |
| `mw-heritage-crosswalk` | `mw_heritage_crosswalk.tsv` | 3,263,954 | 3,078,150 | 185,804 | `182fd19a24f89d32df9740738d5956b7656b3f959baefedbb671c00477c0bf4e` |

## Scope note

This is a byte-encoding artifact of the upload checkout, not a content defect:
every LF-canonical digest above was independently re-derived from the live
published asset and matches the digest already recorded in the committed
frozen manifest for that release, which was itself computed from a since-
renormalized, clean checkout. No dataset content is in question.

_Dr. Mārcis Gasūns_
