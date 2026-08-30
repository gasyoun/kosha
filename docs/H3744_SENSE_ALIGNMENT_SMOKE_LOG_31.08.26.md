# Smoke log — H3744 aligned-sense staging surface

_Created: 31-08-2026 · Last updated: 31-08-2026_

Produced by [scripts/smoke_sense_alignment.py](https://github.com/gasyoun/kosha/blob/main/scripts/smoke_sense_alignment.py)
(`file://`, Chromium headless, viewports 375 / 1280 px, no network).

**31/31 checks pass.**

| check | result | detail |
|---|---|---|
| nAgadanta has exactly 2 aligned meanings | ✅ PASS | got 2 |
| PWG a〉 Elephantenzahn is aligned | ✅ PASS | m. elephant's tusk or ivory |
| …to MW 'elephant's tusk', on witness mbh | ✅ PASS | mbh / m. elephant's tusk or ivory |
| PWG b〉 Pflock in der Wand is aligned | ✅ PASS | a peg in the wall to hang things upon |
| …to MW 'peg in the wall', on witness panc (PAÑCAT. ≡ Pañc.) | ✅ PASS | panc / a peg in the wall to hang things upon |
| the two meanings are NOT merged (tusk ≠ peg row) | ✅ PASS | nAgadanta#1 vs nAgadanta#2 |
| every failure row carries a class from the documented taxonomy | ✅ PASS | absent-dictionary, cross-language-gap, no-gloss, no-shared-witness, witness-too-common |
| unaligned senses are kept in the table, not dropped | ✅ PASS | 26412 rows |
| every aligned row states its method and score | ✅ PASS |  |
| no aligned row is single-dictionary (shape has ≥2 non-zero) | ✅ PASS |  |
| no docs/ (Pages) artifact carries the aligned-sense organ | ✅ PASS | 0 files |
| dist\sense-align-staging/NOT_PUBLISHED.md present | ✅ PASS |  |
| dist\w-staging\a/NOT_PUBLISHED.md present | ✅ PASS |  |
| docs/NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md present | ✅ PASS |  |
| public render (ux=None) contains NO aligned-sense block | ✅ PASS |  |
| live-shaped render (ux={'variant':'a'}) contains NO aligned-sense block | ✅ PASS | the gate is the explicit key, not ux truthiness |
| staging render (ux + sense_align) DOES contain it | ✅ PASS |  |
| staged viewer @375px — 0 console/page errors | ✅ PASS |  |
| staged viewer @375px — table has rows | ✅ PASS | 6 rows |
| staged viewer @375px — नागदन्त tusk row rendered | ✅ PASS |  |
| staged viewer @375px — नागदन्त peg row rendered | ✅ PASS |  |
| staged viewer @375px — failure classes visible on the page | ✅ PASS |  |
| staged viewer @1280px — 0 console/page errors | ✅ PASS |  |
| staged viewer @1280px — table has rows | ✅ PASS | 6 rows |
| staged viewer @1280px — नागदन्त tusk row rendered | ✅ PASS |  |
| staged viewer @1280px — नागदन्त peg row rendered | ✅ PASS |  |
| staged viewer @1280px — failure classes visible on the page | ✅ PASS |  |
| word page padma (ux=a) @375px — 0 console/page errors | ✅ PASS |  |
| word page padma (ux=a) @375px — table has rows | ✅ PASS | 6 rows |
| word page padma (ux=a) @1280px — 0 console/page errors | ✅ PASS |  |
| word page padma (ux=a) @1280px — table has rows | ✅ PASS | 6 rows |

Reproduce:

```bash
python scripts/build_sense_alignment.py
python scripts/build_word_pages.py --ux-staging a --tokens padma,kAla,citra,amfta,vftta,vajra,satya,go,arka,sAra
python scripts/smoke_sense_alignment.py --log docs/H3744_SENSE_ALIGNMENT_SMOKE_LOG_31.08.26.md
```

_Dr. Mārcis Gasūns_
