# changelog_queue — release-envelope pilot (H4239), 06-09-2026

Consumed by cut_release.py at the next release cut (H3355 flow).

## [Unreleased] → Added

- **H4239 (OxAlpha `zai-coding-plan/glm-5.3-flash`) — release-envelope pilot: the
  portfolio V6 scholarly release envelope authored as `release-envelope-v1` and
  piloted on the existing `data-v0.5.0` release —kosha is the first of the six
  research providers to carry one (spec:
  [Uprava docs/SPEC_RELEASE_ENVELOPE_V6_PORTFOLIO_2026.md](https://github.com/gasyoun/Uprava/blob/main/docs/SPEC_RELEASE_ENVELOPE_V6_PORTFOLIO_2026.md);
  adoption beyond the pilot is a separate human decision).**
  [data/manifest/envelopes/data-v0.5.0.envelope.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/envelopes/data-v0.5.0.envelope.json)
  wraps the H3788 frozen manifest (pinned by sha256
  `5be4e26c…8086a`) with the V6 evidence list the frozen manifest does not
  carry: upstream **source pins** (per dataset: pin commit re-derived by
  `rev-list -1 --before` the manifest's `frozen_at` + blob digest), output
  digests restated, **config** (selection rule, tier fence, digest form),
  **tool versions**, **licence** (code CC BY-NC 4.0 / data CC BY-SA 4.0,
  per-dataset), recorded **checks**, **review** provenance (freeze gate H3788 ·
  H4046 regen audit · H4239 authoring), **citation** (concept + version DOI,
  CITATION.cff, policy) and **publication state**. Verified end-to-end:
  [scripts/envelope_check.py](https://github.com/gasyoun/kosha/blob/main/scripts/envelope_check.py)
  re-derives every declared digest from bytes — **10/10 PASS** on the authoring
  box (all 5 source pins resolve and match: frozen == upstream pin == current
  tree); sibling-clone-absent boxes SKIP rather than fail (negative control:
  6 pass / 4 skip / 0 fail). Additive only: no canonical store touched, no
  frozen manifest rewritten, canonical ownership unchanged.
