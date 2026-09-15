# data/disciplines — dataset × discipline join (H4737)

Derived packet: every registered kosha dataset joined through the sibling
[IndologyScholars](https://github.com/gasyoun/IndologyScholars) meso→discipline
crosswalk to the ratified discipline taxonomy. The taxonomy is never re-derived
here; see [DATASET_DISCIPLINES_REPORT.md](DATASET_DISCIPLINES_REPORT.md).

- `dataset_disciplines.json` — per-dataset disciplines + coverage summary + crosswalk NOT-MAPPED sentinels.
- `dataset_disciplines.source.json` — provenance pin (this repo commit, sibling feedCommit, generatedAt).
- Build/verify: `python3 scripts/build_dataset_disciplines.py [--check]` from the repo root.
- Assignment layer (kosha-owned): `data/manifest/dataset_meso_assignments.json`.

_Гасунс_
