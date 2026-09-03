# Sense-dating bucket layer (H4019) — first-attestation era buckets

_Created: 03-09-2026 · Last updated: 03-09-2026 (H4026 go-live)_

## Preface caveat (ships with every render of this layer)

> **«Первое засвидетельствование в цитируемом корпусе, не происхождение
> значения.»** — *First attestation in the cited corpus, not the origin of
> the meaning.*

The buckets below say when a sense is FIRST ATTESTED among the works PWG
itself cites. They do not claim where a meaning comes from. The printed PWG
sense order is never reordered by this layer; no PWG→RU entry text changes.
Buckets are additive machine-readable data (MG ruling 03-09-2026, on the
H4016 GO×STRONG verdict).

## What is here

| file | what | derived? |
|---|---|---|
| `works_hand.tsv` | curated hand layer: canon→DM joins, hand calls, UNDATEABLE classes, conflict notes | **input** (hand calls, with reasons) |
| `evidence/nomen.classification.0309.json` | H4016 seed (verbatim copy): hand-checked alias map + per-citation classification, 5 nominal headwords / 20 senses | input (snapshot) |
| `evidence/dharmamitra-chronology.snapshot-2026-09-03.json` | Dharmamitra chronology field-subset snapshot (1,618 works, 6 eras) — PRIMARY date source | input (snapshot) |
| `evidence/dcs-text-dates-2021.tsv` | DCS 2021 date table folded to 251 text keys — SECONDARY (seed-verbatim only) | input (snapshot) |
| `evidence/citation-canon-top-texts.snapshot-2026-09-03.json` | citation_canon topTexts (50 canon texts + variants) — the work-identity spine | input (snapshot) |
| `work_dates.tsv` + `.json` | one row per distinct resolved locus prefix: work identity → era bucket + via + reason + flags | derived — `--check` recomputes |
| `abbrev_map.tsv` | PWG citation abbreviation → work + era (mode share ≥ 0.9); the render badge lookup | derived — `--check` recomputes |
| `sense_dating.tsv` | one row per sense (slp1, hom, sense_id): n_cites, n_dateable, first_era, bucket_via, marginal, class, conflict notes | derived — `--check` recomputes |
| `COVERAGE_REPORT.md` | era × via × mass-share, nomina-first spot-check, honest residue | derived |

Rebuild + parity gate:

```bash
python scripts/build_sense_dating.py           # rebuild from inputs
python scripts/build_sense_dating.py --check   # parity: recompute == stored (exit 0)
```

## Bucket vocabulary and boundaries

`vedic < epic-sutra < classical < early-medieval < late-medieval` (rank
order used for first-attestation). NULL era = undateable — always carried,
never dropped, never forced.

- **vedic** — Saṃhitās, brāhmaṇas, the older Upaniṣads (Chānd./Bṛh. Āraṇyaka
  strata; the seed's own vedic/epic-sutra Upaniṣad split is kept verbatim).
- **epic-sutra** — epics, sūtra/vedāṅga genre, Pāṇini/Patañjali, dharma-sūtra
  strata, Manu (DCS 100..300 per seed).
- **classical** — kāvya core, Pañcatantra, kośa cluster (Amarakoṣa c.
  4th-6th c. CE), BhG per seed's DM call.
- **early-medieval** — roughly 600-1300 (Kathāsaritsāgara, Gītagovinda,
  Bhāgavata-Purāṇa, Hemacandra's kośas).
- **late-medieval** — 1300+ (Sāhityadarpaṇa, commentators, Śabdakalpadruma
  as a 19th-c. TERMINUS CEILING, low attestation value — H4019 addendum §1).

## Identity spine and tiers (no fuzzy title matching)

Work identity routes through the citation_canon spine (canon text + variants)
and the H4016 seed's hand-checked alias map; DM dates join onto canon
identity, never raw strings (the H1657/H1684 warning: title-only matching is
homonym-dense). Resolution precedence for a resolved locus prefix:

1. **seed** — H4016 hand calls, verbatim (era + via kept; `no-rule` seed rows
   are silence, not a call, and may be extended by the hand table).
2. **hand** — `works_hand.tsv` fold rows, each with an explicit reason string.
3. **canon_dm** — canon variant fold-prefix match → Dharmamitra family-mode
   era (hand-verified expected era asserted at build time; DM chunk strata
   that disagree are recorded as notes, never averaged).
4. **hand abbrev** — unambiguous abbreviation binding (used when the locus
   string itself failed resolution, e.g. Sarvadarśanasaṃgraha).
5. **no-match / unresolved** — NULL era, carried as honest residue.

Anything that does not match a curated identity stays NULL. Disputed,
boundary and recension-dependent works are UNDATEABLE by design (Suśruta
layered-text conflict, Medinīkoṣa, Kāmandakīya, Kāvyādarśa, Mṛcchakaṭikā,
Mudrārākṣasa, Śrutabodha, Rājanighaṇṭu, Lalitavistara, Vaijayantī, ...).

Known traps recorded (not fixed silently): the DCS `RHT` row is NOT
Bṛhatsaṃhitā; DM's Ratnāvalī/Ratnamālā hits are a different work from the
nighaṇṭu Ratnamālā; DM's Rājataraṅgiṇī row is labelled by the Jonarāja
continuation era (the bucket holds for Kalhaṇa's original either way);
`Śabdakalpadruma` dates a 19th-c. compile — terminus ceiling only.

## Consumers

- `scripts/build_sense_dating.py` (this layer, P1+P2).
- `app/dating_hydrate.py` (P3): **LIVE since 03-09-2026 (H4026, MG order)** —
  era badges on PWG `<ls>` citations, rendered on every page built with the
  live default `ux` (the explicit `ux["sense_dating"]` key keeps the no-ux
  path byte-identical). Badges cover BOTH the plain spans and the
  `ls-scan`/`ls-etext` anchors `app/ls_hydrate.py` rewrites resolvable
  citations into, plus the continuation-citation `title` fallback
  (`<ls n="ṚV. 4,">22,9</ls>`); never a URL reverse-resolution. The page-level
  RU+EN caveat renders whenever ≥1 badge does. Rendered proof:
  [evidence/H4026_BADGES_LIVE_PROOF.md](evidence/H4026_BADGES_LIVE_PROOF.md).
- Future: PW dictionary inherits through the same canon spine (H4019
  addendum §3: PW's citation apparatus is ~9.5% of PWG's instance mass).
- Future (measured, unsurfaced): a SENSE-keyed render of
  `sense_dating.tsv.first_era` — the surface has no hom→entry mapping
  (185/255 layer headwords with a committed card have multiple PWG entries
  per slp1; printed-marker fingerprints match several entries at once), so a
  sense-keyed badge would silently attach eras to the wrong homonym. The
  per-citation badge keys on the citation's own abbreviation and cannot
  mis-attach.

## Scope fences (H4019)

PWG senses only in v1 (verbs included — their all-tie rows are honest data).
No morphological/semantic analysis beyond era buckets. Other dictionaries are
future work, not this unit. Nomina-first is a REPORTING emphasis; the join
runs on all senses uniformly.

_Dr. Mārcis Gasūns_
