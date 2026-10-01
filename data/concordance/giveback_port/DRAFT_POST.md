# DRAFT — csl-inflect give-back post (Q3 morph payload, machine-decided triage)

**⛔ HUMAN-GATED — DO NOT POST FROM AN AGENT SESSION.** RELATIONS.md §2/§7:
humans send, agents draft; csl-inflect is dormant and noise-averse; the H185
Task B gate ("do NOT post without MG's explicit go-ahead") applies verbatim.
This file is the payload's public face once MG clears it — one message, on its
merits, with the TSVs offered rather than attached.

**Channel (MG's call):** a comment on
[csl-inflect #10](https://github.com/sanskrit-lexicon/csl-inflect/issues/10)
(Jim's Cologne-vs-Huet noun comparison — this is corpus evidence about the same
tables) **or** a standalone issue if MG prefers the give-back to stand alone.
One message either way, per the noise rule.

---

**Draft comment (post verbatim once cleared):**

> Following the Cologne-vs-Huet comparison here, we joined the Cologne
> MW-inflect tables against corpus attestation as an independent check: every
> form the Digital Corpus of Sanskrit tags with a real case+number, matched on
> a transliteration-normalizing key against the generated tables (MW headwords,
> no DCS input — 6.93M forms). The corpus attests **4,900 paradigm cells the
> tables don't emit**, frequency-sorted so the head is the common core of the
> language:
>
> - **Disagreements (2,212 cells):** the table fills the cell with a different
>   form, both named — e.g. `tvāt` (abl.sg of `tva`) attested 6,853× vs the
>   table's `tvasmāt`; `rājñ` (voc.sg of `rājan`) 5,212× vs `rājan`; `striyaḥ`
>   (nom.pl of `strī`) 1,434× vs `stryaḥ`.
> - **Empty cells (2,688):** no row at all — head of the list is the pronoun
>   paradigm (`asmai` dat.sg of `idam` 3,375×, `tasmai` 3,228×, `etasmin` 784×)
>   and irregular feminine/consonant stems (`mahātmā` 739×, `āpo` 635×) —
>   recognizably the same weak spots that made a hand-made pronoun patch
>   necessary in the first place.
>
> Method guards: finite verbs are excluded on the generator's own scope (680
> verbal lemmas vs 222,735 nominal), sandhi-only spellings are keyed to their
> unsandhied form, and every cell carries a `dcs:<sent_id>` locus so each claim
> is one click from its context. The two per-cell tables (CC BY-SA, DCS
> attribution included) are in our repo at
> `data/concordance/giveback_port/` — happy to re-cut them by stem class or
> post them here in full if that's easier for the comparison programs.

---

**Fact-pin (verified against the payload, 01-10-2026):** counts, head examples
and order all come from `ROUTING.json` + the two payload TSVs; the triage that
decided "owed" is mechanical (DCS `feat_case`) and published in
[MORPHOLOGY_GIVEBACK_TRIAGE_REPORT.md](../../MORPHOLOGY_GIVEBACK_TRIAGE_REPORT.md).
If the payload is ever rebuilt, re-check the numbers in this draft against the
new ROUTING.json before posting.

_Dr. Mārcis Gasūns (draft prepared by roadmap drain A02, OxAlpha)_
