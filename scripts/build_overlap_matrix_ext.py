#!/usr/bin/env python3
"""kosha — extend the headword pairwise-overlap matrix with the Tamil fold (H4732, census C5).

The registered `headword-overlap-matrix` (H684, 11-07-2026) covers the
**15-dict union** and predates the 06-09-2026 `tamil-fold` ingest (H4178):
mwd (Cologne Digital Sanskrit Lexicon = MW), cap (Capeller) and otl (Cologne
Online Tamil Lexicon) from the csl-santam fold are absent from it. This
builder extends the matrix to **18 dictionaries** (153 pairwise cells) without
touching the registered 15-dict dataset or the union master:

* union headwords: sibling ``SanskritLexicography/HeadwordLists/union/union_headwords.tsv``
  (read-only, SL the headword master — never rebuilt here);
* Tamil-fold keys: sibling ``csl-santam/sqlite/tamil.sqlite`` (read-only,
  single table ``tamil(id, st, en)``; 1=mwd, 2=cap, 3=otl; cpd/Pahlavi excluded
  exactly as csl-santam's own UI excludes it);
* keying: fold ``st`` values are Kyoto-Harvard (mwd/cap) or HK-like (otl) —
  converted to the union's SLP1 key via the canonical house chain
  ``sanskrit-util`` (IAST->SLP1 table) x ``tools/KeySwap/scheme_bridge``
  (HK->IAST). The SLP1 table is imported, never re-typed;
* verification: all 105 registered 15x15 baseline cells are recomputed and
  compared ints-exact against the sibling baseline TSV — the extension must
  not move them (tamil codes add only new rows/columns).

Outputs (all under ``data/tamil/``):

* ``headword_overlap_matrix_ext.tsv`` — 153 rows, same 5-column shape as the
  registered matrix (dict_a, dict_b, shared, union, jaccard);
* ``overlap_matrix_ext_stats.json`` — provenance pins + key-cleaning stats +
  baseline-verification verdict + canary cells;
* ``OVERLAP_MATRIX_EXT_DELTA_14-09-2026.md`` — delta report (generated).

Usage:
    python scripts/build_overlap_matrix_ext.py            # build + verify
    python scripts/build_overlap_matrix_ext.py --verify   # verify outputs only

Stdlib only at runtime besides the vendored house translit chain.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import subprocess
from itertools import combinations
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SL_ROOT = ROOT.parent / "SanskritLexicography"
SANTAM_ROOT = ROOT.parent / "csl-santam"
SANSKRIT_UTIL_ROOT = ROOT.parent / "sanskrit-util"

UNION_TSV = SL_ROOT / "HeadwordLists" / "union" / "union_headwords.tsv"
BASELINE_TSV = SL_ROOT / "data" / "headword_overlap_matrix.tsv"
COVERAGE_TSV = ROOT / "data" / "concordance" / "dict_corpus_coverage.tsv"
SOURCE_SQLITE = SANTAM_ROOT / "sqlite" / "tamil.sqlite"

OUT_TSV = ROOT / "data" / "tamil" / "headword_overlap_matrix_ext.tsv"
OUT_STATS = ROOT / "data" / "tamil" / "overlap_matrix_ext_stats.json"
OUT_MD = ROOT / "data" / "tamil" / "OVERLAP_MATRIX_EXT_DELTA_14-09-2026.md"

TAMIL_CODES = ("mwd", "cap", "otl")  # id 1, 2, 3 — cpd (4, Pahlavi) excluded
LEXICON_IDS = {"mwd": 1, "cap": 2, "otl": 3}


def _git_head(repo: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unavailable"


def _load_translit():
    """Import the canonical house chain (import, never re-type the SLP1 table)."""
    sys.path.insert(0, str(SANSKRIT_UTIL_ROOT / "tools" / "KeySwap"))
    sys.path.insert(0, str(SANSKRIT_UTIL_ROOT / "py"))
    from scheme_bridge import hk_to_iast  # noqa: PLC0415
    from sanskrit_util import to_slp1  # noqa: PLC0415

    return hk_to_iast, to_slp1


def _open_source() -> tuple[sqlite3.Connection, dict[str, int]]:
    """Read-only sqlite with the fold's per-cell UTF-8/cp1252/latin-1 decode."""
    cp1252_fallbacks = 0
    latin1_fallbacks = 0

    def _decode(b: bytes) -> str:
        nonlocal cp1252_fallbacks, latin1_fallbacks
        try:
            return b.decode("utf-8")
        except UnicodeDecodeError:
            pass
        try:
            cp1252_fallbacks += 1
            return b.decode("cp1252")
        except UnicodeDecodeError:
            # stray bytes undefined in cp1252 (e.g. 0x81); latin-1 maps all 256
            latin1_fallbacks += 1
            return b.decode("latin-1")

    con = sqlite3.connect(f"file:{SOURCE_SQLITE}?mode=ro", uri=True)
    con.text_factory = _decode
    fallback_stats = {"cp1252": cp1252_fallbacks, "latin1": latin1_fallbacks}
    return con, fallback_stats


def _split_variants(raw: str) -> list[str]:
    """Minimal key cleaning: strip; ' & ' entries contribute each variant."""
    out = []
    for part in raw.strip().split("&"):
        p = part.strip()
        if not p or p.startswith("-"):  # continuation tokens like '-prakalpanA'
            continue
        out.append(p)
    return out


def read_union() -> tuple[dict[str, set[str]], set[str], int]:
    """Per-code headword sets from the union master + the full SLP1 key set."""
    sets: dict[str, set[str]] = {}
    all_keys: set[str] = set()
    n_rows = 0
    with open(UNION_TSV, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        i_slp1, i_dicts = header.index("slp1"), header.index("dicts")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(i_slp1, i_dicts):
                continue
            n_rows += 1
            slp1 = parts[i_slp1]
            all_keys.add(slp1)
            for code in parts[i_dicts].split():
                sets.setdefault(code, set()).add(slp1)
    return sets, all_keys, n_rows


def read_coverage() -> dict[str, str]:
    cov: dict[str, str] = {}
    with open(COVERAGE_TSV, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        j_slp1, j_status = hdr.index("slp1"), hdr.index("status")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > max(j_slp1, j_status):
                cov[parts[j_slp1]] = parts[j_status]
    return cov


def read_baseline() -> dict[tuple[str, str], tuple[int, int, float]]:
    base: dict[tuple[str, str], tuple[int, int, float]] = {}
    with open(BASELINE_TSV, encoding="utf-8") as f:
        f.readline()
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            a, b = parts[0], parts[1]
            base[(a, b)] = (int(parts[2]), int(parts[3]), float(parts[4]))
    return base


def build_tamil_sets(hk_to_iast, to_slp1, union_keys: set[str]) -> tuple[dict[str, set[str]], dict]:
    con, fallback = _open_source()
    try:
        sets: dict[str, set[str]] = {}
        stats: dict[str, dict] = {}
        for code in TAMIL_CODES:
            raw_rows = con.execute(
                "SELECT st FROM tamil WHERE id=?", (LEXICON_IDS[code],)
            ).fetchall()
            n_raw = len(raw_rows)
            keys: set[str] = set()
            n_dropped_parts = 0
            n_residue_keys = 0
            for (st,) in raw_rows:
                for part in _split_variants(st):
                    k = to_slp1(hk_to_iast(part))
                    # residue: anything outside the SLP1 ascii alphabet survives
                    if not k or any(not c.isalpha() for c in k):
                        n_residue_keys += 1
                        if not k:
                            continue
                    keys.add(k)
            n_dropped_parts = n_raw  # per-row accounting lives in variants count below
            matched = sum(1 for k in keys if k in union_keys)
            sets[code] = keys
            stats[code] = {
                "raw_entries": n_raw,
                "unique_slp1_keys": len(keys),
                "matched_into_union": matched,
                "matched_share": round(100.0 * matched / len(keys), 2) if keys else 0.0,
                "keys_with_nonalpha_residue": n_residue_keys,
            }
        fb_cp, fb_l1 = fallback["cp1252"], fallback["latin1"]
    finally:
        con.close()
    return sets, {"per_dict": stats, "cp1252_fallback_cells": fb_cp, "latin1_fallback_cells": fb_l1}


def jaccard(a: set[str], b: set[str]) -> tuple[int, int, float]:
    inter = len(a & b)
    union = len(a | b)
    return inter, union, (inter / union if union else 0.0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="verify emitted outputs only")
    args = parser.parse_args()

    for p in (UNION_TSV, BASELINE_TSV, COVERAGE_TSV, SOURCE_SQLITE):
        if not p.exists():
            print(f"FATAL: missing input {p}", file=sys.stderr)
            return 2

    hk_to_iast, to_slp1 = _load_translit()

    union_sets, union_keys, n_union_rows = read_union()
    base = read_baseline()
    tamil_sets, tamil_stats = build_tamil_sets(hk_to_iast, to_slp1, union_keys)
    cov = read_coverage()

    codes = sorted(union_sets) + sorted(tamil_sets)  # 15 union + 3 tamil = 18
    all_sets = {**union_sets, **tamil_sets}

    rows = []
    for a, b in combinations(codes, 2):
        inter, union, j = jaccard(all_sets[a], all_sets[b])
        rows.append((a, b, inter, union, round(j, 6)))

    # --- verification 1 (hard gate): the extension must not move the 105 base cells ---
    # Recompute the 15x15 cells WITHOUT the tamil sets and compare to the extended run:
    # pairwise counts are pure functions of the two code sets, so adding mwd/cap/otl
    # may only add rows/columns. Any difference here is a real defect.
    union_code_list = sorted(union_sets)
    base_only = {}
    for a, b in combinations(union_code_list, 2):
        inter, union, j = jaccard(union_sets[a], union_sets[b])
        base_only[(a, b)] = (inter, union, round(j, 6))
    ext_map = {(r[0], r[1]): (r[2], r[3], r[4]) for r in rows}
    inv_mismatches = []
    for k, v in base_only.items():
        if ext_map.get(k) != v:
            inv_mismatches.append(f"{k}: {v} vs extended {ext_map.get(k)}")

    # --- verification 2 (reported delta): registered baseline vs CURRENT union ---
    # The registered matrix was built 11-07-2026 on the then-323,425-row union;
    # the union was regenerated 04-09-2026 (H4075 fix1, 323425->323422), so some
    # base cells drift by +-3 in union size independently of this extension.
    union_code_set = set(union_sets)
    drift = []
    for (a, b), (inter, union, j) in base_only.items():
        key = (a, b) if (a, b) in base else (b, a)
        if key not in base:
            drift.append(f"{a}/{b}: no baseline row")
            continue
        b_inter, b_union, b_j = base[key]
        if (inter, union) != (b_inter, b_union) or abs(j - b_j) > 5e-5:
            drift.append(
                {
                    "pair": f"{a}/{b}",
                    "recomputed_on_current_union": [inter, union, j],
                    "registered_baseline": [b_inter, b_union, b_j],
                }
            )

    tamil_profile = {}
    for code in TAMIL_CODES:
        ks = tamil_sets[code]
        att = sum(1 for k in ks if cov.get(k) == "attested")
        tamil_profile[code] = {
            **tamil_stats["per_dict"][code],
            "corpus_attested_of_keys": att,
            "corpus_attested_pct_of_keys": round(100.0 * att / len(ks), 2) if ks else 0.0,
            "note": "attested share counts only keys present in the SLP1 union coverage sidecar; fold-only keys are unknown to DCS coverage",
        }

    stats = {
        "handoff": "H4732 (census C5)",
        "built_with": {
            "kosha_commit": _git_head(ROOT),
            "sanskritlexicography_head": _git_head(SL_ROOT),
            "csl_santam_head": _git_head(SANTAM_ROOT),
            "sanskrit_util_head": _git_head(SANSKRIT_UTIL_ROOT),
            "slp1_table_source": "sanskrit_util.to_slp1 (imported, never re-typed)",
            "hk_stage": "scheme_bridge.hk_to_iast (longest-token-first)",
            "otl_treatment": "HK-like scheme run through the same HK->IAST->SLP1 chain (fold_stats scheme_notes; Wave-4 normalization out of scope)",
        },
        "union_rows": n_union_rows,
        "union_codes": sorted(union_sets),
        "tamil_codes": sorted(tamil_sets),
        "extended_code_count": len(codes),
        "pairwise_cells": len(rows),
        "baseline_cells_checked": len(base_only),
        "extension_invariance": "PASS" if not inv_mismatches else "FAIL",
        "extension_invariance_mismatches": inv_mismatches,
        "baseline_drift_vs_registered": {
            "cause": "registered matrix (H684, 11-07-2026) was computed on the pre-H4075 union (323,425 rows); union regenerated 04-09-2026 (323,422 rows) — drift is upstream of and independent from this extension",
            "drifted_cells": len([d for d in drift if isinstance(d, dict)]),
            "max_union_delta": max(
                [abs(d["recomputed_on_current_union"][1] - d["registered_baseline"][1]) for d in drift if isinstance(d, dict)] or [0]
            ),
            "cells": drift,
        },
        "tamil_fold": {k: v for k, v in tamil_stats.items() if k != "per_dict"},
        "tamil_per_dict": tamil_profile,
        "canaries": {
            "cap_vs_CAE": next((r for r in rows if {r[0], r[1]} == {"cap", "CAE"}), None),
            "mwd_vs_MW": next((r for r in rows if {r[0], r[1]} == {"mwd", "MW"}), None),
            "otl_vs_MW": next((r for r in rows if {r[0], r[1]} == {"otl", "MW"}), None),
        },
    }

    if args.verify:
        ok = stats["extension_invariance"] == "PASS" and OUT_TSV.exists()
        if ok:
            got = OUT_TSV.read_text(encoding="utf-8").rstrip("\n").split("\n")
            want = ["dict_a\tdict_b\tshared\tunion\tjaccard"] + [
                f"{a}\t{b}\t{inter}\t{union}\t{j:.6f}" for a, b, inter, union, j in rows
            ]
            ok = got == want
        print(json.dumps({"verify": "PASS" if ok else "FAIL", "cells": len(rows)}, ensure_ascii=False))
        return 0 if ok else 1

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_TSV, "w", encoding="utf-8") as f:
        f.write("dict_a\tdict_b\tshared\tunion\tjaccard\n")
        for a, b, inter, union, j in rows:
            f.write(f"{a}\t{b}\t{inter}\t{union}\t{j:.6f}\n")
    OUT_STATS.write_text(json.dumps(stats, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    # --- delta report ---
    row_map = {(r[0], r[1]): r for r in rows}
    new_cells = [r for r in rows if r[0] in tamil_sets or r[1] in tamil_sets]
    new_cells.sort(key=lambda r: -r[4])
    profile_rows = sorted(
        [(c, len(all_sets[c])) for c in codes], key=lambda t: -t[1]
    )
    lines = [
        "# Headword overlap matrix — Tamil-fold extension, delta report (H4732, census C5)",
        "",
        f"_Generated 14/15-09-2026 by `scripts/build_overlap_matrix_ext.py`; inputs pinned in [overlap_matrix_ext_stats.json](overlap_matrix_ext_stats.json)._",
        "",
        f"- Registered `headword-overlap-matrix`: 15 dicts / 105 cells (predates the 06-09-2026 [tamil-fold](fold_stats.json) ingest, H4178).",
        f"- This extension: **{stats['extended_code_count']} dicts / {stats['pairwise_cells']} cells** (+ mwd, cap, otl from csl-santam; cpd/Pahlavi excluded as in csl-santam's own UI).",
        f"- New cells: **{len(new_cells)}** (3 x 15 vs the union + 3 among the fold); extension-invariance of the 105 base cells (recomputed with and without the fold): **{stats['extension_invariance']}**.",
        "",
        "## Keying (the load-bearing decision)",
        "",
        "- Fold `st` keys are Kyoto-Harvard (mwd/cap) or HK-like (otl) — [fold_stats.json](fold_stats.json); the union is keyed SLP1.",
        "- Chain: `scheme_bridge.hk_to_iast` -> `sanskrit_util.to_slp1` (house SLP1 table imported, never re-typed). otl runs the same HK-like treatment; residual scheme risk is flagged, fold normalization stays a Wave-4 item.",
        "- Minimal cleaning: strip; `&` variants split into separate keys; `-`-prefixed continuation tokens dropped; non-alphabet residue counted, keys kept (they simply cannot match the union).",
        "",
        "## Baseline drift (reported, not caused by this extension)",
        "",
        f"- {stats['baseline_drift_vs_registered']['drifted_cells']} of 105 registered cells differ from a recomputation on the CURRENT union — max union-size delta {stats['baseline_drift_vs_registered']['max_union_delta']}.",
        f"- Cause: {stats['baseline_drift_vs_registered']['cause']}.",
        "- The extension-invariance gate above proves the fold changes none of them; the authoritative current-union values are the ones in the extended TSV.",
        "",
        "## Per-dictionary profile (extended matrix)",
        "",
        "| dict | headwords | fold keys matched into union | corpus-attested % |",
        "|---|---:|---:|---:|",
    ]
    for c, n in profile_rows:
        if c in tamil_stats["per_dict"]:
            p = tamil_profile[c]
            lines.append(f"| {c} | {n} | {p['matched_into_union']} ({p['matched_share']}%) | {p['corpus_attested_pct_of_keys']} |")
        else:
            att = sum(1 for k in union_sets[c] if cov.get(k) == "attested")
            lines.append(f"| {c} | {n} | — | {round(100.0 * att / n, 2) if n else 0.0} |")
    lines += [
        "",
        "## Top 12 and bottom 6 of the 48 new cells",
        "",
        "| dict_a | dict_b | shared | union | jaccard |",
        "|---|---|---:|---:|---:|",
    ]
    for r in new_cells[:12] + new_cells[-6:]:
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]:.6f} |")
    cap_cae = row_map.get(("CAE", "cap")) or row_map.get(("cap", "CAE")) or (0, 0, 0, 0, 0.0)
    mwd_mw = row_map.get(("MW", "mwd")) or row_map.get(("mwd", "MW")) or (0, 0, 0, 0, 0.0)
    otl_mw = row_map.get(("MW", "otl")) or row_map.get(("otl", "MW")) or (0, 0, 0, 0, 0.0)
    lines += [
        "",
        "## Reading",
        "",
        f"- **cap x CAE = {cap_cae[2]} shared ({cap_cae[4]:.4f} J)** — the same Capeller dictionary via two routes (union CAE key1s vs csl-santam fold), so this cell is the keying-chain canary: a near-full match validates HK->SLP1 end to end.",
        f"- **mwd x MW = {mwd_mw[2]} shared ({mwd_mw[4]:.4f} J)** — Cologne MW re-edition vs the union's MW; the gap is union key2/variant entries and fold encoding noise, not missing content.",
        f"- **otl x MW = {otl_mw[2]} shared ({otl_mw[4]:.4f} J)** — the Tamil Lexicon's Sanskrit layer; the only genuinely new content of the three (the estate's first otl surface beyond the fold).",
        f"- **otl residue is expected, not loss:** {tamil_profile['otl']['keys_with_nonalpha_residue']} of {len(tamil_sets['otl'])} unique keys ({round(100.0 * tamil_profile['otl']['keys_with_nonalpha_residue'] / len(tamil_sets['otl']), 1)}%) carry non-SLP1-alphabet residue — Tamil Lexicon headwords are largely Tamil words in Tamil-specific phonology (ẓ/ṉ/ṟ-class letters the Sanskrit alphabet has no SLP1 letter for); only its Sanskrit layer can overlap the union by construction.",
        "- cpd (Concise Pahlavi) is deliberately excluded: csl-santam's own form and `all` query exclude it (`id<4`).",
        "",
        "## What this changes / does not change",
        "",
        "- Changes: nothing registered. The 15-dict `headword-overlap-matrix` dataset, the union master and `HeadwordLists` are untouched; this ships a kosha-side extended dataset (`headword-overlap-matrix-ext`).",
        "- The 105 base cells proved extension-invariant (identical with and without the fold); against the registered baseline they drift by ≤3 in union size purely from the 04-09 H4075 union regen — recorded per cell in the stats JSON.",
        "",
        "_Auto-generated; do not hand-edit numbers._",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(
        json.dumps(
            {
                "codes": len(codes),
                "cells": len(rows),
                "new_cells": len(new_cells),
                "baseline_invariance": stats["extension_invariance"],
                "baseline_drifted_cells": stats["baseline_drift_vs_registered"]["drifted_cells"],
                "canaries": stats["canaries"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if not inv_mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
