import json
import logging
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.utils.common import load_fee_schedule_tables
from app.utils.validator import validate_speciality_master_df


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    # Load lookup data
    app.state.specialty_lookup = json.load(open(settings.LOOKUP_DIR / "specialty_lookup.json"))
    app.state.anchor_cpt_lookup = json.load(open(settings.LOOKUP_DIR / "anchor_cpt_lookup.json"))
    app.state.zip_centroids_df = pd.read_csv(settings.LOOKUP_DIR / "zip_centroids.csv")
    app.state.cpt_lookup_df = pd.read_csv(settings.LOOKUP_DIR / "cpt_lookup.csv")
    # Load Specialty Master Sheet
    app.state.specialty_master_df = pd.read_excel(settings.LOOKUP_DIR / "Specialty Master Sheet.xlsx")
    validate_speciality_master_df(app.state.specialty_master_df)
    # Load fee schedule tables (RVU + GPCI)
    app.state.rvu_table, app.state.gpci_table = load_fee_schedule_tables()
    logging.info("Lookup data loaded successfully.")

    yield
    del app.state.zip_centroids_df
    del app.state.cpt_lookup_df
    del app.state.specialty_master_df


def _rate_limit_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:  # pragma: no cover - thin wrapper
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
        headers={"Retry-After": "60"},
    )


def create_app() -> FastAPI:
    docs_url = "/docs" if settings.OPENAPI_PUBLIC else None
    openapi_url = "/openapi.json" if settings.OPENAPI_PUBLIC else None

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url=docs_url,
        openapi_url=openapi_url,
        redoc_url=None,
    )

    # slowapi wiring
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)

    # CORS
    origins = []
    if settings.ALLOWED_ORIGINS:
        origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()
