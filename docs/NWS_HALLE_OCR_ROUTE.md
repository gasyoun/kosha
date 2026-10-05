# NWS-Halle remainder OCR route (H6067 · epic E025)

_Created: 05-10-2026 · Last updated: 05-10-2026_

_Driver: [`scripts/ocr_halle_route.py`](https://github.com/gasyoun/kosha/blob/main/scripts/ocr_halle_route.py) · tests: [`tests/test_ocr_halle_route.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_ocr_halle_route.py)_

The batch OCR **route** for the undigitized remainder of the Nachtragswörterbuch
project (MLU Halle): manifest → engine → per-page QC → receiver-shaped export.
The route is built and proven offline; the **run over the real remainder pages
is externally gated** (see Status below).

## Status of the data (why the route, not a run)

- The local `layers/nws.tar.gz` (167,991 lemmas) is the **digitized** part —
  analysis in [`NWS_HALLE_ANALYSIS_2026-10-04.md`](https://github.com/gasyoun/Uprava/blob/main/papers/A61_wsc/NWS_HALLE_ANALYSIS_2026-10-04.md).
- The **undigitized remainder** is confirmed to us only via the H5940 letter
  (license + metadata ask to Prof. Slaje / MLU; MG visa pending — GTD
  @WAITING NWS-HALLE). Its page images **do not exist locally yet**.
- Rights (Impressum probe 04-10-2026): MLU **texts** are usable with
  attribution; **images are not, except by request**. The driver enforces this
  fail-closed (below).

## Rights gate (fail-closed)

`--engine ocr_vlm` refuses (exit 4) unless `--rights-record <file>` exists and
carries the marker line `NWS_RIGHTS_CLEARED: images`. That marker may only be
written into a record after the H5940 letter is answered. The default
`sidecar` engine needs no record because it reads text twins and invents no
pixels — it exists to prove the plumbing and to dry-run QC on any staged set.

## Run

```sh
# offline plumbing / dry-run (sidecar twins beside the images):
python3 scripts/ocr_halle_route.py --scans-dir data/nws_ocr/scans/ --out-dir data/nws_ocr/out/

# production, once Halle's material + written permission exist:
python3 scripts/ocr_halle_route.py --scans-dir data/nws_ocr/scans/ --out-dir data/nws_ocr/out/ \
    --engine ocr_vlm --rights-record data/nws_ocr/RIGHTS_H5941.md
```

Exit codes: `0` all QC-PASS · `3` QC failures present · `4` rights refusal.

## Engines

- **sidecar** (default, offline): reads a `.txt`/`.md` twin next to each page
  image. Deterministic, keyless — used for canary/CI and pre-staging QC.
- **ocr_vlm** (production): one call per page into
  [`Uprava/tools/ocr_vlm/vlm_ocr.py`](https://github.com/gasyoun/Uprava/blob/main/tools/ocr_vlm/vlm_ocr.py)
  (qwen3-vl-plus via DashScope — IAST-diacritic + italic winner of the
  24-09-2026 bench). Needs `DASHSCOPE_API_KEY` in env and the rights record.

## Per-page QC

Each page gets a verdict with reasons in `qc_report.json` + human-readable
`QC_REPORT.md`:

- `near_empty` → status `EMPTY` (fewer than 10 chars);
- `prompt_echo` → status `FAIL` (the model transcribed the prompt — ocr_vlm
  grab #4);
- `no_iast_diacritics` → status `FAIL` (200+ letters, zero IAST diacritics —
  NWS lemmas are Latin-script Sanskrit, a flat page is a transcription
  suspect);
- `engine_error_rc<N>` → status `FAIL` (production engine call failed).

## Export shape (receiver contract)

`--out-dir` receives: one `<page_id>.md` per page, `nws_route_manifest.jsonl`
(`page_id`, `source_image`, `engine`, `sha256_text`, `qc_*`), `qc_report.json`,
`QC_REPORT.md`. This landing shape is the input the **H6064 NWS ingest
pipeline** consumes; when that pipeline lands, re-verify the shape against its
actual loader (contract caveat — this route defines the sender side only).

Bulk output lands under `data/nws_ocr/` and stays **untracked** (derived text
of a private-layer source; the NWS layer stays private until the accession
decision H5939).
