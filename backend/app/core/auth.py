"""API-key authentication dependency for MERC backend.

Validates X-API-Key against keys held in settings. Requests from internal
origins (our own React frontend) bypass the key check via the Origin header.
Stripe webhook and /health are wired exempt at the router level, not here.

Security note: The Origin-header bypass is designed for same-origin browser
requests where CORS enforcement prevents spoofing. It does NOT provide
protection against server-to-server calls (curl, Postman, Wix backend code)
that can set the Origin header freely. Keep INTERNAL_ORIGINS to your own
verified domains only.
"""

from __future__ import annotations

import hmac
import logging

from fastapi import HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)


def _known_keys() -> dict[str, str]:
    """Return mapping of client-name → key, omitting blanks."""
    pairs = {"wix": settings.API_KEY_WIX, "react": settings.API_KEY_REACT}
    return {name: value.strip() for name, value in pairs.items() if value.strip()}


def _internal_origins() -> set[str]:
    raw = settings.INTERNAL_ORIGINS or ""
    return {o.strip() for o in raw.split(",") if o.strip()}


def _identify_by_key(provided: str) -> str | None:
    """Constant-time compare provided key against each known key."""
    for name, real in _known_keys().items():
        if hmac.compare_digest(provided, real):
            return name
    return None


async def require_api_key(request: Request) -> None:
    """FastAPI dependency: pass if AUTH disabled, valid X-API-Key, or internal Origin."""
    if not settings.AUTH_ENFORCED:
        request.state.client = "auth-disabled"
        return

    provided = request.headers.get("X-API-Key", "").strip()
    if provided:
        client = _identify_by_key(provided)
        if client:
            request.state.client = client
            return

    origin = request.headers.get("Origin", "").strip()
    if origin and origin in _internal_origins():
        request.state.client = "internal"
        return

    logger.info(
        "auth.reject path=%s has_key=%s has_origin=%s",
        request.url.path,
        bool(provided),
        bool(origin),
    )
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
