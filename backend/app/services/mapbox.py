"""
mapbox_isochrones.py
--------------------
Generates a Mapbox-based static PNG map with:
  - Drive-time isochrones from a source location
  - Source and provider markers
  - Provider highlighting based on isochrone containment
  - Optional address geocoding via Mapbox Geocoding API
  - Static PNG output via Mapbox Static Images API (for PDF embedding)

Requirements:
    pip install requests shapely polyline
"""

import copy
import json
import math
import os
import urllib.parse
from functools import lru_cache
from io import BytesIO

import matplotlib

matplotlib.use("agg")
import contextily as ctx
import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import requests
from loguru import logger
from shapely.geometry import Point, shape
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings

_MAPBOX_TIMEOUT = (10, 20)  # (connect, read)


@retry(
    retry=retry_if_exception_type(requests.exceptions.Timeout),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _fetch_location_coordinates(address: str) -> tuple[float, float]:
    encoded_address = urllib.parse.quote(address, safe="")
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_address}.json"
    params: dict[str, str | int] = {
        "limit": 1,
        "access_token": settings.MAPBOX_API_KEY,
    }
    response = requests.get(url, params=params, timeout=_MAPBOX_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    if not data.get("features"):
        raise ValueError(f"No coordinates found for address: {address}")

    long, lat = data["features"][0]["center"]  # [longitude, latitude]
    return lat, long


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
    return _fetch_location_coordinates(address)


@retry(
    retry=retry_if_exception_type(requests.exceptions.Timeout),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _fetch_drive_distance_time(lat1: float, long1: float, lat2: float, long2: float) -> tuple[float, float]:
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{long1},{lat1};{long2},{lat2}"
    params = {"access_token": settings.MAPBOX_API_KEY, "overview": "false"}
    response = requests.get(url, params=params, timeout=_MAPBOX_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    route = data["routes"][0]
    distance_miles = route["distance"] * 0.000621371
    duration_minutes = route["duration"] / 60
    return distance_miles, duration_minutes


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
        logger.error("All coordinates must be numeric values.")
        return 10e9, 10e9  # Return large values to indicate an error
    return _fetch_drive_distance_time(lat1, long1, lat2, long2)


# ── Geocoding ─────────────────────────────────────────────────────────────────
@retry(
    retry=retry_if_exception_type(requests.exceptions.Timeout),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def geocode_address(address: str, token: str) -> tuple[float, float]:
    """Convert a free-text address to (lat, lon) using Mapbox Geocoding API."""
    encoded = urllib.parse.quote(address)
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded}.json?access_token={token}&limit=1"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    features = resp.json().get("features", [])
    if not features:
        raise ValueError(f"Geocoding returned no results for: {address!r}")
    lon, lat = features[0]["geometry"]["coordinates"]
    return lat, lon


# ── Contour calculation ───────────────────────────────────────────────────────


def calculate_contour_minutes(
    source_lat: float,
    source_lon: float,
    providers: list[tuple[float, float]],
    token: str,
    profile: str = "driving",
) -> list[int]:
    """
    Automatically calculate isochrone contour intervals based on the
    drive time from source to the furthest provider.

    - Calls the Mapbox Matrix API to get driving durations to all providers.
    - Finds the maximum duration and rounds up to the nearest 5 minutes.
    - Returns a list of [5, 10, 15, ..., max_rounded] in 5-minute steps.
    """
    const_max_destinations = 24
    coordinates = [(source_lon, source_lat)] + [(lon, lat) for lat, lon in providers]
    max_duration_seconds = 0

    for i in range(1, len(coordinates), const_max_destinations):
        batch = [coordinates[0]] + coordinates[i : i + const_max_destinations]
        coords_str = ";".join(f"{lon},{lat}" for lon, lat in batch)
        sources_str = "0"
        destinations_str = ";".join(str(j) for j in range(1, len(batch)))

        url = (
            f"https://api.mapbox.com/directions-matrix/v1/mapbox/{profile}"
            f"/{coords_str}"
            f"?sources={sources_str}"
            f"&destinations={destinations_str}"
            f"&annotations=duration"
            f"&access_token={token}"
        )
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        durations = resp.json().get("durations", [[]])[0]
        valid = [d for d in durations if d is not None]
        if valid:
            max_duration_seconds = max(max_duration_seconds, max(valid))

    if max_duration_seconds == 0:
        raise ValueError("Matrix API returned no valid durations.")

    max_minutes = math.ceil(max_duration_seconds / 60)
    max_rounded = math.ceil(max_minutes / 5) * 5
    max_rounded = min(max_rounded, 60)

    contours = list(range(5, max_rounded + 1, 5))

    if len(contours) > 4:
        contours.pop(1)

    logger.info(f"Furthest provider: {max_minutes} min → rounded to {max_rounded} min. Contours: {contours}")
    return contours


# ── Isochrone fetching ────────────────────────────────────────────────────────


@lru_cache(maxsize=512)
def _fetch_isochrones_raw(
    lat: float,
    lon: float,
    token: str,
    minutes: tuple[int, ...],
    profile: str = "driving",
) -> dict:
    """
    Cached raw fetch from the Mapbox Isochrone API.
    Keyed on (lat, lon, minutes, profile) — same inputs always return the
    same polygons for the lifetime of the process, preventing shape drift
    between calls within a single report or across back-to-back reports.
    Returns {minute: GeoJSON Feature}.
    """
    const_batch_size = 4
    sorted_minutes = sorted(minutes)
    batches = [sorted_minutes[i : i + const_batch_size] for i in range(0, len(sorted_minutes), const_batch_size)]
    by_minute = {}
    for batch in batches:
        contours_param = ",".join(str(m) for m in batch)
        url = (
            f"https://api.mapbox.com/isochrone/v1/mapbox/{profile}"
            f"/{lon},{lat}"
            f"?contours_minutes={contours_param}"
            f"&polygons=true"
            f"&denoise=1"
            f"&generalize=50"
            f"&access_token={token}"
        )
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        for feature in resp.json().get("features", []):
            minute = feature["properties"].get("contour")
            if minute is not None:
                by_minute[int(minute)] = feature
    return by_minute


def fetch_isochrones(
    lat: float,
    lon: float,
    token: str,
    minutes: list[int],
    profile: str = "driving",
    providers: tuple[tuple[float, float], ...] = (),
) -> dict:
    """
    Fetch drive-time isochrone polygons from the Mapbox Isochrone API.
    Automatically batches into requests of 4 (API hard limit).
    Returns {minute: GeoJSON Feature}.

    The raw API response is cached by (lat, lon, minutes, profile) so
    repeated calls with the same source and contours hit the cache instead
    of the network — guaranteeing polygon consistency across the report.

    If providers is given, any isochrone that does not uniquely contain
    at least one provider point (i.e. not already contained by a smaller
    isochrone) is removed from the result.
    """
    by_minute = dict(_fetch_isochrones_raw(lat, lon, token, tuple(sorted(minutes)), profile))

    if providers:
        shapely_isos = {m: shape(feat["geometry"]) for m, feat in sorted(by_minute.items())}

        unique_counts = {m: 0 for m in by_minute}
        for plat, plon in providers:
            point = Point(plon, plat)
            for minute in sorted(shapely_isos):
                if shapely_isos[minute].contains(point):
                    unique_counts[minute] += 1
                    break  # smallest zone wins

        before = set(by_minute.keys())
        by_minute = {m: feat for m, feat in by_minute.items() if unique_counts[m] > 0}
        removed = before - set(by_minute.keys())
        if removed:
            logger.info(f"  Removed empty isochrones: {sorted(removed)} min")

    return by_minute


# ── Provider zone classification ──────────────────────────────────────────────


def classify_providers(
    providers: list[tuple[float, float]],
    isochrones: dict,
) -> dict[tuple[float, float], int | None]:
    """
    For each provider (lat, lon), find the smallest isochrone zone it falls
    within. Returns {(lat, lon): minutes | None}.
    """
    shapely_isos = {m: shape(feat["geometry"]) for m, feat in sorted(isochrones.items())}
    result = {}
    for lat, lon in providers:
        point = Point(lon, lat)
        assigned = None
        for minute in sorted(shapely_isos):
            if shapely_isos[minute].contains(point):
                assigned = minute
                break
        result[(lat, lon)] = assigned
    return result


# ── GeoJSON export ────────────────────────────────────────────────────────────


def save_isochrones_geojson(
    isochrones: dict,
    output_path: str = "isochrones.geojson",
) -> str:
    """
    Save all isochrone features as a GeoJSON FeatureCollection.
    Each feature retains its original Mapbox properties and gets an
    additional 'contour_minutes' property for clarity.
    """
    features = []
    for minute in sorted(isochrones.keys()):
        feature = copy.deepcopy(isochrones[minute])  # never mutate the cached object
        feature["properties"]["contour_minutes"] = minute
        features.append(feature)

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(feature_collection, f, indent=2, ensure_ascii=False)

    logger.info(f"[✓] Isochrones GeoJSON saved → {output_path}")
    return output_path


# ── Contextily map renderer ───────────────────────────────────────────────────

ORDERED_COLORS = ["#60aeca", "#447eca", "#1c41ca", "#053b78", "#000000"]


def render_map_contextily(
    isochrones: dict,
    source_lat: float,
    source_lon: float,
    providers: list[tuple[float, float]],
    provider_zones: dict,
    token: str,
    width_in: float = 12,
    height_in: float = 8,
    dpi: int = 150,
    style: str = "mapbox/streets-v12",
) -> bytes:
    """
    Render isochrones + markers onto a Mapbox basemap using contextily.
    Returns PNG image as bytes (no file written to disk).
    """
    sorted_minutes = sorted(isochrones.keys())
    minute_to_color = {m: ORDERED_COLORS[i % len(ORDERED_COLORS)] for i, m in enumerate(sorted_minutes)}

    fig, ax = plt.subplots(figsize=(width_in, height_in))

    # Draw isochrones largest → smallest for correct z-order
    for minute in sorted(isochrones.keys(), reverse=True):
        geom = shape(isochrones[minute]["geometry"])
        gdf = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326").to_crs(epsg=3857)
        color = minute_to_color[minute]
        gdf.plot(
            ax=ax,
            facecolor="none",
            edgecolor=color,
            alpha=0.7,
            linewidth=1.4,
            zorder=2,
        )

    # Draw providers colored by zone
    for lat, lon in providers:
        zone = provider_zones.get((lat, lon))
        color = minute_to_color.get(zone, "#9b1c1c")
        pt = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=3857)
        pt.plot(ax=ax, color=color, markersize=60, zorder=5, marker="o", edgecolors="white", linewidths=0.5)

    # Draw source marker
    src = gpd.GeoDataFrame(geometry=[Point(source_lon, source_lat)], crs="EPSG:4326").to_crs(epsg=3857)
    src.plot(ax=ax, color="#c40700", markersize=120, zorder=6, marker="*", edgecolors="white", linewidths=0.5)

    # Mapbox basemap via contextily
    mapbox_tiles = f"https://api.mapbox.com/styles/v1/{style}/tiles/256/{{z}}/{{x}}/{{y}}@2x?access_token={token}"
    ctx.add_basemap(
        ax,
        source=mapbox_tiles,
        zoom="auto",
        attribution="© Mapbox © OpenStreetMap",
        attribution_size=7,
    )

    # Legend — isochrone contours
    legend_patches = [
        mpatches.Patch(
            facecolor=minute_to_color[m],
            edgecolor=minute_to_color[m],
            alpha=0.6,
            label=f"{m} min drive",
        )
        for m in sorted_minutes
    ]
    legend_patches.append(mpatches.Patch(color="white", label=""))  # spacer
    legend_patches.append(
        plt.Line2D([0], [0], marker="*", color="w", markerfacecolor="#c40700", markersize=12, label="Source")
    )

    ax.legend(
        handles=legend_patches,
        loc="lower left",
        framealpha=0.85,
        fontsize=8,
        title="Drive time",
        title_fontsize=9,
    )
    ax.set_axis_off()
    plt.tight_layout(pad=0)
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close()
    buf.seek(0)

    logger.info("[✓] Map rendered via contextily (in-memory)")
    return buf.read()


# ── Drive-time stamping ───────────────────────────────────────────────────────

_MAP_ISOCHRONES = [5, 10, 15, 20]


def stamp_provider_drive_times_by_isochrone(
    source_lat: float,
    source_lon: float,
    providers: list,
    token: str,
    max_drive_minutes: int,
) -> dict:
    """
    For each provider object (must have .latitude and .longitude attributes),
    stamp .drive_time_minutes with the isochrone zone it falls within, using
    the same fixed contours and classify_providers logic as generate_map.

    Because both stamp and map derive zones from the same Mapbox isochrone
    polygons via the same classify_providers call, the stamped value and the
    map dot color are guaranteed to agree — zero disagreement.

    Providers outside all zones get drive_time_minutes = None.
    Providers without coordinates are skipped (drive_time_minutes left unchanged).

    Returns the raw isochrone feature dict {minutes: GeoJSON Feature} so
    callers can reuse it (e.g. for ZIP centroid filtering) without a second
    API call.
    """
    coord_pairs = [(p.latitude, p.longitude) for p in providers if p.latitude is not None and p.longitude is not None]
    if not coord_pairs:
        logger.warning("stamp_provider_drive_times_by_isochrone: no providers with coordinates")
        return {}

    step = 5
    max_rounded = min(math.ceil(max_drive_minutes / step) * step, 60)
    contours = [m for m in _MAP_ISOCHRONES if m <= max_rounded] or _MAP_ISOCHRONES
    logger.info(f"Fetching isochrones for drive-time stamping: {contours} min")

    iso_features = fetch_isochrones(
        source_lat,
        source_lon,
        token,
        minutes=contours,
        providers=tuple(coord_pairs),
    )
    zone_map = classify_providers(coord_pairs, iso_features)

    for p in providers:
        if p.latitude is None or p.longitude is None:
            continue
        p.drive_time_minutes = zone_map.get((p.latitude, p.longitude))

    return iso_features


# ── Main entry point ──────────────────────────────────────────────────────────
def generate_map(
    token: str,
    source_lat: float | None = None,
    source_lon: float | None = None,
    source_address: str | None = None,
    providers: list[tuple[float, float]] | None = None,
    provider_addresses: list[str] | None = None,
    geojson_path: str | None = None,
    isochrones: list[int] | str = "auto",
    profile: str = "driving",
    width_in: float = 12,
    height_in: float = 8,
    dpi: int = 150,
    style: str = "mapbox/streets-v12",
) -> dict:
    """
    Main entry point. Accepts coordinates or addresses (geocoded automatically).

    Args:
        isochrones: "auto" to calculate contours from provider drive times,
                    or a list of ints e.g. [15, 20, 30] to use fixed contours.

    Returns dict with keys:
        output_path, geojson_path, provider_zones, isochrones,
        contour_minutes, source, providers
    """
    if source_lat is None or source_lon is None:
        if not source_address:
            raise ValueError("Provide (source_lat, source_lon) or source_address.")
        logger.info(f"[→] Geocoding source: {source_address!r}")
        source_lat, source_lon = geocode_address(source_address, token)
        logger.info(f"    Resolved to ({source_lat:.6f}, {source_lon:.6f})")

    if providers is None:
        if not provider_addresses:
            raise ValueError("Provide providers [(lat,lon),...] or provider_addresses.")
        providers = []
        for addr in provider_addresses:
            logger.info(f"[→] Geocoding provider: {addr!r}")
            lat, lon = geocode_address(addr, token)
            logger.info(f"    Resolved to ({lat:.6f}, {lon:.6f})")
            providers.append((lat, lon))

    # ── Contour resolution ────────────────────────────────────────────────────
    if isochrones == "auto":
        contour_minutes = calculate_contour_minutes(source_lat, source_lon, providers, token, profile=profile)
        logger.info(f"[→] Auto contours: {contour_minutes}")
    elif isinstance(isochrones, list) and all(isinstance(m, int) for m in isochrones):
        contour_minutes = sorted(isochrones)
        logger.info(f"[→] Manual contours: {contour_minutes}")
    else:
        raise ValueError(f"isochrones must be 'auto' or a list of ints, got: {isochrones!r}")
    # ─────────────────────────────────────────────────────────────────────────

    iso_features = fetch_isochrones(
        source_lat,
        source_lon,
        token,
        minutes=contour_minutes,
        profile=profile,
        providers=tuple(providers),
    )

    logger.info(f"  Received {len(iso_features)} contour(s): {sorted(iso_features.keys())} min")

    if geojson_path:
        save_isochrones_geojson(iso_features, geojson_path)

    provider_zones = classify_providers(providers, iso_features)
    for (lat, lon), zone in provider_zones.items():
        label = f"{zone} min" if zone else "outside all zones"
        logger.info(f"  Provider ({lat:.4f}, {lon:.4f}) → {label}")

    logger.info("[→] Rendering map via contextily …")
    map_bytes = render_map_contextily(
        iso_features,
        source_lat,
        source_lon,
        providers,
        provider_zones,
        token=token,
        width_in=width_in,
        height_in=height_in,
        dpi=dpi,
        style=style,
    )

    logger.info("Finished!")

    return {
        "map_bytes": map_bytes,
        "geojson_path": geojson_path,
        "provider_zones": provider_zones,
        "isochrones": iso_features,
        "contour_minutes": contour_minutes,
        "source": (source_lat, source_lon),
        "providers": providers,
    }
