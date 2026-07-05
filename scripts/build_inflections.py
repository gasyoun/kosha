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

K2a scope (H181): verb conjugations ARE now ingested, alongside the nominals.
The upstream Python-2 syntax bug in verbs/pysanskritv2/inputs/clean.py
(`sorted(..., key=lambda (c,v): ...)` — parenthesized lambda-parameter tuple
unpacking, removed in Python 3) that blocked verbs/redo.sh was fixed and
prepared as an on-its-merits upstream PR to sanskrit-lexicon/MWinflect (D5,
RELATIONS.md §2). With it fixed, `sh verbs/redo.sh` produces
verbs/pysanskritv2/tables/calc_tables.txt — present-system conjugations
(pre/ipf/ipv/opt x active/middle/passive), same verbatim-Cologne discipline
as the nominals (D3, no local correction layer).

Verb calc_tables.txt format (`model\troot\tL\tbase\tdata`, tab-separated):
    1,a,pre\tBU\t151456\tBav\tBavati:BavataH:Bavanti:Bavasi:BavaTaH:...(9 items)
  model = `class,voice,tense`: class = gana (1/4/6/10, or `_` for passive);
  voice = a(parasmaipada/active) / m(atmanepada/middle) / p(passive);
  tense = pre/ipf/ipv/opt (present system). The 9 data slots are person-major
  [3rd,2nd,1st] x number [sg,du,pl] -- verified against real endings
  (Bavati=-ti=3sg, Bavasi=-si=2sg, BavAmi=-mi=1sg). Verb rows store
  person/tense/voice and NULL gender/gcase; `model` = "v_<gana>" (or "v_p").

    python scripts/build_inflections.py                 # default MWinflect paths
    python scripts/build_inflections.py --calc-tables PATH --verb-tables PATH
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
DEFAULT_VERB_TABLES = (
    SIBLING / "MWinflect" / "verbs" / "pysanskritv2" / "tables" / "calc_tables.txt"
)

# 8 cases x 3 numbers (sg, du, pl), case-major, matching the fixed `sup`
# ending order in MWinflect/nominals/pydecl/decline.py.
CASES = ["nom", "acc", "instr", "dat", "abl", "gen", "loc", "voc"]
NUMBERS = ["sg", "du", "pl"]
SLOT_LABELS = [(c, n) for c in CASES for n in NUMBERS]  # 24 (case, number) pairs
assert len(SLOT_LABELS) == 24

# 3 persons x 3 numbers, person-major [3rd,2nd,1st] x [sg,du,pl] -- the fixed
# 9-slot verb ending order in MWinflect/verbs (see module docstring).
PERSONS = ["3", "2", "1"]
VERB_SLOTS = [(p, n) for p in PERSONS for n in NUMBERS]  # 9 (person, number) pairs
assert len(VERB_SLOTS) == 9
VOICE_MAP = {"a": "active", "m": "middle", "p": "passive"}

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


def build_verb_inflections(con, verb_tables_path: Path = DEFAULT_VERB_TABLES):
    """K2a (H181): append present-system verb conjugations to `inflections`.

    Called after the nominal load (which owns the DELETE FROM inflections), so
    this is additive. Rows are Python-deduped before insert -- the table PK on
    a migrated (pre-K2a) DB doesn't cover person/tense/voice and its NULL gcase
    means INSERT OR IGNORE won't collapse verb duplicates on its own.
    """
    if not verb_tables_path.exists():
        print(f"[P4 K2a] verb table absent ({verb_tables_path}); skipping verb ingest. "
              "Regenerate via `sh verbs/redo.sh` in the sibling MWinflect checkout "
              "(needs the clean.py Py2->Py3 fix, see module docstring).")
        return 0

    seen = set()
    rows = []
    lines_seen = skipped = 0
    with open(verb_tables_path, encoding="utf-8") as f:
        for line in f:
            lines_seen += 1
            if not line.strip() or line.startswith(";"):
                continue
            parts = line.rstrip("\n\r").split("\t")
            if len(parts) != 5:
                skipped += 1
                continue
            model_str, root, refs, _base, data = parts
            mparts = model_str.split(",")
            if len(mparts) != 3:
                skipped += 1
                continue
            gana, voice_code, tense = mparts
            voice = VOICE_MAP.get(voice_code)
            model = "v_p" if gana == "_" else f"v_{gana}"
            lemma_slp1 = root.replace("-", "")
            items = data.split(":")
            if len(items) != 9:
                skipped += 1
                continue
            for (person, number), item in zip(VERB_SLOTS, items):
                for form in item.split("/"):
                    if not form:
                        continue
                    key = (form, lemma_slp1, model, number, person, tense, voice)
                    if key in seen:
                        continue
                    seen.add(key)
                    # (form, lemma, model, gender=None, gcase=None, number,
                    #  person, tense, voice, refs)
                    rows.append((form, lemma_slp1, model, None, None, number,
                                 person, tense, voice, refs))
    con.executemany(
        "INSERT OR IGNORE INTO inflections "
        "(form_slp1, lemma_slp1, model, gender, gcase, number, person, tense, voice, refs) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    con.commit()
    print(f"[P4 K2a] verb conjugations: {len(rows)} rows inserted "
          f"({lines_seen} source lines, {skipped} skipped as malformed/unexpected shape).")
    return len(rows)


def build_inflections(con, calc_tables_path: Path = DEFAULT_CALC_TABLES,
                      verb_tables_path: Path = DEFAULT_VERB_TABLES):
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

    n_nom = con.execute("SELECT COUNT(*) FROM inflections").fetchone()[0]
    n_forms = con.execute("SELECT COUNT(DISTINCT form_slp1) FROM inflections").fetchone()[0]
    n_lemmas = con.execute("SELECT COUNT(DISTINCT lemma_slp1) FROM inflections").fetchone()[0]
    print(f"[P4 K1] nominal inflections: {n_nom} rows inserted (deduped from {total} generated), "
          f"{n_forms} distinct forms, {n_lemmas} distinct lemmas, "
          f"{lines_seen} source lines ({skipped_lines} skipped as malformed/unexpected shape).")

    # K2a (H181): append verb conjugations.
    build_verb_inflections(con, verb_tables_path)

    n = con.execute("SELECT COUNT(*) FROM inflections").fetchone()[0]
    print(f"[P4 K2a] inflections total (nominals + verbs): {n} rows.")
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--calc-tables", type=Path, default=DEFAULT_CALC_TABLES)
    ap.add_argument("--verb-tables", type=Path, default=DEFAULT_VERB_TABLES)
    args = ap.parse_args()
    con = sqlite3.connect(str(ROOT / "data" / "db" / "kosha.db"))
    build_inflections(con, args.calc_tables, args.verb_tables)
    con.close()
