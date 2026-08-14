# Architecture — kosha `/w/` language groups and RU join

_Created: 13-08-2026 · Last updated: 14-08-2026_

## Chrome

Two levels:

1. **Language:** EN | DE | RU | All
2. **Inside a language:** the dicts of that language
   - EN: MW, AP90
   - DE: PWG
   - RU: pwg_ru, mw_ru
3. **All** (H2653) remains a fourth **top-level** control and stacks every
   dictionary of every language.

First paint: EN, unless SSR `Accept-Language` contains `ru` or (on static
Pages) `navigator.language` starts with `ru`.

## Data

- **Reuse:** `render_word_page` in
  [app/word_page.py](https://github.com/gasyoun/kosha/blob/main/app/word_page.py).
  Extend `DICT_ORDER` / labels; do not fork a second template.
- **Join:** at request (SSR) or build (static) time, look up lemma keys in a
  sibling `SanskritLexicography/RussianTranslation` tree. Path on `.92`:
  clone next to `/opt/kosha/repo` if missing. CI: committed **fixture**
  slice only.
- **Empty-state:** if the sibling or key is missing, the RU inner tab still
  exists and says so in one line.
- **Badge:** unreviewed store rows show **AI-translated**. Do not flip
  `review_status` in the translation store.
- **SanskritRussian strip (W-RU-2 / H2680):** the public glossary already
  used by reading packs. One `<p class="saru-strip">` under the headword
  (lemma, then surface). Honest miss line when the public files miss.
  Not a third dictionary tab.

## Build-vs-reuse

| Piece | Verdict |
|---|---|
| Word-page template | Reuse `word_page.py` |
| pwg_ru / mw_ru text | Reuse sibling stores; do not copy |
| SanskritRussian glossary | Reuse public site-tier files |
| Archive tree | Snapshot live DB version; do not invent a new data_version |
| Rollback | Follow [KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DEPLOYMENT.md) Part IV |

_Dr. Mārcis Gasūns_
