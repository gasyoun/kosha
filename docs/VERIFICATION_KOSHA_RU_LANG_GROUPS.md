# Verification — kosha RU language groups and ops leftovers

_Created: 13-08-2026 · Last updated: 14-08-2026_

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
| Tests | `python -m pytest tests/test_word_page.py tests/test_word_page_all_tab.py tests/test_word_page_lang_groups.py tests/test_word_page_saru_strip.py -q -p no:cacheprovider` |
| Live | `https://samskrtam.ru/w/BU` shows a SanskritRussian public-tier gloss line under the headword when the lemma hits |
| Rights | only public site-tier files; `corpus_lexicon` never read |

**Fail:** a third dictionary tab; restricted bulk layers copied into kosha.

## H2681 (Codex W0 memo)

| Criterion | Proof |
|---|---|
| Memo | [committed under `kosha/docs/`](https://github.com/gasyoun/kosha/blob/main/docs/REVIEW_KOSHA_W0_H1944_H1945_CODEX_2026.md) in [PR #399](https://github.com/gasyoun/kosha/pull/399) |
| Comments | posted on [H1944 / #215](https://github.com/gasyoun/kosha/pull/215#issuecomment-5297808328) and [H1945 / #224](https://github.com/gasyoun/kosha/pull/224#issuecomment-5297808587) |
| No silent patch | no product code changed; the one open P2 was routed to H2768 (Codex) — Resolve kosha extension on strict Salt compatibility faces |
| Gate | no open P0/P1; 188 passed / 30 skipped in the focused W0 suite |

## Risks

- Sibling clone on `.92` is large; clone once, document the path.
- Language chrome can break All-tab tests; run both suites.
- Rollback can leave the unit down — halt after two failed restores on the
  last known-good tree.

_Dr. Mārcis Gasūns_
