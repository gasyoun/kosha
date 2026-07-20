# Bloomfield RV pratīka cross-reference — build report

_Created: 13-07-2026 · Last updated: 13-07-2026_

Built by [scripts/build_bloomfield_rv_crossref.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_bloomfield_rv_crossref.py), resolving CONCORDANCE_ROADMAP.md's Bloomfield-source `@DECIDE` (rights cleared by Marco Franceschini, University of Bologna — see [data/manifest/rights/franceschini_hos9_permission_2026-07-13.md](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/franceschini_hos9_permission_2026-07-13.md)).

## Source

Marco Franceschini's digital edition of Bloomfield's *A Vedic Concordance* (Harvard Oriental Series 9, 1906) — `SanskritLexicography/review/HOS9-Bloomfield-VedConcord1906/` (UTF-16, 88835 concordance entries, alphabetically pratīka-keyed, covers the whole Vedic corpus not just RV).

## Counts

| metric | value |
|---|---|
| RV entries in Bloomfield's concordance (any locus, not just RV) | 36680 |
| distinct RV (maṇḍala,sūkta,verse) keys cited | 10374 |
| RV subset rows in parallel_passage_verses.tsv | 13581 |
| **validated `bloomfield_pratika` matches (column populated)** | **11522** |
| candidate found but text validation failed (left blank) | 1366 |
| unlettered/whole-verse citations (ambiguous half, not auto-attached) | 194 |

## Method — why this is validated, not positional

`parallel_passage_verses.tsv` splits every RV verse into exactly 2 rows (a printed first-half / second-half convention), which does **not** line up 1:1 with Bloomfield's grammatical a/b/c/d pada lettering for the RV's common 4-pada meters (triṣṭubh, anuṣṭubh, jagatī). Naively mapping row 1→pada a, row 2→pada b would silently mismatch on those. Instead: Bloomfield's a/b citations are bucketed to half 1, c/d to half 2, and every bucketed match is **independently validated** — parenthetical variant-reading asides stripped (e.g. "agnim īḍe (ŚŚ.ŚG. īle) purohitam" → "agnim īḍe purohitam"), `form_key()`-normalized, then checked as a **substring** (not just a prefix, since a pada can sit anywhere within its printed half-line) of that half's own `source_text`, with the pratīka's own **final character dropped** before the check — Bloomfield cites each pada in isolated/pausa form ("purohitam"), while the half-line's continuous text carries the actual external sandhi ("purohitaṁ yajñasya", -m→-ṃ before y-), so an exact-final-character match would systematically fail on any non-final pada. Raised the validated rate from an initial prefix-only/no-truncation pass (57%%) to 85%% (11,522/13,581). Only validated matches populate the column; a bucketed-but-unvalidated candidate is left blank and counted (not forced in).

## Honest residue

- **The remaining ~15%% (1,366 rows) is genuine orthographic variance between the two independently-produced digitizations, not a matching bug** — spot-checked, not silently written off. Two recurring patterns: (1) anusvāra-vs-homorganic-nasal spelling *mid-word* (e.g. Bloomfield's "teṣāṃ" vs the PARA digitization's "teṣām" — both valid before a labial, `form_key()` only folds true anusvāra, not this homorganic-consonant convention difference, and it isn't at the final character the truncation targets); (2) consonant-doubling variants (Bloomfield's "gachati" vs "gacchati") — a scribal/digitization convention difference between the two editions. Chasing these further would need edition-specific normalization tuned to risk false-positive matches elsewhere, so they are left unvalidated rather than forced.
- Unlettered Bloomfield citations (a whole-verse reference with no pada letter) are not auto-attached to either half — genuinely ambiguous which half they belong to without a letter to bucket on.
- This build resolves only the RV subset (CONCORDANCE_ROADMAP.md's stated Q2 scope for the Bloomfield cross-reference); the concordance itself covers the whole Vedic corpus (AVŚ, AVP, TS, MS, KS, VS, ŚB, TA, etc.) — `bloomfield_rv_citations.tsv` only extracts the RV-cited subset, the rest is future work if a similar cross-reference is wanted for other texts.
- Cross-references within Bloomfield's own concordance (`See <pratika>.`) are not resolved/followed — only direct RV citations are indexed.

_Dr. Mārcis Gasūns_
