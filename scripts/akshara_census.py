#!/usr/bin/env python3
"""H3597 step 1 - FULL kosha census: freeze the complete akshara.ru head
inventory from the site's own sitemap index (the cheap enumeration path).

The sitemaps enumerate /kosha/w/<slp1> URLs - the site's own declared head set
(51,663 locs as of 27-08-2026: sitemap-kosha-001 40,000 + -002 11,663). The
census manifest freezes it BEFORE the first card fetch and anchors the coverage
report. Card fetches themselves use the H3455 /kosha?q= contract (see
akshara_full_crawl.py).

Sitemap URLs /kosha/w/<head> (no query string) are robots-allowed for
User-agent: * - the Disallow pattern /kosha/w/*? matches only query-string
forms, which are never requested here.

Usage:
  python scripts/akshara_census.py            # download + freeze census
  python scripts/akshara_census.py --check    # verify frozen manifest intact
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "akshara_full"
MANIFEST = OUT_DIR / "head_manifest.jsonl"
CENSUS = OUT_DIR / "census.json"

SITEMAPS = (
    "https://akshara.ru/sitemap-kosha-001.xml",
    "https://akshara.ru/sitemap-kosha-002.xml",
)
LOC_RE = re.compile(r"<loc>\s*(https://akshara\.ru/kosha/w/([^<<?]+))\s*</loc>")
HEAD_PATH_RE = re.compile(r"^[A-Za-z0-9_.~+-]+$")

UA = "kosha-research-bot/0.2 (kosha full census H3597; contact: hello@samskrtam.ru)"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def parse_sitemap(body: bytes) -> list[str]:
    text = body.decode("utf-8")
    heads = []
    for _loc, head in LOC_RE.findall(text):
        head = head.strip()
        if HEAD_PATH_RE.match(head):
            heads.append(head)
    return heads


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify frozen census only")
    args = ap.parse_args()

    if args.check:
        rows = [json.loads(l) for l in open(MANIFEST, encoding="utf-8")]
        c = json.load(open(CENSUS, encoding="utf-8"))
        heads = [r["slp1"] for r in rows]
        assert len(heads) == len(set(heads)) == c["heads"], "manifest/census drift"
        print(f"census check OK: {c['heads']} heads, frozen {c['frozen_ts']}")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen: dict[str, str] = {}
    src_stats = []
    for url in SITEMAPS:
        body = fetch(url)
        heads = parse_sitemap(body)
        src_stats.append({
            "url": url, "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body), "locs": heads and len(heads),
        })
        for h in heads:
            seen.setdefault(h, url)
        print(f"{url.rsplit('/', 1)[-1]}: {len(heads)} locs, "
              f"cumulative unique {len(seen)}", flush=True)

    rows = sorted(seen)
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        for h in rows:
            f.write(json.dumps({"slp1": h}, ensure_ascii=False) + "\n")

    census = {
        "heads": len(rows),
        "frozen_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": src_stats,
        "method": "site's own sitemap-kosha-001/002.xml /kosha/w/<slp1> index "
                  "(robots-allowed, no query strings); card fetches later use the "
                  "H3455 /kosha?q= contract with the same URL guard",
        "handoff": "H3597",
    }
    CENSUS.write_text(json.dumps(census, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"CENSUS FROZEN: {len(rows)} unique heads -> {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
