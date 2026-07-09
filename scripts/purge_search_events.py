"""
Retention purge for the personal search-history table.

Deletes raw search_events rows (per-visitor query log, feeds /api/v1/history)
older than --days (default 180). daily_rollup — the anonymous per-day/per-term
aggregate the /api/v1/stats/* charts read from — is never touched by this
script; it has no per-visitor identifying data and is meant to be kept
forever per the search-history plan.

MG-run maintenance script (A3 local-first: no agent cron, no external
service). Safe to re-run; a run with nothing past the cutoff purges 0 rows.

Usage:
    python scripts/purge_search_events.py                # purge rows older than 180 days
    python scripts/purge_search_events.py --days 90       # custom retention window
    python scripts/purge_search_events.py --dry-run       # report count, delete nothing
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "app"))

import history_db  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=180, help="retention window in days (default: 180)")
    ap.add_argument("--dry-run", action="store_true", help="report the row count that would be deleted, delete nothing")
    args = ap.parse_args()

    if args.days < 1:
        raise SystemExit("FAIL: --days must be >= 1")

    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat()
    con = history_db.open_connection()
    try:
        if args.dry_run:
            n = con.execute("SELECT COUNT(*) FROM search_events WHERE ts < ?", (cutoff,)).fetchone()[0]
            print(f"dry-run: {n} search_events row(s) older than {args.days}d (cutoff {cutoff}) would be purged")
        else:
            n = history_db.purge_old_search_events(con, cutoff)
            print(f"purged {n} search_events row(s) older than {args.days}d (cutoff {cutoff})")
    finally:
        con.close()


if __name__ == "__main__":
    main()
