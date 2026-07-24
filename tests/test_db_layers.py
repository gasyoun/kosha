"""P-D5 queryable kosha.db layers (H1589 / DATA_HUB_ROADMAP P-D5).

Loads the public join-table sidecars into a throwaway SQLite DB and checks:

  4-1  New tables queryable; smoke lemmas return non-null joins where expected
  4-2  Restricted data is not among the loaded layer set
  4-3  Schema + indexes present; G-SIZE helper thresholds are wired

Does NOT require a full kosha.db build — works in a fresh worktree.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from build_db_layers import (  # noqa: E402
    SMOKE_LEMMAS_SLP1,
    build_layers,
    connect,
    smoke_join_report,
)
from check_g_size import FAIL_BYTES, WARN_BYTES, check_path  # noqa: E402

SENSE_TSV = REPO / "data" / "frequency" / "sense_frequency.tsv"
ROOTS_TSV = REPO / "data" / "roots" / "roots_frequency.tsv"
COVERAGE_TSV = REPO / "data" / "concordance" / "dict_corpus_coverage.tsv"


@pytest.fixture(scope="module")
def layers_db(tmp_path_factory):
    if not (SENSE_TSV.exists() and ROOTS_TSV.exists() and COVERAGE_TSV.exists()):
        pytest.skip("P-D5 source TSVs not present in this checkout")
    db_path = tmp_path_factory.mktemp("pd5") / "layers.db"
    con = connect(db_path)
    summary = build_layers(con)
    yield con, summary
    con.close()


def test_required_feeds_exist():
    assert SENSE_TSV.exists(), SENSE_TSV
    assert ROOTS_TSV.exists(), ROOTS_TSV
    assert COVERAGE_TSV.exists(), COVERAGE_TSV


def test_layer_tables_populated(layers_db):
    con, summary = layers_db
    # H1588 estimated rows raise the TSV above the pure-attested 103k floor.
    assert summary["sense_frequency"] > 100_000
    assert summary["roots_frequency"] > 100
    assert summary["dict_corpus_coverage"] > 100_000
    for table in ("sense_frequency", "roots_frequency", "dict_corpus_coverage"):
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert n > 0, table


def test_smoke_dharma_sense_and_coverage(layers_db):
    """dharma / Darma — high-frequency lemma with sense + coverage signal."""
    con, _ = layers_db
    # sense_frequency keys are SLP1 (Darma)
    n_sense = con.execute(
        "SELECT COUNT(*) FROM sense_frequency WHERE lemma_slp1='Darma'"
    ).fetchone()[0]
    assert n_sense > 0, "expected sense_frequency rows for Darma (dharma)"
    cov = con.execute(
        "SELECT status, evidence_count FROM dict_corpus_coverage WHERE slp1='Darma'"
    ).fetchone()
    assert cov is not None
    assert cov[0] == "attested"
    assert cov[1] is not None and cov[1] > 0


def test_smoke_naga_coverage(layers_db):
    con, _ = layers_db
    cov = con.execute(
        "SELECT status, evidence_count FROM dict_corpus_coverage WHERE slp1='nAga'"
    ).fetchone()
    assert cov is not None
    assert cov[0] == "attested"
    n_sense = con.execute(
        "SELECT COUNT(*) FROM sense_frequency WHERE lemma_slp1='nAga'"
    ).fetchone()[0]
    assert n_sense > 0, "expected sense_frequency rows for nAga"


def test_smoke_kr_roots_frequency(layers_db):
    """kṛ is rank-1 in roots_frequency (IAST dcs_lemma)."""
    con, _ = layers_db
    row = con.execute(
        "SELECT rank, attested_count FROM roots_frequency WHERE dcs_lemma='kṛ'"
    ).fetchone()
    assert row is not None, "kṛ must appear in roots_frequency"
    assert row[0] == 1
    assert row[1] > 10_000


def test_smoke_join_report_keys(layers_db):
    con, _ = layers_db
    report = smoke_join_report(con)
    assert set(report.keys()) == set(SMOKE_LEMMAS_SLP1)
    # dharma coverage + sense
    assert report["Darma"]["dict_coverage"] is not None
    assert report["Darma"]["sense_freq_rows"] > 0
    # kṛ roots
    assert report["kf"]["roots_hit"] >= 1


def test_restricted_tables_not_created(layers_db):
    """4-2 — restricted-tier assets must not land as public layers."""
    con, _ = layers_db
    names = {
        r[0]
        for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    forbidden = {
        "corpus_lexicon",
        "sa_ru_glossary",
        "heritage_mirror",
        "samudra_corpus",
        "dcs_full",
        "archive_stopword",
    }
    assert names.isdisjoint(forbidden)


def test_indexes_exist(layers_db):
    con, _ = layers_db
    idxs = {
        r[0]
        for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
    }
    for name in (
        "sense_frequency_lemma",
        "roots_frequency_lemma",
        "dict_corpus_coverage_status",
    ):
        assert name in idxs, name


def test_g_size_thresholds_ordered():
    assert WARN_BYTES < FAIL_BYTES
    assert FAIL_BYTES == int(1.8 * 1000**3)
    assert WARN_BYTES == int(1.5 * 1000**3)


def test_g_size_missing_is_skip(tmp_path):
    assert check_path(tmp_path / "nope.db") == "missing"


def test_g_size_small_ok(tmp_path):
    p = tmp_path / "tiny.db"
    p.write_bytes(b"0" * 100)
    assert check_path(p) == "ok"


def test_live_kosha_db_join_if_present():
    """Optional integration: when kosha.db exists, layers JOIN lemmas."""
    candidates = [
        REPO / "data" / "db" / "kosha.db",
        REPO.parent / "kosha" / "data" / "db" / "kosha.db",
    ]
    db = next((p for p in candidates if p.exists()), None)
    if db is None:
        pytest.skip("kosha.db not present (gitignored; build or use main checkout)")
    # Open read-only; if layers not yet loaded in live DB, load into a copy is
    # too heavy — just verify lemmas smoke keys exist for join readiness.
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        tables = {
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert "lemmas" in tables
        for slp1 in ("Darma", "nAga"):
            n = con.execute(
                "SELECT COUNT(*) FROM lemmas WHERE slp1=?", (slp1,)
            ).fetchone()[0]
            assert n == 1, f"expected lemma {slp1} in live kosha.db"
        if "sense_frequency" in tables:
            total = con.execute("SELECT COUNT(*) FROM sense_frequency").fetchone()[0]
            if total == 0:
                pytest.skip("sense_frequency present but empty — run --stage layers")
            n = con.execute(
                "SELECT COUNT(*) FROM sense_frequency WHERE lemma_slp1='Darma'"
            ).fetchone()[0]
            assert n > 0, "expected Darma rows after --stage layers"
    finally:
        con.close()
