from fastapi import APIRouter

from app.api.v3.endpoints import payment, report

router = APIRouter()
router.include_router(payment.router, tags=["v3-payment"])
router.include_router(report.router, prefix="/report", tags=["v3-report"])
