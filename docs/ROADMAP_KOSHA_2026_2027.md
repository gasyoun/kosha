# Kosha roadmap — August 2026 to July 2027

_Created: 30-07-2026 · Last updated: 17-08-2026_

The governing decisions and autonomy contract live in the
[plan of record](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_ARCHITECTURE_ROADMAP_2026_2027.md).
This is the sole live portfolio/status roadmap. Earlier roadmaps remain
immutable evidence and must carry a completed or superseded banner.

## W0 — stabilization and truth reset

**Window:** months 0–1. **State:** ready. **Feature freeze:** active.

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

**Window:** months 1–3. **State:** gated on W0.

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

**Window:** months 3–5. **State:** gated on W1 live smoke.

Deliverables:

- immutable sense archives with checksums and historical-resolution tests
  (✅ H2346 — [PR #342](https://github.com/gasyoun/kosha/pull/342); the release
  gate is executed by required CI and rejects a local-only citation base since
  H2870);
- MG-minted DOI and updated citation metadata (**human gate** — MG mints; agent
  half is [DOI_CHECKLIST_W2A.md](https://github.com/gasyoun/kosha/blob/main/docs/DOI_CHECKLIST_W2A.md));
- P-D6 public dataset API over manifest records (✅ H2347 — `GET /api/v1/datasets`);
- request correlation, low-cardinality metrics, readiness failures, and
  release observability (✅ H2348 — `X-Request-ID` + `GET /metrics`).

Non-goals: history/auth enablement, full RU, and full sense reconciliation.

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
