# Risk register — the pre-mortem

_Created: 02-07-2026 · Last updated: 02-07-2026_

Judgment-tier pre-mortem for the Gasuns Sanskrit Dictionary (kosha), authored
on Fable 5 (`claude-fable-5`, 02-07-2026). Framing: **it is mid-2027 and
kosha has failed, or — worse — has silently corrupted someone's scholarship.
These are the ways it happened**, each with its early-warning signal and the
mitigation that is now a requirement, not a hope. The register is grounded in
four failure modes running live today in this exact niche
([COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md)
"Avoid" list) and in this project's own origin: the 02-07-2026 audit found
the previous planning corpus partly fabricated.

Mitigations that are testable are wired into
[EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md) gates —
a risk whose mitigation has no test is listed as such, honestly.

## 0. Register

Likelihood/Impact: L/M/H. Owner "MG" = only M.G. can retire it.

| ID | Risk | L | I | Early warning | Owner | Mitigation |
|---|---|---|---|---|---|---|
| R1 | Citation renumbering — `@data_version` is not yet airtight | M | **H** | first data release ships without a version-resolution path | agent + MG | §R1: 4 commitments, T-UC10 forces the path |
| R2 | Silent `<pc>` gaps / wrong pages → false scan links | M | **H** | scan checks pass on HTTP 200 alone | agent | §R2: fail-closed + page-truth (G-PC/G-SCAN) |
| R3 | csl-sqlite release lag vs csl-orig HEAD → stale entries | **H** | M | user reports an error already fixed upstream | agent | §R3: measure lag, surface "data as of", D5 cadence |
| R4 | kosha's own single-maintainer rot | M | **H** | months without commits; alpha never announced | MG | §R4: everything-public + rebuildability (T-UC11) |
| R5 | samskrtam.ru bus factor (domain, hosting, MG-only deploy) | M | M | deploy drifts from runbook; renewal lapses | MG | §R5: citations never point at the server; Pages mirror |
| R6 | License geometry breaks (NC data folded into BY-SA release; unlicensed DCS dump) | M | M | an import PR touches license-ambiguous data | agent + MG | §R6: geometry table; Hellwig ask before P3 public |
| R7 | Name collision with `vidyut-kosha` | L | M | outward material says "Kosha" | agent | public name = Gasuns Sanskrit Dictionary ([RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) §3) |
| R8 | Wrong-but-confident segmentation ships → students learn errors | M | **H** | pressure to drop the 90 % gate or skip calibration | agent | G-SEG gate + `beta` flag escape hatch only |
| R9 | Cologne goodwill spent (noise, perceived rivalry) | L | **H** | any unsolicited PR stream / bot comment | agent + MG | [RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) §2 don'ts; batched-PR discipline |
| R10 | Planning-fiction relapse (✅ without a passing check) | M | **H** | a checkbox with no committed artifact | agent | EVAL_PLAN rule 7; already burned once |
| R11 | Size limits: Pages 100 MB file cap; DB growth | M | L | D5 measurements near limits | agent | measure in D5 before enabling Pages; data via release assets only |
| R12 | Upstream availability rot (Inria bot wall, DCS HTTP-only, VedaWeb URL churn) | **H** | M | a build step suddenly needs a live third-party host | agent | vendor all inputs; builds never call live services |

## R1 — Is `@data_version` airtight? Verdict: only if four commitments hold

The A2 design ([ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)):
citation `mw.142512.3@v0.2.0` pins to a data release whose assets stay
downloadable. Pre-mortem of a scholar's 2026 citation breaking in a 2028
paper review — four holes, four commitments:

- **(a) The API serves only the latest data.** `GET /api/v1/sense/mw.142512.3`
  returns *current* senses; nothing in the v1 contract yet resolves the
  `@v0.2.0` part. A citation that only a manual asset download can resolve is
  not a working citation. **Commitment 1:** the `cite` object must carry a
  resolution URL that works in a browser (release-asset permalink at minimum;
  a `?v=` parameter on `/sense/` serving archived sense dumps is the better
  form) — decided in D4, forced by test **T-UC10** (resolve an old citation
  *after* the entry changed).
- **(b) Renumbering is invisible.** A Cologne correction rewrites a body →
  sense spans shift → `senseN` can change meaning between releases, and
  nothing maps old→new. **Commitment 2:** every rebuild emits
  `sense_crosswalk.tsv` (old senseN → new senseN via span-text similarity,
  with `SPLIT`/`MERGED`/`GONE` markers) as a release asset, and the release
  notes state the count of renumbered senses per dict. Zero-cost when nothing
  changed; the audit trail when it did.
- **(c) The platform is GitHub.** Releases can vanish with a repo, an
  account, or a policy change; the Zenodo DOI is currently scheduled only at
  P7. **Commitment 3 (plan change, recommended):** mirror data releases to
  Zenodo starting from the **first release anyone can cite** (the first
  public data release, P2-era), not from P7. Cost: one webhook/manual upload
  per release. Also: a standing never-delete-releases policy, and
  [LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md)'s
  attribution block requires redistributors to preserve `data_version`
  metadata.
- **(d) L-numbers are "stable" — mostly.** Cologne corrections occasionally
  split/merge entries (suffixed L-numbers exist precisely for this).
  Resolution against a *pinned* release is safe regardless — the exposure is
  only forward navigation from an old ID, which the crosswalk (b) covers.

With 1–4 in place the answer becomes yes. Without (a), the whole citability
claim (UC10, the P7 flagship) is marketing.

## R2 — Silent `<pc>` gaps → false scan links

A wrong scan link is worse than none: it *looks* like print-truth
verification while sending the scholar to the wrong page — the exact trust
kosha runs on (UC2). Three sub-failures:

1. **Missing `<pc>`** → mitigated by measuring coverage per dict
   (`sources.pc_coverage`, G-PC) and **failing closed**: no parsed `<pc>`,
   no link. Never interpolate a page from neighbors.
2. **Mis-parsed `<pc>`** — three different formats (MW `page,col`; PWG
   `vol-page`; AP90 `page-col-letter`) invite a comma-split shortcut that
   returns HTTP 200 forever while being off by a volume. Mitigation:
   **page-truth checking** (G-SCAN): the print form must be *visible on the
   fetched scan image* (vision check + human spot-check), anchored by the two
   known-good fixtures (MW `banD` → p. 720 col. 1; `akza` → 3,2).
3. **Resolver drift** — scan URLs are computed, not stored (right call: no
   staleness), but if Cologne reorganizes `serveimg`/`servepdf`, every link
   breaks at once. Mitigation: G-SCAN re-runs at every data rebuild, so drift
   is caught at the next release, not by a user; the ls_resolver port stays
   a thin, single-file dependency that can be re-synced from upstream.

## R3 — csl-sqlite lag vs csl-orig HEAD

Entry data comes from [csl-sqlite releases](https://github.com/sanskrit-lexicon/csl-sqlite/releases)
(the max-reuse rule, correct), but releases lag csl-orig HEAD — including,
awkwardly, **our own corrections** delivered via the monthly batch PR: kosha
could show an error M.G. personally fixed upstream months earlier.

- **Measure, don't wonder:** at import (D2), record per dict both the
  csl-sqlite release tag and the csl-orig HEAD commit date; compute and log
  the lag. The `sources` table already carries both fields.
- **Surface it:** `data as of {csl-orig commit date}` in `/api/v1/meta` and
  the UI footer. Staleness a user can see is a property; staleness they
  can't is a defect.
- **Decide cadence with data:** D5 sets the rebuild cadence (leaning
  nightly-to-weekly); if csl-sqlite's release rhythm proves slower than the
  cadence needs, the documented fallback (parse csl-orig text directly)
  exists per D2 — exercise it once on one dict during D2 so it is a tested
  path, not a comment.
- **Never** hot-patch `kosha.db` to catch up — corrections flow through
  csl-orig only ([RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) §5).

## R4 — kosha's own single-maintainer rot (the mirror test)

The niche's live cautionary tales, all observed 02-07-2026: meyer's site
last updated 12-2024, closed source, one maintainer; DCS serving plain HTTP
with a broken cert; spokensanskrit's TLS broken through its domain move;
learnsanskrit.org's dictionary a hard 404. kosha is *also* a
single-maintainer project — the differentiator list is only credible if it
doubles as the anti-rot checklist:

- **Everything public and rebuildable:** open code, versioned open data,
  deploy runbook ([KOSHA_DEPLOYMENT.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_DEPLOYMENT.md)),
  boring stack (SQLite + FastAPI + vanilla JS). **T-UC11** (clean-machine
  rebuild from release assets) is the rot test — run at P7 and at every
  major release after.
- **The static Pages tier survives the maintainer:** it serves with zero
  operational attention.
- **DOI'd data outlives the site** (R1 commitment 3 moves this earlier).
- **Succession note in README by P7:** one paragraph naming where the data
  lives, how to rebuild, and that the Cologne ecosystem is welcome to adopt
  the Salt facade if the project stalls.
- **Archive-banner policy:** 12 months without maintenance → an honest
  banner, while Pages + releases + DOI keep working. Rot with a label is
  degradation; rot without one is betrayal (the Gandhāri
  unversioned-citation lesson).

## R5 — samskrtam.ru bus factor

Domain renewal, hosting payments, jurisdiction, and an MG-only manual deploy
(A3: agents never SSH — correct for security, concentrating for risk).

- **The load-bearing mitigation is architectural and already locked:
  citations and permalinks never depend on samskrtam.ru.** Canonical
  citation resolution = GitHub releases + Zenodo DOI (R1); the durable
  lookup mirror = the GitHub Pages static tier. The server is the *rich*
  experience, not the *only* one. Make this a stated policy line in the P7
  docs: cite URLs must not use the samskrtam.ru host.
- Domain/hosting renewals onto M.G.'s calendar with a >30-day margin (GTD
  `@DO` when P2 deploys).
- The deploy runbook stays current: any manual deviation during a deploy
  gets written back into KOSHA_DEPLOYMENT.md the same day (drift between
  runbook and reality is how the next deploy fails).

## R6 — License geometry

Current geometry is sound: Cologne data CC BY-**SA** → kosha data releases
CC BY-SA 4.0 ([LICENSE-DATA.md](https://github.com/gasyoun/kosha/blob/main/LICENSE-DATA.md));
code separately CC BY-NC 4.0 ([LICENSE.md](https://github.com/gasyoun/kosha/blob/main/LICENSE.md));
vidyut is MIT (compatible as a consumed library). Two live edges:

1. **The DCS dump has no license file** (site claims CC BY 3.0). Shipping a
   public evidence layer built on formally unlicensed data is an avoidable
   exposure — **M.G. asks Hellwig before P3 goes public**
   ([RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md)
   §6, registry #5).
2. **gramdict/Zaliznyak data is CC BY-NC** — NC data cannot be folded into a
   BY-SA data release. Safe path (already the plan): borrow the *scheme*
   with credit; ship only in-house-derived token data (WhitneyRoots
   reverse-index work). The trap to guard in review: an executor "enriching"
   the grammar layer by importing gramdict rows directly. Import review
   checklist item: every new data source names its license in
   `data/SOURCES.md` before the import PR merges.
3. Kochergina is in copyright — P6 Gate 2 (MG) already blocks it; Kossovich
   1854 is public domain.

## R7–R12 — short form

- **R7 name collision:** `vidyut-kosha` exists. Public name = **Gasuns
  Sanskrit Dictionary**; "kosha" is repo-internal. Check outward artifacts
  (announcement, docs page, DOI metadata) against this at P7.
- **R8 wrong-but-confident segmentation:** the reputational twin of R2 —
  students trust a confident split. The G-SEG gate (90 % + calibration +
  pick-a-split UI) is the mitigation; the only sanctioned escape hatch is
  the `beta` flag, never a threshold edit
  ([EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md)
  rule 3).
- **R9 Cologne goodwill:** one bot-noise incident can cost the relationship
  the whole program stands on. Binding don'ts live in
  [RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) §2;
  the batched-PR rule is already org law. Also guard the subtler form:
  kosha's announcement must frame track 3 as *built on* Cologne, never as
  its replacement.
- **R10 planning-fiction relapse:** this repo exists because the previous
  planning corpus was found partly fabricated (same-day triage,
  [SanskritLexicography v0.0.34](https://github.com/gasyoun/SanskritLexicography/releases/tag/v0.0.34)).
  Mechanical guard: no ✅ without a committed artifact (EVAL_PLAN rule 7);
  cultural guard: every session states model tier + exact version, and
  claims are dated.
- **R11 size limits:** GitHub blocks files >100 MB in-repo; `mw.sqlite`-scale
  data flirts with that. Data ships as **release assets only** (2 GB/file
  ceiling — ample); the Pages static cache is sized in D5 *before* Pages is
  enabled, not after it 404s.
- **R12 upstream availability rot:** verified live today — Inria bot-walled
  (use the UoHyd mirror), DCS HTTP-only, VedaWeb mid-migration. Rule:
  **builds never call live third-party services**; every input (csl-sqlite
  release, DCS dump, glossary, union headwords) is vendored/pinned locally
  with its version recorded in `data/SOURCES.md`. A build that needs someone
  else's uptime inherits someone else's bus factor.

## Review cadence

The register is re-read at every phase exit (P1–P7): fired triggers move the
risk into [.ai_state.md](https://github.com/gasyoun/kosha/blob/main/.ai_state.md)
Dev Notes with what was done; retired risks get struck through here with the
date, never deleted. New risks discovered mid-phase are appended with the
next free ID.

---

_Dr. Mārcis Gasūns_
