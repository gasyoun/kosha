# NWS residue classification — the 82.7% «absent» decomposed (H6050 · epic E024)

_Created: 06-10-2026 · Last updated: 06-10-2026_

_Driver: [`scripts/nws_residue_classification.py`](https://github.com/gasyoun/kosha/blob/main/scripts/nws_residue_classification.py) · tests: [`tests/test_nws_residue_classification.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_nws_residue_classification.py) (10/10 offline green; `--selftest` pins every number below)_

_Rights: MLU Halle-Wittenberg — texts usable with attribution (Impressum probe 04-10-2026). This doc quotes lemma headwords only, no sense prose; the per-lemma dump is regenerable locally via `--dump` and is not committed._

## The question (H6050)

Classify the NWS-Halle residue outside the union PWG∪PW∪MW∪SCH∪ACC∪PWKVN — the **138,976** stem-absent lemmas (82.7%, H5932 baseline; the 1,340 SCH-removable are already excluded there) — into: sigla-parse errata / rare real lexemes / lemmas uncollected in the reference dictionaries, and estimate the **true coverage gain** the union gets from NWS.

## The answer

**The 82.7% is a transliteration-convention artifact, not lexical novelty.** The H5932 baseline matched tar *filename stems* (`_a_sana`, the site's underscore convention) against SLP1 `<k1>` sets — two different namespaces. Each per-lemma JSON carries the same headword as `key1` in SLP1, and matching on it recovers essentially the whole residue.

| Class | Rule (first-match cascade) | n | % of residue |
|---|---|---:|---:|
| C1 `translit_exact` | `key1` ∈ union (exact) | **138,952** | **99.9827%** |
| C2 `content_uncollected` | `key1` ∉ union, entry carries NWS/SCH content | **0** | 0.0000% |
| C3 `errata_near` | `key1` ∉ union, empty, len ≥ 4, Levenshtein ≤ 1 to some union key | **18** | 0.0130% |
| C4 `orphan_empty` | the rest (scrape artifacts, short junk, sandhi-shaped fragments — all empty) | **6** | 0.0043% |
| **Sum** | | **138,976** | **100.000%** |

Over **all** 167,991 NWS lemmas (not just the residue): `key1` ∈ union for **167,967 (99.986%)**. The whole NWS adds **24 lemma-keys** to the six-dictionary union — and every one of the 24 is a content-empty record (no `nws`, no `sch`, `pw_len` 0, no `has_nws_extra`). **True new-lemma gain of the union from NWS: 24 empty keys (0.014%); content-bearing gain: zero.**

Where NWS *does* add value: the sense/sigla layer on existing lemmas — 25,711 residue entries carry NWS sense content (all flagged `has_nws_extra`); per-dict residue-C1 hits: PW 124,822 · MW 109,959 · PWG 85,809 · SCH 22,946 · PWKVN 11,898 · ACC 8,803.

### Examples per class

- **C1** (translit-recoverable): `_a_sana` → `ASana` *āśana* (PWG) · `_a_b_asa` → `ABAsa` *ābhāsa* (PW/MW; rich NWS sense apparatus) · `vy_as_azwaka` → `vyAsAzwaka` (PWG/PW/MW/ACC) · `k_alav_ala` → `kAlavAla` (PW/MW/SCH/PWKVN). Stem-convention features carried by the residue: `_a` 101,132 · `_s` 26,226 · `_i` 25,183 · `_r` 20,597 · `_d` 17,629 · `_b` 15,559 …
- **C3** (one letter from a union word): `_s_urya` → `SUrya` *śūrya* — one substitution from `sUrya` (PW/PWG/MW/ACC): a real s/s-ś encoding erratum · `varg_iyi` → `vargIyi` ~ `vargIya` (PW/PWG/MW) · `s_am_uika` → `sAmUika` ~ `sAmika` (PW/PWG/MW). Caveat: some Lev-neighbours are themselves errata inside the union (e.g. `Q`-insertion ghosts), so C3 means «one letter from *something attested*», not «certainly a typo of a real word».
- **C4** (orphans): `_watch_state` (scrape-state file caught as a lemma; no key1) · `pravoar`, `voave` (Slavic-looking site junk) · `jau`, `dfa`, `b_aa` (short fragments) · `suarm_ia`, `svarm_ia` (sandhi-shaped …m+īa fragments).

Mapping to the mission's named classes: «эрраты сигл-парса» = C3+C4 (24, all empty) plus the stem-convention decoding itself (C1 is a *namespace* effect, not errata in the data); «редкие реальные лексемы» = **0 measured**; «несобранные в эталонах» = **0 with content** (the 6 C4 orphans are the only candidates and are all junk/empty).

## Method

Deterministic, no hand lists: H5932-method key extraction (stems = tar filename stems, leading `-` stripped; dict keys = `<k1>` on `<L>` lines, whitespace-stripped, leading `-` stripped — ported from [`csl-observatory nws_halle_intersections.py`](https://github.com/sanskrit-lexicon/csl-observatory/blob/main/scripts/nws_halle_intersections.py), pr #259); then the cascade above. Near-neighbour test = all substitution/deletion/insertion variants over ASCII letters ∩ union. Inputs pinned: `pwg-ru-data/layers/nws.tar.gz` sha256 `054b05da…` (167,991 lemmas), csl-orig @ `f4c08c5` (union 243,157).

## Reproduction

```
python3 scripts/nws_residue_classification.py --selftest [--dump DIR]
# SELFTEST PASS: all pinned H6050 numbers reproduce exactly.
python3 -m pytest tests/test_nws_residue_classification.py   # 10 passed
```

Spot-verification of C1 against raw csl-orig (10 random members, `grep -c '<k1>…<'` per dict) — 10/10 genuine `<k1>` lines; the 24-key true residue hand-checked in full.

## Consequences

1. **A61 / H5941**: the 82.7% stem-based figure must NOT be cited as lexical novelty. The key1-based headline is: 167,967 of 167,991 NWS lemmas (99.986%) exist in PWG∪PW∪MW∪SCH∪ACC∪PWKVN by headword; NWS's novelty is the sense/sigla layer on those lemmas, not new headwords. H5941's §2.1/§10.1 wording should say exactly that.
2. **H5937/H5938 re-scope**: at the lemma level this classification *is* the fuzzy-pass answer (delta −138,952, decomposition above); the remaining sigla-parse/fuzzy value is in the sense field, not the lemma keys.
3. **NWS_HALLE_ANALYSIS_2026-10-04.md** (Uprava): its «пост-петербургская лексика в masse» reading of the 82.7% is an artifact of the namespace mismatch — addendum owed there (Uprava PR, same batch).
4. **Ingest (H6064) / PWG→RU queue**: match NWS entries into the estate by `key1`, not by stem; keep the 24 orphans out of any lemma inventory until hand-ruled.
