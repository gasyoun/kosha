#!/usr/bin/env python3
"""H3455 lane A step 3 - parse crawled akshara.ru card HTML into the restricted
benchmark corpus.

Input : data/raw_akshara_pilot/<safe>.html            (dict=all originals)
        data/raw_akshara_pilot/<safe>.<dict>_ru.html  (MT variants, pass 2)
Output: data/akshara_pilot/parsed_corpus.jsonl        (RESTRICTED tier)
        one row per headword:
          {slp1, stratum, originals:{mw,pwg,mac,likh,apte},
           mt:{mw_ru,apte_ru,pwg_ru}, provenance:{part:sha256}}

Markup contract (site v20260820-v3.7-rc3): each dictionary block is
  <article class="dict-entry" data-dict="<code>"> ... </article>
Articles do not nest. Absent dictionaries / absent MT pages are recorded as null.

Usage:
  python scripts/akshara_pilot_parse.py [--selftest]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw_akshara_pilot"
OUT = ROOT / "data" / "akshara_pilot" / "parsed_corpus.jsonl"
MANIFEST = ROOT / "data" / "akshara_pilot" / "sample_manifest.jsonl"

ARTICLE_RE = re.compile(
    r'<article class="dict-entry" data-dict="([a-z_]+)"[^>]*>(.*?)</article>',
    re.DOTALL,
)
STRIP_RE = re.compile(r"<(script|style|noscript)\b.*?</\1>", re.DOTALL)

ORIG_DICTS = ("likh", "mw", "apte", "mac", "pwg")
MT_DICTS = ("mw_ru", "apte_ru", "pwg_ru")


def safe_name(slp1: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.~-]", "_", slp1)[:80] or "_"


def extract_articles(html: str) -> dict[str, str]:
    """data-dict code -> cleaned inner HTML fragment."""
    out: dict[str, str] = {}
    for code, inner in ARTICLE_RE.findall(STRIP_RE.sub("", html)):
        frag = inner.strip()
        if frag:
            out[code] = frag
    return out


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def parse_one(slp1: str) -> dict:
    safe = safe_name(slp1)
    row: dict = {"slp1": slp1, "originals": {}, "mt": {}, "provenance": {}}

    p_all = RAW_DIR / f"{safe}.html"
    if p_all.exists():
        body = p_all.read_bytes()
        row["provenance"]["all"] = sha(body)
        for code, frag in extract_articles(body.decode("utf-8", "replace")).items():
            if code in ORIG_DICTS:
                row["originals"][code] = frag

    for d in MT_DICTS:
        p = RAW_DIR / f"{safe}.{d}.html"
        if not p.exists():
            continue
        body = p.read_bytes()
        row["provenance"][d] = sha(body)
        arts = extract_articles(body.decode("utf-8", "replace"))
        # MT page carries exactly its own dict block; keep it whole.
        if d in arts:
            row["mt"][d] = arts[d]
    return row


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(MANIFEST, encoding="utf-8")]

    if args.selftest:
        # AmarSa was smoke-fetched in pass 1; assert mw article extraction works.
        probe = parse_one("AmarSa")
        assert "mw" in probe["originals"], f"mw missing: {list(probe['originals'])}"
        assert "ग" in probe["originals"]["mw"] or "<" in probe["originals"]["mw"]
        print(f"selftest OK on AmarSa: originals={sorted(probe['originals'])}")
        return 0

    n = have_all = have_any_mt = 0
    fails: list[str] = []
    counts = {d: 0 for d in ORIG_DICTS}
    mt_counts = {d: 0 for d in MT_DICTS}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            slp1 = r["slp1"]
            parsed = parse_one(slp1)
            parsed["stratum"] = r["stratum"]
            if not parsed["originals"] and not parsed["mt"]:
                fails.append(slp1)
                parsed["parse_error"] = "no articles extracted"
            else:
                n += 1
                if all(d in parsed["originals"] for d in ("mw", "pwg")):
                    have_all += 1
                if parsed["mt"]:
                    have_any_mt += 1
                for d in parsed["originals"]:
                    counts[d] += 1
                for d in parsed["mt"]:
                    mt_counts[d] += 1
            f.write(json.dumps(parsed, ensure_ascii=False) + "\n")

    report = {
        "rows": len(rows), "parsed_ok": n, "parse_failures": len(fails),
        "orig_counts": counts, "mt_counts": mt_counts,
        "have_mw_and_pwg": have_all, "have_any_mt": have_any_mt,
        "fail_examples": fails[:10],
    }
    out_rep = OUT.parent / "parse_report.json"
    out_rep.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
