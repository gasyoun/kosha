_Created: 13-07-2026 · Last updated: 13-07-2026_

# Metadoc — Corpus-wide sandhi extraction roadmap

Companion to [ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_CORPUS_SANDHI_PEDAGOGY_2026_2027.md).

## Purpose
Phased plan to scale the H872 Bhagavadgītā sandhi layer to all DCS (then GRETIL)
as reusable pedagogy data. Onboards a fresh session into *what exists, why the
inducer is the core, and what Phase 1 must do first*.

## Audience
Engineering sessions (Sonnet+) picking up any phase; a human owner ruling on the
curriculum difficulty metric and GRETIL license scope.

## Provenance
- Minted: [H882](https://github.com/gasyoun/Uprava/blob/main/handoffs/H882-Opus_kosha_corpus-sandhi-pedagogy-roadmap_13.07.26.md), 13-07-2026.
- Author model: Opus 4.8 (`claude-opus-4-8[1m]`).
- Decisions locked with a human 13-07-2026 (DCS-first · A/B/C bake-off · both
  outputs · all four deliverables · pedagogical-difficulty order).
- Grounded in a working Phase-0 proof, not speculation — two pilots run,
  numbers in §1.

## Ranked improvement backlog (of the roadmap itself)
1. Add the difficulty-metric formula once a human confirms weighting (currently
   prose-only in §5).
2. Fill concrete DCS text names for each Phase-2 tier (currently exemplary, not
   exhaustive) — derive from `dcs-conllu/files/` + a difficulty proxy.
3. Add expected `no-gold` recovery numbers once method B is measured.
4. Cross-link the Phase-4 surfaces to their owning repos' issues once opened.

## Limitations / known gaps
- Phase-0 method A misses vowel coalescence by design (DCS pre-splits it — §1a);
  the roadmap's headline "100 % ruled" is *of token-edge sandhi events*, not of
  all sandhi. Mode 2 (Phase 1) closes this. Do not quote the 100 % without that
  qualifier.
- Gītā-in-DCS lives inside the Mahābhārata dir; exact chapter isolation is
  unverified (risk §6b).
- Two-sided coalescence rules (5–6 %) are induced but unverified.

## Related
- Reuses: [build_gita_sandhi.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_gita_sandhi.py) `categorise()` (H872).
- New code: `scripts/dcs_sandhi_induce.py`, `scripts/compare_sandhi_methods.py`.
- Splitters: `vidyut-data/cheda`, DharmaMitra ([external_tools.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json)).
- Finding worth a FINDINGS append: "DCS FORM pre-splits vowel sandhi; recover via
  the `# text =` continuous line" (§1a).

## Revision history
| Date | Model | Change |
|---|---|---|
| 13-07-2026 | Opus 4.8 `claude-opus-4-8[1m]` | Created with Phase 0 shipped + proven; Phases 1–4 planned. |

_Dr. Mārcis Gasūns_
