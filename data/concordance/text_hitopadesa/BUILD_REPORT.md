_Created: 04-09-2026 · Last updated: 05-09-2026_

# Hitopadeśa per-text concordance pilot — build report (H4034)

_Created: 04-09-2026 · Built by `scripts/build_text_concordance_hitopadesa.py`_

The Tamilex "corpus dictionary" pattern over a Sanskrit text: a full concordance
of every word of the Hitopadeśa, each form feeding back into the kosha
dictionary (headword + numbered PWG senses). This is the **inverse view** of
the [H1455](https://github.com/gasyoun/kosha/blob/main/data/concordance/SENSE_CONCORDANCE_BUILD_REPORT.md)
sense-attestation layer — that layer walks (headword → sense → attestation),
this one walks (one text → every occurrence → dictionary senses). No new join
was invented: the H380 DCS-lemma→headword table, the H1455 sense layer, the
house locus format, the card-token URL encoder and the H4026 era badge are all
consumed, not re-derived.

## Coverage

| metric | value |
|---|---|
| tokens (every word occurrence listed) | 25,040 |
| distinct (surface, lemma) forms | 7,857 |
| distinct lemmas | 3,781 |
| chapters | Hitop, 0–4 (Prastāvikā + 4 books), 3,432 sentences |
| headword join (any method) | 7,503 forms — **95.5%** |
| PWG sense ids attached | 1,024 forms — **13.0%** |
| occurrence refs | every occurrence, document order, `Hitopadeśa, Hitop, <ch>, <sent>[.<sub>]` |

## Honest residue

- **4.5% no headword join (354 forms).** Dominated by DCS causative/
  denominative `-ay` stems (`avalokay`, `cintay`, `ālocay`, `vyāpāday` — 325
  VERB forms) which kosha keys under the root; the same residue class the
  reading packs already report. Indeclinables (`kadācid`, `viśeṣataḥ`) and
  `enad` make up most of the rest. Known join gap, not a concordance defect.
- **87% no sense ids.** The per-sense layer (`sense_corpus_concordance.tsv`)
  is frame-limited to H1455's pilot headwords — sense absence here means
  "headword outside the sense-build frame", NOT "no senses in PWG". Widening
  it is H1670's scale lane, deliberately out of scope for this pilot.
- The text slice is DCS text_id 189 (edition per DCS provenance table); the
  in-estate reading pack `hitopadesa-0` (900 tokens, Prastāvikā only) is a
  strict subset. Dating follows the Dharmamitra chronology join: **early-medieval,
  core c. 9th–10th c. CE, disputed** (`data/dating/work_dates.json`, tier canon_dm).

## Files

- [concordance.tsv](https://github.com/gasyoun/kosha/blob/main/data/concordance/text_hitopadesa/concordance.tsv) — one row per distinct (surface, lemma):
  upos, occurrence refs (document order), headword slp1 + link method +
  confidence, PWG sense ids, `/w/` card href.
- [text_hitopadesa.js](https://github.com/gasyoun/kosha/blob/main/data/concordance/text_hitopadesa/text_hitopadesa.js) + [index.html](https://github.com/gasyoun/kosha/blob/main/data/concordance/text_hitopadesa/index.html) — the
  concordance page (filterable, 500-row render cap) carrying the era badge.
- [MANIFEST.json](https://github.com/gasyoun/kosha/blob/main/data/concordance/text_hitopadesa/MANIFEST.json) — license + provenance + counts.
- [SPOT_CHECK_SAMPLE.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/text_hitopadesa/SPOT_CHECK_SAMPLE.md) — 10-form hand-verified sample,
  independent re-derivation, 10/10 PASS.

## License / rights

Source: DCS 2026 (`dcs_full.sqlite`), **CC BY 4.0** — license-gated ingest
discipline: the derived measurements here are free; bulk redistribution of the
underlying corpus stays gated (DharmaMitra memo precedent). Attribution in the
manifest and on the page.

## Reproduce

```
python3 scripts/build_text_concordance_hitopadesa.py
```

Deterministic over the pinned inputs; writes only `data/concordance/text_hitopadesa/`.

_Dr. Mārcis Gasūns_
