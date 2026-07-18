# roadmap.meta.md — metadoc for `wiki/docs/roadmap.md`

_Created: 18-07-2026 · Last updated: 18-07-2026_

This is a **metadoc** — a document *about* a document. Its subject is
[wiki/docs/roadmap.md](https://github.com/gasyoun/kosha/blob/main/wiki/docs/roadmap.md).
It does not duplicate the subject's content; it records everything *around* it. Kept per the
standing "one metadoc per important document" convention (`~/.claude/CLAUDE.md`).

## Subject
- **Document:** [wiki/docs/roadmap.md](https://github.com/gasyoun/kosha/blob/main/wiki/docs/roadmap.md)
- **Purpose:** The public-facing, one-screen summary of kosha's seven gated phases
  (P1 data+API → P7 citable v1.0) — the wiki/docs-site rendering of
  [IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md)
  for external readers, not a fresh source of truth.
- **Audience:** External visitors to the kosha docs site (`gasyoun.github.io/kosha`,
  ZettelkastenWiki Wave-3 pilot) wanting a status snapshot, and any session maintaining
  the docs-site build (`scripts/build_docs_site.py`).
- **Format / contract:** Docusaurus-style page with YAML frontmatter (`title`, `slug`,
  `section`, `seo_title`, `seo_description`, `aliases`, `last_updated`) — the frontmatter
  contract is shared across `wiki/docs/*.md` and `wiki/faq/*.md` siblings (see
  [wiki/docs/positioning.md](https://github.com/gasyoun/kosha/blob/main/wiki/docs/positioning.md),
  [wiki/docs/what-is-kosha.md](https://github.com/gasyoun/kosha/blob/main/wiki/docs/what-is-kosha.md)).
  `last_updated` in the frontmatter must track the phase-status prose below it — the two
  can silently drift if only one is edited.

## Provenance
- **Created:** 18-07-2026 (handoff H968, Sonnet 5 `claude-sonnet-5`); the wiki page itself
  was authored/last touched 03-07-2026.
- **Next hardening:** none scheduled — bump `last_updated` and the phase-status prose
  together whenever a P1–P7 phase status changes in `IMPLEMENTATION_PLAN.md`.

## Improvement backlog (ranked)

| # | Improvement | Why | Status |
|---|---|---|---|
| 1 | Sync this page's phase statuses against `IMPLEMENTATION_PLAN.md` whenever a phase gate flips (e.g. P2 deploy landing, P3 DCS bands shipping) | Currently reads "generator built, deploy pending" (P2) and would silently go stale if `IMPLEMENTATION_PLAN.md` moves without a matching edit here | parked: no owning session yet — pick up alongside the next P2/P3 status change |
| 2 | Confirm the two `[[../faq/...]]` wikilinks (`what-works-today`, `data-licensing`) still resolve after any docs-site restructure | Wiki-link syntax (not a full blob URL) is fragile to directory moves; `md-hygiene`/`link-audit-fix` skills exist for this class of check | parked: run `/link-audit-fix` next time the wiki tree is restructured |
| 3 | Add a direct link from this page to [ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md)'s live wave status, not just the static P4 pointer | P4's one-line description doesn't surface that K1–K3 are already done and E1 is in progress — an external reader gets a less current picture than the repo actually has | parked: cosmetic, low priority — do opportunistically |

## Known limitations / caveats
- This page is a **derived summary**, not authoritative — `IMPLEMENTATION_PLAN.md` is the
  actual source of truth per this repo's root `CLAUDE.md`; a discrepancy between the two
  should always resolve in favor of `IMPLEMENTATION_PLAN.md`.
- The page was substantive at inspection (7 real phase lines, working wikilinks to two FAQ
  pages, real frontmatter/SEO fields) — it is not a generic scaffold stub, despite being a
  short, single-purpose page.
- Frontmatter `last_updated: 2026-07-03` was not re-verified against
  `IMPLEMENTATION_PLAN.md`'s current phase statuses as of this metadoc's creation date
  (18-07-2026); a staleness check was out of scope for this backfill pass.

## Intended use / known misuse
- **For:** giving an external (non-agent, non-org) reader a fast, public status read on
  where kosha stands, with jump links to the two most relevant FAQ pages.
- **Misuse:** citing this page as the authoritative phase-gate record in internal
  planning — use `IMPLEMENTATION_PLAN.md` for that; this page is the public mirror and can
  lag by design (it isn't updated every time an internal handoff lands).

## Maintenance & sunset plan
- Owner: whoever runs `scripts/build_docs_site.py` after a phase-status change should
  update this source page first; the build script does not synthesize phase status from
  `IMPLEMENTATION_PLAN.md` automatically.
- Sunset trigger: none — this page persists as the docs-site's roadmap route (`/roadmap`)
  for the life of the docs site.

## Deprecation status
`active`

## Related documents
- [IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md) — the actual source of truth this page summarizes.
- [ROADMAP_INFLECT_2026_2027.md](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.md) and its [metadoc](https://github.com/gasyoun/kosha/blob/main/ROADMAP_INFLECT_2026_2027.meta.md) — the P4 spec this page links to.
- [wiki/docs/positioning.md](https://github.com/gasyoun/kosha/blob/main/wiki/docs/positioning.md) and [wiki/docs/what-is-kosha.md](https://github.com/gasyoun/kosha/blob/main/wiki/docs/what-is-kosha.md) — sibling docs-site pages sharing the same frontmatter contract.
- [wiki/faq/what-works-today.md](https://github.com/gasyoun/kosha/blob/main/wiki/faq/what-works-today.md) and [wiki/faq/data-licensing.md](https://github.com/gasyoun/kosha/blob/main/wiki/faq/data-licensing.md) — the two pages this roadmap page wikilinks to.

## Revision history

| Date | Event | Who (tier+version) |
|---|---|---|
| 03-07-2026 | Page authored as part of the docs-site pilot | (unattributed in file history) |
| 18-07-2026 | Metadoc backfilled (H968) | Sonnet 5 `claude-sonnet-5` |

_Dr. Mārcis Gasūns_
