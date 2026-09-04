# H4046 — end-to-end regeneration audit: `regen_checked` stamps on all 121 manifest rows

**Date:** 04-09-2026 · **Tier:** OxAlpha `zai-coding-plan/glm-5.3-flash` · **Box:** Mac

Every row of [data/manifest/datasets.json](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json)
now carries `regen_checked: "2026-09-04 (H4046: <verdict>)"` from the estate-wide
end-to-end regeneration audit ([full report](https://github.com/gasyoun/Uprava/blob/main/docs/REPORT_H4046_kosha_derived-datasets-regen-audit_04-09-2026.md)).

What the audit did before stamping:

1. **Repaired the missing pinned inputs first** (so a FAIL means "breaks even with
   inputs present"): `kosha.db` rebuilt via the full 10-stage DAG (489 s; entries
   444,773 and lemmas 323,425 exact, inflections 6,930,902 vs the H691-vintage
   6,916,522); `dcs_full.sqlite` rebuilt from sibling dcs-conllu after the old file
   was found **0-byte** (tokens **5,688,416 — exact**); `archive_stopword.sqlite`
   rebuilt (**40,573,260 parallels — exact**; needed `p7zip` on this box);
   `corpus.db` + offline packs rebuilt (744,151 lines — manifest's 580,552 stale).
2. **Ran 96 of the builders end-to-end** in throwaway worktrees (nothing committed
   to shared trees), `--check`/`--selftest` accepted, counts vs manifest at ±0.5%.
3. Verdict spread: **62 PASS · 15 run-green-but-stale-artifact · 17 FAIL outright**
   (6 builder defects — two Windows-hardcoded paths, three H1493 KeyError cascades,
   one LOST LFS input; 2 builder scripts absent from every clone on the audit box;
   9 box-input gaps) · 15 NOT-REBUILDABLE-by-design · rest deferred/network-gated.

The stamps are provenance, not a quality flip: the 15 stale-count rows still need
the follow-up kosha PR queued in the Uprava GTD (H4046 rows), and the 6 real
builder defects are red-invariant repairs, not advisories.
