# DATA_HUB_ROADMAP.md — kosha as the Sanskrit data-hub

_Created: 06-07-2026 · Last updated: 06-07-2026_

## Why this exists

The org has four *catalogues* of reusable data
([`REUSE_INDEX.md`](https://github.com/gasyoun/Uprava/blob/main/REUSE_INDEX.md),
[`PROJECT_INTERLINKS.md`](https://github.com/gasyoun/Uprava/blob/main/PROJECT_INTERLINKS.md),
[`FEATURES_INDEX.md`](https://github.com/gasyoun/SanskritLexicography/blob/master/FEATURES_INDEX.md),
[`DATA_LAYERS_CENSUS.md`](https://github.com/gasyoun/Uprava/blob/main/DATA_LAYERS_CENSUS.md))
— yet derived data still goes unreused, because the catalogues describe assets that are
**not served anywhere**: per the census, **70 % of derived data (19.2 GB) is local-only,
gitignored, single-copy, unbackuped**. A fresh session (or an outside researcher) that
finds `corpus_lexicon` in an index has no URL to fetch it from. The fix is not a fifth
index — it is a **hub that hosts the bytes**.

## Locked decisions (MG rulings, 06-07-2026, elicited by Fable 5 `claude-fable-5`)

| # | Decision | Ruling |
|---|---|---|
| D-HUB-1 | Where the hub lives | **kosha is the Sanskrit data-hub** — the existing gh-pages site ([features](https://gasyoun.github.io/kosha/features/) / [questions](https://gasyoun.github.io/kosha/questions/)) is not enough on its own; kosha grows the hub role. All four hub forms apply over time: data releases, one queryable DB, web API, merged machine-readable manifest. |
| D-HUB-2 | Observed reuse failures | (a) data unreachable (gitignored/local-only), (b) sessions don't consult the indexes, (c) one-shot deliverables never wired to consumers. Storage first, then discovery/enforcement. |
| D-HUB-3 | First cargo | All four families — Sa→Ru translation stack, kosha + frequency layer, crosswalks + headwords, DCS derivatives — with the ambition of being **the first place on the internet for Sanskrit NLP data + tools**. |
| D-HUB-4 | Primary consumer | **Agent sessions** in the ~85 repos: the hub must be reachable by URL/clone and advertised in the spine so `/prior-art` lands on it automatically. External researchers second. |
| D-HUB-5 | Byte hosting (big files) | **Own server, samskrtam.ru** (canonical home, alongside the kosha deploy). Interim, until the MG deploy gate opens: small clean assets ship as **kosha GitHub Releases** (`data-v*` tags) so agents have stable URLs today. |
| D-HUB-6 | Rights handling | **Two-tier hub.** Public tier = clean assets (crosswalks, headwords, frequency, roots), each past `/publish-safety-check`. Restricted tier = rights-encumbered data (corpus_lexicon over published RU translations, Heritage LGPLLR-pending mirror, SamudraManthanam corpus.db) backed up privately, reachable by our agents, never published. |
| D-HUB-7 | Directory scope | **Yes** — kosha's public site also becomes a curated **Sanskrit NLP data + tools directory** (our datasets downloadable + external tools/APIs: vidyut, Heritage, SCL/Samsaadhanii, DharmaMitra, DCS…). Content ~80 % exists in `FEATURES_INDEX.md` + `REUSE_INDEX.md` §5 + `SAMSAADHANII_INDEX.md`; the win is publishing it. |
| D-HUB-8 | First slice (06-07-2026) | Roadmap + machine-readable manifest + first public data release (small, already-public assets). |

## Architecture

```
                       ┌─ public tier ──────────────────────────────┐
 source repos          │  kosha GitHub Releases (data-v*, interim)  │   consumers
 (csl-orig, SanLex,    │  → samskrtam.ru/kosha/data/ (canonical,    │   agent sessions (/prior-art)
  VisualDCS, kosha…) ─▶│    after MG deploy)                        │─▶ external NLP researchers
                       │  + public directory page (data + tools)   │   DharmaMitra / SCL / vidyut users
                       └────────────────────────────────────────────┘
                       ┌─ restricted tier ──────────────────────────┐
                       │  private backup (private repo releases /   │─▶ our own agents + apps only
                       │  private storage) for rights-encumbered    │
                       │  and oversize single-copy data             │
                       └────────────────────────────────────────────┘
 manifest: data/manifest/datasets.json — ONE machine-readable list of every canonical
 dataset (both tiers), with location, keying, rights, consumers. Agents read this file.
```

## Phases

| Phase | What | Status |
|---|---|---|
| **P-D0** | Roadmap + locked decisions (this file) + machine-readable manifest [`data/manifest/datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) + spine/hub registration (PROJECT_INTERLINKS row, GTD wiring) | ✅ 06-07-2026 |
| **P-D1** | First public data release `data-v0.1.0`: mw_roots · mw_etymology · dcs_cdsl_xref · union_headwords · mw_heritage_crosswalk · lemma_frequency · headword_index (all already public in their source repos; CC BY-SA 4.0 per [`LICENSE-DATA.md`](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md)) | ✅ 06-07-2026 |
| **P-D2** | Restricted-tier backup of the 19.2 GB local-only census giants (private storage; the 11 GB `archive_stopword.sqlite` needs split-or-exclude ruling) — kills the single-copy risk | 🟡 H233 |
| **P-D3** | Public **Sanskrit NLP data + tools directory** page on the kosha site (our datasets + external stacks), from FEATURES_INDEX/REUSE_INDEX/SAMSAADHANII_INDEX content | ✅ 06-07-2026 (H236) — [`directory/`](https://gasyoun.github.io/kosha/directory/), rendered by [`scripts/build_directory.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_directory.py) from [`datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) + [`external_tools.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json); schema.org `Dataset` JSON-LD per public asset |
| **P-D4** | samskrtam.ru canonical hosting: upload public-tier files, manifest URLs flip from GitHub Releases to server; restricted tier gets a non-public server path | ⛔ MG deploy gate (GTD @DO) |
| **P-D5** | Queryable-DB integration: the manifest's join-table assets ingested into `kosha.db` as attached layers (frequency already done — DCS M9 pattern); one SQLite an agent can query cross-asset | 🟡 after P-D2 |
| **P-D6** | API tier: C-SALT/Kosh-style dataset endpoints on the kosha API, csl-apidev alignment | 🟡 after P-D4 |

## Rules

- **Every changed/new derived dataset ends its session with a manifest row** — a
  deliverable that isn't in `datasets.json` doesn't exist for reuse purposes (this is
  the anti-"one-shot deliverable" enforcement, D-HUB-2c).
- **Public tier only via `/publish-safety-check`** — rights-encumbered assets are
  restricted-tier, no exceptions (D-HUB-6).
- **Release tags are `data-vX.Y.Z`**, separate from kosha code versions; data license
  is CC BY-SA 4.0 (`LICENSE-DATA.md`), never the code license.
- Citation durability rule (RISKS.md R1/R5) applies: manifest `canonical_url`s may point
  at samskrtam.ru, but citation/DOI-facing URLs must survive a server move — DOIs (P-D4+)
  attach to versioned releases, not to the live server.

_Dr. Mārcis Gasūns_
