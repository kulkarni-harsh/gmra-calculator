import json
import logging
import uuid

import stripe
from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.schemas.payment import CreatePaymentIntentRequest
from app.services.email import send_request_confirmation
from app.services.job_store import JobAlreadyExistsError, claim_job_for_generation, create_job_awaiting_payment
from app.services.payment import create_payment_intent
from app.services.queue import send_job

router = APIRouter()


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


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    Processes payment_intent.succeeded for async payment methods (3DS, bank redirects).
    Must be registered in Stripe dashboard pointing to POST /api/webhook/stripe.
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
            # T0 stores address instead of client_provider
            if stored.get("report_type") == "t0":
                provider_name = f"{stored.get('address_line_1', '')}, {stored.get('city', '')} {stored.get('state', '')}"
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
