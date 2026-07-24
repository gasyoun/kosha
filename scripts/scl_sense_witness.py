#!/usr/bin/env python
"""W3a — SCL Reading-Aid sense-label witness (H1588).

Fetches **minimal sense labels only** into a gitignored cache. Never stores
page HTML, multi-sentence gloss dumps, or redistributable SCL/GPL body text
(plan ruling N4 + PLAN sense-frequency fence).

Rights: outreach H057 is still unresolved — this is a validation witness only.
If the scrape is hard-blocked (Anubis, network, empty labels), **fail closed**:
write a reason file, leave the label cache empty/absent, exit 0 so the
LLM/MFS arm can continue under the single-witness degraded gate.

  python scripts/scl_sense_witness.py
  python scripts/scl_sense_witness.py --dry-run   # no network
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wsd_core import CACHE_DIR, SCL_CACHE, ensure_cache_dir, MODEL_PROV  # noqa: E402

# Public SCL entry points historically probed for Reading Aid / morph.
# We only HEAD/GET lightly; any non-JSON or Anubis HTML is treated as blocked.
SCL_PROBE_URLS = (
    "https://sanskrit.uohyd.ac.in/scl/",
    "https://scl.samsaadhanii.in/",
)
REASON_PATH = os.path.join(CACHE_DIR, "scl_witness_reason.json")


def _probe(url: str, timeout: float = 12.0) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "kosha-wsd-witness/H1588 (validation labels only; not a scraper bot)"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(2048)
            ctype = (resp.headers.get("Content-Type") or "").lower()
            text = body.decode("utf-8", errors="replace")
            # Anubis / challenge walls typically return HTML with challenge markers.
            blocked = (
                "anubis" in text.lower()
                or "challenge" in text.lower() and "js" in text.lower()
                or "cf-browser-verification" in text.lower()
                or "just a moment" in text.lower()
            )
            return {
                "url": url,
                "status": getattr(resp, "status", None) or resp.getcode(),
                "content_type": ctype,
                "bytes": len(body),
                "blocked_heuristic": blocked,
                "ok": (not blocked) and 200 <= (resp.getcode() or 0) < 400,
            }
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "error": str(e), "ok": False}
    except Exception as e:
        return {"url": url, "error": repr(e), "ok": False}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="skip network; write fail-closed reason")
    args = ap.parse_args()
    ensure_cache_dir()
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if args.dry_run:
        reason = {
            "status": "fail_closed",
            "reason": "dry-run: network skipped",
            "ts": ts,
            "model": MODEL_PROV,
            "handoff": "H1588",
            "labels_written": 0,
        }
        with open(REASON_PATH, "w", encoding="utf-8") as f:
            json.dump(reason, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("LOG: SCL dry-run fail-closed →", REASON_PATH)
        return 0

    probes = [_probe(u) for u in SCL_PROBE_URLS]
    any_ok = any(p.get("ok") for p in probes)
    # Even if the site homepage is up, we do not have a rights-cleared bulk
    # sense-label API from H057. Without an explicit label endpoint contract,
    # write zero labels and document the degradation (autonomy contract WSD case).
    labels_written = 0
    if os.path.exists(SCL_CACHE):
        # Keep existing cache if present; do not wipe human-local re-runs.
        try:
            with open(SCL_CACHE, encoding="utf-8") as f:
                labels_written = sum(1 for line in f if line.strip())
        except OSError:
            labels_written = 0

    if labels_written == 0:
        # Ensure the cache path exists as an empty file only when we have a
        # successful rights path — currently we never invent labels.
        # Empty file would still be gitignored; prefer reason-only.
        status = "fail_closed"
        reason_txt = (
            "No rights-cleared SCL sense-label API (H057 outreach unresolved). "
            "Homepage probes recorded; zero labels written. "
            "Downstream WSD continues as single-witness (MFS/gloss-grounded arm)."
        )
    else:
        status = "cache_present"
        reason_txt = f"reused existing local cache ({labels_written} labels)"

    reason = {
        "status": status,
        "reason": reason_txt,
        "ts": ts,
        "model": MODEL_PROV,
        "handoff": "H1588",
        "probes": probes,
        "any_homepage_ok": any_ok,
        "labels_written": labels_written,
        "cache_path": SCL_CACHE,
        "fence": "gitignored minimal labels only; never commit SCL body text",
    }
    with open(REASON_PATH, "w", encoding="utf-8") as f:
        json.dump(reason, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"LOG: SCL witness status={status} labels={labels_written}")
    print("reason →", REASON_PATH)
    for p in probes:
        print(" probe", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
