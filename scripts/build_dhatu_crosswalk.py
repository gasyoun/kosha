"""build_dhatu_crosswalk.py — P4 Wave E1 verb follow-on (H855, after H185 Task C).

Cologne's `inflections` verb rows store the **bare SLP1 root** (e.g. `sad`,
`arT`), but vidyut's `Dhatu.mula` wants the *aupadeśika* upadeśa — the
dhātupāṭha citation form with accent + anubandhas (e.g. `za\\da~\\`,
`arTa~`). Passing the bare root resolves only ~70 % of the gaṇa-1/4/6/10 roots
Cologne ingested (K2a); the rest derive nothing, which inflated COLOGNE_ONLY and
depressed the reported present-system agreement in
[`compare_vidyut_verbs.py`](compare_vidyut_verbs.py) (the "12.68 %" the E1 report
flagged as a *mapping artifact*, not real divergence).

This builds a static **Cologne-root → aupadeśika-dhātu crosswalk** that lifts
root resolution to ~93 %. For each Cologne `(root, gaṇa)` it picks, in order:

  1. **3sg** — the dhātupāṭha entry in that gaṇa whose vidyut present-3sg-active
     matches Cologne's own present-3sg-active (the most Cologne-faithful match);
  2. **direct** — the bare root already derives a non-empty paradigm as-is;
  3. **bare** — a normalized-bare-root match (strip accents + the trailing
     anunāsika it-vowel) against the dhātupāṭha;
  4. otherwise **unresolved** (reported honestly, never guessed).

The crosswalk (`data/e1/dhatu_crosswalk.json`) is **committed** so the verb
comparison needs only the *bundled* vidyut package (`Dhatu.mula`, R12-clean),
NOT the ~large external `vidyut-data` download, at run time. Build-time only,
with the sibling `vidyut-data` present:

    python -c "import vidyut; vidyut.download_data('../vidyut-data')"
    python scripts/build_dhatu_crosswalk.py
"""
import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "db" / "kosha.db"
DEFAULT_VDATA = ROOT.parent / "vidyut-data" / "prakriya"
DEFAULT_OUT = ROOT / "data" / "e1" / "dhatu_crosswalk.json"

from vidyut.prakriya import (  # noqa: E402
    Vyakarana, Dhatu, Gana, Lakara, Prayoga, Purusha, Vacana, DhatuPada, Pada, Data,
)

# The four thematic gaṇas Cologne's K2a verb ingest covers (models v_1/v_4/v_6/v_10).
GANA_OF_MODEL = {"v_1": Gana.Bhvadi, "v_4": Gana.Divadi, "v_6": Gana.Tudadi, "v_10": Gana.Curadi}
GANA_INT = {Gana.Bhvadi: 1, Gana.Divadi: 4, Gana.Tudadi: 6, Gana.Curadi: 10}
MODEL_GANA_INT = {m: GANA_INT[g] for m, g in GANA_OF_MODEL.items()}
_ACCENTS = "\\^/="
_IT_VOWELS = "aAiIuUfFxXeEoO"


def _present_3sg_active(v, dhatu):
    """vidyut present-3sg-active (laṭ, prathama, eka, kartari, parasmaipada)."""
    try:
        return {p.text for p in v.derive(Pada.Tinanta(
            dhatu=dhatu, prayoga=Prayoga.Kartari, lakara=Lakara.Lat,
            purusha=Purusha.Prathama, vacana=Vacana.Eka, dhatu_pada=DhatuPada.Parasmaipada))}
    except Exception:
        return set()


def _bare(aupadeshika: str) -> str:
    """Strip accents and the trailing anunāsika it-vowel from an upadeśa to get
    an approximate bare root for spelling-level matching against Cologne."""
    f = aupadeshika
    for a in _ACCENTS:
        f = f.replace(a, "")
    if f.endswith("~"):
        f = f[:-1]
        if f and f[-1] in _IT_VOWELS:
            f = f[:-1]
    return f.replace("~", "")


def build_indexes(v, entries):
    """Index the gaṇa-1/4/6/10 dhātupāṭha by (gaṇa_int, present-3sg) and by
    (gaṇa_int, bare-root). Values are (code, aupadeśika), lowest-code first."""
    by_3sg = defaultdict(list)
    by_bare = defaultdict(list)
    n = 0
    for e in entries:
        g = e.dhatu.gana
        if g not in GANA_INT:
            continue
        n += 1
        gi = GANA_INT[g]
        au = e.dhatu.aupadeshika
        try:
            dhatu = Dhatu.mula(au, g)
        except Exception:
            continue
        for f in _present_3sg_active(v, dhatu):
            by_3sg[(gi, f)].append((e.code, au))
        by_bare[(gi, _bare(au))].append((e.code, au))
    for idx in (by_3sg, by_bare):
        for k in idx:
            idx[k].sort()  # deterministic: lowest dhātupāṭha code wins
    return by_3sg, by_bare, n


def cologne_present_3sg(con, root, model):
    return {r["form_slp1"] for r in con.execute(
        "SELECT form_slp1 FROM inflections WHERE lemma_slp1=? AND model=? "
        "AND person='3' AND number='sg' AND tense='pre' AND voice='active'", (root, model))}


def resolve(v, con, by_3sg, by_bare, root, model):
    """Return (aupadeshika, via, code) or (None, 'unresolved', None)."""
    gi = MODEL_GANA_INT[model]
    gana = GANA_OF_MODEL[model]
    # 1. present-3sg match (most Cologne-faithful)
    for f in sorted(cologne_present_3sg(con, root, model)):
        if (gi, f) in by_3sg:
            code, au = by_3sg[(gi, f)][0]
            return au, "3sg", code
    # 2. the bare root already derives directly (identity upadeśa)
    try:
        d0 = Dhatu.mula(root, gana)
        if _present_3sg_active(v, d0):
            return root, "direct", None
    except Exception:
        pass
    # 3. normalized bare-root match
    if (gi, root) in by_bare:
        code, au = by_bare[(gi, root)][0]
        return au, "bare", code
    return None, "unresolved", None


def build_crosswalk(db_path=DEFAULT_DB, vdata=DEFAULT_VDATA, out=DEFAULT_OUT):
    if not Path(vdata).exists():
        raise SystemExit(
            f"vidyut-data not found at {vdata}\n"
            "Fetch it (build-time only) with:\n"
            "  python -c \"import vidyut; vidyut.download_data('../vidyut-data')\"")
    v = Vyakarana()
    entries = Data(str(vdata)).load_dhatu_entries()
    by_3sg, by_bare, n_gana = build_indexes(v, entries)
    print(f"[H855] dhātupāṭha entries in gaṇas 1/4/6/10: {n_gana}")

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT DISTINCT lemma_slp1 AS root, model FROM inflections "
        "WHERE person IS NOT NULL AND model IN ('v_1','v_4','v_6','v_10') "
        "ORDER BY lemma_slp1, model").fetchall()

    cross = {}
    via_counts = defaultdict(int)
    for r in rows:
        root, model = r["root"], r["model"]
        au, via, code = resolve(v, con, by_3sg, by_bare, root, model)
        via_counts[via] += 1
        cross[f"{model}|{root}"] = {"aupadeshika": au, "via": via, "code": code}

    total = len(rows)
    resolved = total - via_counts["unresolved"]
    payload = {
        "_about": "Cologne verb root -> vidyut aupadeśika-dhātu crosswalk (H855). "
                  "Key 'model|root'; use Dhatu.mula(aupadeshika, gaṇa-of-model). "
                  "via: 3sg=present-3sg match, direct=bare root already derives, "
                  "bare=normalized-bare match, unresolved=no vidyut dhātu found.",
        "vidyut_version": __import__("vidyut").__version__,
        "gana_dhatupatha_entries": n_gana,
        "cologne_root_models": total,
        "resolved": resolved,
        "resolved_pct": round(100 * resolved / total, 1) if total else None,
        "via_counts": dict(via_counts),
        "crosswalk": dict(sorted(cross.items())),
    }
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[H855] resolved {resolved}/{total} ({payload['resolved_pct']}%) "
          f"— via {dict(via_counts)}")
    print(f"[H855] wrote {out}")
    return payload


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--vdata", type=Path, default=DEFAULT_VDATA)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    build_crosswalk(args.db, args.vdata, args.out)
