"""kosha — anonymous visitor identity. One cookie (`kosha_anon_id`), no
login required; `app/history.py`'s magic-link flow later upgrades an anon_id
to an email-linked visitor without needing a new identity mechanism.
"""
import hashlib
import os
import uuid

from fastapi import Request, Response

ANON_COOKIE = "kosha_anon_id"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 2  # 2 years


def resolve_anon_id(request: Request, response: Response) -> str:
    anon_id = request.cookies.get(ANON_COOKIE)
    if not anon_id:
        anon_id = str(uuid.uuid4())
        response.set_cookie(
            ANON_COOKIE, anon_id, max_age=COOKIE_MAX_AGE,
            httponly=True, samesite="lax",
        )
    return anon_id


def hash_ip(request: Request) -> str | None:
    ip = request.client.host if request.client else None
    if not ip:
        return None
    salt = os.getenv("HISTORY_IP_SALT", "kosha-dev-salt")
    return hashlib.sha256(f"{salt}:{ip}".encode("utf-8")).hexdigest()
