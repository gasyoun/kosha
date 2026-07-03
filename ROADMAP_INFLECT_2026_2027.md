# ROADMAP_INFLECT — drastic improvement of the Cologne inflected-form tool

_Created: 03-07-2026 · Last updated: 03-07-2026_

Target: [sanskrit-lexicon.uni-koeln.de/scans/csl-inflect/web/index.php](https://sanskrit-lexicon.uni-koeln.de/scans/csl-inflect/web/index.php)
— and its drastically better successor inside kosha. Rulings elicited from MG
03-07-2026 (interview run by Fable 5, `claude-fable-5`).

## 1. Where things stand (audit, 03-07-2026)

- The live tool: stem → inflected-form tables (nominals in 3 genders,
  pronouns, cardinals, verbs in 10 classes + causatives, non-finites), with
  clickable refs into Kale's *Higher Sanskrit Grammar*. 4 input / 6 output
  transliteration schemes. Backend: pre-generated SQLite tables + PHP
  ([web/](https://github.com/sanskrit-lexicon/csl-inflect/tree/main/web)).
- The UI is 2003-era: bare form, no Devanagari input, no autocomplete, no
  mobile layout, no links into the MW entry display, no JSON API, desktop
  frames aesthetic.
- Upstream [csl-inflect](https://github.com/sanskrit-lexicon/csl-inflect) is
  Jim Funderburk's; last substantive code commit **July 2023** ("Add Go
  button"); everything since is our runbook docs + dependabot. 11 open
  issues, mostly Jim's own 2020 TODOs: Huet verb usage
  ([#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8)), Huet noun
  declensions ([#10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10)),
  perfect forms ([#6](https://github.com/sanskrit-lexicon/csl-inflect/issues/6)),
  cardinals ([#9](https://github.com/sanskrit-lexicon/csl-inflect/issues/9)),
  j-stems ([#12](https://github.com/sanskrit-lexicon/csl-inflect/issues/12)),
  correction facility ([#11](https://github.com/sanskrit-lexicon/csl-inflect/issues/11)).
  Predecessor data generator:
  [MWinflect](https://github.com/sanskrit-lexicon/MWinflect) (cloned locally,
  48 open issues).
- The live page changes only when Jim merges AND deploys. And
  [RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) §2
  is binding: maintainers are noise-averse, "we fixed your frontend" framing
  is poison, track-2 contributions go as ordinary upstream PRs on their
  merits.
- Assets already in hand: kosha P4 in
  [IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md)
  (vidyut-prakriya paradigm tables + paste-anything segmentation); the
  Zaliznyak index line in SanskritLexicography (98,639 headwords, 335
  vidyut-generated paradigms,
  [ZALIZNYAK_INDEX.md](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/ZALIZNYAK_INDEX.md)).

## 2. Decisions taken (MG rulings, 03-07-2026)

| # | Fork | Ruling | Rationale |
|---|---|---|---|
| D1 | Venue | **Hybrid** | Drastic version lives in kosha P4 (our product, our deploy); a small queue of mergeable, on-their-merits upstream PRs improves the Cologne page itself without critique framing. |
| D2 | Scope | **All four**: modern lookup UX · reverse lookup (paste-anything) · dictionary integration · JSON API | "Drastic" means the full student-facing tool, not a facelift. |
| D3 | Engine | **Cologne tables as-is to start — "but it does not have to stay so. Propose improvements, including vidyut"** (verbatim) | Start from Jim's 20 years of hand-corrected data; evolve via a dual-engine comparison (Wave E1) rather than discard it. |
| D4 | Timing | **Stay at P4** | No disruption to D5 → P2 alpha → P3; this roadmap makes P4 concrete. |
| D5 | Upstream PR cadence | **Probe first** | Prepare the queue locally; send ONE small PR as a responsiveness probe; drip the rest only if Jim merges within ~a month, else park. |
| D6 | Open issues | **Research ALL question issues** (MG overrode the narrower "data-relevant only" recommendation) | Full research give-back on Jim's open questions, posted as findings on the issues — the established `/cologne-question-research` org pattern. |

## 3. Waves

### Upstream track (independent of the kosha queue — can start now)

- **Wave U0 — probe PR.** Clone csl-inflect, inventory
  [web/](https://github.com/sanskrit-lexicon/csl-inflect/tree/main/web),
  build the local PR queue (mobile-responsive CSS; Devanagari input option;
  help-page worked examples; output polish), send ONE probe PR
  (mobile-responsive CSS — smallest, most obviously mergeable). Handoff:
  [H093](https://github.com/gasyoun/Uprava/blob/main/handoffs/H093_cslinflect_upstream_probe.md).
- **Wave U1 — question-issue research give-back.** Research all open
  csl-inflect issues and post structured findings per issue (D6). Handoff:
  [H094](https://github.com/gasyoun/Uprava/blob/main/handoffs/H094_cslinflect_question_research.md).
  Runs parallel to U0.
- **Wave U2 — drip the queue** *(conditional: probe merged ≤ ~1 month)*.
  Open the remaining prepared PRs one at a time, each waiting for the
  previous merge. If the probe meets silence: park the queue permanently;
  the kosha track carries everything (D5).

### kosha track (executes in the existing P4 slot, after P3)

- **Wave K1 — data ingest + JSON API. ✅ done 03-07-2026 (Sonnet 5
  `claude-sonnet-5`), nominals only.** Ingested the Cologne inflection
  tables (MWinflect `nominals/pysanskritv2/tables/calc_tables.txt`, the same
  file `csl-inflect/sqlite/lgtab1`+`lgtab2` are built from) into a new
  `inflections` sidecar table
  ([`scripts/build_inflections.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_inflections.py)),
  6,849,382 rows / 3,267,305 distinct forms. New
  `GET /api/v1/forms/{form}/analyze` endpoint (D2: JSON API). Engine =
  Cologne tables verbatim (D3). **Verb conjugations (`vlgtab*`) NOT
  included** — MWinflect's `verbs/` pipeline is blocked by an upstream
  Python-2-only syntax bug (`verbs/pysanskritv2/inputs/clean.py`); tracked as
  follow-up before/alongside K2. See `.ai_state.md` for the full build trace.
- **Wave K2 — modern lookup UX + reverse lookup.** Devanagari/IAST input
  with live transliteration, autocomplete against headwords, mobile layout,
  clean paradigm tables with Devanagari default. Query pipeline per the
  existing P4 plan: forms table → (miss) → segmentation fallback
  (paste-anything). Exit test unchanged: `bhagavān` (form), `rāmeṇa`
  (inflected), `dharmakṣetre` (sandhied) all resolve to entries.
- **Wave K3 — dictionary integration.** Every stem links into the MW entry
  display and back; entry view gains a "show all forms" control. Two silos
  become one tool.

### Evolution track

- **Wave E1 — dual-engine comparison (the vidyut path, D3).** Generate the
  same paradigms with vidyut-prakriya; diff against the Cologne tables;
  classify divergences (Cologne hand-correction wins / vidyut wins / genuine
  scholarly fork). Deliverables: (a) a divergence report that directly
  answers Jim's own comparison issues
  ([#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8),
  [#10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10)) — posted
  there as give-back; (b) a ruling on whether kosha's forms sidecar migrates
  to vidyut, hybridizes, or stays Cologne; (c) optional paper (continues
  Jim's Cologne-vs-Huet line — scaffold via `/paper-scaffold` only if the
  divergence table proves interesting).

## 4. Non-goals (considered and ruled out — do not re-propose)

- **Adopt/mirror** — standing up our own deployed mirror of csl-inflect that
  supersedes the Cologne page. Highest diplomacy risk; rejected (D1).
- **Upstream-only** — betting the whole improvement on a maintainer dormant
  since 2023; rejected (D1).
- **vidyut-only engine** — discarding Jim's hand-corrections
  (`stems_problem.txt`, correction files) unexamined; rejected (D3).
- **Batch-opening multiple simultaneous PRs** to a dormant, noise-averse
  repo; rejected (D5).
- **Any "we fixed your frontend" framing**, bot comments, or new
  correspondence channels
  ([RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md)
  §2 don'ts) — standing prohibition, restated here.

## 5. Sequencing against Phase 1

Nothing in this roadmap preempts the main queue (Phase 1 complete as of
03-07-2026 → P2 alpha → P3 evidence).
U0/U1 are self-contained side sessions; K1–K3 land in the P4 slot; E1 follows
K1 whenever the diff can be run cheaply. Diplomacy triggers stay as recorded
in [RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md)
§7 — a merged probe PR is ordinary upstream contribution, not the G-SALT
announcement, and does not fire trigger 2.

_Dr. Mārcis Gasūns_
