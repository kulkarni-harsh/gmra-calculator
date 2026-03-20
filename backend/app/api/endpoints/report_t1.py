import logging

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.provider_request import ProviderRequest
from app.services.email import send_request_confirmation
from app.services.job_store import JobAlreadyExistsError, claim_job_for_generation
from app.services.payment import verify_payment_intent
from app.services.queue import send_job

router = APIRouter()


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
