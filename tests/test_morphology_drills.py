"""W1a morphology-drills tests (H946).

Locks the acceptance bar from docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md
SS W1a: every drill item is answer-keyed AND evidence-backed, no fabricated
(unattested) forms survive into the default-mode item bank, the coverage
metric is present and monotone, and the class-bucket lesson ordering never
regresses.

Local-only-ish: requires data/morphology/morphology_curriculum.tsv +
data/morphology/drills.json to already be built
(scripts/build_morphology_drills.py) — both are committed release assets,
so this is a pure output-file check, no DB / no DCS dependency.
"""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_morphology_curriculum as bmc  # noqa: E402

TSV = ROOT / "data" / "morphology" / "morphology_curriculum.tsv"
DRILLS = ROOT / "data" / "morphology" / "drills.json"
APKG = ROOT / "data" / "morphology" / "morphology_drills.apkg"
WEIGHTS = ROOT / "data" / "morphology" / "drill_weights.json"

pytestmark = pytest.mark.skipif(not TSV.exists(), reason="morphology_curriculum.tsv not built")


def _rows():
    return list(csv.DictReader(open(TSV, encoding="utf-8"), delimiter="\t"))


def _drills():
    return json.loads(DRILLS.read_text(encoding="utf-8"))


def test_nonempty():
    rows = _rows()
    assert len(rows) > 1000


def test_cumulative_coverage_is_monotone():
    rows = _rows()
    prev = -1.0
    for r in rows:
        cur = float(r["cumulative_pct"])
        assert cur >= prev, "cumulative_pct decreased at rank %s" % r["rank"]
        prev = cur


def test_coverage_headline_reachable():
    rows = _rows()
    for target in (50, 80, 90):
        assert any(float(r["cumulative_pct"]) >= target for r in rows), \
            "curriculum never reaches %d%% cumulative coverage" % target


def test_ranks_are_sequential():
    rows = _rows()
    for i, r in enumerate(rows, 1):
        assert int(r["rank"]) == i


def test_lesson_bucket_order_never_regresses():
    weights = json.loads(WEIGHTS.read_text(encoding="utf-8"))
    order = weights["lesson_group_order"]
    rows = _rows()
    seen_idx = -1
    for r in rows:
        idx = order.index(r["bucket"])
        assert idx >= seen_idx, (
            "bucket %r (rank %s) appears after a later bucket -- lesson "
            "ordering regressed" % (r["bucket"], r["rank"]))
        seen_idx = max(seen_idx, idx)


def test_bucket_for_model_known_classes():
    pronouns = {"tad", "asmad"}
    assert bmc.bucket_for_model("m_a", "loka", pronouns) == "a-stems"
    assert bmc.bucket_for_model("f_A", "senA", pronouns) == "a-stems"
    assert bmc.bucket_for_model("m_i", "kavi", pronouns) == "other-vowel-stems"
    assert bmc.bucket_for_model("m_in", "hastin", pronouns) == "consonant-stems"
    assert bmc.bucket_for_model("v_1", "BU", pronouns) == "present-class-verbs"
    assert bmc.bucket_for_model("sarva", "tad", pronouns) == "pronouns"


def test_drills_every_item_is_answer_keyed_and_evidence_backed():
    data = _drills()
    assert len(data["items"]) > 0
    for it in data["items"]:
        assert it["answer"], "item %s has no answer" % it["id"]
        assert it["evidence"], "item %s has no evidence -- unverified item leaked into drills.json" % it["id"]
        assert it["evidence"].startswith("dcs:"), "item %s evidence is not a corpus locus" % it["id"]
        assert it["corpus_count"] > 0, "item %s claims evidence with zero corpus_count" % it["id"]
        assert it["aspect"] == "morphology"
        assert it["type"] in ("fill", "match")
        assert it["source_dataset"] == "morphology-drills"


def test_drills_choices_include_the_answer():
    data = _drills()
    for it in data["items"]:
        assert it["answer"] in it["choices"], "item %s answer not among its own choices" % it["id"]


def test_no_duplicate_item_ids():
    data = _drills()
    ids = [it["id"] for it in data["items"]]
    assert len(ids) == len(set(ids))


def test_apkg_written():
    assert APKG.exists()
    assert APKG.stat().st_size > 0


def test_apkg_note_count_matches_fill_items():
    import zipfile
    import sqlite3
    import tempfile
    import os

    data = _drills()
    n_fill = sum(1 for it in data["items"] if it["type"] == "fill")

    with zipfile.ZipFile(APKG) as z:
        payload = z.read("collection.anki2")
    fd, tmp = tempfile.mkstemp(suffix=".anki2")
    os.close(fd)
    try:
        Path(tmp).write_bytes(payload)
        con = sqlite3.connect(tmp)
        n_notes = con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        con.close()
    finally:
        try:
            os.remove(tmp)
        except PermissionError:
            pass
    assert n_notes == n_fill
