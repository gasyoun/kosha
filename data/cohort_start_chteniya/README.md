_Created: 01-08-2026 · Last updated: 01-08-2026_

# Cohort pack freeze — «Старт чтения»

Pinned copies of owned pedagogy packs for the 5-week Akro-style pilot.
**Freeze only** — no new linguistics. Systema vendors this tree under
`resources/data/cohort_start_chteniya/` (H2106).

| File | Source | Role |
|---|---|---|
| [MANIFEST.json](https://github.com/gasyoun/kosha/blob/main/data/cohort_start_chteniya/MANIFEST.json) | this freeze | slug, paths, sha256, gloss notes |
| [hitopadesa-0.json](https://github.com/gasyoun/kosha/blob/main/data/cohort_start_chteniya/hitopadesa-0.json) | `reading/data/hitopadesa-0.json` | interim continuous prose (week 3) |
| [subhashita_beginner_pack.json](https://github.com/gasyoun/kosha/blob/main/data/cohort_start_chteniya/subhashita_beginner_pack.json) | `data/subhashita/subhashita_beginner_pack.json` | beginner literature band |
| [sandhi_drills_l1_l3.json](https://github.com/gasyoun/kosha/blob/main/data/cohort_start_chteniya/sandhi_drills_l1_l3.json) | `data/sandhi/sandhi_drills.json` (lesson ≤ 3) | 30 MCQ drills |
| [sandhi_curriculum_l1_l3.tsv](https://github.com/gasyoun/kosha/blob/main/data/cohort_start_chteniya/sandhi_curriculum_l1_l3.tsv) | `data/sandhi/sandhi_curriculum.tsv` (lesson ≤ 3) | 10 rules |
| [lemmas_for_srs.tsv](https://github.com/gasyoun/kosha/blob/main/data/cohort_start_chteniya/lemmas_for_srs.tsv) | derived from the two reading pins | optional SRS lemma feed |

## Schema note

- **hitopadesa-0** = `reading_pack_v1` (`sentences[].tokens[]`) — same shape as Systema’s Nala-1 vendor.
- **subhashita-beginner** = different family (`sayings[]` / `lines[].chunks[]`). H2110 must adapt; do not invent a silent second schema. Adapter note is in `MANIFEST.json`.

## Verify

```bash
python scripts/freeze_cohort_start_chteniya.py --check
```

Rebuild pins (after source pack updates):

```bash
python scripts/freeze_cohort_start_chteniya.py
```

Handoff: [H2109](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2109-Sonnet_kosha_start-chteniya-pack-freeze_01.08.26.md).
Plan: [PLAN_AKRO_START_CHTENIYA_2026](https://github.com/gasyoun/Uprava/blob/main/docs/PLAN_AKRO_START_CHTENIYA_2026.md).

_Dr. Mārcis Gasūns_
