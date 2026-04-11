import logging

import stripe

from app.core.config import settings

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

# ── Prices (cents) — change only here ────────────────────────────────────────
REPORT_AMOUNT_CENTS = 50_000     # A1  $500.00
T1_REPORT_AMOUNT_CENTS = 39_900  # T1  $399.00  Market Entry Report
T2_REPORT_AMOUNT_CENTS = 59_900  # T2  $599.00  Through-the-Door Codes Report

# Display strings derived from the cent constants above.
# Use these everywhere a human-readable price is needed (emails, report upgrades).
A1_DISPLAY_PRICE = f"${REPORT_AMOUNT_CENTS // 100:,}"      # "$500"
T1_DISPLAY_PRICE = f"${T1_REPORT_AMOUNT_CENTS // 100:,}"   # "$399"
T2_DISPLAY_PRICE = f"${T2_REPORT_AMOUNT_CENTS // 100:,}"   # "$599"
T3_DISPLAY_PRICE = "$799"  # Coming-soon tier — no PaymentIntent yet

# Lookup used by the Stripe webhook to verify the charged amount matches the job type.
REPORT_TYPE_AMOUNTS: dict[str, int] = {
    "a1": REPORT_AMOUNT_CENTS,
    "t1": T1_REPORT_AMOUNT_CENTS,
    "t2": T2_REPORT_AMOUNT_CENTS,
}


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


def create_t1_payment_intent(
    *,
    job_id: str,
    customer_email: str,
    specialty_name: str,
    address_label: str,  # e.g. "123 Main St, Austin TX 78701"
) -> str:
    """Create a Stripe PaymentIntent for the T1 Market Entry Report ($399). Returns client_secret."""
    intent = stripe.PaymentIntent.create(
        amount=T1_REPORT_AMOUNT_CENTS,
        currency="usd",
        receipt_email=customer_email,
        payment_method_types=["card"],
        metadata={
            "job_id": job_id,
            "customer_email": customer_email,
            "report_type": "t1",
            "provider_name": address_label,
            "specialty_name": specialty_name,
        },
    )
    return intent.client_secret  # type: ignore[return-value]


def create_t2_payment_intent(
    *,
    job_id: str,
    customer_email: str,
    specialty_name: str,
    address_label: str,
    cpt_codes: list[str] | None = None,
) -> str:
    """Create a Stripe PaymentIntent for the T2 Through-the-Door Codes Report ($599). Returns client_secret."""
    intent = stripe.PaymentIntent.create(
        amount=T2_REPORT_AMOUNT_CENTS,
        currency="usd",
        receipt_email=customer_email,
        payment_method_types=["card"],
        metadata={
            "job_id": job_id,
            "customer_email": customer_email,
            "report_type": "t2",
            "provider_name": address_label,
            "specialty_name": specialty_name,
            "cpt_codes": ",".join(cpt_codes) if cpt_codes else "",
        },
    )
    return intent.client_secret  # type: ignore[return-value]


def verify_payment_intent(
    *,
    payment_intent_id: str,
    expected_email: str,
    expected_amount: int = REPORT_AMOUNT_CENTS,  # caller passes T1_REPORT_AMOUNT_CENTS for T1, T2_REPORT_AMOUNT_CENTS for T2
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

    if intent.amount != expected_amount:
        raise ValueError(f"PaymentIntent amount is {intent.amount}, expected {expected_amount}")

    metadata = intent.metadata or {}
    if metadata.get("customer_email", "").lower().strip() != expected_email.lower().strip():
        raise ValueError("PaymentIntent email does not match request email")

    job_id = metadata.get("job_id")
    if not job_id:
        raise ValueError("PaymentIntent metadata missing job_id")

    return job_id
