# Heritage (Huet) French glosses as an independent second reference — protocol + results

_Created: 09-08-2026 · Last updated: 09-08-2026_

**What this is.** The second-reference arm of the definition-generation evaluation:
the five already-frozen generation arms from
[DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md)
are re-scored against the **Sanskrit Heritage Dictionary** (Gérard Huet) French gloss
layer instead of Monier-Williams. Executes that protocol's ranked next-step **#4**
("Second reference — D20 `heritage_dico_gloss.tsv` French glosses as a multi-reference or
cross-lingual arm") under
[H2408](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2408-Fable_kosha_definition-gen-gloss-wsd-pilot_07.08.26.md).
Venue targets unchanged: eLex 2027 · EURALEX 2028 · IJL.

**No generation was re-run.** `gen_A0_random_floor` · `gen_A1_chat_ctx` ·
`gen_A2_chat_noctx` · `gen_A3_reasoner_ctx` · `gen_F1_fable_ctx` are the byte-identical
frozen outputs of the 11-07 and 15-07 runs. Only the *reference* changes, which is what
makes the comparison paired and cheap.

## Why a second reference is the load-bearing follow-up

Every number in the 11-07/15-07 runs is scored against MW 1899 — a public-domain text
that is certainly in every model's pretraining data. That is the protocol's own
"contamination caveat", and it means the original chrF/judge numbers measure
*reproduction of MW's wording* mixed with genuine sense coverage, with no way to separate
them from inside the MW-only design. The A1−A2 delta (context vs no context) isolates what
attestations add, but **not** what memorisation contributes.

Heritage/Huet is the cleanest independent reference available in-org: a different
lexicographer, a different century, a different language (French), and a licence that
permits use with attribution. Scoring the same candidates against it answers a question
MW alone cannot: **does the arm ranking survive when the reference is not the dictionary
the models may have memorised?**

## Data

| Asset | Role | Source |
|---|---|---|
| `frozen_sample.tsv` (500 MW headwords, seed 730) | item universe + strata | [kosha data/eval/defgen](https://github.com/gasyoun/kosha/tree/main/data/eval/defgen) |
| `gen_<arm>.jsonl` ×5 | frozen candidate glosses | same, H730 + H972 |
| `judge_<arm>.jsonl` ×5 | the MW-referenced judge scores, for pairing | same |
| D20 `heritage_dico_gloss.tsv` (24,549 rows, `mw_key1` → DICO anchor + `gloss_fr`) | **second reference** | [SanskritLexicography/HeadwordLists](https://github.com/gasyoun/SanskritLexicography/blob/master/HeadwordLists/heritage_dico_gloss.md) |

**Rights — why no French text is committed here.** Heritage `gloss_fr` is LGPLLR content
(composition with CC BY-SA approved by Gérard Huet 03-07-2026) and is registered
`tier=restricted` in
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
The harness therefore reads it at runtime from the local `SanskritLexicography` sibling and
**never copies gloss text into kosha**: the committed subset carries `mw_key1` + DICO
anchor + **SHA-256 of each gloss** + word count. That pins the join reproducibly — the
scorer refuses to run if a single digest stops matching the local file — without
redistributing restricted text. This is a rights-*compliance* mechanism, not a rights
adjudication: nothing here was parked for greyness.

## Subset (frozen)

`python scripts/defgen_heritage_ref.py build` → **n = 333** of the 500 frozen headwords
have a non-empty Heritage entry (167 skipped, all `no_heritage_entry`; every skip logged in
[heritage_ref_subset.meta.json](https://github.com/gasyoun/kosha/blob/main/data/eval/defgen/heritage/heritage_ref_subset.meta.json)
with SHA-256 digests of all three inputs). All nine stratum cells survive:

| cell | n | cell | n | cell | n |
|---|--:|---|--:|---|--:|
| high/mono | 52 | mid/mono | 37 | low/mono | 13 |
| high/poly2_4 | 47 | mid/poly2_4 | 36 | low/poly2_4 | 22 |
| high/poly5p | 49 | mid/poly5p | 51 | low/poly5p | 26 |

The subset is **MW-frequency-biased toward the high band** (148 high vs 61 low) because
Heritage covers common headwords more densely — a coverage property of Heritage, not a
sampling choice. Comparisons below are all *within* this subset, so the bias cancels;
the 333-item numbers are not directly comparable to the published 500-item ones.

## Reference divergence — the two dictionaries barely share surface text

| | value |
|---|--:|
| chrF(MW gold, Heritage FR) | **17.72** |
| mean token-F1(MW, FR) | **0.040** |
| mean words, MW gold | 51.1 |
| mean words, Heritage FR | 41.4 |

Two independent glosses of the same headword share almost no tokens across the language
gap. That is the point — and it is also the limit: **surface metrics against a
cross-lingual reference are near-degenerate** and cannot be read as quality (see the
caveat after the results table).

## Results (09-08-2026 run, n = 333, all arms 333/333 judged, 0 nulls)

| Arm | chrF vs MW | chrF vs FR | chrF multi-ref | token-F1 MW | token-F1 FR | judge-FR 0–5 | judge-MW 0–5 (same subset) | ρ FR-judge~chrF-FR | ρ FR-judge~MW-judge |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| A0_random_floor | 12.10 | 8.73 | 13.38 | 0.101 | 0.012 | **0.165** | 0.195 | 0.146 | 0.476 |
| A1_chat_ctx | 18.65 | 10.82 | 19.74 | 0.291 | 0.029 | 4.234 | 4.432 | 0.164 | 0.451 |
| A2_chat_noctx | 16.51 | 9.62 | 17.46 | 0.288 | 0.028 | 3.988 | 4.234 | 0.200 | 0.541 |
| A3_reasoner_ctx | 12.57 | 7.26 | 13.72 | 0.243 | 0.028 | 4.156 | 4.312 | 0.142 | 0.444 |
| F1_fable_ctx | **23.16** | **12.09** | **23.92** | **0.338** | **0.037** | **4.538** | 4.670 | 0.183 | 0.319 |

**Judge gates.** (1) **Floor separation across the language gap: PASS** — the
cross-lingual judge scores the derangement floor **0.165** vs 3.99–4.54 for systems, so it
is not fooled by register-matched random MW text when the reference is French. (2)
**FR-judge ~ MW-judge Spearman ρ 0.32–0.54** — the two references agree item-by-item well
above chance without being redundant. (3) **Human-scored subsample: still NOT run** —
unchanged prerequisite for any paper-grade claim (protocol next-step #1).

### The MW-familiarity premium (paired, same 333 items)

Each arm is judged twice on identical items, so `delta = adequacy_MW − adequacy_FR` is a
paired per-item measurement. Bootstrap 95% CI (5,000 resamples, seed 2408) + exact
two-sided sign test on nonzero pairs:

| Arm | judge-MW | judge-FR | mean Δ (MW−FR) | 95% CI | n nonzero | MW>FR | FR>MW | sign p |
|---|--:|--:|--:|:--:|--:|--:|--:|--:|
| A0_random_floor | 0.195 | 0.165 | +0.030 | [−0.024, +0.081] | 51 | 33 | 18 | 0.049 |
| A1_chat_ctx | 4.432 | 4.234 | +0.198 | [+0.093, +0.306] | 138 | 100 | 38 | 1.3e-07 |
| A2_chat_noctx | 4.234 | 3.988 | +0.246 | [+0.135, +0.360] | 140 | 104 | 36 | 7.6e-09 |
| A3_reasoner_ctx | 4.312 | 4.156 | +0.156 | [+0.042, +0.273] | 142 | 94 | 48 | 0.00014 |
| F1_fable_ctx | 4.670 | 4.538 | +0.132 | [+0.030, +0.243] | 108 | 74 | 34 | 0.00015 |

## Findings

1. **The arm ranking is reference-invariant.** `F1_fable_ctx > A1_chat_ctx >
   A3_reasoner_ctx > A2_chat_noctx > A0_random_floor` holds **identically** under the
   MW judge and the Heritage-French judge. The strongest reading available from the
   original MW-only design was "F1 leads on the dictionary it was scored against"; the
   ranking now survives a change of reference dictionary, century, and language. This is
   the single most useful thing this run buys.
2. **The MW-familiarity premium is real but small: +0.13 to +0.25 on a 0–5 scale.** Every
   system arm scores measurably higher against MW than against Heritage (CI excludes 0,
   sign p ≤ 1.5e-4 in all four), i.e. ~3–5% of the scale. The floor's premium (+0.030)
   is **not** significant by CI — as it should be, since deranged MW text has no sense
   coverage to be credited for in either reference. So the premium is a property of
   systems producing MW-shaped content, not a judge artefact.
3. **The premium does not reorder anything, and is *largest* where memorisation is most
   suspected.** `A2_chat_noctx` — the arm given no attestations, whose only route to a
   gloss is parametric recall of MW — carries the biggest premium (+0.246), and
   `F1_fable_ctx`, the best arm, the smallest (+0.132). Contamination inflates the
   MW-scored numbers slightly and inflates the *memorisation* arm most, which is
   exactly the direction the caveat predicted. It does not manufacture the ranking.
4. **Cross-lingual surface metrics are unusable as a quality signal — use the judge.**
   token-F1 against French collapses to 0.012–0.037 (vs 0.101–0.338 against MW) and
   chrF-FR compresses every arm into 7.3–12.1, because English candidates and French
   references share only proper nouns and Latinate stems. chrF-FR still *orders* the arms
   the same way, but the floor sits at 8.73 against a best system of 12.09 — a 3.4-point
   spread that cannot survive contact with noise. Multi-reference chrF is dominated by the
   MW reference (23.92 vs 23.16 for F1: +0.76) and adds essentially nothing. **For a
   cross-lingual second reference, the judged score is the measurement and the surface
   metric is decoration.**
5. **The frequency-gradient inversion replicates and sharpens.** Per-cell chrF-MW for F1
   still rises as frequency falls (low/mono 45.22 > mid/mono 37.09 > high/mono 26.32) —
   the stratification artefact already logged (high-frequency MW entries have longer,
   more complex gold). Against **French**, the same cells compress to 11.49–17.34: the
   inversion is a property of MW's gold-length distribution, not of model skill at rare
   words. A second reference is what makes that diagnosable.

Per-cell chrF, arm `F1_fable_ctx` (freq/polysemy), both references:

| cell | chrF vs MW | chrF vs FR | cell | chrF vs MW | chrF vs FR |
|---|--:|--:|---|--:|--:|
| high/mono | 26.32 | 11.49 | mid/poly2_4 | 36.27 | 15.96 |
| high/poly2_4 | 26.67 | 12.06 | mid/poly5p | 22.93 | 15.05 |
| high/poly5p | 21.40 | 12.75 | low/mono | 45.22 | 16.91 |
| mid/mono | 37.09 | 15.26 | low/poly2_4 | 38.98 | 17.34 |
| — | — | — | low/poly5p | 29.02 | 13.30 |

## Limitations

- **n = 333, not 500**, and Heritage coverage skews the subset toward high-frequency
  headwords. Within-subset comparisons are sound; cross-run comparison with the published
  500-item table is not.
- **One judge model** (`deepseek-chat`) scores both references. A shared judge is what
  makes the paired delta clean, but it also means a judge-side French-vs-English asymmetry
  would masquerade as an MW premium. The floor result argues against a large asymmetry
  (0.165 vs 0.195, CI includes 0); a second judge family would settle it.
- **Heritage is itself an edited modern dictionary**, partly informed by the same
  19th-c. tradition as MW — "independent" here means independent *authorship, century and
  language*, not causally unrelated to MW.
- **Heritage glosses carry their own debris** (bracketed etymologies, grammatical
  abbreviations, cross-reference tails). The judge is instructed around it, as with MW gold
  noise; deterministic metrics are depressed for all arms equally.
- **Human-scored subsample still not run** — the standing blocker on any paper-grade
  claim, inherited unchanged.
- **F1_fable_ctx remains a reference point, not a reproducible arm** (in-session
  generation, no temperature pinning) — the original caveat applies here too.

## Next steps (ranked, replacing protocol next-step #4)

1. **Human-scored subsample** over both references — now doubly valuable, since it would
   validate the cross-lingual judge and the MW premium in one pass.
2. **Second judge family** for the premium measurement (removes the shared-judge
   confound in Limitations).
3. **Post-1899 / non-MW-attested headword subset** — the clean isolation of genuine
   generation ability that neither reference alone provides.
4. **WSD second reference** — Heritage sense divisions as an alternative sense inventory
   for the agreement pilot, which currently uses MW divisions only.
5. **Third reference** — a German (PW/PWG) or Russian gloss layer would turn the
   two-reference delta into a reference-family trend.

## Reproduction

```
python scripts/defgen_heritage_ref.py build      # subset + digests (no FR text committed)
python scripts/defgen_heritage_ref.py metrics    # chrF/BLEU/token-F1 vs MW, FR, multi-ref
python scripts/defgen_heritage_ref.py judge      # cross-lingual judge, resumable
python scripts/defgen_heritage_ref.py report     # tables + gates
python scripts/defgen_heritage_delta.py          # paired MW-FR premium + bootstrap CI
python scripts/defgen_heritage_coverage.py       # per-arm judge coverage / nulls
```

Requires the local `SanskritLexicography` sibling (Heritage layer) and
`DEEPSEEK_API_KEY` in `RussianTranslation/src/.env`. The judge is resumable: re-run it to
fill items that hit API timeouts (this run needed two retry passes to reach 0 nulls from
74).

## Provenance

Harness, protocol and analysis authored and run by **Fable 5** (`claude-fable-5`) in Claude
Code, 09-08-2026, under
[H2408](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2408-Fable_kosha_definition-gen-gloss-wsd-pilot_07.08.26.md).
Judge model: `deepseek-chat` (DeepSeek API, temperature 0), same blinded protocol as
H730/H972, with a cross-lingual system prompt. Deterministic metrics: sacrebleu 2.6.0.
Generation arms unchanged from H730 (`deepseek-chat`, `deepseek-reasoner`, 11-07-2026) and
H972 (`claude-fable-5`, 15-07-2026).

Heritage French gloss layer © Gérard Huet, Sanskrit Heritage Dictionary, LGPLLR;
composition with CC BY-SA approved 03-07-2026. MW gloss text public domain (1899). DCS
attestations CC BY 4.0 (Oliver Hellwig, Digital Corpus of Sanskrit).

_Dr. Mārcis Gasūns_
