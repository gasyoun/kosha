"""build_hybrid_forms.py — P4 Wave E1 hybridize pass (H185).

Implements MG's E1 dual-engine ruling (05-07-2026, reaffirmed 10-07-2026 —
**HYBRIDIZE**): keep the Cologne csl-inflect tables as the attested,
hand-curated base (D3), and layer **vidyut-prakriya** (a local library —
RISKS.md R12-clean, no live call) over the `inflections` table to:

  1. AUTO-FIX the ṇatva bug (MWinflect#6, Pāṇini 8.4.1-2). Every DIFF cell whose
     ONLY divergence is n↔ṇ (Cologne emits `nfpena`/`nfpAnAm` for attested
     `nfpeRa`/`nfpARAm`) gets the vidyut-corrected form inserted as a new row
     with `source='hybrid-natva-fix'`. The buggy Cologne row is NOT deleted —
     it stays for the reverse-lookup audit trail (a reader who types the wrong
     `nfpena` still resolves it), and the display layer (app/paradigm.py)
     prefers the fix.

  2. GAP-FILL coverage holes. Every VIDYUT_ONLY cell (Cologne has no form,
     vidyut derives one — dominated by cardinal numerals like `saptadaSan`,
     m_card) gets the vidyut form inserted with `source='vidyut-gap-fill'`.

  3. FLAG, not overwrite, the scholarly forks. Pronominal mis-models
     (`sarva` declined nominally in m_a/n_a as well as correctly in m_pron) and
     the feminine/consonant-stem derivation forks (`other`) get `disputed=1` on
     their Cologne rows for that cell — Cologne stays the default display, the
     flag is an editorial-review signal for the K2b UI. Representation-only
     divergences (final-stop voicing) and pure coverage supersets are left
     untouched: neither engine is "wrong" there.

This is the implementation half of E1; the characterisation half is
scripts/compare_vidyut_cologne.py + E1_DIVERGENCE_REPORT.md, whose
classification helpers this script reuses verbatim (is_natva_diff /
is_pronominal_diff / subclass_diff / vidyut_cell / the Vibhakti/Vacana/Linga
mappings) — same engine, same verdicts, so the fix set and the report never
drift.

Idempotent: each run first removes its own prior rows
(`source IN ('hybrid-natva-fix','vidyut-gap-fill')`) and clears every
`disputed` flag, then re-derives. Run it AFTER `scripts/build_inflections.py`
(`--stage inflections`), which DELETEs+repopulates `inflections` from the
Cologne base and would wipe hybrid rows; the build order is
inflections -> hybrid (mirrors the crosswalk->entries->forms->db discipline).

Usage:
    python scripts/build_hybrid_forms.py                 # full entry-bearing set
    python scripts/build_hybrid_forms.py --limit 10000   # top-N (reproduces the E1 report sample)
    python scripts/build_hybrid_forms.py --db PATH --out data/hybrid

Outputs (gitignored measurement, regenerable):
    <out>/hybrid_report.json   — counts + example fixes/flags per class
    <out>/hybrid_summary.txt   — human-readable rollup
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
sys.path.insert(0, str(ROOT / "scripts"))

DEFAULT_DB = ROOT / "data" / "db" / "kosha.db"
DEFAULT_OUT = ROOT / "data" / "hybrid"

# Reuse the E1 comparison engine verbatim — same classifier, same verdicts, so
# the applied fix set can never diverge from E1_DIVERGENCE_REPORT.md's numbers.
from compare_vidyut_cologne import (  # noqa: E402
    GENDER_TO_LINGA, cologne_cells, is_natva_diff, subclass_diff,
    select_stems, vidyut_cell,
)
from vidyut.prakriya import Vyakarana, Pratipadika  # noqa: E402

CASES = ["nom", "acc", "instr", "dat", "abl", "gen", "loc", "voc"]
NUMBERS = ["sg", "du", "pl"]

HYBRID_SOURCES = ("hybrid-natva-fix", "vidyut-gap-fill")


def reset_prior_hybrid(con: sqlite3.Connection) -> tuple[int, int]:
    """Make the pass idempotent: drop this script's own prior rows and clear
    every disputed flag, so a re-run reflects the current engine exactly."""
    n_rows = con.execute(
        "DELETE FROM inflections WHERE source IN (?, ?)", HYBRID_SOURCES
    ).rowcount
    n_flags = con.execute(
        "UPDATE inflections SET disputed=0 WHERE disputed=1"
    ).rowcount
    con.commit()
    return n_rows, n_flags


def _model_refs(con, lemma, model):
    row = con.execute(
        "SELECT refs FROM inflections WHERE lemma_slp1=? AND model=? "
        "AND person IS NULL AND source='cologne_mwinflect' LIMIT 1",
        (lemma, model),
    ).fetchone()
    return row[0] if row else None


def build_hybrid_forms(con: sqlite3.Connection, limit: int = 0,
                       out_dir: Path = DEFAULT_OUT, examples: int = 40) -> dict:
    """Apply the E1 hybridize policy to `inflections`. Returns the report dict."""
    # `disputed` may be absent on a pre-E1 DB queried before build_db.connect()
    # migrated it — ensure it exists so this script is safe to run standalone.
    icols = {r[1] for r in con.execute("PRAGMA table_info(inflections)")}
    if "disputed" not in icols:
        con.execute("ALTER TABLE inflections ADD COLUMN disputed INTEGER NOT NULL DEFAULT 0")
        con.commit()

    n_prior_rows, n_prior_flags = reset_prior_hybrid(con)
    print(f"[E1 hybrid] reset {n_prior_rows} prior hybrid row(s), "
          f"{n_prior_flags} prior disputed flag(s)")

    v = Vyakarana()
    stems = select_stems(con, limit)
    print(f"[E1 hybrid] processing {len(stems)} entry-bearing nominal paradigm(s)")

    stats = Counter()
    gapfill_by_model = Counter()
    disputed_by_sub = Counter()
    natva_stems = set()
    disputed_stems = set()
    ex = defaultdict(list)

    natva_rows = []      # (form, lemma, model, gender, gcase, number, refs)
    gapfill_rows = []
    disputed_cells = []  # (lemma, model, gcase, number)

    # vidyut derivation depends only on (lemma, linga); memoise across the
    # multiple Cologne models a stem may appear under (e.g. m_a + m_pron).
    vid_cache: dict[tuple[str, str], dict] = {}
    t0 = time.time()

    for n, s in enumerate(stems, 1):
        lemma, model, gender = s["lemma"], s["model"], s["gender"]
        linga = GENDER_TO_LINGA[gender]
        ck = (lemma, gender)
        vcells = vid_cache.get(ck)
        if vcells is None:
            try:
                prati = Pratipadika.basic(lemma)
            except Exception:
                stats["bad_stem"] += 1
                vid_cache[ck] = {}
                continue
            vcells = {}
            for gcase in CASES:
                for number in NUMBERS:
                    vcells[(gcase, number)] = vidyut_cell(v, prati, linga, gcase, number)
            vid_cache[ck] = vcells
        if not vcells:
            continue

        col = cologne_cells(con, lemma, model)
        refs = None
        for gcase in CASES:
            for number in NUMBERS:
                c = col.get((gcase, number), set())
                vd = vcells.get((gcase, number), set())
                if not c and not vd:
                    continue
                if c == vd:
                    continue
                cell = f"{gcase}.{number}"
                if not c and vd:
                    # VIDYUT_ONLY — gap-fill (cardinals &c.)
                    if refs is None:
                        refs = _model_refs(con, lemma, model)
                    for form in sorted(vd):
                        gapfill_rows.append((form, lemma, model, gender, gcase, number, refs))
                    stats["gapfill_cells"] += 1
                    gapfill_by_model[model] += 1
                    if len(ex["gapfill"]) < examples:
                        ex["gapfill"].append({"lemma": lemma, "model": model,
                                              "cell": cell, "vidyut": sorted(vd)})
                    continue
                if not vd:
                    continue  # COLOGNE_ONLY — Cologne richer, keep as-is
                # DIFF — classify and act
                sub = subclass_diff(c, vd)
                if sub == "natva":
                    if refs is None:
                        refs = _model_refs(con, lemma, model)
                    for form in sorted(vd):
                        natva_rows.append((form, lemma, model, gender, gcase, number, refs))
                    stats["natva_cells"] += 1
                    natva_stems.add((lemma, model))
                    if len(ex["natva"]) < examples:
                        ex["natva"].append({"lemma": lemma, "model": model, "cell": cell,
                                            "cologne": sorted(c), "vidyut": sorted(vd)})
                elif sub in ("pronominal", "other"):
                    disputed_cells.append((lemma, model, gcase, number))
                    stats["disputed_cells"] += 1
                    disputed_by_sub[sub] += 1
                    disputed_stems.add((lemma, model))
                    if len(ex[f"disputed_{sub}"]) < examples:
                        ex[f"disputed_{sub}"].append({"lemma": lemma, "model": model,
                                                      "cell": cell, "cologne": sorted(c),
                                                      "vidyut": sorted(vd)})
                else:
                    # final_stop / vidyut_superset / cologne_superset — neither
                    # engine wrong; leave Cologne as the default display.
                    stats[f"skipped_{sub}"] += 1

        if n % 5000 == 0:
            print(f"  {n}/{len(stems)}  ({time.time()-t0:.0f}s, "
                  f"natva={stats['natva_cells']} gap={stats['gapfill_cells']} "
                  f"disp={stats['disputed_cells']})")

    # ---- apply mutations ---------------------------------------------------
    con.executemany(
        "INSERT OR IGNORE INTO inflections "
        "(form_slp1, lemma_slp1, model, gender, gcase, number, refs, source, disputed) "
        "VALUES (?,?,?,?,?,?,?,'hybrid-natva-fix',0)",
        natva_rows,
    )
    con.executemany(
        "INSERT OR IGNORE INTO inflections "
        "(form_slp1, lemma_slp1, model, gender, gcase, number, refs, source, disputed) "
        "VALUES (?,?,?,?,?,?,?,'vidyut-gap-fill',0)",
        gapfill_rows,
    )
    con.executemany(
        "UPDATE inflections SET disputed=1 "
        "WHERE lemma_slp1=? AND model=? AND gcase=? AND number=? "
        "AND person IS NULL AND source='cologne_mwinflect'",
        disputed_cells,
    )
    con.commit()

    n_natva_added = con.execute(
        "SELECT COUNT(*) FROM inflections WHERE source='hybrid-natva-fix'").fetchone()[0]
    n_gap_added = con.execute(
        "SELECT COUNT(*) FROM inflections WHERE source='vidyut-gap-fill'").fetchone()[0]
    n_disputed = con.execute(
        "SELECT COUNT(*) FROM inflections WHERE disputed=1").fetchone()[0]

    report = {
        "handoff": "H185",
        "ruling": "hybridize",
        "sample_stems": len(stems),
        "natva_fix": {
            "cells": stats["natva_cells"],
            "stems_affected": len(natva_stems),
            "rows_inserted": n_natva_added,
            "examples": ex["natva"],
        },
        "gap_fill": {
            "cells": stats["gapfill_cells"],
            "rows_inserted": n_gap_added,
            "by_model": dict(gapfill_by_model.most_common()),
            "examples": ex["gapfill"],
        },
        "disputed": {
            "cells_flagged": stats["disputed_cells"],
            "rows_flagged": n_disputed,
            "stems_affected": len(disputed_stems),
            "by_subclass": dict(disputed_by_sub),
            "examples": {k[9:]: ex[k] for k in ex if k.startswith("disputed_")},
        },
        "left_as_is": {k[8:]: stats[k] for k in stats if k.startswith("skipped_")},
        "bad_stems": stats["bad_stem"],
        "elapsed_s": round(time.time() - t0, 1),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "hybrid_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "P4 Wave E1 hybridize (H185) — vidyut layered over Cologne inflections",
        f"entry-bearing paradigms  : {len(stems)}",
        f"ṇatva auto-fix           : {stats['natva_cells']} cells / "
        f"{len(natva_stems)} stems -> {n_natva_added} 'hybrid-natva-fix' rows",
        f"gap-fill (VIDYUT_ONLY)   : {stats['gapfill_cells']} cells -> "
        f"{n_gap_added} 'vidyut-gap-fill' rows  {dict(gapfill_by_model.most_common(6))}",
        f"disputed flags           : {stats['disputed_cells']} cells / "
        f"{len(disputed_stems)} stems  {dict(disputed_by_sub)}",
        f"left as-is (not wrong)   : "
        f"{ {k[8:]: stats[k] for k in stats if k.startswith('skipped_')} }",
        f"bad stems (vidyut parse) : {stats['bad_stem']}",
        f"total disputed rows      : {n_disputed}",
        f"elapsed                  : {report['elapsed_s']}s",
    ]
    (out_dir / "hybrid_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"[E1 hybrid] wrote {out_dir / 'hybrid_report.json'}")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=0,
                    help="top-N entry-bearing stems (0 = full set)")
    ap.add_argument("--examples", type=int, default=40)
    args = ap.parse_args()
    con = sqlite3.connect(str(args.db))
    con.row_factory = sqlite3.Row
    try:
        build_hybrid_forms(con, args.limit, args.out, args.examples)
    finally:
        con.close()


if __name__ == "__main__":
    main()
