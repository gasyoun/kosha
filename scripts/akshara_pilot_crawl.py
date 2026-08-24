#!/usr/bin/env python3
"""H3455 lane A step 2 - polite bounded crawl of akshara.ru dict=all card pages.

Robots discipline (verified 24-08-2026): ONLY /kosha?q=<slp1>&dict=all&script=slp1
HTML pages (allowed for User-agent: *); fenced endpoints (/kosha/card|words|suggest,
/showasset, /internal-scans/) are never requested - enforced by a URL regex guard.

Politeness: identified UA with contact, >=2 s throttle + jitter, exponential backoff,
checkpointed JSONL manifest with resume-from-last-offset, one retry class only.

Usage:
  python scripts/akshara_pilot_crawl.py            # resume crawl to completion
  python scripts/akshara_pilot_crawl.py --limit 3  # smoke run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "akshara_pilot" / "sample_manifest.jsonl"
CRAWL_LOG = ROOT / "data" / "akshara_pilot" / "crawl_manifest.jsonl"
CRAWL_LOG_RU = ROOT / "data" / "akshara_pilot" / "crawl_manifest_ru.jsonl"
RAW_DIR = ROOT / "data" / "raw_akshara_pilot"

RU_DICTS = ("mw_ru", "apte_ru", "pwg_ru")

UA = "kosha-research-bot/0.1 (bounded lexical benchmark pilot; contact: hello@samskrtam.ru)"
ALLOWED_URL = re.compile(r"^https://akshara\.ru/kosha\?q=[^&]+&dict=(all|mw_ru|apte_ru|pwg_ru)&script=slp1$")
THROTTLE_S = 2.0
JITTER_S = 1.0
MAX_RETRY = 3


def guarded_fetch(url: str) -> tuple[int, bytes]:
    """Fetch with the allow-list guard; returns (http_status, body)."""
    if not ALLOWED_URL.match(url):
        raise RuntimeError(f"ROBOTS GUARD: url outside allowed pattern: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    last = None
    for attempt in range(1, MAX_RETRY + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:  # noqa: SLF001 - stdlib attr
            last = e
            if e.code in (429, 500, 502, 503):
                time.sleep(min(60, THROTTLE_S * (2 ** attempt)))
                continue
            raise
        except Exception as e:  # transient network
            last = e
            time.sleep(min(60, THROTTLE_S * (2 ** attempt)))
    raise RuntimeError(f"fetch failed after {MAX_RETRY} tries: {last}")


def done_keys(log: Path) -> set[str]:
    """Keys already fetched OK in `log`. For the ru pass the key carries the dict suffix."""
    done: set[str] = set()
    if log.exists():
        with open(log, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r.get("http") == 200:
                    done.add(r["slp1"])
    return done


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="smoke-run cap")
    ap.add_argument("--ru", action="store_true",
                    help="second pass: fetch dict=mw_ru|apte_ru|pwg_ru per headword")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(MANIFEST, encoding="utf-8")]
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if not args.ru:
        log = CRAWL_LOG
        done = done_keys(log)
        todo = [(r["slp1"], "all", r["url"]) for r in rows if r["slp1"] not in done]
    else:
        log = CRAWL_LOG_RU
        done = done_keys(log)
        todo = []
        for r in rows:
            for d in RU_DICTS:
                key = f"{r['slp1']}|{d}"
                if key in done:
                    continue
                url = f"https://akshara.ru/kosha?q={urllib.parse.quote(r['slp1'])}&dict={d}&script=slp1"
                todo.append((key, d, url))
    if args.limit:
        todo = todo[: args.limit]
    print(f"pass={'ru' if args.ru else 'all'} manifest {len(rows)}, already-done {len(done)}, to-crawl {len(todo)}")

    ok = fail = 0
    for i, (key, tag, url) in enumerate(todo, 1):
        slp1, _, dictpart = key.partition("|")
        safe = re.sub(r"[^A-Za-z0-9_.~-]", "_", slp1)[:80] or "_"
        fname = f"{safe}.html" if not dictpart else f"{safe}.{dictpart}.html"
        t0 = time.monotonic()
        try:
            status, body = guarded_fetch(url)
            (RAW_DIR / fname).write_bytes(body)
            rec = {
                "slp1": key, "stratum": next(r["stratum"] for r in rows if r["slp1"] == slp1),
                "dict": dictpart or "all", "url": url,
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "http": status, "bytes": len(body), "ms": int((time.monotonic() - t0) * 1000),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
            ok += 1
        except Exception as e:
            rec = {"slp1": key, "stratum": "", "dict": dictpart or "all", "url": url,
                   "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "http": 0, "bytes": 0, "error": repr(e)[:200]}
            fail += 1
        with open(log, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if i % 10 == 0 or i == len(todo):
            print(f"[{i}/{len(todo)}] ok={ok} fail={fail} last={rec['http']} {key}", flush=True)
        time.sleep(THROTTLE_S + random.uniform(0, JITTER_S))
    print(f"DONE ok={ok} fail={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
