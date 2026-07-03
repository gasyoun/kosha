# kosha — GitHub Pages static tier

_Created: 03-07-2026 · Last updated: 03-07-2026_

This directory is the **static tier** served by GitHub Pages (Phase 2 public
alpha). Everything under it is **generated from `kosha.db`** by
[`scripts/build_static_cache.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_static_cache.py)
and is **gitignored** — it is a deploy artifact, not committed source (A3: MG
deploys; agents never publish). The generator never calls a live service
(RISKS.md R12) — it renders from the local DB only, so the static tier is a
byte-for-byte snapshot of the `/api/v1/lemma` responses.

Sized per the D5-3 decision
([KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md)).

## What gets generated

| Path | What | Size | Committed? |
|---|---|---|---|
| `cards/<token>.json` | one card per attested lemma (~50,355 lemmas that have **both** a dict entry **and** a corpus attestation), frequency-ranked | ~155 MB, ~3 KB/file | no (Pages deploy) |
| `js/data/lemmas.json` | headword **autocomplete index** — all 323,425 lemmas, `{slp1, iast, dicts}` each, columnar | ~13 MB | no (Pages deploy) |
| `js/data/attested_keys.json` | sorted list of card tokens that exist, so the UI picks static-card vs dynamic-API without a 404 probe | ~0.5 MB | no (Pages deploy) |

The **full 222,179-lemma card set** (every entry-bearing lemma, ~682 MB) is not
part of the Pages tier — it ships as a **release-asset tarball** (`--full-tarball`)
for offline/mirror rebuildability (R1c/R4).

Each `cards/<token>.json` is **byte-identical** to what
`GET /api/v1/lemma/<slp1>?in=slp1` returns (locked by
[`tests/test_static_cache.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_static_cache.py)),
so the static tier and the dynamic API never diverge.

## Card filename encoding (`card_token`)

SLP1 is **case-significant** (`K` ≠ `k`), but many filesystems and checkouts are
case-*insensitive*, so raw keys collide. The card filename keeps `[a-z0-9]`
verbatim and escapes every other UTF-8 byte — uppercase letters, punctuation, and
`_` itself — as `_<hexbyte>`. Lossless, filesystem- and URL-safe, ASCII-only.

The frontend computes the same token to locate a card:

```js
function cardToken(slp1) {
  let out = "";
  for (const b of new TextEncoder().encode(slp1)) {
    out += ((b >= 97 && b <= 122) || (b >= 48 && b <= 57))
      ? String.fromCharCode(b)
      : "_" + b.toString(16).padStart(2, "0");
  }
  return out;                                   // fetch(`cards/${out}.json`)
}
```

Example: SLP1 `BU` (*bhū*) → `_42_55` → `cards/_42_55.json`.

## Regenerating

```sh
# cards + autocomplete index (default; ~6 min for the full attested set)
python scripts/build_static_cache.py

# top-N only — a partial run front-loads value (rank order): top-10k = 95.4%
# of corpus token mass; interruptible and resumable (existing shards skipped)
python scripts/build_static_cache.py --limit 10000

# full 222k card set as a release tarball (~682 MB, opt-in)
python scripts/build_static_cache.py --full-tarball data/releases/cards_full.tar.gz
```

Deployment (enabling Pages, pushing the generated tier) is **MG's** — run
`/publish-safety-check` first.

_Dr. Mārcis Gasūns_
