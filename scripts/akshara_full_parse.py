#!/usr/bin/env python3
"""H3597 - incremental parse + optional raw-HTML reclaim for the FULL kosha crawl.

Wisdomlib-shaped storage (MG ask 28-08-2026): the RESTRICTED corpus lives as
parsed JSONL, the raw card HTML is reclaimed once its parsed row is durably
appended. The crawler itself never reads raws, so parse+delete can run while
the crawl continues.

Inputs  (crawl log, records with http==200 only):
  data/akshara_full/crawl_manifest.jsonl      pass 1 keys: plain slp1
  data/akshara_full/crawl_manifest_ru.jsonl   pass 2 keys: slp1|dict

Outputs (gitignored, RESTRICTED):
  data/akshara_full/parsed_corpus.jsonl       one row per head (originals)
  data/akshara_full/parsed_corpus_ru.jsonl    one row per head|dict (MT)

Safety: a raw file is deleted ONLY after its parsed row has been appended and
flushed for that exact key; --delete-raw also reclaims files whose key was
parsed by a previous run. Crash between append and delete just leaves the
file for the next run. Nothing is ever deleted without a parsed row.

Usage:
  python scripts/akshara_full_parse.py                        # pass 1 backlog
  python scripts/akshara_full_parse.py --pass ru              # pass 2 backlog
  python scripts/akshara_full_parse.py --delete-raw           # parse + reclaim
  python scripts/akshara_full_parse.py --selftest
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from akshara_pilot_parse import extract_articles  # noqa: E402  (reuse, not fork)
from akshara_pilot_parse import MT_DICTS, safe_name  # noqa: E402
from akshara_full_crawl import raw_filename  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw_akshara_full"
CRAWL_LOG = ROOT / "data" / "akshara_full" / "crawl_manifest.jsonl"
CRAWL_LOG_RU = ROOT / "data" / "akshara_full" / "crawl_manifest_ru.jsonl"
CORPUS = ROOT / "data" / "akshara_full" / "parsed_corpus.jsonl"
CORPUS_RU = ROOT / "data" / "akshara_full" / "parsed_corpus_ru.jsonl"

Q_SLP1_RE = re.compile(r'data-q-slp1="([^"]+)"')


def raw_path_for(key: str, which: str) -> Path:
    """Current scheme: hashed collision-proof names. Legacy fallback: the
    flat pre-incident names (non-twin keys parsed from them are trustworthy;
    twin keys must come from the repair pass instead)."""
    hashed = RAW_DIR / raw_filename(key)
    if hashed.exists():
        return hashed
    slp1, _, dictpart = key.partition("|")
    safe = safe_name(slp1)
    flat = RAW_DIR / f"{safe}.html" if which == "all" \
        else RAW_DIR / f"{safe}.{dictpart}.html"
    return flat


def ok_keys(log: Path) -> list[str]:
    out = []
    if log.exists():
        with open(log, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r.get("http") == 200:
                    out.append(r["slp1"])
    return out


def parsed_keys(path: Path) -> set[str]:
    done: set[str] = set()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                done.add(json.loads(line)["slp1"])
    return done


def parse_file(path: Path) -> tuple[dict[str, str], str]:
    """(articles, q_slp1-or-'') for one stored card."""
    arts = extract_articles(path.read_bytes().decode("utf-8", "replace"))
    m = Q_SLP1_RE.search(path.read_bytes().decode("utf-8", "replace"))
    return arts, (m.group(1) if m else "")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass", dest="which", choices=["all", "ru"], default="all")
    ap.add_argument("--delete-raw", action="store_true",
                    help="reclaim raw HTML after its parsed row is appended")
    ap.add_argument("--log", dest="log_override", default="",
                    help="alternate crawl log to parse (repair passes)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        import tempfile
        html = (b'<article class="dict-entry" data-dict="mw">x</article>'
                b'<article class="dict-entry" data-dict="pwg">y</article>'
                b'<body data-q-slp1="a">')
        tmp = Path(tempfile.mkdtemp()) / "probe.html"
        tmp.write_bytes(html)
        arts, q = parse_file(tmp)
        # the akshara site case-normalizes missing keys (q=A served the `a`
        # card); q_slp1 preserves the served head for drain classification.
        assert arts == {"mw": "x", "pwg": "y"} and q == "a", (arts, q)
        print(f"selftest OK: arts={arts} q_slp1={q!r}")
        tmp.unlink()
        return 0

    if args.which == "all":
        log = (ROOT / args.log_override) if args.log_override else CRAWL_LOG
        out = CORPUS
        raw_of = lambda k: raw_path_for(k, "all")  # noqa: E731
    else:
        log = (ROOT / args.log_override) if args.log_override else CRAWL_LOG_RU
        out = CORPUS_RU

        def raw_of(key: str) -> Path:  # noqa: E306 - closure over the pass
            return raw_path_for(key, "ru")

    keys = ok_keys(log)
    done = parsed_keys(out)
    todo = [k for k in keys if k not in done]
    reclaim = []
    if args.delete_raw:
        reclaim = [raw_of(k) for k in done if raw_of(k).exists()]

    freed = 0
    deleted = 0
    new_parses = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", encoding="utf-8", newline="\n") as corpus:
        for key in todo:
            path = raw_of(key)
            if not path.exists():
                continue  # not crawled yet in this pass; next run catches it
            arts, q_slp1 = parse_file(path)
            if args.which == "all":
                row = {"slp1": key, "originals": arts, "q_slp1": q_slp1}
                if not arts:
                    row["honest_miss"] = True  # zero-article «Не найдено» page
            else:
                slp1, _, d = key.partition("|")
                assert d in MT_DICTS
                row = {"slp1": key, "dict": d,
                       "mt": {d: arts[d]} if d in arts else {},
                       "q_slp1": q_slp1}
                if d not in arts:
                    row["honest_miss"] = True
            corpus.write(json.dumps(row, ensure_ascii=False) + "\n")
            corpus.flush()
            new_parses += 1
            if args.delete_raw:
                freed += path.stat().st_size
                path.unlink()
                deleted += 1
    # second sweep: reclaim files whose rows landed in earlier runs
    for path in reclaim:
        freed += path.stat().st_size
        path.unlink()
        deleted += 1

    print(f"pass={args.which} keys={len(keys)} already-parsed={len(done)} "
          f"newly-parsed={new_parses} reclaimed_files={deleted} "
          f"freed={freed / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
