from fastapi import APIRouter

from app.api.v2.router import router as v2_router

api_router = APIRouter()
api_router.include_router(v2_router, tags=["v2"], prefix="/v2")
