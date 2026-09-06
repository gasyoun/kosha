# SIGNOFF — A55 author-voice pass

_Created: 06-09-2026 · Last updated: 06-09-2026_

**Scope.** Manuscript [A55_UNION_HEADWORDS_DATA_PAPER_JOHD.md](https://github.com/gasyoun/kosha/blob/main/papers/A55_UNION_HEADWORDS_DATA_PAPER_JOHD.md) (JOHD data paper, ~1.6k words, data-paper register kept). Pass executed 06-09-2026 by Fable 5.1 (`claude-fable-5-1`) under handoff [H3857](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3857-Fable_Uprava_all-articles-author-voice-pass-workflow_01.09.26.md). Voice, register and framing only; no number, claim or citation altered; mechanical drift gate ([voice_drift_check.py](https://github.com/gasyoun/Uprava/blob/main/tools/voice_drift_check.py) against `origin/main`) CLEAN. No prior review memo and no prior signoff existed for this paper; this is pass 1.

## 1. Voice calls made — each may be vetoed

| # | Location | Call | Rationale |
|---|---|---|---|
| 1 | Header, under the title | Added the academic byline block: `Mārcis Gasūns, independent scholar (ORCID 0000-0003-4513-884X), gasyoun@ya.ru`; bumped `Last updated` to 06-09-2026. | The draft carried no author line; JOHD needs one. Affiliation wording is a human's to confirm (see flag 6). |
| 2 | Abstract, first sentence | "We present a union headword index" → "I present a union headword index". | Single-author paper (the Competing-interests line already says "The author"); first-person singular is the author's voice and JOHD allows it. Veto if the venue's house style prefers "we". |
| 3 | §1 Context | "…the intersection of Monier-Williams with the large Petersburg dictionary, an intersection mislabeled as a union" → "…, mislabeled as a union". | Removed the doubled noun; "exactly" and the claim itself untouched. |
| 4 | §2 Quality control | The nested-parenthesis sentence ("…exports (e.g. PWG 106,054 here vs. … (±≈150 keys each way for PWG); homograph collapse contributes none).") split into two sentences with the example moved out of the outer parentheses. | Two-level parentheses inside a data-paper QC paragraph read as a footnote inside a footnote; every figure and token kept verbatim. |
| 5 | §2 Limitations | "Most importantly, **attestation count is not corroboration.**" → "The chief limitation is that attestation count is not corroboration." | Empty opener plus bold-for-emphasis (de-AI checklist); the ranking ("most important") is preserved by "chief". |
| 6 | §4 Reuse potential, first sentence | "the load-bearing spine of several independent consumers" → "already serves as the headword spine of several independent consumers". | Dropped the decorative doubling ("load-bearing" on top of "spine"); "spine" is the paper's own term from the abstract and §1. |
| 7 | §4 Reuse potential, second paragraph | The "(a) **label** — …; (b) **label** — …" inline list rewritten as four plain sentences; each topic label kept as a topic ("coverage studies can ask…", "for NLP lexicon induction the index is…", "for the history of lexicography, the overlap matrix…", "in digitization QA, …"). | Bold labels with em-dash-as-copula are the de-AI pattern; the four cases, their order, the 323k figure and the ShareAlike sentence are unchanged. No label became a source attribution. |
| 8 | Provenance | One appended line recording this pass with the H3857 link and this signoff. | Required header note; the only place a pass note was added. |

Left deliberately as they were: the "(1) (2) (3)" inline numbering in §2 Steps (JOHD "Steps" convention); the dataset-description bullet list in §3 (JOHD template fields); the em-dash parentheticals in the abstract and §1 (genuine asides, not copulas); the passive constructions in §2 (method register).

## 2. Substance flags carried (not fixed)

1. **Repository location points at two releases.** §1 gives the asset link as `data-v0.1.0` while the dataset line, the DOI and §3 name `data-v0.4.0` (the re-cut that Zenodo archived). The text explains the re-cut, but JOHD's "Repository location" field should probably carry the DOI'd release; a human should decide which link goes in the template.
2. **Uncited reference.** The reference list carries *Gasuns Sanskrit Dictionary data release v0.5.0* (DOI 10.5281/zenodo.22105641), which the body never cites; the v0.4.0 entry is the one the paper uses. Also the list is not alphabetical (the two Gasūns entries sit after Monier-Williams). Neither touched.
3. **"Four lexicographic traditions" (§1) versus the author's standing two-traditions frame** (indigenous kośa versus European). §1 divides the fifteen members into European bilingual, Vedic special lexica, Buddhist Hybrid Sanskrit and Sanskrit-medium encyclopedias (with the Mahābhārata name index counted separately). Backlog item 2 already names §1 for a human pass; the count and grouping are substance and were not changed.
4. **Creation-dates line versus QC paragraph.** §3 says "member exports and union build 2025–2026" while §2 QC reconciles against "the frozen 2014-era exports" (`PWG-unique-key1-106085`). If the 2025–2026 exports are re-crawls of the 2014 frozen ones, a half-sentence in §3 would remove the apparent conflict.
5. **Delta wording in §2 QC.** PWG 106,085 → 106,054 is a net delta of 31, while the parenthesis says "±≈150 keys each way"; consistent as gross-versus-net, but a referee may stumble. Numbers untouched.
6. **Affiliation.** The added byline says "independent scholar"; the Funding statement says the dataset was produced "within the samskrtam.ru Sanskrit-education programme". A human should confirm which affiliation wording goes on the JOHD form. "Dataset creators" in §3 also lacks the ORCID that the JOHD template asks for.
7. **Readiness line** still reads "final human pass pending" — correct until this signoff is read and the readiness is bumped by a human.

## 3. Read-and-sign

- Estimated reading time: ~30 minutes (manuscript plus the eight calls above).
- Proposed readiness after a human read: 5/5 **proposed only** — the draft is already at 4/5 with all numbers re-verified and the DOI minted; what remains is the human ruling on flags 1–3 and 6 and the JOHD template transfer (Backlog item 3).
- Venue: JOHD data-paper track stands; no change recommended. Submission stays frozen until 2026-11-01 per the H3857 rule.
- To sign: reply in this chat with "signed" (or the veto numbers from §1), then bump the Readiness line in the manuscript.

_Dr. Mārcis Gasūns_
