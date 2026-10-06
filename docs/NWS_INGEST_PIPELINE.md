# NWS intake pipeline — siglum-parse + fuzzy works-match + dump readiness (H6064 · epic E025)

_Created: 06-10-2026 · Last updated: 06-10-2026_

_Driver: [`scripts/nws_ingest_pipeline.py`](https://github.com/gasyoun/kosha/blob/main/scripts/nws_ingest_pipeline.py) · tests: [`tests/test_nws_ingest_pipeline.py`](https://github.com/gasyoun/kosha/blob/main/tests/test_nws_ingest_pipeline.py) (17/17 offline green) · registry: [`data/nws/nws_works_registry.json`](https://github.com/gasyoun/kosha/blob/main/data/nws/nws_works_registry.json)_

The intake conveyor for the Nachtragswörterbuch (Halle) layer per decisions
H5937–41 ([grill](https://github.com/gasyoun/Uprava/blob/main/papers/A61_wsc/NWS_DETAIL_GRILL_DECISIONS_2026-10-04.md)):
siglum-parse of the `nws` prose field, fuzzy match against the **174
Erfasste Werke**, key1-based lemma matching (H6050 contract), and readiness
for the post-H5940-letter dump. Rights: MLU Halle-Wittenberg, texts with
attribution (Impressum probe 04-10); the lemma tar stays PRIVATE (H5939).

## Works registry (174)

`data/nws/nws_works_registry.json` — the Erfasste Werke list scraped from
`nws.uzi.uni-halle.de/dictionaries` (fetched 06-10-2026, html sha256
`86c9495e…`, attribution MLU). Each row: siglum · citation · Textgattung ·
Sachkategorie. Rebuild: `--build-registry <fetched.html>` (refuses ≠174).

## Full-tar run (pinned 06-10-2026, tar sha256 `054b05da…`)

| Measure | Value |
|---|---:|
| lemma JSONs (H5937 service filter: 7 service files out) | **167,990** |
| entries with `nws` prose (all `has_nws_extra`) | **34,101** |
| key1 present / stem-decode agreement (`_x`→uppercase, H6050) | 167,990 / 167,990 |
| page-precise refs (`S. n, Z. n`) | **8,440** |
| literature refs (`Author Year : page`) | **8,937** |
| dict-marker entries (`MW : 145`) | **4,941** |
| works of the 174 attested ≥1 citation | **82** |
| unparsed comma-structured segments | **0 (0.000%)** |

Counting note: H6050's "167,991 stems" includes the `_watch_state.json`
scrape-state file, which the H5937 service filter drops here → 167,990 true
lemma JSONs, every one carrying `key1` (the 24 key-less stems of H6050 were
service/junk files, not lemmas — `_watch_state` among them).

Top attested works: Geldner 1907 ×1,571 · Abhyankar 1986 ×753 · Ensink 1964
×527 · Kangle 1969 ×295 · Hoernle 1908 ×239 · Kanta 1953 ×208 ·
Hillebrandt 1885 ×174 · Karashima 2012 ×181. The other 92 works show zero
citations in this scrape — rows exist in the report regardless (compliance
= all 174 processed, not only hits).

Unregistered-sigla census (841 kinds — corpus-text sigla and MW-internal
markers, never dropped): Lex(MW) ×5,873 · Mbh ×2,655 · Kāvya(MW) ×2,014 ·
W(MW) ×1,718 · Renou ×1,433 · ṚV ×745 · Meyer ×678 · R ×601 · PPS ×589 ·
Buddh(MW) ×574 · Suś ×565 · Kathās ×555 … The `X(MW)` family is the NWS
internal MW-source citation (feeds the T(MW) share question of H5937);
Mbh/R/ṚV/Suś… are the corpus attestations. `/books` is a JS modal on the
site — no static sigla bibliography exists, so corpus sigla stay in the
census rather than the 174-works join.

## Dump readiness (post-H5940 letter)

`--from-ocr-route DIR` consumes the H6067 OCR-route export shape
(`nws_route_manifest.jsonl` + `<page_id>.md`): manifest fields enforced
(page_id, source_image, engine, sha256_text), text sha256 verified per
page, QC statuses counted, sigla census parsed from page prose. A fresh
Halle dump tar (same per-lemma JSON shape) goes through `--full-tar
--nws-tar <path>`; `--selftest` pins the sha256 of the measured artifact
and fails on drift. Lemma joins use `key1` only — the 24-orphan rule
(H6050 consequence 4) keeps junk stems out of any lemma inventory.

## Reproduction

```sh
python3 scripts/nws_ingest_pipeline.py --selftest          # SELFTEST PASS (all pins)
python3 -m pytest tests/test_nws_ingest_pipeline.py        # 17 passed (offline)
python3 scripts/nws_ingest_pipeline.py --full-tar --report out/   # 174-row compliance report
```

The private tar is not committed; the report regenerates locally
(pwg-ru-data/layers/nws.tar.gz, kosha row `nws-halle-lemmas`).
