# Metadoc — ROADMAP_GITA_GOLD_EXTRACTION_2026.md

_Created: 13-07-2026 · Last updated: 13-07-2026_

**Purpose.** Companion record for the Gītā-gold extraction roadmap: why it
exists, what a fresh session needs to know, and the ranked workstream backlog.

**Audience.** Whoever picks up a Gītā-gold workstream (W0–W7) in kosha.

**Provenance.** Authored 13-07-2026 (Opus 4.8 `claude-opus-4-8[1m]`) off an MG
interview (4 locked decisions: home=kosha · vendor+cite · all layers ·
inflection-QA is a workstream) following the H848 ch-1 gold pilot
([kosha v0.25.0](https://github.com/gasyoun/kosha/releases/tag/v0.25.0)).
Source workbook inspected directly: `SanskritGrammar/Concordance/Gita.xlsm`
(11 sheets; `Combined` is the 24-col master; 9,091 words / 18 adhyāyas).

**Onboarding facts a session would otherwise rediscover the hard way.**
- The **`Combined` sheet** (not `Grammar`) is the clean labelled master — extract
  from it. `Grammar` adds one thing Combined drops: the **etymology-notes** column.
- `Gita.xlsm` is **not git-committed** — must be vendored; don't wire a build to it.
- The Russian **transliteration** columns use a **private-use font encoding** (junk
  bytes); the Russian **gloss** columns are clean Cyrillic.
- The morphology **codes** (`Code`/`Tense`) decode via the `Encode` + `Abbreviations`
  sheets — W3 can't proceed without them (that's why `Encode` is folded into W7).
- kosha already ships the ch-1 pipeline: `scripts/extract_gita_gold.py` +
  `scripts/build_reading_pack_gita.py` — extend, don't rebuild.

**Ranked backlog (mint each as its own H### at kickoff).**
1. **W0** master dataset vendored + cited — foundation, launchable now (S–M).
2. **W3** morphology+compound gold (needs W7 code-decoders) (M).
3. **W4** inflection-engine QA vs E1 hybrid layer — the highest research value (M–L, after W3).
4. **W1** full 18-adhyāya reader (S).
5. **W2** sandhi layer + reader affordance (M).
6. **W5** Russian + etymology layer (M; RU-translit encoding risk).
7. **W6** root/preverb semantics dataset (S–M).
8. **W7** residual: Encode/Tenses/Abbreviations decoders, Prose interlinear, Vocabulary, verse-index.

**Limitations.** Effort tags are rough. W4's value depends on the Gītā recension
matching kosha's paradigm assumptions. No handoffs minted yet — the roadmap is
the artifact; workstreams mint at kickoff.

**Open decisions (mirror of roadmap §7).** RU-translit transcode map? · author
credit + license · public/Zenodo the master dataset? · is the method a template
for other texts?

**Revision history.**
- 13-07-2026 — created alongside the roadmap (Opus 4.8 `claude-opus-4-8[1m]`).

_Dr. Mārcis Gasūns_
