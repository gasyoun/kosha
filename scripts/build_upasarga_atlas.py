#!/usr/bin/env python
"""H4729 — Unified upasarga atlas: workbook decomposition x Gita semantics x class frequencies.

Census C2 join of three registered datasets into one upasarga dataset
(`data/upasarga/upasarga_atlas.tsv`):

1. `dcs-upasarga-prefixus`  (kosha `data/upasarga/dcs_upasarga_prefixus.tsv`, H4534)
   — DCS prefixed-verb decomposition, MG 2014 workbook, 6,425 rows. Keyed on the
   RESOLVED `prefix` column only (5,059 rows); the naive `prefix_guess` column
   (38 rows, demonstrably wrong where it disagrees, e.g. `abhigā` → guess
   `prati`, resolved `abhi`) never keys the atlas. 1,350 unresolved-prefix rows
   contribute root-level `(dhatu, '')` keys.
2. `sanskrit-upasarga-semantics` (kosha `data/gita/upasarga_semantics.tsv`, H876 W6)
   — Gita root x preverb senses, 214 rows. Root `√`-prefix stripped on join;
   `preverb` kept verbatim (comma-lists like `abhi-,pra-,vi-` are alternative
   readings and are NOT exploded — this reproduces the H4477 census join exactly:
   69 gita (root, preverb) keys, 34 shared with the prefixus side).
3. `dcs-verb-class-prefix-frequency` (VisualDCS
   `derived-data/Glagolnye-formy/Klassy/Spisok-form-s-prefiksami-8444/Cl_Frq/1..10.csv`)
   — per-class `root;count` verb-form frequencies. Root-level only (no preverb
   dimension); bare-number lines without `;` (one per file — the class's unkeyed
   total) are excluded from the join and reported.

Key normalization (all three sides → bare root + hyphen-terminated preverb):
  prefixus  (dhatu, prefix)            -> (dhatu, prefix + '-')
  gita      (√root, preverb)           -> (root, preverb)          # verbatim preverb
  classfreq (root, class file)         -> (root, '')               # aggregated 1:cnt|...

Output columns:
  root  preverb  sense  gita_count  prefixus_forms  prefixus_sample_form
  class_freqs  sources

`sources` is a sorted `+`-join of {classfreq, prefixus, semantics}. Sorted by
(root, preverb) — deterministic, byte-identical on rerun.

Usage:
  python scripts/build_upasarga_atlas.py [--classdir <Cl_Frq dir>]
  python scripts/build_upasarga_atlas.py --verify   # re-read emitted TSV + cross-check

Licence: CC BY-SA 4.0, credit Dr. Mārcis Gasūns (mirrors the three sources).
"""
import argparse
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
PREFIXUS = ROOT / "data" / "upasarga" / "dcs_upasarga_prefixus.tsv"
GITA = ROOT / "data" / "gita" / "upasarga_semantics.tsv"
ATLAS = ROOT / "data" / "upasarga" / "upasarga_atlas.tsv"
DEFAULT_CLASSDIR = (ROOT.parent / "VisualDCS" / "derived-data" / "Glagolnye-formy"
                    / "Klassy" / "Spisok-form-s-prefiksami-8444" / "Cl_Frq")

HEADER = ["root", "preverb", "sense", "gita_count", "prefixus_forms",
          "prefixus_sample_form", "class_freqs", "sources"]


def load_prefixus():
    """(root, preverb) -> {forms, sample}; plus bare-dhatu set for parity stats."""
    keys = {}
    with open(PREFIXUS, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            d = r["dhatu"].strip()
            p = r["prefix"].strip()
            k = (d, p + "-") if p else (d, "")
            e = keys.get(k)
            if e is None:
                keys[k] = {"forms": 1, "sample": r["in_form"].strip()}
            else:
                e["forms"] += 1
                if r["in_form"].strip() < e["sample"]:
                    e["sample"] = r["in_form"].strip()
    return keys


def load_gita():
    """(root, preverb) -> {sense, count}; root-level (empty preverb) included."""
    keys, dup = {}, []
    with open(GITA, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rt = r["root"].strip()
            if rt.startswith("√"):
                rt = rt[1:]
            k = (rt, r["preverb"].strip())
            if k in keys:
                dup.append(k)
                continue
            keys[k] = {"sense": r["sense"].strip(), "count": r["count"].strip()}
    return keys, dup


def load_classfreq(classdir):
    """root -> {class: count}; skips unkeyed bare-number total lines (reported)."""
    freq, skipped = {}, []
    for fp in sorted(classdir.glob("*.csv")):
        cls = fp.stem
        with open(fp, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                if ";" not in line:
                    skipped.append((cls, line))
                    continue
                rt, c = line.split(";", 1)
                rt = rt.strip()
                freq.setdefault(rt, {})[cls] = freq.get(rt, {}).get(cls, 0) + int(c)
    return freq, skipped


def fmt_classfreq(perclass):
    if not perclass:
        return ""
    return "|".join(f"{c}:{perclass[c]}" for c in sorted(perclass, key=int) if perclass[c])


def build(classdir):
    pfx = load_prefixus()
    gita, gita_dups = load_gita()
    freq, skipped = load_classfreq(classdir)

    universe = set(pfx) | set(gita) | {(rt, "") for rt in freq}
    rows = []
    for (rt, pv) in sorted(universe):
        p = pfx.get((rt, pv))
        g = gita.get((rt, pv))
        # class frequencies attach to the ROOT-level row only (dataset has no preverb dim)
        cf = fmt_classfreq(freq.get(rt, {})) if pv == "" else ""
        sources = []
        if p:
            sources.append("prefixus")
        if g:
            sources.append("semantics")
        if (rt, "") in universe and pv == "" and rt in freq:
            sources.append("classfreq")
        rows.append({
            "root": rt,
            "preverb": pv,
            "sense": g["sense"] if g else "",
            "gita_count": g["count"] if g else "",
            "prefixus_forms": str(p["forms"]) if p else "",
            "prefixus_sample_form": p["sample"] if p else "",
            "class_freqs": cf,
            "sources": "+".join(sources),
        })

    with open(ATLAS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    shared = set(pfx) & set(gita)
    shared_nonempty = {k for k in shared if k[1]}
    stats = {
        "rows": len(rows),
        "prefixus_keys": len(pfx),
        "prefixus_resolved_rows": sum(v["forms"] for k, v in pfx.items() if k[1]),
        "prefixus_unresolved_rows": sum(v["forms"] for k, v in pfx.items() if not k[1]),
        "gita_keys": len(gita),
        "gita_preverb_keys": sum(1 for k in gita if k[1]),
        "gita_dup_keys": gita_dups,
        "classfreq_roots": len(freq),
        "classfreq_skipped_total_lines": skipped,
        "classfreq_dhatu_match": len({rt for rt, _ in pfx} & set(freq)),
        "classfreq_gita_match": len({rt for rt, _ in gita} & set(freq)),
        "shared_keys_all": len(shared),
        "shared_keys_nonempty_preverb": len(shared_nonempty),
    }
    return rows, stats


def verify(classdir):
    """Re-read the emitted TSV and cross-check against a fresh recompute. Exit 1 on mismatch."""
    pfx = load_prefixus()
    gita, _ = load_gita()
    freq, _ = load_classfreq(classdir)
    with open(ATLAS, encoding="utf-8") as f:
        back = list(csv.DictReader(f, delimiter="\t"))
    errs = []

    universe = set(pfx) | set(gita) | {(rt, "") for rt in freq}
    if len(back) != len(universe):
        errs.append(f"row count {len(back)} != expected union {len(universe)}")
    back_keys = {(r["root"], r["preverb"]) for r in back}
    if back_keys != universe:
        errs.append("key set mismatch vs recomputed union")

    # H4477 anchor: 34 shared (root, preverb) keys between prefixus and gita semantics
    shared = {k for k in set(pfx) & set(gita) if k[1]}
    if len(shared) != 34:
        errs.append(f"shared nonempty-preverb keys {len(shared)} != H4477 anchor 34")

    # root/preverb key parity on a deterministic sample of shared keys
    sample = sorted(shared)[:5]
    by_key = {(r["root"], r["preverb"]): r for r in back}
    print("key-parity sample (shared prefixus x semantics keys):")
    for k in sample:
        r = by_key.get(k)
        p = pfx[k]
        g = gita[k]
        ok = r and r["sense"] == g["sense"] and int(r["prefixus_forms"]) == p["forms"]
        print(f"  {'PASS' if ok else 'FAIL'}  √{k[0]} + {k[1]}  sense='{g['sense']}'"
              f"  gita_count='{g['count']}'  prefixus_forms={p['forms']}"
              f"  sample_form='{p['sample']}'")
        if not ok:
            errs.append(f"parity sample FAIL on {k}")

    # class-freq round-trip on root-level rows
    mism = 0
    for rt, perclass in freq.items():
        got = by_key[(rt, "")]["class_freqs"] if (rt, "") in by_key else None
        if got != fmt_classfreq(perclass):
            mism += 1
    if mism:
        errs.append(f"class_freqs round-trip mismatches: {mism}")

    if errs:
        for e in errs:
            print("VERIFY FAIL:", e)
        sys.exit(1)
    print(f"VERIFY PASS — {len(back)} rows; {len(shared)} shared keys (H4477 anchor 34);"
          f" classfreq round-trip clean")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classdir", default=str(DEFAULT_CLASSDIR),
                    help=f"VisualDCS Cl_Frq dir (default: {DEFAULT_CLASSDIR})")
    ap.add_argument("--verify", action="store_true",
                    help="re-read the emitted atlas TSV and cross-check (exit 1 on mismatch)")
    args = ap.parse_args()
    classdir = Path(args.classdir)
    if not classdir.is_dir():
        sys.exit(f"Cl_Frq dir not found: {classdir} — pass --classdir")

    if args.verify:
        verify(classdir)
        return

    rows, st = build(classdir)
    print(f"atlas written: {ATLAS.relative_to(ROOT)} — {st['rows']} data rows")
    print(f"  prefixus keys: {st['prefixus_keys']} "
          f"(resolved rows {st['prefixus_resolved_rows']}, unresolved {st['prefixus_unresolved_rows']})")
    print(f"  gita keys: {st['gita_keys']} (with preverb {st['gita_preverb_keys']})"
          + (f"  DUP KEYS: {st['gita_dup_keys']}" if st['gita_dup_keys'] else ""))
    print(f"  classfreq roots: {st['classfreq_roots']}"
          f"  (dhatu-side match {st['classfreq_dhatu_match']},"
          f" gita-root-side match {st['classfreq_gita_match']})")
    if st["classfreq_skipped_total_lines"]:
        print(f"  skipped unkeyed total lines: {len(st['classfreq_skipped_total_lines'])}"
              f" {st['classfreq_skipped_total_lines']}")
    print(f"  shared keys: all {st['shared_keys_all']}, nonempty-preverb"
          f" {st['shared_keys_nonempty_preverb']} (H4477 anchor: 34)")
    print("sources breakdown:", end=" ")
    from collections import Counter
    for srcs, n in Counter(r["sources"] for r in rows).most_common():
        print(f"{srcs or 'NONE'}={n}", end="  ")
    print()


if __name__ == "__main__":
    main()
