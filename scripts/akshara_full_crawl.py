#!/usr/bin/env python3
"""H3597 - FULL akshara.ru kosha crawl over the frozen census manifest.

Extends the H3455 bounded pilot (scripts/akshara_pilot_crawl.py) to ALL
51,663 census heads, ALL dictionaries. MG ruling 27-08-2026: NO volume stop -
census first, full run regardless of volume; report volume at milestone
checkpoints (every 1000 URLs), never abort because it got big.

Contract UNCHANGED from H3455:
  - only /kosha?q=<slp1>&dict=(all|mw_ru|apte_ru|pwg_ru)&script=slp1 card pages;
    robots-fenced endpoints NEVER requested (guard reused verbatim from the
    pilot module - import, not fork);
  - identified UA with contact, 2.0 s throttle + <=1 s jitter, exponential
    backoff, one retry class;
  - checkpointed append-only JSONL manifests with resume-from-log (a crash
    never restarts from zero - resumeability is LOAD-BEARING at ~207k URLs).

Passes:
  pass 1 (default): dict=all originals, data/akshara_full/crawl_manifest.jsonl
  pass 2 (--ru):    dict=mw_ru|apte_ru|pwg_ru, crawl_manifest_ru.jsonl

Usage:
  python scripts/akshara_full_crawl.py             # pass 1, resume to completion
  python scripts/akshara_full_crawl.py --ru        # pass 2, resume to completion
  python scripts/akshara_full_crawl.py --limit 3   # smoke run
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
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from akshara_pilot_crawl import MAX_RETRY, THROTTLE_S, guarded_fetch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "akshara_full" / "head_manifest.jsonl"
CRAWL_LOG = ROOT / "data" / "akshara_full" / "crawl_manifest.jsonl"
CRAWL_LOG_RU = ROOT / "data" / "akshara_full" / "crawl_manifest_ru.jsonl"
MILESTONES = ROOT / "data" / "akshara_full" / "milestones.jsonl"
RAW_DIR = ROOT / "data" / "raw_akshara_full"

RU_DICTS = ("mw_ru", "apte_ru", "pwg_ru")
MILESTONE_EVERY = 1000

# H3597 report §5: the site can serve a near-miss head's card for a cold key.
Q_SLP1_RE = re.compile(r'data-q-slp1="([^"]+)"')


def verify_head(body: bytes, slp1: str, url: str) -> tuple[bytes, bool, str]:
    """Cold-fetch mis-resolution guard: if the stored card names a different
    head (data-q-slp1 != requested), re-fetch once warm and keep the answer.
    Zero-article pages carry no marker and pass through untouched.

    Returns (body_to_store, replaced_by_warm_refetch, misresolved_to)."""
    m = Q_SLP1_RE.search(body.decode("utf-8", "replace"))
    if m is None or m.group(1) == slp1:
        return body, False, ""
    time.sleep(THROTTLE_S)
    try:
        _status, body2 = guarded_fetch(url)
    except Exception:  # keep the (wrong-headed) body; drain report decides
        return body, False, m.group(1)
    m2 = Q_SLP1_RE.search(body2.decode("utf-8", "replace"))
    if m2 is None or m2.group(1) == slp1:
        return body2, True, ""
    return body2, False, m2.group(1)


def done_keys(log: Path) -> set[str]:
    """Keys already fetched OK in `log`; ru-pass keys carry the dict suffix."""
    done: set[str] = set()
    if log.exists():
        with open(log, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r.get("http") == 200:
                    done.add(r["slp1"])
    return done


def milestone(todo_n: int, i: int, ok: int, fail: int, t0: float) -> None:
    rate = i / max(1e-9, time.monotonic() - t0)
    eta_h = (todo_n - i) / max(1e-9, rate) / 3600.0
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "at": i, "of": todo_n, "ok": ok, "fail": fail,
        "urls_per_s": round(rate, 3), "eta_hours": round(eta_h, 1),
    }
    with open(MILESTONES, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"MILESTONE {i}/{todo_n} ok={ok} fail={fail} "
          f"rate={rate:.2f}/s eta={eta_h:.1f}h", flush=True)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="smoke-run cap")
    ap.add_argument("--ru", action="store_true",
                    help="pass 2: dict=mw_ru|apte_ru|pwg_ru per headword")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(MANIFEST, encoding="utf-8")]
    heads = [r["slp1"] for r in rows]
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if sys.platform == "win32":
        # Network I/O alone does not hold off Windows sleep; ask the OS to
        # keep the system awake for as long as this process lives.
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
        except Exception:  # noqa: BLE001 - best-effort keep-awake
            pass

    if not args.ru:
        log = CRAWL_LOG
        done = done_keys(log)
        todo = [(h, "all",
                 f"https://akshara.ru/kosha?q={urllib.parse.quote(h)}&dict=all&script=slp1")
                for h in heads if h not in done]
    else:
        log = CRAWL_LOG_RU
        done = done_keys(log)
        todo = []
        for h in heads:
            for d in RU_DICTS:
                key = f"{h}|{d}"
                if key in done:
                    continue
                todo.append((key, d,
                             f"https://akshara.ru/kosha?q={urllib.parse.quote(h)}&dict={d}&script=slp1"))
    if args.limit:
        todo = todo[: args.limit]
    print(f"pass={'ru' if args.ru else 'all'} census {len(rows)}, "
          f"already-done {len(done)}, to-crawl {len(todo)}", flush=True)

    ok = fail = 0
    t0 = time.monotonic()
    for i, (key, tag, url) in enumerate(todo, 1):
        slp1, _, dictpart = key.partition("|")
        safe = re.sub(r"[^A-Za-z0-9_.~-]", "_", slp1)[:80] or "_"
        fname = f"{safe}.html" if not dictpart else f"{safe}.{dictpart}.html"
        t = time.monotonic()
        try:
            status, body = guarded_fetch(url)
            body, resolved_fix, misresolved = verify_head(body, slp1, url)
            (RAW_DIR / fname).write_bytes(body)
            rec = {
                "slp1": key, "dict": dictpart or "all", "url": url,
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "http": status, "bytes": len(body),
                "ms": int((time.monotonic() - t) * 1000),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
            if resolved_fix:
                rec["resolved_fix"] = True
            if misresolved:
                rec["misresolved"] = misresolved
            ok += 1
        except Exception as e:  # noqa: BLE001 - log everything, keep crawling
            rec = {"slp1": key, "dict": dictpart or "all", "url": url,
                   "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "http": 0, "bytes": 0, "error": repr(e)[:200]}
            fail += 1
        with open(log, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if i % 50 == 0 or i == len(todo):
            rate = i / max(1e-9, time.monotonic() - t0)
            print(f"[{i}/{len(todo)}] ok={ok} fail={fail} rate={rate:.2f}/s "
                  f"last={rec['http']} {key}", flush=True)
        if i % MILESTONE_EVERY == 0:
            milestone(len(todo), i, ok, fail, t0)
        time.sleep(THROTTLE_S + random.uniform(0, 1.0))
    milestone(len(todo), len(todo), ok, fail, t0)
    print(f"DONE ok={ok} fail={fail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
