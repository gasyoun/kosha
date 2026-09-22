# csl-orig v02: pw = Kurzfassung, pwg = the 7-volume original — the labels are inverted vs intuition

_Created: 19-09-2026 · Last updated: 19-09-2026_

---
name: csl-orig-pw-pwg-naming-inversion
description: In csl-orig v02 (and Cologne CDSL generally), code `pw` is Böhtlingk's 1879 Kürzerer Fassung and `pwg` is the 1855-1875 Böhtlingk/Roth original — verify before any pw/pwg comparison
metadata:
  type: project
---

In csl-orig `v02/`, **`pw` = Böhtlingk's *Sanskrit-Wörterbuch in kürzerer
Fassung* 1879-1889** (the Kurzfassung) and **`pwg` = Böhtlingk/Roth
*Sanskrit-Wörterbuch* 1855-1875** (the 7-volume original — the German
dictionary kosha serves). Proof: the sources' own
`v02/pw/pwheader.xml` / `v02/pwg/pwgheader.xml` `<titleStmt>` titles; the
csl-orig README agrees ("PWG (large), PW (small)"); data agrees (pwg articles
are the massive ones — `gam` 114.9 KB vs 33.4 KB body; pwg has 2.25× the
`<ls>` citations).

Two traps recorded with it (H4805, 19-09-2026):

1. BOTH the 14-09-2026 shortlist cand.5 / handoff H4805 premise AND the
   first landing (kosha PR #597) had the labels swapped; a verifier pass
   corrected the report + manifest row same-day. Any pw/pwg work must
   re-check the header files, not the handoff prose.
2. The original's (`pwg.txt`) on-disk keying is thin: 106,082 distinct `k1`
   vs pw's 151,349, and bare roots can be absent from both inventories
   (`kf` = √kṛ has no `<k1>kf<` in either file). "Present in pw but not
   pwg" is often "original article not on disk", not a Kurzfassung cut.

Measured artifacts: kosha `data/concordance/pw_pwg_*` (H4805), report
`PW_KURZFASSUNG_CUT_REPORT.md` (Verifier addendum section).

_Гасунс_
