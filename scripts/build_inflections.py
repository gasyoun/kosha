"""kosha P4 Wave K1 — forms/analysis sidecar (case/number/gender), imported
from the Cologne csl-inflect tool's own data pipeline (sibling repo
MWinflect, the local clone of csl-inflect's generation code — see
ROADMAP_INFLECT_2026_2027.md D3: "Cologne tables as-is to start", not
vidyut-generated tables).

Source: MWinflect's nominals/pysanskritv2/tables/calc_tables.txt — the exact
file csl-inflect's own sqlite/lgtab1 and sqlite/lgtab2 builders (`sqlite/
lgtab1/lgtab1.sql`, `sqlite/lgtab2/lgtab2.sql` .import) consume. Rather than
shelling out to the sqlite3 CLI (not installed in this environment) we parse
calc_tables.txt directly and derive the same information those two tables
hold, PLUS the grammatical case/number label neither lgtab1 nor lgtab2
stores explicitly (they only store table position implicitly).

calc_tables.txt format (`model\tstem\trefs\tdata`, tab-separated, no header):
    m_a	deva	95518,deva:95519,deva	devaH:devO:devAH:devam:...(24 items, ':' sep)
    ind	a-kasmAt	224,akasmAt	akasmAt   (1 item — indeclinable)

Each of the 24 items may itself hold sandhi/alternate-form variants
separated by '/' (e.g. `ttyE/ttaye`) — every variant becomes its own row.

Data is already SLP1 (confirmed against MWinflect/nominals/pydecl/decline.py:
`self.sup = 'aH:O:AH:am:...'` — H=visarga, O=au, E=ai, A/I/U=long vowels —
so no transcoding is needed to join against kosha's SLP1-native lemma keys).

Case/number decode: the fixed 24-slot order is 8 cases x 3 numbers, each
case contiguous (sg,du,pl) — verified against nominals/pydecl/decline.py's
`Decline_m_a.sup` comment and cross-checked against real forms in
calc_tables.txt (e.g. rAmeRa = index 6 = instr-sg; BagavAn = index 0 =
nom-sg; Darmakzetre = index 18 = loc-sg — all three of the roadmap's exit-
test forms, found verbatim in the generated table). Case order: nom, acc,
instr, dat, abl, gen, loc, voc (the traditional 1st-7th + vocative order).

Scope note (K1, verbatim from the task brief): verb conjugations
(vlgtab1/vlgtab2, MWinflect's verbs/ pipeline) are NOT ingested here. The
verbs/pysanskritv2/inputs/clean.py generation script has a genuine upstream
Python-2-only syntax bug (`sorted(..., key=lambda (c,v): ...)` — parenthesized
lambda-parameter tuple unpacking, removed in Python 3) that blocks the whole
verbs/redo.sh chain (bases/ and tables/ then fail on their missing inputs in
turn). This is an unrelated breakage in MWinflect's own pipeline, not a kosha
concern to patch around — see .ai_state.md and CHANGELOG.md for the exact
trace. None of K1's roadmap exit-test forms are verb forms, so this does not
block K1's own exit bar.

    python scripts/build_inflections.py                 # default MWinflect path
    python scripts/build_inflections.py --calc-tables PATH
"""
import argparse
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SIBLING = ROOT.parent
DEFAULT_CALC_TABLES = (
    SIBLING / "MWinflect" / "nominals" / "pysanskritv2" / "tables" / "calc_tables.txt"
)

# 8 cases x 3 numbers (sg, du, pl), case-major, matching the fixed `sup`
# ending order in MWinflect/nominals/pydecl/decline.py.
CASES = ["nom", "acc", "instr", "dat", "abl", "gen", "loc", "voc"]
NUMBERS = ["sg", "du", "pl"]
SLOT_LABELS = [(c, n) for c in CASES for n in NUMBERS]  # 24 (case, number) pairs
assert len(SLOT_LABELS) == 24

BATCH = 50_000


def _gender(model: str):
    if model == "ind":
        return None
    prefix = model.split("_", 1)[0]
    return prefix if prefix in ("m", "f", "n") else None


def iter_rows(calc_tables_path: Path):
    """Yield (form_slp1, lemma_slp1, model, gender, gcase, number, refs) tuples."""
    with open(calc_tables_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.rstrip("\n\r")
            if not line or line.startswith(";"):
                continue
            parts = line.split("\t")
            if len(parts) != 4:
                continue  # malformed line — skip, don't crash the whole ingest
            model, stem, refs, data = parts
            lemma_slp1 = stem.replace("-", "")
            gender = _gender(model)
            items = data.split(":")
            if model == "ind":
                for form in items[0].split("/"):
                    if form:
                        yield (form, lemma_slp1, model, gender, None, None, refs)
                continue
            if len(items) != 24:
                # Not the expected 8x3 paradigm (unexpected model shape) —
                # skip rather than mis-label; logged via the caller's counter.
                continue
            for (gcase, number), item in zip(SLOT_LABELS, items):
                for form in item.split("/"):
                    if form:
                        yield (form, lemma_slp1, model, gender, gcase, number, refs)


def build_inflections(con, calc_tables_path: Path = DEFAULT_CALC_TABLES):
    if not calc_tables_path.exists():
        raise SystemExit(
            f"missing MWinflect nominal table: {calc_tables_path}\n"
            "Regenerate via `sh nominals/redo.sh` in the sibling MWinflect checkout "
            "(requires a python3 on PATH; see .ai_state.md for the K1 build notes)."
        )

    con.execute("DELETE FROM inflections")
    con.commit()

    total = 0
    skipped_lines = 0
    batch = []
    lines_seen = 0
    with open(calc_tables_path, encoding="utf-8") as f:
        for line in f:
            lines_seen += 1
            if not line.strip() or line.startswith(";"):
                continue
            parts = line.rstrip("\n\r").split("\t")
            if len(parts) != 4:
                skipped_lines += 1
                continue
            model, stem, refs, data = parts
            lemma_slp1 = stem.replace("-", "")
            gender = _gender(model)
            items = data.split(":")
            if model == "ind":
                slots = [(None, None, it) for it in items[:1]]
            elif len(items) == 24:
                slots = [(gc, n, it) for (gc, n), it in zip(SLOT_LABELS, items)]
            else:
                skipped_lines += 1
                continue
            for gcase, number, item in slots:
                for form in item.split("/"):
                    if not form:
                        continue
                    batch.append((form, lemma_slp1, model, gender, gcase, number, refs))
                    if len(batch) >= BATCH:
                        con.executemany(
                            "INSERT OR IGNORE INTO inflections "
                            "(form_slp1, lemma_slp1, model, gender, gcase, number, refs) "
                            "VALUES (?,?,?,?,?,?,?)",
                            batch,
                        )
                        con.commit()
                        total += len(batch)
                        batch = []
    if batch:
        con.executemany(
            "INSERT OR IGNORE INTO inflections "
            "(form_slp1, lemma_slp1, model, gender, gcase, number, refs) VALUES (?,?,?,?,?,?,?)",
            batch,
        )
        con.commit()
        total += len(batch)

    n = con.execute("SELECT COUNT(*) FROM inflections").fetchone()[0]
    n_forms = con.execute("SELECT COUNT(DISTINCT form_slp1) FROM inflections").fetchone()[0]
    n_lemmas = con.execute("SELECT COUNT(DISTINCT lemma_slp1) FROM inflections").fetchone()[0]
    print(f"[P4 K1] inflections: {n} rows inserted (deduped from {total} generated), "
          f"{n_forms} distinct forms, {n_lemmas} distinct lemmas, "
          f"{lines_seen} source lines ({skipped_lines} skipped as malformed/unexpected shape). "
          "Verb conjugations NOT included (upstream MWinflect verbs/ pipeline blocker — see module docstring).")
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--calc-tables", type=Path, default=DEFAULT_CALC_TABLES)
    args = ap.parse_args()
    con = sqlite3.connect(str(ROOT / "data" / "db" / "kosha.db"))
    build_inflections(con, args.calc_tables)
    con.close()
