import logging

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.address_report_request import AddressReportRequest
from app.services.email import send_request_confirmation
from app.services.job_store import JobAlreadyExistsError, claim_job_for_generation
from app.services.payment import T0_REPORT_AMOUNT_CENTS, verify_payment_intent
from app.services.queue import send_job

router = APIRouter()


@router.post("/generate")
async def submit_t0_report_job(payload: AddressReportRequest):
    """Verify Stripe payment, enqueue T0 report generation. Poll GET /api/status/{job_id}."""
    try:
        job_id = verify_payment_intent(
            payment_intent_id=payload.payment_intent_id,
            expected_email=str(payload.customer_email),
            expected_amount=T0_REPORT_AMOUNT_CENTS,  # $399 — not the T1 $500 default
        )
    except ValueError as exc:
        logging.warning("T0 payment verification failed: %s", exc)
        raise HTTPException(status_code=402, detail=str(exc)) from exc

    try:
        claim_job_for_generation(
            job_id
        )  # return value (payload JSON) not needed — full payload already in request body
    except JobAlreadyExistsError:
        raise HTTPException(status_code=409, detail="This payment has already been used to generate a report") from None

    send_job(job_id)

    if payload.customer_email:
        status_url = f"{settings.FRONTEND_URL}/status" if settings.FRONTEND_URL else ""
        address_label = f"{payload.address_line_1}, {payload.city} {payload.state} {payload.zip_code}"
        send_request_confirmation(
            to=str(payload.customer_email),
            job_id=job_id,
            provider_name=address_label,
            status_url=status_url,
        )

    return {"job_id": job_id, "status": "pending"}
