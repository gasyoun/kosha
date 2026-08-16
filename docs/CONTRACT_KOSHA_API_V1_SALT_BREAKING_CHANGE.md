# kosha `/api/v1` — the Salt contract and the W0C breaking change

_Created: 31-07-2026 · Last updated: 16-08-2026_

Handoff [H1945](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1945-Opus_kosha_architecture-roadmap-w0c-contract-trust-boundaries_30.07.26.md)
· plan of record
[PLAN_KOSHA_ARCHITECTURE_ROADMAP_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_ARCHITECTURE_ROADMAP_2026_2027.md)
D6/D13 · executed by Opus 5 1M (`claude-opus-5[1m]`).

This document is the cut: what `/api/v1` returned through v0.97, what it
returns now, and why the change was made before the API became public rather
than after.

## 1. Why now

D6 makes the
[C-SALT / CSL Salt profile](https://github.com/sanskrit-lexicon/csl-standards/blob/main/docs/SALT_API_PROFILE.md)
binding for `/api/v1`. kosha already served that profile on its `/dicts/*`
faces and a *different*, flat shape on `/api/v1` — two contracts over one
dataset, kept in step by hand. The risk register's own entry for this reads
"API migration breaks unknown clients → pre-public breaking change; freeze
golden old/new fixtures and document the cut". The public `samskrtam.ru`
dictionary URL is not yet deployed, so the population of clients that can break
is the ones in this repository.

## 2. The shape, before and after

Through v0.97 a `results[]` element was flat:

```json
{
  "dict": "mw", "L": "101", "headword": "agni",
  "scan_url": "https://…/servepdf.php?page=5",
  "rendered_html": "<span class='sdata'>agni</span>…",
  "sense_ids": ["mw.101.1@1.2.0"],
  "evidence": {"band": 1, "…": "…"},
  "heritage": {"covered": true, "…": "…"}
}
```

From W0C it is a Salt entry, and everything above lives under `kosha`:

```json
{
  "id": "lemma-agni",
  "headword_slp1": "agni",
  "sense": ["agni, m. fire, sacrificial fire", "the god of fire…"],
  "re_headwords_slp1": [],
  "created": null,
  "xml": null,
  "csl": {
    "lnum": "101", "page": "5", "column": "1",
    "scanUrl": "https://…/servepdf.php?page=5",
    "references": [], "accentedKey": "agni",
    "headwordIast": "agni", "headwordDeva": "अग्नि",
    "xmlCsl": null, "html": null, "text": null
  },
  "kosha": {
    "dict": "mw", "L": "101", "headword": "agni",
    "scan_url": "https://…/servepdf.php?page=5",
    "sense_ids": ["mw.101.1@1.2.0"],
    "rendered_html": "<span class=\"sdata\">agni</span>…",
    "evidence": {"band": 1, "…": "…"},
    "heritage": {"covered": true, "…": "…"},
    "cite": {"text": "mw.101.1@1.2.0", "…": "…"},
    "raw": null
  }
}
```

The `{data_version, query, results}` envelope is **unchanged**. A client
reading `data_version` or `query` needs no edit; a client reading
`results[i].rendered_html` reads `results[i].kosha.rendered_html`.

### Migration in one line

| Was | Is |
|---|---|
| `r.dict` · `r.L` · `r.headword` | `r.kosha.dict` · `r.kosha.L` · `r.kosha.headword` |
| `r.rendered_html` | `r.kosha.rendered_html` (now sanitized) |
| `r.sense_ids` · `r.evidence` · `r.heritage` | `r.kosha.…` |
| `r.scan_url` | `r.kosha.scan_url`, or `r.csl.scanUrl` |
| `r.raw` (with `?raw=1`) | `r.kosha.raw`, or `r.csl.xmlCsl` |
| — | `r.id`, `r.sense[]`, `r.headword_slp1` (new, Salt-defined) |

In-repo consumers were migrated in the same pass:
[`ui/src/lib/datasource.js`](https://github.com/gasyoun/kosha/blob/main/ui/src/lib/datasource.js)
unwraps at the data boundary (`entryFields`), and
[`app/word_page.py`](https://github.com/gasyoun/kosha/blob/main/app/word_page.py)
does the same server-side. Both accept the old shape too, because the static
tier is deployed out of band and a card generated before the cut can still be
live when a new bundle ships.

## 3. Three decisions worth recording

**Rendered HTML lives under `kosha`, not `csl.html`.** The profile lists
`csl.html` as the CSL *host's* rendering. kosha is a derivative that re-renders
Cologne markup through its own port of `basicdisplay.php`. Publishing our render
in Cologne's slot would claim an authority we do not have, so `csl.html` and
`csl.text` are `None` and the render is served, attributed, at
`kosha.rendered_html`.

**`xml` stays `null`.** Profile §8.1 reserves it for the TEI-P5 body and
forbids CSL display-XML there. Filling it with Cologne markup would look like
conformance and be its opposite — a client would parse Cologne's tagset as TEI.
The unmodified markup is available at `csl.xmlCsl`, opt-in via `?raw=1`.

**The public faces are explicit projections.** `/api/v1` and static/SSR cards
retain the full object above. `/dicts/*` exposes only the six §8.1 fields plus
`csl`, because profile §9 permits no other structural divergence. Both are
built by one serializer; the latter is a terminal field projection. Decision:
[H2768 strict-face contract](DECISION_H2768_SALT_FACE_EXTENSION_CONTRACT.md).

**A Salt `id` is dictionary-scoped, not globally unique.** C-SALT addresses
entries under `/dicts/{dict}/…`, so `lemma-agni` means "agni in *this*
dictionary" — and MW, PWG and Apte each mint exactly that string. C-SALT never
notices, because a C-SALT response is always one dictionary's; kosha's lemma
card merges three. **The key on a lemma card is `(kosha.dict, id)`.** Pinned by
`test_salt_face_entry_matches_the_api_salt_projection` and
`test_dictionary_scoped_ids_may_collide_across_dictionaries`.

## 4. Errors

Two shapes, each owned by a contract — as against the three that used to leave
the service.

| Surface | Shape | Why |
|---|---|---|
| `/api/v1/*` | `{"error": {"code", "message", "suggestions"}}`, top level | kosha's own contract; was nested inside FastAPI's `detail` |
| `/dicts/*` | `{"error": "<message>"}` | profile §3.2 — the faces exist to be wire-compatible with C-SALT |

Request-validation failures and unhandled exceptions are normalized too, and
answer **400** rather than FastAPI's 422 so one service does not answer one
class of mistake with two statuses. Salt faces now return **400** where they
previously returned 200 with an error body.

## 5. What is deliberately still missing

Recorded so a later reader does not mistake a known gap for an oversight.

| Gap | Status |
|---|---|
| `re_headwords_slp1` always `[]` | kosha has no run-on/sub-headword layer; an empty list is the honest answer |
| `created` always `null` | no per-entry build timestamp is stored |
| `query_type` ∈ {`wildcard`, `regexp`, `fuzzy`, `match`, `match_phrase`} | not indexed; explicit 400 per profile §4, never a silent empty result |
| `field` ∈ {`id`, `sense`, `re_headwords_slp1`, `created`, `xml`} | same |
| GraphQL face (§6), clean-URL permalinks (§6a) | P7-scoped, out of W0 |
| `csl.html` / `csl.text` | `None` by decision, §3 above |

---

_Dr. Mārcis Gasūns_
