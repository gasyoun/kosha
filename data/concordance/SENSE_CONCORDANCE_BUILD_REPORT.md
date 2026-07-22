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

## Per-tier attestation rows

| tier | confidence | rows | meaning |
|---|---|---|---|
| ls | 0.99 | 85472 | PWG's OWN `<ls>` under the sense — guaranteed-correct witness |
| locus | 0.90 | 5 | DCS attestation locus-matched to a sense's `<ls>` set |
| overlap | 0.50–0.70 | 564 | shared proper-noun/binomial/digit gloss tokens |
| **review queue** | <0.60 | 897 | conf<τ + unassigned residue (kept, never dropped) |

DCS side: **1145** headword↔DCS-lemma links over the pilot; **569** assigned to a sense (5 by locus, 564 by gloss-overlap); the rest parked to `sense_review_queue.tsv`.

**Honest note on the locus tier (VERIFICATION risk 1, confirmed by spike):** DCS uses critical-edition references (`MBh, 12, <adhyāya>` + śloka) while PWG cites Böhtlingk–Roth editions (continuous verse, e.g. `MBH 12,3630`); several PWG-cited texts (Pañcatantra, Kathāsaritsāgara) are absent from DCS entirely. So the passage-level locus tier is a weak signal by construction — the **load-bearing sense↔passage witness is PWG's own `<ls>`** (the `ls` tier), and A2's `<ls>`-resolution rate is the honest acceptance gate, exactly as the risk register anticipated.

## Rights (A7)

Every row carries `rights ∈ {public, evidence-only}`; the public viewer filters to `public`. PWG `<ls>` sources are pre-1900 editions (public); DCS is CC BY 4.0 (public). **87134 public rows, 0 evidence-only** — no modern-copyright gloss (Kochergina/Smirnov) is consumed in wave-1, so 0 evidence-only rows arise; the classifier is wired for future modern glosses.

## A3 — `nāgadanta` worked example (the translator-split, resolved)

PWG keeps one homonym; the sense-sharded layer restores the per-sense loci that the thin bilingual glossaries dropped:

- **sense 1a** — Elephantenzahn, Elfenbein H. an. 4,111 . MED. t. 203 . MBH. 12,3630
  - `<ls>`: H. an. 4,111, MED. t. 203, MBH. 12,3630
  - DCS: —
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
