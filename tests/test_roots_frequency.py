"""H950 (W2b) — roots frequency + attestation layer.

Data-only invariants: monotone coverage, every root traceable to WhitneyRoots's
canonical triangulation, no fabricated attested forms, TSV/JSON agreement.
"""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TSV = REPO / "data" / "roots" / "roots_frequency.tsv"
JSON_PATH = REPO / "data" / "roots" / "roots_frequency.json"
GH = REPO.parent if (REPO.parent / "WhitneyRoots").exists() else REPO.parent.parent
SOURCE = GH / "WhitneyRoots" / "src" / "dcs_freq.json"


def _read_tsv_rows():
    with open(TSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _read_json():
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def test_files_exist():
    assert TSV.exists(), TSV
    assert JSON_PATH.exists(), JSON_PATH


def test_coverage_monotone_nondecreasing():
    rows = _read_tsv_rows()
    prev = -1.0
    for r in rows:
        pct = float(r["coverage_pct"])
        assert pct >= prev, f"coverage_pct decreased at rank {r['rank']}: {prev} -> {pct}"
        prev = pct
    assert prev == 100.0, f"final coverage_pct should reach 100.0, got {prev}"


def test_coverage_strictly_increases_with_positive_count():
    rows = _read_tsv_rows()
    prev = -1.0
    for r in rows:
        pct = float(r["coverage_pct"])
        assert int(r["attested_count"]) > 0
        assert pct > prev, f"rank {r['rank']} added zero coverage despite positive count"
        prev = pct


def test_ranks_are_dense_sequential():
    rows = _read_tsv_rows()
    ranks = [int(r["rank"]) for r in rows]
    assert ranks == list(range(1, len(rows) + 1))


def test_every_root_traces_to_whitneyroots_source():
    if not SOURCE.exists():
        import pytest
        pytest.skip("WhitneyRoots checkout not present in this environment")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    known_roots = {v["root"] for v in source["entries"].values()}
    rows = _read_tsv_rows()
    for r in rows:
        for root in r["root_iast"].split(" / "):
            assert root in known_roots, f"root {root!r} not in WhitneyRoots's own hub"


def test_no_duplicate_corpus_mass_from_homonym_sharing():
    """A dcs_lemma shared by several Whitney roots (homonym_shared) must be
    counted once toward coverage, not once per homonym -- H950's own bug
    caught before commit: three `kṛ` homonyms each report the identical
    corpus total, and naively summing them would triple-count the mass."""
    rows = _read_tsv_rows()
    lemmas = [r["dcs_lemma"] for r in rows]
    assert len(lemmas) == len(set(lemmas)), "a dcs_lemma appears in more than one row"


def test_tsv_json_row_count_and_order_agree():
    tsv_rows = _read_tsv_rows()
    data = _read_json()
    assert len(tsv_rows) == len(data["roots"]) == data["metadata"]["n_ranked"]
    for tr, jr in zip(tsv_rows, data["roots"]):
        assert int(tr["rank"]) == jr["rank"]
        assert tr["root_iast"] == jr["root_iast"]
        assert tr["dcs_lemma"] == jr["dcs_lemma"]
        assert int(tr["attested_count"]) == jr["attested_count"]
        assert float(tr["coverage_pct"]) == jr["coverage_pct"]


def test_top_forms_are_verbatim_from_source_not_fabricated():
    if not SOURCE.exists():
        import pytest
        pytest.skip("WhitneyRoots checkout not present in this environment")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    by_lemma_forms = {}
    for v in source["entries"].values():
        if v["dcs_status"] in ("matched", "aliased", "homonym_shared") and v["total"] > 0:
            by_lemma_forms.setdefault(v["dcs_lemma"], v["top_forms"])
    data = _read_json()
    for row in data["roots"]:
        assert row["top_forms"] == by_lemma_forms[row["dcs_lemma"]], (
            f"top_forms for {row['dcs_lemma']!r} diverge from WhitneyRoots's source"
        )
