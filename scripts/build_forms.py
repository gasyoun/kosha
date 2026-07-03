"""kosha D3 — forms layer (form -> lemma), imported from the SanskritRussian
glossary pipeline (sibling repo, published copy of
SanskritLexicography/RussianTranslation/glossary's generated feeds — see
that dir's README.md: "the committed data + live site live in that repo").

Consumes three SLP1-keyed TSVs, no live calls:
    dcs_form2lemma.tsv         408,660 pairs (source='dcs')
    vidyut_form2lemma.tsv       28,567 pairs, DCS-miss fallback (source='vidyut')
    heritage_only_forms.tsv    992,194 pairs, Heritage/INRIA rule-generated
                                paradigm forms absent from dcs+vidyut (source='heritage')

H111 trust ordering (highest to lowest): dcs > vidyut > heritage. Heritage's
declension/conjugation engine generates the WHOLE paradigm of every stem, so it
over-generates grammatically-possible but unattested forms (hypergeneration);
H105's hand-adjudication also found occasional stem mis-assignment. Heritage
rows are corroborating evidence only -- never surface a heritage-only
form/lemma as authoritative without a dcs/vidyut row for the same form_slp1.
The heritage feed is loaded LAST and is purely additive: it can only add rows
(form_slp1, lemma_slp1, 'heritage') that don't already exist for
(form_slp1, lemma_slp1) under dcs/vidyut, and it never touches existing
dcs/vidyut rows. Each heritage row also carries its `category` (nominal,
finite-verb, participle, iic/iiv/iip-compound, ...) so consumers can filter
the compound-initial categories, the largest hypergeneration source.
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
HERITAGE_F2L = SIBLING / "SanskritLexicography" / "HeadwordLists" / "heritage_only_forms.tsv"


def _load_tsv(path, source):
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            rows.append((row["form_slp1"], row["lemma_slp1"], source, None))
    return rows


def _load_heritage(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            rows.append((row["form_slp1"], row["lemma_slp1"], "heritage",
                         row["heritage_category"]))
    return rows


def build_forms(con):
    if not DCS_F2L.exists() or not VIDYUT_F2L.exists():
        raise SystemExit(f"missing form->lemma feeds under {GLOSSARY_REPO} "
                          f"(expected dcs_form2lemma.tsv + vidyut_form2lemma.tsv)")
    if not HERITAGE_F2L.exists():
        raise SystemExit(f"missing heritage feed: {HERITAGE_F2L} "
                          f"(regenerate via SanskritLexicography/HeadwordLists/heritage_forms_oracle.py)")

    con.execute("DELETE FROM forms")
    dcs_rows = _load_tsv(DCS_F2L, "dcs")
    vidyut_rows = _load_tsv(VIDYUT_F2L, "vidyut")
    con.executemany(
        "INSERT OR IGNORE INTO forms (form_slp1, lemma_slp1, source, category) VALUES (?,?,?,?)",
        dcs_rows + vidyut_rows,
    )
    con.commit()
    n_dcs_vidyut = con.execute("SELECT COUNT(*) FROM forms").fetchone()[0]

    # heritage loaded LAST, additive-only (INSERT OR IGNORE never touches the
    # dcs/vidyut rows just inserted above -- H111).
    heritage_rows = _load_heritage(HERITAGE_F2L)
    con.executemany(
        "INSERT OR IGNORE INTO forms (form_slp1, lemma_slp1, source, category) VALUES (?,?,?,?)",
        heritage_rows,
    )
    con.commit()

    n = con.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
    n_heritage = n - n_dcs_vidyut
    print(f"[D3] forms: {n} form->lemma pairs loaded "
          f"(dcs+vidyut {n_dcs_vidyut}, heritage +{n_heritage})")
    return n


if __name__ == "__main__":
    con = sqlite3.connect(str(ROOT / "data" / "db" / "kosha.db"))
    build_forms(con)
    con.close()
