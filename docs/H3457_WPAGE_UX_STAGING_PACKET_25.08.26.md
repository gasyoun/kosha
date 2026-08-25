# H3457 — word-page UX upgrade, staged: design packet + evidence

_Created: 25-08-2026 · Last updated: 25-08-2026_

Handoff: [H3457 (Fable 5) — w-page UX upgrade staged: core_rank badge, favorites, PWG scan anchors](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3457-Fable_kosha_wpage-ux-badge-favorites-scananchors_24.08.26.md)
· executor Fable 5 (`claude-fable-5`) · lane C of 3 (MG go 24-08-2026).
**Status: STAGED, NOT PUBLISHED** —
[docs/NOT_PUBLISHED_H3457_WPAGE_UX.md](https://github.com/gasyoun/kosha/blob/main/docs/NOT_PUBLISHED_H3457_WPAGE_UX.md).

## 1. What was asked, what shipped

| # | Feature (ruling 24-08-2026) | Shipped as | Where |
|---|---|---|---|
| 1 | Frequency/study badge from `lemma_frequency.tsv` `core_rank` + `coverage_pct` | `study_badge()` — three rungs cut on the raw rank (≤500 *core · learn first* · ≤2000 *core · second circle* · else *core vocabulary*), rank number always shown, tooltip carries coverage weight + source; **no badge** when the lemma is outside the 7,120-lemma ordering | [app/word_page_ux.py](https://github.com/gasyoun/kosha/blob/main/app/word_page_ux.py) |
| 2 | Favorites, client-side, static-site friendly, index page | `♡` button hydrated by JS, `localStorage['kosha_favorites']`, static `favorites.html` (list + TSV / Anki export + clear), footer link with live count | same + `favorites_page_html()` |
| 3 | Entry → print-scan anchors, PWG first via the scan-index machinery (H839 precedent) | stable `id="e-{dict}-{L}"` per entry + `#` permalink; PWG link **rebuilt through the H839 `{vol}-{col:04d}` key** from the new committed table [data/pwg_scan/pwg_L_pc.tsv](https://github.com/gasyoun/kosha/blob/main/data/pwg_scan/pwg_L_pc.tsv) (122,730 L rows from csl-orig `<pc>`), labelled `PWG 7, 1737 ↗`; MW / Apte labelled `MW p. 346 ↗` (single-volume) | same + [scripts/build_pwg_scan_anchors.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_pwg_scan_anchors.py) |
| 4 | Error-report widget | **PARKED** (needs a backend) — not built, as ruled | — |

**Why #3 is a bug fix and not only a label.** Every one of the 48,540 PWG
`scan_url`s in the committed `docs/cards/` set is bare-page (they predate
H839), and Cologne's `servepdf.php` serves **volume 1** for a bare column —
`gam` (L 119742, printed at 7-1737) linked to 1-1737. The static tier has no
`kosha.db` to regenerate cards from, so the volume now lives in a committed
sidecar and is folded in at render time (registered in
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
as `pwg-print-anchors`). MW-side print anchors (the Cologne scan-index
campaign) stay a later wave.

## 2. Design directions (Phase 1 — our own theme, not an akshara clone)

Contract: the existing P5 word-page theme
([P5_ADVANCED_UI_DESIGN.md](https://github.com/gasyoun/kosha/blob/main/P5_ADVANCED_UI_DESIGN.md);
tokens in `app/word_page.py::PAGE_CSS` — system-ui, accent `#7b2d26` / dark
`#e0a44a`, band chips, `.chip` family). akshara.ru was the *feature* reference
only (badge · favorites · scan links); no visual element was copied. Every
direction is the **real template + one variant's CSS/markup** over the real
`gam` card (MW ×3, PWG ×4, Apte ×1, core_rank 7), self-contained, no external
requests, light + dark, 375 / 1280 — built by
[scripts/build_wpage_ux_mockups.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_wpage_ux_mockups.py)
into [mockups/h3457-wpage-ux/](https://github.com/gasyoun/kosha/tree/main/mockups/h3457-wpage-ux)
(12 screenshots under `shots/`, 0 console errors each).

Axis: **where the study affordances live relative to the reading column.**

| Dir | Name | What it does | Screens |
|---|---|---|---|
| **a** | inline strip | badge beside the band chip, heart at the strip's right edge; print anchor in each entry head next to the headword | [light 1280](https://github.com/gasyoun/kosha/blob/main/mockups/h3457-wpage-ux/shots/a-light-1280.png) · [dark 375](https://github.com/gasyoun/kosha/blob/main/mockups/h3457-wpage-ux/shots/a-dark-375.png) |
| b | study rail | a sticky right rail (≥900 px) / stacked card (mobile) with the badge explained, the heart, and an *In print* list of every entry's anchor; entry heads stay light | [light 1280](https://github.com/gasyoun/kosha/blob/main/mockups/h3457-wpage-ux/shots/b-light-1280.png) · [dark 375](https://github.com/gasyoun/kosha/blob/main/mockups/h3457-wpage-ux/shots/b-dark-375.png) |
| c | margin marks | editorial: small-caps rank line under the headword, text-link `☆ save`, column marks `[PWG 7, 1737]` right-aligned like an apparatus | [light 1280](https://github.com/gasyoun/kosha/blob/main/mockups/h3457-wpage-ux/shots/c-light-1280.png) · [dark 375](https://github.com/gasyoun/kosha/blob/main/mockups/h3457-wpage-ux/shots/c-dark-375.png) |

### Winner: **a — inline strip** (implemented in the staging build)

1. **Reading first.** The word page's primary job is lookup; **b** costs the
   entire first 375-px viewport before the first gloss (measured on the dark-375
   shot), which is the wrong trade for a dictionary.
2. **Same semantic row.** The badge sits beside the existing `band 1` chip —
   both are frequency facts — so it reads as one family, not a new widget.
3. **Anchor where the citation is.** `PWG 7, 1737 ↗` beside the entry's own
   headword tells the reader which entry a scan belongs to; b's rail list
   loses that adjacency once a lemma has eight entries.
4. **c** is the most elegant, but `☆ save` as small-caps text has the lowest
   affordance of the three for a learner feature, and the extra rank line
   pushes the SanskritRussian gloss down on mobile.

Grafted from **b** into a: nothing structural — the explainer sentence lives in
the badge tooltip. **b** and **c** stay buildable
(`--ux-staging b|c`) if a human rules differently; reversing the choice is one
flag.

## 3. Staging build (Phase 2)

```
python scripts/build_pwg_scan_anchors.py                      # once; ../csl-orig
python scripts/build_word_pages.py --ux-staging a --tokens kf,gam,vac,as,deva,Darma,agni,rAma,jana,nf,yA
python scripts/smoke_wpage_ux.py --variant a --log docs/H3457_WPAGE_UX_SMOKE_LOG_25.08.26.md
python scripts/spotcheck_wpage_ux.py --variant a
```

Output tree (gitignored `dist/`, local-only):

```
dist/w-staging/a/
├── NOT_PUBLISHED.md
├── favorites.html
└── w/  Darma.html agni.html as.html deva.html gam.html jana.html kf.html nf.html rAma.html vac.html yA.html
```

11 pages, 1.21 MB, mean 107.6 KB/page (`build_word_pages.py` META). `BU` was
in the sample list but has no committed card (SSR long tail) — honest miss,
not a failure. Cache-bust: the pages carry `<meta name="data-version">` from
the card as before; the layer adds no fetched asset, so nothing to bust.

Guard rails: `render_word_page(card)` with no `ux` is **byte-identical** to the
pre-H3457 output (test `test_default_render_is_unchanged_by_the_ux_layer`);
`--ux-staging` refuses any output root under `docs/`
(`test_staging_build_refuses_docs`). The public D4 head, the committed `w/`
tree and the SSR route are untouched.

## 4. Evidence

### 4.1 Playwright smoke — PASS 22/22

[docs/H3457_WPAGE_UX_SMOKE_LOG_25.08.26.md](https://github.com/gasyoun/kosha/blob/main/docs/H3457_WPAGE_UX_SMOKE_LOG_25.08.26.md):
11 pages × {375, 1280} px, Chromium headless over `file://`, 12.2 s. Per row:
0 console/page errors; badge present iff the TSV has a `core_rank`, with
`data-core-rank`/`data-coverage` byte-equal to the TSV; every PWG anchor
carries the vol-col key; favorite click → `aria-pressed=true` → **reload →
still true** → listed on `favorites.html` (n=1) → un-favorite → false.
Verb roots in the sample: `kf`, `gam`, `vac`, `as`, `yA`.

### 4.2 Badge rank / coverage vs `lemma_frequency.tsv` — 11/11 byte-match

| token | TSV core_rank | TSV coverage_pct | page data-core-rank | page data-coverage | match |
|---|---:|---|---:|---|---|
| `agni` | 17 | 0.290706 | 17 | 0.290706 | ✅ |
| `as` | 5 | 0.73065 | 5 | 0.73065 | ✅ |
| `Darma` | 12 | 0.346062 | 12 | 0.346062 | ✅ |
| `deva` | 4668 | 0.00273034 | 4668 | 0.00273034 | ✅ |
| `gam` | 7 | 0.478229 | 7 | 0.478229 | ✅ |
| `jana` | 83 | 0.105583 | 83 | 0.105583 | ✅ |
| `kf` | 1 | 0.991412 | 1 | 0.991412 | ✅ |
| `nf` | 354 | 0.0452156 | 354 | 0.0452156 | ✅ |
| `rAma` | 81 | 0.108463 | 81 | 0.108463 | ✅ |
| `vac` | 2 | 0.929154 | 2 | 0.929154 | ✅ |
| `yA` | 7208 | 0.000630077 | 7208 | 0.000630077 | ✅ |

First run had 3 misses (`Darma`, `rAma`, `yA`): the cards case-fold
`query.key` (`"darma"`), so the lookup now keys on the token-decoded SLP1.
That same case-folding makes the **public** page render `Darma` as दर्म —
pre-existing, out of scope, filed as
[kosha#433](https://github.com/gasyoun/kosha/issues/433).

### 4.3 Print anchors — 45 distinct hrefs on the 11 pages; PWG 24/24 carry the vol-col key

Live check, 25-08-2026 08:30–08:40. Local `GET` on the raw links returned
**429** on all 10 tries (12 s spacing) — the per-IP throttle already on the
board for this host ([Uprava SERVER_OUTAGES.md](https://github.com/gasyoun/Uprava/blob/main/SERVER_OUTAGES.md),
row `www.sanskrit-lexicon.uni-koeln.de`, H870 note). The board's documented
route — `servepdf.php?…&api=1` through WebFetch's egress — answered every
key and named the pdf it resolves to, which proves the **volume**, not just a
200:

| # | page | L | page key | resolves to | volume right |
|---:|---|---|---|---|---|
| 1 | `agni` | 117975 | `7-1686` | `pwg7-1685.pdf` | ✅ (two-column spread) |
| 2 | `agni` | 349 | `1-0028` | `pwg1-0027.pdf` | ✅ |
| 3 | `agni` | 62586 | `5-0948` | `pwg5-0947.pdf` | ✅ |
| 4 | `as` | 118657 | `7-1705` | `pwg7-1705.pdf` | ✅ |
| 5 | `as` | 118659 | `7-1706` | `pwg7-1705.pdf` | ✅ |
| 6 | `as` | 65826 | `5-1076` | `pwg5-1075.pdf` | ✅ |
| 7 | `as` | 7256 | `1-0535` | `pwg1-0535.pdf` | ✅ |
| 8 | `as` | 7257 | `1-0538` | `pwg1-0537.pdf` | ✅ |
| 9 | `as` | 7258 | `1-0544` | `pwg1-0543.pdf` | ✅ |
| 10 | `Darma` | 32130 | `3-0529` | `pwg3-0529.pdf` | ✅ |
| 11 | `gam` | 119742 | `7-1737` | `pwg7-1737.pdf` | ✅ (was 1-1737 on the committed card) |

11/11 resolved; each to its own volume across 1/3/5/7. The raw-link 429 is a
per-IP budget, not a link defect (H870 established the same on MW).

## 5. Registration (Phase 3)

1. `data/manifest/datasets.json` — row `pwg-print-anchors` (110 datasets);
   README count region + `directory/index.html` regenerated.
2. `.gitignore` — `dist/` (staging output, never the Pages input).
3. `tests/test_word_page_ux_staging.py` — 8 tests (parity, badge byte-match,
   no invented badge, H839 key, rungs, favorites markup, rail placement,
   docs/ refusal).
4. `CHANGELOG.md` [Unreleased] · `.ai_state.md` Completed.
5. NOT-PUBLISHED marker: [docs/NOT_PUBLISHED_H3457_WPAGE_UX.md](https://github.com/gasyoun/kosha/blob/main/docs/NOT_PUBLISHED_H3457_WPAGE_UX.md)
   — carries the one-edit flip procedure for when a human rules.

## 6. Residuals

1. **Flip live** — a human decides variant + timing (marker doc). Then:
   `ux=` at the two public call sites, regenerate `w/` + D4 head, refresh the
   P5 budget row (`docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md` §6).
2. **MW / Apte print anchors via the scan-index campaign** — later wave, as
   ruled.
3. **kosha#433** — case-folded `query.key` renders wrong Devanagari on
   capital-initial public pages (pre-existing; fix candidates in the issue).
4. Error-report widget — parked, needs a backend.

_Dr. Mārcis Gasūns_
