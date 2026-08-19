# ROADMAP_INFLECT — drastic improvement of the Cologne inflected-form tool

_Created: 03-07-2026 · Last updated: 19-08-2026_

> **Truth-pass 19-08-2026** ([H3001 (Opus 5) — Stale-roadmap slice 3: full /ask replan of stale Tier-1 roadmaps](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3001-Opus_multi_stale-roadmap-s3-tier1-ask-replan_17.08.26.md)).
> Every handoff this roadmap references is closed ✅. Two status corrections applied
> below: **Wave U2's condition fired on 03-07-2026** and went unnoticed for six weeks
> — and a 19-08-2026 re-check found the wave had in fact been **delivered on
> 09-07-2026**, so the row was understating it twice over (see U2),
> and **Wave E1 is done** but was still marked pending. The residual programme is
> [docs/PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_INFLECT_PEDAGOGY_RESIDUAL_2026H2.md).

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
  [H093](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H093-Sonnet_csl-inflect_cslinflect_upstream_probe_03.07.26.md).
- **Wave U1 — question-issue research give-back.** Research all open
  csl-inflect issues and post structured findings per issue (D6). Handoff:
  [H094](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H094-Fable_csl-inflect_cslinflect_question_research_03.07.26.md).
  Runs parallel to U0.
- **Wave U2 — drip the queue. ✅ DONE 09-07-2026 — the whole queue shipped six
  weeks before anything was queued to ship it.**
  D5 gated this on *"probe merged ≤ ~1 month"*. The probe —
  [csl-inflect PR #17 "Make the inflected-form lookup usable on phones"](https://github.com/sanskrit-lexicon/csl-inflect/pull/17)
  — was **merged the same day it was opened, 03-07-2026**. The condition was
  satisfied immediately — and the queue was then **drained on 09-07-2026**:
  [`help-examples` PR #22](https://github.com/sanskrit-lexicon/csl-inflect/pull/22) and [`output-polish` PR #23](https://github.com/sanskrit-lexicon/csl-inflect/pull/23)
  both merged, while [`devanagari-input` PR #21](https://github.com/sanskrit-lexicon/csl-inflect/pull/21) was closed after
  [PR #20](https://github.com/sanskrit-lexicon/csl-inflect/pull/20) landed mid-review and independently added the same `DEVA`
  option, and was superseded by
  [`devanagari-input-slp1` PR #24](https://github.com/sanskrit-lexicon/csl-inflect/pull/24) — merged the same day, wiring the
  client-side conversion `main` was missing. **Nothing remained unsent.**
  The row nonetheless read "conditional" until 19-08-2026, when the truth-pass
  above minted
  [H3165 (Sonnet 5) — Wave U2: drip the three prepared csl-inflect PRs](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H3165-Sonnet_csl-inflect_inflect-u2-drip-prepared-prs_19.08.26.md)
  to drip a queue that was already empty; H3165 closed the same day as a stale
  mint (Opus 5 `claude-opus-5`), evidence in [FINDINGS §501](https://github.com/gasyoun/Uprava/blob/main/FINDINGS.md).
  The upstream give-back track is **complete**; the kosha track carries
  everything further (D5).

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
- **Wave K2 — modern lookup UX + reverse lookup. ✅ done 05-07-2026.**
  - **K2a — backend. ✅ done 05-07-2026 (Opus 4.8 `claude-opus-4-8`, H181).**
    Reverse-lookup cascade (`inflections` → `forms` → vidyut-cheda
    segmentation) behind `/api/v1/forms/{form}/analyze` with `resolved_by`
    provenance; verb conjugations ingested (the K1 upstream Py-2 blocker fixed +
    upstream-PR'd); `stem_bridge` reconciliation (`Bagavant`→`Bagavat`).
  - **K2b — frontend. ✅ done 05-07-2026 (Opus 4.8 `claude-opus-4-8`, H183).**
    Svelte 5 + Vite app ([`ui/`](https://github.com/gasyoun/kosha/tree/main/ui))
    built into [`docs/inflect/`](https://github.com/gasyoun/kosha/tree/main/docs/inflect),
    served at `gasyoun.github.io/kosha/inflect/`. Auto-detect input
    (Devanagari/IAST/SLP1 → SLP1) with live transliteration, autocomplete off
    the shared `lemmas.json` (prefix range-seek), Devanagari-default paradigm
    tables with an IAST/SLP1 toggle, paste-anything reverse box, mobile layout
    (in-container grid scroll). Data backend is **both** (K2b-2): static
    pre-generated JSON by default (works with no live server), live API when
    `window.KOSHA_API` is set. New `GET /api/v1/paradigm/{lemma}` +
    [`scripts/build_paradigms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_paradigms.py)
    (parity-locked static shards). Exit forms `bhagavān` / `rāmeṇa` /
    `dharmakṣetre` all resolve with visible provenance; `tattvamasi` resolves
    via the live-API segmentation path.
- **Wave K3 — dictionary integration. ✅ folded into K2b per MG 05-07-2026.**
  The dictionary cross-links K3 owned — every stem/lemma links into its in-app
  MW/PWG/AP90 entry, and the entry view gained a "show all forms" control back
  into the paradigm UI — were delivered as part of K2b (H183 ruling K2b-3), not
  as a separate wave. K3 owes nothing further.

### Evolution track

- **Wave E1 — dual-engine comparison (the vidyut path, D3). ✅ done 12-07-2026
  (Opus 4.8 `claude-opus-4-8`, [v0.21.0](https://github.com/gasyoun/kosha/releases/tag/v0.21.0),
  [PR #64](https://github.com/gasyoun/kosha/pull/64)) — the hybridize layer and the
  verb comparison both shipped; only the diplomacy-gated upstream post remains
  parked.** The 05-07-2026 "🔶 pending" reading below was correct on the day and
  stale from 12-07-2026 onward; corrected 19-08-2026.
  - **Done:** [`scripts/compare_vidyut_cologne.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_cologne.py)
    (vidyut-prakriya 0.4.0 local, R12-clean) + [`E1_DIVERGENCE_REPORT.md`](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md):
    **90.5 % cell agreement** over 240k cells / 10k nominal stems, divergences
    classified — ṇatva bug ([MWinflect#6](https://github.com/sanskrit-lexicon/MWinflect/issues/6))
    confirmed with a **larger blast radius than the documented 69** (89 stems in
    the top-10k sample), pronominal mis-models, feminine-stem forks, cardinal
    coverage gaps vidyut fills.
  - **(a) give-back** to [#10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10)
    ([#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8) = verb side):
    **drafted, not posted** — diplomacy-gated (RELATIONS.md §2/§7), awaits MG
    go-ahead. Draft in [H185](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md).
  - **(b) ruling** migrate/hybridize/stay: report **recommends hybridize** (keep
    Cologne base per D3, layer vidyut to auto-fix ṇatva + fill gaps + flag
    forks). Filed as an **@DECIDE** in [Uprava/GTD_NEXT_ACTIONS.md](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md).
  - **(c) optional paper** — three-engine (Cologne/Huet/vidyut) divergence table;
    scaffold only if MG wants it.
  - **Shipped 12-07-2026 under [H185](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md):**
    the **hybridize forms layer** ([`scripts/build_hybrid_forms.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_hybrid_forms.py)
    — 326 ṇatva cells / 89 stems auto-fixed, 16 cardinal cells gap-filled,
    13,770 cells flagged `disputed=1`, no Cologne row deleted) and the **verb
    comparison** ([`scripts/compare_vidyut_verbs.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_verbs.py)).
  - **Still open — the verb number is not yet interpretable.** Strict verb
    agreement came out at **12.68 %** against 90.5 % for nominals, which H185 read
    as a dhātu-identity mapping gap rather than a real divergence; no verb
    hybridization was applied on that basis. Building the identity layer and
    re-running the comparison is
    [H3166 (Opus 5) — Verb dhātu-identity crosswalk](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3166-Opus_kosha_inflect-dhatu-identity-crosswalk_19.08.26.md).
  - **Still parked — human act, blocks nothing.** The
    [csl-inflect#10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10)
    ṇatva give-back is drafted and correct; posting it is diplomacy-gated
    ([RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) §2/§7)
    and waits on a human reading the draft in H185 and deciding this is the moment
    to tell a dormant maintainer their data carries a 20-year-old bug. The optional
    three-engine paper (E1c) likewise waits on a human yes/no.

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
