# Roadmap — kosha RU language groups and ops leftovers (finished)

_Created: 13-08-2026 · Last updated: 01-09-2026_

> **Truth-pass 01-09-2026** (Sonnet 5 `claude-sonnet-5`, [H3787](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3787-Sonnet_kosha_ru-lang-groups-ops-residual_31.08.26.md)). All five wave handoffs below are ✅ shipped and merged; the [Salt-face residual](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2768-Codex_kosha_salt-face-kosha-extension-contract_14.08.26.md) named in [PR #399](https://github.com/gasyoun/kosha/pull/399) is also ✅ shipped. No open wave, no open `/ask` fork (all 24 ruled). Kept in place, not archived ([FINDINGS §475](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md) clause 3, MG 31-08-2026 ruling: a drained kosha roadmap keeps its path and gets a dated banner in place).

Companion to
[PLAN_KOSHA_RU_LANG_GROUPS_OPS_2026.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_RU_LANG_GROUPS_OPS_2026.md).

## Waves — all shipped

| Wave | Deliverable | Unblocks | Handoff | Status |
|---|---|---|---|---|
| W-RU-1 | Two-level EN/DE/RU chrome; pwg_ru + mw_ru via sibling join; All still stacks all languages; locale EN unless `ru` | SanskritRussian strip | H2670 | ✅ [PR #393](https://github.com/gasyoun/kosha/pull/393) merged |
| W-RU-2 | One-line SanskritRussian glossary strip on `/w/` | — | H2680, after H2670 on main | ✅ [PR #395](https://github.com/gasyoun/kosha/pull/395) merged |
| W-OPS-A | Snapshot live `0.1.0-dev` under `/opt/kosha/archive`; `/ready` configured; one pinned sense 200 | — | H2671 | ✅ [PR #391](https://github.com/gasyoun/kosha/pull/391) merged |
| W-OPS-B | Live Part IV restore, smoke, immediate re-promote | — | H2672 | ✅ [PR #394](https://github.com/gasyoun/kosha/pull/394) merged |
| W-W0 | Compare memo of H1944 and H1945 + review comments on those PRs | follow-on only if a defect is named | H2681 | ✅ [PR #399](https://github.com/gasyoun/kosha/pull/399) merged |

W-RU-1 is first among product work. W-OPS-A, W-OPS-B, and W-W0 are independent
of W-RU-1 and of each other.

## Non-goals

- Kochergina 1987
- Extra Cologne dictionaries (PW, MW 1872, Grassmann)
- Vendoring the full pwg_ru/mw_ru stores into kosha
- Declaring Wave 1 product-exit complete
- Re-deriving H1944/H1945 code in the Codex session

_Dr. Mārcis Gasūns_
