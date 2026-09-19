# Gītā gold master vs DCS own tagging — divergence map (H4799)

_Created: 19-09-2026 · Last updated: 19-09-2026_

## What this is

The third Gītā QA leg. Two already existed; this one is new and distinct:

1. `gita-inflection-qa` (H874/W4): gold case·number·gender vs **kosha's own
   inflection engine** (E1 hybrid layer) — 93.0→98.7% agreement after re-cut.
2. `gold-adjudicate`-family checks: gold internal consistency.
3. **This dataset (H4799): gold master lemma/POS vs DCS's OWN hand tagging**
   of the same text — DCS chapters `MBh, 6, BhaGī 1..18` in
   `dcs_full.sqlite` (10,547 tokens), joined word-by-word against
   `data/gita/gita_gold_master.tsv` (9,092 gold words).

Builder: `scripts/gita_gold_vs_dcs_tagging.py` (~9 s, read-only over the DCS
DB). Artifact: `data/gita/gita_gold_vs_dcs_tagging.tsv` — 9,144 aligned
groups, one row per gold word / DCS token group.

## Alignment method

- Compound-aware group join: gold treats compounds as one word
  (`dharma-kṣetra`), DCS tokenises them apart (`dharma` + `kṣetra`) — groups
  carry 1 gold word ↔ 1..6 DCS tokens (`COMPOUND_SPLIT`, 584 groups; DCS has
  ~10% more tokens for exactly this reason).
- Sandhi-neutral join key: final `ḥ/ṃ/s` deleted symmetrically, avagraha →
  `a`, niggahita `ṁ`≡`ṃ`; vowel sandhi (`mahā`+`iṣvāsāḥ` ↔ `maheṣv-āsāḥ`)
  handled by a consonant-skeleton tier with a 0.55 difflib guard.
- Word-count drift recovered by minimal single-side drops with realignment
  proof (a blind drop-both freezes the offset — first version's defect).
- Residue: 85 `GOLD_ONLY` + 40 `DCS_ONLY` rows (1.4% of groups) — the two
  editions genuinely segment ~125 places differently.

## Headline numbers

| Measure | Value |
|---|---|
| Aligned groups | 9,144 |
| 1:1 groups (lemma/POS comparable) | 8,402 |
| Lemma string agreement | 3,363 (40.0%) |
| + known lemmatization conventions | 4,262 (50.7%) |
| POS agreement (coarse verb/nominal/indecl) | 5,385 (64.1%) |
| Exact MATCH rows | 2,933 (32.1%) |

## Findings

1. **The lemma gap is dominated by lemmatization conventions, not errors.**
   Five systematic families (975 rows):
   - `pronoun-stem` (615): gold cites the pronominal stem (asmat, yuṣmat,
     tat, yat, etat, kim), DCS the anaphoric form (mad, tvad, tad, yad,
     etad, ka).
   - `vowel-sandhi/contraction` (135): gold marks preverbs separately
     (`ava-√āp`, `pra-√ah`), DCS contracts (`avāp`, `prāh`).
   - `final-t/d+n` (70): `jagat/jagant`, `mahant/mahat` stem-shape variants.
   - `adverb--tas/-taḥ` (51): `tataḥ/tatas`, `bhūyaḥ/bhūyas`.
   - `nasal-class` (28): `sam-jaya/saṃjaya`, `puṁgava/puṅgava`.
2. **Genuine lemma divergences** (1,678 LEMMA_DIVERGE + 2,462
   LEMMA+POS_DIVERGE rows): root-choice disagreements (`√dṛś` vs `paś`,
   `prokta` vs `pravac`, `sant` vs `as`), sandhi-locked lemmas
   (`etat/enad`, `kim-cit/kaścit`), and POS-coupled ones — a candidate feed
   for manual adjudication, not auto-applied corrections.
3. **POS agreement (64%) is a floor, not a ceiling** — driven by two
   artifacts, both documented, neither a tagging error:
   - the gold master's `form_type` column is sparsely filled (13 of 9,092
     rows); POS is derived from the `code` column (`1n.1 m.`/`1v.1`), so
     ~238 words stay `unknown`;
   - participial treatment differs by design: gold tags finite use of
     participles as `verb`, DCS tags them ADJ/PART (nominal→indecl 1,171 and
     nominal→verb 741 are mostly this).
4. **DCS does not split compounds the gold master keeps joined** in 584+
   places — anyone consuming both datasets side-by-side must use group
   alignment, never positional alignment (this burned the first version of
   this very script; see `FINDINGS` note in the script docstring).

## Provenance

- Gold: `data/gita/gita_gold_master.tsv` (H848 W0, MIT/public, MG).
- DCS: `dcs_full.sqlite` `MBh, 6, BhaGī 1..18` — DCS upstream CC BY 4.0.
- Regen: `python scripts/gita_gold_vs_dcs_tagging.py` (needs the VisualDCS
  sibling checkout; deterministic, no network).

_Гасунс_
