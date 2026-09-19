# Grammar Lab × vidyut derivation gaps — join report (H4795)

_Created: 19-09-2026 · Last updated: 19-09-2026_

Join of the SanskritGrammar grammar-lab-g1 topic graph (Whitney + Zaliznyak
root alternation, H2492) to kosha
[`panini-derivation-status`](https://github.com/gasyoun/kosha/blob/main/data/concordance/derivation_status.tsv)
(401,368 AG rows, H1368 W2a) by root/lemma, with the failing alternation
classes ranked by corpus frequency
([`lemma_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv)).

Builder (deterministic, read-only on all inputs, no network — R12):
[`scripts/grammar_lab_vidyut_gaps.py`](https://github.com/gasyoun/kosha/blob/main/scripts/grammar_lab_vidyut_gaps.py).
Output table:
[`grammar_lab_vidyut_gaps.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/grammar_lab_vidyut_gaps.tsv).

## Method

1. Each g1 topic carries exactly one whitney-root exemplar root
   (`anchor_key_slp1` from the bundle's Type-D edges); 32 topics → 14 distinct
   exemplar roots.
2. For each root, all `derivation_status.tsv` rows with
   `pos_tried ∈ {verbal, both}` are aggregated by `derivation_status`.
   **Failure = `engine-error`** (candidate cells existed, none derivable) —
   the W2a data statement already attributes engine-error to the verbal
   dhātu/gaṇa/lakāra mapping. **`ambiguous`** (>1 chain) is reported as a
   separate decision-fail column, never merged into engine-error.
3. Weight per failing row = corpus `count_all` of its attested form
   (fallback: the root's own lemma frequency, applied once per
   (root, status) bucket, never per row). Form→lemma frequency exact-match
   misses fall back silently to the root bucket; the fallback is counted, not
   hidden (see caveats).
4. Present-class labels come from the DCS M9 class lists
   ([`dcs-verb-roots-by-class`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json),
   443 attested roots) joined via
   [`src/kosha/transliterate.py`](https://github.com/gasyoun/kosha/blob/main/src/kosha/transliterate.py)
   IAST→SLP1. Roots absent from that list are reported
   `not-in-dcs-class-list` — an absence, never a guess.

## Headline findings

1. **Four of the 14 distinct exemplar roots are total vidyut failures,
   spanning 6 of the 32 topics** — and every engine-error root in the AG
   bucket has `ok = 0` **and** `ambiguous = 0`: failure is root-level (no
   verbal form of the root derives at all), not per-form noise. 4,300
   engine-error rows / 69 roots.
2. **The four failing exemplar roots, by corpus-weighted priority:**

   | Rank | Root (SLP1) | Weight | Engine-error rows | g1 topic(s) exemplifying it | DCS class |
   |---:|---|---:|---:|---|---|
   | 1 | `vac` | 9,291,044 | 304 | samprasarana | adAdi (2) |
   | 2 | `Sru` | 3,083,937 | 327 | open-vs-closed-roots · present-nu-class · attested-vs-predicted | not-in-list |
   | 3 | `hu` | 567,777 | 230 | present-reduplicating | juhotyAdi (3) |
   | 4 | `krI` | 12,844 | 76 | present-na-class | not-in-list |

   The topic table double-counts `Sru` across its three topics (one exemplar
   root per topic by g1 design) — the de-duplicated view is these four.

3. **Top engine-error roots overall** (any root, not only exemplars):
   `grah` (329 rows, w 1.42M), `Sru` (327, 3.08M), `vac` (304, 9.29M),
   `stu` (260, 391K), `hu` (230, 568K), `brU` (191, 1.51M), `banD` (126,
   278K), `As` (119), `laB` (155, 481K), `su` (141, 1.59M), `sev` (115),
   `pf` (150, 174K).
4. **Structural pattern in the failure roster:** the 69 failing roots cluster
   in exactly the alternation classes Whitney/Zaliznyak flag as
   irregular — set/nasal-class roots (`grah`, `banD`, `laB`, `lamb`, `mand`,
   `spand`, `stamB`, `skamB`), vocalic-ṛ roots (`pf`, `spf`, `SF`, `dF`,
   `mfg`, `Cfd`), class-IX nā-roots (`krI`, `pf`'s kryAdi side), class-V
   svAdi (`hi`, `spf`), and the reduplicating class (`hu`, `pf`). Roots in
   every attested DCS present class appear, but the weight is dominated by
   `adAdi` and `not-in-dcs-class-list` roots.
5. **Verbal derivation is weak even where the engine does not error:** the
   `kf` exemplar (8 topics) yields 20 ok / 804 verbal rows (2.5%);
   `BU` 28/431; `gam` 32/422. The g1 alternation topics are therefore a
   representative sample of a systemic verbal-derivation gap, not an outlier
   slice.

## Caveats

- g1 gives **one exemplar root per topic**, so the topic ranking is
  root-driven: several topics share a root and therefore a row of numbers.
  The TSV keeps them separate (the graph consumer needs per-topic rows); the
  report de-duplicates (finding 2).
- `not-in-dcs-class-list` means the DCS M9 lists (443 attested roots) do not
  carry the root — absence of a label, not absence of a class.
- `lemma_frequency.tsv` tail rows with empty `count_all` are skipped by the
  builder (known artifact of that file).
- Weights are exact-form lemma matches with a root fallback; they are a
  ranking signal, not a corpus total.

## Reproduce

```bash
python scripts/grammar_lab_vidyut_gaps.py
```

Requires siblings `../SanskritGrammar` (grammar_lab export) and
`../VisualDCS` (M9 class lists), both read-only.

Manifest row: `grammar-lab-derivation-gaps` in
[`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).

_Гасунс_
