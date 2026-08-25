# H3479 — literary-source `<ls>` citation links (H3457 wave 2)

_Created: 25-08-2026 · Last updated: 25-08-2026_

**Status: staged, not live** — same non-publication contract as
[docs/NOT_PUBLISHED_H3457_WPAGE_UX.md](https://github.com/gasyoun/kosha/blob/main/docs/NOT_PUBLISHED_H3457_WPAGE_UX.md),
extended in this pass to cover this wave.

## What this wave adds

[H3457](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H3457-Fable_kosha_wpage-ux-badge-favorites-scananchors_24.08.26.md)
gave every dictionary entry a print-scan anchor pointing at *where the entry
itself* is printed. This wave, H3479, does the same for the LITERARY SOURCES a
PWG entry *cites* — the `<span class='ls'>` markup app/render.py already emits
for Cologne's `<ls>` element (its own documented deferral: "renders as
`<span class='ls'>text</span>` without an href"). PWG only; MW-side literary
scans are a later wave (the registry below is PWG-specific and no MW
equivalent was checked).

Code: [app/ls_hydrate.py](https://github.com/gasyoun/kosha/blob/main/app/ls_hydrate.py)
(new), wired into
[app/word_page.py::_entry_html](https://github.com/gasyoun/kosha/blob/main/app/word_page.py)
behind the same `ux=` staging gate H3457 uses. Census script:
[scripts/ls_census_h3479.py](https://github.com/gasyoun/kosha/blob/main/scripts/ls_census_h3479.py).

**Never a new resolver.** Reuses two things that already exist:
[`ls_resolver.generate_href`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/ls_resolver.py)
(SanskritLexicography sibling — the production PWG citation resolver, 83.6%
coverage over 41,115 real `<ls>` citations, H2827) and
[`pwg_scan_index.tsv`](https://github.com/sanskrit-lexicon/csl-observatory/blob/main/data/pwg_scan_index_tracker/pwg_scan_index.tsv)
(csl-observatory sibling, kosha manifest row `pwg-scan-index-campaign`) for
which sources the volunteer scan campaign has actually wired live. Both are
optional sibling checkouts, read lazily; absent either, hydration is a no-op
(same DB-free / honest-miss posture as the H3457 print anchors).

## 1. Census — `<ls>` citations on the staged sample

11 lemmas named in the handoff (`kf, gam, vac, as, deva, Darma, agni, rAma,
jana, nf, yA`). `kf` and `nf` carry **zero PWG entries** (MW/AP90 only for
those two roots in the current data) — an honest miss, not a bug.

| lemma | pwg entries | `<ls>` total | scan_wired | e-text | mintable | no_locus |
|---|---:|---:|---:|---:|---:|---:|
| `kf` | 0 | 0 | 0 | 0 | 0 | 0 |
| `gam` | 4 | 1985 | 576 | 1106 | 251 | 52 |
| `vac` | 1 | 803 | 188 | 495 | 102 | 18 |
| `as` | 10 | 869 | 260 | 474 | 113 | 22 |
| `deva` | 3 | 263 | 68 | 123 | 37 | 35 |
| `Darma` | 2 | 228 | 57 | 66 | 67 | 38 |
| `agni` | 4 | 118 | 16 | 68 | 18 | 16 |
| `rAma` | 2 | 184 | 56 | 74 | 23 | 31 |
| `jana` | 3 | 155 | 51 | 83 | 13 | 8 |
| `nf` | 0 | 0 | 0 | 0 | 0 | 0 |
| `yA` | 6 | 1698 | 459 | 1080 | 113 | 46 |
| **all 11** | — | **6303** | **1731** | **3569** | **737** | **266** |

Columns:
- **scan_wired** — resolves via `generate_href` AND the target host is a
  `scan_wired == "yes"` row in the campaign registry (a volunteer-scanned page
  image of the printed source). Hydrated as `<a class="ls ls-scan">`, title =
  the registry's full source name.
- **e-text** — resolves via `generate_href` to a live host the resolver knows,
  but NOT one the 82-row PWG campaign registry tracks: Ashtadhyayi.com sutra
  pages, the RV/AV hymn-line anchors, and several `sanskrit-lexicon-scans.
  github.io` hosts the registry's own scope doesn't happen to cover
  (Mahābhārata, Rāmāyaṇa, Manu, Śatapatha Brāhmaṇa, Kathāsaritsāgara, the
  Bhāgavata Purāṇa editions — all large canonical texts scanned/wired outside
  this particular volunteer campaign). Hydrated as `<a class="ls ls-etext">`.
  Reproduce the host breakdown with a one-off `urlparse` tally over
  `ls_hydrate.resolve_one` — see the module docstring.
- **mintable** — a real locus (digits present) but no resolver pattern covers
  it — the gap [`ls_links.py`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/ls_links.py)
  calls the same thing on the pwg_ru side. Left as plain `<span class='ls'>`
  text, untouched.
- **no_locus** — a bare abbreviation (e.g. a continuation citation with no
  digits of its own) with nothing to point at. Also untouched.

Reproduce: `python scripts/ls_census_h3479.py` (reads the committed
`docs/cards/*.json` + both sibling checkouts; no network).

## 2. Hydration behind `ux=`

`build_word_pages.py --ux-staging <variant>` unchanged in signature; the
hydration fires only when `ux` is truthy AND the entry's `dict == "pwg"`
(app/word_page.py::_entry_html). The default `render_word_page(card)` path —
no `ux` argument — is byte-identical to pre-H3479 output, same as H3457's
guarantee; see `tests/test_word_page_ux_staging.py` (10/10 still pass
unchanged).

Built the 11-lemma sample as staging variant `d` (H3480's recommended
direction):

```
python scripts/build_word_pages.py --ux-staging d --tokens kf,gam,vac,as,deva,_44arma,agni,r_41ma,jana,nf,y_41 --force
```

## 3. Smoke — Playwright, extended

[scripts/smoke_wpage_ux.py](https://github.com/gasyoun/kosha/blob/main/scripts/smoke_wpage_ux.py)
gained an `a.ls` check (every link carries a real `http(s)` href) alongside
the existing badge/PWG-anchor/favorites checks. Full log:
[docs/H3479_LS_CITATION_WAVE2_SMOKE_LOG_25.08.26.md](https://github.com/gasyoun/kosha/blob/main/docs/H3479_LS_CITATION_WAVE2_SMOKE_LOG_25.08.26.md).

**22/22 rows PASS** (11 pages × 2 viewports), 0 console errors, 0 bad `ls`
links across 4,995 distinct `<ls>` hrefs rendered on the sample.

## 4. Live check — ≥10 links, both buckets

12 distinct hrefs GET-checked (6 `ls-scan`, 6 `ls-etext`, one per distinct host
sampled), 1.5 s apart, `kosha-h3479-livecheck/1.0` user agent — these are
static GitHub Pages / Ashtadhyayi.com hosts, not Cologne's `serveimg`/
`servepdf` (the host the H3457 packet's `api=1` route note applies to), so no
special throttled route was needed here.

| # | class | host / path | HTTP | bytes |
|---:|---|---|---:|---:|
| 1 | ls-scan | `amara_dlc/app1?1,1,4,2` | 200 | 610 |
| 2 | ls-scan | `medini/app2?3,5,11` | 200 | 639 |
| 3 | ls-scan | `anekarthasamgraha/app1?2,327` | 200 | 583 |
| 4 | ls-scan | `abch2/app1?1379` | 200 | 703 |
| 5 | ls-scan | `vajasasa/app1?20,9` | 200 | 577 |
| 6 | ls-scan | `taittiriyas/app1?3,5,2,2` | 200 | 584 |
| 7 | ls-etext | `ashtadhyayi.com/sutraani/2/4/31` | 200 | 242532 |
| 8 | ls-etext | `mbhcalc?12.2260` | 200 | 647 |
| 9 | ls-etext | `mbhcalc?12.9232` | 200 | 647 |
| 10 | ls-etext | `mbhcalc?13.1370` | 200 | 647 |
| 11 | ls-etext | `mbhcalc?12.7850` | 200 | 647 |
| 12 | ls-etext | `ramayanaschl/?2,42,7` | 200 | 6136 |

**12/12 HTTP 200.**

## Goal / stop condition

`/goal ls-citation links live on the staged pages with census table + smoke
green + 10 links verified, stop after 3 tries` — met on try 1: census table
above, smoke 22/22 PASS, 12/12 live links verified.

## What keeps this off the public surface

Same three guarantees as H3457 (docs/NOT_PUBLISHED_H3457_WPAGE_UX.md): default
render is byte-identical, `--ux-staging` refuses any `docs/` output root, and
nothing here was pushed to Pages or samskrtam.ru. `docs/NOT_PUBLISHED_H3457_WPAGE_UX.md`
extended in this PR to name this wave alongside H3457/H3480.

_Dr. Mārcis Gasūns_
