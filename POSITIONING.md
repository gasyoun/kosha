# Gasuns Sanskrit Dictionary — comparative positioning review

_Created: 02-07-2026 · Last updated: 02-07-2026_

A judgment-tier review requested by M.G. on 02-07-2026: how the Gasuns Sanskrit
Dictionary (working codename **kosha**, deployment target `samskrtam.ru/kosha`)
compares to other digital-humanities dictionary projects, where it can be
drastically improved, how it sits in the digital-Sanskrit-lexicography lineage,
and what would make it genuinely best for Sanskrit students. Authored on
Fable 5 (`claude-fable-5`); external-project states are as of the model's
January 2026 knowledge cutoff — re-verify any competitor claim before citing it
in print. Executive distillation:
[POSITIONING_SUMMARY.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING_SUMMARY.md).

## 0. The three tracks — what "Gasuns" means here

This project is the third track of a single sustained program, and the review
below is about track 3 only:

1. **Improving the source.** Corrections to the Cologne dictionaries
   themselves, through the canonical csl-orig change-file workflow — the
   scholarly ground truth this dictionary stands on.
2. **Improving the Cologne UI.** Contributions to the existing access layer —
   csl-websanlexicon, csl-apidev (Salt/Kosh API), csl-app — upstream, for
   everyone.
3. **The advanced integration layer at `samskrtam.ru/kosha`** — Gasuns' own
   server, his own way of mixing the data (multi-dict × corpus evidence ×
   morphology × scans × trilingual glosses) **and his own advanced UI**. Track
   3 is deliberately *not* upstreamed: it is where design opinions that don't
   belong in Cologne's conservative frontend get to exist.

Tracks 1–2 earn the right to track 3: the same person correcting the source
and maintaining the shared UI is the one best placed to build the opinionated
layer above them.

---

## 1. The comparative landscape

The honest one-line placement: **kosha is "Logeion for Sanskrit" — and nobody
has built that yet.**

[Logeion](https://logeion.uchicago.edu/) (U. Chicago) is the DH benchmark for
what kosha wants to be: *all* the major Greek/Latin dictionaries behind one
fast search box, corpus frequency data, textbook cross-references, a mobile
app. Its lesson is that the winning move in classical-language lexicography was
never a new dictionary — it was **collapsing the silos** over dictionaries
that already existed. Sanskrit has the silos (CDSL serves ~40 dictionaries,
one at a time) but not yet the collapse.

The field around kosha:

| Project | What it is | What kosha takes / where kosha differs |
|---|---|---|
| **CDSL Cologne** (+ csl-websanlexicon, Kosh/C-SALT APIs) | The authoritative data layer, ~40 dicts, since 1994 | kosha *is* a consumption layer over it (M3); differs by multi-dict view, form lookup, and modern latency. Not a competitor — the substrate |
| **Ambuda / vidyut** (A. Prasad) | The strongest modern Sanskrit DH stack: Rust morphology (`vidyut-prakriya` generates from Pāṇinian rules), `vidyut-kosha`, a reader with word-click analysis | The bar for engineering quality. kosha should **consume vidyut, never compete with it** — and must not pretend the name collision away: `vidyut-kosha` exists; kosha's identity has to be "the multi-dictionary + print-scan + trilingual layer", which Ambuda does not do |
| **Sanskrit Heritage** (G. Huet) | Segmentation + morphology since the 1990s, lexicon-limited | Sandhi/compound segmentation at query time — the one Heritage capability kosha's student story needs (via vidyut or Heritage, whichever measures better) |
| **DCS** (O. Hellwig) | The lemmatized corpus, ~5.6 M tokens | The **evidence layer**: attestation counts, first-attestation era, per-genre bands. Already banded in-house (`dcs_freq` 1–5, hapax/core-80 flags) |
| **VedaWeb** (Cologne) | Per-word RV morphology + accent, CC BY | Model of corpus-anchored lexicography; validation set for the accent axis |
| **michaelmeyer.fr/sanskrit** | One of the **two original reference sites** ([KOSHA_REFERENCE_ANALYSIS.md](https://github.com/gasyoun/SanskritLexicography/blob/master/KOSHA_REFERENCE_ANALYSIS.md)) — the speed benchmark: static precomputed pages, near-instant lookup, AP59 scan links | Proof that precomputation beats server rendering for dictionary lookup; the static-cache tier is this insight, generalized. kosha adds what it lacks: multi-dict view, morphology, corpus evidence, provenance |
| **sanskritdictionary.com** (+ Wisdom Library, learnsanskrit.org) | The other **original reference site** — the feature benchmark: encoding toggle, inflected-form lookup, multi-dict view; the rest are aggregators, fast but provenance-thin | The founding formula was "meyer's speed + sanskritdictionary's features"; kosha's differentiator against all of them is **print-truth**: every entry linked to the scanned page, every datum carrying its source + version |
| **ELEXIS / Lexonomy / OntoLex-Lemon / TEI-Lex0** | The European retro-digitization infrastructure | Where dictionary *publishing* went: standardized models, APIs, citable versioned releases. kosha's "persistent IDs + provenance, DOI-ready" decision is aligned but not yet concrete — the MDF/third-export-schema discussion ([csl-standards#1](https://github.com/sanskrit-lexicon/csl-standards/issues/1)) is the natural anchor |
| **TLFi / OED online / TLL digital** | Big-language digital lexicography | The provenance-and-citation standard to imitate; also proof that sense-level persistent IDs are what makes a dictionary *citable in scholarship* |

Two structural facts fall out of this table. First, **every ingredient kosha
needs already exists** — dictionaries (CDSL), morphology (vidyut/Heritage),
corpus evidence (DCS), scans (Cologne), translations (mw_ru/pwg_ru), grammar
index (the Zaliznyak-token work). The project is *pure integration*, which is
why the reuse-first mandate (M3) is not just hygiene, it is the thesis.
Second, **no existing project occupies the intersection**: multi-dictionary ×
scan-anchored × corpus-graded × trilingual (DE/EN/RU). That intersection is
kosha's defensible identity.

## 2. Drastic improvements over the current plan

The Phase-1 plan is deliberately minimal (spine → entries → morphology → API).
Ranked by leverage, what would change kosha's league:

1. **Evidence-graded entries — the flagship.** Rank search results and order
   senses by DCS attestation, and stamp every lemma with the in-house
   frequency band (`dcs_freq` 1–5, hapax flag, core-80 flag, genre/era
   profile — all already computed for pwg_ru). "Attested 1,234× in DCS, first
   in the Rigveda, mostly epic" on every headword. No Sanskrit dictionary
   interface does this; it is also the direct delivery vehicle for the
   evidence-graded-lexicography research program
   ([ROADMAP_2026_2027.md](https://github.com/gasyoun/SanskritLexicography/blob/master/ROADMAP_2026_2027.md)).
2. **Paste-anything lookup.** Students meet *sandhied, compounded, inflected*
   text, not citation forms. Query pipeline: try form→lemma glossary → try
   segmentation (vidyut / Heritage) → offer splits. This single feature is the
   difference between "dictionary website" and "reading companion".
3. **Generated paradigms on every entry** via vidyut-prakriya + the compact
   Zaliznyak-style grammar token (`m·8n*`) from the reverse-index work —
   98,639 headwords already indexed. A full declension table one tap away,
   plus a *compact* index token for print/export. Nobody else has the
   Zaliznyak layer; it is a genuine innovation imported from the Russian
   lexicographic tradition.
4. **Citable, versioned releases.** Sense-level persistent IDs + a DOI per
   data release + an OntoLex-Lemon/TEI-Lex0 (or MDF) export. This is what
   separates a DH *resource* from a DH *website*, and it is cheap if designed
   in now and nearly impossible to retrofit.
5. **Offline PWA.** The static-cache tier (M4) is 90 % of an offline app
   already; a service worker over the top-N cache gives students a
   no-connectivity dictionary — Logeion needed native apps for this, kosha
   gets it almost free.
6. **Trilingual gloss layer.** MW (EN) + PWG (DE) + pwg_ru/Kochergina (RU) on
   one screen. Unique worldwide; especially decisive for the Russian-speaking
   student audience nobody else serves.

On the reader/UI question there was a disagreement, resolved by M.G. on
02-07-2026 and recorded here. Fable's recommendation was "don't build a
reader — Ambuda owns that ground; be the best API a reader can call."
**M.G. overrode it: the Gasuns Sanskrit Dictionary will have its own advanced
UI, its own way**, at `samskrtam.ru/kosha`. The reconciled position, which
both sides of the argument support:

- **API-first architecture stays.** The own UI is built as *a client of the
  same public API* — so the investment in the UI never forecloses other
  consumers (Ambuda, SamudraManthanam, anyone), and the API remains the
  citable scholarly surface.
- **The UI competes on the identity, not on Ambuda's features.** Its ground
  is the intersection Ambuda doesn't occupy: multi-dictionary comparison,
  scan-anchored print-truth, evidence badges, the trilingual DE/EN/RU layer,
  the Zaliznyak grammar token. A text-reading surface can grow out of that
  lookup-first identity (corpus sentences → passage view) rather than by
  cloning a reader.

## 3. Fit in the digital Sanskrit lexicography line

The lineage runs: Böhtlingk–Roth 1855–75 → MW 1899 → **digitization** (Cologne,
Malten, 1994–) → **correction infrastructure** (csl-orig change-file workflow,
Funderburk/Patel) → **API-ification** (csl-apidev, C-SALT/Kosh, 2020s) →
**integration** — dictionaries joined to corpus, morphology, scans, and
translations. Each generation kept the previous one's asset intact and added a
layer. kosha is squarely the fourth layer: it writes no dictionary content,
corrects nothing at source (corrections keep flowing through the canonical
csl-orig pattern and reach kosha at rebuild time), and adds *join + access*.

Within M.G.'s own program it is the public face of a decade of private
plumbing: union headwords → mw_ru/pwg_ru translations → DCS frequency bands →
Zaliznyak grammar index → scan resolver — every one of these currently lives
in repos a student will never open. kosha is where that stack finally faces
users, and simultaneously the demonstration artifact for the P1–P6 paper line
(a working evidence-graded dictionary is a stronger argument than any journal
figure).

The lineage also dictates the discipline: the 02-07-2026 audit showed how
easily this layer can rot into fiction (invented `<pc>` semantics, imaginary
endpoints). The Cologne line survived thirty years on source-truth and audit
trails; kosha inherits that or it does not belong in the line. Hence the
measurement-gated plan: no ✅ without a passing check.

## 4. Best for Sanskrit students

Design target: a second-year student with a Gītā verse on their screen.

- **Meet the form, not the lemma.** `bhagavān` → `bhagavant-` (glossary layer,
  Phase 1) and eventually any sandhied string (improvement #2). Diacritic-free
  typing — `krsna` finds `kṛṣṇa` — via SLP1 fuzzy matching (the approach is
  already canonicalized in-house, [SHARED_CODE.md §12](https://github.com/gasyoun/github-spine/blob/main/SHARED_CODE.md)).
- **Progressive disclosure.** First screen: headword, one or two plain glosses,
  frequency badge, tiny paradigm token. Everything else — full MW/PWG
  apparatus, citations, scans, etymology — one tap deeper. Learner speed and
  scholarly depth are the same page at different depths, not different sites.
- **Frequency honesty.** The core-80/hapax badges tell a student what to
  memorize and what to look up and forget — the single highest-value signal a
  dictionary can give a learner, and the one print dictionaries structurally
  cannot.
- **Corpus examples with translations.** One attested sentence per sense where
  the aligned corpus (1.09 M Sa→Ru pairs; DCS for Sa-only) can supply it —
  real usage, not invented examples.
- **Take-away artifacts.** Export lookups as CSV/Anki deck; pre-built "reading
  packs" (per-chapter glossaries for standard texts, generated from the DCS
  lemmatization of that text). Cheap to generate, enormously sticky
  pedagogically.
- **Zero friction.** Free, no login, no ads, offline-capable, fast on a phone
  (the static tier is CDN-cached by construction). The audience that most
  needs Kochergina + PWG in one place — Russian-speaking students — currently
  has the *worst* tooling; the trilingual layer is aimed at them.

The compounding effect matters more than any single feature: form-lookup ×
frequency badge × paradigm table × corpus example is a complete
*look-up-to-learned* loop, and no existing Sanskrit tool closes that loop.

---

_Dr. Mārcis Gasūns_
