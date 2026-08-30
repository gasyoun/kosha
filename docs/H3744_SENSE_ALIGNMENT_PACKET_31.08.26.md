# H3744 — the aligned-sense table (PWG · MW · Apte): design, evidence, limits

_Created: 31-08-2026 · Last updated: 31-08-2026_

Handoff: [H3744 (Opus 5, 🔴3 hard) — sense-reconciliation W2 slice 1: PWG/MW/Apte
aligned-sense table, staged behind `ux=` with a published compare
page](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3744-Opus_kosha_sense-recon-w2-aligned-sense-table_30.08.26.md)
· executor Opus 5 (`claude-opus-5`) · design record
[PLAN_KOSHA_IMPROVEMENT_SET_2026-08-30.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_IMPROVEMENT_SET_2026-08-30.md)
· source of record
[ROADMAP_KOSHA_SENSE_RECONCILIATION_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_SENSE_RECONCILIATION_2026H2.md)
§ Wave 2.

**Compare page (published, the thing to look at):**
[gasyoun.github.io/h3744-sense-align/](https://gasyoun.github.io/h3744-sense-align/)

## 1. Scope fences — stated so a later session cannot re-scope quietly

- **IN** — PWG, MW, Apte (`ap90`) only.
- **OUT** — the Sa→Sa dictionaries (ŚKDR / Medinī / VCP / Amara): a deliberate second slice.
- **OUT** — the lemma-variant graph (`nAgadanta`↔`nAgadantaka`-class normalisation).
- **OUT** — wave 2's second acceptance pass: it needs a review sheet and a human vote,
  which contradicts `{launch-box: any}`. **Nothing here has passed it.**
- **OUT** — the `pwg_ru` RU-sense-structure deliverable: its own handoff.
- **NOT PUBLISHED** — the table is not on the 2,324 live static pages.
  Contract: [NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md](https://github.com/gasyoun/kosha/blob/main/docs/NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md).

## 2. The problem this wave had to solve first

The handoff called this the hard unit because the row model was unknown before
someone started. It was unknown for a specific reason: **the three dictionaries
share neither a sense granularity nor a metalanguage.** PWG glosses in German,
MW and Apte in English. The obvious signal — gloss overlap — is structurally
unavailable across exactly the boundary the wave exists to cross, and the
existing pilot view
([sense_crossdict_pilot.tsv](https://github.com/gasyoun/kosha/blob/main/data/concordance/sense_crossdict_pilot.tsv),
H1587) said so in its own `note` column on every row: *"MW/Apte columns are
inventory not sense-aligned."* Three columns side by side is not an alignment.

## 3. The bridge: shared literary witness, weighted

Both traditions cite their sources per sense, in `<ls>`. The canonical case, in
the data:

| | gloss | cites |
|---|---|---|
| PWG `nAgadanta` 1〉a〉 | *Elephantenzahn, Elfenbein* | `H. an. 4,111` · `MED. t. 203` · **`MBH. 12,3630`** |
| MW L104994 | elephant's tusk or ivory | **`MBh.`** |
| PWG `nAgadanta` 1〉b〉 | *Pflock in der Wand zum Anhängen von Sachen* | `H. 1011` · **`PAÑCAT. 116,19`** |
| MW L104995 | a peg in the wall to hang things upon | **`Pañc.`** · `Kathās.` |

The tusk↔peg split — the whole point of the
[नागदन्त thread](https://groups.google.com/g/nagari/c/NOWqiBQl1Xc/m/_R8O4-39CAAJ) —
is recoverable from the citations alone, in any pair of languages.

Three things make it a method rather than a coincidence:

1. **Abbreviation normalisation.** `MBH. 12,3630` and `MBh.` both key to `mbh`;
   `PAÑCAT.` folds onto `Pañc.` because one extends the other. Folding is
   refused below four characters — at two, `R.` (Rāmāyaṇa) is a prefix of `RV.`
   (Ṛgveda) and folding them would invent a witness.
2. **Weighting.** A shared `MBh.` says almost nothing when every sense of the
   lemma cites `MBh.`, and a great deal when nothing else does. Each witness
   weighs `1/df`, df counted **within the lemma** across all three dictionaries.
   A witness unique to one sense on each side scores 0.5; one spread over six
   senses scores 0.167 and cannot carry a row alone.
3. **Gloss overlap is fenced to English.** MW↔Apte Jaccard is used (Apte often
   reprints MW's wording, so it is strong there); it is never let across the PWG
   boundary, where it would silently measure nothing.

## 4. The row model

**One row = one meaning**, not one sense. Columns:

`lemma_slp1 · group_id · status · shape · method · score · witnesses · flags ·
failure_class · pwg_sense_ids · pwg_gloss · mw_sense_ids · mw_gloss ·
apte_sense_ids · apte_gloss · note`

`shape` is the `pwg-mw-apte` sense count of the row (`1-1-1`, `1-1-0`, `0-1-2`),
which is how sense-granularity mismatch becomes visible instead of being
smoothed away. Unaligned senses stay in the table as `1-0-0`-shaped rows with a
`failure_class`; they are the record, not the residue.

**Grouping is best-match, not reachability — and this was the one real design
reversal of the build.** Transitive closure over surviving edges was implemented
first and produced blobs: `amṛta`'s MW and Apte senses all cite RV/MBh and all
share wording, so a single component swallowed *not dead*, *nectar* and *N. pr.
the mother of Parikṣit* and presented them as one meaning — a false claim in the
shape of a row. Each sense now takes at most **one** partner per other
dictionary, its best-scoring one; a losing candidate is recorded as `outranked`
rather than absorbed. Three-dictionary rows went from unreadable blobs to **262
clean `1-1-1` rows**, and the largest surviving group is `2-2-2` (two of them).

## 5. Numbers (pilot, 500 headwords)

| metric | value |
|---|---:|
| senses considered | 33,763 |
| meaning groups (table rows) | 30,470 |
| **aligned groups** | **2,957** (9.7 % of rows) |
| lemmas with ≥1 aligned meaning | 477 / 500 |
| lemmas present in all three dictionaries | 273 |
| clean three-dictionary rows (`1-1-1`) | 262 |
| PWG-crossing rows (`1-1-0` / `1-0-1` / `1-1-1` …) | 1,433 |

Marked defaults, all logged: `TAU = 0.30` · `GLOSS_FLOOR = 0.20` ·
`PREFIX_MIN = 4`.

9.7 % of rows is a low number and an honest one: the method is strict, and
everything it cannot align stays visible with its reason attached rather than
being dropped to flatter the ratio. Full counts, shapes and methods:
[SENSE_ALIGNMENT_BUILD_REPORT.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/SENSE_ALIGNMENT_BUILD_REPORT.md).

## 6. Failure classes — the deliverable, not the excuse

| class | senses | why it is not a bug |
|---|---:|---|
| `no-shared-witness` | 17,671 | the sense cites sources; no cross-dictionary sense of the lemma cites any of them |
| `witness-too-common` | 6,844 | shared witnesses exist but weigh below τ — real citation, no discriminating power |
| `no-gloss` | 3,025 | a structural chunk (PWG `<div>` carrying only `<lex>m.</lex>`); excluded before alignment |
| `cross-language-gap` | 1,835 | a PWG sense with **no `<ls>` at all** — the bridge does not exist for it, and German→English gloss overlap measures nothing. A structural ceiling, not a tuning knob |
| `outranked` | 1,101 | a qualifying partner preferred a better-scoring sense |
| `absent-dictionary` | 62 | the lemma has no entry in the others |

Per-sense rows:
[sense_alignment_failures.tsv](https://github.com/gasyoun/kosha/blob/main/data/concordance/sense_alignment_failures.tsv).

### 6a. And the failures that do NOT announce themselves

A false positive looks exactly like a true one. From this build, on `amfta`:
PWG *N. pr. Mutter von Parikṣit* was matched to MW *not dead* / Apte *Not dead*
on `mbh`. The MW↔Apte half of that row is right; the PWG half is wrong — a
proper name and a negated adjective are not one meaning. It is visible on the
published compare page, deliberately left there.

**No precision figure is quoted anywhere in this wave.** Measuring the rate of
such rows is the wave-2 acceptance pass — sample, judge, `/review-sheet` human
vote — which is explicitly out of this slice's scope. An unmeasured number would
be worse than the stated gap.

## 7. Where it renders, and why not on the live pages

| surface | path | how it is gated |
|---|---|---|
| word-page organ | `dist/w-staging/a/w/*.html` | `ux={"sense_align": True}`, set only by `--ux-staging` |
| standalone viewer | `dist/sense-align-staging/index.html` | `dist/` is gitignored; the writer refuses any path under `docs/` |
| compare page | [gasyoun.github.io/h3744-sense-align/](https://gasyoun.github.io/h3744-sense-align/) | published on purpose |

**Truth-fix found while building** (it changed the gate): H3457's `NOT_PUBLISHED`
marker was *deleted* when MG published that layer on 26-08-2026 (commit
`070050a`), and all 2,324 live `/w/` pages now carry its organs. So `ux=` being
truthy is **no longer** a non-publication gate — an organ hung on plain `ux`
truthiness would ship on the next live rebuild. The aligned-sense organ
therefore rides its own explicit key, and a test asserts that a live-shaped
`ux={"variant": "a"}` render contains no `sense-align` markup.

The reason for the fence itself is not caution for its own sake: the live pages
present dictionary text **verbatim**, and kosha asserts nothing beyond having
reprinted it. This table asserts, in kosha's own voice, that *this* PWG sense
and *that* MW sense are the same meaning — a lexicographic claim that can be
scholarly wrong in a way a frequency badge or a favourites heart never can.

## 8. Evidence

- Smoke, **31/31 pass**, both surfaces × 375/1280 px, zero console errors:
  [H3744_SENSE_ALIGNMENT_SMOKE_LOG_31.08.26.md](https://github.com/gasyoun/kosha/blob/main/docs/H3744_SENSE_ALIGNMENT_SMOKE_LOG_31.08.26.md)
  ([scripts/smoke_sense_alignment.py](https://github.com/gasyoun/kosha/blob/main/scripts/smoke_sense_alignment.py)).
- Unit tests, **26 pass**, no `kosha.db` needed:
  [tests/test_sense_alignment.py](https://github.com/gasyoun/kosha/blob/main/tests/test_sense_alignment.py)
  — the नागदन्त tusk↔peg case in miniature, the `r`/`rv` folding refusal, the
  "a witness shared by everything carries no edge" case, and the three-render
  publication fence.
- Build report with every count, shape and marked default:
  [SENSE_ALIGNMENT_BUILD_REPORT.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/SENSE_ALIGNMENT_BUILD_REPORT.md).
- Manifest row `sense-alignment-pilot` in
  [data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).

## 9. Reproduce

```bash
python scripts/build_sense_alignment.py
python scripts/build_word_pages.py --ux-staging a --tokens padma,kAla,citra,amfta,vftta,vajra,satya,go,arka,sAra
python scripts/smoke_sense_alignment.py --log docs/H3744_SENSE_ALIGNMENT_SMOKE_LOG_31.08.26.md
python scripts/build_sense_align_compare.py --out ../gasyoun.github.io/h3744-sense-align
```

`build_sense_alignment.py` needs `kosha.db` (gitignored; it falls back to the
main clone beside the worktree). Everything downstream of the committed TSV —
the organ, the tests, the compare page — does not.

## 10. What the next slice should take, in order

1. **Sa→Sa dictionaries** (ŚKDR / Medinī / VCP / Amara) as further columns. The
   row model already carries per-dictionary cells; adding a fourth is a loader,
   not a redesign. Note that ŚKDR/Medinī are cited *by* PWG, so they arrive with
   the witness bridge already pointing at them.
2. **The acceptance pass** — a sample of aligned rows, an LLM judge, a
   `/review-sheet` vote. Until it runs, precision is unknown, and this packet
   says so rather than guessing.
3. **The lemma-variant graph**, which would let `nAgadanta` and `nAgadantaka`
   share a witness pool and would fix the homonym-blind `df`.

_Dr. Mārcis Gasūns_
