import json
import logging

import stripe
import ulid
from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.schemas.payment import (
    CreatePaymentIntentRequest,
    CreateT1PaymentIntentRequest,
    CreateT2PaymentIntentRequest,
    CreateT3PaymentIntentRequest,
)
from app.services.email import send_request_confirmation
from app.services.job_store import JobAlreadyExistsError, claim_job_for_generation, create_job_awaiting_payment
from app.services.payment import (
    REPORT_TYPE_AMOUNTS,
    create_payment_intent,
    create_t1_payment_intent,
    create_t2_payment_intent,
    create_t3_payment_intent,
)
from app.services.queue import send_job

router = APIRouter()


@router.post("/create-payment-intent")
async def create_payment_intent_endpoint(payload: CreatePaymentIntentRequest):
    """
    Pre-generate a job_id, create a Stripe PaymentIntent for $500, and pre-store the full
    generation payload in DynamoDB with status 'awaiting_payment'. This ensures the webhook
    can enqueue the job even if the user's browser closes before /generate is called.
    """
    job_id = f"MERC-{ulid.ulid()}"
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


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    Processes payment_intent.succeeded for async payment methods (3DS, bank redirects).
    Must be registered in Stripe dashboard pointing to POST /api/payments/webhook/stripe.
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

        # Verify the charged amount matches the report type stored in DynamoDB.
        # This guards against webhook replays where a cheaper job_id is reused for a pricier tier.
        try:
            stored = json.loads(payload_json)
            report_type = stored.get("report_type", "a1")
            expected_amount = REPORT_TYPE_AMOUNTS.get(report_type, REPORT_TYPE_AMOUNTS["a1"])
            if intent.get("amount") != expected_amount:
                logging.error(
                    "Stripe webhook: amount mismatch for job %s (type=%s, got=%d, expected=%d) — skipping",
                    job_id,
                    report_type,
                    intent.get("amount"),
                    expected_amount,
                )
                return {"received": True}
        except Exception as exc:
            logging.error("Stripe webhook: could not verify amount for job %s: %s", job_id, exc)

        send_job(job_id)
        logging.info("Stripe webhook: enqueued job %s via payment_intent.succeeded", job_id)

        try:
            customer_email = stored.get("customer_email", "")
            # T1/T2 store address instead of client_provider; A1 stores client_provider
            if stored.get("report_type") in ("t1", "t2"):
                provider_name = (
                    f"{stored.get('address_line_1', '')}, {stored.get('city', '')} {stored.get('state', '')}"
                )
            else:
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


@router.post("/create-t1-payment-intent")
async def create_t1_payment_intent_endpoint(payload: CreateT1PaymentIntentRequest):
    """Pre-generate job_id, create Stripe PaymentIntent for $399, store T1 job in DynamoDB."""
    job_id = f"MERC-{ulid.ulid()}"
    address_label = f"{payload.address_line_1}, {payload.city} {payload.state} {payload.zip_code}"

    try:
        client_secret = create_t1_payment_intent(
            job_id=job_id,
            customer_email=str(payload.customer_email),
            specialty_name=payload.specialty_name,
            address_label=address_label,
        )
    except Exception as exc:
        logging.error("Failed to create T1 Stripe PaymentIntent: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to create payment session") from exc

    pre_payload_json = json.dumps(
        {
            "report_type": "t1",
            "specialty_name": payload.specialty_name,
            "address_line_1": payload.address_line_1,
            "address_line_2": payload.address_line_2,
            "city": payload.city,
            "state": payload.state,
            "zip_code": payload.zip_code,
            "drive_time_minutes": payload.drive_time_minutes,
            "customer_email": str(payload.customer_email),
            "payment_intent_id": "pending",
        }
    )

    try:
        create_job_awaiting_payment(
            job_id=job_id,
            payload_json=pre_payload_json,
            specialty_name=payload.specialty_name,
            provider_name=address_label,
        )
    except JobAlreadyExistsError:
        logging.error("job_id collision at T1 intent creation: %s", job_id)
        raise HTTPException(status_code=500, detail="Failed to initialize job") from None

    return {"client_secret": client_secret, "job_id": job_id}


@router.post("/create-t2-payment-intent")
async def create_t2_payment_intent_endpoint(payload: CreateT2PaymentIntentRequest):
    """Pre-generate job_id, create Stripe PaymentIntent for $599, store T2 job in DynamoDB."""
    job_id = f"MERC-{ulid.ulid()}"
    address_label = f"{payload.address_line_1}, {payload.city} {payload.state} {payload.zip_code}"

    try:
        client_secret = create_t2_payment_intent(
            job_id=job_id,
            customer_email=str(payload.customer_email),
            specialty_name=payload.specialty_name,
            address_label=address_label,
            cpt_codes=payload.cpt_codes,
        )
    except Exception as exc:
        logging.error("Failed to create T2 Stripe PaymentIntent: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to create payment session") from exc

    pre_payload_json = json.dumps(
        {
            "report_type": "t2",
            "specialty_name": payload.specialty_name,
            "address_line_1": payload.address_line_1,
            "address_line_2": payload.address_line_2,
            "city": payload.city,
            "state": payload.state,
            "zip_code": payload.zip_code,
            "drive_time_minutes": payload.drive_time_minutes,
            "customer_email": str(payload.customer_email),
            "payment_intent_id": "pending",
            "cpt_codes": payload.cpt_codes,
        }
    )

    try:
        create_job_awaiting_payment(
            job_id=job_id,
            payload_json=pre_payload_json,
            specialty_name=payload.specialty_name,
            provider_name=address_label,
        )
    except JobAlreadyExistsError:
        logging.error("job_id collision at T2 intent creation: %s", job_id)
        raise HTTPException(status_code=500, detail="Failed to initialize job") from None

    return {"client_secret": client_secret, "job_id": job_id}


@router.post("/create-t3-payment-intent")
async def create_t3_payment_intent_endpoint(payload: CreateT3PaymentIntentRequest):
    """Pre-generate job_id, create Stripe PaymentIntent for $599, store T3 job in DynamoDB."""
    job_id = f"MERC-{ulid.ulid()}"
    address_label = f"{payload.address_line_1}, {payload.city} {payload.state} {payload.zip_code}"

    try:
        client_secret = create_t3_payment_intent(
            job_id=job_id,
            customer_email=str(payload.customer_email),
            specialty_name=payload.specialty_name,
            address_label=address_label,
            cpt_codes=payload.cpt_codes,
        )
    except Exception as exc:
        logging.error("Failed to create T3 Stripe PaymentIntent: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to create payment session") from exc

    pre_payload_json = json.dumps(
        {
            "report_type": "t3",
            "specialty_name": payload.specialty_name,
            "address_line_1": payload.address_line_1,
            "address_line_2": payload.address_line_2,
            "city": payload.city,
            "state": payload.state,
            "zip_code": payload.zip_code,
            "drive_time_minutes": payload.drive_time_minutes,
            "customer_email": str(payload.customer_email),
            "payment_intent_id": "pending",
            "cpt_codes": payload.cpt_codes,
        }
    )

    try:
        create_job_awaiting_payment(
            job_id=job_id,
            payload_json=pre_payload_json,
            specialty_name=payload.specialty_name,
            provider_name=address_label,
        )
    except JobAlreadyExistsError:
        logging.error("job_id collision at T3 intent creation: %s", job_id)
        raise HTTPException(status_code=500, detail="Failed to initialize job") from None

    return {"client_secret": client_secret, "job_id": job_id}
