# VERIFICATION — kosha inflect + pedagogy residual

_Created: 19-08-2026 · Last updated: 19-08-2026_

Index: [PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md).

Missing evidence is INCONCLUSIVE, never PASS
([PLAYBOOK_EVIDENCE_OF_DONE_2026.md](https://github.com/gasyoun/Uprava/blob/main/docs/PLAYBOOK_EVIDENCE_OF_DONE_2026.md)).

## Per-unit gates

| Unit | PASS requires | FAIL looks like |
|---|---|---|
| **K1** | Per branch: rebase note, PHP-CLI test result, PR URL, merge state. If the drip stopped, a GTD `@WAITING` row naming the open PR and its date | Two of our PRs open on csl-inflect at once · any PR body referencing kosha's own inflect surface or framing the Cologne tool as deficient · a branch opened without re-verifying against current `main` |
| **K2** | Crosswalk TSV with row counts **by `match_basis`** · matched-subset agreement % **and** unmatched residue % · ≥40-row class-weighted hand adjudication · drafted-not-posted #8 answer · updated `E1_DIVERGENCE_REPORT.md` verb section · 229+ tests green | A single headline agreement % with no residue beside it · a many-to-one crosswalk row · any verb hybridization applied · anything posted upstream |
| **K3** | Coverage % **with numerator and denominator** · 15-row hand spot-check · manifest row · release tag · H1279 TODO struck | Coverage raised by widening past the public site-tier subset · a bare % with no denominator · re-curation of the 106-saying band |

## Programme-level gates

1. **Both source roadmaps tell the truth.** After the programme,
   `python Uprava/tools/roadmap_handoff_truth.py kosha/ROADMAP_INFLECT_2026_2027.md kosha/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md`
   must show no referenced handoff in a state the document contradicts.
2. **No silent caps.** If a unit covers less than its stated scope (fewer branches
   dripped, a sample smaller than specified), the shortfall is `log()`-ed in the
   close row. Silent truncation reads as full coverage.
3. **Every number carries its denominator.** Agreement %, coverage %, residue % —
   a bare percentage in any close row is a FAIL of this programme's reporting
   contract, regardless of the underlying work.

## The specific regression this programme exists to prevent

A conditional wave whose condition fires unnoticed. Wave U2 sat "conditional" for
six weeks after its condition was satisfied on day one, and no scan caught it
because every handoff it referenced was ✅ — the mechanical drain census reads a
fully-closed roadmap as *drained*, not as *lying*.

**Standing check for any future conditional wave in kosha:** a wave gated on an
external event must name the observable that decides it (here: a PR's merge state)
in a form a script can read. A condition phrased only in prose is a condition that
will expire silently. Applies to the drip protocol's own stopping rule too.

_Dr. Mārcis Gasūns_
