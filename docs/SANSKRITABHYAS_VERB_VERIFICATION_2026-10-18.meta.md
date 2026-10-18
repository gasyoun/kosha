# SANSKRITABHYAS_VERB_VERIFICATION_2026-10-18.md — metadoc

_Created: 18-10-2026 · Last updated: 18-10-2026_

## Purpose

Companion record for
[SANSKRITABHYAS_VERB_VERIFICATION_2026-10-18.md](https://github.com/gasyoun/kosha/blob/main/docs/SANSKRITABHYAS_VERB_VERIFICATION_2026-10-18.md),
the lane spec for using sanskritabhyas.in as an **independent** external witness on our
present-system verbal forms. The subject document answers: *what can the site verify, what
can it not, how do we read it, and what is the one thing blocking the run?* Its single
load-bearing fact is the split between verification (gaṇas 1/4/6/10 × four lakāras) and
coverage (everything else) — conflating the two would manufacture thousands of fake defects.

## Audience & use

- Whoever runs the crawl: §4 has the grabber and the access constraint (Cloudflare; user
  browser only).
- Whoever reads the agreement number: §2 fixes the denominator (4,700 kartari rows =
  42,300 cells), §3 the join and the ` / ` variant rule.
- Verb-pipeline work upstream: every DIFF that survives triage becomes an MWinflect issue,
  never a silent kosha patch.

## Maintenance

- Re-derive the headcount whenever `calc_tables.txt` changes: `wc -l` plus the
  `awk -F'\t'` gaṇa census in §2 — the numbers are measurements, not prose to be trusted.
- The grabber in §4 is the canonical copy; if it changes, bump the subject doc's
  `Last updated` and re-run the self-test in §5.
- Once the crawl has run, §8's status table becomes history: add a dated banner with the
  agreement figures, do not rewrite the scaffold numbers.
- The mobile duplicate (`d-lg-none`) is the trap: a parser that forgets it doubles every
  cell. Keep that warning even after the crawl.

## Related

- Comparator: [`scripts/sanskritabhyas_compare.py`](https://github.com/gasyoun/kosha/blob/main/scripts/sanskritabhyas_compare.py)
- Reference table: [MWinflect `calc_tables.txt`](https://github.com/sanskrit-lexicon/MWinflect/blob/main/verbs/pysanskritv2/tables/calc_tables.txt)
- Access dead end: [Uprava DEAD_ENDS §2](https://github.com/gasyoun/Uprava/blob/main/DEAD_ENDS.md)
- Sibling comparator (vidyut vs Cologne verbs): [`scripts/compare_vidyut_verbs.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_vidyut_verbs.py)

_Д-р Марцис Гасунс_
