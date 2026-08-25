# Pack-token static word pages

_Created: 13-08-2026 · Last updated: 25-08-2026_

Committed **Pages** half of the P5 `/w/` surface (H2665). Reading packs under
[`reading/`](https://github.com/gasyoun/kosha/blob/main/reading/) emit
`../w/{token}.html`. Those resolve on GitHub Pages as site-root
[`https://gasyoun.github.io/kosha/w/{token}.html`](https://gasyoun.github.io/kosha/w/vac.html),
not `docs/w/` (that tree stays gitignored for the full D4 head).

## Regen

```sh
python scripts/build_word_pages.py --reading-packs --force
```

Harvests unique `../w/{token}.html` hrefs from `reading/`, renders each token
that has a [`docs/cards/{token}.json`](https://github.com/gasyoun/kosha/blob/main/docs/cards)
card through the same `render_word_page` template as SSR. Tokens without a
card stay unpublished here — the live API covers them at
`GET /w/{slp1}`.

## 13-08-2026 measure

| | |
|---|---:|
| Pack href tokens | 2,926 |
| Pages written (have card) | 2,324 |
| No card (SSR only) | 602 |
| Total HTML | 60.4 MB |
| Mean page | 25.4 KB |
| Share of 1 GB soft cap | 5.9% |

This is **not** the D4 95% frequency head (N=11,148 → `docs/w/`, gitignored).
It is the pack walkthrough set.

## 25-08-2026 regen (H3490)

| | |
|---|---:|
| Pack href tokens | 2,926 |
| Pages written (have card) | 2,324 |
| Total HTML | 74.2 MB (mean 31.2 KB/page) |

Regenerated after the RU-tab fixes (H3480 `{#…#}`/`{%…%}` pre-pass, H3490 bare-SLP1
transliteration + escaped-tag rows) — every page changed, since the template had
also grown the SanskritRussian line and the sense-frequency block since 13-08.

_Dr. Mārcis Gasūns_
