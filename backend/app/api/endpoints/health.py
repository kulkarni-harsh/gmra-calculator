"""Health-check endpoint — used by load balancers and uptime probes."""

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("")
def health_check() -> dict[str, str]:
    """Return service liveness with a UTC timestamp."""
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}
