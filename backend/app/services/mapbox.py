
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
import json
import urllib.parse
from typing import TYPE_CHECKING, Optional
import math

if TYPE_CHECKING:
    from app.types.alphasophia import Provider
import requests
from shapely.geometry import shape, Point, mapping
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
import io

try:
    import polyline as polyline_lib

    HAS_POLYLINE = True
except ImportError:
    HAS_POLYLINE = False
import logging
from functools import lru_cache
from urllib.parse import quote

import requests
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
    encoded_address = quote(address, safe="")
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
        logging.error("All coordinates must be numeric values.")
        return 10e9, 10e9  # Return large values to indicate an error
    return _fetch_drive_distance_time(lat1, long1, lat2, long2)

# ── Geocoding ─────────────────────────────────────────────────────────────────
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

    Args:
        source_lat/lon: Origin point.
        providers:      List of (lat, lon) provider coordinates.
        token:          Mapbox access token.
        profile:        Routing profile: "driving" | "walking" | "cycling".

    Returns:
        List of int, e.g. [5, 10, 15, 20] for a 17-minute furthest provider.
    """
    # Mapbox Matrix API accepts max 25 coordinates total (1 source + N destinations)
    # For larger provider lists, batch into chunks of 24
    MAX_DESTINATIONS = 24

    coordinates = [(source_lon, source_lat)] + [(lon, lat) for lat, lon in providers]
    max_duration_seconds = 0

    for i in range(1, len(coordinates), MAX_DESTINATIONS):
        batch = [coordinates[0]] + coordinates[i:i + MAX_DESTINATIONS]
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
        durations = resp.json().get("durations", [[]])[0]  # row 0 = from source
        valid = [d for d in durations if d is not None]
        if valid:
            max_duration_seconds = max(max_duration_seconds, max(valid))

    if max_duration_seconds == 0:
        raise ValueError("Matrix API returned no valid durations.")

    max_minutes = math.ceil(max_duration_seconds / 60)
    # Round up to nearest 5
    max_rounded = math.ceil(max_minutes / 5) * 5
    # Clamp to a sensible upper bound (Mapbox Isochrone API max is 60 min)
    max_rounded = min(max_rounded, 60)

    contours = list(range(5, max_rounded + 1, 5))

    if len(contours) > 4:
        contours.pop(1)

    logger.info(
        f"Furthest provider: {max_minutes} min → rounded to {max_rounded} min. "
        f"Contours: {contours}"
    )
    return contours

# ── Isochrone fetching ────────────────────────────────────────────────────────

def fetch_isochrones(
        lat: float,
        lon: float,
        token: str,
        minutes: list[int],
        profile: str = "driving",
) -> dict:
    """
    Fetch drive-time isochrone polygons from the Mapbox Isochrone API.
    Automatically batches into requests of 4 (API hard limit).
    Returns {minute: GeoJSON Feature}.
    """
    BATCH_SIZE = 4
    sorted_minutes = sorted(minutes)
    batches = [
        sorted_minutes[i:i + BATCH_SIZE]
        for i in range(0, len(sorted_minutes), BATCH_SIZE)
    ]
    by_minute = {}
    for batch in batches:
        contours_param = ",".join(str(m) for m in batch)
        url = (
            f"https://api.mapbox.com/isochrone/v1/mapbox/{profile}"
            f"/{lon},{lat}"
            f"?contours_minutes={contours_param}"
            f"&polygons=true"
            f"&denoise=1"
            f"&generalize=250"
            f"&access_token={token}"
        )
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        for feature in resp.json().get("features", []):
            minute = feature["properties"].get("contour")
            if minute is not None:
                by_minute[int(minute)] = feature
    return by_minute


# ── Provider zone classification ──────────────────────────────────────────────

def classify_providers(
        providers: list[tuple[float, float]],
        isochrones: dict,
) -> dict[tuple[float, float], Optional[int]]:
    """
    For each provider (lat, lon), find the smallest isochrone zone it falls
    within. Returns {(lat, lon): minutes | None}.
    """
    shapely_isos = {
        m: shape(feat["geometry"])
        for m, feat in sorted(isochrones.items())
    }
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


# ── Coordinate helpers ────────────────────────────────────────────────────────

def _round_coords(coords: list, precision: int = 5) -> list:
    """Recursively round all coordinates in a GeoJSON coordinate array."""
    if not coords:
        return coords
    if isinstance(coords[0], (int, float)):
        return [round(c, precision) for c in coords]
    return [_round_coords(ring, precision) for ring in coords]


def _simplify_polygon(geojson_geometry: dict, tolerance: float = 0.01) -> dict:
    """
    Simplify a GeoJSON polygon/multipolygon using Shapely to reduce vertex
    count and keep the URL short.
    tolerance is in degrees: 0.001 ≈ 100m, 0.01 ≈ 1km, 0.02 ≈ 2km.
    """
    geom = shape(geojson_geometry)
    simplified = geom.simplify(tolerance, preserve_topology=True)
    result = dict(mapping(simplified))
    result["coordinates"] = _round_coords(list(result["coordinates"]))
    return result


# ── Polyline encoding ─────────────────────────────────────────────────────────

def _encode_polyline(coords: list[tuple[float, float]]) -> str:
    """
    Encode (lat, lon) pairs as a Google-format encoded polyline (precision 5).
    Uses the `polyline` library if installed, otherwise pure Python.
    """
    if HAS_POLYLINE:
        return polyline_lib.encode(coords, 5)
    result = []
    prev_lat = prev_lon = 0
    for lat, lon in coords:
        for value, prev in [(lat, prev_lat), (lon, prev_lon)]:
            delta = round(value * 1e5) - round(prev * 1e5)
            delta = delta << 1
            if delta < 0:
                delta = ~delta
            while delta >= 0x20:
                result.append(chr((0x20 | (delta & 0x1f)) + 63))
                delta >>= 5
            result.append(chr(delta + 63))
        prev_lat = lat
        prev_lon = lon
    return "".join(result)


def _geometry_to_path_overlays(
        geojson_geometry: dict,
        stroke_color: str,
        stroke_opacity: float,
        fill_color: str,
        fill_opacity: float,
        stroke_width: int = 1,
) -> list[str]:
    """
    Convert a GeoJSON Polygon/MultiPolygon to encoded polyline `path` overlay
    strings for the Static Images API. Uses exterior ring only.
    """
    sc = stroke_color.lstrip("#")
    fc = fill_color.lstrip("#")
    geom_type = geojson_geometry["type"]

    if geom_type == "Polygon":
        rings = [geojson_geometry["coordinates"][0]]
    elif geom_type == "MultiPolygon":
        rings = [poly[0] for poly in geojson_geometry["coordinates"]]
    else:
        return []

    paths = []
    for ring in rings:
        lat_lon = [(round(c[1], 5), round(c[0], 5)) for c in ring]
        encoded = _encode_polyline(lat_lon)
        encoded_uri = urllib.parse.quote(encoded, safe="")
        paths.append(
            f"path-{stroke_width}+{sc}-{stroke_opacity}"
            f"+{fc}-{fill_opacity}({encoded_uri})"
        )
    return paths


# ── Marker GeoJSON ────────────────────────────────────────────────────────────

def _build_marker_geojson(
    source_lat: float,
    source_lon: float,
    providers: list[tuple[float, float]],
    provider_zones: dict[tuple[float, float], Optional[int]],
    minute_to_color: dict,
) -> str:
    """
    Build a compact GeoJSON FeatureCollection for source + providers.
    Accepts minute_to_color built externally by build_static_image_url().
    """
    features = [{
        "type": "Feature",
        "properties": {
            "marker-color":  "#c40700",
            "marker-size":   "medium",
            "marker-symbol": "marker",
        },
        "geometry": {
            "type": "Point",
            "coordinates": [round(source_lon, 5), round(source_lat, 5)],
        },
    }]

    zone_groups: dict[Optional[int], list] = {}
    for lat, lon in providers:
        zone = provider_zones.get((lat, lon))
        zone_groups.setdefault(zone, []).append([round(lon, 5), round(lat, 5)])

    for zone, coords_list in zone_groups.items():
        color = "#" + minute_to_color.get(zone, "9b1c1c")
        geom = (
            {"type": "Point",      "coordinates": coords_list[0]}
            if len(coords_list) == 1
            else {"type": "MultiPoint", "coordinates": coords_list}
        )
        features.append({
            "type": "Feature",
            "properties": {
                "marker-color":  color,
                "marker-size":   "medium",
                "marker-symbol": "doctor",
            },
            "geometry": geom,
        })

    return json.dumps({"type": "FeatureCollection", "features": features},
                      separators=(",", ":"))


def _build_isochrone_label_overlays(
    isochrones: dict,
    minute_to_color: dict,
) -> list[str]:
    """
    Generate pin-s label overlays at each isochrone's centroid.
    Uses the pin-s-{label}+{color} format which supports up to 2 chars.
    """
    from shapely.geometry import shape
    overlays = []
    for minute, feature in isochrones.items():
        centroid  = shape(feature["geometry"]).centroid
        color     = minute_to_color.get(minute, "000000").lstrip("#")
        label     = str(minute)          # "5", "10", "15" etc. — up to 2 chars
        overlays.append(
            f"pin-s-{label}+{color}({round(centroid.x, 5)},{round(centroid.y, 5)})"
        )
    return overlays

# ── Static image URL builder ──────────────────────────────────────────────────

def build_static_image_url(
    source_lat: float,
    source_lon: float,
    providers: list[tuple[float, float]],
    provider_zones: dict[tuple[float, float], Optional[int]],
    isochrones: dict,
    token: str,
    width: int = 1200,
    height: int = 800,
    style: str = "mapbox/streets-v12",
    simplify_tolerance: float = 0.003,
) -> tuple[str, dict]:
    width  = min(width,  1280)
    height = min(height, 1280)

    # Styles by rank (index 0 = smallest/innermost, index 4 = largest/outermost)
    ORDERED_STYLES = [
        {"stroke": "#60aeca", "fill": "60aeca", "stroke_op": 1, "fill_op": 0},  # 1st (smallest)
        {"stroke": "#447eca", "fill": "447eca", "stroke_op": 1, "fill_op": 0},  # 2nd
        {"stroke": "#1c41ca", "fill": "1c41ca", "stroke_op": 1, "fill_op": 0},  # 3rd
        {"stroke": "#053b78", "fill": "053b78", "stroke_op": 1, "fill_op": 0},  # 4th
        {"stroke": "#000000", "fill": "000000", "stroke_op": 1, "fill_op": 0},  # 5th (largest)
    ]

    ORDERED_COLORS = ["60aeca", "447eca", "1c41ca", "053b78", "000000"]

    sorted_minutes = sorted(isochrones.keys())
    minute_to_style = {
        minute: ORDERED_STYLES[i]
        for i, minute in enumerate(sorted_minutes)
    }
    minute_to_color = {
        minute: ORDERED_COLORS[i]
        for i, minute in enumerate(sorted_minutes)
    }
    minute_to_color[None] = "9b1c1c"  # outside all zones → red

    overlay_parts = []

    for minute in sorted(isochrones.keys(), reverse=True):  # largest → smallest (z-order)
        feature  = isochrones[minute]
        s        = minute_to_style[minute]
        geometry = _simplify_polygon(feature["geometry"], simplify_tolerance)
        paths    = _geometry_to_path_overlays(
            geometry,
            stroke_color=s["stroke"], stroke_opacity=s["stroke_op"],
            fill_color=s["fill"],     fill_opacity=s["fill_op"],
            stroke_width=2,
        )
        overlay_parts.extend(paths)

    encoded_markers = urllib.parse.quote(
        _build_marker_geojson(source_lat, source_lon, providers, provider_zones, minute_to_color),
        safe="",
    )
    overlay_parts.append(f"geojson({encoded_markers})")

    url = (
        f"https://api.mapbox.com/styles/v1/{style}/static"
        f"/{','.join(overlay_parts)}"
        f"/auto"
        f"/{width}x{height}@2x"
        f"?padding=20"
        f"&access_token={token}"
    )

    char_count = len(url)
    if char_count > 8192:
        logger.info(
            f"[!] URL is {char_count} chars — exceeds 8,192 limit.\n"
            f"    Increase simplify_tolerance (current: {simplify_tolerance})."
        )
    else:
        logger.info(f"[✓] URL length: {char_count} chars (limit: 8,192)")

    return url, minute_to_color


# ── Download ──────────────────────────────────────────────────────────────────

def download_static_image(url: str) -> bytes:
    """Download the static map PNG and return as bytes."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    logger.info("[✓] Static map downloaded")
    return resp.content


def add_legend(
    image_data: bytes,
    isochrones: dict,
    minute_to_color: dict,
) -> bytes:
    """Draw a drive-time legend onto the PNG and return bytes."""
    img = Image.open(io.BytesIO(image_data)).convert("RGBA")
    entries = sorted(isochrones.keys())
    row_h, swatch_w, swatch_h = 70, 40, 30
    padding = 16
    box_w = 320
    box_h = padding * 2 + row_h * len(entries)
    box_x, box_y = 20, 1350

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        fill=(255, 255, 255, 200),
        outline=(180, 180, 180, 255),
        width=1,
    )
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except Exception:
        font = ImageFont.load_default(size=32)

    for i, minute in enumerate(entries):
        color_hex = minute_to_color.get(minute, "000000").lstrip("#")
        r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
        sx = box_x + padding
        sy = box_y + padding + i * row_h + (row_h - swatch_h) // 2
        draw.rectangle([sx, sy, sx + swatch_w, sy + swatch_h], fill=(r, g, b, 255))
        draw.text(
            (sx + swatch_w + 12, box_y + padding + i * row_h + (row_h - 32) // 2),
            f"{minute} min drive",
            fill=(30, 30, 30, 255),
            font=font,
        )

    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    return buf.getvalue()

# ── Main entry point ──────────────────────────────────────────────────────────

def generate_map(
        token: str,
        source_lat: float,
        source_lon: float,
        providers: "list[Provider]",
        profile: str = "driving",
        width: int = 1200,
        height: int = 800,
) -> bytes:
    """
    Generate a static map PNG with drive-time isochrones and provider markers.

    Args:
        token:      Mapbox access token.
        source_lat: Latitude of the source (subject) office.
        source_lon: Longitude of the source (subject) office.
        providers:  List of Provider objects; must have latitude and longitude set.
        profile:    Routing profile: "driving" | "walking" | "cycling".
        width:      Image width in pixels (max 1280).
        height:     Image height in pixels (max 1280).

    Returns:
        PNG image bytes with the drive-time legend overlaid.
    """
    provider_coords: list[tuple[float, float]] = [
        (p.latitude, p.longitude)
        for p in providers
        if p.latitude is not None and p.longitude is not None
    ]

    if not provider_coords:
        raise ValueError("No providers with valid latitude/longitude coordinates.")

    contour_minutes = calculate_contour_minutes(
        source_lat, source_lon, provider_coords, token, profile=profile
    )
    isochrones = fetch_isochrones(source_lat, source_lon, token, minutes=contour_minutes, profile=profile)

    logger.info(f"    Received {len(isochrones)} contour(s): {sorted(isochrones.keys())} min")

    provider_zones = classify_providers(provider_coords, isochrones)
    for (lat, lon), zone in provider_zones.items():
        label = f"{zone} min" if zone else "outside all zones"
        logger.info(f"    Provider ({lat:.4f}, {lon:.4f}) → {label}")

    logger.info("[→] Building static image URL …")
    url, minute_to_color = build_static_image_url(
        source_lat, source_lon,
        provider_coords, provider_zones,
        isochrones, token,
        width=width, height=height,
    )
    logger.info("[→] Downloading static image and adding legend …")
    image_bytes = download_static_image(url)
    image_bytes = add_legend(image_bytes, isochrones, minute_to_color)

    logger.info("Finished!")
    return image_bytes
