# P5 — Advanced UI design spec (the word page, MG's own way)

_Created: 10-07-2026 · Last updated: 10-07-2026_

The wireframe-locking design session that
[IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md)
§P5 requires **before** any build ("Design session first (judgment tier + MG)").
Rulings elicited from MG 10-07-2026 (interview run by Opus 4.8 `claude-opus-4-8`).
The build handoff is
[H537](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H537-Opus_kosha_p5_advanced_ui_word_page_build_10.07.26.md).

This spec supersedes the P5 bullets in the implementation plan for the four forks
it settles; everything else in §P5 (Lighthouse ≥90 exit, Gītā-walkthrough exit)
stays authoritative.

## 1. What P5 is

The public product surface at `samskrtam.ru/kosha` and `gasyoun.github.io/kosha` —
the "own advanced UI, API-first" that
[POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md) §2
records as the MG override. It is the reader-facing face over everything P1–P4
already built: the unified entry render, the DCS evidence layer (P3), and the
inflection/paradigm engine (P4). P5 adds **no new data** — it is presentation,
routing, crawlability, and study tooling over the existing API v1 + static tier.

The unit of the product is the **word page**: one headword, every dictionary's
entry for it, its evidence, its paradigm, its scan — on one addressable URL.

## 2. Decisions taken (MG rulings, 10-07-2026)

| # | Fork | Ruling | Consequence |
|---|---|---|---|
| P5-1 | Multi-dict presentation | **Tabs** (`MW │ PWG │ AP90 │ RU`) | One dictionary visible at a time; tab bar switches. Compact, closest to the michaelmeyer.fr one-page feel. **Crawlability caveat** (§5): a fetcher sees only the active tab unless every tab's content is in the prerendered DOM — so the prerender ships **all tabs' HTML in the page**, CSS-hidden, JS-activated. |
| P5-2 | Progressive-disclosure default depth | **All three modes, user-selectable** | A view-mode toggle offering (a) **Gloss** — short gloss + frequency band + Zaliznyak token; (b) **Full** — the complete rendered apparatus, all senses/refs; (c) **Adaptive** — Gloss on mobile, Full on desktop. Adaptive is the default first-visit mode; the choice persists per-visitor (localStorage). |
| P5-3 | Scope of the wave | **Full P5 build** | Permalink pages + `#`-browse + `sandhi:`/`root:` operators + CSV/Anki export + the Gītā 1 & Nala 1 reading packs, not a slice. Sequenced in §6 so each lands testable. |
| P5-4 | Permalink render target | **Both** | Prerender the top-N attested lemmas to the GitHub Pages tier (crawlable + offline, ships now, no server gate) **and** FastAPI SSR the long tail at `samskrtam.ru/kosha` once MG's P2 deploy lands. The static tier is authoritative for the head; SSR fills the tail. |

Rationale notes worth keeping:
- **Tabs + crawlability are in tension** (P5-1). The plan's own §P5 says permalink
  pages must be server-rendered "the crawlability lesson from the 02-07 survey
  (only Wisdom Library was readable to a fetcher)". Tabs normally hide content from
  a fetcher. We resolve it by rendering **all tab panels into the DOM** at
  prerender/SSR time and toggling visibility with CSS `hidden` + JS — never by
  lazy-fetching a tab's content on click. A `<noscript>` path shows all panels
  stacked. This keeps the tab *UX* while paying the crawlability *bill*.
- **Adaptive default** (P5-2) is the honest reconciliation of "student-friendly
  minimal" vs "scholar wants everything": pick by viewport, let either reader
  override, remember it.
- **Both** (P5-4) means the static prerender is the SEO/offline substrate and the
  SSR is a superset for coverage — the two must render **byte-comparable** primary
  content (same `render()` output), the standing kosha parity contract (the
  static-card == live-API test that already guards P2/P3).

## 3. The word page — anatomy

URL: `/w/{slp1}` (e.g. `/w/kfzRa` for कृष्ण). SLP1 is the canonical addressing key
already used by `/api/v1/lemma/{key}` — permalinks reuse it, no new key scheme.

```
┌───────────────────────────────────────────────┐
│ कृष्ण   kṛṣṇa   [kfzRa]        ▪ band 4 ▪ m·8n* │  ← headword strip (always visible)
│                             [Gloss·Full·Adaptive]│  ← view-mode toggle (persists)
├───────────────────────────────────────────────┤
│ [ MW ]  PWG   AP90   RU                         │  ← dict tab bar (P5-1)
│ ─────────────────────────────────────────────  │
│ black, dark, dark-blue … (active tab body,      │  ← entry body, depth per mode
│ rendered by app/render.py, scan ↗ per dict)     │
│                                                 │
│ ▸ evidence   ▸ paradigm (all forms)   ▸ scan    │  ← P3/P4 disclosures
└───────────────────────────────────────────────┘
```

- **Headword strip** — Devanagari + IAST + SLP1 key, frequency band badge (P3),
  Zaliznyak-style grammar token (P4, e.g. `m·8n*`). Always visible in every mode.
- **View-mode toggle** (P5-2) — `Gloss · Full · Adaptive`, persisted in
  `localStorage` (`kosha_view_mode`); Adaptive is the first-visit default.
- **Dict tab bar** (P5-1) — one tab per dictionary that has an entry for this
  headword, in fixed order MW → PWG → AP90 → RU (RU tab hidden until P6 gates
  clear). All panels prerendered into the DOM (§5).
- **Entry body** — the active tab's `rendered_html` from `app/render.py`
  (unchanged from P4); Gloss mode shows a truncated first-sense gloss + "full
  entry →", Full mode shows the whole apparatus.
- **Disclosures** — evidence sidebar (P3), paradigm table (P4, "show all forms"),
  scan link (P1 `scan_resolver`). Collapsed by default in Gloss/Adaptive-mobile,
  expanded in Full.

## 4. Search, browse, operators

- **Autocomplete search box** — reuse the existing prefix range-seek over the
  shared `js/data/lemmas.json` (the K2b `loadLemmaIndex` path in
  [`ui/src/lib/datasource.js`](https://github.com/gasyoun/kosha/blob/main/ui/src/lib/datasource.js));
  do NOT build a second index (H183 §3 standing rule). Enter on a hit → `/w/{slp1}`.
- **`#`-browse mode** — `/browse/{letter}` alphabetic index pages (Devanagari
  varṇa order), each a prerendered list of headwords under that akṣara. Crawlable
  spine that links every word page (SEO internal-linking).
- **Operators** in the search box:
  - `root:BU` → all lemmas under a root (drives off the P4 paradigm/forms tables).
  - `sandhi:tattvamasi` → force the paste-anything reverse pipeline
    (`/api/v1/forms/{form}/analyze`, K2a) instead of a headword lookup, showing the
    split.
  - Bare input auto-routes: a known headword → word page; an inflected/sandhied
    form → reverse analyze; ambiguous → a disambiguation list.
- **`<abbr>` tooltips** — the dictionary abbreviation expansions (already available
  in the render layer) surfaced as hover/tap tooltips.

## 5. Crawlability & the render targets (P5-4)

The non-negotiable from the 02-07 competitor survey: a fetcher with no JS must read
the full entry. So:

- **Static prerender** (`scripts/build_word_pages.py`, new): for the top-N attested
  lemmas (same frequency-ranked set as the P2 static cards — reuse
  [`scripts/build_static_cache.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_static_cache.py)'s
  card set, do not recompute N), emit `/w/{token}.html` with **all dict panels'
  HTML present** (active shown, rest `hidden`), the headword strip, evidence, and a
  `<noscript>` all-stacked fallback. Progressive JS hydrates the tabs + view-mode
  toggle + disclosures on top. Ships to Pages now, no server dependency.
- **FastAPI SSR** (`GET /w/{slp1}` in `app/main.py`, new): server-renders the same
  template for the long tail (any lemma, not just top-N) once `samskrtam.ru` is
  deployed. Same Jinja/template output as the prerender so the two are
  byte-comparable on primary content — locked by a new parity test mirroring
  `test_static_cache.py`'s card == live-API contract.
- **N and size:** re-measure the Pages tier budget before the bulk prerender —
  P2 cards already measured **402 MB** (`.ai_state.md` D5-3 note), ~60% headroom
  under the 1 GB soft limit; word-page HTML is heavier than a card JSON, so N may be
  smaller than the 50,355 card set. **Log the actual N and the dropped tail
  explicitly** (no-silent-caps, `IMPLEMENTATION_PLAN.md` cross-cutting rule); the
  SSR tail covers whatever the static head drops.

## 6. Build sequence (H537)

Each step lands testable; CI (once it exists) stays green. Reuse the existing
Svelte `ui/` app and `datasource.js` "both" shim — extend, don't fork.

1. **Word-page component + route.** New `WordPage.svelte` (tabs + view-mode toggle +
   disclosures), reusing `EntryView.svelte`, the P3 evidence block, and
   `ParadigmTable.svelte`. Client route `/w/{slp1}`.
2. **Tab layout + view-mode toggle** (P5-1, P5-2), persistence in `localStorage`,
   `<noscript>` stacked fallback.
3. **Static prerender pipeline** (`scripts/build_word_pages.py`, P5-4 static half) +
   `#`-browse index pages; N logged.
4. **FastAPI `GET /w/{slp1}` SSR** (P5-4 server half) + byte-parity test vs the
   prerender.
5. **Operators** (`root:`, `sandhi:`, auto-route) + `<abbr>` tooltips.
6. **Study tooling:** CSV/Anki export of session lookups; Gītā 1 & Nala 1 reading
   packs generated from DCS lemmatization.
7. **Exit checks** (from the plan, unchanged): MG sign-off on live staging;
   Lighthouse mobile ≥90; paste a Gītā verse → read every word end-to-end.

## 7. Reuse ledger (check-prior-art, don't rebuild)

| P5 need | Already exists — reuse | Source |
|---|---|---|
| per-dict entry HTML | `app/render.py` + `getEntry()` (returns `{dict, rendered_html, scan_url}`) | P1/P4 |
| static ∥ live "both" data path | `ui/src/lib/datasource.js` `API ?? static` shim | K2b |
| autocomplete index | `js/data/lemmas.json` + prefix range-seek | K2b, H183 §3 |
| frequency band + Zaliznyak token | P3 evidence + P4 paradigm token | P3/P4 |
| paradigm "show all forms" | `ParadigmTable.svelte` + `/api/v1/paradigm/{lemma}` | K2b |
| reverse/sandhi split | `/api/v1/forms/{form}/analyze` (K2a cascade) | K2a |
| scan anchor | `app/scan_resolver.py` `servepdf.php` mechanism | P1 |
| top-N card set (prerender N) | `scripts/build_static_cache.py` card set | P2 |

New code is only: `WordPage.svelte`, `scripts/build_word_pages.py`, the
`GET /w/{slp1}` SSR route + template, the operator router, the export + reading-pack
generators. Everything else is composition.

## 8. Non-goals (ruled out — do not re-propose)

- **Stacked or accordion multi-dict layout** — considered, rejected for tabs (P5-1).
- **Lazy-fetching tab content on click** — breaks crawlability (§5); all panels
  prerender into the DOM instead.
- **A second autocomplete/headword index** — the shared `lemmas.json` is canonical
  (H183 §3).
- **Hardcoding `samskrtam.ru` into citation/permalink paths** — `PUBLIC_BASE` stays
  host-independent (RISKS.md R1/R5; `CLAUDE.md` citation-durability convention).
- **Live third-party calls at build time** — prerender uses local data only (R12).
- **Shipping the RU tab before P6 gates** — RU tab hidden until G5 review + the
  Kochergina rights decision clear (`IMPLEMENTATION_PLAN.md` §P6).

_Dr. Mārcis Gasūns_
