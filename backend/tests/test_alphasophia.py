"""Unit tests for app.services.alphasophia helpers (httpx mocked)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


@pytest.mark.asyncio
async def test_get_npi_address_returns_none_for_none_npi():
    """get_npi_address must short-circuit on None without making any HTTP call."""
    from app.services.alphasophia import get_npi_address

    assert await get_npi_address(None) == (None, None, None)


@pytest.mark.asyncio
async def test_get_npi_address_returns_none_for_empty_string():
    """get_npi_address must short-circuit on empty string without making any HTTP call."""
    from app.services.alphasophia import get_npi_address

    assert await get_npi_address("") == (None, None, None)


@pytest.mark.asyncio
async def test_get_npi_address_returns_location_address():
    """get_npi_address picks the LOCATION address and returns (address_1, address_2, postal_code)."""
    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {
        "results": [
            {
                "addresses": [
                    {
                        "address_purpose": "MAILING",
                        "address_1": "PO Box 1",
                        "address_2": None,
                        "postal_code": "00000",
                    },
                    {
                        "address_purpose": "LOCATION",
                        "address_1": "1 Clinic Way",
                        "address_2": "Suite 200",
                        "postal_code": "94101",
                    },
                ]
            }
        ]
    }
    with patch("app.services.alphasophia._npi_client.get", new=AsyncMock(return_value=fake_response)):
        from app.services.alphasophia import get_npi_address

        addr = await get_npi_address("1234567890")

    assert addr == ("1 Clinic Way", "Suite 200", "94101")


@pytest.mark.asyncio
async def test_get_npi_address_returns_none_tuple_when_no_location_address():
    """get_npi_address returns (None, None, None) when only MAILING address is present."""
    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {
        "results": [
            {
                "addresses": [
                    {
                        "address_purpose": "MAILING",
                        "address_1": "PO Box",
                        "address_2": None,
                        "postal_code": "00000",
                    }
                ]
            }
        ]
    }
    with patch("app.services.alphasophia._npi_client.get", new=AsyncMock(return_value=fake_response)):
        from app.services.alphasophia import get_npi_address

        addr = await get_npi_address("1234567890")

    assert addr == (None, None, None)


@pytest.mark.asyncio
async def test_get_npi_address_swallows_timeout_and_returns_none():
    """get_npi_address must return (None, None, None) when all retry attempts time out.

    _fetch_npi_address retries 3 times on TimeoutException before reraising;
    we patch _fetch_npi_address directly to avoid the retry delay in tests.
    """
    with patch(
        "app.services.alphasophia._fetch_npi_address",
        new=AsyncMock(side_effect=httpx.TimeoutException("slow")),
    ):
        from app.services.alphasophia import get_npi_address

        addr = await get_npi_address("1234567890")

    assert addr == (None, None, None)


@pytest.mark.asyncio
async def test_get_npi_address_swallows_request_error_and_returns_none():
    """get_npi_address returns (None, None, None) on a network-level RequestError."""
    mock_request = MagicMock()
    with patch(
        "app.services.alphasophia._fetch_npi_address",
        new=AsyncMock(side_effect=httpx.RequestError("connection refused", request=mock_request)),
    ):
        from app.services.alphasophia import get_npi_address

        addr = await get_npi_address("1234567890")

    assert addr == (None, None, None)


@pytest.mark.asyncio
async def test_get_npi_address_swallows_http_status_error_and_returns_none():
    """get_npi_address returns (None, None, None) on a non-2xx HTTP response."""
    mock_request = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    with patch(
        "app.services.alphasophia._fetch_npi_address",
        new=AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "404 Not Found", request=mock_request, response=mock_resp
            )
        ),
    ):
        from app.services.alphasophia import get_npi_address

        addr = await get_npi_address("1234567890")

    assert addr == (None, None, None)


@pytest.mark.asyncio
async def test_get_npi_address_swallows_unexpected_exception_and_returns_none():
    """get_npi_address returns (None, None, None) on any unexpected exception."""
    with patch(
        "app.services.alphasophia._fetch_npi_address",
        new=AsyncMock(side_effect=ValueError("unexpected")),
    ):
        from app.services.alphasophia import get_npi_address

        addr = await get_npi_address("1234567890")

    assert addr == (None, None, None)
