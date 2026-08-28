#!/usr/bin/env python3
"""H3597 repair pass - re-fetch case-twin keys corrupted by the filename collision.

Incident (28-08-2026): the crawler originally stored raw cards as flat
<safe>.html names; NTFS is case-insensitive while the akshara census contains
case twins that the site serves as DIFFERENT cards (dvipAd != dvipad). Each
twin pair therefore shared one physical file - the second fetch overwrote the
first - and the 28-08 parse+delete run consolidated the corruption: one row
per pair (possibly holding the twin's card) and no row for the other twin.

Repair:
  1. build data/akshara_full/head_manifest_repair.jsonl - every census key
     that case-matches another census key AND was crawled under the old flat
     scheme (both members, regardless of which side survived);
  2. run the normal crawler over it (--manifest/--log overrides, hashed
     collision-proof filenames, same 2 polite streams, resume from repair log);
  3. purge the tainted corpus rows (both members of every affected pair);
  4. parse the repair log into the corpus with the fixed parser.

Usage:
  python scripts/akshara_repair_twins.py --build      # step 1 only
  python scripts/akshara_repair_twins.py --status     # how much is left
  python scripts/akshara_repair_twins.py --purge      # step 3 (after repair crawl)

Full repair sequence (run when pass 1 prints DONE):
  python scripts/akshara_repair_twins.py --build
  python scripts/akshara_full_crawl.py --manifest data/akshara_full/head_manifest_repair.jsonl --log data/akshara_full/crawl_manifest_repair.jsonl
  python scripts/akshara_repair_twins.py --purge
  python scripts/akshara_full_parse.py --log data/akshara_full/crawl_manifest_repair.jsonl --delete-raw
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "akshara_full"
CENSUS = DATA / "head_manifest.jsonl"
CRAWL_LOG = DATA / "crawl_manifest.jsonl"
REPAIR_MANIFEST = DATA / "head_manifest_repair.jsonl"


def crawled_keys() -> set[str]:
    out: set[str] = set()
    if CRAWL_LOG.exists():
        for line in open(CRAWL_LOG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("http") == 200 and "|" not in r["slp1"]:
                out.add(r["slp1"])
    return out


def twin_keys_crawled() -> list[str]:
    heads = [json.loads(l)["slp1"] for l in open(CENSUS, encoding="utf-8")]
    groups: dict[str, list[str]] = defaultdict(list)
    for h in heads:
        groups[h.casefold()].append(h)
    crawled = crawled_keys()
    out: set[str] = set()
    for members in groups.values():
        if len(members) > 1 and any(m in crawled for m in members):
            out.update(m for m in members if m in crawled)
    return sorted(out)


def corpus_keys() -> set[str]:
    corpus = DATA / "parsed_corpus.jsonl"
    out: set[str] = set()
    if corpus.exists():
        for line in open(corpus, encoding="utf-8"):
            out.add(json.loads(line)["slp1"])
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--purge", action="store_true",
                    help="drop every corpus row whose slp1 is in the repair "
                         "manifest (tainted or twin-of-tainted); the repair "
                         "parse re-adds them from clean raws")
    args = ap.parse_args()

    if args.build:
        keys = twin_keys_crawled()
        with open(REPAIR_MANIFEST, "w", encoding="utf-8", newline="\n") as f:
            for k in keys:
                f.write(json.dumps({"slp1": k}, ensure_ascii=False) + "\n")
        print(f"repair manifest FROZEN: {len(keys)} keys -> {REPAIR_MANIFEST.name}")
        return 0

    if args.purge:
        if not REPAIR_MANIFEST.exists():
            print("repair manifest missing - run --build first")
            return 1
        repair = {json.loads(l)["slp1"]
                  for l in open(REPAIR_MANIFEST, encoding="utf-8")}
        corpus = DATA / "parsed_corpus.jsonl"
        kept = dropped = 0
        kept_rows = []
        for line in open(corpus, encoding="utf-8"):
            if json.loads(line)["slp1"] in repair:
                dropped += 1
            else:
                kept += 1
                kept_rows.append(line)
        tmp = corpus.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.writelines(kept_rows)
        tmp.replace(corpus)
        print(f"purged {dropped} tainted rows, kept {kept}")
        return 0

    if args.status:
        todo = twin_keys_crawled()
        parsed = corpus_keys()
        have_row = [k for k in todo if k in parsed]
        print(f"twin keys crawled so far : {len(todo)}")
        print(f"  with a (possibly tainted) corpus row : {len(have_row)}")
        print(f"  without any corpus row               : {len(todo) - len(have_row)}")
        if REPAIR_MANIFEST.exists():
            print("repair manifest exists: run the crawler over it, then purge+reparse")
        else:
            print("repair manifest not built yet: run with --build")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
