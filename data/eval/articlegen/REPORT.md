# Article generation vs Cologne gold — metrics report

_Created: 18-11-2026 · Last updated: 18-11-2026_

**Executed under H6253 by Hy4 flash Free (`opencode-go/hy4-flash-free`);
filename tier OxAlpha retained as provenance (H3688).**

**Sample:** 100 main headwords × 2 models + 5 MG-canary rows.
Reference = frozen Cologne MW v02 gold; negative class = mutated wrong article.

## Metrics (main split, csl-observatory table format)

| Metric | GLM 5.3 Flash | DeepSeek 4.1 Flash |
|---|---:|---:|
| Gloss token F1 | 0.1437 | 0.1470 |
| Gloss char-3 F1 | 0.1303 | 0.1541 |
| Example F1 | 0.1923 | 0.1017 |
| Example recall | 0.2146 | 0.1333 |
| Citation attestation (Cologne inventory) | 0.5800 | 0.7433 |
| Citation gold-entry match | 0.1017 | 0.0767 |
| Root–headword ok | 0.9500 | 0.9500 |
| Gloss present | 1.0000 | 1.0000 |
| Examples present | 1.0000 | 1.0000 |

Parse failures: GLM 0 · DeepSeek 0

## Hallucination taxonomy

| Category | Instances |
|---|---:|
| example_not_in_gold | 389 |
| citation_not_in_entry | 201 |
| unattested_citation | 41 |
| root_headword_mismatch | 12 |

Full per-item evidence: [hallucination_taxonomy.tsv](hallucination_taxonomy.tsv).

## Canary (MG human act)

5 canary rows are held out. The scoring script reproduces the evaluation only after
MG fills `canary/mg_labels.tsv`; until then the canary verdict is **INCONCLUSIVE**
and no PASS is claimed.

_Dr. Mārcis Gasūns_
