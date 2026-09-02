# Kosha roadmap — August 2026 to July 2027

_Created: 30-07-2026 · Last updated: 02-09-2026_

> **Truth-pass 02-09-2026** (H3775) — `roadmap_handoff_truth.py --check` flagged this
> page drained but still living: **10 of 10 referenced handoffs have shipped, zero remain OPEN**.
> Kept at this path per MG ruling 31-08-2026 (do not archive) — the strategy/plan
> layer still holds even though its backlog has fully closed. A future session
> reopening work here should mint a fresh H### rather than un-close these.

The governing decisions and autonomy contract live in the
[plan of record](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_ARCHITECTURE_ROADMAP_2026_2027.md).
This is the sole live portfolio/status roadmap. Earlier roadmaps remain
immutable evidence and must carry a completed or superseded banner.

## W0 — stabilization and truth reset

**Window:** months 0–1. **State:** freeze-exit criteria met — audited 01-09-2026
(H3788): H1943/H1944/H1945 merged, issues #198/#201/#210 closed, `main`
protected with both CI workflows required by name, H2681 retrospective clean.
**Feature freeze:** active. Evidence:
[CITABLE_V1_RECORD_KOSHA_01.09.26.md](https://github.com/gasyoun/kosha/blob/main/docs/CITABLE_V1_RECORD_KOSHA_01.09.26.md) §1.

Deliverables:

- one live roadmap and one integrated architecture contract;
- corrected manifest/README/state truth, including issues #198 and #201;
- installable Python package, typed settings, locked dependencies;
- complete declarative build DAG, immutable build lock, postconditions, and
  atomic promotion;
- fixture-backed required Python/UI CI and protected dependency merging;
- encrypted, atomic, checksum-verifying restricted-backup transport;
- Salt-compatible shared serializer, renderer sanitizer, and citation archive
  gate;
- history/auth/analytics absent by default.

Unblocked by: nothing. Exit is defined in
[verification](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_ARCHITECTURE.md).

## W1 — public-product readiness

**Window:** months 1–3. **State:** every agent-measurable gate PASSES (audited
01-09-2026, H3788); the only open item is the human §9 branded-complete tick,
which does **not** gate W2 — the packet records the W2 unlock condition as met
on 08-08-2026. Evidence:
[CITABLE_V1_RECORD_KOSHA_01.09.26.md](https://github.com/gasyoun/kosha/blob/main/docs/CITABLE_V1_RECORD_KOSHA_01.09.26.md) §2.

Deliverables:

- `core.db`, attached `inflections.db`, attached public `layers.db`, and
  separate disabled history storage behind one query repository;
- generated-surface registry with validation for every committed and
  out-of-band surface;
- readiness checks for database availability, data version, archives, and
  optional writable subsystems;
- versioned deployment bundle, restored deployment runbook, local deployment
  rehearsal, and rollback packet;
- MG production deploy, Lighthouse mobile score at least 90, Gītā walkthrough,
  citation checks, and rollback confirmation — fillable packet:
  [MG_LIVE_SMOKE_PACKET_W1E.md](https://github.com/gasyoun/kosha/blob/main/docs/MG_LIVE_SMOKE_PACKET_W1E.md)
  (H2345 agent half; W1 product exit remains MG-signed).

Non-goal: Claude Code never receives production credentials or performs the
production deployment.

## W2 — citable v1

**Window:** months 3–5. **State:** ✅ **a citable release exists** — `v0.117.1`,
version DOI [`10.5281/zenodo.22231444`](https://doi.org/10.5281/zenodo.22231444)
under concept DOI [`10.5281/zenodo.21965599`](https://doi.org/10.5281/zenodo.21965599),
with a frozen dataset manifest and a stated versioning policy (H3788,
01-09-2026). W1 live smoke is green and does not block. Record:
[CITABLE_V1_RECORD_KOSHA_01.09.26.md](https://github.com/gasyoun/kosha/blob/main/docs/CITABLE_V1_RECORD_KOSHA_01.09.26.md).

Deliverables:

- immutable sense archives with checksums and historical-resolution tests
  (✅ H2346 — [PR #342](https://github.com/gasyoun/kosha/pull/342); the release
  gate is executed by required CI and rejects a local-only citation base since
  H2870);
- DOI minting and updated citation metadata (✅ — automatic since the
  GitHub–Zenodo webhook of 14-08-2026; 21 deposits archived as of 01-09-2026.
  Agents may mint DOIs (ruling 16-08-2026); `publish-safety-check` still gates
  and visibility flips stay human. The old
  [DOI_CHECKLIST_W2A.md](https://github.com/gasyoun/kosha/blob/main/docs/DOI_CHECKLIST_W2A.md)
  described hand-minting and is superseded);
- frozen dataset manifest per data release (✅ H3788 —
  [scripts/freeze_release_manifest.py](https://github.com/gasyoun/kosha/blob/main/scripts/freeze_release_manifest.py)
  + [data/manifest/frozen/](https://github.com/gasyoun/kosha/tree/main/data/manifest/frozen));
- stated versioning policy (✅ H3788 —
  [VERSIONING_AND_CITATION_POLICY_KOSHA.md](https://github.com/gasyoun/kosha/blob/main/docs/VERSIONING_AND_CITATION_POLICY_KOSHA.md));
- P-D6 public dataset API over manifest records (✅ H2347 — `GET /api/v1/datasets`);
- request correlation, low-cardinality metrics, readiness failures, and
  release observability (✅ H2348 — `X-Request-ID` + `GET /metrics`).

Non-goals: history/auth enablement, full RU, and full sense reconciliation.

Named W2 residuals (H3788 §5): cut `data-v0.6.0` carrying a frozen manifest —
blocked on `release_asset` + `data_statement` for `pwg-sense-attestation-window`
and `kosha-mastery-schedule`; renormalize the canonical checkout so it stops
being a CRLF source for uploads; wire `freeze_release_manifest.py check` into
the release gate.

## W3 — full sense reconciliation

**Window:** months 5–9. **State:** gated on W0 freeze exit; may overlap stable
W1/W2 operations.

Deliverables:

- preregistered stratified human-validation sample and thresholds;
- reuse of PWG sense loci, cross-dictionary pilot, sense frequency, DCS
  evidence, and existing text crosswalks;
- separate mechanical, model-derived, and human-adjudicated provenance tiers;
- quarantined uncertain mappings;
- deterministic rebuild, manifest registration, validation report, and
  product/static parity.

Non-goal: no second research programme runs in parallel.

## W4 — evidence-selected expansion

**Window:** months 9–12. **State:** human decision required after W3 evidence.

The user chooses exactly one:

1. full trilingual Russian dictionary;
2. Pāṇinian ambiguous-chain recovery or another concordance;
3. downstream sense-frequency distribution.

Codex prepares the decision packet. No Claude Code executor selects the lane.

## In-flight handoff set (pointer, not status)

Three Claude Code handoffs claimed 30-08-2026 execute open units of this portfolio and of
[docs/ROADMAP_KOSHA_2026H2.md](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026H2.md):
the design record, exclusions and gates are in
[docs/PLAN_KOSHA_IMPROVEMENT_SET_2026-08-30.md](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_IMPROVEMENT_SET_2026-08-30.md).
Status stays here; the plan does not fork it.

## Portfolio non-goals

- no repository split;
- no PostgreSQL migration;
- no external pipeline orchestrator;
- no second transcoder, headword index, crosswalk, concordance matcher, or
  corpus derivation when a canonical sibling asset exists;
- no course/SRS platform inside kosha;
- no production deployment by an agent;
- no repeated rights research once facts are recorded.

---

_Dr. Mārcis Gasūns_
