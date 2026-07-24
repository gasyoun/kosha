"""Zaliznyak declension-class drill tests (H1461).

Pure output-file checks (mirrors tests/test_morphology_drills.py) -- requires
data/zaliznyak/zaliznyak_drills.json to already be built
(scripts/build_zaliznyak_drills.py, reads the SanskritLexicography sibling at
build time only). No sibling repo or DB needed at test time.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
JSON = ROOT / "data" / "zaliznyak" / "zaliznyak_drills.json"
APKG = ROOT / "data" / "zaliznyak" / "zaliznyak_drills.apkg"
CLASSES_TSV = ROOT / "data" / "zaliznyak" / "zaliznyak_paradigm_classes.tsv"

pytestmark = pytest.mark.skipif(not JSON.exists(), reason="zaliznyak_drills.json not built")


def _data():
    return json.loads(JSON.read_text(encoding="utf-8"))


def test_nonempty():
    items = _data()["items"]
    assert len(items) >= 1000


def test_every_item_is_answer_keyed():
    for it in _data()["items"]:
        assert it["answer"], "item %s has no answer" % it["id"]


def test_choices_include_the_answer():
    for it in _data()["items"]:
        assert it["answer"] in it["choices"], "item %s answer not among its own choices" % it["id"]


def test_choices_have_no_duplicates():
    for it in _data()["items"]:
        assert len(it["choices"]) == len(set(it["choices"])), "item %s has duplicate choices" % it["id"]


def test_no_duplicate_item_ids():
    ids = [it["id"] for it in _data()["items"]]
    assert len(ids) == len(set(ids))


def test_type_is_known():
    for it in _data()["items"]:
        assert it["type"] in ("classify", "odd-one-out")


def test_apkg_written():
    assert APKG.exists()
    assert APKG.stat().st_size > 0


def test_apkg_note_count_matches_items():
    import os
    import sqlite3
    import tempfile
    import zipfile

    items = _data()["items"]
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
    assert n_notes == len(items)


def test_paradigm_classes_member_counts_positive():
    import csv

    rows = list(csv.DictReader(open(CLASSES_TSV, encoding="utf-8"), delimiter="\t"))
    assert len(rows) > 0
    for r in rows:
        assert int(r["member_count"]) > 0
