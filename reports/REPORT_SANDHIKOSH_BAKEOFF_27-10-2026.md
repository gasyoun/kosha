# Report — SandhiKosh benchmark TSV import + splitter bake-off (H6841 / WHEEL9 item a)

_Created: 2026-10-27 · Executor: OxAlpha (opencode/z-ai/glm-5.3-flash) · Windows box, worker lane_

**Handoff:** [H6841](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6841-OxAlpha_kosha_wheel9-sandhikosh-benchmark-bakeoff_14.10.26.md)
**Gate provenance:** the handoff's structured `{gate: until:2026-10-18}` self-released by expiry
(deep manual §4.3: until-gates "release themselves on expiry"; H6842 sibling executed on the same
reading, PR #1115 close notes "structured until-gate self-released per deep manual §4.3; no refusal
recorded"). The GTD `@DECIDE WHEEL9-sandhi-nlp-wave1` row itself stays MG's — pending as card A7 of the
H7132 decide-bundle; this handoff makes NO claim of MG adoption and takes no decision for MG.
**Bench provenance:** [wheel-watch-sandhi-nlp-2026-10.md](https://github.com/gasyoun/Uprava/blob/main/reports/wheel-watch-sandhi-nlp-2026-10.md)
(map 7, sandhi-scaffold row, ADOPT) + [docs/EVAL_SETS_CENSUS_14-10-2026.md](https://github.com/gasyoun/Uprava/blob/main/docs/EVAL_SETS_CENSUS_14-10-2026.md) bucket A.

## 1. Asset landed

`data/sandhi/sandhikosh/` — 6 committed TSVs (13,929 benchmark items, columns
`id, word, split, rule, type, source`) + `convert_summary.json` +
[README.md](../data/sandhi/sandhikosh/README.md) with full license facts:

- upstream `sanskrit-sandhi/SandhiKosh`, last commit `b4938f8…` (2020-01-30), dead repo, 12★, **no license file**;
  only statement = README "free of cost for research purposes only" + LREC 2018 citation.
- Raw xls mirror **kept out of git** (license-gated-ingest: research-only clause, redistribution
  unstated). TSV layer committed as the derived measurement layer permitted by H6841; manifest tier `restricted`.
- Convert: `python tools/sandhikosh_xls_to_tsv.py --src <dir-with-xls>` (deterministic; xlrd).

## 2. Bake-off (per-category, denominators, reproduce)

Harmonies: [tools/sandhikosh_bakeoff.py](../tools/sandhikosh_bakeoff.py) reuses the
WHEEL6/H6456 pattern (`SanskritGrammar/scripts/pilot_process_sanskrit_vs_rules.py`) —
no splitter or scorer rebuilt. Protocol: gold/preds transliterated Devanagari→IAST
(indic-transliteration), compared after the H6456 canon (NFC + anusvāra → m). Items with a
space in the joined surface (no single junction; 4,921 of 13,929) excluded by protocol and
counted per source. Metrics: exact full-split match + first-token match. Full run = 12.6 s.

```
pip install xlrd process-sanskrit indic-transliteration
python tools/sandhikosh_bakeoff.py                      # metrics JSON → reports/sandhikosh_bakeoff_metrics.json
python tools/sandhikosh_xls_to_tsv.py --src <xls dir>   # regenerate TSVs (byte-identical)
```

| category | n scored | nulls | upstream raw exact % | upstream+pausa exact % |
|---|---|---|---|---|
| vowel | 2,329 | 29 | 53.93 | **58.95** |
| consonant | 3,848 | 171 | 49.61 | **57.82** |
| visarga | 2,318 | 167 | 0.00 | **46.72** |
| unlabeled (rule_literature sheet) | 145 | 1 | 24.83 | **29.66** |
| **overall** | **8,640** | 368 | **37.05** (3,201) | **54.68** (4,724) |

First-token: raw 49.33% · pausa 66.18%.

| source | scored | excluded (no single junction) | raw exact % | pausa exact % |
|---|---|---|---|---|
| uoh (9,368) | 6,521 | 2,847 | 43.09 | 63.29 |
| astadhyayii (2,700) | 1,199 | 1,501 | 5.50 | 13.09 |
| bhagvad_gita (1,429) | 878 | 551 | 30.64 | 41.46 |
| rule_internal (150) | 147 | 3 | 1.36 | 3.40 |
| rule_external (132) | 117 | 15 | 15.38 | 23.93 |
| rule_literature (150) | 146 | 4 | 24.66 | 29.45 |

## 3. Findings

1. **The adopted house splitter (Process-Sanskrit 1.5.2, WHEEL6 verdict) measures 37.05% exact
   raw / 54.68% with the `_pausa_normalize` house convention** on the SandhiKosh junction bench —
   same ballpark as its 42.8% on the H6456 DCS-gold junctions. First public cross-benchmark
   measurement of the adopted runtime.
2. **Visarga category: 0.0% raw → 46.72% with pausa normalization.** The raw arm's miss was
   wholesale-formal, not competence: upstream's `canonical()` yields Pāṇinian pausa forms
   (`vacanas`) while SandhiKosh gold is visarga citation form (`vacanaḥ`). Both numbers are
   reported per H6456's symmetric-comparison discipline (relative comparison valid; the raw-vs-pausa
   delta is itself the interesting quantity). Remaining visarga misses now carry the same class
   profile as other categories (over-split / unknown pada examples in the JSON).
3. **Ours (rule-lookup audit arm): 1 scored / 9,007 null / 0 exact.** Replicates the H6456
   structural diagnosis on an external benchmark — the induced/hand `X Y → Z` tables
   (41 files, 9,796 surface keys, work-internal IAST) essentially never contain a SandhiKosh
   joined form's exact surface, rule-lookup without a lexicon/morphology cannot segment
   arbitrary sandhi text. The rules stay a niche audit layer; the split runtime stays upstream.
4. **Astaadhyayii sheet underperforms everywhere (5.5% raw):** sutra-rule "words" are
   Pāṇinian abbreviation formulas (e.g. `mukhanāsikāvacano'nunāsikaḥ`, `nājjhalau` with gold
   padānta `n + ajjhalau`), not attested sandhi — a benchmark-internal caveat users should know.

## 4. Neuro arm — HONESTLY DECLINED

ByT5-Sanskrit / CharSS (method C per the wheel dossier): **not run.** The kosha sandhi harness
hosts three methods (A DCS-gold / B vidyut-cheda / C DharmaMitra API) — none hosts the HF
checkpoints for ByT5-Sanskrit or CharSS; wiring them would be rework, which the H6841 step-3
"IF the harness hosts them without rework" clause excludes. No network dependency was added.

## 5. Registry rows

- kosha `data/manifest/datasets.json`: `sandhikosh-tsv` (tier `restricted`, in_release
  `not-applicable`, rights note = research-only clause, builder = this converter).
- Uprava [REUSE_INDEX.md](https://github.com/gasyoun/Uprava/blob/main/REUSE_INDEX.md): row for
  the TSV asset + the two tools.

## Verifier instructions (fresh context)

Open `data/sandhi/sandhikosh/README.md` (license row: research-only, no LICENSE file upstream);
re-run `python tools/sandhikosh_bakeoff.py` on the committed TSVs and confirm the headline:
upstream 37.05% exact (3,201/8,640), upstream+pausa 54.68% (4,724/8,640), visarga 0.00→46.72;
denominators as §2 table; `data/sandhi/sandhikosh/*.xls` must NOT exist in git
(`git ls-files data/sandhi/sandhikosh` shows only tsv/json/md).