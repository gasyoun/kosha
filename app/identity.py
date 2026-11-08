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

#: H6909 (bughunt 13.10 BH-K5): single documented dev override for the cookie
#: hardening flags. Defaults OFF — `Secure` is on unless this env var is
#: explicitly truthy, so production and any https deployment are unaffected.
#: Documented in KOSHA_DEPLOYMENT.md.
COOKIE_INSECURE_DEV_ENV = "KOSHA_COOKIE_INSECURE_DEV"
_FLAG_TRUE = ("1", "true", "yes", "on")


def issue_anon_cookie(response: Response, anon_id: str) -> None:
    """The ONE mint for the `kosha_anon_id` cookie (H6909, BH-K5).

    Every call site must route through here so the hardening flags live in a
    single place: `HttpOnly`, `SameSite=lax`, `max_age` and `Secure` (the
    default) — the only off switch being `KOSHA_COOKIE_INSECURE_DEV`, a
    manual plain-http LAN/localhost override that defaults off (prod-safe).
    """
    response.set_cookie(
        ANON_COOKIE, anon_id, max_age=COOKIE_MAX_AGE,
        httponly=True, samesite="lax",
        secure=os.getenv(COOKIE_INSECURE_DEV_ENV, "").strip().lower() not in _FLAG_TRUE,
    )


def resolve_anon_id(request: Request, response: Response) -> str:
    anon_id = request.cookies.get(ANON_COOKIE)
    if not anon_id:
        anon_id = str(uuid.uuid4())
        issue_anon_cookie(response, anon_id)
    return anon_id


def hash_ip(request: Request) -> str | None:
    ip = request.client.host if request.client else None
    if not ip:
        return None
    salt = (os.getenv("HISTORY_IP_SALT") or "").strip()
    # H6909 (bughunt 13.10 BH-K4): fail closed. The committed dev-salt
    # fallback is gone — without a configured salt nothing is hashed and no
    # visitor data is persisted. The startup gate in kosha.settings refuses
    # history-enabled-without-salt first; this is the request-time backstop.
    if not salt:
        raise RuntimeError(
            "HISTORY_IP_SALT is unset or empty; refusing to hash visitor IPs "
            "with a fallback salt (bughunt 13.10 BH-K4). Set a random "
            "host-local HISTORY_IP_SALT, or leave KOSHA_HISTORY_ENABLED off."
        )
    return hashlib.sha256(f"{salt}:{ip}".encode("utf-8")).hexdigest()
