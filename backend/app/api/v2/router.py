from fastapi import APIRouter
from app.api.v2.endpoints import report

router = APIRouter()
router.include_router(report.router, prefix="/report")
