_Created: 13-07-2026 · Last updated: 14-07-2026 (Method B vidyut-cheda bake-off shipped, H903)_

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
   coverage **47 % → 58 %** (93/161).
   - **Phase 1.1 — MWT right-edge visarga.** ✅ DONE (H894). The MWT-final word's
     sandhi with the token *after* the MWT is hidden in the component's
     un-sandhied FORM and shows only in the MWT surface tail. New **mode 2b**
     (`induce_mwt_edge`) takes the last alignment op ending at the component's
     final phoneme — handling substitution (`ḥ t → s t`, `ḥ v → r v`), elision
     (`ḥ i → Ø i`, `ḥ e → Ø e`), and multi-char (`aḥ → o`). Coverage
     **58 % → 61 %** (98/161); visarga now the top category. Remaining gap is a
     long tail of low-frequency rules a small pilot under-attests (truer test =
     running on the Gītā text itself, item 5) plus a few malformed Gītā-table
     entries (stray Cyrillic glyphs).
2. **Method B — Vidyut cheda.** ✅ DONE (H903). `Chedaka(vidyut-data/)` bound
   (root dir, not the `.msgpack` directly); input transliterated IAST→SLP1,
   predicted tokens SLP1→IAST + pausa-normalized (trailing underlying `-s`/`-r`
   → `ḥ`, matching DCS's own `Unsandhied` convention). `Chedaka.run()` returns
   only `text`/`lemma`/`data` — **no character offsets** — so a predicted token
   can't be re-anchored to an arbitrary surface span; scope is therefore mode-1
   (plain word-word) junctions only, consumed `n`-at-a-time per DCS word/MWT
   unit and the whole sentence skipped on a count mismatch (cheda routinely
   over-segments a DCS "word" into compound parts DCS keeps as one token, e.g.
   `hitopadeśaḥ`→`hita`+`upadeśaḥ`, `dhūrjaṭeḥ`→`dhūs`+`jaṭ`+`es` — a genuine
   splitter-granularity mismatch, not a bug). Results on 2 pedagogical texts
   (`scripts/compare_sandhi_methods.py --text <name> --methods AB`):

   | Text | A rules/junctions | B rules/junctions scored | B vs A (full) F1 | B vs A (mode-1-only, fair) F1 |
   |---|---|---|---|---|
   | Hitopadeśa | 615 / 8,713 | 500 / 1,359 | 0.188 | 0.224 |
   | Amaruśataka | 216 / 989 | 61 / 73 | 0.166 | 0.282 |

   Even on the fair (mode-1-only) slice, B recovers well under a third of A's
   rule inventory — vidyut-cheda alone, without gold, is nowhere near the A
   ceiling; a meaningful chunk of B's sentences are dropped outright to the
   count-mismatch skip (62–84 % of sentences in these two texts) because DCS
   and vidyut disagree on where a "word" ends. `no_gold_total`/`no_gold_recovered`
   counters are wired for item 4 below but never fired on these 2 texts (see
   there — DCS's `Unsandhied` coverage looks complete on the sample checked).
3. **Method C — neural (DharmaMitra).** API-only ([`external_tools.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json) row
   `dharmamitra`); gate behind `--allow-network`, cache responses. **Not started**
   — explicitly deferred by H903 ("(Later) method C").
4. **A/B/C report — "27 % no gold split" claim NOT reproduced.** One table per
   pilot: coverage, distinct-rule agreement, where B/C recover junctions A's
   gold split lacks. H903 measured this directly (`no_gold_total`/
   `no_gold_recovered` in `method_B`'s stats, gated on `w["uns"] is None`): zero
   no-gold mode-1 junctions in Hitopadeśa (3,432 sentences) or Amaruśataka (212
   sentences), and a 15-directory random sample across the wider DCS corpus
   (3 files each) also showed zero. This ~27 % figure — cited in this roadmap's
   §Risks as a planning-stage estimate — does not hold on what was actually
   sampled; DCS `Unsandhied` coverage looks complete wherever a token exists.
   If a real no-gold gap exists, it's likely GRETIL-specific (§0: "no DCS/GRETIL
   text has [Unsandhied] annotation" refers to GRETIL lacking the field
   entirely, a **Phase 3** concern, not a DCS gap) — re-verify against GRETIL
   once that phase starts rather than trusting the 27 % number for DCS.
5. **Gītā gold scoring.** ✅ DONE (method A) — [`scripts/score_gita_gold.py`](https://github.com/gasyoun/kosha/blob/main/scripts/score_gita_gold.py).
   DCS stores the Gītā inside the Mahābhārata as book-6 chapters relabelled
   `MBh, 6, BhaGī 1…18` (the numeric MBh-6 sequence skips 23–40) — 18 `.conllu`
   files, `*BhaGī*.conllu`. Scored against `gita_sandhi.tsv`:
   **frequency-mass coverage 87.1 %** (2,971 / 3,412 junction-attestations) —
   the true number, vs the 61 % rule-string proxy a small pilot gives (small
   texts under-attest rare rules). Rule-string coverage 82/161. The missed
   12.9 % is a long tail, each rule <1 %. Method B/C scoring pending their bindings.
   - **Phase 1.2 — spaced notation.** ✅ DONE (H897). The missed final-`t`
     assimilation, `i`→`y` semivowel, and MWT-internal visarga were all *induced*
     but written in merged form (`t a → da`, `i e → ye`, `ḥ v → rv`) instead of
     the hand table's spaced form (`t a → d a`, `i e → y e`, `ḥ v → r v`). One
     rule in `induce_coalescence` — split the output when the right word's
     initial phoneme survives unchanged — fixed it, leaving genuine coalescence
     (`a a → ā`, `a e → ai`) merged. **Frequency-mass coverage 87.1 % → 96.3 %**
     (rule-string 82 → 116/161). The residual 3.7 % is mostly malformed
     `gita_sandhi.tsv` entries (a stray-Cyrillic rule, a space-less `m b→`) and
     `aḥ`-vs-`ḥ` notation variants — worth a source-side fix, not an inducer one.

**Exit criterion:** ≥90 % of the Gītā hand rules by frequency mass. **✅ MET —
method A at 96.3 %** (H897). Method B/C bake-off + Phase 2 sweep are next.

---

## 3. Phase 2 — DCS corpus sweep (pedagogical-difficulty order)

**First sweep ✅ DONE (H900)** — [`scripts/build_corpus_sandhi.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_corpus_sandhi.py)
runs the validated method-A inducer over a curated 8-text set in learner order
and builds per-text tables + the merged
[`data/sandhi/corpus_sandhi.tsv`](https://github.com/gasyoun/kosha/blob/main/data/sandhi/corpus_sandhi.tsv).
**53,291 sandhi events · 1,674 distinct rules; the top 69 rules cover 80 % of all
corpus sandhi** — the graded-curriculum backbone. Texts swept: Hitopadeśa,
Vetālapañcaviṃśatikā, Śukasaptati, Amaruśataka, Aṣṭāvakragīta, Bhagavadgītā,
Gītagovinda, Kathāsaritsāgara.

Remaining process order (learner path, not corpus size):

1. **Easy readers** — ✅ Hitopadeśa, Vetāla, Śukasaptati, Kathāsaritsāgara; more nīti to add.
2. **Gītā-family** — ✅ Aṣṭāvakragīta, Bhagavadgītā, Gītagovinda; other gītās.
3. **Epic** — Rāmāyaṇa, Mahābhārata (largest; stabilises global frequency).
4. **Kāvya** — Kālidāsa, Bhāravi, etc. (Amaruśataka ✅ started).
5. **Śāstra / commentary** — dense sandhi, last.

**Outputs (both, per the decision):**
- Per-text: `data/sandhi/<id>_sandhi.tsv` (Gītā schema).
- Merged: `data/sandhi/corpus_sandhi.tsv` — global ranks (`rule · category ·
  global_count · global_pct · n_texts · top_texts · examples`), rebuilt each sweep.
- **Manifest:** ✅ `corpus-sandhi` row added to
  [`datasets.json`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
  (beside the existing `gita-sandhi`); a data-statement `.meta.md` is a follow-up.

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
- **Risks.** (a) DCS `no gold split` ~27 % of junctions **— H903 measured this
  directly and did NOT reproduce it (0 % on 2 pedagogical texts + a 15-dir DCS
  sample); the real "no gold split" gap looks GRETIL-specific, see §2 item 4.**
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
