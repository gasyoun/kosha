# Sense-alignment adjudication rubric (blind)

_Created: 22-09-2026 · Last updated: 22-09-2026_

Each card is one row of an automatic cross-dictionary sense aligner. The aligner claims
that the dictionary senses printed on the card all denote the SAME meaning of the
Sanskrit headword `lemma` (SLP1 transliteration). PWG = Böhtlingk-Roth (German),
MW = Monier-Williams, Apte, MD = Macdonell (English), SKD = Śabdakalpadruma (Sanskrit,
IAST), VCP = Vācaspatyam (Sanskrit). Glosses may be truncated.

For every card decide:

- verdict: `same` — the senses denote the same meaning (for a multi-meaning entry,
  the claimed meaning is among those printed for the same lexeme);
  `different` — they do not; `unsure` — the printed text is too short or garbled to decide.
- near_miss: `yes` only for a `different` verdict that is close: metonymy, a
  part-of-speech variant of the same meaning, or a sibling referent (e.g. two plants
  of one genus). Otherwise `no`.
- failure_shape (only for `different` cards that carry an SKD line; else `n/a`):
  `dhatu-vs-noun` — the SKD text is a verbal-root (dhātu) entry (grammar of a
  root: gaṇa, pada, seṭ/aniṭ, dhātupāṭha citations such as "iti kavikalpadrumaḥ",
  meanings given as locatives like "gatau") while the other side is a nominal meaning;
  `other-homonym` — the SKD text is a nominal entry for the same headword string but a
  different lexeme/meaning; `other` — anything else (describe in the note).
- note: one short sentence with the evidence.

Judge only from the card text. Do not look anything up.

Both adjudicators (H5252) received exactly this rubric and the output of
`python scripts/render_selective_risk_deck.py --deck data/concordance/selective_risk_skd/review_deck.tsv --width 400`.

_Гасунс_
