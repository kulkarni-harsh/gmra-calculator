import json
import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.schemas.payment import CreateT0PaymentIntentRequest
from app.services.job_store import JobAlreadyExistsError, create_job_awaiting_payment
from app.services.payment import create_t0_payment_intent

router = APIRouter()


@router.post("/create-payment-intent")
async def create_t0_payment_intent_endpoint(payload: CreateT0PaymentIntentRequest):
    """Pre-generate job_id, create Stripe PaymentIntent for $399, store T0 job in DynamoDB."""
    job_id = f"MERC-{uuid.uuid4().hex[:12].upper()}"
    address_label = f"{payload.address_line_1}, {payload.city} {payload.state} {payload.zip_code}"

    try:
        client_secret = create_t0_payment_intent(
            job_id=job_id,
            customer_email=str(payload.customer_email),
            specialty_name=payload.specialty_name,
            address_label=address_label,
        )
    except Exception as exc:
        logging.error("Failed to create T0 Stripe PaymentIntent: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to create payment session") from exc

    pre_payload_json = json.dumps({
        "report_type": "t0",
        "specialty_name": payload.specialty_name,
        "address_line_1": payload.address_line_1,
        "address_line_2": payload.address_line_2,
        "city": payload.city,
        "state": payload.state,
        "zip_code": payload.zip_code,
        "miles_radius": payload.miles_radius,
        "customer_email": str(payload.customer_email),
        "payment_intent_id": "pending",
    })

    try:
        create_job_awaiting_payment(
            job_id=job_id,
            payload_json=pre_payload_json,
            specialty_name=payload.specialty_name,
            provider_name=address_label,
        )
    except JobAlreadyExistsError:
        logging.error("job_id collision at T0 intent creation: %s", job_id)
        raise HTTPException(status_code=500, detail="Failed to initialize job") from None

    return {"client_secret": client_secret, "job_id": job_id}
