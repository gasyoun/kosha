# Data statement — Sanskrit root × preverb (upasarga) semantics

_Created: 13-07-2026 · Last updated: 13-07-2026_

**Dataset:** `sanskrit-upasarga-semantics` — how PREVERBS (upasarga) shift a verb
root's meaning: `√vac` "speak" → `pra-√vac` "declare"; `√as` "be" →
`sam-ni-√as` "renounce", `vi-ud-√as` "reject". A compositional dimension the
Cologne dictionaries are thin on.

**Vendored file:** [`data/gita/upasarga_semantics.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/upasarga_semantics.tsv)
(regenerate: [`scripts/extract_upasarga_semantics.py`](https://github.com/gasyoun/kosha/blob/main/scripts/extract_upasarga_semantics.py)).

**Source.** The `verbs` sheet of `SanskritGrammar/Concordance/Gita.xlsm` — the
roots attested in the Gītā with their base sense and preverb-modified senses.

**Fields.** `root · preverb · combined · sense · count` (`preverb` empty = the
base sense; `count` = the root's corpus frequency, on the base row).

**License.** **MIT**; public. Credit **Dr. Mārcis Gasūns**.

**Surfacing.** A standalone browsable page (`reading/upasarga/`) renders the
root → preverb → sense table. Deep integration as a panel on each `/w/` root
card is a documented follow-up (roadmap W6 note).

**Relation.** Roadmap **W6** —
[`ROADMAP_GITA_GOLD_EXTRACTION_2026.md`](https://github.com/gasyoun/kosha/blob/main/ROADMAP_GITA_GOLD_EXTRACTION_2026.md).

_Dr. Mārcis Gasūns_
