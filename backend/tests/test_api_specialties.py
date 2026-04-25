"""Integration tests for /api/providers/* endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

_FAKE_SPECIALTY_LOOKUP = {
    "fm": {
        "description": "Family Medicine",
        "taxonomy_codes": ["207Q00000X"],
        "google_places_keywords": ["family medicine"],
        "states": {"US": 50.0, "CA": 60.0},
    },
    "no_density": {
        "description": "Made Up",
        "taxonomy_codes": [],
        "google_places_keywords": [],
        # no "states" key — should be filtered out of /specialties
    },
}


@pytest.fixture
def client_with_specialty_lookup() -> TestClient:
    """Return a TestClient whose app.state has a controlled specialty_lookup."""
    from app.main import app

    app.state.specialty_lookup = _FAKE_SPECIALTY_LOOKUP
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /api/providers/specialties
# ---------------------------------------------------------------------------


def test_list_specialties_returns_only_specialties_with_density(client_with_specialty_lookup):
    """Specialties without a 'states' key must be excluded from the response."""
    r = client_with_specialty_lookup.get("/api/providers/specialties")
    assert r.status_code == 200
    descriptions = [s["description"] for s in r.json()]
    assert "Family Medicine" in descriptions
    assert "Made Up" not in descriptions


def test_list_specialties_includes_national_density(client_with_specialty_lookup):
    """Each returned specialty must carry national_density and taxonomy_codes."""
    r = client_with_specialty_lookup.get("/api/providers/specialties")
    fm = next(s for s in r.json() if s["description"] == "Family Medicine")
    assert fm["national_density"] == 50.0
    assert fm["taxonomy_codes"] == ["207Q00000X"]


def test_list_specialties_includes_id_field(client_with_specialty_lookup):
    """Each returned specialty must include the lookup key as 'id'."""
    r = client_with_specialty_lookup.get("/api/providers/specialties")
    fm = next(s for s in r.json() if s["description"] == "Family Medicine")
    assert fm["id"] == "fm"


# ---------------------------------------------------------------------------
# GET /api/providers/search-providers
# ---------------------------------------------------------------------------


def test_search_providers_returns_empty_when_no_taxonomy(client_with_specialty_lookup):
    """Unknown specialty (no taxonomy codes) must return an empty list, not an error."""
    r = client_with_specialty_lookup.get(
        "/api/providers/search-providers",
        params={"zip_code": "94101", "specialty_name": "Made Up"},
    )
    assert r.status_code == 200
    assert r.json() == []


def test_search_providers_calls_alphasophia_and_returns_dump(client_with_specialty_lookup):
    """A valid specialty with taxonomy codes must call AlphaSophia and serialise providers."""
    from app.types.alphasophia import Provider

    fake_provider = Provider(id=1, npi="1234567890", name="Dr A")
    with patch(
        "app.api.endpoints.providers.get_hcp_data",
        new=AsyncMock(return_value=[fake_provider]),
    ):
        r = client_with_specialty_lookup.get(
            "/api/providers/search-providers",
            params={"zip_code": "94101", "specialty_name": "Family Medicine"},
        )
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["npi"] == "1234567890"


def test_search_providers_returns_empty_on_alphasophia_error(client_with_specialty_lookup):
    """AlphaSophia errors must be swallowed and return an empty list."""
    with patch(
        "app.api.endpoints.providers.get_hcp_data",
        new=AsyncMock(side_effect=RuntimeError("503")),
    ):
        r = client_with_specialty_lookup.get(
            "/api/providers/search-providers",
            params={"zip_code": "94101", "specialty_name": "Family Medicine"},
        )
    assert r.status_code == 200
    assert r.json() == []


def test_search_providers_filters_non_provider_items(client_with_specialty_lookup):
    """Non-Provider items returned by AlphaSophia must be silently dropped."""
    from app.types.alphasophia import Provider

    fake_provider = Provider(id=2, npi="0000000001", name="Dr B")
    mixed_return = [fake_provider, "not-a-provider", None]
    with patch(
        "app.api.endpoints.providers.get_hcp_data",
        new=AsyncMock(return_value=mixed_return),
    ):
        r = client_with_specialty_lookup.get(
            "/api/providers/search-providers",
            params={"zip_code": "94101", "specialty_name": "Family Medicine"},
        )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["npi"] == "0000000001"


# ---------------------------------------------------------------------------
# GET /api/providers/provider
# ---------------------------------------------------------------------------


def test_get_provider_returns_404_when_no_taxonomy(client_with_specialty_lookup):
    """Unknown specialty must respond with 404."""
    r = client_with_specialty_lookup.get(
        "/api/providers/provider",
        params={"zip_code": "94101", "npi": "1234567890", "specialty_name": "Made Up"},
    )
    assert r.status_code == 404


def test_get_provider_returns_provider_when_match(client_with_specialty_lookup):
    """When AlphaSophia returns the matching NPI the endpoint must return 200 with provider data."""
    from app.types.alphasophia import Provider

    fake = Provider(id=1, npi="1234567890", name="Dr A")
    with patch(
        "app.api.endpoints.providers.get_hcp_data",
        new=AsyncMock(return_value=[fake]),
    ):
        r = client_with_specialty_lookup.get(
            "/api/providers/provider",
            params={"zip_code": "94101", "npi": "1234567890", "specialty_name": "Family Medicine"},
        )
    assert r.status_code == 200
    assert r.json()["npi"] == "1234567890"


def test_get_provider_returns_404_when_npi_not_found(client_with_specialty_lookup):
    """When no provider matches the requested NPI, the endpoint must return 404."""
    with patch(
        "app.api.endpoints.providers.get_hcp_data",
        new=AsyncMock(return_value=[]),
    ):
        r = client_with_specialty_lookup.get(
            "/api/providers/provider",
            params={"zip_code": "94101", "npi": "9999999999", "specialty_name": "Family Medicine"},
        )
    assert r.status_code == 404


def test_get_provider_returns_502_on_alphasophia_error(client_with_specialty_lookup):
    """AlphaSophia errors on single-provider lookup must return 502, not 500."""
    with patch(
        "app.api.endpoints.providers.get_hcp_data",
        new=AsyncMock(side_effect=RuntimeError("connection refused")),
    ):
        r = client_with_specialty_lookup.get(
            "/api/providers/provider",
            params={"zip_code": "94101", "npi": "1234567890", "specialty_name": "Family Medicine"},
        )
    assert r.status_code == 502
