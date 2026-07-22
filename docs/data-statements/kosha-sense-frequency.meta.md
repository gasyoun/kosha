# Data statement — DCS per-sense frequency sidecar (`kosha-sense-frequency`)

_Created: 22-07-2026 · Last updated: 22-07-2026_

Data statement for the `kosha-sense-frequency` dataset served by the kosha
data-hub. Manifest row:
[data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).
The wave-1 sidecar to
[`kosha-lemma-frequency`](https://github.com/gasyoun/kosha/blob/main/docs/data-statements/kosha-lemma-frequency.meta.md):
that gives per-**lemma** frequency, this gives per-**sense** frequency
("частотность значений") — how often each numbered meaning of a word is
actually attested.

## Composition & counts

103,079 rows, long format, one per `(lemma_slp1, layer, sense_id)`, counted on
the DCS **WordSem** annotation (Sanskrit-WordNet synset gold, present on 219/270
texts corpus-wide; 531,747 sense-tagged tokens = 9.3% of the corpus). TSV, UTF-8,
10 columns:

| Column | Content |
|---|---|
| `lemma_slp1` | lemma, SLP1 (same join key as `lemma_frequency.tsv`) |
| `layer` | `wn` (native Sanskrit-WordNet synset) · `mw` (MW numbered sense) · `semdom` (WordNet lexicographer supersense) |
| `sense_id` | synset id (`wn`) · `<lemma>#<mw_ord>` (`mw`) · supersense name (`semdom`) |
| `sense_gloss` | short display gloss for the sense |
| `count_all` | whole-corpus attested token count for this sense |
| `sense_rank` | dense rank of the sense within its lemma+layer, by `count_all` desc (1 = dominant) |
| `lemma_share` | `count_all` ÷ Σ over the lemma's senses in this layer (the dominance ratio) |
| `n_texts` | document frequency — distinct DCS texts attesting this (lemma, sense) |
| `dispersion_dp` | Gries Deviation of Proportions over texts (0 = even, →1 = bursty/concentrated) |
| `largest_text_share` | fraction of the sense's tokens in its single biggest text (burstiness diagnostic) |
| `count_adj` | dispersion-adjusted count = `count_all` × (1 − `dispersion_dp`) — discounts genre-concentrated senses |
| `sense_rank_adj` | dense rank within lemma+layer by `count_adj` (the de-biased sense order) |
| `periods` | per-period vector — **empty in wave-1** (see limitations) |
| `provenance` | `attested` (WordSem gold) on every wave-1 row; `estimated` is reserved for wave-2 WSD |
| `confidence` | null for `attested`; wave-2 fills it for `estimated` rows |

Rows by layer: `wn` 57,143 · `mw` 23,088 · `semdom` 22,848. The native `wn`
layer is lossless; the `mw` and `semdom` layers are projections whose coverage is
measurable against it (Layer 2 reaches 68.8% of WordSem tokens, Layer 3 51.2%).

Companion artefacts in the same folder:
[`wordsem_inventory.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/wordsem_inventory.tsv)
(the recovered synset→gloss decode, 23,920 synsets),
[`wn_to_mw_map.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/wn_to_mw_map.tsv)
(synset→MW sense, with `match_type`), and
[`dcs_mw_sense_order_delta.md`](https://github.com/gasyoun/kosha/blob/main/data/frequency/dcs_mw_sense_order_delta.md)
(the DCS-vs-MW sense-order finding).

## Source provenance

Derived in [gasyoun/kosha](https://github.com/gasyoun/kosha)
(`data/frequency/build_sense_frequency_layer.py`) by joining three existing
assets, none re-derived:

- **Attestation** — the DCS `WordSem` synset per token, from
  [`dcs_full.sqlite`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  `token.m_wordsem` (the canonical VisualDCS CoNLL-U ingest; the sqlite is the
  lossless ingested form of the same CoNLL-U releases — re-parsing the 15,901
  files is explicitly discouraged by the manifest).
- **Decode** — the synset→gloss inventory recovered from the DCS CoNLL-U
  distribution's `conllu/lookup/word-senses.csv`, the table the stub sqlite
  lacked ([SL FINDINGS §78](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md)).
- **MW numbered senses** — kosha's own
  [`kosha.db`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  `senses` (692,403 senses), matched to synsets by English gloss-overlap.
- **Semantic domain** — the WordNet lexicographer supersense (26 categories),
  propagated down the WordNet hypernym tree (`sembank-relations.csv`).

## Curation rationale

The corpus records which *sense* of a polysemous word is attested (via WordSem
gold), but that signal sat un-decoded — a bare synset id with no gloss table
([SL FINDINGS §78](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md)).
This sidecar freezes one canonical per-sense frequency so consumers (kosha cards,
[`mfs_baseline.py`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/mfs_baseline.py),
A58) LEFT-JOIN it rather than re-deriving sense disambiguation. It is a
**sidecar**: kosha's card build LEFT-JOINs it onto `senses` at build time; the
canonical MW/kosha senses are never overwritten.

## Language variety

Sanskrit (ISO 639-3 `san`) as sampled by DCS, restricted further to the 219
WordSem-tagged texts — a *subset* of the corpus with its own genre skew (the
sense-tagged texts over-represent śāstra/lexical works such as rasaśāstra, which
inflates e.g. `rasa`'s "mercury" sense). Concept glosses and supersenses are
English (Princeton/Sanskrit-WordNet).

## Annotator / process information

Deterministic aggregation over DCS's expert WordSem annotation (Hellwig's
pipeline upstream). The one adjudicated step is the synset→MW-sense projection
(`wn_to_mw_map.tsv`), an English gloss-overlap match with a `match_type`
(`exact`/`overlap`/`unresolved`) on every row — a candidate assignment, not a
hand-verified gold label. No LLM-generated sense labels are in the table.

## Known biases & limitations

- **Gold, not estimate:** every wave-1 row is `provenance=attested` — it *is* the
  WordSem gold, so no disambiguation-accuracy is claimed. Full-corpus WSD
  (`estimated` rows) is wave-2.
- **9.3% token coverage:** only the 219 WordSem-tagged texts contribute; the 51
  untagged texts, including the 2026 Vedic wave, carry zero WordSem
  ([SL FINDINGS §11 addendum](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md)).
- **`periods` is empty in wave-1:** no clean per-token text→DCS-period map ships
  in the CoNLL-U release; the wave-2 path is `conllu/lookup/chapter-info.xml`
  `era`.
- **Layer-2 (MW) is a 68.8%-coverage projection:** unresolved tokens are counted
  only at the native `wn` layer. Layer-3 (semdom) is best-effort (51.2%); a null
  supersense means the token is counted at layers 1–2 only.
- **Layer 3 is the WordNet supersense**, native to the WordSem synset id-space —
  not the SIL-semdom A58 crosswalk (keyed by Amarakosha eid / Princeton WordNet,
  a different id-space); that projection is deferred.
- **Polysemy ≠ homonymy:** this counts senses *within* one lemma. The homonym
  axis (different lemmas, same spelling) is owned by WhitneyRoots
  [`token_attribution.json`](https://github.com/gasyoun/WhitneyRoots/blob/main/crosswalk/token_attribution.json).
- **Cross-source containment:** per-lemma Σ(`wn` count) ≤ `lemma_frequency`
  `count_all` holds for 24,151/24,169 checked lemmas (99.93%); the 18 residual
  excesses are DCS-vintage mismatches between the `dcs_full` token count and the
  Leonchenko lemma-frequency sheet, not senses out-counting the lemma.
- Upstream UD `Tense=Past` conflates aorist/perfect (inherited).
- **Corpus-composition bias — the load-bearing caveat, and the wave-1.5 partial
  correction.** DCS is *not* a balanced sample of Sanskrit: the WordSem-tagged subset
  over-represents rasaśāstra/āyurveda, so raw token frequency inflates genre-concentrated
  senses (`rasa` reads 51% "mercury"). This is the classic *domain-relativity of the
  predominant sense* — a word's most-frequent sense flips by corpus (McCarthy, Koeling,
  Weeds & Carroll, *Finding Predominant Word Senses in Untagged Text*, ACL 2004,
  [P04-1036](https://aclanthology.org/P04-1036/); Koeling, McCarthy & Carroll,
  *Domain-Specific Sense Distributions and Predominant Sense Acquisition*, HLT/EMNLP 2005,
  [H05-1053](https://aclanthology.org/H05-1053/)). **Wave-1.5** ships a genre-label-free
  partial correction as extra columns: `dispersion_dp` (Gries's Deviation of Proportions,
  *Dispersions and adjusted frequencies in corpora*, IJCL 13(4):403–437, 2008),
  `n_texts`, `largest_text_share`, and `count_adj = count_all × (1 − dispersion_dp)` with
  its own `sense_rank_adj`. This down-weights bursty senses (`rasa` mercury/juice gap
  narrows 1.74× → 1.47×; single-text artefacts like `artha` "sense" in 3 texts are crushed)
  but is **corpus-size-relative**, so it under-penalises concentration in *large*
  rasaśāstra texts. The fuller fix is **wave-2 genre-stratified post-stratification**
  (`p_balanced(s) = Σ_g w_g · P(s|g)` with a target `w_g`, not count-proportional — Little,
  *Post-Stratification*, JASA 1993; Biber, *Representativeness in Corpus Design*, 1993) plus
  Chan & Ng EM sense-prior re-estimation (*Estimating Class Priors in Domain Adaptation for
  WSD*, COLING-ACL 2006, [P06-1012](https://aclanthology.org/P06-1012/)). **Keep both
  numbers:** `count_all` is right for a reader *in* that genre (mercury really is dominant
  in rasaśāstra); `count_adj` for "Sanskrit generally".

## Intended use / known misuse

**For:** the kosha-cards "N in this sense · M for the lemma" display,
corpus-grounded most-frequent-sense baselines, the DCS-vs-MW sense-order study
(M01 Ch6), sense-weighted teaching order.
**Misuse:** reading a count as a disambiguation-accuracy figure (it is gold, not
a prediction); treating the `mw`/`semdom` projections as complete (report the
unresolved fraction); using it as a homonym splitter; reading Layer-2 dominance
as an MW-ordering defect (the sense-order delta is a corpus-usage finding, MW's
order is untouched).

## License

DCS-derived content: CC BY, attribution to Oliver Hellwig's Digital Corpus of
Sanskrit; released compilation under the public-tier terms in
[LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md)
(CC BY-SA 4.0 where CDSL-derived MW sense keys are joined in). WordNet glosses
are Princeton WordNet (WordNet 3.0 license).

## Maintenance & sunset plan

Rebuilt by `build_sense_frequency_layer.py` (via Steps 1–3 of the frequency
folder) when a new DCS snapshot is ingested; re-released at the next `data-v*`
cut. Each snapshot's file stays downloadable in its release for reproducibility.

## Deprecation status

`active` (wave-1).

## Citation

Cite the release: *Gasuns Sanskrit Dictionary data release* (CC BY-SA 4.0),
asset `sense_frequency.tsv`, with attribution to the Digital Corpus of Sanskrit
(Hellwig) and Princeton/Sanskrit WordNet. `CITATION.cff` + Zenodo DOI pending the
next `/cut-release` freeze.

## Provenance of this statement

Authored 22-07-2026 by Opus 4.8 (`claude-opus-4-8`) under handoff
[H1453](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1453-Opus_kosha_sense-frequency-wordsem-3layer-wave1_22.07.26.md),
from the build outputs, the `sense_frequency.meta.json` coverage counters, and
column inspection of the live files.

_Dr. Mārcis Gasūns_
