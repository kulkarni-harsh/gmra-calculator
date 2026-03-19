import logging

from fastapi import APIRouter, HTTPException, Request

from app.services.alphasophia import get_hcp_data
from app.types.alphasophia import Provider
from app.utils.common import get_taxonomy_codes

router = APIRouter()


@router.get("/specialties")
async def list_specialties(request: Request):
    """Return all specialties that have provider density data."""
    specialty_lookup: dict = request.app.state.specialty_lookup
    return [
        {
            "id": specialty_id,
            "description": data["description"],
            "taxonomy_codes": data.get("taxonomy_codes", []),
            "national_density": data.get("states", {}).get("US"),
        }
        for specialty_id, data in specialty_lookup.items()
        if data.get("states")
    ]


@router.get("/search-providers")
async def search_providers(zip_code: str, specialty_name: str, request: Request):
    """Search for providers by ZIP code and specialty name."""
    taxonomy_codes = get_taxonomy_codes(request.app.state.specialty_lookup, specialty_name)
    if not taxonomy_codes:
        logging.warning("No taxonomy codes found for specialty %s", specialty_name)
        return []
    try:
        providers = await get_hcp_data(
            zip_codes_list=[zip_code],
            taxonomy_codes_list=taxonomy_codes,
            cpt_codes_list=[],
            npi_list=[],
            page_size=200,
        )
    except Exception as exc:
        logging.error("Failed to fetch providers from AlphaSophia: %s", exc)
        providers = []
    return [p.model_dump() for p in providers if isinstance(p, Provider)]


@router.get("/provider")
async def get_provider(zip_code: str, npi: str, specialty_name: str, request: Request):
    """Fetch a single provider by ZIP code, NPI, and specialty."""
    taxonomy_codes = get_taxonomy_codes(request.app.state.specialty_lookup, specialty_name)
    if not taxonomy_codes:
        logging.warning("No taxonomy codes found for specialty %s", specialty_name)
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        providers = await get_hcp_data(
            zip_codes_list=[zip_code],
            taxonomy_codes_list=taxonomy_codes,
            cpt_codes_list=[],
            npi_list=[npi],
            page_size=10,
        )
    except Exception as exc:
        logging.error("Failed to fetch provider from AlphaSophia: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to fetch provider data") from exc

    match = next((p for p in providers if isinstance(p, Provider) and p.npi == npi), None)
    if not match:
        raise HTTPException(status_code=404, detail="Provider not found")

    return match.model_dump()
