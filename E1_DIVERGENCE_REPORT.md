# E1 — vidyut-prakriya vs Cologne csl-inflect: nominal divergence report

_Created: 05-07-2026 · Last updated: 05-07-2026_

Wave **E1** of the inflection roadmap
([ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md)
§ Evolution track, ruling **D3**): generate the same paradigms with a second,
independent engine — [vidyut-prakriya](https://github.com/ambuda-org/vidyut)
(rule-based Paninian derivation) — diff them against the ingested Cologne
[csl-inflect](https://github.com/sanskrit-lexicon/csl-inflect) tables, and
classify the divergences so MG can rule whether kosha's forms layer should
**migrate to vidyut, hybridize, or stay Cologne**. This continues Jim
Funderburk's own Cologne-vs-Huet comparison line
([csl-inflect #10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10),
[#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8)) with a **third**
engine (vidyut ≠ Huet — both Paninian, different implementations).

## Method

- **Engine:** [`scripts/compare_vidyut_cologne.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_cologne.py),
  vidyut 0.4.0 `vidyut.prakriya` as a **local library** — no live third-party
  call at build or query time (RISKS.md **R12**-clean), consistent with the D3
  guardrail. Nominals only (verbs are a larger dhātu+gaṇa+lakāra mapping,
  deliberately deferred — see § Verbs below).
- **Sample:** 10,000 frequency-ranked stems that have a dictionary entry
  (`inflections` ⋈ `entries`, ranked by `lemmas.rank_all`), **240,000**
  case×number cells across **87** Cologne declension models. The goal is to
  *characterise* divergence, not regenerate all 6.85 M cells.
- **Mapping:** Cologne `lemma_slp1` → vidyut `Pratipadika.basic`; `gender`
  m/n/f → `Linga` Pum/Napumsaka/Stri; case → `Vibhakti`; number → `Vacana`.
  Each cell's Cologne form-set is compared to vidyut's; cells are classified
  `AGREE` / `DIFF` / `VIDYUT_ONLY` / `COLOGNE_ONLY`, and every `DIFF` is
  sub-classified (below). Reproduce with
  `python scripts/compare_vidyut_cologne.py --limit 10000` (~7 s; raw stats →
  gitignored `data/e1/e1_divergence.json`).

## Headline

| Class | Cells | Share |
|---|---:|---:|
| **AGREE** | 217,226 | **90.5 %** |
| DIFF | 22,758 | 9.5 % |
| VIDYUT_ONLY (Cologne empty, vidyut fills) | 16 | 0.0 % |
| COLOGNE_ONLY (vidyut empty) | 0 | 0.0 % |

**Two independent engines — one 20-year hand-curated table set, one modern
Paninian derivation — agree on 90.5 % of cells.** That is the strong baseline
D3 anticipated: Cologne's data is trustworthy, so vidyut is a *check and
supplement*, not a replacement.

## Divergence taxonomy (the 9.5 % that differ)

| Sub-class | Cells | % of DIFF | Verdict |
|---|---:|---:|---|
| `other` (systematic derivation forks) | 13,666 | 60.0 % | ⚖️ **scholarly fork** — stem-specific |
| `final_stop` (`cāt` vs `cāt`/`cād`) | 7,454 | 32.8 % | 🟰 **representation choice** — neither wrong |
| `vidyut_superset` (vidyut adds valid variants) | 955 | 4.2 % | ➕ vidyut richer |
| `natva` (`nṛpena` vs `nṛpeṇa`) | 326 | 1.4 % | 🔴 **Cologne wrong** (MWinflect#6) |
| `cologne_superset` (Cologne adds variants) | 253 | 1.1 % | ➕ Cologne richer |
| `pronominal` (`sarvāya` vs `sarvasmai`) | 104 | 0.5 % | 🔴 **Cologne wrong** (mis-modelled) |

### 🔴 Cologne clearly wrong (vidyut wins)

- **ṇatva bug (MWinflect#6) — 326 cells / 89 stems in the sample.** Cologne's
  m_a table never applied the Pāṇini 8.4.1-2 retroflexion, so it emits
  `nṛpena`/`nṛpānām` where the attested / vidyut form is `nṛpeṇa`/`nṛpāṇām`.
  **The blast radius is larger than the 69 compounds
  [MWinflect#6](https://github.com/sanskrit-lexicon/MWinflect/issues/6)
  enumerates** — 89 affected stems in just the top-10k sample, so the full table
  count is materially higher. vidyut fixes every one automatically.
- **Pronominal stems declined nominally — 104 cells.** `sarva`, and other
  sarvanāmas, appear in Cologne's m_a/n_a rows declined as ordinary nouns
  (dat.sg `sarvāya`, abl.sg `sarvāt`, gen.pl `sarvāṇām`, nom.pl `sarvāḥ`) *as
  well as* in a correct `m_pron` row. vidyut declines them pronominally
  (`sarvasmai`, `sarvasmāt`, `sarveṣām`, `sarvasmin`, `sarve`) — the m_a/n_a
  copy is a mis-modelled duplicate.

### ⚖️ Genuine derivation forks (scholarly judgment — the `other` 60 %)

Concentrated in the feminine and consonant models (`f_A` 1,760, `m_a`/`n_a`
pronominal residue, `f_1_t`, and the monosyllabic/`-us`/`-is` stems):

- **Feminine of consonant/adjectival stems** — `mahat` (fem): Cologne declines
  the consonant stem (`mahat`, `mahatā`, `mahataḥ`…); vidyut forms the **-ī
  feminine** (`mahatī`, `mahatyā`, `mahatīm`…). The -ī feminine is the standard
  analysis, but which surface a dictionary *should list* is an editorial call.
- **Monosyllabic / irregular ā-stems** — `vā`: Cologne applies the regular
  `senā` template (`vayā`, `vāyai`, `vānām`); vidyut applies the monosyllabic
  feminine rules (`vā`, `vai`, `vām`). Genuinely different analyses of a rare
  stem.

These are exactly the cases D3 warned against discarding blind: some are Jim's
deliberate editorial choices, some are vidyut being more Paninian; **neither
engine is uniformly right**.

### 🟰 Representation choices & coverage (neither "wrong")

- **Final-stop voicing (33 % of DIFF)** — vidyut lists both pre-sandhi variants
  (`cāt` **and** `cād`) where Cologne lists one. Cosmetic; a display/citation
  convention, resolvable by normalising one way.
- **Optionality modelling** — `para`/`sva` (optional sarvanāmas): vidyut merges
  `parāḥ`+`pare` in one cell; Cologne splits them across m_a and m_pron rows.
- **Cologne richer (253 cells)** — Cologne lists optional neuter i/u-stem
  vocatives (`guro` beside `guru`) that vidyut omits. Cologne is *more*
  permissive here.
- **Coverage gaps vidyut fills (VIDYUT_ONLY)** — Cologne's `inflections` has **no
  rows** for some cardinal-number paradigms (`saptadaśan` = 17, `m_card`);
  vidyut generates the full declension. A real coverage win for vidyut on
  numerals.

## Answer to csl-inflect #10 / #8 (give-back)

[#10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10) set up a
Cologne-vs-Huet noun-declension comparison (`decline_one_huet.py`,
`readme_compare.txt`). This report adds an **independent third data point** — a
vidyut-prakriya comparison over 10k entry-bearing stems — that corroborates the
Huet line and quantifies where the three engines part ways. The drafted
give-back comment for #10 is in the E1 handoff
([H185](https://github.com/gasyoun/Uprava/blob/main/handoffs/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md));
**it is not posted** — posting to the dormant, noise-averse upstream is
diplomacy-gated (RELATIONS.md §2/§7) and awaits MG's go-ahead. [#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8)
is verb-side and is answered by the verb follow-on, not this nominal pass.

## Recommendation → MG ruling (migrate / hybridize / stay)

**Recommended: hybridize.** Keep Cologne as the attested, hand-curated base
(D3 — do not discard Jim's 20 years), and layer vidyut to:

1. **auto-correct the ṇatva bug** (326+ cells; the single highest-value fix —
   surfaces today verbatim in the K2b UI per the D3 guardrail);
2. **fill coverage gaps** (cardinal numerals and any other VIDYUT_ONLY cells);
3. **flag — not silently overwrite — the pronominal mis-models and the
   feminine-stem forks** for editorial review (they are 60 % of DIFF and are
   *not* mechanical fixes).

A full **migrate** discards Cologne's richer optional forms (neuter vocatives)
and its editorial choices; a pure **stay** ships a known, now-quantified bug.
The @DECIDE is filed in
[Uprava/GTD_NEXT_ACTIONS.md](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md).

## Verbs (deferred)

This pass is nominals only. Verb conjugation needs a dhātu → (gaṇa, lakāra,
pada, prayoga) mapping from Cologne's `v_<gana>`/`v_p` models into vidyut's
`Tinanta` API — a larger effort that also answers
[#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8) directly. Queued
in [H185](https://github.com/gasyoun/Uprava/blob/main/handoffs/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md).

## Optional paper

The three-engine (Cologne / Huet / vidyut) divergence table — especially the
ṇatva blast-radius quantification and the pronominal/feminine-fork taxonomy —
continues Jim's Cologne-vs-Huet line and is publishable. Scaffold via
`/paper-scaffold` only if MG wants it (roadmap E1 deliverable (c), optional).

_Dr. Mārcis Gasūns_
