# changelog_queue — A3 rebuilt on the narrowed medial-anusvāra fold (H3975), 06-09-2026

Consumed by cut_release.py at the next release cut (H3355 flow).

## [Unreleased] → Changed

- **H3975 (Opus 5 `claude-opus-5`) — the A3 chain is rebuilt on
  [sanskrit-util 0.12.0](https://github.com/sanskrit-lexicon/sanskrit-util/releases/tag/v0.12.0),
  which narrows `form_key()`'s medial anusvāra fold before a labial; the largest known
  defect in the morphology join is closed and the human review sheet no longer carries a
  single spelling twin.** *Homorganic* is a place of articulation, so anusvāra before
  `p ph b bh m` is phonetically /m/: under 0.11.0 `vaiśaṃpāyana` keyed as `vaiśanpāyana`
  and could never meet the `vaiśampāyanaḥ` the generator already emits. Measured on the one
  class that reaches a human, **278 of 2,521 `slot-conflict` rows (11.03%, 11.58% by corpus
  weight) were not disagreements at all** — `saṃbhavaḥ` vs `sambhavaḥ` — plus 90 candidates
  that collapse into their own lemma once refolded. After the rebuild both are **0**:
  slot-conflicts 2,521 → 2,212, coverage-holes 2,711 → 2,688, owed 5,232 → 4,900.
- **The re-partition is reported in both directions, against a same-inputs control arm —
  not against the 02-09-2026 figures.** `kosha.db` was itself rebuilt on 04-09-2026
  (1,732.3 → 1,767.5 MB; generated forms 3,326,312 → 3,333,034), so a raw before/after diff
  would quote an input change as a key effect. The control arm re-runs the identical audit
  over the identical inputs with a pinned 0.11.0 checkout, which isolates the key.
  Numbers and method: [`CONCORDANCE_ROADMAP.md`](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md)
  § "The join key was broken, and what fixing it moved".
- **`scripts/concordance_core.py` now honours `GITHUB_ROOT` when resolving sanskrit-util.**
  Its hard-coded `sys.path.insert(0, <repo>/../sanskrit-util/py)` ran at import time and
  silently outranked the path the caller had already put first, so the first control-arm run
  loaded 0.12.0 in both arms and produced numbers identical to the treatment. A controlled
  key-version A/B is impossible without this. The stale comment in
  `scripts/build_morphology_attestation_audit_inflections.py` claiming its own path entry
  wins is corrected to state the real ordering.
- **`scripts/rebuild_a3_chain.py` gained `--check` and enforces six `form_key` invariants**
  (both folds *and* their deliberate limits: final `-n` is not merged into final `-m`;
  `saṃvatsara` keeps `n` because `v` is not a labial stop; `saṃskṛta == sanskṛta`) before
  spending ~55 minutes, so no consumer can rebuild against a stale library checkout.
- **`scripts/measure_medial_anusvara_residual.py` is now a standing regression check**, not a
  one-shot measurement: it carries the recorded 02-09-2026 baseline (5,588 rows / 2,521
  conflicts / 278 twins / 90 lemma-twins), reports deltas and prints PASS/FAIL. It also had a
  dead `sys.path` entry (an extra `GitHub` segment) that silently measured site-packages
  instead of the sibling checkout — fixed. The screening banner on the validation sheet and
  the residual section of the triage report are now **measured in-run** rather than typed,
  and the sheet builder warns on stderr if the library carries the labial fold yet twins
  survive.

_Dr. Mārcis Gasūns_
