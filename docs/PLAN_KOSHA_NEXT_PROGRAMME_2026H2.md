# Plan — kosha next programme (post-A4 / post-sense-W1), 2026 H2

_Created: 24-07-2026 · Last updated: 30-07-2026_

**🔒 SUPERSEDED 30-07-2026 (H1943) as the portfolio governing plan:** the plan
of record for kosha overall is now
[docs/PLAN_KOSHA_ARCHITECTURE_ROADMAP_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_ARCHITECTURE_ROADMAP_2026_2027.md).
This document remains the decision record for the programme it indexes and is
preserved in place, not moved.

The index for kosha's **next multi-wave programme** after Concordance A4 W3b
(`data-v0.3.0`) and the sense-frequency / sense-reconciliation wave-1 ships.
It records **what was decided and by whom**, states the **autonomy contract**,
and links the four layer docs.

> **Scope in one line.** Drain already-staged residual work and finish A4's web
> surface (W1); ship a pilot cross-dictionary sense view (W2); run full
> two-witness WSD under a hard SCL-cache fence (W3); attach hub join tables into
> `kosha.db` (W4); then P5 SSR long-tail + static-head exit under an assumed
> near-term samskrtam.ru deploy (W5).

| Doc | What it answers |
|---|---|
| [ROADMAP_KOSHA_NEXT_PROGRAMME_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_NEXT_PROGRAMME_2026H2.md) | Wave order, dependencies, non-goals |
| [ARCHITECTURE_KOSHA_NEXT_PROGRAMME.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_NEXT_PROGRAMME.md) | Component boundaries, SCL fence, SSR/static split, prior-art reuse |
| [IMPLEMENTATION_KOSHA_NEXT_PROGRAMME.md](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_NEXT_PROGRAMME.md) | Step-ordered build sequence per wave |
| [VERIFICATION_KOSHA_NEXT_PROGRAMME.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_NEXT_PROGRAMME.md) | Acceptance criteria, stop conditions, risks |
| [PLAN_KOSHA_NEXT_PROGRAMME_2026H2.meta.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_NEXT_PROGRAMME_2026H2.meta.md) | Provenance, backlog, limitations |

**Sibling plans (consume, do not rewrite):**

- [PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md) — A4 W1–W3 **done**; this plan owns residual **W4a/W4b** only
- [PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md) — W1 done; this plan owns **WSD wave-2**
- [PLAN_KOSHA_SENSE_RECONCILIATION_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_RECONCILIATION_2026H2.md) — W1 done; this plan owns **pilot cross-dict view**
- [PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/PLAN_KOSHA_PEDAGOGY_ENGINE_2026_2027.md) — waves shipped; residual H1461/H1492/H1493 already staged

---

## 1. Decisions taken

| # | Decision | Source | Note |
|---|---|---|---|
| N1 | Programme = **all four fronts, sequential**: residual+W4 → sense recon pilot → WSD → P-D5 → product SSR | Human 24-07-2026 | User: "All 4, one after another" |
| N2 | Wave order = **W1 residual+W4 → W2 recon pilot → W3 WSD → W4 P-D5 → W5 product** | Human 24-07-2026 | Risk-ordered; unblocked first |
| N3 | Full **two-witness WSD now** (SCL scrape + LLM gloss-grounded), ≥70% held-out gold | Human 24-07-2026 | Overturns the cheap-fix-only recommendation |
| N4 | SCL fence = **minimal sense labels cached locally, gitignored**; never commit or publish SCL text | Human 24-07-2026 | Re-runnable; rights-safe store |
| N5 | Sense recon W2 = **cross-dict view on the existing 500-headword pilot only** | Human 24-07-2026 | Full inventory later; human sample still ~6-mo deferred |
| N6 | Deploy posture = **assume samskrtam.ru within days**; include SSR work | Human 24-07-2026 | W5 is live scope, not parked |
| N7 | Product package (W5) = **P5 SSR `/w/{slp1}` long-tail + static head N=11,148 + exit checklist** | Human 24-07-2026 | Analytics/email/ESP out of scope |
| N8 | Autonomy = **marked default + log on ambiguity; stop only on rights-red or acceptance-fail** | Human 24-07-2026 | See §2 |
| N9 | Do **not** re-mint H1265 / H1267 / H1461 / H1492 / H1493 | Default | Already 🟡 staged |
| N10 | P6 trilingual RU **out of this plan** | Default | Still G5 + Kochergina gated |
| N11 | Sense-order Axx paper **stays GTD `@DECIDE` only** | Default | Not agent-executable this plan |
| N12 | Static head **N = 11,148** remains the D4/D5 standing rule | Inherited | Re-measure in W5, do not re-open the number without new frequency data |

---

## 2. Autonomy contract (verbatim)

- **On unplanned ambiguity:** apply the marked default in the relevant layer doc
  and **log it** (one line in `.ai_state.md` Dev Notes + a `LOG:` comment at the
  decision site), then keep going. Never stall for a human.
- **Stop conditions:** halt and hand back only if (a) a **rights-red**
  `/publish-safety-check` cannot be cleared without committing modern-copyright
  or SCL body text, or (b) a wave's **acceptance gate** in
  [VERIFICATION](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_NEXT_PROGRAMME.md)
  cannot be met by any step in that wave after a genuine attempt.
- **WSD SCL special case:** if the SCL scrape is hard-blocked after a genuine
  attempt (Anubis wall, network, no labels recoverable), **fail closed to
  LLM-only**, re-label the gate as single-witness held-out ≥70%, log the
  degradation, and continue — do not invent SCL data.
- **Commit authority:** wave handoffs authorize commit → PR → merge. kosha is a
  **guarded main-tree repo** — work in a `git worktree` off `origin/main` only.
- **The fence (must NOT touch):**
  - Never overwrite human-reviewed MW / kosha `senses` / app_data — sense layers
    remain **sidecars**.
  - Never commit SCL/GPL body text, full gloss dumps, or scraped page HTML —
    gitignored label cache only.
  - Never touch `csl-orig`, sibling canonical stores, or force-push.
  - Never add BY-NC on top of Cologne BY-SA data releases.

---

## 3. Already-staged handoffs (W1 residual — execute, do not re-mint)

| ID | Deliverable | Tier |
|---|---|---|
| [H1265](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1265-Haiku_kosha_computed_readme_dataset_count_invariant_18.07.26.md) | Computed README dataset count + test invariant | Haiku |
| [H1267](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1267-Haiku_kosha_relaxed_tier_dead_end_record_18.07.26.md) | D6 relaxed-tier → DEAD_ENDS record | Haiku |
| [H1461](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1461-Sonnet_kosha_zaliznyak-declension-drill-surface_22.07.26.md) | Zaliznyak paradigm-class drills | Sonnet |
| [H1492](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1492-Sonnet_kosha_kosha-sandhi-sastra-commentary-sweep_22.07.26.md) | Śāstra/commentary sandhi sweep | Sonnet |
| [H1493](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1493-Sonnet_kosha_kosha-gita-prose-reading-view_22.07.26.md) | Gītā prose view (opportunistic) | Sonnet |

## 4. New handoffs minted by this plan

See [IMPLEMENTATION](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_NEXT_PROGRAMME.md)
§ handoff table — IDs filled at mint time in the staging manifest.

---

## 5. Autonomy-readiness gate (Phase 4)

**PASS for wave-1.** Every W1 deliverable has architecture, ordered steps,
acceptance, and risks. No blocking `@DECIDE` sits inside W1. W3 carries a
rights fence with a logged fail-closed path (N4 + autonomy WSD special case).
W5 assumes deploy (N6) but still ships the **static head** path that works on
Pages alone if the server is late.

**Wave-2+ are pre-specified** so later sessions can mint without re-interviewing;
they do not all run unattended in one 8h session.

---

_Dr. Mārcis Gasūns_
