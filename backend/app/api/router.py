from fastapi import APIRouter

from app.api.endpoints import jobs, payment, providers
from app.api.v2.router import router as v2_router

api_router = APIRouter()
api_router.include_router(providers.router, tags=["providers"])
api_router.include_router(payment.router, tags=["payment"])
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(v2_router, tags=["v2"], prefix="/v2")
