# WSD fusion report (H1588)

_Created: 24-07-2026 · Last updated: 24-07-2026_

**Model:** Grok 4.5 (grok-4.5) · **Handoff:** H1588 (Opus-lock override)

## Gate

| Metric | Value |
|---|---|
| Method | `mfs` |
| Held-out accuracy | **0.8396** (threshold 0.7) |
| Gate pass | **YES** |
| Test scored | 71892 |
| Correct | 60362 |
| WordSem mapped (exact\|overlap) | 363694 |
| Degradation | single-witness MFS (SCL cache empty / H057 rights fail-closed) |

## SCL witness

| Field | Value |
|---|---|
| Labels in cache | 0 |
| Status | fail_closed |
| Reason | No rights-cleared SCL sense-label API (H057 outreach unresolved). Homepage probes recorded; zero labels written. Downstream WSD continues as single-witness (MFS/gloss-grounded arm). |

## Fusion

| Outcome | N |
|---|---|
| Promoted estimated lemma-rows | 13709 |
| Estimated tokens (sum count_all) | 4506310 |
| Review-queue rows | 0 |
| Attested rows retained | 103079 |
| Total sense_frequency rows | 116788 |

Review queue empty reason: empty because gate_pass and single-witness MFS: no SCL labels to disagree with

## Honesty

- Estimated counts are **MFS mass on untagged DCS tokens** (no WordSem), not blended into attested.
- Cards must show a separate estimated chip (W3d).
- SCL body text was never written to the tree (gitignore fence).

_Dr. Mārcis Gasūns_
