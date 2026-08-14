# Implementation — kosha `/w/` language groups (H2670)

_Created: 13-08-2026 · Last updated: 13-08-2026_

Worktree off `origin/main`. Do not edit the guarded main checkout.

1. Add a small committed fixture under `tests/fixtures/ru_join/` with one
   pwg_ru row and one mw_ru row for a known lemma (e.g. `BU` or `banD`).
2. Write `src/kosha/api/ru_join.py` (or `app/ru_join.py` if that matches
   current shims): resolve sibling path, return `{pwg_ru, mw_ru}` or
   missing. No write into the store.
3. Extend `app/word_page.py`: language row, inner dict row, All still
   stacks all. Locale: request header on SSR; `navigator.language` in
   existing page JS.
4. Wire the join into `GET /w/{slp1}` in `app/main.py` so SSR sees live
   sibling data when present.
5. Tests in `tests/test_word_page.py` (and a new
   `tests/test_word_page_lang_groups.py`): chrome, All still complete,
   empty-state, AI-translated badge, `Accept-Language: ru` default.
6. CHANGELOG Unreleased bullet; PR; merge; deploy `.92` (clone sibling if
   missing); smoke `https://samskrtam.ru/w/BU`.
7. **Stop.** Do not start the SanskritRussian strip in this PR.

W-RU-2 is [H2680](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2680-Grok_kosha_w-page-sanskritrussian-strip_13.08.26.md).
H2671, H2672, and
[H2681](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2681-Codex_kosha_w0-h1944-h1945-compare-memo_13.08.26.md)
are separate handoffs.

_Dr. Mārcis Gasūns_
