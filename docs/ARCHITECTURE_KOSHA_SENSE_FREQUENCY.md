# ARCHITECTURE — kosha sense-frequency layer

_Created: 22-07-2026 · Last updated: 22-07-2026_

Index: [PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md).

## The crosswalk chain

```
DCS token  ──(WordSem MISC key)──►  Sanskrit-WordNet synset_id
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
             LAYER 1: WN synset    LAYER 2: MW sense     LAYER 3: semdom domain
             (native gold,        (via WN→MW bridge,     (via WN→semdom /
              lossless)            kosha `senses`)        semdom-amarakosha xwalk)
```

Every corpus token that carries a `WordSem` tag contributes **one count to each of the three layers**
(the token's synset maps up to exactly one MW sense candidate and one semdom domain, where the crosswalk
resolves). Frequencies are counted on the native synset first (no loss), then aggregated up the two
projections — so a projection's coverage/ambiguity is always measurable against the synset ground truth.

## Data model — `data/frequency/sense_frequency.tsv`

Long format, one row per (lemma, layer, sense, period-bucket collapsed into a vector), mirroring
`lemma_frequency.tsv`:

| column | meaning |
|---|---|
| `lemma_slp1` | join key (SLP1, sanskrit-util-normalised) — same key as `lemma_frequency.tsv` |
| `layer` | `wn` \| `mw` \| `semdom` |
| `sense_id` | WN synset id / kosha `senses.sense_id` / semdom domain id, per layer |
| `sense_gloss` | short gloss for display (from the decode inventory / kosha `senses` / semdom label) |
| `count_all` | whole-corpus attested token count for this sense |
| `sense_rank` | dense rank of this sense **within its lemma**, by `count_all` desc (1 = dominant sense) |
| `lemma_share` | `count_all` / Σ counts over the lemma's senses in this layer (the dominance ratio) |
| `periods` | pipe-joined `period=count` vector, same period order as `lemma_frequency` |
| `provenance` | `attested` (WordSem gold) \| `estimated` (wave-2 WSD) |
| `confidence` | null for `attested`; wave-2 fills for `estimated` |

Sidecar rule (identical to lemma-frequency): **not a materialised column** — kosha's card build
LEFT-JOINs `sense_frequency` onto `senses` at build time, keeping the asset independently rebuildable.

## Companion artefacts

- `data/frequency/wordsem_inventory.tsv` — the recovered decode table (synset_id → gloss → WN lemma). The
  keystone; without it Layer 1 has ids but no meanings.
- `data/frequency/wn_to_mw_map.tsv` — WN synset → kosha `senses.sense_id`, with a `match_type`
  (exact-gloss / lemma+gloss-overlap / unresolved). Built from the reused MW→WordNet bridge.
- `data/frequency/dcs_mw_sense_order_delta.md` — the decision-#3 finding report.

## Components (wave-1)

| Component | File | Reads | Writes |
|---|---|---|---|
| Decode recovery | `data/frequency/build_wordsem_inventory.py` | DCS CoNLL-U releases | `wordsem_inventory.tsv` |
| WN→MW crosswalk | `data/frequency/build_wn_mw_map.py` | `wordsem_inventory.tsv`, kosha `senses` | `wn_to_mw_map.tsv` |
| Sense-frequency build | `data/frequency/build_sense_frequency_layer.py` | VisualDCS WordSem tokens, the two maps, semdom-amarakosha xwalk | `sense_frequency.tsv`, `.meta.json` |
| Order-delta report | `data/frequency/build_sense_order_delta.py` | `sense_frequency.tsv` (mw layer), kosha `senses` order | `dcs_mw_sense_order_delta.md` |
| Card wiring | kosha card build (locate existing lemma-frequency join site) | `sense_frequency.tsv` | rendered cards |

## Build-vs-reuse (see PLAN for the full table)

Everything except the four thin build scripts above and the card-badge markup is **reuse**. The scripts
are joiners/counters over existing assets — no analyzer, no morphology, no transcoder is built (SCL +
`vidyut` + `sanskrit-util` already own those).

## Source-of-truth notes / traps

- WordSem is on **219/270 texts**; the 29 "went-Vedic" 2026 texts arrived with **zero** WordSem
  ([SL FINDINGS §11 addendum](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md)).
  Filter on the `WordSem` MISC key per text; never assume a text is sense-tagged.
- The stub `dcs_full.sqlite` reports only 9.3% `m_wordsem`
  ([SL FINDINGS §78](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md)) — an
  undercount. Prefer the CoNLL-U releases, which are the richer WordSem source.
- Homonymy vs polysemy: WhitneyRoots
  ([`token_attribution.json`](https://github.com/gasyoun/WhitneyRoots/blob/main/crosswalk/token_attribution.json))
  already splits **homonym** tokens (different lemmas, same spelling) by DCS `lemma_id`+gloss. This layer
  handles **polysemy** (senses within one lemma). Keep the two axes distinct; cite WhitneyRoots for the
  homonym split rather than re-deriving it.
- ⚠ Upstream UD `Tense=Past` conflates aorist/perfect (existing lemma-frequency caveat) — inherited, note
  in the data-statement.

_Dr. Mārcis Gasūns_
