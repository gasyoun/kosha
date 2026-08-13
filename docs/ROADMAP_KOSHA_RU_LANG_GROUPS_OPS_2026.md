# Roadmap — kosha RU language groups and ops leftovers

_Created: 13-08-2026 · Last updated: 13-08-2026_

Companion to
[PLAN_KOSHA_RU_LANG_GROUPS_OPS_2026.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_RU_LANG_GROUPS_OPS_2026.md).

## Waves

| Wave | Deliverable | Unblocks | Handoff |
|---|---|---|---|
| W-RU-1 | Two-level EN/DE/RU chrome; pwg_ru + mw_ru via sibling join; All still stacks all languages; locale EN unless `ru` | SanskritRussian strip | H2670 |
| W-RU-2 | One-line SanskritRussian glossary strip on `/w/` | — | H2680, after H2670 on main |
| W-OPS-A | Snapshot live `0.1.0-dev` under `/opt/kosha/archive`; `/ready` configured; one pinned sense 200 | — | H2671 |
| W-OPS-B | Live Part IV restore, smoke, immediate re-promote | — | H2672 |
| W-W0 | Compare memo of H1944 and H1945 + review comments on those PRs | follow-on only if a defect is named | H2681 |

W-RU-1 is first among product work. W-OPS-A, W-OPS-B, and W-W0 are independent
of W-RU-1 and of each other.

## Non-goals

- Kochergina 1987
- Extra Cologne dictionaries (PW, MW 1872, Grassmann)
- Vendoring the full pwg_ru/mw_ru stores into kosha
- Declaring Wave 1 product-exit complete
- Re-deriving H1944/H1945 code in the Codex session

_Dr. Mārcis Gasūns_
