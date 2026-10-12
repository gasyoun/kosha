# A72 side-census — Kochergina label inventory (the Cyrillic leg)

_Handoff: H6461 · Census date: 13-10-2026 · Executor: OxAlpha (opencode/z-ai/glm-5.3-flash)_

## Mission and data

Label/abbreviation inventory of Kochergina's *Sanskritsko-russkij slovar'* derived
from the estate's digitized entry bodies — the B1-family source behind the
`kochergina-corpus-concordance` dataset (H4748):

- **Entry bodies probed:** `SamudraManthanam/web/corpus_builder/jsonl/kochergina.jsonl` (READ-ONLY, third-party digitization; B1-family probe **positive** — bodies carry labels)
- **Headword cross-check:** CORRECTIONS `Kochergina-1987_29007.txt` (29,007 headwords, UTF-16; count-only, not redistributed)
- **Corrections store:** SanskritLexicography `KOCHERGINA_CORRECTIONS.md` (adjudicated sense corrections; not a label source)
- **Comparison target:** CSDL census collision class — csl-atlas `data/abbrev/abbrev_census.json` `collisionMatrix`, 448 polysemous legend strings (H6409)

**MG verdict 11-10 grill R1.3 side-census (probe positive).** Payload:
`data/abbrev/kochergina_label_census.json` · Script:
`scripts/a72_kochergina_label_census.py` (`--emit` / `--check` parity gate).

## Denominators

| Measure | Count |
|---|---|
| Entry bodies probed | **29,180** |
| Distinct `group` ids | 29,180 (records are 1:1 with groups; homograph folding happens downstream in the concordance keys, not here) |
| **Entries with ≥1 label evidence** | **24,190 (82.9%)** |
| Entries with `nom. pr.` | 920 (bigram; `nom.` token total 974 mostly overlaps it) |
| Entries with homograph ordinal (I–VI after head) | 1,466 |
| Entries with verb-class numeral (I–X in paradigm block) | 846 |
| Headword file cross-check | 29,007 (29,006 newline-terminated lines + final line; matches `…_29007.txt` naming) |
| Distinct abbreviation tokens in inventory | 352 |

Denominator definition: an entry carries **label evidence** when it contains ≥1
token from the curated lexicon (POS/verb-system/case/compound/proper-name/cross-ref/domain/homoglyph-drift
categories), a `nom. pr.` bigram, a homograph ordinal, or a paradigm class
numeral. Prose look-alikes (`-что-л.` → `л.`, `т. е.`, `т. п.`, `н. э.`, `II в.`)
are excluded (`excludedLookalikes` in the payload).

## Inventory (top of distribution — full 352-token table in the JSON payload)

| Token | Count | Function |
|---|---|---|
| `m.` | 8,363 | masculine (POS) |
| `см.` | 7,641 | cross-reference ("see") |
| `n.` | 5,343 | neuter |
| `f.` | 3,578 | feminine |
| `pr.` | 1,828 | present system |
| `bah.` | 1,177 | bahuvrīhi compound |
| `adv.` | 984 | adverb |
| `nom.` | 974 | ~always inside `nom. pr.` (proper name) |
| `Acc.` `Loc.` `Instr.` `Gen.` `Abl.` `Dat.` `Voc.` `Nom.` | 915/424/403/403/276/130/11/6 | case government |
| `pp.` `aor.` `pf.` `fut.` `caus.` `inf.` `ger.` `des.` `spv.` `cpv.` `den.` `pfph.` `imp.` `ppr.` `p.` | 868/768/677/455/218/95/91/19/76/65/65/57/7/5/69 | verb-system labels |
| `P.` `A.` `U.` | 451/191/207 | parasmaipada / ātmanepada / ubhayapada |
| `sg.` `pl.` `du.` `dv.` | 102/436/104/145 | number; `dv.` = dvandva (context-verified) |
| `pn.` `pron.` `pcl.` `encl.` `pref.` `indc.` `conj.` `praep.` `int.` | 169/10/11/15/17/7/6/15/3 | misc POS |
| `назв.` `букв.` `перен.` `тж.` `напр.` `особ.` `соотв.` `знач.` `обознач.` `употр.` `вышеназв.` | 730/305/47/86/163/30/17/14/14/12/27 | Russian usage labels |
| `грам.` `филос.` `астр.` `фон.` `миф.` `бот.` `муз.` `рел.` `анат.` `хинд.` `лингв.` `совр.` `поэт.` `мат.` `юр.` `воен.` `театр.` `будд.` `лит.` `мед.` `зоол.` | 250/81/28/26/20/20/13/13/15/16/17/16/7/9/8/6/6/5/5/4/4 | domain/register labels |
| `corr.` `metr.` `end.` `upa.` `ag.` | 5/4/4/3/19 | grammar misc (correlative, metre, ending, upapada, āgama) |
| `patr.` `patron.` | 23/5 | patronymic |
| homograph ordinals `I`…`VI` | 692/687/74/11/1/1 | homograph sigla after headword |
| class numerals `I`…`X` | 516/77/20/108/33/80/18/5/46/78 | present-class sigla in paradigm blocks (IV notably frequent) |

### Digitization artifacts (honest findings)

- **Script-homoglyph drift:** Latin sigla sometimes digitized with Cyrillic
  homoglyphs — `Р.` (39) for `P.`, `рf.` (6) for `pf.`, `рr.` (3) for `pr.`,
  `Асс.` (4) for `Acc.`, `lnstr.` (7) for `Instr.`, `jut.` (13) for `fut.`,
  `preap.` (5) for `praep.`. Genuine Cyrillic `А.` (77) also occurs as an
  ātmanepada sense-marker inside Russian text; the two classes are counted
  separately in the payload's inventory (they are distinct surface tokens) and
  unified only under homoglyph folding for the collision comparison.
- `Inf.` (2) vs `inf.` (95): case-capital drift, both present.

## Comparison vs the CSDL census collision class (H6409)

The collision class = 448 legend strings with polysemy ≥2 across the CSDL canon.
Kochergina overlaps it **by surface string**, not by expansion grammar:

- **Exact overlap: 42 tokens** — `m. n. f. adv. nom. pron. conj. int. metr.` ·
  `P. A. U.` · `Abl. Acc. Dat. Gen. Loc. Nom. Voc.` · `sg. pl. du.` ·
  `pr. pf. aor. fut. caus. inf. Inf. ger. imp. pp. p.` · `abs. part. red. ind.`
  `patron. S. V. acc. instr.`
- **Homoglyph-folded only: 7 tokens** — `А.` `Р.` `Аbl.` `аdv.` `рf.` `рr.` `рр.` (drift artifacts above)
- **Kochergina-specific (no CSDL collision)**: the Russian leg — `см. назв. букв.
  перен. тж. напр. …`, domain labels, `bah. dv.`, Cyrillic-А sense-marker,
  homograph ordinals, class numerals.

Interpretation: the **grammatical core** (POS gender, case government,
verb-system) is shared surface vocabulary with CSDL legends — the same
homograph strings A72 v1 flagged as polysemous (e.g. `A.` = Ātmanepada vs
Active vs work-title). The Cyrillic leg adds a parallel **Russian-language label
layer** with no CSDL counterpart, plus compound-type and numeral-siglum systems
CSDL legends express differently. Any cross-dictionary label disambiguator
(H6464 eval lane) must therefore treat script as a first-class feature:
Latin-script tokens collide with CSDL legends; Cyrillic-script tokens do not.

## Edition note (honest state)

The estate holds a **digitization of the 1987 printing** (В. А. Кочергина,
*Санскритско-русский словарь*, 1987 — the edition named in
`KOCHERGINA_CORRECTIONS.md` and in the H4748 dataset row). **Gasuns 2006**
(learnsanskrit.ru) cites the **1978 edition**; the estate carries no 1978 copy,
so this inventory describes the **1987 digitization only** and no 1978-vs-1987
label drift can be verified from estate material. The mojibake findings above
are artifacts **of the digitization**, not of the printed 1987 source.

## Licensing statement

Kochergina is a **third-party Russian dictionary**: this census publishes the
**derived label inventory, counts and comparisons only — never full entry
text** (same RIGHTS FENCE as the H4748 dataset, N10). The sibling dataset
`kochergina-corpus-concordance` is CC BY-SA 4.0 (links + counts only). The
CORRECTIONS headword file was used read-only for the 29,007-count cross-check
and is not redistributed. DCS-derived layers referenced here are CC BY 4.0.

## Verification evidence

- `python3 scripts/a72_kochergina_label_census.py --emit data/abbrev/kochergina_label_census.json` → PASS (29,180 probed, 24,190 labeled)
- `… --check data/abbrev/kochergina_label_census.json` → **CHECK PASS** (byte-equivalent re-derivation; derive-don't-store parity)
- Mechanical `occurCheck` on spot entries e1–e3: every extracted label token literally occurs in its body — PASS (e1: no labels — correctly, `-что-л.` excluded; e2: `bah. напр.`; e3: `Abl.`)
- Manual hand-verification of 8 entry bodies during calibration (e1–e3; अञ्ज् `(U. pr. … VII- fut. …)`; समर्थ `(Loc, Dat.)`; प्रतिमुच् `(Acc.) (Dat., Loc, Gen.) (Abl.)`; चतुर्थांश `m. … bah.`; अभिमन्यु `m. nom. pr.`) — all match extracted labels
- B1-family probe-first requirement: satisfied (labels confirmed in first probe sample before census was written)

## Residuals

- Label *expansion* dictionary (token → full Russian term) is a separate
  pedagogy unit (H6465 consumes the collision tables); this census ships
  surface tokens + functions only.
- 228 of the 352 inventory tokens occur fewer than 3 times (long tail incl.
  one-off digitization artifacts); the payload's inventory keeps them all —
  honest tail, nothing silently dropped.
