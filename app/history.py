"""kosha — personal search history + aggregate analytics endpoints.
Plan: `Uprava/handoffs` kosha search-history plan (Phases A/B/C). Writable
history DB is separate from the read-only dictionary DB (history_db.py);
personal endpoints are cookie-scoped via identity.py, aggregate endpoints are
public/credential-free so a future embed (e.g. the Cologne homepage) can
fetch them directly.
"""
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from history_db import (
    clear_visitor_history,
    get_history_db,
    get_visitor_history,
)
from identity import resolve_anon_id

router = APIRouter()

MAGIC_LINK_TTL = timedelta(minutes=30)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Personal history (Phase A)
# ---------------------------------------------------------------------------

@router.get("/api/v1/history")
def get_history(request: Request, response: Response, limit: int = 50, offset: int = 0,
                 con: sqlite3.Connection = Depends(get_history_db)):
    if limit > 200:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "bad_request", "message": "limit must be <= 200", "suggestions": []}
        })
    anon_id = resolve_anon_id(request, response)
    rows, total = get_visitor_history(con, anon_id, limit, offset)
    results = [
        {"ts": r["ts"], "query_raw": r["query_raw"], "query_slp1": r["query_slp1"],
         "mode": r["mode"], "results_total": r["results_total"]}
        for r in rows
    ]
    return {"query": {"limit": limit, "offset": offset, "total": total}, "results": results}


@router.delete("/api/v1/history")
def delete_history(request: Request, response: Response,
                    con: sqlite3.Connection = Depends(get_history_db)):
    anon_id = resolve_anon_id(request, response)
    deleted = clear_visitor_history(con, anon_id)
    return {"deleted": deleted}


# ---------------------------------------------------------------------------
# Aggregate analytics (Phase B) — public, no cookie required
# ---------------------------------------------------------------------------

@router.get("/api/v1/stats/summary")
def stats_summary(con: sqlite3.Connection = Depends(get_history_db)):
    total_searches = con.execute("SELECT COUNT(*) FROM search_events").fetchone()[0]
    unique_visitors = con.execute("SELECT COUNT(DISTINCT anon_id) FROM search_events").fetchone()[0]
    top = con.execute(
        "SELECT query_slp1, SUM(count) AS n FROM daily_rollup "
        "GROUP BY query_slp1 ORDER BY n DESC LIMIT 10"
    ).fetchall()
    return {
        "total_searches": total_searches,
        "unique_visitors": unique_visitors,
        "top_terms": [{"query_slp1": r["query_slp1"], "count": r["n"]} for r in top],
    }


@router.get("/api/v1/stats/timeseries")
def stats_timeseries(interval: str = "day", days: int = 30,
                      con: sqlite3.Connection = Depends(get_history_db)):
    if interval not in ("day", "week"):
        raise HTTPException(status_code=400, detail={
            "error": {"code": "bad_request", "message": "interval must be 'day' or 'week'", "suggestions": []}
        })
    if days > 365:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "bad_request", "message": "days must be <= 365", "suggestions": []}
        })
    since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    rows = con.execute(
        "SELECT day, SUM(count) AS n FROM daily_rollup WHERE day >= ? GROUP BY day ORDER BY day",
        (since,),
    ).fetchall()
    daily = [{"day": r["day"], "count": r["n"]} for r in rows]
    if interval == "day":
        return {"interval": interval, "points": daily}
    # week: bucket by ISO year-week
    buckets: dict[str, int] = {}
    for point in daily:
        d = datetime.fromisoformat(point["day"]).date()
        iso_year, iso_week, _ = d.isocalendar()
        key = f"{iso_year}-W{iso_week:02d}"
        buckets[key] = buckets.get(key, 0) + point["count"]
    points = [{"week": k, "count": v} for k, v in sorted(buckets.items())]
    return {"interval": interval, "points": points}


@router.get("/api/v1/stats/top")
def stats_top(limit: int = 50, days: int | None = None,
              con: sqlite3.Connection = Depends(get_history_db)):
    if limit > 200:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "bad_request", "message": "limit must be <= 200", "suggestions": []}
        })
    if days:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
        rows = con.execute(
            "SELECT query_slp1, SUM(count) AS n FROM daily_rollup WHERE day >= ? "
            "GROUP BY query_slp1 ORDER BY n DESC LIMIT ?",
            (since, limit),
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT query_slp1, SUM(count) AS n FROM daily_rollup "
            "GROUP BY query_slp1 ORDER BY n DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return {"results": [{"query_slp1": r["query_slp1"], "count": r["n"]} for r in rows]}


# ---------------------------------------------------------------------------
# Magic-link email login (Phase C) — scaffolding only. `send_magic_link_email`
# is a stub: wiring a real transactional-email provider is an open @DECIDE
# (see the kosha search-history plan) and is a one-function swap once picked.
# ---------------------------------------------------------------------------

def send_magic_link_email(email: str, token: str) -> None:
    # Stub: no external service is called (A3 local-first / RISKS.md R12).
    # Logs the link so MG can test the flow locally until a provider is chosen.
    print(f"[kosha][magic-link stub] would email {email}: /api/v1/auth/verify?token={token}")


@router.post("/api/v1/auth/request-link")
def request_link(request: Request, response: Response, email: str,
                  con: sqlite3.Connection = Depends(get_history_db)):
    anon_id = resolve_anon_id(request, response)
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + MAGIC_LINK_TTL).isoformat()
    con.execute(
        "INSERT INTO magic_links (token, email, anon_id, expires_at) VALUES (?, ?, ?, ?)",
        (token, email, anon_id, expires_at),
    )
    con.commit()
    send_magic_link_email(email, token)
    return {"sent": True}


@router.get("/api/v1/auth/verify")
def verify_link(token: str, request: Request, response: Response,
                 con: sqlite3.Connection = Depends(get_history_db)):
    row = con.execute("SELECT * FROM magic_links WHERE token = ?", (token,)).fetchone()
    if row is None or row["used"]:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "link_not_found", "message": "invalid or already-used link", "suggestions": []}
        })
    if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail={
            "error": {"code": "link_expired", "message": "magic link expired, request a new one", "suggestions": []}
        })
    con.execute("UPDATE magic_links SET used = 1 WHERE token = ?", (token,))
    con.execute(
        "INSERT INTO visitors (anon_id, email, email_verified, created_at) VALUES (?, ?, 1, ?) "
        "ON CONFLICT(anon_id) DO UPDATE SET email = excluded.email, email_verified = 1",
        (row["anon_id"], row["email"], _now()),
    )
    con.commit()
    # Re-issue the same anon_id cookie on this device so the just-linked
    # history is immediately visible; cross-device history is looked up by
    # email at read time in a later pass, not by merging anon_id rows here.
    response.set_cookie("kosha_anon_id", row["anon_id"], max_age=60 * 60 * 24 * 365 * 2,
                         httponly=True, samesite="lax")
    return {"linked": True, "email": row["email"]}
