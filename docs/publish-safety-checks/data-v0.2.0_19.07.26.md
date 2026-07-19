# `/publish-safety-check` — kosha `data-v0.2.0` release

_Created: 19-07-2026 · Last updated: 19-07-2026_

Run before cutting the `data-v0.2.0` release (H1264/W1c), per D8's step 6/1c-5.

**Scope.** 33 rows flip from `in_release: "unreleased"` to `data-v0.2.0`: the
32-row backlog + `morphology-attestation-audit` (new since the plan was
authored). All 33 are `tier: public`. See
[migrate_manifest_schema.py](https://github.com/gasyoun/kosha/blob/main/scripts/migrate_manifest_schema.py)
and the build report in this handoff for the full row list.

## Checklist

1. **Intended visibility — GO.** kosha is a public repo; the data-hub role and
   GitHub-Releases publication pattern is an established, MG-approved, repeated
   precedent ([`data-v0.1.0`](https://github.com/gasyoun/kosha/releases/tag/data-v0.1.0),
   [DATA_HUB_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md)
   D-HUB-8). No fresh visibility decision needed — D7 (this same handoff)
   makes this the standing cadence.
2. **Rights-gated content — GO.** All 33 rows are `tier: public` (verified by
   script, zero `restricted`/`intermediate` rows in the set).
   `heritage-forms-crosswalk-extras` verified still `tier: restricted`,
   `in_release: "not-applicable"` — LGPLLR (D10) untouched. No `restricted`-tier
   row anywhere in the manifest carries a release-tag `in_release` value
   (checked programmatically: empty set).
3. **Personal data — GO.** Scanned each row's `keying`/`notes` fields for
   email/phone/roster/personal-name markers — zero hits. Content is
   linguistic/pedagogical (concordances, sandhi, morphology, reading packs,
   vocab drills) sourced from public-domain/CC-licensed Sanskrit texts.
4. **Secrets + history — GO.** Grepped all 50 files backing the 33
   `release_asset` entries for key/token/password/secret/private-key patterns.
   All ~30 hits were false positives — English dictionary glosses ("to keep a
   *secret*") and NLP `token` column names — spot-verified by context. No
   credential-shaped string found.
5. **Gitignored-bulk leakage — GO.** Every `release_asset` path resolved to a
   real, `git`-tracked file (`git check-ignore` clean on all 33; the 18-file
   `gita-reading-pack` range glob also clean). No gitignored/local-only path
   backs any row entering this release.

## Verdict

**GO.** Proceed with `data-v0.2.0`.

_Dr. Mārcis Gasūns_
