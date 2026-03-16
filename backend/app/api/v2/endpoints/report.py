import logging
import uuid

from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.schemas.provider_request import ProviderRequest
from app.services.alphasophia import get_hcp_data
from app.services.email import send_request_confirmation
from app.services.job_store import create_job, get_job
from app.services.queue import send_job
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


@router.post("/generate")
async def submit_report_job(payload: ProviderRequest):
    """
    Enqueue a report generation job. Returns a job_id immediately.
    Poll GET /status/{job_id} to check progress and retrieve the result.
    """
    job_id = f"MERC-{uuid.uuid4().hex[:12].upper()}"
    create_job(
        job_id=job_id,
        payload_json=payload.model_dump_json(),
        specialty_name=payload.specialty_name,
        provider_name=payload.client_provider.name,
    )
    send_job(job_id)

    if payload.customer_email:
        status_url = f"{settings.FRONTEND_URL}/status" if settings.FRONTEND_URL else ""
        send_request_confirmation(
            to=payload.customer_email,
            job_id=job_id,
            provider_name=payload.client_provider.name,
            status_url=status_url,
        )

    return {"job_id": job_id, "status": "pending"}


@router.get("/status/{job_id}")
async def get_report_status(job_id: str):
    """
    Poll job status. When status == 'done', result_html contains the report.
    Statuses: pending → running → done | failed
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resp: dict = {
        "job_id": job_id,
        "status": job["status"],
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "specialty_name": job.get("specialty_name"),
        "provider_name": job.get("provider_name"),
    }

    if job["status"] == "done":
        resp["result_html"] = job.get("result_html", "")
        resp["report_s3_url"] = job.get("report_s3_url", "")
    elif job["status"] == "failed":
        resp["error"] = job.get("error", "Unknown error")

    return resp
