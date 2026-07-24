"""P-D5 — ingest selected public join-table assets into kosha.db as additive layers.

Implements DATA_HUB_ROADMAP.md phase P-D5 / next-programme Wave 4:
manifest public join assets become queryable SQL tables an agent can LEFT JOIN
against lemmas/entries. Pattern mirrors the frequency LEFT JOIN already done
for lemmas (build_db.build_lemmas) — additive, never mutates core lexical
tables (entries / forms / lemmas / senses).

Selected layers (rights confirmed public in datasets.json; local paths present):

  * sense_frequency       data/frequency/sense_frequency.tsv
  * roots_frequency       data/roots/roots_frequency.tsv
  * dict_corpus_coverage  data/concordance/dict_corpus_coverage.tsv  (summary)
  * mw_roots              sibling csl-orig v02/mw/mw_roots.tsv      (optional)
  * mw_etymology          sibling csl-orig v02/mw/mw_etymology.tsv  (optional)

R-N7 / D5-4 discipline: prefer **summary** tables (dict_corpus_coverage, not
the full 74k-row dict_corpus_concordance locus dump; no VisualDCS bulk copy).
Large raw assets stay as release files / sibling feeds.

Restricted-tier rows are NEVER loaded here. Public API routes are unchanged —
these tables are for agent/SQL query only until an explicit rights-cleared
endpoint is designed.

Usage:
    python scripts/build_db.py --stage layers
    python scripts/build_db_layers.py              # same, standalone
    python scripts/build_db_layers.py --db PATH

Idempotent: each table is DROP + recreate on every run.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "db" / "kosha.db"

SENSE_FREQ_TSV = ROOT / "data" / "frequency" / "sense_frequency.tsv"
ROOTS_FREQ_TSV = ROOT / "data" / "roots" / "roots_frequency.tsv"
DICT_COVERAGE_TSV = ROOT / "data" / "concordance" / "dict_corpus_coverage.tsv"

# Smoke lemmas used by tests and the operator note (IAST → SLP1).
SMOKE_LEMMAS_SLP1 = ("Darma", "nAga", "kf")  # dharma, nāga, kṛ


def _find_github_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "SanskritLexicography").is_dir() or (candidate / "csl-orig").is_dir():
            return candidate
    return start.parent


SIBLING = _find_github_root(ROOT)
MW_ROOTS_TSV = SIBLING / "csl-orig" / "v02" / "mw" / "mw_roots.tsv"
MW_ETYMOLOGY_TSV = SIBLING / "csl-orig" / "v02" / "mw" / "mw_etymology.tsv"

LAYER_META_KEY = "pd5_layers"
LAYER_VERSION = "1.0.0"  # bump when table schema set changes


def _int_or_none(v: str | None):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def _float_or_none(v: str | None):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def ensure_layer_schema(con: sqlite3.Connection) -> None:
    """Drop + recreate layer tables so schema bumps apply cleanly.

    Core lexical tables (entries/forms/lemmas/senses/…) are never touched.
    """
    con.executescript(
        """
        DROP TABLE IF EXISTS sense_frequency;
        DROP TABLE IF EXISTS roots_frequency;
        DROP TABLE IF EXISTS dict_corpus_coverage;
        DROP TABLE IF EXISTS mw_roots;
        DROP TABLE IF EXISTS mw_etymology;

        CREATE TABLE sense_frequency (
            lemma_slp1 TEXT NOT NULL,
            layer TEXT NOT NULL,
            sense_id TEXT NOT NULL,
            sense_gloss TEXT,
            count_all INTEGER,
            sense_rank INTEGER,
            lemma_share REAL,
            n_texts INTEGER,
            dispersion_dp REAL,
            largest_text_share REAL,
            count_adj REAL,
            sense_rank_adj INTEGER,
            count_bal_uniform REAL,
            sense_rank_bal INTEGER,
            count_nonsastra REAL,
            sense_rank_nonsastra INTEGER,
            top_genre TEXT,
            top_genre_share REAL,
            periods TEXT,
            provenance TEXT,
            confidence REAL,
            PRIMARY KEY (lemma_slp1, layer, sense_id)
        );
        CREATE INDEX sense_frequency_lemma ON sense_frequency(lemma_slp1);
        CREATE INDEX sense_frequency_layer ON sense_frequency(layer, lemma_slp1);

        CREATE TABLE roots_frequency (
            rank INTEGER PRIMARY KEY,
            root_iast TEXT NOT NULL,
            dcs_lemma TEXT NOT NULL,
            grammar_class TEXT,
            dcs_status TEXT,
            attested_count INTEGER NOT NULL,
            coverage_pct REAL NOT NULL,
            top_attested_forms TEXT
        );
        CREATE INDEX roots_frequency_lemma ON roots_frequency(dcs_lemma);

        CREATE TABLE dict_corpus_coverage (
            slp1 TEXT PRIMARY KEY,
            n_dicts INTEGER,
            status TEXT NOT NULL,
            best_tier TEXT,
            evidence_count INTEGER
        );
        CREATE INDEX dict_corpus_coverage_status ON dict_corpus_coverage(status);

        CREATE TABLE mw_roots (
            mw_L TEXT NOT NULL,
            e TEXT,
            k1_slp1 TEXT NOT NULL,
            root_iast TEXT,
            verb_type TEXT,
            classes TEXT,
            whitney_anchor TEXT,
            westergaard TEXT,
            PRIMARY KEY (mw_L, e)
        );
        CREATE INDEX mw_roots_k1 ON mw_roots(k1_slp1);

        -- L_id is not unique in mw_etymology.tsv (one MW L can yield multiple
        -- derivation rows when the printed entry carries several roots).
        CREATE TABLE mw_etymology (
            id INTEGER PRIMARY KEY,
            L_id TEXT NOT NULL,
            headword TEXT,
            headword_slp1 TEXT NOT NULL,
            root TEXT,
            root_slp1 TEXT,
            root_via TEXT,
            root_class TEXT,
            root_canonical TEXT,
            prefixes TEXT,
            affix TEXT,
            affix_slp1 TEXT,
            "group" TEXT
        );
        CREATE INDEX mw_etymology_L ON mw_etymology(L_id);
        CREATE INDEX mw_etymology_head ON mw_etymology(headword_slp1);
        CREATE INDEX mw_etymology_root ON mw_etymology(root_slp1);
        """
    )
    con.commit()


def load_sense_frequency(con: sqlite3.Connection, path: Path = SENSE_FREQ_TSV) -> int:
    if not path.exists():
        raise SystemExit(f"[layers] missing required feed: {path}")
    con.execute("DELETE FROM sense_frequency")
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.append(
                (
                    r["lemma_slp1"],
                    r["layer"],
                    r["sense_id"],
                    r.get("sense_gloss") or None,
                    _int_or_none(r.get("count_all")),
                    _int_or_none(r.get("sense_rank")),
                    _float_or_none(r.get("lemma_share")),
                    _int_or_none(r.get("n_texts")),
                    _float_or_none(r.get("dispersion_dp")),
                    _float_or_none(r.get("largest_text_share")),
                    _float_or_none(r.get("count_adj")),
                    _int_or_none(r.get("sense_rank_adj")),
                    _float_or_none(r.get("count_bal_uniform")),
                    _int_or_none(r.get("sense_rank_bal")),
                    _float_or_none(r.get("count_nonsastra")),
                    _int_or_none(r.get("sense_rank_nonsastra")),
                    r.get("top_genre") or None,
                    _float_or_none(r.get("top_genre_share")),
                    r.get("periods") or None,
                    r.get("provenance") or None,
                    _float_or_none(r.get("confidence")),
                )
            )
    con.executemany(
        "INSERT INTO sense_frequency ("
        "lemma_slp1, layer, sense_id, sense_gloss, count_all, sense_rank, "
        "lemma_share, n_texts, dispersion_dp, largest_text_share, count_adj, "
        "sense_rank_adj, count_bal_uniform, sense_rank_bal, count_nonsastra, "
        "sense_rank_nonsastra, top_genre, top_genre_share, periods, "
        "provenance, confidence"
        ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM sense_frequency").fetchone()[0]
    print(f"[layers] sense_frequency: {n} rows from {path.name}")
    return n


def load_roots_frequency(con: sqlite3.Connection, path: Path = ROOTS_FREQ_TSV) -> int:
    if not path.exists():
        raise SystemExit(f"[layers] missing required feed: {path}")
    con.execute("DELETE FROM roots_frequency")
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.append(
                (
                    int(r["rank"]),
                    r["root_iast"],
                    r["dcs_lemma"],
                    r.get("grammar_class") or None,
                    r.get("dcs_status") or None,
                    int(r["attested_count"]),
                    float(r["coverage_pct"]),
                    r.get("top_attested_forms") or None,
                )
            )
    con.executemany(
        "INSERT INTO roots_frequency ("
        "rank, root_iast, dcs_lemma, grammar_class, dcs_status, "
        "attested_count, coverage_pct, top_attested_forms"
        ") VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM roots_frequency").fetchone()[0]
    print(f"[layers] roots_frequency: {n} rows from {path.name}")
    return n


def load_dict_corpus_coverage(
    con: sqlite3.Connection, path: Path = DICT_COVERAGE_TSV
) -> int:
    """Summary coverage sidecar — one row per union headword (R-N7)."""
    if not path.exists():
        raise SystemExit(f"[layers] missing required feed: {path}")
    con.execute("DELETE FROM dict_corpus_coverage")
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.append(
                (
                    r["slp1"],
                    _int_or_none(r.get("n_dicts")),
                    r["status"],
                    r.get("best_tier") or None,
                    _int_or_none(r.get("evidence_count")),
                )
            )
    con.executemany(
        "INSERT INTO dict_corpus_coverage "
        "(slp1, n_dicts, status, best_tier, evidence_count) "
        "VALUES (?,?,?,?,?)",
        rows,
    )
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM dict_corpus_coverage").fetchone()[0]
    attested = con.execute(
        "SELECT COUNT(*) FROM dict_corpus_coverage WHERE status='attested'"
    ).fetchone()[0]
    print(
        f"[layers] dict_corpus_coverage: {n} rows "
        f"({attested} attested) from {path.name}"
    )
    return n


def load_mw_roots(con: sqlite3.Connection, path: Path = MW_ROOTS_TSV) -> int | None:
    if not path.exists():
        print(f"[layers] mw_roots: SKIP (sibling feed missing: {path})")
        return None
    con.execute("DELETE FROM mw_roots")
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.append(
                (
                    r["mw_L"],
                    r.get("e") or "",
                    r["k1_slp1"],
                    r.get("root_iast") or None,
                    r.get("verb_type") or None,
                    r.get("classes") or None,
                    r.get("whitney_anchor") or None,
                    r.get("westergaard") or None,
                )
            )
    con.executemany(
        "INSERT INTO mw_roots "
        "(mw_L, e, k1_slp1, root_iast, verb_type, classes, whitney_anchor, westergaard) "
        "VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM mw_roots").fetchone()[0]
    print(f"[layers] mw_roots: {n} rows from {path}")
    return n


def load_mw_etymology(
    con: sqlite3.Connection, path: Path = MW_ETYMOLOGY_TSV
) -> int | None:
    if not path.exists():
        print(f"[layers] mw_etymology: SKIP (sibling feed missing: {path})")
        return None
    con.execute("DELETE FROM mw_etymology")
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.append(
                (
                    r["L_id"],
                    r.get("headword") or None,
                    r["headword_slp1"],
                    r.get("root") or None,
                    r.get("root_slp1") or None,
                    r.get("root_via") or None,
                    r.get("root_class") or None,
                    r.get("root_canonical") or None,
                    r.get("prefixes") or None,
                    r.get("affix") or None,
                    r.get("affix_slp1") or None,
                    r.get("group") or None,
                )
            )
    con.executemany(
        'INSERT INTO mw_etymology '
        "(L_id, headword, headword_slp1, root, root_slp1, root_via, "
        'root_class, root_canonical, prefixes, affix, affix_slp1, "group") '
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM mw_etymology").fetchone()[0]
    print(f"[layers] mw_etymology: {n} rows from {path}")
    return n


def smoke_join_report(con: sqlite3.Connection) -> dict:
    """LEFT JOIN smoke lemmas across layers — returns per-lemma facts."""
    out = {}
    has_lemmas = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='lemmas'"
    ).fetchone()
    for slp1 in SMOKE_LEMMAS_SLP1:
        row = {
            "lemma_slp1": slp1,
            "in_lemmas": None,
            "sense_freq_rows": 0,
            "dict_coverage": None,
            "roots_hit": 0,
            "etym_rows": 0,
        }
        if has_lemmas:
            lem = con.execute(
                "SELECT slp1, count_all, rank_all FROM lemmas WHERE slp1=?",
                (slp1,),
            ).fetchone()
            row["in_lemmas"] = dict(lem) if lem else None
        row["sense_freq_rows"] = con.execute(
            "SELECT COUNT(*) FROM sense_frequency WHERE lemma_slp1=?",
            (slp1,),
        ).fetchone()[0]
        cov = con.execute(
            "SELECT status, best_tier, evidence_count FROM dict_corpus_coverage "
            "WHERE slp1=?",
            (slp1,),
        ).fetchone()
        if cov:
            row["dict_coverage"] = {
                "status": cov[0],
                "best_tier": cov[1],
                "evidence_count": cov[2],
            }
        # roots: kṛ is dcs_lemma 'kṛ' in roots_frequency (IAST); map loosely
        # by checking dcs_lemma against common SLP1↔IAST for smoke set.
        iast_map = {"Darma": "dharma", "nAga": "nāga", "kf": "kṛ"}
        iast = iast_map.get(slp1, slp1)
        row["roots_hit"] = con.execute(
            "SELECT COUNT(*) FROM roots_frequency WHERE dcs_lemma=? OR dcs_lemma LIKE ?",
            (iast, iast + "%"),
        ).fetchone()[0]
        row["etym_rows"] = con.execute(
            "SELECT COUNT(*) FROM mw_etymology WHERE headword_slp1=?",
            (slp1,),
        ).fetchone()[0]
        out[slp1] = row
    return out


def build_layers(con: sqlite3.Connection) -> dict:
    """Load all P-D5 public layers. Returns a summary dict for tests/meta."""
    ensure_layer_schema(con)
    summary = {
        "version": LAYER_VERSION,
        "sense_frequency": load_sense_frequency(con),
        "roots_frequency": load_roots_frequency(con),
        "dict_corpus_coverage": load_dict_corpus_coverage(con),
        "mw_roots": load_mw_roots(con),
        "mw_etymology": load_mw_etymology(con),
    }
    con.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (LAYER_META_KEY, json.dumps(summary, ensure_ascii=False)),
    )
    con.commit()
    smoke = smoke_join_report(con)
    print("[layers] smoke joins:")
    for k, v in smoke.items():
        print(f"  {k}: {v}")
    summary["smoke"] = smoke
    return summary


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    # meta table may be missing on a layers-only fresh DB
    con.execute(
        "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
    )
    con.commit()
    return con


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help=f"path to kosha.db (default {DB_PATH})",
    )
    args = ap.parse_args(argv)
    con = connect(args.db)
    try:
        build_layers(con)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
