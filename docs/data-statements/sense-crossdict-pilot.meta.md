# Data statement — sense-crossdict-pilot

_Created: 24-07-2026 · Last updated: 24-07-2026_

| Field | Value |
|---|---|
| Dataset id | `sense-crossdict-pilot` |
| Builder | [`scripts/build_sense_crossdict_pilot.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sense_crossdict_pilot.py) |
| Scope | **500-headword pilot only** (H1455 list) — not full inventory |
| Tier | public |
| Licence | CC BY-SA 4.0 (Cologne + DCS composition as for sibling concordance) |
| Handoff | H1587 · next-programme W2 |
| Model | Grok 4.5 (`grok-4.5`) |

## Provenance

- Pilot list: `data/concordance/sense_pilot_headwords.tsv`
- PWG senses + loci: `data/concordance/sense_corpus_concordance.tsv` (H1455)
- MW / Apte glosses: `kosha.db` `entries`+`senses` (read-only body spans)
- Viewer: `concordance/senses/crossdict.html`

## Limitations

- MW and Apte columns are **inventory** next to PWG, not automatic sense-alignment.
- Apte coverage is partial on the pilot (~half); nulls are honest.
- Full-inventory recon and human sample sheet are **out of scope** for this wave.

---

_Dr. Mārcis Gasūns_
