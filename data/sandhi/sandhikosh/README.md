# SandhiKosh TSV layer — provenance + license facts (H6841 / WHEEL9 item a)

_Created 27-10-2026 · executor OxAlpha (opencode/z-ai/glm-5.3-flash) · handoff
[H6841](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6841-OxAlpha_kosha_wheel9-sandhikosh-benchmark-bakeoff_14.10.26.md)_

## What this is

TSV conversion of the four [SandhiKosh](https://github.com/sanskrit-sandhi/SandhiKosh)
xls workbooks — the first (and only) public Sanskrit sandhi benchmark
(LREC 2018: Bhardwaj, Gantayat, Chaturvedi, Garg, Agarwal, *Sandhikosh: a
benchmark corpus for evaluating sanskrit sandhi tools*). Used here as the
EXTERNAL eval anchor for the sandhi-scaffold splitter bake-off
([tools/sandhikosh_bakeoff.py](../../../tools/sandhikosh_bakeoff.py),
[report](../../../reports/REPORT_SANDHIKOSH_BAKEOFF_27-10-2026.md)).

| file | upstream sheet | rows | columns |
|---|---|---|---|
| uoh.tsv | UoH_Corpus.xls / Sheet1 | 9,368 | id, word, split, rule, type, source |
| astadhyayii.tsv | Astaadhyaayii Corpus.xls / Sheet1 | 2,700 | id (sutra:loc), word, split, rule, type, source |
| bhagvad_gita.tsv | Bhagvad_Gita Corpus.xls / Sheet1 | 1,429 | id, word, split, type |
| rule_internal.tsv | Rule-based…xls / Internal | 150 | id (internalsandhi_N), word, split, rule, type |
| rule_external.tsv | Rule-based…xls / External | 132 | id (externalsandhi_N), word, split, rule, type |
| rule_literature.tsv | Rule-based…xls / Literature | 150 | id (literature_N), word, split |

Total 13,929 items. One upstream row skipped (bhagvad_gita: empty word/split).
No cell content changed: NFC normalization + whitespace trim + numeric rule
cells rendered without the xls float (`1.0` → `1`). `convert_summary.json` is
the emitted counts receipt.

## License facts

- **Upstream license: NONE on file.** The repo ships no LICENSE file and no
  SPDX identifier (GitHub license API: `null`) and has been dead since
  2020-01-30 (last commit `b4938f82982a3217899fb554bbc093fab3a6b85b`).
- **Only license statement** is the repo `README.txt`, verbatim: "The corpus
  is provided below free of cost for research purposes only. If you use this
  corups [sic] in your research, please cite the following paper:" (LREC 2018
  citation — Bhardwaj et al., *Sandhikosh*, Proceedings of LREC 2018, May
  2018, Miyazaki).
- Classification: research-only clause, redistribution terms unstated →
  **NOT a public/redistributable license**. Mirror-only discipline applies.

## Gating decisions (license-gated-ingest, H6841)

1. **Raw xls mirror is NOT in git** — kept in the box-local scratch only
   (`C:/Users/COMPUTER/AppData/Local/Temp/opencode/h6841-upstream-mirror/`,
   verified byte-identical to upstream by git clone checksum). It is NOT a
   published asset. The xls binaries are not vendored anywhere in this repo.
2. **This TSV layer is committed** as the *derived measurement layer* allowed
   by H6841 ("derived measurements publishable"): it re-keys the benchmark
   junctions into the harness protocol (id/word/split/rule/type/source) so the
   bake-off is reproducible from git without fetching upstream. The benchmark's
   scholarly content is thereby in git under the upstream research-only clause;
   the upstream README citation obligation is honored by this file. If any
   future use goes beyond research (distribution, serving), treat before
   release as rights-gated — tier in the kosha dataset manifest is
   accordingly `restricted` (not in any public release bundle).
3. **No GPL vendoring**: none of the GPL repos named by H6841
   (scl, Sandhi_Prakarana, shantanuo) is touched; SandhiKosh itself is not
   forked, no upstream PR, upstream untouched.

## Reproduce

```
pip install xlrd
python tools/sandhikosh_xls_to_tsv.py --src <dir-with-SandhiKosh-xls>
```

Idempotent: re-running on the unchanged workbooks yields byte-identical TSVs.
Converter: [tools/sandhikosh_xls_to_tsv.py](../../../tools/sandhikosh_xls_to_tsv.py).