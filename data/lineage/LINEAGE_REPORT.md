# LINEAGE REPORT — kośa-lineage crosswalk (H4033, wave B)

_Created: 04-09-2026 · Last updated: 04-09-2026_

**Handoff:** [H4033](https://github.com/gasyoun/Uprava/blob/main/handoffs/H4033-OxAlpha_Kosha_kosa-lineage-crosswalk_04.09.26.md) · **Executor:** OxAlpha (opencode/z-ai/glm-5.3-flash) · **Pattern:** the Tamilex Caturakarāti lineage study (Chevillard/Trento), applied to the Sanskrit kośa chain. **Manifest SHA-16:** `49f251bfa1f7b3ce` (frozen before computation; matching rule in [lineage_manifest.json](lineage_manifest.json)).

## Step 0 — inventory

| Source | File | Entries | Identity |
|---|---|---|---|
| SKD (Śabdakalpadruma) | csl-orig/v02/skd/skd.txt | 42,531 `<L>` records | verified (H4016) |
| VCP (Vācaspatyam) | csl-orig/v02/vcp/vcp.txt | 50,135 | Cologne CDSL |
| AMAR (Amarakośa) | AMAR/amar.txt | 2,359 synonym groups (11,057 stems) | **verified 04-09: "Amarakośa in CDSL Format"** (Nāmaliṅgānuśāsana, SLP1, uohyd source) |
| Medinīkośa | NOT digitized | — | measured via named quotations inside skd.txt |

## Headword-lineage (frozen rule: k1 slp1 lowercased minus trailing visarga; AMAR = synonym stems minus gender suffixes)

| Pair | A | B | Intersection | Jaccard | A∩B/A | A∩B/B |
|---|---|---|---|---|---|---|
| SKD ↔ VCP | 35,525 | 44,172 | **20,084** | 0.337 | **56.5 %** | 45.5 % |
| SKD ↔ AMAR(stems) | 35,525 | 11,057 | 3,635 | 0.085 | 10.2 % | **32.9 %** |

**Reading:** SKD shares a majority of its headword stock with Vācaspatyam (both 19th-c. encyclopedic kośas drawing on the same tradition), and absorbed a **third of the Amarakośa synonym inventory** as headwords — the classical-kośa base is measurably inside the modern compiles. This is the Sanskrit Caturakarāti finding: the lineage is not anecdotal, it is a majority-derivation.

## Quotation census (entries naming a source kośa in skd.txt)

| Source named | SKD entries | Note |
|---|---|---|
| **medinī** | **4,347** (10.2 %) | spot-checked: genuine attribution formula («… iti / medinī . (gloss)») |
| śabdaratnāvalī | 3,602 lines | later lexical source — richer lineage than the classical 5 |
| kavīkalpadruma | 2,189 lines | |
| śabdacandrikā | 1,311 lines | |
| amara by name | 30 | Amara functions as SKD's base vocabulary, rarely named |
| vaijayantī / śāśvata / kṣīrasvāmin | 0 under these patterns | recorded honestly |

## Definition-similarity tier: NO-GO (method finding)

Token-Jaccard over markup-stripped SKD↔VCP bodies on 3,000 deterministic shared headwords: **median 0.059, mean 0.072, zero pairs ≥ 0.5** — spot-check shows WHY: the two works share the lexical stock, not the prose (different compilers' phrasing, sandhi, abbreviation styles). Definition-lineage must be measured at the QUOTED-SOURCE level (which this census does) or via lemmatized alignment (future work) — naive text similarity is structurally blind here. Recorded as the probe's honest negative.

## Cascade recommendations for the H4019 consumer

1. **SKD→Medinīkośa edge is STRONG and now measured**: 4,347 SKD entries name medinī; NCC dates Medinīkośa **1200–75 CE** (H4019 addendum 3). The dating layer's cascade can legitimately bucket those senses **late-medieval via a named-source chain** instead of the SKD 19th-c. ceiling — next data/dating revision should consume the medinī-marker as a cascade trigger (bundle: sense-level regex = mechanical).
2. The śabdaratnāvalī / kavīkalpadruma / śabdacandrikā edges (7,100+ lines combined) are additional dated-able chains — inventory their dates before any cascade use (they postdate/amend Medinīkośa; NOT bucketed here).
3. AMAR line: SKD absorbed 32.9 % of Amarakośa's stock, but Amara is rarely NAMED — the AMAR edge carries no quotation trigger; headword-overlap alone must NOT drive buckets (classical era via overlap would overstate earliness — conservative-later rule holds).

## Honest residue

- AMAR stems normalized minimally (gender suffixes stripped; hyphen compounds kept whole) — some sandhi-joined stems may miss; direction of the reported containment is conservative.
- Quotation census is token-level on entry bodies (multi-line, hyphenated linebreaks may split a rare name); the medinī count (4,347) is a floor.
- Spot-checks: 10/10 shared-headword pairs + 10/10 medinī hits hand-verified ([spotcheck_dump.tsv](spotcheck_dump.tsv)).
- VCP↔AMAR pair not computed (both feed SKD; the direct edge adds little to the cascade question).

_Dr. Mārcis Gasūns_
