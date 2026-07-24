# Data statement — Pāṇinian sūtra ↔ DCS corpus concordance (`paninian-corpus-concordance`)

_Created: 24-07-2026 · Last updated: 24-07-2026_

Data statement for the A4 / Concordance-Q3 **W2b** public dataset served by the
kosha data-hub. Manifest row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
(`id: paninian-corpus-concordance`). Download: [`paninian_concordance.tsv` in
release data-v0.3.0](https://github.com/gasyoun/kosha/releases/tag/data-v0.3.0).

## Composition & counts

**893,482** rows, one per `(sūtra, form, locus)` triple: every W2a `ok`-status
AG-bucket form is inverted through its ordered Ashtadhyayi-only sūtra chain.
TSV, UTF-8. Schema = `concordance_core.RECORD_FIELDS` plus A4 columns:

| Column | Content |
|---|---|
| `anchor_type` | constant `panini-sutra` |
| `anchor_id` | `sutra:<a.p.n>` (e.g. `sutra:6.1.77`) |
| `anchor_key_slp1` | empty (sūtra anchors do not carry a form key) |
| `target_locus` | `dcs:<sent_id>` or `dcs:<sent_id>_<sub>` |
| `source_dataset` | `dcs` |
| `match_method` | `exact` (0.95) or `floor` (0.85) from `TIER_CONFIDENCE` |
| `confidence` | looked up, never hand-set |
| `evidence_count` | 1 per inverted form-step |
| `form_key_slp1` | attested form key (length-preserving) |
| `dcs_text` | attested surface form (IAST; W2b field name is historical) |
| `chain_position` | 1-based index of this sūtra in the ordered derivation |
| `chain_length` | Ashtadhyayi-only step count for the chain |
| `chain_id` | stable id into `derivation_chains.tsv` |
| `derivation_status` | `ok` (only ok forms are inverted) |
| `tense_caveat` | `1` when DCS `Tense=Past` conflates aorist/perfect |

**221** distinct sūtras carry ≥1 corpus exemplar (7/8 adhyāyas; adhyāya 5 has
none in this build). Chain length min 6 / median 12 / max 36.

Sibling release assets in the same cut: `derivation_status.tsv` +
`derivation_chains.tsv` (W2a harness), `panini_ambiguity_by_sutra.tsv` (2b-6),
`sutra_coverage_map.tsv` (W3a dark-class map).

## Source provenance

Built by [`scripts/build_panini_concordance.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_panini_concordance.py)
(H1390) over W2a's committed TSVs only — no re-derivation, no live network:

- `data/concordance/derivation_status.tsv` (401,368 AG forms)
- `data/concordance/derivation_chains.tsv` (2,815 distinct chains)

Upstream rights (gates A4 publication — plan D2 / W1a):
[data/manifest/rights/vidyut_prakriya_derivation_2026-07.md](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/vidyut_prakriya_derivation_2026-07.md).

## Curation rationale

No published corpus-grounded Pāṇinian concordance keyed by sūtra number existed.
This layer freezes one invertible build of vidyut-prakriya chains over attested
∧ generated forms so consumers query `sutra → exemplars` without re-running the
harness.

## Language variety

Sanskrit (ISO 639-3 `san`) as sampled by DCS attestations that also appear in
kosha's non-heritage generated `forms` table (the AG bucket). Genre skew is
DCS's (śāstra, epic, kāvya heavy).

## Annotator / process information

Deterministic inversion of W2a chain tables. Derivation chains themselves come
from local `vidyut.prakriya` 0.4.0 (no LLM). No human re-labelling of sūtra
steps in this layer; W2a sampled 30 ok chains for human verification (see
DERIVATION_HARNESS_BUILD_REPORT.md).

## Known biases & limitations

- **ok-only inversion:** all 86,857 `ambiguous` W2a rows carry empty `chain_id`
  (W2a gap vs ARCHITECTURE §4); they are not inverted here (documented, not
  silently zeroed).
- **Ashtadhyayi-only steps:** Dhatupatha / Vārttika / Kaumudī chain steps (0.32%)
  are dropped — not Pāṇini's own sūtras.
- **R-C4 tense caveat:** 466 inverted ok forms carry `tense_caveat=1`.
- **Coverage is not the full Aṣṭādhyāyī:** 221 lit sūtras of the named 3983
  enumeration — see the W3a coverage map for the three dark classes.
- **Fire-set ≠ full grammar:** only AG-lemma Cologne cells exercise the engine.

## Intended use / known misuse

**For:** sūtra-keyed corpus exemplars, teaching "which forms exercise rule X",
A4 research papers, the `/concordance/panini/` viewer.
**Misuse:** treating 221 lit sūtras as "the Aṣṭādhyāyī coverage of Sanskrit";
collapsing dark classes into one "dark" figure; inventing chain attribution for
ambiguous forms; ignoring `tense_caveat` on tense-sensitive claims.

## License

**CC BY-SA 4.0** (A4 composition ruling, W1a): CDSL ShareAlike binds; vidyut MIT
and DCS CC BY 4.0 compose without conflict. Attribution required:

> Derivation metadata generated with [vidyut](https://github.com/ambuda-org/vidyut)
> (Ambuda / Arun Prasad), MIT; derivation data via ashtadhyayi.com, MIT.
> Attestation loci from the Digital Corpus of Sanskrit (Oliver Hellwig et al.),
> CC BY 4.0. Dictionary-side form generation from Cologne CDSL, CC BY-SA 4.0.

See [LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md).

## Maintenance & sunset plan

Rebuild when W2a is re-run (new AG bucket or fixed ambiguous-chain recording).
Each `data-v*` cut freezes the TSV for citation; a later cut supersedes for live
use without deleting old release assets.

## Deprecation status

`active`.

_Dr. Mārcis Gasūns_
