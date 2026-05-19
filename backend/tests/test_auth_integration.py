"""End-to-end auth wiring via the real app router."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import config as config_mod
from app.main import app

_FAKE_SPECIALTY_LOOKUP = {
    "fm": {
        "description": "Family Medicine",
        "taxonomy_codes": ["207Q00000X"],
        "google_places_keywords": ["family medicine"],
        "states": {"US": 50.0},
    },
}


@pytest.fixture
def auth_on(monkeypatch):
    monkeypatch.setattr(config_mod.settings, "AUTH_ENFORCED", True)
    monkeypatch.setattr(config_mod.settings, "API_KEY_WIX", "wix-key-abc")
    monkeypatch.setattr(config_mod.settings, "API_KEY_REACT", "react-key-xyz")
    monkeypatch.setattr(config_mod.settings, "INTERNAL_ORIGINS", "https://app.merc.com")
    # Pre-populate app state so endpoint handlers don't crash before auth is checked.
    # Use monkeypatch.setattr so the attribute is rolled back after each test.
    monkeypatch.setattr(app.state, "specialty_lookup", _FAKE_SPECIALTY_LOOKUP, raising=False)
    return config_mod.settings


@pytest.mark.integration
def test_health_open_without_key(auth_on):
    """Health endpoint stays open for ALB target group checks."""
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200


@pytest.mark.integration
def test_stripe_webhook_open_without_key(auth_on):
    """Stripe webhook uses its own signature auth, not API key."""
    client = TestClient(app)
    # Empty body / bad signature — but auth dependency should NOT reject before reaching the handler.
    r = client.post("/api/payments/webhook/stripe")
    assert r.status_code != 401  # may be 400 from Stripe sig validation, but not 401 from us


@pytest.mark.integration
def test_protected_endpoint_requires_key(auth_on):
    """A non-exempt endpoint returns 401 without auth."""
    client = TestClient(app)
    r = client.get("/api/providers/specialties")
    assert r.status_code == 401


@pytest.mark.integration
def test_protected_endpoint_accepts_wix_key(auth_on):
    client = TestClient(app)
    r = client.get("/api/providers/specialties", headers={"X-API-Key": "wix-key-abc"})
    assert r.status_code == 200


@pytest.mark.integration
def test_protected_endpoint_accepts_internal_origin(auth_on):
    client = TestClient(app)
    r = client.get("/api/providers/specialties", headers={"Origin": "https://app.merc.com"})
    assert r.status_code == 200
