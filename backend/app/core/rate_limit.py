"""slowapi-based in-app rate limiter.

Keyed on (client, ip) so different API-key holders get independent buckets.
Storage is in-memory per ECS task; the effective ceiling is therefore
limit * task_count. Acceptable for current scale — revisit when partner count
grows or rate-limit precision becomes business-critical.
"""
from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def client_id_key(request: Request) -> str:
    """Key requests by (client-tag, remote-ip)."""
    client = getattr(request.state, "client", None) or "anonymous"
    ip = request.client.host if request.client else "unknown"
    return f"{client}:{ip}"


limiter = Limiter(
    key_func=client_id_key,
    default_limits=["300/minute"],
    headers_enabled=True,
)


# Re-export for convenience in route modules.
__all__ = ["client_id_key", "limiter", "get_remote_address"]
