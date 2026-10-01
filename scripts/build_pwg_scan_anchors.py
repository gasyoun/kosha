"""build_pwg_scan_anchors.py — PWG entry L → print (volume, column) anchor table (H3457).

Why this exists: kosha's scan resolver (src/kosha/scan_resolver.py, H839) proved
that Cologne's servepdf.php for PWG honours ONLY the "{vol}-{col:04d}" page key —
a bare column number silently serves volume 1. The committed static cards under
docs/cards/ predate that fix: every PWG `scan_url` there is bare-page (48,540 of
them at 25-08-2026), so e.g. `gam` (L 119742, printed at 7-1737) links to volume
1 column 1737. The cards cannot be regenerated without kosha.db, and the static
site must stay DB-free, so this script derives the missing (vol, col) per PWG
`L` straight from the Cologne source and commits it as a small TSV the word-page
template overlays at render time.

Source: csl-orig v02/pwg/pwg.txt — the `<L>{L}<pc>{vol}-{col}<k1>…` header line
of every entry (PWG's own "vol-Spalte" page/column key, exactly the key Cologne's
pdffiles.txt uses).

Output: data/pwg_scan/pwg_L_pc.tsv  (L, vol, col) — one row per entry, sorted by L.

Usage:
    python scripts/build_pwg_scan_anchors.py                       # ../csl-orig default
    python scripts/build_pwg_scan_anchors.py --pwg path/to/pwg.txt
"""
import argparse
import csv
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "pwg_scan" / "pwg_L_pc.tsv"
DEFAULT_PWG = ROOT.parent / "csl-orig" / "v02" / "pwg" / "pwg.txt"

HEAD_RE = re.compile(r"^<L>(\d+)<pc>(\d+)-(\d+)<k1>")


def parse_pwg(path):
    rows, bad = [], 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.startswith("<L>"):
                continue
            m = HEAD_RE.match(line)
            if not m:
                bad += 1
                continue
            rows.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    rows.sort()
    return rows, bad


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pwg", type=Path, default=DEFAULT_PWG)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    if not args.pwg.exists():
        sys.exit(f"error: {args.pwg} not found (clone sanskrit-lexicon/csl-orig next to kosha)")
    rows, bad = parse_pwg(args.pwg)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["L", "vol", "col"])
        for L, vol, col in rows:
            w.writerow([L, vol, col])
    vols = sorted({v for _, v, _ in rows})
    print(f"[pwg-scan-anchors] {len(rows)} entries -> {args.out} "
          f"(volumes {vols[0]}..{vols[-1]}, {bad} header lines without a parsable <pc>)")
    per_vol = {}
    for _, v, _ in rows:
        per_vol[v] = per_vol.get(v, 0) + 1
    print("[pwg-scan-anchors] per-volume: " + ", ".join(f"vol{v}={n}" for v, n in sorted(per_vol.items())))


if __name__ == "__main__":
    main()
