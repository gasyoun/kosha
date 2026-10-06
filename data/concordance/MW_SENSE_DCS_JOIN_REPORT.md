# MW senses × DCS citations — full-volume join (H6066)

_Created: 06-10-2026 · Builder: [scripts/build_mw_sense_dcs_join.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_mw_sense_dcs_join.py) · Executor: GLM 5.3 (opencode/zai-coding-plan/glm-5.3)_

Full-volume join of the **MW sense inventory** (kosha.db `entries`/`senses`, dict='mw': 286,525 entries → **303,023 numbered senses**) against **DCS corpus citations**, per the `sense-corpus-join` skill (`per-sense-freq` axis, full volume). Outputs:

- [`mw_sense_dcs_join.tsv.gz`](mw_sense_dcs_join.tsv.gz) — one row per MW sense (303,023 rows, 18 cols); `dict_only` rows keep empty corpus columns
- [`mw_sense_dcs_join_corpus_only.tsv`](mw_sense_dcs_join_corpus_only.tsv) — 26,120 DCS lemmas with no MW headword
- [`mw_sense_dcs_observatory_feed.json`](mw_sense_dcs_observatory_feed.json) — dashboard feed for csl-observatory (H6071)
- [`mw_sense_dcs_join.meta.json`](mw_sense_dcs_join.meta.json) — pins, key, denominators, n

## Join key and tiers

Key: **SLP1** (sanskrit-util normalised on both sides by the source builders; MW `slp1_key` ↔ `lemma_frequency.lemma_slp1`). Sense ordinal = 1-based printed order within an slp1_key group, ordered by `(CAST(L AS INTEGER), sense_n)` — the **identical convention** `build_wn_mw_map.py` established for `sense_id=<lemma>#<mw_ord>` (H1453), so WordSem per-sense counts land on the correct sense by construction.

| tier | meaning |
|---|---|
| `dcs_match=lemma` | headword-level DCS citation aggregates (count/rank/grammar/periods_sum from the committed lemma-frequency sidecar) — a **lower bound attributed to every sense** of an attested headword |
| `ws_count` (ws_prov=attested) | WordSem per-sense ATTESTED counts (23,088 senses, gold via H1453) |
| `mfs_est=1` | estimated most-frequent-sense flag for untagged lemmas (13,709 senses, H1588) — a flag, never a count |
| `dcs_match=dict_only` | senses of headwords with no DCS attestation — kept as rows |

## Both denominators (skill Phase 3)

| denominator | value |
|---|---|
| senses with attested headword / all MW senses | **143,428 / 303,023 = 47.33%** |
| senses with WordSem per-sense attestation / all MW senses | **23,088 / 303,023 = 7.62%** |
| DCS lemmas matching ≥1 MW headword / DCS lemmas | **57,157 / 83,277 = 68.63%** |

## Residues (first-class, never dropped)

| residue | n |
|---|---|
| `dict_only` senses (headword unattested in DCS) | 159,595 |
| corpus_only DCS lemmas (no MW headword) | 26,120 (sidecar TSV) |
| senses on homonym-collision keys (`n_entries_key`>1) | 136,092 — **declared, not resolved**: corpus lemmas cannot split MW homonyms; conflict adjudication stays a human/judgment call (skill gate) |
| MW entries without numbered senses | 0 |

Direction-A caveat (FINDINGS §86): the 159,595 corpus-unattested senses are **not** "ghost senses" by default — the corpus is lacunar (WordSem tags only a subset; sandhi-hidden forms and untagged stems remain).

## Validation sample (skill Phase 4, seed 6066, recomputable)

`python scripts/build_mw_sense_dcs_join.py --validate` — 50 attested senses, evidence re-queried from `dcs_full.sqlite` / `wn_to_mw_map.tsv` (NOT from the sidecars the build read):

| check | result |
|---|---|
| link (joined lemma present in DCS) | **0/50 fail** |
| ws per-sense count re-derivation from wn_to_mw_map | **0/5 fail** |
| lemma count vs raw dcs_full-2026 tokens, ±5% | 24/50 within · 26/50 sidecar **below** · 0 above |

The count cross-check shows the committed sidecar (source: M9 `archive.sqlite` period_freq, Leonchenko aggregate) is a **strict lower bound** against the fresher dcs_full-2026 snapshot (5,688,416 tokens) — it never exceeds it in the sample. `dcs_count_all` therefore reads as a conservative citation count; consumers wanting the 2026-snapshot count must re-derive from `dcs-full-sqlite` (pins in meta.json).

Declared encoding asymmetry: `dcs_full.lemma` is IAST (lowercased), sidecars are SLP1; SLP1 capitals are phonemes (B=bh, D=dh), so the validation probe transcodes IAST→SLP1 with canonical sanskrit-util and matches exactly — never casefold (casefolding corrupts SLP1).

## Prior art consumed, not rebuilt (Phase 0)

`kosha-sense-frequency` (sense_frequency.tsv, H1453/H1459/H1588) · `kosha-lemma-frequency` (lemma_frequency.tsv) · kosha.db MW entries/senses (senses spans via wn_to_mw_map's slicing contract) · `dcs-full-sqlite` (validation probe only). This join EXTENDS the sense-corpus programme from the H1455 pilot (500 PWG headwords, dictionary-own `<ls>`) to the full MW inventory on the corpus side; it does not duplicate any existing pair.

## Observatory feed

`mw_sense_dcs_observatory_feed.json`: machine-readable metrics block (both denominators, residues, tier semantics) + top-50 WordSem-attested senses — consumable by csl-observatory research dashboards (H6071).

_Dr. Mārcis Gasūns_
