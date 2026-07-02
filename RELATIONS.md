# Ecosystem relations — who we ask, what we offer, when

_Created: 02-07-2026 · Last updated: 02-07-2026_

The diplomacy plan for the Gasuns Sanskrit Dictionary (kosha), authored on
Fable 5 (`claude-fable-5`, 02-07-2026). kosha is track 3 of a three-track
program ([POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md)
§0): tracks 1–2 (source corrections upstream, shared-UI contributions) earn
the standing that track 3 spends. Every external relationship below exists to
protect that standing. Live survey behind the claims:
[COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md)
(02-07-2026).

## 0. Principles

1. **Lead with what kosha gives, not what it takes.** Every first contact
   opens with a concrete contribution (a parity-tested Salt implementation, a
   measured bug report, a gold-sample evaluation), never with a request.
2. **Contact when there is something live to show.** No "we're planning to…"
   emails. Triggers are phase exits, recorded in §7.
3. **Humans send, agents draft.** Every message below is a draft for M.G.'s
   signature and judgment; no agent sends outward mail or posts on M.G.'s
   behalf.
4. **The Meyer rule: never ingest anyone's own digitization without written
   permission.** Aggregating from Cologne is licensed reuse (CC BY-SA);
   taking another scholar's self-digitized data is not, whatever a scraper
   can technically reach.
5. **Noise is the cardinal sin.** Cologne maintainers have pushed back on bot
   comment/commit noise before (measured, not assumed). One well-timed,
   substantive message per party beats a stream of updates. Public, async
   channels (a GitHub issue) beat email where both work.
6. **Upstream what belongs upstream** — the decision table in §5 is binding;
   track 3 never hoards a fix that tracks 1–2 should carry.

## 1. Michaël Meyer — the permission ask

**Who:** Michaël Meyer ([michaelmeyer.fr/sanskrit](https://michaelmeyer.fr/sanskrit);
GitHub [michaelnmmeyer](https://github.com/michaelnmmeyer)); PhD on vyākaraṇa
and non-dual Kashmir Śaivism; ERC-DHARMA, CNRS, Paris — per his own pages,
verified 02-07-2026. He built the closest existing thing to "Logeion for
Sanskrit": 41 dictionaries on one page, per-sense scan links for 19.

**What is HIS and therefore off-limits without permission:** the **seven
indices he digitized himself** — Renou ×3, Tāntrikābhidhānakośa, Bergaigne,
Caland-Henry, Whitney emendations — plus his cross-reference clusters and his
site code. The Cologne-encoded dictionaries on his site are *not* his and
kosha takes those from Cologne anyway. **Standing rule: none of Meyer's own
work enters kosha, ever, without his written yes.** If he declines or never
answers, kosha ships without those indices — no scraping, no "it was
publicly visible" rationalization.

**What we ask:** permission (and ideally source files) to serve his seven
self-digitized indices inside kosha, under a license of his choosing, with a
per-entry attribution block naming him.

**What we offer:** loud credit; corrections our pipeline finds in that data
flow back to him; versioned, DOI-backed citability for his indices (his site
has no versioning — we add durability, not competition); an open API he is
welcome to consume in return.

**When:** after the P2 alpha is live — the ask is credible when there is a
running site to point at, not a plan. Mirrored as an `@DO` for M.G. in
[Uprava/GTD_NEXT_ACTIONS.md](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md)
at P2 exit.

**Draft (English; offer to continue in French):**

> **Subject:** Your Sanskrit indices — a permission question from a Cologne
> contributor
>
> Dear Dr. Meyer,
>
> I am Mārcis Gasūns, a long-time contributor to the Cologne Digital Sanskrit
> Dictionaries (corrections to MW/PWG/AP90 sources through the csl-orig
> change-file workflow). Your site is, in my view, the best thing that has
> happened to Sanskrit dictionary access in years — the per-sense scan links
> and the phoneme-aware search especially; I have studied both closely and
> say so in writing in my project's comparison notes.
>
> I am building an open, API-first dictionary layer over the Cologne data
> (working title: Gasuns Sanskrit Dictionary, at samskrtam.ru/kosha —
> versioned data releases, sense-level citable IDs, morphology and corpus
> evidence attached; alpha at [URL]). The Cologne dictionaries I take from
> Cologne directly. My question concerns only the seven indices you digitized
> yourself — Renou, the Tāntrikābhidhānakośa, Bergaigne, Caland-Henry, the
> Whitney emendations: would you permit their inclusion, under whatever
> license and attribution you set? I would credit you on every entry, send
> back any errors my pipeline surfaces, and version the data so citations to
> it remain stable. If you would rather they stay only on your site, that of
> course settles it — I will not use them without your explicit permission.
>
> Si vous préférez correspondre en français, bien volontiers.
>
> With admiration for the work,
> Mārcis Gasūns

## 2. Cologne maintainers (Jim Funderburk, Dhaval Patel; Thomas Malten)

**Posture:** kosha is a *consumer and second implementer*, not a fork and not
a rival frontend. The maintainers are noise-averse — our own local rule
already forbids PR streams to csl-orig (batched ~monthly). The framing that
works leads with service to *their* standard:

> **The framing paragraph (reuse verbatim when the moment comes):** kosha is
> a second, independent implementation of the Salt API profile
> ([SALT_API_PROFILE](https://github.com/sanskrit-lexicon/csl-standards/blob/main/docs/SALT_API_PROFILE.md)),
> parity-tested against csl-apidev's run-verified envelopes, reading the same
> [csl-sqlite releases](https://github.com/sanskrit-lexicon/csl-sqlite/releases).
> Corrections it surfaces flow through the canonical csl-orig change-file
> queue, as they always have. Where Salt's `sense` face is still TODO, kosha
> has working versioned sense IDs to offer as a reference design.

**Channel + timing:** nothing until G-SALT parity actually passes
([EVAL_PLAN.md](https://github.com/gasyoun/kosha/blob/main/EVAL_PLAN.md) §3).
Then **one** public artifact: a csl-standards issue (or a comment on the
existing Salt profile thread) announcing the second implementation and
offering the sense-face design. The wider announcement waits for P7
(csl-newsletter + INDOLOGY, already in
[IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md)).

**Don'ts:** no bot comments; no unsolicited UI critique ("we fixed your
frontend" framing is poison — track 2 contributions go as ordinary upstream
PRs on their merits); no new correspondence channels when a GitHub issue
suffices.

## 3. Ambuda / Arun Prasad (vidyut)

**Posture:** consume, never compete
([POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md)
§1). vidyut-kosha/vidyut-prakriya are MIT-licensed developer libraries with no
end-user UI — kosha putting a UI on them is the intended use of a library,
but courtesy and credit are owed, and the **name collision is real**:
`vidyut-kosha` exists, so the public product name is **Gasuns Sanskrit
Dictionary**; "kosha" stays an internal repo codename precisely for this
reason. Never brand outward as "Kosha".

**Give-back:** the G-SEG gold-sample report evaluates vidyut-cheda on 200
stratified forms — that report, with the error table, is a genuinely useful
upstream artifact. File it as a GitHub issue/discussion on the vidyut repo at
P4, with data attached. Any vidyut bugs found (the ecosystem's own
sanskrit-util had a ळ→`x` class bug — [FINDINGS §39](https://github.com/gasyoun/SanskritLexicography/blob/master/FINDINGS.md) —
so we look for the same class in what we consume) are reported with minimal
repro cases. Credit vidyut on the paradigm/segmentation surfaces in the UI
and docs.

**Channel + timing:** GitHub (his native medium), first contact = the P4
gold-sample report. No earlier "heads-up" mail needed — MIT reuse with credit
is the normal course.

## 4. C-SALT / CCeH (the Kosh team, Cologne Center for eHumanities)

**What we have for them:** Salt's `sense` face is TODO upstream; kosha will
have working, versioned, sense-level IDs (`{dict}.{L}.{senseN}@data_version`,
[ARCHITECTURE.md](https://github.com/gasyoun/kosha/blob/main/ARCHITECTURE.md)
A2) plus a run-verified second implementation of the REST faces. That is a
reference design for the profile's open TODO, offered publicly.

**Channel + timing:** the same csl-standards issue as §2 (one artifact serves
both audiences — csl-standards is where the profile lives and where CCeH-side
eyes already are). After D4 parity + first sense IDs minted. If the Kosh team
engages, the GraphQL face port (P7) is the natural second touchpoint.

## 5. Upstream-vs-track-3 policy (binding decision table)

| Finding / artifact | Destination |
|---|---|
| Dictionary text error (any dict) | csl-orig correction queue (`/cologne-correction-queue`), monthly batch PR — **never** patched in `kosha.db` |
| Renderer bug that also exists in the canonical csl-websanlexicon template | upstream PR to [csl-websanlexicon](https://github.com/sanskrit-lexicon/csl-websanlexicon) first; kosha's port picks it up on next sync |
| Renderer behavior that is a kosha design opinion | track 3, stays here |
| Salt profile ambiguity or bug found during parity work | [csl-standards](https://github.com/sanskrit-lexicon/csl-standards) issue |
| Sense-ID scheme | offered upstream (§4); maintained in kosha until/unless adopted |
| Segmentation / paradigm bug in vidyut | upstream issue to Ambuda/vidyut with repro |
| Transcoding bug | [sanskrit-util](https://github.com/sanskrit-lexicon/sanskrit-util) (the shared home) — never a local workaround without an upstream issue filed |
| Merged multi-dict view, evidence layer, RU layer, own UI | track 3 by definition ([POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md) §0) — deliberately not upstreamed |

## 6. The rest of the map (short form)

- **DCS / Oliver Hellwig:** kosha consumes the CoNLL-U dump for the evidence
  layer. Known license tension: the site is CC BY 3.0 but the GitHub dump
  carries **no license file** ([COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md)
  §8). **Before P3 ships publicly, M.G. asks Hellwig to confirm/clarify the
  dump's license** (short, single email; also flags our attribution format).
  Mirror as `@DO` at P3 start. Every evidence badge carries DCS attribution +
  BibTeX regardless.
- **Sanskrit Heritage / Gérard Huet + UoHyd:** use the UoHyd mirror only (the
  Inria host is Anubis-walled, verified 02-07-2026). If Heritage wins G-SEG
  and gets wired, a courtesy note to Huet + prominent credit; Heritage's
  pick-a-split UX is also credited as the design source of ours.
- **VedaWeb → Tekst:** mid-migration (archived 16-02-2026); hold any
  integration until URLs settle. The C-SALT seam (§4) is the eventual path —
  a Tekst-side dictionary panel pointing at kosha's Salt facade is UC12's
  dream consumer.
- **Wisdom Library, sanskritdictionary.com, learnsanskrit.cc:** no
  relationship needed; ideas learned from them are credited in
  [COMPARISON.md](https://github.com/gasyoun/kosha/blob/main/COMPARISON.md)
  ("steal with attribution of the idea").
- **Zaliznyak / gramdict:** the compact grammar token borrows Zaliznyak's
  *scheme* (with credit); the token **data** kosha ships is derived in-house
  from the WhitneyRoots reverse-index work. The gramdict *dataset* is
  CC BY-NC and must not be folded into kosha's CC BY-SA data releases — see
  [RISKS.md](https://github.com/gasyoun/kosha/blob/main/RISKS.md) R6.
- **Kochergina estate:** P6 rights decision, M.G. personally
  ([IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md)
  P6 Gate 2). Kossovich 1854 is public domain and needs no ask.
- **SamudraManthanam:** in-house — the UC13 dogfooding consumer, no diplomacy
  required, but its integration report is public proof for §2–§4 claims.

## 7. Contact registry (state as of 02-07-2026)

| # | Party | Channel | Trigger (when to contact) | Ask | Offer | Status |
|---|---|---|---|---|---|---|
| 1 | Michaël Meyer | email (his site's contact) | P2 alpha live | permission: 7 self-digitized indices | attribution, corrections back, versioned citability | not contacted |
| 2 | Cologne maintainers | csl-standards issue | G-SALT parity green (P1/D4) | none — announce + offer sense-face design | second Salt implementation | not contacted (standing relationship via corrections) |
| 3 | Arun Prasad (Ambuda/vidyut) | GitHub issue on vidyut | P4 gold-sample report done | none | G-SEG evaluation report + bug repros | not contacted |
| 4 | C-SALT / CCeH (Kosh) | same csl-standards issue as #2 | D4 + first sense IDs | feedback on sense-face design | reference implementation | not contacted |
| 5 | Oliver Hellwig (DCS) | email | before P3 goes public | dump license clarification | attribution format, usage report | not contacted |
| 6 | Gérard Huet / UoHyd | email | only if Heritage wins G-SEG | none | credit, integration note | not contacted |
| 7 | Kochergina rights holder | M.G. personally | P6 | reprint rights | — | not contacted |

All sends are M.G.'s (principle 3). Each trigger, when it fires, becomes an
`@DO` row in
[Uprava/GTD_NEXT_ACTIONS.md](https://github.com/gasyoun/Uprava/blob/main/GTD_NEXT_ACTIONS.md)
in the same session that fires it.

---

_Dr. Mārcis Gasūns_
