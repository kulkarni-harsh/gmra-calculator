from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("")
def health_check() -> dict:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
