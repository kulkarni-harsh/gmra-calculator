from fastapi import APIRouter

from app.api.endpoints import jobs, payment, providers, report_t0, report_t1

api_router = APIRouter()
api_router.include_router(providers.router, tags=["providers"], prefix="/providers")
api_router.include_router(payment.router, tags=["payments"], prefix="/payments")
api_router.include_router(jobs.router, tags=["jobs"], prefix="/jobs")
api_router.include_router(report_t1.router, tags=["reports-t1"], prefix="/reports/t1")
api_router.include_router(report_t0.router, tags=["reports-t0"], prefix="/reports/t0")
