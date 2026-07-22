# PLAN_KOSHA_SENSE_FREQUENCY_2026H2 — metadoc

_Created: 22-07-2026 · Last updated: 22-07-2026_

**Subject doc:** [PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md)

## Purpose
Execution-ready `/ask` plan for a **per-sense** frequency layer ("частотность значений") in kosha, built
on DCS's WordSem = Sanskrit-WordNet gold. The index for a five-doc set (roadmap / architecture /
implementation / verification) driving handoff [H1453](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1453-Opus_kosha_sense-frequency-wordsem-3layer-wave1_22.07.26.md).

## Audience
The wave-1 execution agent (Opus 4.8) and any future session extending sense-frequency (wave-2 WSD, wave-3
surfaces). Secondary: anyone auditing the DCS-vs-MW sense-order finding.

## Provenance
Authored 22-07-2026, Opus 4.8 (`claude-opus-4-8`), via `/ask`. Three interview rounds with MG (goal/anchor,
architecture, verification+autonomy). Grounded in a prior-art sweep: SL FINDINGS §11 addendum / §78, INTERLINKS
§277, kosha manifest, WhitneyRoots token_attribution, semdom-amarakosha crosswalk (A58), Samsaadhanii/SCL index.

## The load-bearing discovery
The org had recorded the DCS sense-tags as an undecodable 9.3% (FINDINGS §78, measured on a **stub sqlite**).
The corpus-wide census (219/270 texts, INTERLINKS §277) shows WordSem is Sanskrit-WordNet gold and the
CoNLL-U releases are the real source. This reframed the project from "blocked/infeasible" to "bounded and
mostly-reuse". Any future doubt about feasibility should re-check the CoNLL-U WordSem coverage, not the sqlite.

## Ranked improvement backlog
1. **Verify the CoNLL-U WordSem decode path empirically** (Step-1 spike) — the single assumption the whole
   plan rests on; upgrade this doc to CONFIRMED once a real inventory row-count exists.
2. Pin the exact on-disk path + release version of the DCS CoNLL-U corpus (left as Step-0 discovery).
3. Quantify the WN→MW `unresolved` fraction once `build_wn_mw_map.py` runs — decides how thin Layer 2 is.
4. Decide (post-wave-1, GTD @DECIDE) whether the sense-order delta becomes an ARTICLES paper.
5. Wave-2: resolve the SCL licence (H057) before any scrape.

## Limitations
- No accuracy claim is possible for wave-1 (it's the gold itself); accuracy only enters at the wave-2 gate.
- Layer 2 (MW) and Layer 3 (semdom) inherit the coverage of their reused crosswalks — not guaranteed full.
- Polysemy only; homonym splitting stays with WhitneyRoots.

## Related docs
- Roadmap / Architecture / Implementation / Verification (linked from the index).
- [DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md) (wave-2 WSD).
- M01 Ch6 "Senses: Inheritance and Order" (consumer of the sense-order delta).

## Revision history
| Date | Change | By |
|---|---|---|
| 22-07-2026 | Initial `/ask` plan set authored; H1453 minted | Opus 4.8 (`claude-opus-4-8`) |

_Dr. Mārcis Gasūns_
