#!/usr/bin/env python3
"""NWS-Halle undigitized-remainder OCR route (H6067, epic E025).

Batch driver for the sanscritica-ocr programme over a page-scan set:
manifest -> engine -> per-page QC -> receiver-shaped export.

Engines
  sidecar  (default, offline)  reads a .txt/.md twin sitting next to each
           image - deterministic plumbing proof, no network, no API key.
  ocr_vlm  (production) shells Uprava/tools/ocr_vlm (qwen3-vl-plus via
           DashScope; IAST-diacritic + italic winner of the 24-09-2026 bench).
           Needs DASHSCOPE_API_KEY in env and a rights record.

Rights gate (fail-closed)
  MLU Halle permits the TEXTS with attribution; IMAGES only on request
  (Impressum probe 04-10-2026, papers/A61_wsc/NWS_HALLE_ANALYSIS_2026-10-04.md).
  A real-engine run therefore refuses unless --rights-record points at an
  existing file whose first 64 KiB contain the marker line:
      NWS_RIGHTS_CLEARED: images
  The marker will exist only after H5940's letter is answered; the sidecar
  engine needs no record because it invents no pixels.

Exit codes: 0 all pages QC-PASS - 3 QC failures present - 4 rights refusal - 2 usage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import force_utf8_stdio  # noqa: E402  (house helper, H6067)

force_utf8_stdio()

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf"}
SIDECAR_EXTS = (".txt", ".md")

OCR_VLM_PAGE = Path.home() / "Documents/GitHub/Uprava/tools/ocr_vlm/vlm_ocr.py"
RIGHTS_MARKER = "NWS_RIGHTS_CLEARED: images"

# ocr_vlm grab #4: the model can echo the prompt itself; known phrase fragments.
PROMPT_ECHO_MARKERS = (
    "PRE-REFORM ORTHOGRAPHY",
    "правило №1",
    "сноски",
    "transcribe the page",
)
# NWS lemmas are Latin-script Sanskrit; a long page with zero IAST diacritics
# is a transcription suspect, not a plausible dictionary page.
IAST_CHARS = set("āīūṛṝḷḹṭḍṇśṣḥṃṁḹṅñĀĪŪṚṚṆŚṢṬḌṄÑ")
MIN_PLAUSIBLE_CHARS = 10
IAST_FLOOR_LENGTH = 200


def build_manifest(scans_dir: Path) -> list[dict]:
    """Every image-like page in scans_dir -> {page_id, image, sidecar}."""
    if not scans_dir.is_dir():
        raise SystemExit(f"scans dir not found: {scans_dir}")
    rows = []
    for image in sorted(scans_dir.iterdir()):
        if not image.is_file() or image.suffix.lower() not in IMAGE_EXTS:
            continue
        sidecar = None
        for ext in SIDECAR_EXTS:
            candidate = image.with_suffix(ext)
            if candidate.exists():
                sidecar = candidate
                break
        rows.append({"page_id": image.stem, "image": str(image), "sidecar": str(sidecar) if sidecar else None})
    if not rows:
        raise SystemExit(f"no page images in {scans_dir}")
    return rows


def check_rights(record_path: Path | None) -> tuple[bool, str]:
    """Fail-closed image-rights gate; see module docstring."""
    if record_path is None:
        return False, "no --rights-record given (images need MLU permission: H5940/H5941)"
    if not record_path.is_file():
        return False, f"rights record missing on disk: {record_path}"
    head = record_path.read_bytes()[:65536].decode("utf-8", "replace")
    if RIGHTS_MARKER not in head:
        return False, f"{record_path} does not carry marker {RIGHTS_MARKER!r}"
    return True, "ok"


def qc_page(text: str) -> dict:
    """Per-page QC verdict for a page transcription."""
    reasons: list[str] = []
    char_count = len(text.strip())
    letters = sum(ch.isalpha() for ch in text)
    diacritics = sum(ch in IAST_CHARS for ch in text)
    iast_ratio = round(diacritics / letters, 4) if letters else 0.0
    prompt_echo = any(marker in text for marker in PROMPT_ECHO_MARKERS)
    if prompt_echo:
        reasons.append("prompt_echo")
    if char_count < MIN_PLAUSIBLE_CHARS:
        reasons.append("near_empty")
    elif letters >= IAST_FLOOR_LENGTH and iast_ratio == 0.0:
        reasons.append("no_iast_diacritics")
    status = "PASS" if not reasons else ("EMPTY" if reasons == ["near_empty"] else "FAIL")
    return {
        "char_count": char_count,
        "iast_ratio": iast_ratio,
        "prompt_echo": prompt_echo,
        "status": status,
        "reasons": reasons,
    }


def run_sidecar(rows: list[dict]) -> list[dict]:
    """Offline engine: read the sidecar twin of each page."""
    out = []
    for row in rows:
        text = Path(row["sidecar"]).read_text(encoding="utf-8") if row["sidecar"] else ""
        out.append({**row, "engine": "sidecar", "text": text, "qc": qc_page(text)})
    return out


def run_ocr_vlm(rows: list[dict]) -> list[dict]:
    """Production engine: one Uprava/tools/ocr_vlm call per page."""
    if not OCR_VLM_PAGE.is_file():
        raise SystemExit(f"ocr_vlm lane not found: {OCR_VLM_PAGE}")
    out = []
    for row in rows:
        proc = subprocess.run(
            [sys.executable, str(OCR_VLM_PAGE), row["image"]],
            capture_output=True,
            text=True,
            timeout=300,
        )
        text = proc.stdout if proc.returncode == 0 else ""
        qc = qc_page(text)
        if proc.returncode != 0:
            qc["status"] = "FAIL"
            qc["reasons"] = qc["reasons"] + [f"engine_error_rc{proc.returncode}"]
        out.append({**row, "engine": "ocr_vlm", "text": text, "qc": qc})
    return out


def write_reports(rows: list[dict], out_dir: Path) -> None:
    """Page markdown + QC report + receiver-shaped manifest jsonl."""
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    for row in rows:
        page_md = out_dir / f"{row['page_id']}.md"
        page_md.write_text(row["text"], encoding="utf-8")
        manifest_rows.append(
            {
                "page_id": row["page_id"],
                "source_image": row["image"],
                "engine": row["engine"],
                "sha256_text": hashlib.sha256(row["text"].encode("utf-8")).hexdigest(),
                **{f"qc_{k}": v for k, v in row["qc"].items()},
            }
        )
    with (out_dir / "nws_route_manifest.jsonl").open("w", encoding="utf-8") as fh:
        for entry in manifest_rows:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    (out_dir / "qc_report.json").write_text(
        json.dumps({"pages": manifest_rows}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    passed = sum(1 for r in rows if r["qc"]["status"] == "PASS")
    failed = sum(1 for r in rows if r["qc"]["status"] == "FAIL")
    empty = sum(1 for r in rows if r["qc"]["status"] == "EMPTY")
    lines = [
        "# NWS-Halle OCR route — QC report",
        "",
        f"- pages: {len(rows)} · PASS {passed} · FAIL {failed} · EMPTY {empty}",
        f"- engine: {rows[0]['engine'] if rows else 'n/a'}",
        "- receiver: data/nws_ocr/ landing shape (final consumer = H6064 NWS ingest pipeline)",
        "",
        "| page | status | reasons | chars | iast_ratio |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {r['page_id']} | {r['qc']['status']} | {','.join(r['qc']['reasons']) or '-'} | {r['qc']['char_count']} | {r['qc']['iast_ratio']} |"
        for r in rows
    ]
    (out_dir / "QC_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="NWS-Halle remainder OCR batch route")
    ap.add_argument("--scans-dir", type=Path, required=True, help="directory of page images")
    ap.add_argument("--out-dir", type=Path, required=True, help="export landing dir")
    ap.add_argument("--engine", choices=("sidecar", "ocr_vlm"), default="sidecar")
    ap.add_argument("--rights-record", type=Path, default=None, help="file carrying the image-rights marker")
    args = ap.parse_args(argv)

    if args.engine == "ocr_vlm":
        ok, why = check_rights(args.rights_record)
        if not ok:
            print(f"RIGHTS GATE REFUSAL: {why}", file=sys.stderr)
            return 4

    rows = build_manifest(args.scans_dir)
    rows = run_ocr_vlm(rows) if args.engine == "ocr_vlm" else run_sidecar(rows)
    write_reports(rows, args.out_dir)

    failed = sum(1 for r in rows if r["qc"]["status"] == "FAIL")
    print(f"route: {len(rows)} pages · FAIL {failed} · out {args.out_dir}")
    return 3 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
