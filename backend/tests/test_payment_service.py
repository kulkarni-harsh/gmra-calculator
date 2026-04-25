"""Unit tests for app.services.payment — price constants + Stripe wrappers (mocked)."""

from unittest.mock import MagicMock, patch
import pytest


def test_price_constants_are_consistent():
    from app.services.payment import (
        A1_DISPLAY_PRICE,
        REPORT_AMOUNT_CENTS,
        REPORT_TYPE_AMOUNTS,
        T1_DISPLAY_PRICE,
        T1_REPORT_AMOUNT_CENTS,
        T2_DISPLAY_PRICE,
        T2_REPORT_AMOUNT_CENTS,
        T3_DISPLAY_PRICE,
        T3_REPORT_AMOUNT_CENTS,
        T4_DISPLAY_PRICE,
        T4_REPORT_AMOUNT_CENTS,
    )

    assert REPORT_AMOUNT_CENTS == 50_000
    assert T1_REPORT_AMOUNT_CENTS == 39_900
    assert T2_REPORT_AMOUNT_CENTS == 49_900
    assert T3_REPORT_AMOUNT_CENTS == 59_900
    assert T4_REPORT_AMOUNT_CENTS == 79_900
    assert A1_DISPLAY_PRICE == "$500"
    assert T1_DISPLAY_PRICE == "$399"
    assert T2_DISPLAY_PRICE == "$499"
    assert T3_DISPLAY_PRICE == "$599"
    assert T4_DISPLAY_PRICE == "$799"
    assert REPORT_TYPE_AMOUNTS == {
        "a1": REPORT_AMOUNT_CENTS,
        "t1": T1_REPORT_AMOUNT_CENTS,
        "t2": T2_REPORT_AMOUNT_CENTS,
        "t3": T3_REPORT_AMOUNT_CENTS,
        "t4": T4_REPORT_AMOUNT_CENTS,
    }


def test_create_payment_intent_passes_amount_and_metadata():
    fake_intent = MagicMock(client_secret="cs_test_123")
    with patch("app.services.payment.stripe.PaymentIntent.create", return_value=fake_intent) as m:
        from app.services.payment import create_payment_intent

        cs = create_payment_intent(
            job_id="MERC-1",
            customer_email="x@y.com",
            provider_name="Dr A",
            specialty_name="Family Medicine",
        )
    assert cs == "cs_test_123"
    kwargs = m.call_args.kwargs
    assert kwargs["amount"] == 50_000
    assert kwargs["currency"] == "usd"
    assert kwargs["metadata"]["job_id"] == "MERC-1"


def test_create_t1_payment_intent_uses_399_amount_and_t1_metadata():
    fake_intent = MagicMock(client_secret="cs_t1")
    with patch("app.services.payment.stripe.PaymentIntent.create", return_value=fake_intent) as m:
        from app.services.payment import create_t1_payment_intent

        cs = create_t1_payment_intent(
            job_id="MERC-2",
            customer_email="x@y.com",
            specialty_name="FM",
            address_label="123 Main",
        )
    assert cs == "cs_t1"
    kwargs = m.call_args.kwargs
    assert kwargs["amount"] == 39_900
    assert kwargs["metadata"]["report_type"] == "t1"


def test_create_t2_payment_intent_uses_599_amount_and_serializes_cpt_codes():
    fake_intent = MagicMock(client_secret="cs_t2")
    with patch("app.services.payment.stripe.PaymentIntent.create", return_value=fake_intent) as m:
        from app.services.payment import create_t2_payment_intent

        cs = create_t2_payment_intent(
            job_id="MERC-3",
            customer_email="x@y.com",
            specialty_name="FM",
            address_label="123 Main",
            cpt_codes=["99213", "99214"],
        )
    assert cs == "cs_t2"
    kwargs = m.call_args.kwargs
    assert kwargs["amount"] == 49_900
    assert kwargs["metadata"]["cpt_codes"] == "99213,99214"
    assert kwargs["metadata"]["report_type"] == "t2"


def test_create_t2_payment_intent_no_cpt_codes_serializes_empty_string():
    fake_intent = MagicMock(client_secret="cs_t2_empty")
    with patch("app.services.payment.stripe.PaymentIntent.create", return_value=fake_intent) as m:
        from app.services.payment import create_t2_payment_intent

        cs = create_t2_payment_intent(
            job_id="MERC-4",
            customer_email="x@y.com",
            specialty_name="FM",
            address_label="123 Main",
        )
    assert cs == "cs_t2_empty"
    kwargs = m.call_args.kwargs
    assert kwargs["metadata"]["cpt_codes"] == ""


def test_verify_payment_intent_returns_job_id_on_success():
    fake_intent = MagicMock(
        status="succeeded",
        amount=50_000,
        metadata={"customer_email": "X@Y.com", "job_id": "MERC-9"},
    )
    with patch("app.services.payment.stripe.PaymentIntent.retrieve", return_value=fake_intent):
        from app.services.payment import verify_payment_intent

        out = verify_payment_intent(payment_intent_id="pi_1", expected_email="x@y.com")
    assert out == "MERC-9"


def test_verify_payment_intent_raises_on_wrong_status():
    fake_intent = MagicMock(
        status="processing",
        amount=50_000,
        metadata={"customer_email": "x@y.com", "job_id": "MERC-9"},
    )
    with patch("app.services.payment.stripe.PaymentIntent.retrieve", return_value=fake_intent):
        from app.services.payment import verify_payment_intent

        with pytest.raises(ValueError, match="processing"):
            verify_payment_intent(payment_intent_id="pi_1", expected_email="x@y.com")


def test_verify_payment_intent_raises_on_wrong_amount():
    fake_intent = MagicMock(
        status="succeeded",
        amount=10_000,
        metadata={"customer_email": "x@y.com", "job_id": "MERC-9"},
    )
    with patch("app.services.payment.stripe.PaymentIntent.retrieve", return_value=fake_intent):
        from app.services.payment import verify_payment_intent

        with pytest.raises(ValueError, match="amount"):
            verify_payment_intent(payment_intent_id="pi_1", expected_email="x@y.com")


def test_verify_payment_intent_raises_on_email_mismatch():
    fake_intent = MagicMock(
        status="succeeded",
        amount=50_000,
        metadata={"customer_email": "other@y.com", "job_id": "MERC-9"},
    )
    with patch("app.services.payment.stripe.PaymentIntent.retrieve", return_value=fake_intent):
        from app.services.payment import verify_payment_intent

        with pytest.raises(ValueError, match="email"):
            verify_payment_intent(payment_intent_id="pi_1", expected_email="x@y.com")


def test_verify_payment_intent_raises_when_metadata_missing_job_id():
    fake_intent = MagicMock(
        status="succeeded",
        amount=50_000,
        metadata={"customer_email": "x@y.com"},
    )
    with patch("app.services.payment.stripe.PaymentIntent.retrieve", return_value=fake_intent):
        from app.services.payment import verify_payment_intent

        with pytest.raises(ValueError, match="job_id"):
            verify_payment_intent(payment_intent_id="pi_1", expected_email="x@y.com")


def test_verify_payment_intent_raises_on_stripe_invalid_request_error():
    import stripe

    with patch(
        "app.services.payment.stripe.PaymentIntent.retrieve",
        side_effect=stripe.error.InvalidRequestError("No such payment_intent", param="id"),
    ):
        from app.services.payment import verify_payment_intent

        with pytest.raises(ValueError, match="Invalid PaymentIntent"):
            verify_payment_intent(payment_intent_id="pi_bad", expected_email="x@y.com")


def test_verify_payment_intent_raises_on_generic_stripe_error():
    import stripe

    with patch(
        "app.services.payment.stripe.PaymentIntent.retrieve",
        side_effect=stripe.error.StripeError("network failure"),
    ):
        from app.services.payment import verify_payment_intent

        with pytest.raises(ValueError, match="Stripe error"):
            verify_payment_intent(payment_intent_id="pi_bad", expected_email="x@y.com")


def test_verify_payment_intent_accepts_custom_expected_amount_for_t1():
    fake_intent = MagicMock(
        status="succeeded",
        amount=39_900,
        metadata={"customer_email": "x@y.com", "job_id": "MERC-T1"},
    )
    with patch("app.services.payment.stripe.PaymentIntent.retrieve", return_value=fake_intent):
        from app.services.payment import T1_REPORT_AMOUNT_CENTS, verify_payment_intent

        out = verify_payment_intent(
            payment_intent_id="pi_t1",
            expected_email="x@y.com",
            expected_amount=T1_REPORT_AMOUNT_CENTS,
        )
    assert out == "MERC-T1"
