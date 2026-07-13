_Created: 13-07-2026 · Last updated: 13-07-2026 (Phase 1 mode-2 shipped, H888)_

# Corpus-wide sandhi extraction for Sanskrit pedagogy — roadmap (2026–2027)

Scale the Bhagavadgītā sandhi layer (H872) from **one hand-annotated text** to
**every DCS text, then GRETIL** — producing corpus-attested, frequency-ranked
sandhi data reusable across four pedagogy surfaces. Grounded in a working Phase-0
proof (this handoff, [H882](https://github.com/gasyoun/Uprava/blob/main/handoffs/H882-Opus_kosha_corpus-sandhi-pedagogy-roadmap_13.07.26.md)).

Roadmap decisions locked with a human 13-07-2026: **DCS-first** (GRETIL phase-3);
**A/B/C split-method bake-off** (compare all three, don't pick blind); **both**
per-text and merged outputs; **all four** pedagogy deliverables; text order by
**pedagogical difficulty**.

---

## 0. What already exists (don't rebuild)

| Asset | Path | Reuse |
|---|---|---|
| Gītā sandhi table (161 rules / 3,412 junctions) | [kosha `data/gita/gita_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_sandhi.tsv) | **gold for notation validation** |
| Gītā builder + `categorise()` 4-class fn | [kosha `scripts/build_gita_sandhi.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_gita_sandhi.py) | classifier + aggregator reused **verbatim** |
| Teaching page (theme-aware) | [kosha `reading/sandhi/index.html`](https://github.com/gasyoun/kosha/blob/main/reading/sandhi/index.html) | template for per-text + reference pages |
| DCS CoNLL-U corpus (local) | `dcs-conllu/files/` — 270 texts, 15,900 files | **primary substrate** (`Unsandhied=` field) |
| Vidyut cheda segmenter + rules | `vidyut-data/cheda/model.msgpack`, `vidyut-data/sandhi/rules.csv` | **method B** splitter |
| Sandhi quiz component + data | [csl-guides `src/data/sandhi-quiz.json`](https://github.com/sanskrit-lexicon/csl-guides/blob/main/src/data/sandhi-quiz.json), `docs/users/sandhi-quiz.mdx` | drills/flashcards surface |
| Interactive teaching widget | [SanskritGrammar `src/components/talmud/SandhiCollider.jsx`](https://github.com/gasyoun/SanskritGrammar/blob/main/src/components/talmud/SandhiCollider.jsx) | reader-hover / collider surface |

**The reframing.** The Gītā's 161 rules were *aggregated from a hand-annotated
`sandhi` column* (`Gita.xlsm` → `gita_gold_master.tsv`). No DCS/GRETIL text has
that column. So the new engineering core is a **junction-rule inducer**: derive
the same `X Y → Z` notation automatically from (word-split + sandhied surface).
The A/B/C bake-off is really *"which split source feeds the inducer best."*

---

## 1. Phase 0 — DCS junction-rule inducer (✅ DONE this session)

Delivered + proven on two pilots (verse + prose, matching the difficulty ladder):

| Script | Role |
|---|---|
| [`scripts/dcs_sandhi_induce.py`](https://github.com/gasyoun/kosha/blob/main/scripts/dcs_sandhi_induce.py) | method A: induce rules from DCS `Unsandhied=`, reuse `categorise()`, emit per-text `data/sandhi/<slug>_sandhi.tsv` |
| [`scripts/compare_sandhi_methods.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_sandhi_methods.py) | A/B/C harness skeleton (A wired; B/C stubbed) + notation validation vs Gītā gold |

**Results (model: Opus 4.8 `claude-opus-4-8[1m]`, 13-07-2026):**

| Text | Register | Sandhi events | Ruled | Distinct rules | Flagged (two-sided) |
|---|---|---|---|---|---|
| Aṣṭāvakragīta | verse | 722 | 100 % | 147 | 38 (5 %) |
| Hitopadeśa | prose | 4,554 | 100 % | 453 | 295 (6.5 %) |

**Notation validation:** method A independently reproduced **75 of the Gītā's 161
hand-written rules** on Aṣṭāvakragīta (a different text) — top shared `aḥ a → o '`,
`ḥ t → s t`, `m p → ṃ p`, `m s → ṃ s`. The inducer speaks the human's notation.

### 1a. The load-bearing Phase-0 finding — DCS pre-splits vowel coalescence

DCS keeps `a + a` (and most vowel sandhi) as **separate un-coalesced tokens**:
`na`/`na` + `agniḥ`/`agniḥ` (FORM == Unsandhied). The merged form `nāgnir`
survives **only in the continuous `# text =` line**, not the per-token FORM. So a
token-edge diff (method A as built) is near-perfect on consonant/visarga/anusvāra
sandhi but **systematically misses vowel coalescence** — which is exactly why the
Gītā hand table (annotated from continuous text) has `a a → ā` as its #1 rule and
method A does not. **Consequence for Phase 1:** a *second induction mode* aligning
the `# text =` raw line against the space-joined FORM tokens. Do not treat this as
a bug in Phase 0 — it is the discovery Phase 0 was built to make.

---

## 2. Phase 1 — dual-mode inducer + A/B/C bake-off + gold scoring

1. **Vowel-coalescence mode (mode 2).** ✅ DONE (H888). The mechanism turned out
   cleaner than free-text alignment: DCS records each coalesced span as a
   CoNLL-U **multi-word token** (`5-6 nāgnir` over `5 na` + `6 agniḥ`), so mode 2
   aligns the MWT surface against its component `Unsandhied` forms and reads the
   rule off the internal boundary (`na`+`agniḥ` → `a a → ā`; sandhi-aware so
   `na`+`eva`→`naiva` gives `a e → ai`). Also fixed a Phase-0 bug (MWT range
   lines were counted as tokens). Result: `a a → ā`, `a ā → ā`, `a e → ai`,
   `a i → e`, `i a → y a`, `e a → e '`, `a u → o` all recovered; Gītā-gold
   coverage **47 % → 58 %** (93/161). **Residual (Phase 1.1):** visarga elision
   at MWT *right* edges (`ḥ m → Ø m`, `ḥ y → Ø y`) — the MWT-final word's sandhi
   with the token after it, visible only in the MWT surface tail.
2. **Method B — Vidyut cheda.** Reconstruct the raw line from FORM, segment with
   `vidyut-data/cheda/model.msgpack`, run the *same* inducer → isolates splitter
   quality. Score against A on the same text (junction-level agreement + rule P/R/F1).
3. **Method C — neural (DharmaMitra).** API-only ([`external_tools.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json) row
   `dharmamitra`); gate behind `--allow-network`, cache responses.
4. **A/B/C report.** One table per pilot: coverage, distinct-rule agreement,
   where B/C recover junctions A's gold split lacks (the 27 % `no gold split`).
5. **Gītā gold scoring.** Run all three on the Gītā text (inside the DCS
   `Mahābhārata` dir; isolate by chapter range) and score against
   `gita_sandhi.tsv` — the one place a human wrote the same notation independently.

**Exit criterion:** a chosen default method (likely A + mode 2, with B filling
`no-gold` gaps) reproducing ≥90 % of the Gītā hand rules by frequency mass.

---

## 3. Phase 2 — DCS corpus sweep (pedagogical-difficulty order)

Process order (learner path, not corpus size):

1. **Easy readers** — Hitopadeśa ✅ pilot, Pañcatantra, Vetālapañcaviṃśati, easy nīti.
2. **Gītā-family** — Aṣṭāvakragīta ✅ pilot, Bhagavadgītā (validation), other gītās.
3. **Epic** — Rāmāyaṇa, Mahābhārata (largest; stabilises global frequency).
4. **Kāvya** — Kālidāsa, Bhāravi, etc.
5. **Śāstra / commentary** — dense sandhi, last.

**Outputs (both, per the decision):**
- Per-text: `data/sandhi/<slug>_sandhi.tsv` (Gītā schema + `text_id`).
- Merged: `data/sandhi/corpus_sandhi.tsv` — global frequency ranks across all
  processed texts (`rule · category · global_count · global_pct · n_texts ·
  top_texts · examples`), rebuilt each sweep. Drives curriculum ordering.
- **Manifest:** add `gita-sandhi` + `dcs-corpus-sandhi` rows to
  [`datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) when the merged dataset is first cut (17-field schema);
  data-statement `.meta.md` per the hub convention.

---

## 4. Phase 3 — GRETIL extension

GRETIL is raw, unanalyzed, mixed-encoding, mixed-license. Every text needs a
splitter run (method B/C — no `Unsandhied=` gold), so it inherits Phase-1's
validated pipeline. Gate each text through [`/publish-safety-check`](https://github.com/gasyoun/claude-config/blob/main/commands/publish-safety-check.md) for license
before ingest. Lower priority than a complete, gold-quality DCS layer.

---

## 5. Phase 4 — pedagogy deliverables (all four)

| Surface | Feeds from | Build |
|---|---|---|
| **Reader hover** | per-text tsv → junction→rule map | extend the Gītā reader / `SandhiCollider.jsx` to any text; hover shows the induced rule + its corpus frequency |
| **Graded curriculum** | merged tsv global ranks + a difficulty metric (frequency × class × environment count) | "learn these N junctions to read X % of text Y"; ordered rule syllabus |
| **Drills / flashcards** | junction pairs (split ⇄ join) + distractors | generate Anki/quiz items; reuse csl-guides `sandhi-quiz.json` shape |
| **Reference tables** | merged tsv per rule-class | corpus-wide `reading/sandhi/` pages per class (visarga/anusvāra/vowel/consonant), ranked, with attested examples |

Difficulty metric is the one genuinely new pedagogy artifact (a human should
confirm its weighting before it drives curriculum order).

---

## 6. Data schema, licensing, risks

- **Schema.** Per-text = Gītā's `rule · category · count · pct · examples`.
  Merged adds `text_id`/global aggregates. `categorise()` shared across all.
- **Licensing.** DCS = CC BY-SA 4.0 (attribute Oliver Hellwig / DCS). GRETIL
  varies per text — publish-safety-check gate. Derived tables are ODbL-compatible
  share-alike; credit Dr. Mārcis Gasūns for the pedagogy layer.
- **Risks.** (a) DCS `no gold split` ~27 % of junctions — method B recall matters.
  (b) DCS chapter boundaries for isolating the Gītā from Mahābhārata. (c) IAST
  glyph artifacts in DCS source (e.g. `kḷ` mojibake) — normalise on read.
  (d) Two-sided coalescences (5–6 %) need verification, not blind trust.

---

## 7. Ranked backlog (starter lines)

1. **Phase 1 mode-2 (vowel coalescence)** — highest value, unblocks curriculum.
   ```
   Read C:\Users\user\Documents\GitHub\Uprava\handoffs\H882-Opus_kosha_corpus-sandhi-pedagogy-roadmap_13.07.26.md and execute it.
   ```
   _Sonnet+ tier; extend `dcs_sandhi_induce.py` with `# text =`↔FORM alignment._
2. **Method B (Vidyut cheda) binding** — fill `compare_sandhi_methods.py:method_B`.
3. **Gītā gold scoring run** — isolate Gītā in DCS Mahābhārata, score A/B/C vs `gita_sandhi.tsv`.
4. **Phase 2 sweep** — run all easy-reader + gītā-family texts, build `corpus_sandhi.tsv`, add manifest rows.
5. **Phase 4 reader-hover** — extend the reader to a swept text.

---

_Dr. Mārcis Gasūns_
