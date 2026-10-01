# kosha GitHub Pages headroom plan — W4b gate recalibration (H4841)

_Created: 15-09-2026 · Last updated: 15-09-2026_

Produced by H4841 (Opus 5 `claude-opus-5`, run as the OxAlpha-tier handoff). Gate: [`scripts/measure_pages_budget.py`](https://github.com/gasyoun/kosha/blob/main/scripts/measure_pages_budget.py) · tests: [`tests/test_pages_budget_gate.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_pages_budget_gate.py) · log row: [ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md § W4b re-measure log](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md).

## 1. What was measured (15-09-2026, `main` @ `e6c692e34`)

Live probe: `gh api repos/gasyoun/kosha/pages` → `build_type: legacy`, `source: main:/`, repo has `.nojekyll`. **Pages publishes the whole tracked tree**, so the byte-true footprint is the sum of tracked blob sizes at HEAD.

| Tier | Tracked bytes | Share of 1,024 MB |
|---|---:|---:|
| `docs/cards/` (50,355 JSON) | 303.8 MB | 29.7% |
| `concordance/` (incl. panini 0.88 MB) | 116.3 MB | 11.4% |
| `reading/` | 25.1 MB | 2.5% |
| `docs/js/` | 13.9 MB | 1.4% |
| **`w/` committed** (10,725 files; 10,370 D4 head pages = 408.6 MB, mean **38.48 KB/page**) | **417.7 MB** | **40.8%** |
| served tiers subtotal | **876.9 MB** | **85.6%** |
| `data/` (of which `data/concordance/` 391.2 MB) | 571.7 MB | 55.8% |
| everything else | 31.3 MB | 3.1% |
| **published tree total** | **1,479.9 MB** | **144.5%** |

Deployed artifact (`github-pages`, run for `e6c692e34`): **238.4 MB compressed**. Every `pages-build-deployment` run on 15-09 succeeded at this size, so GitHub is not currently enforcing the documented 1 GB limit on the raw tree — that is a tolerance, not a guarantee.

## 2. Why the old gate said PASS

1. **Wrong page template in the sampler.** It rendered pages with `ux=None`; the committed tree is rendered with the published layer `DEFAULT_LIVE_UX` (H4026: study badge, favorites, scan anchors, era badges). Same 300 cards: **22.80 KB** without the layer, **36.75 KB** with it. This was the main source of the under-read.
2. **Wrong multiplier.** It projected `N=11,148 × mean`, but only 10,370 head lemmas have a card (778 go to server-side rendering). That over-counts by 7.5%, which partly hid defect 1.
3. **Missing tiers.** It counted cards + concordance + reading + docs/js + a *projected* head. It never counted the committed `w/` (so the H4833 deploy did not show up) or `data/`.
4. **Correction to the H4841 mission text:** the old frame was **not** single-band. `head_tokens[::step]` already spread across ranks 0…10,166 of 10,370. A true first-300 band would have read **70.0 KB/page**, an *over*-read. The frame is now explicitly stratified anyway, so the invariant is locked by a test rather than implied by a slice.

## 3. What the recalibrated gate does

1. It measures the published tree byte-true, split into tiers that add up to exactly the total. `w/` is one of those tiers, so it can't be counted twice or missed.
2. It projects the **unbuilt** head pages (head tokens with a card but no committed `w/<token>.html`) and adds them to the total. Today that's 0 pages.
3. The sample frame has a take-all stratum (the largest 2% of cards by JSON bytes = 207 cards) plus a size-sorted systematic sample in the head/mid/tail rank thirds (100 each). All pages render with the published ux layer.
4. **Sampler check:** it runs the estimator over the whole head and compares it to the byte-true census of the committed head. The estimate was 410.1 MB against a census of 408.6 MB = **+0.37%**, inside the ±5% acceptance. Other frames I tried before this one: a plain rank-band mean was off by up to ±8.6%, and a card-bytes ratio estimator by up to −8.9%.
5. **The ceiling stays at 70% (716.8 MB).** The gate now reads **GATE FAIL — 1,479.9 MB = 144.5%**. Moving the ceiling to make it pass would be the silent drift the handoff forbids. Even the served tiers alone (85.6%) are above 70%.

## 4. Headroom options

1. **(a) Slim-page refactor.** Move the inline chrome/CSS/JS shared by all word pages into one cached asset and cut the 38.5 KB mean. Cost: all 10,725 `w/` pages re-render. Byte-parity with the H4026 published chrome breaks by design, so it needs a visual-regression pass. It saves at most part of the 417.7 MB `w/` tier, and `data/` (571.7 MB) is untouched, so the tree stays above 100%. Several hours of work plus review.
2. **(b) Move the head to samskrtam.ru (P-D4 canonical tier, MG deploy gate).** Pages keeps only a thin redirect shell. Saves up to ~418 MB. Cost: depends on the samskrtam.ru deploy, which isn't live yet (MG-gated). Citation durability (RISKS R1/R5) needs `PUBLIC_BASE` to stay host-independent, which rules out moving the canonical citation host. Still leaves `data/` published.
3. **(c) Accept the current size and plan the next tier's home.** Cost: none now. Risk: the tree is already 144.5% of the documented limit. GitHub can start refusing builds without notice, and every new tier makes that more likely.
4. **(d) Publish only the served surfaces (new option, found by this measurement).** Switch Pages from legacy `main:/` to a GitHub Actions workflow that uploads an allowlist: `index.html`, `w/`, `docs/` (cards + js + site pages), `concordance/`, `reading/`, `directory/`, and the few site assets. `data/` and repo internals stay in git but are no longer served. Cost: one workflow file plus a Pages settings change (Source → GitHub Actions). No page re-renders, so byte-parity is safe. The published tree drops from 1,479.9 MB to about 877 MB (85.6%). Risk: any external link into `/kosha/data/…` breaks. A grep of site HTML/JS on 15-09 found none, but a Pages access-log check isn't possible, so data-hub consumers should fetch from release assets or `raw.githubusercontent.com` instead. About 1 hour.

## 5. Recommendation

Do **(d) now**, then **(b)** when samskrtam.ru goes live. (d) removes 603 MB of unserved bytes with no re-render and no chrome risk, and gets the published site back under the 1 GB limit. The remaining 85.6% is almost exactly the served surface, and (b) is the only option that shrinks it much. Keep the gate at 70% so it keeps failing until (b) lands. What would change this recommendation: evidence that external users rely on `/kosha/data/…` URLs, which would make (d) a breaking change and push to (a) + (b).

**A human should decide:** (d) changes what the public site serves (a publication change), so it waits for MG's go. Reply «да, (d)» to have an agent write the allowlist workflow and flip Pages to GitHub Actions. Reply «нет» to keep the legacy source.

## 6. Side finding

The kosha [CLAUDE.md](https://github.com/gasyoun/kosha/blob/main/CLAUDE.md) says `docs/cards/` and `docs/js/data/*.json` are "never committed in-repo". They are: 50,355 card files are tracked at HEAD. That line is stale, and the tracked cards are why Pages serves them. I didn't change it in this unit.

_Гасунс_
