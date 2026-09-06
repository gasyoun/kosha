# SIGNOFF A56 — author-voice pass (Zaliznyak-style grammar-token index, JOHD data paper)

_Created: 06-09-2026 · Last updated: 06-09-2026_

**Scope.** Manuscript [papers/A56_ZALIZNYAK_GRAMMAR_INDEX_DATA_PAPER_JOHD.md](https://github.com/gasyoun/kosha/blob/main/papers/A56_ZALIZNYAK_GRAMMAR_INDEX_DATA_PAPER_JOHD.md) (JOHD data paper, ~1.6k words, EN). Pass executed under handoff [H3857](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3857-Fable_Uprava_all-articles-author-voice-pass-workflow_01.09.26.md) by Fable 5.1 (`claude-fable-5-1`) on 06-09-2026, branch `voice-pass/A56`. Voice, register and framing only; no number, claim or citation altered; mechanical drift gate ([tools/voice_drift_check.py](https://github.com/gasyoun/Uprava/blob/main/tools/voice_drift_check.py)) CLEAN — 108 numbers, 23 URLs, 12 DOIs, 6 citations, 3 IAST tokens, 19 headings, 8 table rows count-identical before and after. The data-paper register (JOHD section skeleton, passive Method steps, inline lettered lists) was kept on purpose; the pass touched only what read as machine prose.

## 1. Voice calls made — each may be vetoed

| # | Location | Call | Rationale |
|---|---|---|---|
| 1 | Header | Added the academic byline block (`Mārcis Gasūns, independent scholar (ORCID …), gasyoun@ya.ru`) under the dated header; bumped `Last updated` to 06-09-2026. | The manuscript carried no author block; JOHD needs one and the brief adds it when absent. |
| 2 | Abstract, sentence 2 | `We apply this design…` → `I apply this design…`; the three-em-dash sentence split in two: the Petersburg Dictionary gloss now sits with the "dictionary scale" clause, the counts (`≈94,000 of ≈106,000, ≈89%, 335`) in their own sentence, and `no inflection tables are transcribed` attached by a semicolon. | Single-author paper (`The author declares…`), so first-person singular; three parentheticals hung on em-dashes in one sentence is the pattern the pass exists to remove. Every number and the "for the first time at dictionary scale" claim kept verbatim. |
| 3 | Abstract, last two sentences | `… (see §3) — a full Sanskrit lexicon exercises …` → full stop before `A full Sanskrit lexicon exercises …`; the verbless `Released under CC BY-SA 4.0.` → `The dataset is released under CC BY-SA 4.0.` | Dash-appended interpretation and telegram fragment; both were sentences waiting for a verb. |
| 4 | §1 Context, para 1 | `usable by trained readers, opaque to software and learners` → `usable by trained readers but opaque to …` | Asyndetic pair read as parcellation; the contrast is what the sentence means. |
| 5 | §1 Context, para 2 | `The design decision with the widest consequence: paradigms are …` → `… is that paradigms are …`; the trailing ` — the token layer stays compact` joined with a semicolon. | Colon-as-copula opener. `The token, not the table, is the datum.` kept: it is the author's thesis, not the "not X, it's Y" tic. |
| 6 | §2 Quality control | `The closed token inventory was grown only when …` → `I grew the closed token inventory only when …`; `All headline counts … were re-verified` → `I re-verified all headline counts …`. | Two agent-hiding passives where the author is the agent; `only` and `all` preserved. The Method steps (1)–(3) stay passive — standard data-paper register. |
| 7 | §3, token-frequency question | Dropped `actually` from `How much paradigm diversity does a full Sanskrit lexicon actually exercise?` | Rhetorical intensifier; the question is the same. |
| 8 | §3, closing sentence | `… other languages — a rare cross-linguistic object: the paradigm entropy …` → `… other languages. That makes it a rare cross-linguistic object: the paradigm entropy …` | Em-dash stacked on a colon; `directly comparable` and `rare` kept at strength. |
| 9 | §4, para 1 | `… no additional lexicographic work — evidence that the token layer …` → `… work. That is evidence that the token layer …` | Dash-appended clause; "evidence" kept as written (no strength change). |
| 10 | §4, para 2 | The bold-label, em-dash list `(a) **learner tooling** — …; (b) **quantitative morphology** — …` recast as four sentences: `External reuse runs in four directions. (a) In learner tooling, … (b) In quantitative morphology, … (c) In NLP, the index is … (d) As lexicographic method, it is …`. Lettering, order, every parenthetical (Monier-Williams join remark) and every figure (98k, 8-column) kept. | Bold-every-label plus em-dash copulas is the checklist's bullet-sheet pattern; the labels were topics, and they stay topics (prepositional phrases), never source attributions. |
| 11 | Backlog to 5/5, item 1 | `the one honesty gap named in Limitations` → `the one validation gap named in Limitations` | Fake-candour flavour on an internal note; the gap is the same. |
| 12 | Provenance | One-line pass note appended (handoff link, model, this signoff). | Required header note; placed in the section that already lists prior passes, nowhere else. |

## 2. Substance flags carried (not fixed)

1. **Tokenized-headword count vs row count.** The abstract says `≈94,000 of PWG's ≈106,000 headwords (≈89%) are assigned one of 335 … tokens`, while §3 says the TSV has 98,639 rows and `Three indeclinable classes cover 2,003 headwords; the remaining 332 declension classes partition 96,636` (2,003 + 96,636 = 98,639, i.e. every row carries a token). Either ≈4,600 rows are tokenized cross-reference/marker entries that the abstract does not count as headwords, or the ≈94,000 figure is stale. A human should state which population the 98,639 and the ≈94,000 denote, in one sentence, before submission.
2. **"Six tokens cover half the lexicon"** — computed over the 98,639 rows (§3 table) but phrased in the abstract as if over headwords; same population question as flag 1.
3. **References list an uncited entry.** `Gasūns, M. Gasuns Sanskrit Dictionary data release v0.5.0. Zenodo, 26-08-2026. doi 10.5281/zenodo.22105641` is never cited in the text (the paper cites only `data-v0.4.0` / `10.5281/zenodo.22102090`). Keep it only if v0.5.0 supersedes the DOI of record; otherwise drop at submission.
4. **Frozen-asset naming.** §2 Quality control re-verifies against `data-v0.1.0` while the header, §1 and §3 cite `data-v0.4.0` ("a re-cut of the identical data-v0.1.0 content"). Consistent as stated, but a referee will ask; consider saying "the data-v0.1.0 asset, re-cut unchanged as data-v0.4.0" once in §2.
5. **Reference format.** The Zaliznyak, CDSL and vidyut entries carry no access dates or edition data and the two Gasūns entries use DD-MM-YYYY; JOHD's template will want a uniform style. Formatting only, left untouched.
6. **§3 singleton counts.** The paper itself flags that the 48/121 thin-tail figures are classifier-dependent and that a manual check "is owed before these figures are read as a finding" — yet the abstract presents `48 classes are singletons` as a finding (with the same caveat in parentheses). Not altered; noting the tension for the human pass.
7. **Zaliznyak's ≈100,000 words.** §1 Context asserts "roughly 100,000 words" for the 1977 dictionary; Backlog item 3 says the text deliberately avoids asserting his token count, which it does — but the word count is asserted and should be bibliographically checked in the same step.
8. **Internal sections.** `## Backlog to 5/5` and `## Provenance` are not JOHD sections and must be stripped at template transfer (Backlog item 4 already says so).

## 3. Read-and-sign

About 30 minutes: read the abstract, §1 Context and §4 as the changed surfaces (calls 2–10), then rule on flags 1–3, which are the only ones a referee would raise unprompted.

Proposed readiness: stays **4/5** (propose only). The 5/5 bump still waits on the paradigm-sample validation (Backlog item 1) and on flag 1.

Venue: JOHD data-paper track remains the right fit; no change recommended. No submission before 2026-11-01 (freeze).

_Dr. Mārcis Gasūns_
