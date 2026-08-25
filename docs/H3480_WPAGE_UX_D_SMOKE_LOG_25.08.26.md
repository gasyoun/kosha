# H3457 word-page UX staging — Playwright smoke log (variant `d`)

_Created: 25-08-2026 · Last updated: 25-08-2026_

_Run 25-08-2026 09:58 local · Chromium headless via Python Playwright · file:// over `dist/w-staging/d/` · 11 pages × 2 viewports · 20.4 s · verdict **PASS**_

Local-only: nothing here touched docs/, Pages or samskrtam.ru (docs/NOT_PUBLISHED_H3457_WPAGE_UX.md).

| token | slp1 | px | ok | console | badge vs lemma_frequency.tsv | PWG anchors (bad) | favorites: click → reload → listed → un-fav |
|---|---|---:|---|---:|---|---|---|
| `agni` | `agni` | 375 | ✅ | 0 | rank 17 cov 0.290706 -> page ('17', '0.290706') | 4 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `as` | `as` | 375 | ✅ | 0 | rank 5 cov 0.73065 -> page ('5', '0.73065') | 10 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `Darma` | `Darma` | 375 | ✅ | 0 | rank 12 cov 0.346062 -> page ('12', '0.346062') | 1 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `deva` | `deva` | 375 | ✅ | 0 | rank 4668 cov 0.00273034 -> page ('4668', '0.00273034') | 3 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `gam` | `gam` | 375 | ✅ | 0 | rank 7 cov 0.478229 -> page ('7', '0.478229') | 4 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `jana` | `jana` | 375 | ✅ | 0 | rank 83 cov 0.105583 -> page ('83', '0.105583') | 3 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `kf` | `kf` | 375 | ✅ | 0 | rank 1 cov 0.991412 -> page ('1', '0.991412') | 0 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `nf` | `nf` | 375 | ✅ | 0 | rank 354 cov 0.0452156 -> page ('354', '0.0452156') | 0 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `rAma` | `rAma` | 375 | ✅ | 0 | rank 81 cov 0.108463 -> page ('81', '0.108463') | 1 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `vac` | `vac` | 375 | ✅ | 0 | rank 2 cov 0.929154 -> page ('2', '0.929154') | 1 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `yA` | `yA` | 375 | ✅ | 0 | rank 7208 cov 0.000630077 -> page ('7208', '0.000630077') | 2 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `agni` | `agni` | 1280 | ✅ | 0 | rank 17 cov 0.290706 -> page ('17', '0.290706') | 4 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `as` | `as` | 1280 | ✅ | 0 | rank 5 cov 0.73065 -> page ('5', '0.73065') | 10 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `Darma` | `Darma` | 1280 | ✅ | 0 | rank 12 cov 0.346062 -> page ('12', '0.346062') | 1 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `deva` | `deva` | 1280 | ✅ | 0 | rank 4668 cov 0.00273034 -> page ('4668', '0.00273034') | 3 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `gam` | `gam` | 1280 | ✅ | 0 | rank 7 cov 0.478229 -> page ('7', '0.478229') | 4 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `jana` | `jana` | 1280 | ✅ | 0 | rank 83 cov 0.105583 -> page ('83', '0.105583') | 3 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `kf` | `kf` | 1280 | ✅ | 0 | rank 1 cov 0.991412 -> page ('1', '0.991412') | 0 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `nf` | `nf` | 1280 | ✅ | 0 | rank 354 cov 0.0452156 -> page ('354', '0.0452156') | 0 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `rAma` | `rAma` | 1280 | ✅ | 0 | rank 81 cov 0.108463 -> page ('81', '0.108463') | 1 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `vac` | `vac` | 1280 | ✅ | 0 | rank 2 cov 0.929154 -> page ('2', '0.929154') | 1 (0) | click->true reload->true listed=True (n=1) unfav->false |
| `yA` | `yA` | 1280 | ✅ | 0 | rank 7208 cov 0.000630077 -> page ('7208', '0.000630077') | 2 (0) | click->true reload->true listed=True (n=1) unfav->false |

Reproduce: `python scripts/build_word_pages.py --ux-staging d --tokens agni,as,Darma,deva,gam,jana,kf,nf,rAma,vac,yA` then `python scripts/smoke_wpage_ux.py --variant d`.

_Dr. Mārcis Gasūns_
