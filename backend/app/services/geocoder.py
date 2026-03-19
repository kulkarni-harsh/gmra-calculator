"""Address geocoding using the Mapbox Geocoding API (v5)."""

import logging
import urllib.parse

import httpx

logger = logging.getLogger(__name__)


async def geocode_address(address: str, api_key: str) -> tuple[float, float] | None:
    """
    Geocode a free-form address string to (latitude, longitude).

    Returns None if geocoding fails or returns no results.
    """
    if not api_key:
        logger.warning("geocode_address: MAPBOX_API_KEY is not set — cannot geocode")
        return None

    encoded = urllib.parse.quote(address, safe="")
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded}.json"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                url,
                params={
                    "access_token": api_key,
                    "limit": 1,
                    "country": "US",
                    "types": "address",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])
            if not features:
                logger.warning("geocode_address: no results for '%s'", address)
                return None
            lon, lat = features[0]["center"]
            return float(lat), float(lon)
    except Exception as exc:
        logger.error("geocode_address failed for '%s': %s", address, exc)
        return None
