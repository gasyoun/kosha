# NOT PUBLISHED — H3744 aligned-sense table (PWG · MW · Apte)

_Created: 31-08-2026 · Last updated: 31-08-2026_

Same posture as the H3457 word-page UX staging wave, different reason. H3457's
staging was about taste — where a badge sits. This one is about a **claim**.

**A truth-fix found while building this** (it changes the gate): H3457's
`NOT_PUBLISHED` marker was *deleted* when MG published that layer on 26-08-2026
(commit `070050a`), and all **2,324** live `/w/` pages now carry its organs. So
`ux=` being truthy is **no longer** a non-publication gate — anything hung on
mere `ux` truthiness ships the next time the live tree is regenerated. The
aligned-sense organ therefore rides an explicit `ux={"sense_align": True}` key
that only `scripts/build_word_pages.py --ux-staging` ever sets.

## What is staged

The cross-dictionary aligned-sense table built by
[scripts/build_sense_alignment.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_sense_alignment.py)
(algorithm: [app/sense_align.py](https://github.com/gasyoun/kosha/blob/main/app/sense_align.py)),
rendered on two surfaces, neither of them public:

| surface | path | gate |
|---|---|---|
| word-page organ | `dist/w-staging/<variant>/w/*.html` | `ux={"sense_align": True}` — set only by `--ux-staging`; neither `ux=None` nor a plain `ux={"variant": …}` live build can reach it |
| standalone viewer | `dist/sense-align-staging/index.html` | `dist/` is gitignored; the writer refuses any path under `docs/` |
| compare page (before/after) | [gasyoun.github.io/h3744-sense-align/](https://gasyoun.github.io/h3744-sense-align/) | published deliberately — see below |

## Why this one is not on the live pages

The 2,324 live static pages present dictionary text **verbatim**: MW says what MW
says, PWG what PWG says, and kosha asserts nothing beyond having reprinted it.
An aligned-sense table breaks that: it asserts that *this* PWG sense and *that*
MW sense are the same meaning. That is a lexicographic claim in kosha's own
voice, and it can be **scholarly wrong** — wrong in a way page chrome, a badge
or a favourites heart never can be. A reader who trusts the printed columns
would have no way to tell which part of the page is Cologne and which part is us.

So the alignment ships where it can be looked at and argued with, and does not
ship where it would be read as the dictionaries' own claim. The publication call
is a human's, made by looking at the compare page — not by reading a packet.

## The compare page IS published, and that is not a contradiction

[gasyoun.github.io/h3744-sense-align/](https://gasyoun.github.io/h3744-sense-align/)
shows the current word page beside the staged one, framed as a proposal, on the
vote hub — the same shape as
[h3457-compare](https://gasyoun.github.io/h3457-compare/). It carries no claim
of being the dictionary; it carries a request for a ruling. Publishing the
question is not publishing the answer.

## What would lift the fence

A human ruling on the compare page, plus — for anything beyond the pilot — the
wave-2 **second acceptance pass**: a sample, an LLM judge and a `/review-sheet`
human vote. That pass is explicitly **out of scope** for H3744 (it needs a human
vote, which contradicts `{launch-box: any}`), so nothing in this wave may be
read as having cleared it.

## Scope fences (restated so a later session cannot re-scope quietly)

- **IN** — PWG, MW, Apte (ap90) only.
- **OUT** — the Sa→Sa dictionaries (ŚKDR / Medinī / VCP / Amara): a deliberate second slice.
- **OUT** — the lemma-variant graph (`nAgadanta`↔`nAgadantaka`-class normalisation).
- **OUT** — wave 2's second acceptance pass.
- **OUT** — the `pwg_ru` RU-sense-structure deliverable (its own handoff).

## Mechanical guards (not just prose)

1. `scripts/build_sense_alignment.py` exits with an error if its staging root
   resolves under `docs/`.
2. `app/word_page.py` reaches the organ only when `ux.get("sense_align")` is
   set — neither the public prerender path nor a plain `ux` live build
   evaluates it.
3. `tests/test_sense_alignment.py` asserts that neither the `ux=None` render nor
   a plain `ux={"variant": "a"}` render carries any `sense-align` markup.
4. [scripts/smoke_sense_alignment.py](https://github.com/gasyoun/kosha/blob/main/scripts/smoke_sense_alignment.py)
   greps the whole `docs/` tree for the organ on every run.

_Dr. Mārcis Gasūns_
