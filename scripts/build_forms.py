"""kosha D3 — forms layer (form -> lemma), imported from the SanskritRussian
glossary pipeline (sibling repo, published copy of
SanskritLexicography/RussianTranslation/glossary's generated feeds — see
that dir's README.md: "the committed data + live site live in that repo").

Consumes two SLP1-keyed TSVs, no live calls:
    dcs_form2lemma.tsv     408,660 pairs (source='dcs')
    vidyut_form2lemma.tsv   28,567 pairs, DCS-miss fallback (source='vidyut')
"""
import csv
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SIBLING = ROOT.parent
GLOSSARY_REPO = SIBLING / "SanskritRussian"
DCS_F2L = GLOSSARY_REPO / "dcs_form2lemma.tsv"
VIDYUT_F2L = GLOSSARY_REPO / "vidyut_form2lemma.tsv"


def _load_tsv(path, source):
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            rows.append((row["form_slp1"], row["lemma_slp1"], source))
    return rows


def build_forms(con):
    if not DCS_F2L.exists() or not VIDYUT_F2L.exists():
        raise SystemExit(f"missing form->lemma feeds under {GLOSSARY_REPO} "
                          f"(expected dcs_form2lemma.tsv + vidyut_form2lemma.tsv)")

    con.execute("DELETE FROM forms")
    rows = _load_tsv(DCS_F2L, "dcs") + _load_tsv(VIDYUT_F2L, "vidyut")
    con.executemany(
        "INSERT OR IGNORE INTO forms (form_slp1, lemma_slp1, source) VALUES (?,?,?)",
        rows,
    )
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
    print(f"[D3] forms: {n} form->lemma pairs loaded (dcs + vidyut)")
    return n


if __name__ == "__main__":
    con = sqlite3.connect(str(ROOT / "data" / "db" / "kosha.db"))
    build_forms(con)
    con.close()
