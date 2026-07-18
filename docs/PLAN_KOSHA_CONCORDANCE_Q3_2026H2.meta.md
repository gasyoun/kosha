# Metadoc — PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md

_Created: 18-07-2026 · Last updated: 18-07-2026_

Companion record for
[PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md)
and the four documents it indexes. What a fresh session needs in order to trust,
revise, or discard the plan without re-deriving it.

---

## 1. Purpose

The plan set converts a set of human rulings (17-07/18-07-2026) into an
execution-ready programme for kosha's 2026 H2: the Pāṇinian sūtra ↔ corpus
concordance (A4), plus four hygiene defects that would otherwise corrupt the
quarter's own bookkeeping.

It exists because kosha's **agent-runnable** build queue was empty — pedagogy
W0–W3a shipped, zero open issues, zero open PRs, and everything still specced
blocked on a human. Stated precisely, because "P1–P5 done" would be false:
README's phase table has **P2 at "generator built (v0.5.0) — next: MG deploy"** and
**P5 at "word page built … gated on P2 deploy / DCS corpus data"**, and
`IMPLEMENTATION_PLAN` still carries **P6** (gated on human review + rights) and
**P7** (gated on P2+P3). Nothing an agent may start without a human first deploying
or ruling — which on a Tier-1 repo that is also the org's data hub is a scheduling
emergency, not a rest state.

## 2. Audience

| Reader | What they use it for |
|---|---|
| An executing agent (any tier) | Wave specs, exit checks, the autonomy contract |
| A future planning session | What was already ruled, so it is not re-litigated |
| A human reviewing scope | The decisions table and the corrected-premises table |
| A cross-repo session | The dependency and rights facts A4 exports |

## 3. Provenance

| Field | Value |
|---|---|
| Authored | 18-07-2026 |
| Model | **Opus 4.8** (`claude-opus-4-8`) |
| Mode | Phase-2 planning subagent under an `/ask-batch` orchestration |
| Worktree | `kosha-askbatch`, branch `askbatch-slice2-plan`, off `origin/main` |
| Inputs | Phase-1 audit brief; human rulings 17-07/18-07-2026; direct verification against the kosha worktree, `Uprava/handoffs/`, `VisualDCS` |
| Git ops | None — the orchestrator handles all commits and pushes |

**Verification stance.** Every quantitative claim was re-measured rather than
inherited. Four briefed premises did not survive that check and are corrected in
plan §3 — the manifest schema defect, the Pages-budget overflow claim, the DICO
default, and the A3 dependency. This metadoc exists partly so those corrections
are not lost if the plan is later summarised.

## 4. What was measured, and how

| Claim | Method | Result |
|---|---|---|
| Manifest composition | parsed [datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json) | 77 rows: 63 public · 11 restricted · 3 intermediate |
| `in_release` state | field census | all 77 present; 38 `null` · 32 `"unreleased"` · 7 `data-v0.1.0` |
| `release_asset` state | field census | 39 present · **38 absent** (this is the field the brief believed was `in_release`) |
| Static-head N at 95% | cumulative sort of `count_all` over [lemma_frequency.tsv](https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv) | **N = 11,148**; 59,282 lemmas / 4,550,704 tokens |
| Word-page total | 9.7 KB × 50,355 | **477.0 MB** — confirms the ~478 MB figure |
| Pages budget | 402 + 477 vs 1,024 MB | **879 MB = 86%** — does **not** exceed the cap |
| README drift | README vs manifest | claims 57 (43 public); actual 77 (63) — restricted/intermediate correct |
| Dead links | resolved each blob URL against `Uprava/handoffs/` | 7 unique targets, **14 occurrences**, all present under `archive/` |
| Relaxed tier | `wc -l` + [GOLDEN_SAMPLE.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/GOLDEN_SAMPLE.md) | 2,171 links; **0/3** correct vs strict **11/11** |
| A3 existence | repo-wide grep for `morphology-attestation-audit` | **no artefact, no manifest row** |
| vidyut licence | [external_tools.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/external_tools.json) | **MIT** (bundled-data licence still unverified — W1a) |
| DICO layer | manifest row inspection | already registered inside `heritage-forms-crosswalk-extras`, **`tier: restricted`**, LGPLLR pending |
| Wave-1 runnability | filesystem + import check | vidyut 0.4.0 importable; `kosha.db` 1.67 GB; `dcs_full.sqlite` 920 MB — all present |
| `kosha.db` growth | file size vs D5 record | 289.8 MB (03-07) → **1.67 GB** (18-07) = 5.8× in 10 days |

## 5. Ranked improvement backlog

| # | Improvement | Why it matters | Cost |
|---|---|---|---|
| 1 | **Resolve the A4/A3 numbering in [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md) itself** | Plan §1 reconciles two conflicting labels, but the roadmap still carries the old one. A third naming will appear if this is left | S |
| 2 | **Verify the 9.7 KB/page constant** | The Pages budget rests on one figure from one build log. If word pages fattened as cards did (2.6× post-v0.7.0), the budget is wrong in the unsafe direction | S |
| 3 | **Re-measure the D5 database and latency figures wholesale** | [D5_MEASUREMENTS.md](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md) reports 289.8 MB and "14.5% of the 2 GB ceiling"; the file is now 1.67 GB / 84%. If the size figure is that stale, the latency figures may be too — and the SLO rests on them | M |
| 4 | **Pilot the verbal vidyut mapping before committing to W2a's scope** | E1 proved the nominal mapping only and explicitly deferred verbs. If the verbal mapping is weak, A4's coverage over verbs collapses and the deliverable narrows | M |
| 5 | **Decide where A4 derivation metadata lives** | R-Q1: at 84% of the release-asset ceiling, adding derivation tables to `kosha.db` may breach it. W1b measures; the decision should be explicit, not incidental | S |
| 6 | **Push the D6 lesson beyond kosha** | "Length- and sibilant-folding normalisation is not a viable relaxed-match tier for Sanskrit" is an org-wide finding. Recorded in `DEAD_ENDS`; should reach `SHARED_CODE.md` where the normalisers live | S |
| 7 | **Quantify the LGPLLR blast radius** | Heritage gates the DICO layer and possibly other assets. Nobody has listed what unblocks if it resolves — which is why it has sat open | M |
| 8 | **Add a manifest-vs-reality drift check to CI** | W1c and W1d each fix one drift instance. A general check (does every row's `source_path` exist? does every released row's asset exist?) would catch the next class | M |
| 9 | **Settle DCS's licence repo-wide** | `external_tools.json` says CC BY-SA 4.0, `CONCORDANCE_ROADMAP.md:151` and the `reading-pack-*` manifest notes say CC BY 4.0. The primary input's licence determines whether ShareAlike on every derived dataset is mandatory or optional. W1a resolves it against Hellwig's own terms and corrects whichever file is wrong | S |
| 10 | **Add a `RECORD_FIELDS` conformance test** | Two of this plan set's defects were schema drift against `concordance_core.py` (the pre-H539 `corpus_locus`/`corpus_text_id` names, and `confidence` literals not drawn from `TIER_CONFIDENCE`). A test asserting every emitted concordance TSV's header prefix equals `RECORD_FIELDS` and every `confidence` equals `TIER_CONFIDENCE[match_method]` would catch it mechanically | S |

## 6. Limitations

- **The plan is unexecuted.** No wave has run; every runtime estimate is a
  projection. W2a's pilot exists specifically because its cost is unknown.
- **Sūtra-coverage magnitude is unknown.** How many of ~4,000 sūtras will have
  exemplars is exactly what the programme measures. If the lit fraction is very
  small, the deliverable is still valid but its framing shifts from "a
  concordance" toward "a coverage study". The plan does not pre-commit to a
  number, deliberately.
- **The verbal mapping is unproven** — see backlog #4.
- **Two rights questions are open**: vidyut's bundled data (W1a, likely clean)
  and Heritage LGPLLR (human decision, blocks DICO). Neither is resolved here.
- **`@DECIDE` R-C2 is untouched** — the canonical parallel-passage variant remains
  open from Q2. A4 does not consume it, so it does not block, but it is still open.
- **The 9.7 KB/page and 402 MB figures are inherited, not re-measured** — the two
  load-bearing constants this plan did not independently verify. Backlog #2.
- **The 77-row manifest census is current, not stale.** An earlier draft of this
  metadoc claimed an uncommitted 78th row (`handoff-lifecycle-gold`) from an
  in-flight session; that was **wrong**. The row is **committed on `origin/main`**
  as [`1bd3c566`](https://github.com/gasyoun/kosha/commit/1bd3c5661) (PR #127) and
  is one of the 77 counted here. The `M datasets.json` seen in the shared main tree
  was a **stale working copy of that already-merged row** — the main tree sits 3
  commits behind `origin/main`. W1c/W1d should still `git fetch origin` and work in
  a fresh worktree, but for the ordinary reason, not because a count is in motion.
  The genuine argument for computing the count (W1d) is the 14-07 "fix stale
  dataset count" commit that was stale again in four days — not this.
- **Model-tier assignments are judgements.** The tier derivation (mechanical →
  Haiku/Sonnet; correctness-critical → Opus) is applied per handoff, but a wave
  that turns out harder than specced may need re-tiering rather than escalation
  mid-run.

## 7. Related documents

| Doc | Relation |
|---|---|
| [CONCORDANCE_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/CONCORDANCE_ROADMAP.md) | **Parent.** A4 is its Q4 flagship; this plan promotes it and absorbs A3. ⚠️ Its line 151 says DCS is **CC BY 4.0**, contradicting `external_tools.json`'s **CC BY-SA 4.0** — surfaced as an open question for W1a, plan §3 |
| [KOSHA_DECISIONS_NEEDED.md](https://github.com/gasyoun/kosha/blob/main/KOSHA_DECISIONS_NEEDED.md) | D5-1/2/3 decisions; D5-3 is the precedent for the D4 standing rule |
| [D5_MEASUREMENTS.md](https://github.com/gasyoun/kosha/blob/main/D5_MEASUREMENTS.md) | Measurement precedent; its DB-size figure is stale (backlog #3) |
| [E1_DIVERGENCE_REPORT.md](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md) | Proves local vidyut driving; nominal mapping only |
| [DATA_HUB_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md) | Where the D7 rolling-cadence rule is recorded |
| [RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md) | R1/R5 citability, R11 asset size, R12 no-live-calls |
| [EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md) | Anti-gaming rules the verification doc inherits |
| [GOLDEN_SAMPLE.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/GOLDEN_SAMPLE.md) | Evidence for the D6 dead-end record |

## 8. Revision history

| Date | Change | By |
|---|---|---|
| 18-07-2026 | Initial authoring of the five-doc set + this metadoc. Four briefed premises corrected against the repo; A3 identified as an unbuilt prerequisite and absorbed into wave 1; static-head N measured at 11,148 | Opus 4.8 (`claude-opus-4-8`) |
| 18-07-2026 | **Adversarial-review patch, 10 findings applied / 1 refuted.** A4 record schema rewritten against `concordance_core.RECORD_FIELDS` + `TYPED_LINK_ID_GRAMMAR.md` (the doc had used the pre-H539 `corpus_locus`/`corpus_text_id` names); `match_method` corrected from a constant `exact`/1.0 to the `floor` tier (0.85) it actually earns; the false "uncommitted 78th row / in-flight H1251 session" contention warning removed (the row is committed as `1bd3c566`, the main tree is 3 commits stale); the unverified "Q1 viewer reads this unmodified" reuse claim replaced with the measured shard-emitter work; the instruction to overwrite `.ai_state.md`'s **correct** ~60% deployed-tier headroom with the ~14% projection removed; `sanskrit-util` added as a precondition; M1's manifest mechanics restated (`canonical_base` does not exist; `interim_release` is a release tag, not Pages); release/commit counts split into their two real windows (24 tags 13-07→15-07, 70 commits in range; 237 = whole history from 02-07); and the DCS BY-SA/BY licence contradiction surfaced as an open question rather than silently picked. **One finding refuted and left unchanged:** the `<br/>` in architecture §1's mermaid diagram — it sits inside a fenced mermaid block, which `check_md_full_urls.py`'s `strip_code()` deletes before the HTML scan runs, so the hook never sees it and cannot block it; the no-HTML rule targets prose, not fenced diagram syntax. Partially refuted: the "23 releases" count, where 23 is a defensible reading (tags cut *after* `v0.36.0`) and the actual defect was pairing it with a 237 drawn from a different window | Opus 4.8 (`claude-opus-4-8`) |

---

_Dr. Mārcis Gasūns_
