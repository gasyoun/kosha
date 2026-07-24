# P5 word-page exit packet — static head + SSR long-tail

_Created: 24-07-2026 · Last updated: 24-07-2026_

Companion metadoc: [P5_WORD_PAGE_EXIT_PACKET.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/P5_WORD_PAGE_EXIT_PACKET.meta.md).

**Handoff:** [H1590](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1590-Opus_kosha_p5-ssr-static-head-exit-packet_24.07.26.md)
(W5 of [PLAN_KOSHA_NEXT_PROGRAMME_2026H2](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_NEXT_PROGRAMME_2026H2.md);
builds on H537 P5 surface + H1586 D4 budget re-measure).

**Executor this pass:** Grok 4.5 (`grok-4.5`) on Opus-lock override.

---

## 1. What shipped (agent-complete)

| Piece | Status | Evidence |
|---|---|---|
| D4 static head measured from `lemma_frequency.tsv` | ✅ | N=**11,148** at **95.00%** token mass (4,550,704 tokens · 59,282 countable lemmas) |
| `build_word_pages.py --coverage 0.95` / `--head N` | ✅ | [scripts/build_word_pages.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_word_pages.py) |
| Head ∩ cards prerender | ✅ | **10,370** pages written (778 head lemmas lack a static card → SSR) |
| `docs/w/` + `docs/browse/` gitignored regenerable | ✅ | [.gitignore](https://github.com/gasyoun/kosha/blob/main/.gitignore) — match cards policy |
| SSR `GET /w/{slp1}` byte-parity vs template | ✅ | `tests/test_word_page.py::test_ssr_route_byte_parity_with_template` — **4/4 green** (DB-gated; needs local `data/db/kosha.db`) |
| Head-selection unit tests | ✅ | `tests/test_build_word_pages_head.py` |
| Host-independent links (5-4) | ✅ | template asserts no `samskrtam` hardcode |

### Build command (operator / MG deploy)

```sh
# After cards exist (build_static_cache.py):
python scripts/build_word_pages.py --coverage 0.95 --force
# or, after re-measure confirms N, pin explicitly:
python scripts/build_word_pages.py --head 11148 --force
```

Output: gitignored `docs/w/*.html` + `docs/browse/`. Deploy with the other regenerable
static tiers (cards) — not committed.

### Budget log (this pass — full head build 24-07-2026)

| Metric | Value |
|---|---:|
| D4 N @ 95% | 11,148 |
| Coverage achieved | 95.00% |
| Pages built (head ∩ cards) | 10,370 |
| Head without card (SSR) | 778 |
| SSR tail beyond head (freq lemmas) | ≈48,134 |
| Total head HTML | **184.9 MB** |
| Mean page size | **17.4 KB** |
| Head share of 1,024 MB soft cap | **18.1%** |
| Projected web tier (cards 289.7 + conc 67.8 + reading 22.4 + js 13.3 + head 184.9) | **578.1 MB / 56.5%** |

Mean **17.4 KB** is higher than the H1586 sample mean (11.95 KB, n=348 head-band):
the full head includes heavier multi-dict lemmas. Still **≪75% / ≪90%** gates — no
head trim. Append-only row also in
[ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md) §6.

---

## 2. Exit checklist (P5 §7 / VERIFICATION 5-1…5-4)

| ID | Criterion | Agent result | Live / human |
|---|---|---|---|
| **5-1** | Static head N=11,148 build completes; size logged | ✅ script + measure + tests | MG: run full `--coverage 0.95` on deploy host; paste META into budget log |
| **5-2** | SSR parity test green | ✅ 4/4 local with `kosha.db` | CI may skip (DB-gated) — document, do not fail CI |
| **5-3** | Exit packet written; live checks honest | ✅ this file | MG signs §3 |
| **5-4** | Host-independent links | ✅ template + tests | re-spot-check on live HTML |

### Live checks (honest status)

| Check | Status | Notes |
|---|---|---|
| Lighthouse mobile ≥ 90 on a sample `/w/` page | ⛔ **BLOCKED** | Needs Pages/static head deployed (or local static server over `docs/w/`). Not faked green. |
| Paste a Gītā verse → open every word end-to-end | ⛔ **BLOCKED** | Needs reading pack + live `/w/` (static or SSR). H537 packs may already exist under `reading/`; walkthrough still needs a live surface. |
| MG sign-off on live staging (`samskrtam.ru` or Pages) | ⛔ **BLOCKED** | Deploy assumption N6 — server may land within days; static head works on Pages alone when MG regenerates `docs/w/`. |
| Live SSR long-tail for out-of-head lemma (no card / rank > N) | ⛔ **BLOCKED** | Requires FastAPI on samskrtam.ru. Route + parity exist in-repo. |
| Sample static head page crawlable without JS | 🟡 **LOCAL-ONLY** | `render_word_page` + tests guarantee panels + `<noscript>`; confirm on a built file after deploy. |

**Do not mark the live rows green until a human has run them on a deployed URL.**

---

## 3. Deploy checklist (MG)

1. Ensure `docs/cards/` + `docs/js/data/attested_keys.json` are current (`build_static_cache.py`).
2. `python scripts/build_word_pages.py --coverage 0.95 --force`
3. Confirm `docs/w/` page count ≈ head_with_card and total MB under budget.
4. Deploy regenerable static tree (cards + `w/` + `browse/`) to Pages / samskrtam.ru static root.
5. If API host is up: run uvicorn; spot-check `GET /w/{slp1}` for a **tail** lemma (not in head).
6. Lighthouse mobile on 3 head pages + 1 SPA `#/w/` route.
7. Gītā 1 walkthrough: every linked token opens a word page with dict panels.
8. Sign this packet (date + URL) and flip live rows above to ✅.

---

## 4. Non-goals (N7)

- Analytics / ESP / magic-link email
- Changing D4 N without new frequency data
- Committing `docs/w/` into git
- P6 RU tab / Kochergina

---

## 5. Acceptance map (VERIFICATION_KOSHA_NEXT_PROGRAMME Wave-5)

| ID | Met? |
|---|---|
| 5-1 | ✅ agent + operator command |
| 5-2 | ✅ local; CI skip documented |
| 5-3 | ✅ packet; live ⛔ blocked listed |
| 5-4 | ✅ |

Wave-5 **agent exit** is met. Wave-5 **product exit** (Lighthouse + walkthrough + MG live sign-off) remains human/deploy-gated.

---

_Dr. Mārcis Gasūns_
