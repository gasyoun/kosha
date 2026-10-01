# H4026 — sense-dating badges LIVE: rendered proof (03-09-2026)

_Created: 03-09-2026 · Last updated: 03-09-2026_

Executor: OxAlpha (opencode / zai-coding-plan/glm-5.3-flash). Rendered with the
live build shape (`render_word_page(card, token, ux={"variant": "a", "sense_dating": True})`)
after the H4026 go-live changes — the exact pipeline `build_word_pages.py` now
runs by default.

## Proof files

| file | what to look at |
|---|---|
| `badges-live.padma.html` | PWG panel, sense **4〉** (part of a pillar) and **5〉** (temple form): citation `VARĀH. BṚH. S. 52,29` / `55,17` rides a green-ish **classical** chip inside its scan link (BṚhatsaṃhitā → classical via Dharmamitra, mode share 0.993). Caveat disclosure `dating-note` present (RU+EN). |
| `badges-live.han.html` | Verb root han: 1,162 badges, vedic present (the all-tie ṚV-floor senses); all **31 `SUŚR.` citations carry NO badge** — Suśruta is disputed → era NULL in the layer → no abbrev_map row → refusal, in both span and anchor form. |

## What changed for the go-live (H4026)

1. `app/dating_hydrate.py` — badge pass extended to the `<a class="ls ls-scan|ls-etext">`
   anchors `app/ls_hydrate.py` rewrites resolvable citations into (before this, the
   live path badged only the citations ls_hydrate could NOT link — padma 4/5 badge-zero),
   plus the continuation-citation `title` fallback (`<ls n="ṚV. 4,">22,9</ls>`).
   Never reverse-resolves a link URL — a linked continuation stays an honest miss.
2. `app/word_page.py` — the explicit `ux["sense_dating"]` key (H3744 doctrine) is now
   the PUBLISHED layer: badge hits are threaded to the page and the RU+EN caveat block
   (`_dating_caveat_block`) renders whenever ≥1 badge rendered. No-ux path byte-identical.
3. `scripts/build_word_pages.py` — live build default `ux` is now the published layer
   `{"variant": "a", "sense_dating": True}` (was `None` since H3457 published the
   organs only into the committed tree — a blind rebuild would have stripped them).
4. The committed `w/` tree (2,324 pages) regenerated with `--reading-packs --force`:
   1,818 pages carry ≥1 badge; organs byte-identical to the H3457 publish.

## Reproduce

```bash
python scripts/build_sense_dating.py --check          # parity: OK (11347 works, 278 abbrevs, 7349 senses)
python -m pytest tests/test_sense_dating.py -q        # 17 passed (incl. H4026 render gates)
python scripts/build_word_pages.py --reading-packs --force
grep -c "ls-era" w/_41_44i.html                        # a PWG-bearing page
```

## Scope note (measured, not assumed)

The handoff's "badges on sense entries wherever first_era is present" is surfaced
through the H4019-authored render contract: per-citation era badges from
`data/dating/abbrev_map.tsv` (the layer README names it "the render badge lookup").
A SENSE-keyed render of `sense_dating.tsv.first_era` was measured and NOT built:
the layer keys senses by the H1456 microstructure (slp1, hom, sense_id), while the
surface has no hom→entry mapping — 185 of 255 layer headwords with a committed card
have MULTIPLE PWG entries sharing one slp1 (e.g. padma L=42109 + L=77977), and
printed-marker fingerprints match several entries at once (amṛta: 3). A sense-keyed
badge would attach eras to the wrong homonym's senses — silently wrong data. The
per-citation badge cannot mis-attach: it keys on the citation's own abbreviation.

_Др. Мārcis Gasūns_

_Dr. Mārcis Gasūns_
