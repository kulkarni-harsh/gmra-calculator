import json
import math
import time

import requests

from app.core.config import settings
from app.services.geocoding import calculate_distance_miles
from app.types.alphasophia import Provider
from app.types.cpt import CPT
from app.types.google_maps import GooglePlace, SiteOfCare

# Google Places Nearby Search API hard cap is 50,000 m ≈ 31.07 miles.
# Requests with a larger radius are silently clamped to this value.
_MAX_API_RADIUS_MILES = 15


def find_nearby_google_places(
    source_longitude: float,
    source_latitude: float,
    keywords: list[str],
    radius_miles: float = 3.0,
    dedup_threshold_miles: float = 0.03,  # ~50m in miles
) -> list[GooglePlace]:
    tile_radius = min(radius_miles, _MAX_API_RADIUS_MILES)

    if radius_miles <= _MAX_API_RADIUS_MILES:
        tile_centers = [(source_latitude, source_longitude)]
    else:
        tile_centers = _generate_tile_centers(
            source_latitude, source_longitude, radius_miles, tile_radius
        )

    raw_results: list[dict] = []
    for keyword in keywords:
        for lat, lon in tile_centers:
            raw_results.extend(_fetch_places_raw(lat, lon, tile_radius, keyword))

    parsed: list[GooglePlace] = []
    for place in raw_results:
        try:
            parsed.append(
                GooglePlace(
                    name=place["name"],
                    vicinity=place.get("vicinity", "N/A"),
                    latitude=place["geometry"]["location"]["lat"],
                    longitude=place["geometry"]["location"]["lng"],
                    phone=_normalize_phone(place.get("international_phone_number", "")),
                    place_id=place.get("place_id", ""),
                )
            )
        except Exception as e:
            print(f"Skipping place '{place.get('name', '?')}': {e}")

    # Filter to the actual requested radius (tiles may have fetched places outside it)
    parsed = [
        p for p in parsed
        if p.latitude is not None
        and p.longitude is not None
        and (
            calculate_distance_miles(source_latitude, source_longitude, p.latitude, p.longitude) or 0
        ) <= radius_miles
    ]

    # with open("debug_google_places.json", "w") as f:
    #     f.write(json.dumps([p.model_dump() for p in parsed], indent=2))

    deduped = _dedup_google_places(parsed, dedup_threshold_miles)

    # with open("debug_google_places_deduped.json", "w") as f:
    #     f.write(json.dumps([p.model_dump() for p in deduped], indent=2))

    return deduped


def _fetch_places_raw(
    lat: float,
    lon: float,
    radius_miles: float,
    specialty_type: str,
) -> list[dict]:
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params: dict[str, str | int] = {
        "location": f"{lat},{lon}",
        "radius": int(min(radius_miles, _MAX_API_RADIUS_MILES) * 1609.34),
        "keyword": specialty_type,
        "key": settings.GOOGLE_API_KEY,
    }

    results: list[dict] = []
    while True:
        response = requests.get(url, params=params)
        data = response.json()
        results.extend(data.get("results", []))

        next_token = data.get("next_page_token")
        if not next_token:
            break
        time.sleep(2)
        params = {"pagetoken": next_token, "key": settings.GOOGLE_API_KEY}

    return results


def _generate_tile_centers(
    center_lat: float,
    center_lon: float,
    total_radius_miles: float,
    tile_radius_miles: float,
) -> list[tuple[float, float]]:
    """
    Return a rectangular grid of (lat, lon) points that collectively cover
    a circle of `total_radius_miles`. Grid spacing is set so adjacent tiles
    overlap enough to guarantee no gaps.
    """
    # sqrt(2) spacing ensures square grid cells are fully covered by circles.
    spacing_miles = tile_radius_miles * math.sqrt(2)

    miles_per_deg_lat = 69.0
    miles_per_deg_lon = 69.0 * math.cos(math.radians(center_lat))

    steps = math.ceil(total_radius_miles / spacing_miles)

    centers: list[tuple[float, float]] = []
    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            lat = center_lat + (i * spacing_miles) / miles_per_deg_lat
            lon = center_lon + (j * spacing_miles) / miles_per_deg_lon
            dist = calculate_distance_miles(center_lat, center_lon, lat, lon) or 0
            if dist <= total_radius_miles:
                centers.append((lat, lon))

    return centers


def _normalize_phone(phone: str) -> str:
    digits = "".join(filter(str.isdigit, phone))
    return digits[-10:] if len(digits) >= 10 else ""


def _dedup_google_places(
    google_places: list[GooglePlace],
    threshold_miles: float,
) -> list[GooglePlace]:
    canonical_list = []
    used: set[int] = set()

    for i, place in enumerate(google_places):
        if i in used:
            continue

        used.add(i)

        for j, other in enumerate(google_places):
            if j in used:
                continue

            if (
                place.latitude is not None
                and place.longitude is not None
                and other.latitude is not None
                and other.longitude is not None
            ):
                dist_miles = calculate_distance_miles(
                    lat1=place.latitude, lon1=place.longitude,
                    lat2=other.latitude, lon2=other.longitude,
                )
            else:
                dist_miles = None

            # NOTE: There were instances where two far-apart hospitals had the same phone number,
            # so we intentionally do NOT dedup by phone alone — only by proximity.
            if dist_miles is not None and dist_miles <= threshold_miles:
                used.add(j)

        canonical_list.append(place)

    return canonical_list


def get_sites_of_care_list(providers_list: list[Provider]) -> list[SiteOfCare]:
    place_id_site_of_care_map: dict[str, SiteOfCare] = {}
    for i in providers_list:
        if i.nearest_google_place:
            if i.nearest_google_place.place_id not in place_id_site_of_care_map:
                place_id_site_of_care_map[i.nearest_google_place.place_id] = SiteOfCare(
                    **i.nearest_google_place.model_dump(),
                    is_locum=False,
                    distance_from_source_miles=i.distance_from_source_miles,
                    drive_time_minutes=i.drive_time_minutes,
                    cpt_list=i.cpt_list,
                    npi_list=[i.npi] if i.npi else [],
                    taxonomy=i.taxonomy,
                    location=i.location,
                )
            else:
                existing_site = place_id_site_of_care_map[i.nearest_google_place.place_id]
                existing_site.cpt_list = CPT.merge_lists(existing_site.cpt_list, i.cpt_list)
                if i.npi:
                    existing_site.npi_list.append(i.npi)
        else:
            locum_site_of_care = SiteOfCare(
                place_id=f"locum_{i.npi}",
                name=i.name,
                npi_list=[i.npi] if i.npi else [],
                vicinity=i.location.address_line_1,
                latitude=i.latitude,
                longitude=i.longitude,
                phone=None,
                is_locum=True,
                distance_from_source_miles=i.distance_from_source_miles,
                drive_time_minutes=i.drive_time_minutes,
                cpt_list=i.cpt_list,
                taxonomy=i.taxonomy,
                location=i.location,
            )
            place_id_site_of_care_map[f"locum_{i.npi}"] = locum_site_of_care

    return list(place_id_site_of_care_map.values())
