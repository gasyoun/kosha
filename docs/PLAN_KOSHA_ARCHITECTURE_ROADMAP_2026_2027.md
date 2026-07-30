# Kosha architecture and roadmap reset — plan of record

_Created: 30-07-2026 · Planning span: August 2026–July 2027_

## Goal

Make kosha a reproducible, secure, Cologne-compatible public dictionary and
API before another feature programme begins. The repository remains a modular
monorepo: the dictionary/API is the primary product, the data hub supports it,
and teaching/course delivery remains downstream.

This plan is the decision index for:

- [the twelve-month roadmap](https://github.com/gasyoun/kosha/blob/main/docs/ROADMAP_KOSHA_2026_2027.md);
- [the platform architecture](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_PLATFORM.md);
- [the W0 implementation sequence](https://github.com/gasyoun/kosha/blob/main/docs/IMPLEMENTATION_KOSHA_ARCHITECTURE_WAVE1.md);
- [verification and risks](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_ARCHITECTURE.md).

## Decisions taken

| # | Ruling | Consequence |
|---|---|---|
| D1 | Run the public-product lane and one bounded research lane in parallel, but only after a hard stabilization freeze | W0 must exit before sense reconciliation starts |
| D2 | kosha is primarily the public dictionary/API | Data-hub and static surfaces support that product; Systema owns course/SRS delivery |
| D3 | Plan across twelve months | One live roadmap covers W0–W4; specialist plans become immutable history |
| D4 | v1 is dictionary/API/static experience plus durable citations and DOI | Full RU and full sense reconciliation do not block v1 |
| D5 | Keep a modular monorepo | Create bounded packages without splitting repositories |
| D6 | `/api/v1` must be Cologne Salt compatible | Each entry uses the Salt profile with kosha-only fields namespaced under `kosha` |
| D7 | Split SQLite before further bulk ingest | Core, attached inflections, attached public layers, and separate writable history |
| D8 | Use an in-repo declarative DAG | No external orchestrator; default build expands to the complete dependency order |
| D9 | Mount immutable citation archives locally | Releases verify archive assets, checksums, public base, and historical resolution |
| D10 | History, analytics, and magic-link auth are off for public v1 | Router inclusion is feature-gated and false by default |
| D11 | Refactor incrementally behind compatibility tests | Existing `app/` and `scripts/` entry points remain temporary shims |
| D12 | Adopt `pyproject.toml` plus a committed dependency lock | Runtime packages become installable; `sys.path` injection is retired incrementally |
| D13 | Use typed Pydantic Salt models | API, static cards, SSR, and Salt facade share one serializer |
| D14 | Use two-tier CI | Fixture DB on every PR; full-data clean-build/release gates separately |
| D15 | Preserve crawlable/static surfaces under a registry | Each surface declares inputs, builder, outputs, deploy class, rights tier, and acceptance command |
| D16 | First research programme after W0 is full sense reconciliation | It uses a preregistered human-validation sample and existing evidence |
| D17 | Public v1 has a strict release gate | Clean build, CI, Salt parity, deterministic artifacts, citations, sanitizer, and live smoke all pass |
| D18 | Rights facts are recorded once and mechanically reused | Rights uncertainty never delays work or publication; only a confirmed prohibition, explicit restricted tier, privacy exposure, or platform rule blocks |
| D19 | On ambiguity, apply the documented default and log it | Park only the affected item when no default exists |
| D20 | Halt only for security/privacy exposure, destructive-data risk, incompatible API/citation contracts, or repeated verification failure | Isolated noncritical failures are logged and skipped |
| D21 | Claude Code may branch, commit, push, open, and merge after its full gate passes | Codex reviews decisions before execution and performs retrospective post-merge review |
| D22 | Programme-wide fence is strict | No production credentials/deploy, no direct upstream edits, no restricted-byte publication, no history enablement, no feature/research work during W0 |
| D23 | Execution handoffs are Claude Code only | Codex receives no implementation handoff |

## Autonomy contract

Claude Code executes each numbered handoff end to end.

- **Default on ambiguity:** apply the plan's marked default and log the
  deviation in the PR and `.ai_state.md`.
- **Rights:** do not reopen or repeat a recorded rights assessment. Uncertain
  rights do not halt, park, skip, or delay work or publication. Stop
  publication only for a confirmed prohibition, an explicit restricted
  designation, privacy exposure, or a platform-policy restriction.
- **Stop conditions:** security/privacy exposure, destructive-data risk,
  incompatible Salt/citation contracts, or the same required gate failing
  after three serious repair attempts.
- **Git authority:** branch, commit, push, open a PR, and merge it only when
  the handoff's complete gate is green. Record the exact Claude model.
- **Fence:** never use production credentials, deploy production, edit Cologne
  or sibling upstreams directly, publish restricted bytes, enable history/auth,
  or begin feature/research work during W0.
- **Review:** Codex reviews every merged handoff retrospectively. Any corrective
  implementation becomes a new Claude Code handoff.

## W0 execution

W0 is divided into three serial handoffs:

1. [H1943 — governance and integrity](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1943-Sonnet_kosha_architecture-roadmap-w0a-governance-integrity_30.07.26.md)
2. [H1944 — reproducible substrate](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1944-Opus_kosha_architecture-roadmap-w0b-reproducible-substrate_30.07.26.md)
3. [H1945 — contract and trust boundaries](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1945-Opus_kosha_architecture-roadmap-w0c-contract-trust-boundaries_30.07.26.md)

H1944 starts only after H1943 merges. H1945 starts only after H1944 merges and
the Codex retrospective review records no unresolved P1 finding.

## Autonomy-readiness verdict

**PASS for H1943.** Its inputs are committed, its steps are ordered, its
acceptance commands are local, and no unresolved decision blocks execution.

**CONDITIONAL for H1944/H1945.** They are decision-complete but dependency
gated on the previous merged handoff and Codex review. They are not parallel
work.

---

_Dr. Mārcis Gasūns_
