"""compare_vidyut_verbs.py — P4 Wave E1 dual-engine diff, VERB half (H185 Task C).

The nominal sibling (scripts/compare_vidyut_cologne.py) compared vidyut-prakriya
against Cologne's declension tables. This script does the same for the
present-system CONJUGATIONS ingested in K2a (`inflections` rows with
`person IS NOT NULL`, models `v_<gana>` / `v_p`), directly answering
[csl-inflect #8](https://github.com/sanskrit-lexicon/csl-inflect/issues/8)
(Jim's Cologne-vs-Huet VERB comparison) with an independent third engine.

Mapping (Cologne -> vidyut Tinanta):
  * model `v_1/v_4/v_6/v_10`  -> Gana Bhvadi/Divadi/Tudadi/Curadi
  * model `v_p` (passive)     -> Prayoga.Karmani; the gaṇa is taken from the same
    root's `v_<gana>` model (a passive row carries no gaṇa of its own), and the
    root is skipped if it has no active/middle model to borrow one from.
  * tense pre/ipf/ipv/opt     -> Lakara Lat/Lan/Lot/VidhiLin (the present system)
  * voice active/middle/passive -> DhatuPada Parasmaipada/Atmanepada / Karmani
  * person 3/2/1 -> Purusha Prathama/Madhyama/Uttama;  number sg/du/pl -> Vacana

Honest coverage boundary (the reason the report flagged verbs as "a larger
follow-on"): vidyut's `Dhatu.mula` wants the *aupadeśika* root (with accent /
it-markers), but Cologne stores the bare SLP1 root. We pass the bare root as
the upadeśa; where Cologne's (root, gaṇa) doesn't match a vidyut derivation the
cell is VIDYUT_EMPTY, and roots that derive nothing at all are reported as an
unresolved-mapping bucket, NOT counted as disagreements. So the agreement % is
over the cells where BOTH engines produced something — a lower-bound
characterisation on the derivable subset, stated as such in the report.

Nominals-clean discipline reused: vidyut is a LOCAL library (RISKS.md R12), no
live call at build or query.

Usage:
    python scripts/compare_vidyut_verbs.py                 # all entry-bearing roots
    python scripts/compare_vidyut_verbs.py --limit 200
    python scripts/compare_vidyut_verbs.py --out data/e1
"""
import argparse
import json
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "db" / "kosha.db"
DEFAULT_OUT = ROOT / "data" / "e1"
DEFAULT_CROSSWALK = ROOT / "data" / "e1" / "dhatu_crosswalk.json"

ROOT_SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT_SCRIPTS))
# Reuse the nominal comparison's representation-vs-conflict sub-classifier so a
# verb DIFF is judged on the SAME basis (final-stop voicing = cosmetic, superset
# = coverage) instead of over-counting cosmetic differences as disagreement.
from compare_vidyut_cologne import is_final_stop_variant  # noqa: E402
from vidyut.prakriya import (  # noqa: E402
    Vyakarana, Dhatu, Gana, Lakara, Prayoga, Purusha, Vacana, DhatuPada, Pada,
)

GANA_OF_MODEL = {
    "v_1": Gana.Bhvadi, "v_4": Gana.Divadi, "v_6": Gana.Tudadi, "v_10": Gana.Curadi,
}
TENSE_LAKARA = {
    "pre": Lakara.Lat, "ipf": Lakara.Lan, "ipv": Lakara.Lot, "opt": Lakara.VidhiLin,
}
PERSON_PURUSHA = {"3": Purusha.Prathama, "2": Purusha.Madhyama, "1": Purusha.Uttama}
NUMBER_VACANA = {"sg": Vacana.Eka, "du": Vacana.Dvi, "pl": Vacana.Bahu}
# voice -> (prayoga, dhatu_pada or None)
VOICE_DERIV = {
    "active":  (Prayoga.Kartari, DhatuPada.Parasmaipada),
    "middle":  (Prayoga.Kartari, DhatuPada.Atmanepada),
    "passive": (Prayoga.Karmani, None),
}
TENSES = ["pre", "ipf", "ipv", "opt"]
PERSONS = ["3", "2", "1"]
NUMBERS = ["sg", "du", "pl"]


def open_db(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def load_crosswalk(path: Path) -> dict:
    """Load the H855 Cologne-root -> aupadeśika-dhātu crosswalk
    (`'model|root' -> aupadeśika`). A missing file yields {} -> every root falls
    back to its bare-root upadeśa, i.e. the pre-H855 behaviour. The committed
    crosswalk carries only aupadeśika strings, so this stays vidyut-data-free
    (only bundled `Dhatu.mula` is used downstream — R12)."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {k: e["aupadeshika"] for k, e in data.get("crosswalk", {}).items()
            if e.get("aupadeshika")}


def upadesha(cross: dict, root: str, model: str) -> str:
    """The upadeśa to feed Dhatu.mula for this Cologne (root, model): the
    crosswalk's aupadeśika if resolved, else the bare root (pre-H855 fallback)."""
    return cross.get(f"{model}|{root}", root)


def select_roots(con, limit: int):
    """Entry-bearing verb roots with their models, plus each root's borrowable
    gaṇa (for the passive v_p model). Returns [(root, [models], gana_model)]."""
    rows = con.execute(
        "SELECT DISTINCT i.lemma_slp1 AS root, i.model AS model, l.rank_all AS rank "
        "FROM inflections i "
        "JOIN entries e ON e.slp1_key = i.lemma_slp1 "
        "LEFT JOIN lemmas l ON l.slp1 = i.lemma_slp1 "
        "WHERE i.person IS NOT NULL "
        "ORDER BY (l.rank_all IS NULL), l.rank_all ASC, i.lemma_slp1 ASC"
    ).fetchall()
    by_root = {}
    order = []
    for r in rows:
        if r["root"] not in by_root:
            by_root[r["root"]] = []
            order.append(r["root"])
        by_root[r["root"]].append(r["model"])
    roots = []
    for root in order:
        models = by_root[root]
        gana_model = next((m for m in models if m in GANA_OF_MODEL), None)
        roots.append((root, models, gana_model))
    if limit:
        roots = roots[:limit]
    return roots


def cologne_verb_cells(con, root, model):
    """{(tense, voice, person, number): set(forms)} for one root+model."""
    out = defaultdict(set)
    for r in con.execute(
        "SELECT form_slp1, tense, voice, person, number FROM inflections "
        "WHERE lemma_slp1=? AND model=? AND person IS NOT NULL",
        (root, model),
    ):
        out[(r["tense"], r["voice"], r["person"], r["number"])].add(r["form_slp1"])
    return out


def vidyut_verb_cell(v, dhatu, voice, tense, person, number):
    prayoga, dhatu_pada = VOICE_DERIV[voice]
    kwargs = dict(dhatu=dhatu, prayoga=prayoga, lakara=TENSE_LAKARA[tense],
                  purusha=PERSON_PURUSHA[person], vacana=NUMBER_VACANA[number])
    if dhatu_pada is not None:
        kwargs["dhatu_pada"] = dhatu_pada
    try:
        return {pr.text for pr in v.derive(Pada.Tinanta(**kwargs))}
    except Exception:
        return set()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--examples", type=int, default=50)
    ap.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK,
                    help="H855 root->aupadeśika crosswalk; absent -> bare-root fallback")
    args = ap.parse_args()

    con = open_db(args.db)
    v = Vyakarana()
    cross = load_crosswalk(args.crosswalk)
    roots = select_roots(con, args.limit)
    print(f"[E1 verbs] comparing {len(roots)} entry-bearing verb root(s) "
          f"(vidyut Tinanta vs Cologne; {len(cross)} roots via H855 dhātu crosswalk)")

    cls = Counter()
    per_voice = defaultdict(Counter)
    examples = defaultdict(list)
    roots_all_empty = []      # vidyut derived nothing for the whole root (mapping gap)
    roots_no_gana_passive = []
    t0 = time.time()

    for n, (root, models, gana_model) in enumerate(roots, 1):
        try:
            gana_dhatu = (Dhatu.mula(upadesha(cross, root, gana_model),
                                     GANA_OF_MODEL[gana_model]) if gana_model else None)
        except Exception:
            gana_dhatu = None
        root_vidyut_hits = 0

        for model in models:
            if model in GANA_OF_MODEL:
                # H855: use the crosswalk's aupadeśika upadeśa (falls back to the
                # bare root — the pre-H855 behaviour — when unresolved).
                try:
                    dhatu = Dhatu.mula(upadesha(cross, root, model), GANA_OF_MODEL[model])
                except Exception:
                    dhatu = Dhatu.mula(root, GANA_OF_MODEL[model])
                voices = ["active", "middle"]
            else:  # v_p passive — borrow the root's gaṇa
                if gana_dhatu is None:
                    roots_no_gana_passive.append(root)
                    continue
                dhatu = gana_dhatu
                voices = ["passive"]

            col_cells = cologne_verb_cells(con, root, model)
            for voice in voices:
                for tense in TENSES:
                    for person in PERSONS:
                        for number in NUMBERS:
                            col = col_cells.get((tense, voice, person, number), set())
                            vid = vidyut_verb_cell(v, dhatu, voice, tense, person, number)
                            if not col and not vid:
                                continue
                            if vid:
                                root_vidyut_hits += 1
                            if col == vid:
                                label = "AGREE"
                            elif col and vid:
                                label = "DIFF"
                            elif vid:
                                label = "VIDYUT_ONLY"
                            else:
                                label = "COLOGNE_ONLY"
                            cls[label] += 1
                            per_voice[voice][label] += 1
                            if label == "DIFF":
                                # sub-classify: cosmetic (final-stop t/d),
                                # coverage (one engine a superset), or genuine.
                                if is_final_stop_variant(col, vid):
                                    sub = "final_stop"
                                elif col < vid:
                                    sub = "vidyut_superset"
                                elif vid < col:
                                    sub = "cologne_superset"
                                else:
                                    sub = "conflict"
                                cls[f"DIFF_{sub}"] += 1
                                if len(examples[f"DIFF_{sub}"]) < args.examples:
                                    examples[f"DIFF_{sub}"].append({
                                        "root": root, "model": model,
                                        "cell": f"{voice}.{tense}.{person}.{number}",
                                        "cologne": sorted(col), "vidyut": sorted(vid)})
                            if label in ("VIDYUT_ONLY", "COLOGNE_ONLY") \
                                    and len(examples[label]) < args.examples:
                                examples[label].append({
                                    "root": root, "model": model,
                                    "cell": f"{voice}.{tense}.{person}.{number}",
                                    "cologne": sorted(col), "vidyut": sorted(vid)})
        if root_vidyut_hits == 0:
            roots_all_empty.append(root)
        if n % 100 == 0:
            print(f"  {n}/{len(roots)}  ({time.time()-t0:.0f}s)")

    both = cls["AGREE"] + cls["DIFF"]  # cells where both engines produced a form
    # "compatible" = AGREE + the DIFFs that aren't a real conflict (final-stop
    # voicing is a citation-form choice; a superset is a coverage difference) —
    # the honest agreement figure, mirroring the nominal report's taxonomy.
    compatible = (cls["AGREE"] + cls["DIFF_final_stop"]
                  + cls["DIFF_vidyut_superset"] + cls["DIFF_cologne_superset"])
    report = {
        "handoff": "H185-C + H855 (dhātu-identity crosswalk)",
        "answers": "csl-inflect#8 (Huet verb comparison)",
        "sample_roots": len(roots),
        "crosswalk_roots_resolved": len(cross),
        "roots_vidyut_underivable": len(roots_all_empty),
        "roots_no_gana_for_passive": len(sorted(set(roots_no_gana_passive))),
        "classes": dict(cls),
        "strict_agreement_pct": round(100 * cls["AGREE"] / both, 2) if both else None,
        "compatible_pct": round(100 * compatible / both, 2) if both else None,
        "genuine_conflict_cells": cls["DIFF_conflict"],
        "diff_subclasses": {k[5:]: cls[k] for k in sorted(cls) if k.startswith("DIFF_")},
        "per_voice": {vc: dict(c) for vc, c in sorted(per_voice.items())},
        "examples": {k: examples[k] for k in examples},
        "underivable_examples": sorted(roots_all_empty)[:40],
        "elapsed_s": round(time.time() - t0, 1),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "e1_verbs_divergence.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "P4 Wave E1 verbs — vidyut Tinanta vs Cologne csl-inflect (present system)",
        f"entry-bearing roots        : {len(roots)}",
        f"roots via H855 crosswalk   : {len(cross)} (aupadeśika upadeśa; else bare-root)",
        f"roots vidyut can't derive  : {len(roots_all_empty)} (residual upadeśa/gaṇa gap)",
        f"roots w/o gaṇa for passive : {len(sorted(set(roots_no_gana_passive)))}",
        f"cells both-nonempty        : {both}",
        f"AGREE (strict)             : {cls['AGREE']} "
        f"({report['strict_agreement_pct']}% of both-nonempty)",
        f"COMPATIBLE (+ cosmetic)    : {compatible} ({report['compatible_pct']}%)",
        f"  DIFF final-stop (t/d)      : {cls['DIFF_final_stop']}",
        f"  DIFF vidyut superset       : {cls['DIFF_vidyut_superset']}",
        f"  DIFF cologne superset      : {cls['DIFF_cologne_superset']}",
        f"  DIFF genuine conflict      : {cls['DIFF_conflict']}",
        f"VIDYUT_ONLY (COL empty)    : {cls['VIDYUT_ONLY']}",
        f"COLOGNE_ONLY (vidyut empty): {cls['COLOGNE_ONLY']}  (upadeśa/gaṇa gap)",
        f"per-voice AGREE/DIFF       : "
        + "  ".join(f"{vc}:{c['AGREE']}/{c['DIFF']}" for vc, c in sorted(per_voice.items())),
        f"elapsed                    : {report['elapsed_s']}s",
    ]
    (args.out / "e1_verbs_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"[E1 verbs] wrote {args.out / 'e1_verbs_divergence.json'}")


if __name__ == "__main__":
    main()
