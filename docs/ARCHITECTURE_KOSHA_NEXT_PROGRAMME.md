# Architecture — kosha next programme

_Created: 24-07-2026 · Last updated: 24-07-2026_

Index: [PLAN_KOSHA_NEXT_PROGRAMME_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_NEXT_PROGRAMME_2026H2.md).

## 1. Prior-art / build-vs-reuse (mandatory)

| Piece | Verdict | Evidence |
|---|---|---|
| Panini KWIC viewer shell | **Reuse / extend** | [`concordance/panini/index.html`](https://github.com/gasyoun/kosha/blob/main/concordance/panini/index.html) + adhyāya shards from W2b; Q1 shell pattern in [`concordance/dict/`](https://github.com/gasyoun/kosha/blob/main/concordance/dict/) |
| Sūtra-coverage map data | **Consume** | [`sutra_coverage_map.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/sutra_coverage_map.tsv) (H1468) — never re-classify dark classes |
| Derivation chains | **Consume** | `derivation_status.tsv` / `paninian_concordance.tsv` |
| Sense frequency sidecar | **Extend** | [`sense_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/sense_frequency.tsv) + cards UI from H1453 |
| Sense corpus concordance | **Consume** | [`sense_corpus_concordance.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/) + pilot from H1455 |
| Word-page SSR/prerender | **Complete** | [`app/word_page.py`](https://github.com/gasyoun/kosha/blob/main/app/word_page.py), [`scripts/build_word_pages.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_word_pages.py), `GET /w/{slp1}` already present — W5 finishes head sizing + exit, not a greenfield |
| Drill HTML/JSON schema | **Reuse** | sandhi/morphology builders for H1461 |
| Corpus sandhi inducer | **Reuse** | `build_corpus_sandhi.py` for H1492 |
| DEFGEN protocol | **Reuse pattern** | [`DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md`](https://github.com/gasyoun/kosha/blob/main/docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md) for LLM WSD arm |
| Transcoding | **Vendor** | sibling `sanskrit-util` only — never hand-roll |
| form_key() joins | **House rule** | length-preserving; never NFD+strip |

**Do not rebuild:** WhitneyRoots roots explorer, SanskritKaraoke metre, csl-guides script quizzes, Samudra FTS corpus, DCS sqlite, pwg microstructure sense parse.

## 2. Wave-1 — panini surface (W4a)

**Components:**

1. **Coverage panel** — reads `sutra_coverage_map.tsv` (or a slim JS shard of it). Renders four statuses distinctly: `lit` · `dark-unattested` · `dark-out-of-scope` · `dark-engine-gap`. Collapsing dark classes into one bucket is **forbidden** (same honesty bar as W3a).
2. **Chain panel** — for a lit sūtra's exemplar form, resolve `chain_id` → ordered sūtra list (already in W2a/W2b artefacts).
3. **Trust block** — source artefact path, n, build date, link to `SUTRA_COVERAGE_BUILD_REPORT.md` / `PANINI_BUILD_REPORT.md`.
4. **CSV fallback** — download of the coverage map (house `/viz-page`).

**Host:** Pages interim (`gasyoun.github.io/kosha/concordance/panini/`); `PUBLIC_BASE` host-independent links (R1/R5).

## 3. Wave-2 — pilot cross-dict sense view

**Data model (pilot only):**

| column | source |
|---|---|
| `lemma_slp1` | pilot list from H1455 |
| `pwg_sense_id` + gloss snippet | `sense_corpus_concordance` / PWG loci map |
| `mw_sense_id` + gloss | kosha MW senses (read-only) |
| `apte_sense_id` + gloss | if available in RT extract; else `null` + honest gap |
| `locus_examples` | up to k from sense concordance |
| `confidence` | from W1 aligner |

**UI:** static page under `concordance/senses/` or `reading/` — side-by-side columns, not a new SPA framework. No MW reorder.

## 4. Wave-3 — two-witness WSD

```
WordSem gold (held-out) ──► acceptance metric (≥70%)
         ▲
untagged DCS tokens ──► LLM gloss-grounded arm ──┐
         │                                        ├─ fusion ─► estimated rows
         └──► SCL scrape ─► gitignored label cache ─┘
```

**SCL store (ruling N4):**

- Path: e.g. `data/frequency/.cache/scl_sense_labels.jsonl` — **gitignored**, listed in `.gitignore` same pass.
- Contents: minimal labels only (`lemma_slp1`, `scl_sense_id` or short label token, fetch timestamp) — **no** multi-sentence gloss dumps, no HTML.
- Manifest: do **not** register the cache as a public dataset; optional `restricted` intermediate row only if needed for agent discovery, still non-release.
- Publish-safety: estimated counts may publish; SCL cache never ships in a release asset.

**LLM arm:** prompt grounded in MW gloss list for the lemma; temperature 0; reuse DEFGEN scoring harness where possible.

**Fusion:** agree → `estimated` with both witnesses; disagree → flag `review` or drop from estimated (marked default: **drop from estimated, keep in review queue TSV**).

## 5. Wave-4 — P-D5 kosha.db layers

**Pattern:** same as frequency LEFT JOIN on lemmas — additive tables, never destructive rebuild of core entries.

Candidate public layers (confirm per-row rights at implement time from `datasets.json`):

- lemma / sense frequency sidecars (if not already joined)
- dict-corpus concordance summary counts
- roots frequency
- uttarapada pointer metadata (pointer datasets stay pointers — do not copy VisualDCS bulk)

Restricted-tier rows: **local attach only**, never in public API without rights clearance.

## 6. Wave-5 — static head + SSR tail

Standing rules **D4/D5** from Concordance plan:

- Static head **N = 11,148** lemmas = 95% of DCS token mass (from `lemma_frequency.tsv`).
- SSR tail: `GET /w/{slp1}` via FastAPI on samskrtam.ru (assumed near-term).
- Prerender builder already exists; W5 sizes the head, verifies budget, runs exit checks.
- Pages soft cap ~1 GB — re-measure and **append** (never overwrite) the budget log with date + tier.

## 7. Interfaces / contracts

| Contract | Owner |
|---|---|
| Manifest row for every new public dataset | `data/manifest/datasets.json` |
| Data-statement meta | `docs/data-statements/*.meta.md` |
| Sense sidecars never mutate MW | H1453/H1455 fence |
| Host-independent citations | `PUBLIC_BASE` / `app/cite.py` |
| Worktree-only commits | `.githooks/pre-commit` main-tree guard |

---

_Dr. Mārcis Gasūns_
