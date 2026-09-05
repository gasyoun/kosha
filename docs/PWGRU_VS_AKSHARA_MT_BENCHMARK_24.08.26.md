_Created: 25-08-2026 · Last updated: 05-09-2026_

# H3456 — pwg_ru vs akshara-MT blinded benchmark: verdict memo

_Created: 24-08-2026 · OxAlpha (`opencode/x-preview-f-free`) executing H3456 (Fable 5 mint, MG «go здесь») · RESTRICTED inputs, public scores_

## Question

Is our c1-lane PWG→RU translation quality distinguishable from akshara.ru's AI MT of the same dictionary, on headwords where both exist?

## Design

- **Arms**: our frozen TM snapshot ([tm/pwg_ru_translated.jsonl](https://github.com/gasyoun/pwg-ru-data/blob/main/tm/pwg_ru_translated.jsonl), sha256 `811bbc21…`, 11,603 rows; 11,094 rows joined) vs H3455's parsed `pwg_ru` MT blocks. Blinded per item (seed 730 random A/B assignment), judge saw only anonymized packets + the German source.
- **Denominator honesty**: the planned "≥250 shared headwords" does not exist — the true three-way intersection our-TM ∩ their-MT ∩ sample is **101 heads**. LLM-judged on a size-stratified sample of **40** (seed 730); chrF computed on all 101. Both denominators reported.
- **Entry-level join** (their MT is one blob per entry; ours is subcard-keyed): sense-level alignment NOT attempted this pass.
- **Rubric**: adequacy 0–5 per arm per item (5 = full faithful rendering … 0 = off-topic). Judge = OxAlpha single-judge; calibration = all items read in full with per-item notes committed.

## Result

| metric | value |
|---|---|
| judged pairs | 40 |
| mean adequacy **ours** | **4.53** |
| mean adequacy **akshara MT** | **4.33** |
| paired diff (ours − theirs) | +0.20 |
| bootstrap 95% CI (5000 resamples) | **[−0.12, +0.53] — crosses zero** |
| win / tie / loss | 22 / 2 / 16 |
| score distribution ours | 19×4, 21×5 (never <4) |
| score distribution theirs | 3×3, 21×4, 16×5 (never <3) |
| chrF-6 mean over all 101 | 23.3 (weak signal: sense order/segmentation differ; secondary only) |

**Verdict: NO significant difference on this sample** (CI includes 0). Our lane is comparable-or-slightly-ahead; both are high-quality renderings of Böhtlingk–Roth.

## Where they differ (judge notes, consistent)

1. **Long entries → ours ahead**: within the equal 6000-char cap ours packs more real content (compact SLP1 keys vs their deva+iast duplication), completes preverb/caus/desid/intens sections, and structures senses explicitly.
2. **Tiny entries → theirs ahead**: one clean rendering with a Devanāgarī form and no artifacts; ours carries concat defects.
3. **Our known defects to fix** (actionable, cheap):
   - **duplicate-line artifacts** from subcard concatenation — worst case B090 (`vasin`) renders the WHOLE entry twice;
   - **source-language residues** in stub rows: untranslated "N. pr.", German "s."/"das."/"vgl." doubling ("s. см.", "ср. vgl."), genitive "-'s" left as-is;
   - **beyond-PWG enrichment mixed unflagged into `ru` text** ([NWS]/[Reg]/[Buddh] advisory rows) — dilutes fidelity-to-source and would contaminate any export that treats `ru` as pure PWG translation. Recommend a provenance marker or separate field.
4. Their systematic weaknesses (for completeness): UI furniture inside translated text («Показать парадигмы», «Стр. печ. изд.»), no structural sense markup.

## Provenance & rights

- Inputs restricted: judge packets + TM snapshot gitignored; ONLY scores/blinding map/chrF/stats are committed (no third-party text).
- Blinding map [blinding_map.jsonl](https://github.com/gasyoun/kosha/blob/main/data/akshara_pilot/bench/blinding_map.jsonl) committed alongside scores for auditability.
- **Public use of akshara MT text stays parked behind a fresh @DECIDE** — this benchmark changes nothing about that ruling.

## Next steps

1. Fix the three our-side defect classes above in the RussianTranslation pipeline (they are lane-internal, no akshara dependency).
2. Re-run this benchmark after the fixes if a publish decision ever needs it.
3. QUESTIONS_LOG row records the hypothesis outcome (comparable, not significantly different).

_Dr. Mārcis Gasūns_
