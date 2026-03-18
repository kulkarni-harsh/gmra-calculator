import json
import logging
import uuid

import stripe
from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.schemas.payment import CreatePaymentIntentRequest
from app.schemas.provider_request import ProviderRequest
from app.services.alphasophia import get_hcp_data
from app.services.email import send_request_confirmation
from app.services.job_store import JobAlreadyExistsError, claim_job_for_generation, create_job_awaiting_payment, get_job
from app.services.payment import create_payment_intent, verify_payment_intent
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


@router.post("/create-payment-intent")
async def create_payment_intent_endpoint(payload: CreatePaymentIntentRequest):
    """
    Pre-generate a job_id, create a Stripe PaymentIntent for $500, and pre-store the full
    generation payload in DynamoDB with status 'awaiting_payment'. This ensures the webhook
    can enqueue the job even if the user's browser closes before /generate is called.
    """
    job_id = f"MERC-{uuid.uuid4().hex[:12].upper()}"
    try:
        client_secret = create_payment_intent(
            job_id=job_id,
            customer_email=payload.customer_email,
            provider_name=payload.provider_name,
            specialty_name=payload.specialty_name,
        )
    except Exception as exc:
        logging.error("Failed to create Stripe PaymentIntent: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to create payment session") from exc

    pre_payload_json = json.dumps(
        {
            "specialty_name": payload.specialty_name,
            "client_provider": payload.client_provider.model_dump(),
            "miles_radius": payload.miles_radius,
            "customer_email": str(payload.customer_email),
            "payment_intent_id": "pending",
        }
    )
    try:
        create_job_awaiting_payment(
            job_id=job_id,
            payload_json=pre_payload_json,
            specialty_name=payload.specialty_name,
            provider_name=payload.provider_name,
        )
    except JobAlreadyExistsError:
        logging.error("job_id collision at intent creation: %s", job_id)
        raise HTTPException(status_code=500, detail="Failed to initialize job") from None

    return {"client_secret": client_secret, "job_id": job_id}


@router.post("/generate")
async def submit_report_job(payload: ProviderRequest):
    """
    Verify Stripe payment, then enqueue report generation.
    Returns a job_id immediately. Poll GET /status/{job_id} to check progress.
    """
    try:
        job_id = verify_payment_intent(
            payment_intent_id=payload.payment_intent_id,
            expected_email=payload.customer_email,
        )
    except ValueError as exc:
        logging.warning("Payment verification failed: %s", exc)
        raise HTTPException(status_code=402, detail=str(exc)) from exc

    try:
        claim_job_for_generation(job_id)
    except JobAlreadyExistsError:
        raise HTTPException(status_code=409, detail="This payment has already been used to generate a report") from None
    send_job(job_id)

    if payload.customer_email:
        status_url = f"{settings.FRONTEND_URL}/status" if settings.FRONTEND_URL else ""
        send_request_confirmation(
            to=payload.customer_email,
            job_id=job_id,
            provider_name=str(payload.client_provider.name),
            status_url=status_url,
        )

    return {"job_id": job_id, "status": "pending"}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    Processes payment_intent.succeeded for async payment methods (3DS, bank redirects).
    Must be registered in Stripe dashboard pointing to POST /api/v2/webhook/stripe.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload") from None
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature") from None

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        metadata = intent.get("metadata", {})
        job_id = metadata.get("job_id")
        if not job_id:
            logging.warning("Stripe webhook: payment_intent.succeeded missing job_id, intent=%s", intent.get("id"))
            return {"received": True}

        try:
            payload_json = claim_job_for_generation(job_id)
        except JobAlreadyExistsError:
            # Already claimed by the synchronous /generate path — nothing to do
            logging.info("Stripe webhook: job %s already claimed via sync path", job_id)
            return {"received": True}
        except Exception as exc:
            logging.error("Stripe webhook: failed to claim job %s: %s", job_id, exc)
            raise HTTPException(status_code=500, detail="Failed to process webhook") from exc

        send_job(job_id)
        logging.info("Stripe webhook: enqueued job %s via payment_intent.succeeded", job_id)

        try:
            stored = json.loads(payload_json)
            customer_email = stored.get("customer_email", "")
            provider_name = stored.get("client_provider", {}).get("name", "")
            if customer_email:
                status_url = f"{settings.FRONTEND_URL}/status" if settings.FRONTEND_URL else ""
                send_request_confirmation(
                    to=customer_email,
                    job_id=job_id,
                    provider_name=provider_name,
                    status_url=status_url,
                )
        except Exception as exc:
            logging.error("Stripe webhook: confirmation email failed for job %s: %s", job_id, exc)

    return {"received": True}


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
        resp["report_pdf_s3_url"] = job.get("report_pdf_s3_url", "")
    elif job["status"] == "failed":
        resp["error"] = job.get("error", "Unknown error")

    return resp
