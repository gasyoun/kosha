# H3975 — isolating the `form_key()` 0.12.0 change from the 04-09-2026 `kosha.db` rebuild

_Created: 06-09-2026 · Last updated: 06-09-2026_

Evidence for the re-partition table in
[`CONCORDANCE_ROADMAP.md`](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md)
§ "The same defect one position inward". Executed by Claude Code Opus 5 (`claude-opus-5`).

## Why a control arm was needed

[FINDINGS §626](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md)'s own
rule: a merge-key fix is a **re-partition, not a monotone gain**, and it must not be quoted as
discovered data. Reporting it honestly needs both directions and a clean denominator.

The obvious comparison — the 02-09-2026 (H3925) figures against today's — is **confounded**.
`kosha.db` was itself rebuilt on 04-09-2026 (1,732.3 → 1,767.5 MB; `inflections` 6,917,018 →
6,930,902 rows, 3,326,312 → 3,333,034 distinct `form_slp1`), so any delta mixes a key change
with an input change. The attested side is clean — DCS's raw distinct values are identical
across both dates (381,413 sandhied surfaces / 303,859 unsandhied) — but the generated side is
not, and AG/G¬A are counted over it.

## Design

One factor, one level changed: **the same audit script, over the same `kosha.db` and the same
`dcs_full.sqlite`, with sanskrit-util pinned to 0.11.0 instead of 0.12.0.**

The control root is a directory of symlinks (`kosha` and `VisualDCS` → the real checkouts,
`sanskrit-util` → a 0.11.0 worktree), passed to the audit as `GITHUB_ROOT`. Treatment
artifacts are copied aside before the control run and restored after it, so the committed
outputs remain the treatment arm's.

Driver: `scratchpad/run_control_arm.sh` (session-local); both arms took ~420 s.

## The first run was invalid, and it looked like a null result

The control arm's first run produced numbers **byte-identical** to the treatment arm —
`AG 239,189 / G¬A 3,093,845 / A¬G 163,058`, and `AnG_keys_control.txt` compared equal to
`AnG_keys_treatment.txt`. That is not a null result; it is a broken manipulation.

Cause: `scripts/build_morphology_attestation_audit_inflections.py` resolves the library from
`GITHUB_ROOT` and does `sys.path.insert(0, …)` — but it imports `concordance_core` **first**,
and that module ran its own `sys.path.insert(0, <repo>/../sanskrit-util/py)` at import time,
landing on top. Both arms therefore loaded 0.12.0. The audit's own comment asserted the
opposite ("put on the path here FIRST and that stale-relative guess never fires"); it was
wrong about its own import order.

Fixed in this pass: `concordance_core.py` honours `GITHUB_ROOT`, and the audit's comment now
states the real ordering. The manipulation check is a one-liner and is now run before the
7-minute audit:

```
control  : form_key('saṃbhavaḥ') -> sanbhava   (0.11.0)
treatment: form_key('saṃbhavaḥ') -> sambhava   (0.12.0)
```

## Result — both directions

| | control — 0.11.0 | treatment — 0.12.0 | Δ |
|---|---:|---:|---:|
| distinct attested keys | 352,745 | **352,112** | −633 |
| **AG** (generated view) | 238,466 | **239,189** | **+723** |
| **G¬A** | 3,094,568 | **3,093,845** | −723 |
| **AG** (attested view) | 188,509 | **189,054** | +545 |
| **A¬G** | 164,236 | **163,058** | **−1,178 (−0.72%)** |
| attested-side coverage | 53.44% | **53.69%** | +0.25 pp |

Set diff of the two arms' A¬G key lists (`comm` over sorted `morph_attest_infl_AnG.tsv`
column 1):

- **left A¬G: 1,178**
- **entered A¬G: 0**

It reconciles without slack: 633 of the 1,178 leavers stopped being distinct keys at all —
they merged into their `m`-spelled twin, which *is* the denominator change — and 545 became
matched (188,509 → 189,054). 633 + 545 = 1,178.

Leavers are the expected shape: `abhisaṃbaddham`, `abhisaṃbandhaḥ`, `abhisaṃbodhana`,
`'ṃbhasi`, `saṃbhavaḥ` — every one an anusvāra directly before a labial.

## Why this fix is monotone and 0.11.0's was not

The word-final fix (0.11.0) **broke** 1,131 generated matches: folding final `-ṃ` onto `-m`
removed matches that had existed only because final `-ṃ` and final `-n` were conflated. There
was real contrast at that position — `rājan` vs `rājam` is two words.

At this position there is none. A loss would require an attested form spelled with a literal
`-nb-`, `-np-` or `-nm-` whose key stopped matching. Sanskrit orthography does not produce
those sequences: before a labial the nasal is written `m` or as anusvāra, never `n`. The
measured 0 entrants is what that phonology predicts — which is why the direction had to be
measured rather than assumed in either direction.

## Reproducing

1. `python scripts/rebuild_a3_chain.py --check` — asserts the six `form_key` invariants
   (both folds and their deliberate limits) without spending the ~55-minute rebuild.
2. `python scripts/measure_medial_anusvara_residual.py` — standing PASS/FAIL check; prints
   the medial-labial twin count against the recorded 02-09-2026 baseline (278 → 0, 90 → 0).
3. Control arm: point `GITHUB_ROOT` at a root whose `sanskrit-util` is a 0.11.0 checkout and
   re-run `scripts/build_morphology_attestation_audit_inflections.py`. **Probe
   `concordance_core.form_key('saṃbhavaḥ')` in that environment first** — if it returns
   `sambhava`, the pin did not take and the run is wasted.

Process lesson: [Uprava FINDINGS §715](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md).

_Dr. Mārcis Gasūns_
