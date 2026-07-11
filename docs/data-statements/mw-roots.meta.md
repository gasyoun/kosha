# Data statement — MW verbal-root inventory (`mw-roots`)

_Created: 11-07-2026 · Last updated: 11-07-2026_

Data statement (Bender & Friedman 2018 / Gebru et al. 2021 datasheet form) for the
`mw-roots` dataset served by the kosha data-hub. Manifest row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
Download: [`mw_roots.tsv` in release data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0).

## Composition & counts

2,113 rows, one per verbal root recorded in Monier-Williams' *A Sanskrit-English
Dictionary* (1899). TSV, UTF-8, 8 columns:

| Column | Content |
|---|---|
| `mw_L` | MW entry L-number (stable Cologne entry id) |
| `e` | entry sub-index (homonym counter within an L) |
| `k1_slp1` | root in SLP1 |
| `root_iast` | root in IAST |
| `verb_type` | `genuineroot` (750) or `root` (1,363) — MW's own distinction between roots he treated as genuine and forms "fictitiously formed to serve as roots" |
| `classes` | present-class + voice codes as printed (e.g. `10P,10Ā`) |
| `whitney_anchor` | anchor into Whitney's *Roots* (1885) where linkable |
| `westergaard` | Westergaard *Radices* (1841) reference where linkable |

## Source provenance

Extracted from the Cologne Digital Sanskrit Dictionaries (CDSL) digitization of
MW 1899, file `v02/mw/mw_roots.tsv` in
[sanskrit-lexicon/csl-orig](https://github.com/sanskrit-lexicon/csl-orig) —
server-regenerated upstream by the Cologne project (Funderburk, Malten et al.),
mirrored unmodified into the kosha public tier. The printed source is a
public-domain 1899 edition; the digitization is CC BY-SA 4.0.

## Curation rationale

Three org repos independently re-scanned `mw.txt` for roots before this file
existed and got three different counts (750 / 809 / 1,163) — the divergence that
motivated registering one canonical inventory. This dataset exists so that no
consumer ever re-derives "the MW root list" from entry markup again: the
`verb_type` split makes MW's genuine-vs-artificial root distinction explicit
instead of leaving it to each scanner's regex.

## Language variety

Sanskrit (ISO 639-3 `san`), lexicographic register: the root inventory of a
dictionary that spans Vedic through Classical Sanskrit, as systematized by a
19th-century European lexicographer. Romanized: SLP1 (computational key) and
IAST (display). No Devanagari column. Root shapes follow MW's normalization,
which differs in places from Whitney's and from the Dhātupāṭha tradition — the
`whitney_anchor` column is the bridge, not an identity.

## Annotator / process information

Deterministic extraction from structured dictionary markup by the Cologne
upstream pipeline. No LLM-generated content; no human annotation beyond the
original lexicographer's. The kosha release repackages the upstream file
byte-identically.

## Known biases & limitations

- MW's root inventory reflects 1899 scholarship: it includes roots modern
  philology rejects and lists as `root` many back-formations (MW's own caveat,
  preserved in `verb_type`).
- `whitney_anchor` and `westergaard` are sparsely populated — absence of an
  anchor means "not yet linked", not "absent from Whitney/Westergaard".
- Class/voice codes are as printed; MW's class assignments occasionally differ
  from DCS corpus-attested behavior — join against
  [`dcs-verb-roots-by-class`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  for attestation-grounded classes.

## Intended use / known misuse

**For:** root-level joins (crosswalks to Whitney, DCS, Dhātupāṭha), verb
worklists, coverage studies, teaching inventories. **Misuse:** treating the
2,113 rows as "the roots of Sanskrit" — this is *MW's* inventory, a
lexicographic artifact, not a corpus-attested or Pāṇinian root list; and
re-scanning `mw.txt` instead of consuming this file (the exact failure this
dataset was minted to end).

## License

CC BY-SA 4.0, inherited from csl-orig per
[LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md).
Attribution: Cologne Digital Sanskrit Dictionaries (Univ. of Cologne) and the
kosha data release.

## Maintenance & sunset plan

Upstream-maintained: the file is regenerated on the Cologne server whenever MW
corrections land in csl-orig; kosha re-mirrors it at each `data-v*` release cut
(see [DATA_HUB_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md)).
Sunset: if csl-orig ever ships its own release channel for this file, the kosha
copy becomes a redirect row in the manifest rather than a re-served asset.

## Deprecation status

`active`.

## Citation

Cite the release: *Gasuns Sanskrit Dictionary data release v0.1.0* (CC BY-SA
4.0), asset `mw_roots.tsv`,
[github.com/gasyoun/kosha/releases/tag/data-v0.1.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0),
with attribution to the Cologne Digital Sanskrit Dictionaries. A repo
`CITATION.cff` + Zenodo DOI are pending the next `/cut-release` freeze; until
then the release URL is the citable locator.

## Provenance of this statement

Authored 11-07-2026 by Fable 5 (`claude-fable-5`) under handoff
[H665](https://github.com/gasyoun/Uprava/blob/main/handoffs/H665-Fable_kosha_dataset-data-statements_11.07.26.md),
from the manifest row, the release assets, and column inspection of the live file.

_Dr. Mārcis Gasūns_
