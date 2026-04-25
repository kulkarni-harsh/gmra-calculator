"""Unit tests for app.services.geocoder — Mapbox geocode_address (httpx mocked)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.geocoder import geocode_address


@pytest.mark.asyncio
async def test_geocode_address_returns_lat_lon_on_success():
    """Happy path: API returns a single feature, expect (lat, lon) tuple."""
    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {"features": [{"center": [-122.4194, 37.7749]}]}

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)
    fake_client.get = AsyncMock(return_value=fake_response)

    with patch("app.services.geocoder.httpx.AsyncClient", return_value=fake_client):
        result = await geocode_address("123 Main St, SF, CA", api_key="mb_test")

    assert result == (37.7749, -122.4194)


@pytest.mark.asyncio
async def test_geocode_address_returns_none_when_no_features():
    """API returns an empty features list — expect None."""
    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {"features": []}

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)
    fake_client.get = AsyncMock(return_value=fake_response)

    with patch("app.services.geocoder.httpx.AsyncClient", return_value=fake_client):
        result = await geocode_address("nowhere", api_key="mb_test")

    assert result is None


@pytest.mark.asyncio
async def test_geocode_address_returns_none_without_api_key():
    """Empty api_key short-circuits before any HTTP call."""
    result = await geocode_address("any address", api_key="")
    assert result is None


@pytest.mark.asyncio
async def test_geocode_address_returns_none_on_http_error():
    """Any exception from httpx is caught and returns None."""
    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)
    fake_client.get = AsyncMock(side_effect=RuntimeError("network failure"))

    with patch("app.services.geocoder.httpx.AsyncClient", return_value=fake_client):
        result = await geocode_address("any address", api_key="mb_test")

    assert result is None


@pytest.mark.asyncio
async def test_geocode_address_returns_float_tuple():
    """Returned coordinates are floats, not raw JSON values."""
    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {"features": [{"center": ["-73.9857", "40.7484"]}]}

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)
    fake_client.get = AsyncMock(return_value=fake_response)

    with patch("app.services.geocoder.httpx.AsyncClient", return_value=fake_client):
        result = await geocode_address("Empire State Building, NY", api_key="mb_test")

    assert result is not None
    lat, lon = result
    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert lat == pytest.approx(40.7484)
    assert lon == pytest.approx(-73.9857)
