# Gasuns Sanskrit Dictionary — positioning distillation

_Created: 02-07-2026 · Last updated: 02-07-2026_

Executive distillation of
[POSITIONING.md](https://github.com/gasyoun/kosha/blob/main/POSITIONING.md)
(full review, Fable 5 `claude-fable-5`, 02-07-2026). One page; the long doc
carries the evidence and the caveats.

## The identity in one line

**"Logeion for Sanskrit" — and that slot is empty.** All major dictionaries
behind one fast search box, corpus-frequency-aware, student-usable. Sanskrit
has the silos (CDSL, ~40 dicts served one at a time) but nobody has built the
collapse.

## Three tracks, one program

1. **Improve the source** — csl-orig corrections (Cologne ground truth).
2. **Improve the shared Cologne UI** — csl-websanlexicon / csl-apidev /
   csl-app, upstream, for everyone.
3. **This project**: the advanced integration layer + Gasuns' own advanced UI
   at `samskrtam.ru/kosha` — the opinionated mixing of data that doesn't
   belong in Cologne's conservative frontend.

## The defensible intersection

No existing project occupies: **multi-dictionary × scan-anchored print-truth
× corpus-graded × trilingual (DE/EN/RU)**. The two original reference sites
set the bar — **michaelmeyer.fr/sanskrit** (speed: static precomputed pages)
and **sanskritdictionary.com** (features: encoding toggle, form lookup,
multi-dict view) — and the founding formula is *meyer's speed +
sanskritdictionary's features + the provenance and corpus evidence neither
has*. Ambuda/vidyut is the strongest modern neighbor — consume vidyut, never
re-implement it. Aggregators lose on provenance; CDSL itself is the
substrate, not a competitor.

## Six improvements, ranked by leverage

1. **Evidence-graded entries** — rank results and senses by DCS attestation;
   frequency band + era/genre badge on every lemma. Flagship; nobody has it.
2. **Paste-anything lookup** — sandhied/compounded/inflected text segmented at
   query time. Dictionary → reading companion.
3. **Generated paradigms + the Zaliznyak grammar token** (98,639 headwords
   already indexed) — a genuine innovation from the Russian tradition.
4. **Sense-level persistent IDs + DOI'd releases** — citable resource, not
   website. Cheap now, unretrofittable later.
5. **Offline PWA** — nearly free given the static-cache tier.
6. **Trilingual gloss layer** (MW-EN · PWG-DE · pwg_ru/Kochergina-RU) —
   unique worldwide; the underserved Russian-speaking audience is the wedge.

## The UI decision (recorded)

Fable recommended "no reader — be the best API." **M.G. overrode: the
dictionary gets its own advanced UI, its own way.** Reconciliation: the UI is
a client of the same public API (nothing is foreclosed for other consumers),
and it competes on the intersection above — not by cloning Ambuda's reader.

## Lineage

Böhtlingk–Roth → MW → Cologne digitization (1994–) → correction
infrastructure (csl-orig) → API-ification (Kosh/C-SALT) → **integration =
this project**. It writes no dictionary content and corrects nothing at
source; it adds the join + access layer — and it is the public face of a
decade of private plumbing (union headwords, pwg_ru, frequency bands,
Zaliznyak index, scan resolver) plus the working demonstration for the P1–P6
paper line.

## For students

Design target: a second-year with a Gītā verse on screen. Meet the *form*,
not the lemma (incl. diacritic-free typing); progressive disclosure (plain
gloss + frequency badge first, full apparatus one tap deeper); frequency
honesty (core-80 vs hapax — what to memorize vs look up and forget); one
attested corpus sentence per sense; Anki/CSV export + per-chapter reading
packs; free, offline, no login. The loop that no existing tool closes:
**form-lookup × frequency badge × paradigm table × corpus example =
look-up-to-learned.**

---

_Dr. Mārcis Gasūns_
