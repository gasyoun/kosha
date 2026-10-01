# H4730 report — classsplit verdict bank → zaliznyak oddball drills

_Created: 15-09-2026 · Last updated: 15-09-2026_

Executor: OxAlpha (`opencode/z-ai/glm-5.3-flash`) · Handoff: [H4730](https://github.com/gasyoun/Uprava/blob/main/handoffs/H4730-OxAlpha_SanskritGrammar_xwalk-c3-classsplit-zaliznyak-drills_14.09.26.md)

## What shipped

| Artifact | Path |
|---|---|
| Builder | [scripts/build_zaliznyak_oddbank_drills.py](../scripts/build_zaliznyak_oddbank_drills.py) |
| Drill bank (JSON) | [data/zaliznyak/zaliznyak_oddbank_drills.json](../data/zaliznyak/zaliznyak_oddbank_drills.json) |
| Flat fallback (TSV) | [data/zaliznyak/zaliznyak_oddbank_drills.tsv](../data/zaliznyak/zaliznyak_oddbank_drills.tsv) |
| Data statement | [docs/data-statements/zaliznyak-oddbank-drills.meta.md](data-statements/zaliznyak-oddbank-drills.meta.md) |
| Manifest row + consumer flip | [data/manifest/datasets.json](../data/manifest/datasets.json) (`zaliznyak-oddbank-drills`; consumers set on `dcs-nominal-class-split(-adj)`) |

## Census C3 closure

`dcs-nominal-class-split` (H3984) and `dcs-nominal-class-split-adj` (H4011)
had `"consumers": []`. This handoff makes them consumed: the new bank reads
both verdict files at build time and flips their `consumers` fields. The edge
(VisualDCS verdicts → kosha zaliznyak-oddbank-drills) is registered in
Uprava `interlinks_edges.tsv` + `PROJECT_INTERLINKS.md` in the same pass.

## Build result

```
source rows: 2159 (unresolved excluded from drills: 695)
  classify-verdict:dcs-nominal-class-split:one_lexeme_two_spellings: 191
  classify-verdict:dcs-nominal-class-split:at_only: 51
  classify-verdict:dcs-nominal-class-split:ant_only: 1
  classify-verdict:dcs-nominal-class-split-adj:one_lexeme_two_spellings: 1015
  classify-verdict:dcs-nominal-class-split-adj:at_only: 193
  classify-verdict:dcs-nominal-class-split-adj:ant_only: 13
  odd-one-out: (same oddball classes) total 258
items: 1722 -> data/zaliznyak/zaliznyak_oddbank_drills.json + .tsv
```

## Verification (evidence)

- `python3 scripts/build_zaliznyak_oddbank_drills.py --check` →
  `CHECK PASS: 1722 items, all verdict_refs re-resolve` — every drill item
  traces 1:1 to a verdict row (lemma_id + lemma + verdict must match the live
  source JSONs); odd-one-out carries exactly 4 refs and the oddball ref must
  BE the answer.
- Answer-position distribution across the 4 choices is rotation-balanced:
  64/65/65/64.
- Spot checks: bhagavant/bhagavat `classify-verdict` item present
  (`one_lexeme_two_spellings`, lemma_id 48483 — the pinned pair from H3984).

## Delivery

- **Changed:** new builder + bank + tsv + data statement; manifest row added;
  both producer rows' `consumers` flipped; changelog queue entry.
- **Unchanged:** the two VisualDCS verdict files (read-only, never vendored);
  the parent `zaliznyak-drills` dataset and its committed 3,434 items; all
  G2/paradigm totals upstream.
- **Checks:** `--check` PASS (above); build is deterministic (no RNG).
- **Risks:** verdict banks regen upstream could orphan refs — `--check` is
  the wired regression gate (build fails loud, never ships stale traces).
- **Inspect:** open `data/zaliznyak/zaliznyak_oddbank_drills.json`, pick any
  item, follow its `verdict_refs` into the VisualDCS JSON.

_Гасунс_
