# sense-corpus-concordance — build report (H1455 wave-1)

_Created: 22-07-2026 · Last updated: 22-07-2026_

Built by [scripts/build_sense_corpus_concordance.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_sense_corpus_concordance.py) (H1455, Opus 4.8 `claude-opus-4-8`), consuming the H1456 PWG per-sense `<ls>` export.

## A2 — `<ls>`-locus-resolution rate (THE wave-1 acceptance metric)

| metric | value |
|---|---|
| pilot (slp1,hom) groups | 500 |
| `<ls>` citations on pilot leaf senses | 85472 |
| resolved to a bibliographic source (pwgbib) | 84909 |
| **resolution rate** | **99.3%** (floor 60%) |

Resolution reuses the canonical `RussianTranslation/src/pwg_sources.py` (pwgbib.txt) — the abbrev table is consumed, never re-derived.

## MBh vulgate resolution (wave-1.5 — reused prior art)

PWG's continuous Böhtlingk–Roth Mahābhārata numbering IS resolvable to a Nīlakaṇṭha-vulgate address — the csl-atlas **f8 fitted-index crosswalk** (H610/H761, all 18 parvans, held-out MW 55.2% within ±3; [DEAD_ENDS §8b retracted](https://github.com/gasyoun/SanskritLexicography/blob/master/DEAD_ENDS.md)). This layer now **consumes** it (`mbh_vulgate.py` → `mbh_vulgate_concordance.csv`): **7055/7353** MBh `<ls>` loci on pilot senses resolved to a vulgate `parvan.adhyāya.śloka` (crosswalk present: True). Example: `MBH. 12,3630` → **vulgate 12.98.19**.

## Per-tier attestation rows

| tier | confidence | rows | meaning |
|---|---|---|---|
| ls | 0.99 | 85472 | PWG's OWN `<ls>` under the sense — guaranteed-correct witness (MBh loci carry their resolved vulgate address) |
| locus | 0.90 | 5 | DCS attestation verse-equal to a sense's `<ls>` (canonically-numbered Vedic texts) |
| locus-mbh | 0.65–0.80 | 48 | DCS Mahābhārata attestation whose (parvan, adhyāya) matches a sense's `<ls>`-resolved vulgate adhyāya (±1, vulgate↔critical drift) |
| overlap | 0.50–0.70 | 532 | shared proper-noun/binomial/digit gloss tokens |
| **review queue** | <0.60 | 860 | conf<τ + unassigned residue (kept, never dropped) |

DCS side: **1145** headword↔DCS-lemma links over the pilot; **585** assigned to a sense (5 by verse-locus, 48 by MBh-vulgate-adhyāya, 532 by gloss-overlap); the rest parked to `sense_review_queue.tsv`.

**Honest note — corrected (wave-1.5).** An earlier draft of this report called PWG↔DCS Mahābhārata locus-matching *infeasible*. That over-claimed: PWG-continuous → **vulgate** is a SOLVED problem (csl-atlas f8), and it is now consumed. The residual is narrower and specific — DCS's Mahābhārata is the **BORI critical edition**, whose adhyāya/śloka numbering drifts ~±1 adhyāya from the vulgate — so a DCS match through the crosswalk is an adhyāya-level **corroboration** (`locus-mbh`, conf ≤ 0.80), not exact-verse identity. Texts DCS lacks entirely (Pañcatantra, Kathāsaritsāgara) still cannot be DCS-matched. The `ls` tier (PWG's own `<ls>`, now carrying resolved vulgate addresses) remains the load-bearing witness.

## Rights (A7)

Every row carries `rights ∈ {public, evidence-only}`; the public viewer filters to `public`. PWG `<ls>` sources are pre-1900 editions (public); DCS is CC BY 4.0 (public). **87092 public rows, 0 evidence-only** — no modern-copyright gloss (Kochergina/Smirnov) is consumed in wave-1, so 0 evidence-only rows arise; the classifier is wired for future modern glosses.

## A3 — `nāgadanta` worked example (the translator-split, resolved)

PWG keeps one homonym; the sense-sharded layer restores the per-sense loci that the thin bilingual glossaries dropped:

- **sense 1a** — Elephantenzahn, Elfenbein H. an. 4,111 . MED. t. 203 . MBH. 12,3630
  - `<ls>`: H. an. 4,111, MED. t. 203, MBH. 12,3630
  - DCS: nāgadanta (locus-mbh)
- **sense 1b** — Pflock in der Wand zum Anhängen von Sachen H. 1011 . H. an. MED. PAÑCA
  - `<ls>`: H. 1011, H. an, MED, PAÑCAT. 116,19, PAÑCAT 252,10, KATHĀS. 76,24
  - DCS: —
- **sense 2** — f. ( adj. comp. ) N. pr. einer Apsaras R. 2,91,17
  - `<ls>`: R. 2,91,17
  - DCS: —
- **sense 3a** — N. einer Pflanze, Tiaridium indicum Lehm. H. an. MED. RATNAM. 35 . SUŚ
  - `<ls>`: H. an, MED, RATNAM. 35, SUŚR. 1,138,12, SUŚR 2,62,6, SUŚR. 2, 102,9, SUŚR. 2, 284,8, SUŚR. 2, 387,16
  - DCS: —
- **sense 3b** — = MED. , welches ŚKDR. und WILS. hier durch Hure erklären: aber H. an.
  - `<ls>`: MED, ŚKDR, WILS, H. an
  - DCS: —

Sense **1a** (Elephantenzahn / tusk) carries its **MBH** locus; sense **1b** (Pflock / peg) carries its **PAÑCAT** loci — the exact split the [नागदन्त thread](https://groups.google.com/g/nagari/c/NOWqiBQl1Xc/m/_R8O4-39CAAJ) argued about. `nāgadantaka` `1b` (HIT 27,12) is recorded `variant_of nāgadanta`, corroborating the peg sense (A4).

## Determinism (A8)

Steps 1–3 + 5 are deterministic (byte-identical on re-run); only the optional LLM residue tier (`--run-llm`, `wf/sense_adjudicate.js`) may vary and is bounded + logged. This run did **not** dispatch the LLM tier — residue is parked to the review queue (marked default, autonomy contract).

_Dr. Mārcis Gasūns_
