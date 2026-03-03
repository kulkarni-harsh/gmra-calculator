from fastapi import APIRouter

from app.api.v1.endpoints import health, slides

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(slides.router, tags=["slides"], prefix="/slides")
