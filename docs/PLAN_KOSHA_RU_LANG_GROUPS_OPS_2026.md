# Plan — kosha Russian language groups, archives, rollback, W0 memo

_Created: 13-08-2026 · Last updated: 13-08-2026_

Index for the 13-08-2026 `/ask` sitting. A fresh agent executes the named
handoffs; this file is the decision record.

| Doc | What it answers |
|---|---|
| [ROADMAP_KOSHA_RU_LANG_GROUPS_OPS_2026.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_RU_LANG_GROUPS_OPS_2026.md) | Wave order and non-goals |
| [ARCHITECTURE_KOSHA_RU_LANG_GROUPS.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_RU_LANG_GROUPS.md) | Language chrome, sibling join, All tab |
| [IMPLEMENTATION_KOSHA_RU_LANG_GROUPS.md](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_RU_LANG_GROUPS.md) | File-level build order for H2670 |
| [VERIFICATION_KOSHA_RU_LANG_GROUPS.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_RU_LANG_GROUPS.md) | Proof commands and stop conditions |
| [PLAN_KOSHA_RU_LANG_GROUPS_OPS_2026.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_RU_LANG_GROUPS_OPS_2026.meta.md) | Provenance |

This plan does **not** replace
[PLAN_KOSHA_ARCHITECTURE_ROADMAP_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_ARCHITECTURE_ROADMAP_2026_2027.md).
It is a slice: Russian on `/w/`, two ops leftovers, one W0 memo.

## Decisions taken (interview 13-08-2026)

| # | Decision | Vote |
|---|---|---|
| R1 | First RU ship = all public RU layers, **sequenced** | pwg_ru + mw_ru tabs first; SanskritRussian strip after |
| R2 | Extra handoffs this sitting | Archives + rollback + W0 Codex review (not more Cologne dicts) |
| R3 | Archives done | Mount + one pinned version |
| R4 | Rollback done | Live Part IV restore on `.92` |
| R5 | P6 G5 wait | **Override:** ship labeled AI-translated. No Kochergina |
| R6 | Data path | Runtime join from sibling `RussianTranslation`; CI fixture |
| R7 | Chrome | Language groups **EN / DE / RU**, then dicts inside |
| R8 | SanskritRussian strip | Mint child now; execute after H2670 merges; Grok 4.6 |
| R9 | W0 review | Written compare memo **plus** GitHub review comments on the PRs |
| R10 | Archive pin | Snapshot live `0.1.0-dev` |
| R11 | Rollback window | Restore, smoke, re-promote **immediately** |
| R12 | Chrome detail | Two-level: EN/DE/RU then inner dicts |
| R13 | First paint | EN unless `Accept-Language` / `navigator.language` is `ru` |
| R14 | Prod sibling | Clone next to `/opt/kosha/repo` if missing |
| R15 | All tab | Still stacks **every** dict, all languages (H2653 kept) |
| R16 | RU proof | Pytest + live `/w/BU` after deploy |
| R17 | Locale proof | SSR header + JS `navigator.language` |
| R18 | Archive smoke | `/ready` configured + one pinned sense 200 |
| R19 | Rollback smoke | `/health` + `/ready` after restore **and** after re-promote |
| R20 | On ambiguity | Marked default + log |
| R21 | Halt | Live unit down or data-wipe risk; pytest red after 5 tries |
| R22 | Authority | PR → merge → deploy `.92` |
| R23 | Fence | No `csl-orig`, no rewrite of pwg_ru/mw_ru stores, no Kochergina, no `.95` |
| R24 | This sitting | Plan + handoffs only; **do not start H2670 here** |

## Autonomy contract (verbatim)

- **On unplanned ambiguity:** apply the marked default in the layer docs, log
  one line in the PR body, continue.
- **Stop:** `kosha.service` down after a restore attempt; any path that would
  drop `/opt/kosha/db/kosha.db`; pytest still red after five genuine tries.
- **Commit:** worktree off `origin/main`, PR, merge (`gasyoun/*`), deploy the
  known `.92` recipe when the change is user-visible.
- **Fence:** do not edit `csl-orig`; do not rewrite pwg_ru/mw_ru canonical
  cards; do not add Kochergina; do not SSH `.95`; do not claim Wave 1 complete.

## Handoffs

| ID | Role |
|---|---|
| [H2670](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2670-Grok_kosha_w-page-ru-pwg-mw-tabs_13.08.26.md) | Language groups + pwg_ru/mw_ru join |
| [H2680](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2680-Grok_kosha_w-page-sanskritrussian-strip_13.08.26.md) | SanskritRussian strip after H2670 |
| [H2671](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2671-Grok_kosha_citation-archive-mount_13.08.26.md) | Archive snapshot + pin |
| [H2672](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2672-Grok_kosha_identity-rollback-drill_13.08.26.md) | Live rollback drill |
| [H2681](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2681-Codex_kosha_w0-h1944-h1945-compare-memo_13.08.26.md) | W0 memo + PR comments |

## Autonomy-readiness gate

**PASS.** Every wave-1 deliverable has architecture, steps, acceptance, and
risks. No blocking `@DECIDE`. Prior-art is join-not-rebuild. Ambiguity policy
is R20.

_Dr. Mārcis Gasūns_
