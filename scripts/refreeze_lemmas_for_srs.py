#!/usr/bin/env python3
"""H5399 — re-derive the lemmas_for_srs.tsv pin from the ALREADY-COMMITTED pins.

Why not just run `freeze_cohort_start_chteniya.py`: a full builder re-run also
re-pins the sandhi assets from sources that have moved since the 2026-08-01
freeze, and it rewrites MANIFEST.json from scratch, dropping the H2129
`manifest_fix` and H5398 `gloss_fix` provenance notes. Same reasoning, and the
same graft shape, as the H5398 re-pin.

So: read the two committed pins, rebuild the derived TSV with the H5399-fixed
gloss reader (`lemma_rows`), and graft ONLY the `lemmas-for-srs` row's
sha256/bytes/built_source/gloss_ru_coverage/stats into the committed manifest.
The other four pin rows and every note field are left byte-identical.

    python scripts/refreeze_lemmas_for_srs.py            # rebuild + graft
    python scripts/refreeze_lemmas_for_srs.py --dry-run  # report only
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from freeze_cohort_start_chteniya import (  # noqa: E402
    OUT,
    lemma_rows,
    sha256_file,
    write_json,
    write_lemma_tsv,
)

MANIFEST = OUT / "MANIFEST.json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="report the coverage delta, write nothing")
    args = ap.parse_args()

    hito = json.loads((OUT / "hitopadesa-0.json").read_text(encoding="utf-8"))
    sub = json.loads((OUT / "subhashita_beginner_pack.json").read_text(encoding="utf-8"))
    rows = lemma_rows(hito, sub)

    lemma_path = OUT / "lemmas_for_srs.tsv"
    before_lines = lemma_path.read_text(encoding="utf-8").splitlines()[1:]
    before_glossed = sum(1 for ln in before_lines if ln.split("\t")[3].strip())

    glossed = sum(1 for r in rows if r["gloss_ru"])
    by_pack = {}
    for r in rows:
        slot = by_pack.setdefault(r["pack"], [0, 0])
        slot[0] += 1
        slot[1] += 1 if r["gloss_ru"] else 0

    print("rows %d (was %d)" % (len(rows), len(before_lines)))
    print("gloss_ru present %d -> %d" % (before_glossed, glossed))
    for pack in sorted(by_pack):
        total, has = by_pack[pack]
        print("  %-20s %4d/%4d (%.1f%%)" % (pack, has, total, 100.0 * has / total))

    if args.dry_run:
        return 0

    write_lemma_tsv(lemma_path, rows)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hit = None
    for pack in manifest["packs"]:
        if pack["slug"] == "lemmas-for-srs":
            hit = pack
            break
    if hit is None:
        raise SystemExit("MANIFEST.json has no lemmas-for-srs pack row")

    hit["sha256"] = sha256_file(lemma_path)
    hit["bytes"] = lemma_path.stat().st_size
    hit["built_source"] = date.today().isoformat()
    hit["gloss_ru_coverage"] = "%d/%d rows have gloss_ru" % (glossed, len(rows))
    hit["stats"] = {
        "unique_lemmas": len(rows),
        "hitopadesa_0": by_pack.get("hitopadesa-0", [0, 0])[0],
        "subhashita_beginner": by_pack.get("subhashita-beginner", [0, 0])[0],
    }
    write_json(MANIFEST, manifest)

    print("\ngrafted lemmas-for-srs: sha256=%s bytes=%d" % (hit["sha256"][:16], hit["bytes"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
