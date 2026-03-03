import re
from functools import lru_cache

import pandas as pd
from geopy.distance import geodesic
from tqdm import tqdm

tqdm.pandas()


def normalize_street(address):
    """Normalize the street address by removing suite, unit, apartment, room, building information."""
    if not isinstance(address, str):
        return None

    return re.sub(
        r"\b(Suite|Ste|Unit|#|Floor|Fl|Apt|Apartment|Room|Rm|Bldg|Building)\b.*",
        "",
        address,
        flags=re.IGNORECASE,
    ).strip()


@lru_cache(maxsize=20000)
def get_location_coordinates(
    geocoder_client, address_line_1: str, city: str, state: str, zip_code: str
) -> tuple[float, float]:
    """Get latitude and longitude for a given address using the geocoder client."""
    street = normalize_street(address_line_1)
    zip_code = str(zip_code).removesuffix(".0")

    full_address = f"{street}, {city}, {state} {zip_code}, USA"
    location_results = geocoder_client.geocode(full_address)

    if location_results:
        return location_results[0]["geometry"]["lat"], location_results[0]["geometry"]["lng"]
    raise ValueError("Geocoding failed for:", [address_line_1, street, city, state, zip_code])


def geocode_addresses(df: pd.DataFrame, geocoder_client) -> pd.DataFrame:
    """Geocode addresses in the DataFrame and add latitude and longitude columns."""
    df[["latitude", "longitude"]] = df.progress_apply(
        lambda row: pd.Series(
            get_location_coordinates(
                geocoder_client,
                str(row["Primary Practice First Line"]),
                str(row["Primary Practice City"]),
                str(row["Primary Practice State"]),
                str(row["Primary Practice ZIP"]),
            )
        ),
        axis=1,
    )
    return df


def calculate_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float | None:
    # Use geopy's geodesic method to calculate the distance
    if any([pd.isnull(x) for x in [lat1, lon1, lat2, lon2]]):
        return None
    # if len(filter(lambda x: pd.isnull(x), [lat1, lon1, lat2, lon2])):

    point1 = (lat1, lon1)
    point2 = (lat2, lon2)
    distance = geodesic(point1, point2).miles
    return distance


def zips_within_radius_geopy(
    lat: float, lon: float, radius_miles: float, centroids_df: pd.DataFrame
) -> dict[str, float]:
    """
    Find zip codes within a specified radius (in miles) from a given latitude and longitude using geopy

    Args
    ----
        lat (float): Latitude of the center point.
        lon (float): Longitude of the center point.
        radius_miles (float): Radius in miles to search for zip codes.
        centroids_df (pd.DataFrame): DataFrame containing zip code centroids with columns 'zip', 'lat', and 'lon'.

    Returns
    -------
        dict[str, float]: A dictionary where keys are zip codes and values are distances in miles.
    """
    center = (lat, lon)
    result = {}

    for _, row in centroids_df.iterrows():
        dist = geodesic(center, (row["lat"], row["lon"])).miles
        if dist <= radius_miles:
            result[row["zip"]] = dist

    return result
