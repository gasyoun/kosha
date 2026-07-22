# IMPLEMENTATION — kosha sense-frequency, wave-1 (file-level, step-ordered)

_Created: 22-07-2026 · Last updated: 22-07-2026_

Index: [PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md) ·
Architecture: [ARCHITECTURE_KOSHA_SENSE_FREQUENCY.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_SENSE_FREQUENCY.md).

Environment: guarded repo → **work in a worktree off `origin/main`**. All scripts follow the Windows/encoding
rules (`sys.stdout.reconfigure(encoding='utf-8')`; `encoding='utf-8'` on output-capturing `subprocess`;
no UTF-8 BOM; multi-step logic in `.py` files, not inline shell).

---

### Step 0 — Locate the inputs (no writes)

- Confirm the DCS **CoNLL-U releases** path on disk (the `WordSem` MISC-key source). Start from
  VisualDCS `derived-data/Corpus-Delta-2021-2026/` and
  [`annotation_layers_by_text.csv`](https://github.com/gasyoun/VisualDCS/blob/main/derived-data/Corpus-Delta-2021-2026/annotation_layers_by_text.csv)
  (per-text WordSem token counts — tells you which 219 texts to read).
- Confirm kosha `senses` table location + schema (`sense_id`, `lemma`/`slp1` join, sense order column).
- Locate the [`semdom-amarakosha-crosswalk`](https://github.com/gasyoun/Uprava/blob/main/REUSE_INDEX.md)
  asset in SanskritLexicography and the MW→WordNet bridge (FEATURES_INDEX C19).
- **Ambiguity default:** if the CoNLL-U releases are not on disk, attempt the recovery from the
  public DCS release URLs; if still unavailable, LOG and proceed to Steps 2–3 scaffolding, park Step 1.

### Step 1 — `build_wordsem_inventory.py` → `wordsem_inventory.tsv`

- Parse the WordSem MISC key across the 219 tagged CoNLL-U texts; collect the distinct synset ids and,
  from the release's WordNet side (or the DCS `lemma.meanings` gloss where the synset resolves to a lemma),
  emit `synset_id → gloss → wn_lemma`.
- Acceptance: row count > the 9.3%-sqlite decode count; every synset id seen in the corpus is present or
  logged as un-decodable. Depends on: Step 0.

### Step 2 — `build_wn_mw_map.py` → `wn_to_mw_map.tsv`

- For each synset, match to kosha `senses` via the MW→WordNet bridge; where the bridge is silent, fall
  back to lemma+gloss-overlap scoring; tag `match_type` (`exact` / `overlap` / `unresolved`).
- Never write into `senses` — output is a standalone map. Depends on: Step 1.

### Step 3 — `build_sense_frequency_layer.py` → `sense_frequency.tsv` + `.meta.json`

- Stream WordSem-tagged tokens; per token, increment counts for the WN synset (Layer 1) and, via the two
  maps, the MW sense (Layer 2) and semdom domain (Layer 3). Bucket by DCS period for the `periods` vector.
- Compute `sense_rank` and `lemma_share` per lemma per layer. Set `provenance=attested`, `confidence=null`.
- Write `.meta.json` mirroring `lemma_frequency.meta.json` (generator, source, join_key, period_order,
  rows, per-layer coverage counts, the WordSem 219/270 caveat, the aorist/perfect caveat).
- Acceptance: see [VERIFICATION](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_SENSE_FREQUENCY.md).
  Depends on: Steps 1–2.

### Step 4 — `build_sense_order_delta.py` → `dcs_mw_sense_order_delta.md`

- For each lemma, compare frequency-dominant MW sense (`sense_rank=1` in the `mw` layer) against MW's
  canonical sense-1 (from `senses` order). Emit the mismatches as a finding table.
- **Fence:** report only — do not touch `senses`. Frame as a *DCS-derivation* finding, not an MW defect.
  Depends on: Step 3. Feeds M01 Ch6.

### Step 5 — manifest + data-statement

- Add `kosha-sense-frequency` row to
  [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  (tier=public, source_path, release_asset, LEFT-JOIN note, data_statement link).
- Write `docs/data-statements/kosha-sense-frequency.meta.md` (mirror the lemma-frequency data-statement).

### Step 6 — kosha-cards UI ("N in this sense · M for the lemma")

- Find the existing card build site that LEFT-JOINs `lemma_frequency` (grep the card templates/build for
  `lemma_frequency`); add a symmetric LEFT-JOIN of `sense_frequency` (mw layer) keyed by lemma+sense.
- Render per sense: `N in this sense · M for the lemma` with `lemma_share` as a bar. Add the **two-tier
  badge** scaffold: an `attested` chip (populated) and an `estimated` chip (empty in wave-1, present so
  wave-2 lights it up). Never blend the two into one number.
- Verify in the browser preview per the verification workflow. Depends on: Step 3.

### Step 7 — commit → PR → merge, update hubs

- Commit per logical step (`ai-wip:` micro-commits allowed). Push the worktree branch, open a PR,
  auto-merge + delete branch.
- Post-work hub sweep (`/artifact-propagate`): manifest row (done in Step 5); flip the H1453 registry row;
  add the sense-order finding to GTD (@DECIDE: register as a paper?); update kosha `.ai_state.md`.
- Remove the worktree the same pass.

---

## Dependency order

`Step 0 → Step 1 → Step 2 → Step 3 → {Step 4, Step 5, Step 6} → Step 7`. Steps 4/5/6 are independent of
each other once Step 3 lands.

_Dr. Mārcis Gasūns_
