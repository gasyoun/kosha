"""kosha — build kosha.db from source feeds.

Phase 1 (PHASE1_PLAN.md D1-D3): vendor the lemma spine, load per-dict
entries, import the forms layer. Run stages independently via --stage,
or all in order with no flag. Idempotent: re-running drops and rebuilds
each stage's tables.

    python scripts/build_db.py --stage lemmas
    python scripts/build_db.py --stage entries --dicts mw,pwg,ap90
    python scripts/build_db.py --stage forms
    python scripts/build_db.py            # all stages, in order
"""
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


def _find_github_root(start: Path) -> Path:
    """Walk up from ROOT to the GitHub/ dir that holds sibling repos.

    ROOT.parent is correct for a normal checkout, but a git worktree
    (kosha/.claude/worktrees/<name>/) nests ROOT two levels deeper, which
    would silently point SIBLING at .claude/worktrees/ instead of GitHub/.
    """
    for candidate in (start, *start.parents):
        if (candidate / "SanskritLexicography").is_dir():
            return candidate
    return start.parent


# SanskritLexicography is a sibling repo (org convention: all repos under
# the same GitHub/ root). Consume, don't rebuild (SHARED_CODE.md).
SIBLING = _find_github_root(ROOT)
UNION_HEADWORDS = SIBLING / "SanskritLexicography" / "HeadwordLists" / "union" / "union_headwords.tsv"
FREQ_TSV = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
HERITAGE_CROSSWALK = SIBLING / "SanskritLexicography" / "HeadwordLists" / "mw_heritage_crosswalk.tsv"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE IF NOT EXISTS sources (
    dict TEXT PRIMARY KEY,
    title TEXT, edition TEXT,
    csl_orig_commit TEXT NOT NULL,
    source_path TEXT,
    pc_format TEXT NOT NULL,
    pc_coverage REAL,
    entry_count INTEGER
);

-- P3 evidence-layer columns (band, first_era, example_*) are added by an
-- ALTER TABLE migration in scripts/build_evidence.py ensure_columns(), not
-- listed here, so a fresh CREATE and a migrated pre-P3 DB converge on the
-- same shape without a second code path.
CREATE TABLE IF NOT EXISTS lemmas (
    slp1 TEXT PRIMARY KEY,
    iast TEXT NOT NULL,
    n_dicts INTEGER, dicts TEXT, gender TEXT,
    count_all INTEGER, grammar_all TEXT, rank_all INTEGER,
    periods TEXT, periods_sum INTEGER, coverage_pct REAL, core_rank INTEGER
);

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    dict TEXT NOT NULL REFERENCES sources(dict),
    L TEXT NOT NULL,
    slp1_key TEXT NOT NULL,
    k2 TEXT,
    pc_raw TEXT,
    vol INTEGER, page INTEGER, col TEXT,
    body TEXT NOT NULL,
    UNIQUE(dict, L)
);
-- Lemma lookups filter (dict, slp1_key) and ORDER BY L. A covering
-- (dict, slp1_key, L) index serves BOTH the equality seek and the ordering, so
-- the planner never falls back to scanning the whole dict via the UNIQUE(dict,L)
-- autoindex (measured D5: that scan cost ~240 ms/lookup; this index: ~0.3 ms —
-- a plain slp1_key-only index was NOT chosen because ORDER BY L made the planner
-- prefer the ordered autoindex-scan). See D5_MEASUREMENTS.md §3.
CREATE INDEX IF NOT EXISTS entries_dict_key ON entries(dict, slp1_key, L);

CREATE TABLE IF NOT EXISTS senses (
    entry_id INTEGER NOT NULL REFERENCES entries(id),
    sense_n INTEGER NOT NULL,
    span_start INTEGER NOT NULL, span_end INTEGER NOT NULL,
    PRIMARY KEY (entry_id, sense_n)
);

-- H111: `source` carries a trust ordering, highest first --
--   dcs      corpus-attested (DCS) -- highest trust
--   vidyut   rule-generated, DCS-miss fallback
--   heritage rule-generated full paradigm (Heritage/INRIA SL_morph.xml) --
--            lowest trust: the declension engine over-generates
--            grammatically-possible but unattested forms (hypergeneration),
--            and H105's hand-adjudication found occasional stem mis-assignment.
--            A heritage-only form/lemma must never be surfaced as authoritative
--            by kosha lookup or a downstream oracle without dcs/vidyut
--            corroboration (join on form_slp1 and check `source`).
-- `category` is NULL for dcs/vidyut; heritage rows carry the coarse Heritage
-- grammatical category (nominal/finite-verb/participle/...) so consumers can
-- filter out the over-generation-prone categories (iic/iiv/iip compounds are
-- the largest hypergeneration source) without re-deriving it from the XML.
CREATE TABLE IF NOT EXISTS forms (
    form_slp1 TEXT NOT NULL,
    lemma_slp1 TEXT NOT NULL,
    source TEXT NOT NULL,
    category TEXT,
    PRIMARY KEY (form_slp1, lemma_slp1, source)
);
CREATE INDEX IF NOT EXISTS forms_lemma ON forms(lemma_slp1);

-- P4 Wave K1 (ROADMAP_INFLECT_2026_2027.md D3: Cologne tables verbatim, not
-- vidyut -- that substitution is Wave E1's job later). Sourced from
-- MWinflect's nominals/pysanskritv2/tables/calc_tables.txt (the same
-- calc_tables.txt csl-inflect's own sqlite/lgtab1+lgtab2 builders consume --
-- see scripts/build_inflections.py for the exact ingest + case/number decode
-- derived from nominals/pydecl/decline.py's fixed 24-slot `sup` order).
-- Only nominal declensions are populated in K1; verb conjugations
-- (vlgtab1/vlgtab2) are blocked upstream in MWinflect's own verbs pipeline
-- `gcase`/`number` are NULL for indeclinables (model='ind').
--
-- P4 Wave K2a (H181): verb conjugations ARE now ingested. The upstream
-- MWinflect Python-2 syntax bug (verbs/pysanskritv2/inputs/clean.py's
-- parenthesized-tuple lambda parameter) was fixed and prepared as an
-- upstream PR, unblocking verbs/redo.sh -> verbs/pysanskritv2/tables/
-- calc_tables.txt (present-system conjugations: pre/ipf/ipv/opt x
-- active/middle/passive). Verb rows carry `person`/`tense`/`voice` (NULL for
-- nominals) and NULL gender/gcase; nominal rows carry gender/gcase/number and
-- NULL person/tense/voice. `model` is the declension paradigm for nominals
-- (m_a, n_a, m_vat, ind) or a "v_<gana>"/"v_p" conjugation-class tag for verbs.
CREATE TABLE IF NOT EXISTS inflections (
    form_slp1 TEXT NOT NULL,
    lemma_slp1 TEXT NOT NULL,
    model TEXT NOT NULL,
    gender TEXT,
    gcase TEXT,
    number TEXT,
    person TEXT,
    tense TEXT,
    voice TEXT,
    refs TEXT,
    source TEXT NOT NULL DEFAULT 'cologne_mwinflect',
    PRIMARY KEY (form_slp1, lemma_slp1, model, gcase, number, person, tense, voice)
);
CREATE INDEX IF NOT EXISTS inflections_form ON inflections(form_slp1);
CREATE INDEX IF NOT EXISTS inflections_lemma ON inflections(lemma_slp1);

-- P4 Wave K2a (H181): stem-normalization bridge. `inflections` (Cologne,
-- case/number-labeled) and `forms` (DCS/vidyut/heritage, lemma-only) cite the
-- same lexeme under different stem spellings -- classically the strong/weak
-- nasal stem (Bagavant in `forms` vs Bagavat in `inflections`), or -an/-a
-- (rAjan/rAja). This crosswalk maps each variant stem spelling to ONE
-- canonical lemma key so the reverse-lookup pipeline surfaces a single
-- unified answer. Built by scripts/build_stem_bridge.py: data-gated (a pair is
-- bridged only when the two spellings SHARE a surface form AND are equal under
-- a whitelisted morphophonemic collapse), so unrelated homographs are never
-- merged. See data/SOURCES.md for the rule and coverage.
CREATE TABLE IF NOT EXISTS stem_bridge (
    variant_slp1 TEXT NOT NULL PRIMARY KEY,
    canonical_slp1 TEXT NOT NULL,
    rule TEXT
);
CREATE INDEX IF NOT EXISTS stem_bridge_canonical ON stem_bridge(canonical_slp1);

-- H345: MW <-> Heritage (INRIA) entry-level crosswalk, consumed verbatim from
-- SanskritLexicography/HeadwordLists/mw_heritage_crosswalk.tsv (never
-- re-derived here -- the anchors come from the Heritage mirror's own MW<->DICO
-- alignment, see that repo's mw_heritage_crosswalk.md). One row per unique MW
-- key1 (SLP1, = entries.slp1_key for dict='mw'), full crosswalk fidelity
-- including uncovered rows so "known uncovered" and "not an MW key" stay
-- distinguishable. Match tiers, from `covered` x `anchor`:
--   covered=1, anchor set   -- resolved to a DICO page anchor (link-out works)
--   covered=1, anchor NULL  -- covered but anchor unresolved (homonym-suffix
--                              mismatch, ~2.3% of covered; documented upstream)
--   covered=0               -- MW entry not in Heritage's lexicon
-- This is a coverage WITNESS only (is the headword in Heritage's hand-built
-- lexicon?), independent of forms.source='heritage' (H111's rule-generated
-- paradigm forms, lowest-trust). Do not conflate the two layers.
CREATE TABLE IF NOT EXISTS heritage_anchor (
    mw_key1 TEXT NOT NULL PRIMARY KEY,
    covered INTEGER NOT NULL,
    anchor TEXT
);
"""


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    # H111 migration: CREATE TABLE IF NOT EXISTS above is a no-op against a
    # pre-existing kosha.db from before the `category` column was added.
    cols = {row[1] for row in con.execute("PRAGMA table_info(forms)")}
    if "category" not in cols:
        con.execute("ALTER TABLE forms ADD COLUMN category TEXT")
        con.commit()
    # K2a (H181) migration: verb columns on `inflections` (nullable, so
    # pre-K2a nominal rows keep working; `--stage inflections` repopulates
    # both nominals and verbs). ALTER can't widen the PRIMARY KEY of an
    # existing table, but verb rows carry NULL gcase (NULLs never collide in a
    # SQLite unique index) and are Python-deduped in build_inflections, so the
    # old PK stays correct; a fresh DB gets the wider PK from SCHEMA above.
    icols = {row[1] for row in con.execute("PRAGMA table_info(inflections)")}
    for c in ("person", "tense", "voice"):
        if c not in icols:
            con.execute(f"ALTER TABLE inflections ADD COLUMN {c} TEXT")
    con.commit()
    # P3 migration: evidence-layer columns on lemmas (band, first_era,
    # example_*) -- see scripts/build_evidence.py ensure_columns(), called
    # again at --stage evidence time; done here too so a pre-existing DB
    # queried before that stage runs doesn't error on missing columns.
    from build_evidence import ensure_columns  # noqa: E402
    ensure_columns(con)
    return con


def build_lemmas(con):
    """D1 — vendor union_headwords.tsv, LEFT-JOIN the frequency sidecar."""
    if not UNION_HEADWORDS.exists():
        raise SystemExit(f"missing sibling feed: {UNION_HEADWORDS}")
    if not FREQ_TSV.exists():
        raise SystemExit(f"missing frequency sidecar: {FREQ_TSV}")

    freq = {}
    with open(FREQ_TSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            freq[row["lemma_slp1"]] = row

    con.execute("DELETE FROM lemmas")
    n = 0
    with open(UNION_HEADWORDS, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = []
        for r in reader:
            slp1 = r["slp1"]
            fr = freq.get(slp1)
            rows.append((
                slp1, r["iast"], int(r["n_dicts"]) if r["n_dicts"] else None,
                r["dicts"], r["gender"] or None,
                int(fr["count_all"]) if fr and fr["count_all"] else None,
                fr["grammar_all"] if fr else None,
                int(fr["rank_all"]) if fr and fr["rank_all"] else None,
                fr["periods"] if fr else None,
                int(fr["periods_sum"]) if fr and fr["periods_sum"] else None,
                float(fr["coverage_pct"]) if fr and fr.get("coverage_pct") else None,
                int(fr["core_rank"]) if fr and fr.get("core_rank") else None,
            ))
            n += 1
        con.executemany(
            "INSERT INTO lemmas (slp1, iast, n_dicts, dicts, gender, "
            "count_all, grammar_all, rank_all, periods, periods_sum, "
            "coverage_pct, core_rank) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
    con.commit()
    count = con.execute("SELECT COUNT(*) FROM lemmas").fetchone()[0]
    joined = con.execute("SELECT COUNT(*) FROM lemmas WHERE count_all IS NOT NULL").fetchone()[0]
    print(f"[D1] lemmas: {count} rows loaded, {joined} carry a frequency signal")
    return count, joined


def build_heritage(con):
    """H345 — ingest the MW↔Heritage crosswalk verbatim (consume, don't
    rebuild). Sibling feed like union_headwords; needs the SanskritLexicography
    checkout. Idempotent: full delete + reload."""
    if not HERITAGE_CROSSWALK.exists():
        raise SystemExit(f"missing sibling feed: {HERITAGE_CROSSWALK}")

    con.execute("DELETE FROM heritage_anchor")
    rows = []
    with open(HERITAGE_CROSSWALK, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.append((
                r["mw_key1"],
                int(r["covered_flag"]),
                r["heritage_entry_anchor"] or None,
            ))
    con.executemany(
        "INSERT INTO heritage_anchor (mw_key1, covered, anchor) VALUES (?,?,?)",
        rows,
    )
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM heritage_anchor").fetchone()[0]
    covered = con.execute("SELECT COUNT(*) FROM heritage_anchor WHERE covered=1").fetchone()[0]
    anchored = con.execute(
        "SELECT COUNT(*) FROM heritage_anchor WHERE covered=1 AND anchor IS NOT NULL"
    ).fetchone()[0]
    joined = con.execute(
        "SELECT COUNT(DISTINCT h.mw_key1) FROM heritage_anchor h "
        "JOIN entries e ON e.dict='mw' AND e.slp1_key=h.mw_key1 WHERE h.covered=1"
    ).fetchone()[0]
    print(f"[heritage] {total} MW keys loaded: {covered} Heritage-covered "
          f"({anchored} anchor-resolved, {covered - anchored} unresolved), "
          f"{joined} covered keys join a loaded MW entry")
    return total, covered, anchored, joined


STAGES = {"lemmas": build_lemmas}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=list(STAGES) + ["entries", "forms", "evidence", "inflections", "stem_bridge", "heritage"], default=None)
    ap.add_argument("--dicts", default="mw,pwg,ap90")
    args = ap.parse_args()

    con = connect()
    if args.stage in (None, "lemmas"):
        build_lemmas(con)
    if args.stage == "entries":
        from build_entries import build_entries  # noqa: E402
        build_entries(con, args.dicts.split(","))
    if args.stage == "forms":
        from build_forms import build_forms  # noqa: E402
        build_forms(con)
    if args.stage == "inflections":
        # P4 Wave K1: opt-in like `forms` (requires the sibling MWinflect
        # checkout's generated calc_tables.txt, not present on every dev
        # machine) -- not part of the default no-flag build.
        from build_inflections import build_inflections  # noqa: E402
        build_inflections(con)
    if args.stage == "stem_bridge":
        # K2a (H181): stem-normalization crosswalk between `inflections` and
        # `forms`. Requires both to be populated first.
        from build_stem_bridge import build_stem_bridge  # noqa: E402
        build_stem_bridge(con)
    if args.stage in (None, "heritage"):
        # H345: Heritage coverage witness. Part of the default build (same
        # sibling checkout the lemmas stage already requires); joined-entry
        # count in its summary line is 0 until `--stage entries` has run.
        build_heritage(con)
    if args.stage in (None, "evidence"):
        # P3 evidence layer: runs after lemmas + forms are populated (band
        # needs lemmas.rank_all; examples need the forms.form_slp1->lemma_slp1
        # join). When args.stage is None (full build), forms must already be
        # built for examples to resolve -- run `--stage forms` at least once
        # before the first full build on a fresh DB.
        from build_evidence import build_evidence  # noqa: E402
        build_evidence(con)
    # data_version (A2): NOT a citable release yet — Phase 1 D1-D4 local dev
    # build. First real data_version bump happens at the first GitHub release
    # per ARCHITECTURE.md (P2, D5-gated). "0.1.0-dev" marks this explicitly.
    con.execute(
        "INSERT INTO meta (key, value) VALUES ('data_version','0.1.0-dev') "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value"
    )
    con.commit()
    # Refresh planner statistics so index selectivity is known (cheap ~5 s;
    # the entries_dict_key covering index is chosen even without stats, but
    # ANALYZE keeps the search/forms plans optimal too). D5.
    con.execute("ANALYZE")
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
