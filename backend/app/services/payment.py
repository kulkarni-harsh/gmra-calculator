import logging

import stripe

from app.core.config import settings

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
REPORT_AMOUNT_CENTS = 50_000  # $500.00


def create_payment_intent(
    *,
    job_id: str,
    customer_email: str,
    provider_name: str,
    specialty_name: str,
) -> str:
    """Create a Stripe PaymentIntent for $500. Returns the client_secret."""
    intent = stripe.PaymentIntent.create(
        amount=REPORT_AMOUNT_CENTS,
        currency="usd",
        receipt_email=customer_email,
        payment_method_types=["card"],
        metadata={
            "job_id": job_id,
            "customer_email": customer_email,
            "provider_name": provider_name,
            "specialty_name": specialty_name,
        },
    )
    return intent.client_secret  # type: ignore[return-value]


def verify_payment_intent(
    *,
    payment_intent_id: str,
    expected_email: str,
) -> str:
    """
    Retrieve and verify the PaymentIntent.
    Returns the job_id from metadata on success.
    Raises ValueError with a human-readable message on any failure.
    """
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    except stripe.error.InvalidRequestError as exc:
        raise ValueError(f"Invalid PaymentIntent: {exc}") from exc
    except stripe.error.StripeError as exc:
        raise ValueError(f"Stripe error: {exc}") from exc

    if intent.status != "succeeded":
        raise ValueError(f"PaymentIntent status is '{intent.status}', expected 'succeeded'")

    if intent.amount != REPORT_AMOUNT_CENTS:
        raise ValueError(f"PaymentIntent amount is {intent.amount}, expected {REPORT_AMOUNT_CENTS}")

    metadata = intent.metadata or {}
    if metadata.get("customer_email", "").lower().strip() != expected_email.lower().strip():
        raise ValueError("PaymentIntent email does not match request email")

    job_id = metadata.get("job_id")
    if not job_id:
        raise ValueError("PaymentIntent metadata missing job_id")

    return job_id
