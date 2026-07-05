# kosha inflection UI (P4 Wave K2b)

_Created: 05-07-2026 · Last updated: 05-07-2026_

The translator-first Sanskrit **inflection lookup UI** — the frontend half of
[ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md)'s
Wave K2, built over Wave K2a's backend (the `inflections` / `forms` /
`stem_bridge` tables and `/api/v1/forms/{form}/analyze`). Svelte 5 + Vite; the
production build ships into
[`../docs/inflect/`](https://github.com/gasyoun/kosha/tree/main/docs/inflect)
so MG's existing GitHub Pages deploy serves it at
`https://gasyoun.github.io/kosha/inflect/` with no new deploy path.

## Features (H183)

- **Stem → paradigm** — auto-detect input (Devanagari / IAST / SLP1 → SLP1),
  full case×number (nominal) and voice/tense/person×number (verb) grids,
  **Devanagari-default** rendering with an IAST/SLP1 output toggle.
- **Analyse a form** — paste-anything reverse box wrapping the `/analyze`
  cascade, showing each parse's `resolved_by` provenance.
- **Autocomplete** — live suggestions off the shared 323k-lemma
  [`docs/js/data/lemmas.json`](https://github.com/gasyoun/kosha/blob/main/docs/js/data/lemmas.json)
  index (prefix range-seek, not a full scan), with live transliteration.
- **Dictionary cross-links (folded roadmap Wave K3)** — every stem/lemma links
  into its in-app MW/PWG/AP90 entry, and the entry has a "show all forms"
  control back into the paradigm — two silos, one tool.

## Data backend (K2b-2 "both")

One code path per feature ([`src/lib/datasource.js`](src/lib/datasource.js)):

- **Static (default)** — fetches the pre-generated JSON that ships with the
  Pages deploy. Works fully on `gasyoun.github.io` with **no live server**
  (RISKS.md R1/R5/R12-clean). Stage-3 vidyut segmentation can't run in a static
  browser, so a sandhied/compound miss (e.g. `tattvamasi`) honestly reports
  `segmentation_available:false`.
- **Live API** — when `window.KOSHA_API` is set to a kosha FastAPI base URL,
  every lookup hits `/api/v1/…` for freshness. That's kosha's **own** server,
  never a live third-party service (R12).

Set the API base by injecting a script before the app bundle, e.g. in a Pages
wrapper: `<script>window.KOSHA_API = "https://api.example.org";</script>`.

## Build

```sh
cd ui
npm ci            # install pinned deps
npm run build     # -> ../docs/inflect/  (commit the output; it is the Pages input)
npm test          # vitest: translit / token-parity / autocomplete / data-path / App e2e
npm run dev       # local dev server (data fetched from ../docs/inflect/data, ../docs/js, ../docs/cards)
```

The build uses `emptyOutDir:false` so it never wipes the committed
`docs/inflect/data/` shards; the app bundle (`index.html`, `assets/`) is
overwritten each build.

## Static data generation

The paradigm and reverse-index shards are generated from `kosha.db` by
[`../scripts/build_paradigms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_paradigms.py)
(never calls a live service — R12):

```sh
python scripts/build_paradigms.py            # --demo (default): the committed exit-check demo set
python scripts/build_paradigms.py --all      # full 176k attested-with-entry set (~250 MB; MG deploys, A3)
python scripts/build_paradigms.py --limit 5000   # top-N by frequency rank (partial / smoke)
```

The **demo set** (the H183 exit-check stems + a few common teaching stems) is
committed so the static site works out of the box. The **full set** is deployed
out-of-band by MG exactly like the P2 cards tier (run `/publish-safety-check`
first). Each paradigm shard is byte-identical to `GET /api/v1/paradigm/<slp1>` —
parity locked by
[`../tests/test_paradigms.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_paradigms.py).

## Reuse (maximum-reuse rules)

- Transliteration is the vendored **sanskrit-util** JS package
  ([`src/lib/sanskrit-util.mjs`](src/lib/sanskrit-util.mjs), SHARED_CODE.md
  family #1) — re-copy from `sanskrit-util/js/index.mjs` on package updates;
  never edit in place. `src/lib/translit.js` adds only the auto-detect sniffer
  (JS twin of `app/transliterate.py`).
- `card_token` / `reverseBucket` ([`src/lib/cardToken.js`](src/lib/cardToken.js))
  are exact twins of the Python encoders in `scripts/`.
- Autocomplete reuses the existing `lemmas.json` index — no second index.

_Dr. Mārcis Gasūns_
