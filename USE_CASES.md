# Use cases — Gasuns Sanskrit Dictionary

_Created: 02-07-2026 · Last updated: 02-07-2026_

Thirteen concrete scenarios the product must serve, in priority order of the
locked audience decision (**Translators > Learners > Scholars**, plus machine
consumers). Each names the actor, the trigger, the flow, the acceptance test,
and the phase of
[IMPLEMENTATION_PLAN.md](https://github.com/gasyoun/kosha/blob/main/IMPLEMENTATION_PLAN.md)
that delivers it. These are the seeds for `EVAL_PLAN.md`'s acceptance suite —
an executor session should turn each acceptance line into a real test.

| # | Actor | One-line scenario | Phase |
|---|---|---|---|
| UC1 | Translator | Disambiguate a gloss across MW+PWG+AP90 on one screen | P1–P2 |
| UC2 | Translator | Verify a suspicious reading against the printed page | P1–P2 |
| UC3 | Translator | Paste an inflected/sandhied form straight from a text | P1 (forms) / P4 (sandhi) |
| UC4 | Translator | Check whether a sense is actually attested, and where | P3 |
| UC5 | RU translator | Read the Russian gloss beside the German and English | P6 |
| UC6 | Student | Work through a Gītā verse word by word | P4–P5 |
| UC7 | Student | Look up `krsna` on a phone, no diacritics, offline in class | P2 |
| UC8 | Student | See how a word declines, at a glance and in full | P4 |
| UC9 | Student | Take the session's words home (Anki/CSV, reading packs) | P5 |
| UC10 | Scholar | Cite one sense, permanently, in a paper | P7 |
| UC11 | Scholar | Bulk-download the versioned dataset for offline analysis | P7 |
| UC12 | Corpus platform | Embed Cologne dictionary lookups via the Salt facade | P1/D4 (REST) · P7 (GraphQL) |
| UC13 | Reader app | Word-click glossing through the public API | P1 · P4 |

---

## Translators (primary audience)

**UC1 — Multi-dictionary disambiguation.** While translating a PWG card, the
German gloss is ambiguous. Search once (any scheme, auto-detected) → one page
with the MW, PWG, and AP90 entries stacked, per-block source attribution.
*Accept:* `dharma` returns all three dicts' entries in <1 s, each labeled,
each with its L-number.

**UC2 — Print-truth check.** A digitized reading looks wrong. Click the
entry's scan link → the exact printed page (page + column precision where the
dict's `<pc>` supports it). *Accept:* MW `banD` (L142512) links to p. 720
col. 1; 10-sample scan URLs return HTTP 200 (PHASE1_PLAN D3 check).

**UC3 — Paste the text's form, not the lemma.** The text has `rāmeṇa` or
`dharmakṣetre`. Paste it → lemma(s) + entries; ambiguous sandhi offers a
pick-a-split list. *Accept:* `bhagavān → bhagavant-` via the glossary (P1);
`dharmakṣetre` split offered (P4, gated ≥90 % top-1 on the gold sample).

**UC4 — Evidence, not authority.** Is this sense real usage or lexicographer's
inertia? Entry shows DCS attestation count, first-attestation era, genre
sketch, one cited example sentence. *Accept:* `dharma` shows band + counts +
≥1 attested example with source label (P3 exit check).

**UC5 — The Russian layer.** A Russian-speaking translator sees RU glosses
(approved pwg_ru cards; Kochergina if rights clear) beside DE/EN, each gloss
labeled with source + review status. *Accept:* P6 exit check; **only
`approved` cards ever display** — `ai_translated` never leaks to users.

## Students / learners

**UC6 — The Gītā-verse walkthrough.** Paste a whole verse → every word
resolves (form → lemma → plain gloss first); tap for depth. This is P5's
end-to-end acceptance script. *Accept:* a designated verse resolves every
word without a dead end.

**UC7 — Phone, no diacritics, no signal.** Types `krsna` → `kṛṣṇa` via SLP1
fuzzy matching; repeat lookups work offline (PWA static tier). *Accept:* P2
exit check (mobile + offline repeat-lookup).

**UC8 — "How does it decline?"** Headword shows the compact Zaliznyak-style
token (`m·8n*`); one tap opens the full vidyut-generated paradigm table.
*Accept:* a-stem, ī-stem, and one verb class render (P4 exit check).

**UC9 — Take-away artifacts.** Export the session's lookups as CSV/Anki;
download a per-chapter reading pack (pre-built glossary from DCS
lemmatization). *Accept:* Gītā 1 and Nala 1 packs exist and open (P5).

## Scholars

**UC10 — Permanent citation.** Copy a versioned sense citation
(`mw.142512.3@v0.2.0` + DOI) from the entry's Cite button (formatted +
BibTeX + CSL-JSON). *Accept:* the citation resolves in a fresh browser after
a later data release changed the entry (P7 exit check).

**UC11 — Bulk reuse.** Download the versioned data release (SQLite + dumps,
CC BY-SA 4.0 with the attribution block) and rebuild locally. *Accept:*
release assets are independently downloadable and rebuildable (P7).

## Machine consumers

**UC12 — Drop-in C-SALT provider.** A corpus platform (VedaWeb-style) points
its dictionary integration at kosha's Salt facade
(`/dicts/{id}/restful/entries|ids`, GraphQL by P7) and works unchanged.
*Accept:* parity vs csl-apidev's run-verified envelopes for
`agni`/`indra`/`ka`, incl. `-L{lnum}` homonym ids (P1/D4 check).

**UC13 — Reader integration.** A reader app calls `GET /api/v1/form/{form}`
per clicked word and renders the Salt-shaped entry + `kosha.*` extensions.
*Accept:* documented in the API docs page; SamudraManthanam performs the
first real integration (dogfooding target, post-P4).

---

_Dr. Mārcis Gasūns_
