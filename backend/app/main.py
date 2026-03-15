import json
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI
from opencage.geocoder import OpenCageGeocode

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
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
    app.state.geocoder_client = OpenCageGeocode(settings.OPENCAGE_API_KEY)
    # Load Specialty Master Sheet
    app.state.specialty_master_df = pd.read_excel(settings.LOOKUP_DIR / "Specialty Master Sheet.xlsx")
    validate_speciality_master_df(app.state.specialty_master_df)
    # Load fee schedule tables (RVU + GPCI)
    app.state.rvu_table, app.state.gpci_table = load_fee_schedule_tables()
    print("Lookup data loaded successfully.")

    yield
    del app.state.zip_centroids_df
    del app.state.cpt_lookup_df
    del app.state.specialty_master_df


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()
