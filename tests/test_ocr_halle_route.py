"""Offline tests for the NWS-Halle remainder OCR route (H6067, epic E025).

No network, no API keys: the sidecar engine and the fail-closed rights gate
are exercised on tmp fixtures; the production ocr_vlm adapter is only checked
to refuse cleanly without a rights record.
"""

import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ocr_halle_route as route  # noqa: E402

# 1x1 transparent PNG — the route never reads pixels itself.
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)

GOOD_PAGE = "artha " + "kāma dharma mokṣa " * 12  # >200 letters, IAST diacritics
EMPTY_PAGE = "   \n"
ECHO_PAGE = "PRE-REFORM ORTHOGRAPHY transcribed"


@pytest.fixture()
def scans(tmp_path: Path) -> Path:
    d = tmp_path / "scans"
    d.mkdir()
    for name, text in (
        ("page_0001.png", GOOD_PAGE),
        ("page_0002.png", EMPTY_PAGE),
        ("page_0003.png", ECHO_PAGE),
    ):
        (d / name).write_bytes(PNG_1PX)
        (d / name).with_suffix(".txt").write_text(text, encoding="utf-8")
    return d


def test_manifest_build(scans: Path) -> None:
    rows = route.build_manifest(scans)
    assert [r["page_id"] for r in rows] == ["page_0001", "page_0002", "page_0003"]
    assert all(r["sidecar"] for r in rows)


def test_manifest_empty_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        route.build_manifest(tmp_path / "missing")


def test_qc_verdicts() -> None:
    good = route.qc_page(GOOD_PAGE)
    assert good["status"] == "PASS" and good["iast_ratio"] > 0
    assert route.qc_page(EMPTY_PAGE)["status"] == "EMPTY"
    echo = route.qc_page(ECHO_PAGE)
    assert echo["status"] == "FAIL" and "prompt_echo" in echo["reasons"]
    flat = route.qc_page("plain ascii without diacritics " * 30)
    assert flat["status"] == "FAIL" and "no_iast_diacritics" in flat["reasons"]


def test_sidecar_run_and_reports(scans: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    rows = route.run_sidecar(route.build_manifest(scans))
    route.write_reports(rows, out)
    assert {r["qc"]["status"] for r in rows} == {"PASS", "EMPTY", "FAIL"}
    assert (out / "page_0001.md").read_text(encoding="utf-8") == GOOD_PAGE
    manifest = [json.loads(l) for l in (out / "nws_route_manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(manifest) == 3
    assert all(len(m["sha256_text"]) == 64 for m in manifest)
    assert all(m["engine"] == "sidecar" for m in manifest)
    report = json.loads((out / "qc_report.json").read_text(encoding="utf-8"))
    assert len(report["pages"]) == 3


def test_cli_sidecar_qc_exit_codes(scans: Path, tmp_path: Path) -> None:
    """Fixture has one FAIL (prompt echo) -> designed QC exit code 3, report written."""
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ocr_halle_route.py"),
         "--scans-dir", str(scans), "--out-dir", str(out)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 3, proc.stderr
    assert (out / "QC_REPORT.md").exists()
    # clean set (good page only) -> exit 0
    clean = tmp_path / "clean_scans"
    clean.mkdir()
    (clean / "p.png").write_bytes(PNG_1PX)
    (clean / "p.txt").write_text(GOOD_PAGE, encoding="utf-8")
    ok = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ocr_halle_route.py"),
         "--scans-dir", str(clean), "--out-dir", str(tmp_path / "clean_out")],
        capture_output=True, text=True,
    )
    assert ok.returncode == 0, ok.stderr


def test_rights_gate_refusal_without_record(scans: Path, tmp_path: Path) -> None:
    """No rights record -> ocr_vlm run must refuse with exit 4, write nothing."""
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ocr_halle_route.py"),
         "--scans-dir", str(scans), "--out-dir", str(out), "--engine", "ocr_vlm"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 4
    assert "RIGHTS GATE REFUSAL" in proc.stderr
    assert not out.exists()


def test_rights_gate_accepts_marked_record(scans: Path, tmp_path: Path) -> None:
    ok, why = route.check_rights(None)
    assert not ok
    missing = tmp_path / "nope.md"
    ok, why = route.check_rights(missing)
    assert not ok and "missing on disk" in why
    record = tmp_path / "h5941_answer.md"
    record.write_text("... " + route.RIGHTS_MARKER + " ...", encoding="utf-8")
    ok, why = route.check_rights(record)
    assert ok and why == "ok"
    unmarked = tmp_path / "unmarked.md"
    unmarked.write_text("answer without the marker", encoding="utf-8")
    ok, why = route.check_rights(unmarked)
    assert not ok and "marker" in why
