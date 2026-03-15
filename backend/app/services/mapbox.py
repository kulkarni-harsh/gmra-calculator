import logging
from functools import lru_cache
from urllib.parse import quote

import requests

from app.core.config import settings


@lru_cache(maxsize=20000)
def get_location_coordinates(address: str) -> tuple[float, float]:
    """
    Retrieve the latitude and longitude coordinates for a given address.

    Args
    ----
        address (str): The address for which to retrieve coordinates.

    Returns
    -------
        tuple[float, float]: A tuple containing the latitude and longitude.
    """
    address = (address or "").strip()
    if not address:
        raise ValueError("Address is required for geocoding.")

    encoded_address = quote(address, safe="")
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_address}.json"
    params: dict[str, str | int] = {
        "limit": 1,
        "access_token": settings.MAPBOX_API_KEY,
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    if not data.get("features"):
        raise ValueError(f"No coordinates found for address: {address}")

    long, lat = data["features"][0]["center"]  # [longitude, latitude]
    return lat, long


@lru_cache(maxsize=20000)
def get_drive_distance_time(lat1: float, long1: float, lat2: float, long2: float) -> tuple[float, float]:
    """
    Calculate the driving distance and time between two geographic coordinates using the Mapbox Directions API.

    Args
    ----
        lat1 (float): Latitude of the starting point.
        long1 (float): Longitude of the starting point.
        lat2 (float): Latitude of the destination point.
        long2 (float): Longitude of the destination point.

    Returns
    -------
        tuple[float, float]: A tuple containing the driving distance in miles and the driving time in minutes.
    """
    if not all([isinstance(coord, int | float) for coord in [lat1, long1, lat2, long2]]):
        logging.error("All coordinates must be numeric values.")
        return 10e9, 10e9  # Return large values to indicate an error
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{long1},{lat1};{long2},{lat2}"

    params = {"access_token": settings.MAPBOX_API_KEY, "overview": "false"}

    response = requests.get(url, params=params)
    data = response.json()

    route = data["routes"][0]

    distance_meters = route["distance"]
    duration_seconds = route["duration"]

    distance_miles = distance_meters * 0.000621371
    duration_minutes = duration_seconds / 60

    return distance_miles, duration_minutes
