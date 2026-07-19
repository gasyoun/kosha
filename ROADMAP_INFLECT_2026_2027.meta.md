# ROADMAP_INFLECT_2026_2027.meta.md — metadoc for `ROADMAP_INFLECT_2026_2027.md`

_Created: 18-07-2026 · Last updated: 18-07-2026_

This is a **metadoc** — a document *about* a document. Its subject is
[ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md).
It does not duplicate the subject's content; it records everything *around* it. Kept per the
standing "one metadoc per important document" convention (`~/.claude/CLAUDE.md`).

## Subject
- **Document:** [ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md)
- **Purpose:** Plans the "drastic improvement" of the Cologne inflected-form tool
  ([csl-inflect](https://github.com/sanskrit-lexicon/csl-inflect)) — a hybrid track: a
  small, diplomacy-gated upstream PR queue on the dormant Jim Funderburk repo, plus a
  full modern rebuild inside kosha's own P4 slot (data ingest, JSON API, reverse lookup,
  dictionary integration, vidyut dual-engine comparison).
- **Audience:** Whoever executes kosha Phase P4, or touches
  [csl-inflect](https://github.com/sanskrit-lexicon/csl-inflect)/[MWinflect](https://github.com/sanskrit-lexicon/MWinflect)
  upstream; also the human deciding the E1 hybridize-vs-migrate @DECIDE.
- **Format / contract:** Waves (U0–U2 upstream, K1–K3 kosha, E1 evolution) are marked
  ✅/🔶/🟡 inline as they land, with handoff links — this doc is actively edited in place
  as waves complete, not a frozen plan. §4 "Non-goals" is a do-not-re-propose list and
  must stay intact even as waves close.

## Provenance
- **Created:** 18-07-2026 (handoff H968, Sonnet 5 `claude-sonnet-5`); the roadmap itself
  was authored 03-07-2026 (Fable 5 `claude-fable-5`-run MG interview), last substantively
  updated 05-07-2026 as waves K1–K3 and E1's nominal comparison landed.
- **Next hardening:** none scheduled — updates ride on E1's pending ruling/verb comparison
  (H185) and any U2 drip-PR activity.

## Improvement backlog (ranked)

| # | Improvement | Why | Status |
|---|---|---|---|
| 1 | Close the E1 hybridize-vs-migrate @DECIDE (Cologne-base + vidyut auto-fix layer, per the report's recommendation) | Blocks whether ṇatva-bug auto-correction and gap-filling actually ship | queued (H185) — filed as @DECIDE in [Uprava/GTD_NEXT_ACTIONS.md](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md) |
| 2 | Run the E1 verb-engine comparison (answers upstream issue [#8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8)) | Only the nominal comparison (240k cells) is done; verb divergence is unmeasured | queued (H185) |
| 3 | Post the drafted give-back to csl-inflect issue [#10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10) | Diplomacy-gated (RELATIONS.md §2/§7) — drafted, awaiting MG go-ahead | parked: awaits MG go-ahead |
| 4 | Decide U2 (drip the prepared upstream PR queue) | Conditional on whether the U0 probe PR was merged within ~1 month; status of that probe is not recorded in this roadmap and should be checked before assuming U2 is still live | parked: verify probe-PR outcome first, then re-open as its own H### |
| 5 | Optional three-engine (Cologne/Huet/vidyut) divergence paper | Explicitly scaffold-only pending MG interest, per §3 Wave E1(c) | parked: MG interest not yet confirmed |

## Known limitations / caveats
- The roadmap's §3 Wave U2 status (probe-PR outcome) is not visible from this file alone —
  a fresh session must check [H093](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H093-Sonnet_csl-inflect_cslinflect_upstream_probe_03.07.26.md)
  or the live csl-inflect PR history before assuming the probe result.
- E1's 90.5% cell-agreement figure is over nominal stems only (240k cells / 10k stems);
  it does not yet cover verb conjugations — do not generalize the agreement rate to verbs
  until the pending verb comparison (H185) lands.
- The roadmap is diplomacy-sensitive (RELATIONS.md §2/§7 constraints on maintainer
  contact) — §4's non-goals list exists specifically to prevent re-litigating rejected
  approaches (adopt/mirror, upstream-only, vidyut-only engine, batch-PR).

## Intended use / known misuse
- **For:** anyone picking up kosha P4 work, or considering a csl-inflect/MWinflect
  upstream contribution — read §2 decisions and §4 non-goals before proposing an approach
  that was already ruled out.
- **Misuse:** treating any of the four §4 non-goals as still open for debate without a new
  MG ruling that explicitly supersedes the recorded one. Also misuse: contacting
  Jim Funderburk or posting to csl-inflect issues in "we fixed your frontend" framing —
  explicitly banned by RELATIONS.md §2, restated in this roadmap's §4.

## Maintenance & sunset plan
- Owner: whichever session executes the next wave (U2, E1 verb comparison, or the E1
  ruling) updates the Waves section status markers in the same pass.
- Sunset trigger: once E1's ruling is closed and K1–K3/E1 are all ✅, this roadmap is
  superseded by whatever P5 (advanced UI) roadmap follows — not yet triggered.

## Deprecation status
`active`

## Related documents
- [wiki/docs/roadmap.md](https://github.com/gasyoun/kosha/blob/main/wiki/docs/roadmap.md) and its [metadoc](https://github.com/gasyoun/kosha/blob/main/wiki/docs/roadmap.meta.md) — the public-site P1–P7 phase page that names this roadmap as P4's spec.
- [IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md) — the locked P1–P7 engineering plan this roadmap's P4 slot belongs to.
- [RELATIONS.md](https://github.com/gasyoun/kosha/blob/main/RELATIONS.md) — the binding upstream-diplomacy constraints (§2, §7) this roadmap defers to.
- [E1_DIVERGENCE_REPORT.md](https://github.com/gasyoun/kosha/blob/main/E1_DIVERGENCE_REPORT.md) — the E1 nominal-comparison data this roadmap's Wave E1 summarizes.
- [H185 (archived)](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H185-Opus_kosha_e1_dual_engine_ruling_05.07.26.md) — the pending ruling/give-back/verb-comparison handoff.

## Revision history

| Date | Event | Who (tier+version) |
|---|---|---|
| 03-07-2026 | Roadmap authored (D1–D6 locked, audit + waves scaffolded) | Fable 5 `claude-fable-5` |
| 05-07-2026 | Waves K1–K3 marked done, E1 nominal comparison landed | Opus 4.8 `claude-opus-4-8` |
| 18-07-2026 | Metadoc backfilled (H968) | Sonnet 5 `claude-sonnet-5` |

_Dr. Mārcis Gasūns_
