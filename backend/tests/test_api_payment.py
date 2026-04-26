"""Integration tests for /api/payments/* endpoints."""

from unittest.mock import patch


def _client_provider_dict() -> dict:
    return {
        "id": 1,
        "npi": "1234567890",
        "name": "Dr A",
    }


def test_create_payment_intent_returns_client_secret_and_job_id(client):
    payload = {
        "specialty_name": "Family Medicine",
        "client_provider": _client_provider_dict(),
        "miles_radius": 5,
        "customer_email": "x@y.com",
        "provider_name": "Dr A",
    }
    with (
        patch("app.api.endpoints.payment.create_payment_intent", return_value="cs_test_a1"),
        patch("app.api.endpoints.payment.create_job_awaiting_payment"),
    ):
        r = client.post("/api/payments/create-payment-intent", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["client_secret"] == "cs_test_a1"
    assert body["job_id"].startswith("MREC-")


def test_create_payment_intent_502_when_stripe_fails(client):
    payload = {
        "specialty_name": "Family Medicine",
        "client_provider": _client_provider_dict(),
        "miles_radius": 5,
        "customer_email": "x@y.com",
        "provider_name": "Dr A",
    }
    with patch("app.api.endpoints.payment.create_payment_intent", side_effect=RuntimeError("Stripe down")):
        r = client.post("/api/payments/create-payment-intent", json=payload)
    assert r.status_code == 502


def test_create_t1_payment_intent_returns_client_secret(client):
    payload = {
        "specialty_name": "Family Medicine",
        "address_line_1": "1 Clinic Way",
        "address_line_2": "",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "drive_time_minutes": 30,
        "customer_email": "x@y.com",
    }
    with (
        patch("app.api.endpoints.payment.create_t1_payment_intent", return_value="cs_t1"),
        patch("app.api.endpoints.payment.create_job_awaiting_payment"),
    ):
        r = client.post("/api/payments/create-t1-payment-intent", json=payload)
    assert r.status_code == 200
    assert r.json()["client_secret"] == "cs_t1"


def test_create_t1_payment_intent_job_id_starts_with_merc(client):
    payload = {
        "specialty_name": "Cardiology",
        "address_line_1": "2 Heart Blvd",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75201",
        "drive_time_minutes": 15,
        "customer_email": "doc@example.com",
    }
    with (
        patch("app.api.endpoints.payment.create_t1_payment_intent", return_value="cs_t1b"),
        patch("app.api.endpoints.payment.create_job_awaiting_payment"),
    ):
        r = client.post("/api/payments/create-t1-payment-intent", json=payload)
    assert r.status_code == 200
    assert r.json()["job_id"].startswith("MREC-")


def test_create_t1_payment_intent_502_when_stripe_fails(client):
    payload = {
        "specialty_name": "Family Medicine",
        "address_line_1": "1 Clinic Way",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "drive_time_minutes": 30,
        "customer_email": "x@y.com",
    }
    with patch("app.api.endpoints.payment.create_t1_payment_intent", side_effect=RuntimeError("Stripe down")):
        r = client.post("/api/payments/create-t1-payment-intent", json=payload)
    assert r.status_code == 502


def test_create_t1_payment_intent_invalid_drive_time_422(client):
    payload = {
        "specialty_name": "Family Medicine",
        "address_line_1": "1 Clinic Way",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "drive_time_minutes": 99,
        "customer_email": "x@y.com",
    }
    r = client.post("/api/payments/create-t1-payment-intent", json=payload)
    assert r.status_code == 422


def test_create_t2_payment_intent_returns_client_secret(client):
    payload = {
        "specialty_name": "Family Medicine",
        "address_line_1": "1 Clinic Way",
        "address_line_2": "",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "drive_time_minutes": 30,
        "customer_email": "x@y.com",
        "cpt_codes": ["99213", "99214"],
    }
    with (
        patch("app.api.endpoints.payment.create_t2_payment_intent", return_value="cs_t2"),
        patch("app.api.endpoints.payment.create_job_awaiting_payment"),
    ):
        r = client.post("/api/payments/create-t2-payment-intent", json=payload)
    assert r.status_code == 200
    assert r.json()["client_secret"] == "cs_t2"


def test_create_t2_payment_intent_job_id_starts_with_merc(client):
    payload = {
        "specialty_name": "Neurology",
        "address_line_1": "3 Brain Ave",
        "city": "Houston",
        "state": "TX",
        "zip_code": "77001",
        "drive_time_minutes": 45,
        "customer_email": "neuro@example.com",
        "cpt_codes": ["99215"],
    }
    with (
        patch("app.api.endpoints.payment.create_t2_payment_intent", return_value="cs_t2b"),
        patch("app.api.endpoints.payment.create_job_awaiting_payment"),
    ):
        r = client.post("/api/payments/create-t2-payment-intent", json=payload)
    assert r.status_code == 200
    assert r.json()["job_id"].startswith("MREC-")


def test_create_t2_payment_intent_502_when_stripe_fails(client):
    payload = {
        "specialty_name": "Family Medicine",
        "address_line_1": "1 Clinic Way",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "drive_time_minutes": 30,
        "customer_email": "x@y.com",
        "cpt_codes": ["99213"],
    }
    with patch("app.api.endpoints.payment.create_t2_payment_intent", side_effect=RuntimeError("Stripe down")):
        r = client.post("/api/payments/create-t2-payment-intent", json=payload)
    assert r.status_code == 502


def test_create_t2_payment_intent_empty_cpt_codes_422(client):
    payload = {
        "specialty_name": "Family Medicine",
        "address_line_1": "1 Clinic Way",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "drive_time_minutes": 30,
        "customer_email": "x@y.com",
        "cpt_codes": [],
    }
    r = client.post("/api/payments/create-t2-payment-intent", json=payload)
    assert r.status_code == 422


def test_stripe_webhook_invalid_signature_400(client):
    import stripe

    with patch(
        "app.api.endpoints.payment.stripe.Webhook.construct_event",
        side_effect=stripe.error.SignatureVerificationError("bad sig", "raw"),
    ):
        r = client.post(
            "/api/payments/webhook/stripe",
            content=b"{}",
            headers={"stripe-signature": "bad"},
        )
    assert r.status_code == 400


def test_stripe_webhook_returns_received_for_unknown_event(client):
    event = {
        "type": "customer.created",
        "data": {"object": {}},
    }
    with patch(
        "app.api.endpoints.payment.stripe.Webhook.construct_event",
        return_value=event,
    ):
        r = client.post(
            "/api/payments/webhook/stripe",
            content=b"{}",
            headers={"stripe-signature": "ok"},
        )
    assert r.status_code == 200
    assert r.json() == {"received": True}


def test_stripe_webhook_enqueues_job_on_payment_intent_succeeded(client):
    event = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test",
                "metadata": {"job_id": "MREC-TEST"},
                "amount": 50000,
            }
        },
    }
    stored_payload = (
        '{"report_type": "a1", "specialty_name": "Family Medicine", '
        '"client_provider": {"id": 1, "npi": "1234567890", "name": "Dr A"}, '
        '"customer_email": "x@y.com", "payment_intent_id": "pending"}'
    )
    with (
        patch(
            "app.api.endpoints.payment.stripe.Webhook.construct_event",
            return_value=event,
        ),
        patch(
            "app.api.endpoints.payment.claim_job_for_generation",
            return_value=stored_payload,
        ),
        patch("app.api.endpoints.payment.send_job") as mock_send_job,
        patch("app.api.endpoints.payment.send_request_confirmation"),
    ):
        r = client.post(
            "/api/payments/webhook/stripe",
            content=b"{}",
            headers={"stripe-signature": "ok"},
        )
    assert r.status_code == 200
    assert r.json() == {"received": True}
    mock_send_job.assert_called_once_with("MREC-TEST")
