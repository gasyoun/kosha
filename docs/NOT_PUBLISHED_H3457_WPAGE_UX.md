# NOT PUBLISHED — H3457 word-page UX layer is STAGING ONLY

_Created: 25-08-2026 · Last updated: 25-08-2026_

**Status: staged, not live. A human decides when (and whether) this goes public.**
No session may flip it without that ruling — MG named the lane
"product-facing later" when opening it (24-08-2026).

## What is staged

The word-page UX layer built under
[H3457](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3457-Fable_kosha_wpage-ux-badge-favorites-scananchors_24.08.26.md)
(Fable 5 `claude-fable-5`): study badge from `core_rank` / `coverage_pct`,
localStorage favorites + favorites index page, print-scan anchors (PWG rebuilt
through the H839 volume-column key). Code:
[app/word_page_ux.py](https://github.com/gasyoun/kosha/blob/main/app/word_page_ux.py),
the `ux=` parameter of
[app/word_page.py](https://github.com/gasyoun/kosha/blob/main/app/word_page.py),
the `--ux-staging` flag of
[scripts/build_word_pages.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_word_pages.py).
Design packet + evidence:
[docs/H3457_WPAGE_UX_STAGING_PACKET_25.08.26.md](https://github.com/gasyoun/kosha/blob/main/docs/H3457_WPAGE_UX_STAGING_PACKET_25.08.26.md).

## What keeps it off the public surface

1. `render_word_page(card)` with no `ux` argument is **byte-identical** to the
   pre-H3457 output; the static prerender (`--coverage` / `--reading-packs`),
   the committed `w/` tree and the FastAPI SSR route all call it without `ux`.
   Locked by `tests/test_word_page_ux_staging.py::test_default_render_is_unchanged_by_the_ux_layer`.
2. `build_word_pages.py --ux-staging <variant>` writes only to
   `dist/w-staging/<variant>/` (gitignored) and **refuses** any output root
   under `docs/` (the Pages deploy input). Locked by
   `test_staging_build_refuses_docs`.
3. Nothing from this handoff was pushed to GitHub Pages, `gasyoun.github.io/kosha`,
   or samskrtam.ru.

## How a human flips it live (the one edit, when ruled)

1. Reply in chat with the variant to ship (`a` is the implemented winner; `b` /
   `c` are built alternatives — see the packet).
2. An agent then passes `ux={"variant": "<v>"}` in the two public call sites
   (`build_word_pages.build_word_pages` for the static tiers and the
   `GET /w/{slp1}` SSR route in `app/main.py`), regenerates the committed
   `w/` tree (`--reading-packs --force`) and the D4 head, refreshes the P5
   budget row in `docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md` §6, and deletes
   this marker in the same PR.

Until then: **do not** copy `dist/w-staging/` into `docs/`, do not commit it,
do not deploy it.

_Dr. Mārcis Gasūns_
