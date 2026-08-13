# Verification — kosha RU language groups and ops leftovers

_Created: 13-08-2026 · Last updated: 13-08-2026_

## H2670

| Criterion | Command / URL |
|---|---|
| Tests | `python -m pytest tests/test_word_page.py tests/test_word_page_all_tab.py tests/test_word_page_lang_groups.py -q -p no:cacheprovider` |
| Live | `https://samskrtam.ru/w/BU` shows EN/DE/RU + All; RU inner tabs exist |
| Locale | `Accept-Language: ru` selects RU on SSR |

**Fail:** German PWG dumped under RU; missing empty-state; Kochergina text.

## H2671

| Criterion | Proof |
|---|---|
| Pin exists | `/opt/kosha/archive` has a `0.1.0-dev` snapshot |
| Ready | `GET https://samskrtam.ru/ready` archives configured |
| Sense | one `.../sense/{id}@0.1.0-dev` (or documented pin) returns 200 |

## H2672

| Criterion | Proof |
|---|---|
| After restore | `/health` and `/ready` 200 |
| After re-promote | `/health` and `/ready` 200; unit left on **current** |

## H2680 (after H2670 on main)

| Criterion | Command / URL |
|---|---|
| Tests | pytest on the word-page suite plus a fixture that the strip is one line, not a tab |
| Live | `https://samskrtam.ru/w/BU` shows a SanskritRussian public-tier gloss line under the headword when the lemma hits |
| Rights | only public site-tier files; `corpus_lexicon` never read |

**Fail:** a third dictionary tab; restricted bulk layers copied into kosha.

## H2681 (Codex W0 memo)

| Criterion | Proof |
|---|---|
| Memo | committed under `kosha/docs/` |
| Comments | posted on the H1944 / H1945 PRs (or #215 if that is the review home) |
| No silent patch | defects named as follow-on, not fixed in the memo session |

## Risks

- Sibling clone on `.92` is large; clone once, document the path.
- Language chrome can break All-tab tests; run both suites.
- Rollback can leave the unit down — halt after two failed restores on the
  last known-good tree.

_Dr. Mārcis Gasūns_
