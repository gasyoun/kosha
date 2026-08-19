# IMPLEMENTATION — kosha inflect + pedagogy residual

_Created: 19-08-2026 · Last updated: 19-08-2026_

Index: [PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md).

Ordered steps per unit. Every unit starts with `precheck_handoff.py` + claim and a
session-unique worktree (`../kosha-h<id>-<pid>` off `origin/main`); kosha is a
guarded main tree.

## K1 — [H3165 (Sonnet 5) — Wave U2: drip the three prepared csl-inflect PRs](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3165-Sonnet_csl-inflect_inflect-u2-drip-prepared-prs_19.08.26.md)

1. Locate the H093 fork and confirm the three branches still exist:
   `devanagari-input`, `help-examples`, `output-polish`.
2. **Re-verify each against current upstream `main`.** The merged probe changed
   `web/` CSS, so at minimum `output-polish` may now conflict. Rebase; re-test
   under PHP CLI as H093 did.
3. Open **PR 1 only** (`devanagari-input`). PR body: what it does, how it was
   tested, nothing about kosha, nothing about the tool being deficient.
4. **Wait.** Merged → open PR 2. Not merged → file a GTD `@WAITING` row naming the
   PR and its open date, flip Wave U2 in the roadmap to "parked, awaiting PR #N",
   and stop. Parking is a legitimate exit.
5. Repeat for PR 3.
6. Same pass: update Wave U2's status in
   [ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md).

## K2 — [H3166 (Opus 5) — Verb dhātu-identity crosswalk](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3166-Opus_kosha_inflect-dhatu-identity-crosswalk_19.08.26.md)

1. Extract the root key each side actually uses: Cologne verb tables (as ingested
   by [`scripts/build_inflections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_inflections.py))
   vs vidyut-prakriya dhātupāṭha (`dhatu` + gaṇa + `sanadi` + prefix).
2. **Decompose the 87 % non-agreement** into: unmatched root key · matched root,
   different gaṇa · matched root+gaṇa, different form. This census decides whether
   the rest of the plan is worth running — publish it even if it says "no identity
   gap after all".
3. Build the crosswalk TSV with `match_basis` ∈ {`exact`, `anubandha-stripped`,
   `homophone-disambiguated-by-gaṇa`, `prefix-decomposed`, `ambiguous-multi`,
   `unmatched`}. One row per (Cologne key, vidyut key) pair; never many-to-one to
   raise the count.
4. Re-run [`scripts/compare_vidyut_verbs.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_verbs.py)
   keyed through the crosswalk. Emit **two** headline numbers: matched-subset
   agreement, and unmatched residue as a share of all cells.
5. Classify surviving divergences (engine bug · modelling fork · coverage gap),
   ≥40 rows hand-adjudicated, mirroring the nominal report's method.
6. Update the verb section of
   [`E1_DIVERGENCE_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md);
   draft (do **not** post) the [csl-inflect#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8) answer.
7. Tests green, manifest row if a new dataset, release, PR + merge.

**Stop before:** applying any verb hybridization. That is a separate ruling.

## K3 — [H3167 (Sonnet 5) — Re-run gloss.ru over the subhāṣita beginner pack](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3167-Sonnet_kosha_pedagogy-subhashita-gloss-ru-rerun_19.08.26.md)

1. Run the shipped gloss builder with `--gloss-lang ru` over the subhāṣita pack.
2. Compute per-pack RU coverage % **with its denominator**; publish beside the
   other packs' figures.
3. Regenerate the reader page + Anki deck so the RU toggle has data.
4. Hand-check 15 sayings: the RU triple must belong to the token, not a homograph.
5. Manifest row, release, PR + merge. Strike H1279's leftover TODO where logged.

## Truth-pass edits (already applied by H3001, listed so nobody redoes them)

| File | Correction |
|---|---|
| [ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md) | U2 condition marked **fired** with the PR #17 merge date; E1 flipped to ✅ with only the diplomacy-gated post parked |
| [docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_PEDAGOGY_SURFACES_2026_2027.md) | Wave RU flipped 🟡 queued → ✅ shipped, with the K3 leftover named |

## Fences (all units)

- Guarded main tree — worktree only, never the shared checkout.
- No `csl-orig` edits. No sandhi data edits. No sibling-repo source edits.
- One upstream PR open at a time; no upstream posting without the N1 go-ahead.
- RU gloss source stays the public site-tier subset.

_Dr. Mārcis Gasūns_
