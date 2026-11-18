# Article generation against Cologne gold — protocol and results

_Created: 18-11-2026 · Last updated: 18-11-2026_

**What this is.** Executes H6253 (OxAlpha-titled; run by Hy4 flash Free,
`opencode-go/hy4-flash-free`, provenance per H3688): generate full dictionary
articles — gloss, examples, citations, inferred root — for 105 A55 union
headwords with two model arms, score them against frozen Cologne Monier-Williams
gold, and publish a hallucination taxonomy. The 5-article MG canary stays a
human act; no PASS is claimed until it is filled.

**Prior-art verdict (EXISTS at the gloss level; PARTIAL at article level).**
kosha already carries the definition-generation line —
[DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md](DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md),
H730/H752/H972/H2408, a frozen 500-headword sample with gloss-only arms and a
gated judge. H6253 does not duplicate it: the unit of generation here is a
whole article (examples and citations are first-class scored fields), the gold
is the Cologne MW entry itself rather than a gloss string, and the deliverable
includes a citation-attestation and hallucination taxonomy. The existing
harness scripts (`defgen_score.py` etc.) were read; no shared code was copied.

## Frozen inputs

| Input | Role | Provenance |
|---|---|---|
| `HeadwordLists/union/union_headwords.tsv` (A55, 323,422 rows) | headword universe | SanskritLexicography, `kosha` data-v0.4.0 |
| `csl-orig/v02/mw/mw.txt` (286,525 `<L>` entries) | Cologne gold + citation inventory | CDSL MW, public domain |
| seed `6253` | deterministic sample | 152,577 eligible keys (union ∩ MW with ≥1 `<s>`, ≥1 `<ls>`, gloss ≥20 chars) |

105 keys sampled: 100 main + 5 canary. SHA-256 of both inputs is recorded in
`data/eval/articlegen/sample.meta.json`. Scoring always reads the frozen
`sample.tsv` and `citation_inventory.json`, never a re-derived join.

## Arms

| Arm | Model | Input | Scored fields |
|---|---|---|---|
| `glm` | GLM 5.3 Flash (`opencode-go/glm-5.3-flash`) | SLP1 + IAST + gender, no gold | gloss, examples, citations, root |
| `deepseek` | DeepSeek 4.1 Flash (`opencode-go/deepseek-v4.1-flash`) | same | same |

Gold-free prompts: each batch prompt contains only the headword fields, so the
answer key is structurally absent from generation context. Temperature is not
settable through the CLI path (one greedy-ish pass per batch, no retries).
**Contamination caveat (load-bearing):** MW 1899 is public domain and certainly
in pretraining. These numbers measure reproduction + grounding, not generation
from corpus evidence alone.

## Metrics (deterministic, no paid judge)

- **Gloss token F1 / char-3 F1** — set overlap with the frozen Cologne gloss,
  after SLP1→IAST transliteration of the gold side (the generated side is IAST)
  and Unicode case/diacritic folding. Comparing the two raw scripts would score
  a representation mismatch, not reproduction.
- **Example F1 / recall** — near-exact reproduction: char-3 F1 ≥ 0.5 against a
  Cologne `<s>` example after the same script normalisation (an em-dash-split
  SLP1 compound like `rADA—nATa` must not score zero against its IAST spelling).
- **Citation attestation** — share of generated abbreviations found in the
  Cologne MW `<ls>` inventory (38,672 unique abbreviations); a citation outside
  it is `unattested_citation`.
- **Citation gold-entry match** — share found in *this headword's* entry;
  corpus-attested but entry-absent citations are `citation_not_in_entry`.
- **Root–headword ok** — heuristic: normalised inferred root shares a 3-char
  window with the IAST headword; failure is `root_headword_mismatch`, listed as
  a candidate, not a proven error.

## Hallucination taxonomy

`unattested_citation` · `citation_not_in_entry` · `example_not_in_gold` ·
`root_headword_mismatch` · `empty_field` · `response_parse_failure`.
Each row in `hallucination_taxonomy.tsv` carries model, headword, category and
the generated string that triggered it (≥10 examples required by H6253).

## Canary — human act

`canary/mg_labels_template.tsv` holds the 5 held-out headwords. MG marks each
article's gloss / examples / citations correct (1) or incorrect (0) against the
Cologne entry. `articlegen_score.py --canary` then checks that the script's
binary verdicts reproduce ≥80% of those 30 decisions. With no labels the script
exits 2 with `INCONCLUSIVE`; a missing label is never silently read as 0-correct.

## Reproduce

```bash
python3 scripts/articlegen_build.py \
  --union ../SanskritLexicography/HeadwordLists/union/union_headwords.tsv \
  --mw ../csl-orig/v02/mw/mw.txt --out data/eval/articlegen
# generation: opencode run -m <model> --auto "$(cat prompts/batch_NN.txt)" > raw/<arm>_batch_NN.txt
python3 scripts/articlegen_score.py --self-test   # positive control vs mutated negative
python3 scripts/articlegen_score.py               # tables + taxonomy
python3 scripts/articlegen_score.py --canary      # MG labels required
```

## Premortem (landing to guarded kosha main)

- **Failure modes.** (1) model transcript parse drift silently drops headwords;
  `response_parse_failure` rows and explicit `missing` counts in the summary
  catch it. (2) Cologne gold mis-parsed; input sha256 and a manual spot-check of
  five `<L>` rows are the guard. (3) canary mistaken for machine-labeled;
  `--canary` refuses without MG's file. (4) large-repo worktree index hazard;
  worktree created off freshly fetched `origin/main` with a full-timeout build,
  verified clean before edits.
- **Early signals.** `n_main != 100` in the summary; any arm with
  `parse_failures > 0`; taxonomy count 0 across both arms; canary returning PASS
  while `mg_labels.tsv` is absent.
- **Points of no return.** PR merge to `origin/main` (revertable by a follow-up
  commit; the change is additive data + scripts + docs).

_Dr. Mārcis Gasūns_
