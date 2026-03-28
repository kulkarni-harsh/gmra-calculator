import logging
import threading
from functools import lru_cache

import pandas as pd
import requests
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.types import SexAgeCounts, ZipPopulationMap

_log = logging.getLogger(__name__)

_CENSUS_TIMEOUT = (10, 30)  # (connect, read)
_TIGERWEB_TIMEOUT = (10, 30)
_TIGERWEB_URL = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/1/query"
# ACS 5-year vintage — bump when Census releases a newer dataset.
# Latest available as of 2026: 2024 (covers survey years 2020-2024).
# 2025 vintage expected ~December 2026.
_ACS_VINTAGE = 2024

# Cache ZCTA boundary polygons by ZIP code to avoid re-fetching across reports.
_zcta_geometry_cache: dict[str, BaseGeometry] = {}
_zcta_geometry_cache_lock = threading.Lock()


def get_age_mapping(start_idx: int) -> dict[str, str]:
    """
    Get the mapping of census variable codes to age groups for either
    male or female demographics.

    The start_idx parameter determines whether the mapping is for
    male (start_idx=2) or female (start_idx=26) demographics.

    The mapping is based on the ACS 5-year estimates for the B01001
    table, which provides detailed age and sex breakdowns.
    """
    return {
        f"B01001_{start_idx:03d}E": "Total",
        f"B01001_{start_idx + 1:03d}E": "0-4",
        f"B01001_{start_idx + 2:03d}E": "5-9",
        f"B01001_{start_idx + 3:03d}E": "10-14",
        f"B01001_{start_idx + 4:03d}E": "15-17",
        f"B01001_{start_idx + 5:03d}E": "18-19",
        f"B01001_{start_idx + 6:03d}E": "20",
        f"B01001_{start_idx + 7:03d}E": "21",
        f"B01001_{start_idx + 8:03d}E": "22-24",
        f"B01001_{start_idx + 9:03d}E": "25-29",
        f"B01001_{start_idx + 10:03d}E": "30-34",
        f"B01001_{start_idx + 11:03d}E": "35-39",
        f"B01001_{start_idx + 12:03d}E": "40-44",
        f"B01001_{start_idx + 13:03d}E": "45-49",
        f"B01001_{start_idx + 14:03d}E": "50-54",
        f"B01001_{start_idx + 15:03d}E": "55-59",
        f"B01001_{start_idx + 16:03d}E": "60-61",
        f"B01001_{start_idx + 17:03d}E": "62-64",
        f"B01001_{start_idx + 18:03d}E": "65-66",
        f"B01001_{start_idx + 19:03d}E": "67-69",
        f"B01001_{start_idx + 20:03d}E": "70-74",
        f"B01001_{start_idx + 21:03d}E": "75-79",
        f"B01001_{start_idx + 22:03d}E": "80-84",
        f"B01001_{start_idx + 23:03d}E": "85-1000",
    }


@retry(
    retry=retry_if_exception_type(requests.exceptions.Timeout),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _fetch_zip_demographics(zip_codes_list: tuple[str, ...], api_key: str) -> list[list[str]]:
    male_vars = get_age_mapping(2)
    female_vars = get_age_mapping(26)
    vars_to_get = list(male_vars.keys()) + list(female_vars.keys()) + ["B01003_001E"]  # Total population

    params = {
        "get": ",".join(vars_to_get),
        "for": f"zip code tabulation area:{','.join(zip_codes_list)}",
        "key": api_key,
    }
    r = requests.get(f"https://api.census.gov/data/{_ACS_VINTAGE}/acs/acs5", params=params, timeout=_CENSUS_TIMEOUT)
    r.raise_for_status()
    return r.json()


@lru_cache(maxsize=1000)
def get_zip_demographics(zip_codes_list: tuple[str], api_key: str) -> ZipPopulationMap:
    """
    Get demographic data for a list of zip codes from the US Census API.

    The function retrieves total population and age group breakdowns for both
    male and female demographics.

    Args
    ----
    zip_codes_list : tuple[str]
        A tuple of zip codes for which to retrieve demographic data.
    api_key : str
        A valid API key for accessing the US Census API.

    Returns
    -------
    dict[str, dict[str, dict[str, int]]]
        A dictionary where each key is a zip code and the value is another dictionary containing demographic data.
    """
    male_vars = get_age_mapping(2)
    female_vars = get_age_mapping(26)

    data = _fetch_zip_demographics(zip_codes_list, api_key)

    pop_df = pd.DataFrame(data[1:], columns=data[0])
    dict_data: ZipPopulationMap = (
        pop_df.set_index("zip code tabulation area")
        .apply(
            lambda row: {
                "M": {y: int(row[x]) for x, y in male_vars.items()},
                "F": {y: int(row[x]) for x, y in female_vars.items()},
                "Total": int(row["B01003_001E"]),
            },
            axis=1,
        )
        .to_dict()
    )
    return dict_data


def combine_demographics(pop1: SexAgeCounts, pop2: SexAgeCounts) -> SexAgeCounts:
    """Combine two demographic dictionaries by summing the counts for each age group and total population."""
    combined: SexAgeCounts = {"M": {}, "F": {}, "Total": pop1["Total"] + pop2["Total"]}

    for age_group in pop1["M"].keys():
        combined["M"][age_group] = pop1["M"][age_group] + pop2["M"][age_group]
        combined["F"][age_group] = pop1["F"][age_group] + pop2["F"][age_group]

    return combined


@retry(
    retry=retry_if_exception_type(requests.exceptions.Timeout),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _fetch_zcta_batch(batch: list[str]) -> list[dict]:
    """Fetch one batch of ZCTA GeoJSON features from TIGERweb (retried on timeout)."""
    where = "ZCTA5 IN (" + ",".join(f"'{z}'" for z in batch) + ")"
    resp = requests.get(
        _TIGERWEB_URL,
        params={"where": where, "outFields": "ZCTA5", "f": "geojson", "outSR": "4326"},
        timeout=_TIGERWEB_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("features", [])


def _fetch_zcta_geometries(zip_codes: tuple[str, ...]) -> dict[str, BaseGeometry]:
    """
    Fetch ZCTA boundary polygons from Census TIGERweb for the given ZIP codes.
    Results are cached in-process behind a thread lock so concurrent requests
    for the same ZIPs don't duplicate network calls.
    Returns {zip_code: shapely_polygon}.
    """
    with _zcta_geometry_cache_lock:
        missing = [z for z in zip_codes if z not in _zcta_geometry_cache]

    if not missing:
        with _zcta_geometry_cache_lock:
            return {z: _zcta_geometry_cache[z] for z in zip_codes if z in _zcta_geometry_cache}

    batch_size = 50
    for i in range(0, len(missing), batch_size):
        batch = missing[i : i + batch_size]
        try:
            features = _fetch_zcta_batch(batch)
        except Exception as exc:
            _log.critical(
                "TIGERweb batch %d–%d failed — those ZIPs excluded from population: %s", i, i + batch_size, exc
            )
            continue

        with _zcta_geometry_cache_lock:
            for feature in features:
                zcta = str(feature["properties"].get("ZCTA5", "")).zfill(5)
                geom = shape(feature["geometry"])
                if not geom.is_valid:
                    geom = geom.buffer(0)
                _zcta_geometry_cache[zcta] = geom

    with _zcta_geometry_cache_lock:
        return {z: _zcta_geometry_cache[z] for z in zip_codes if z in _zcta_geometry_cache}


def get_population_in_polygon(
    iso_polygon: BaseGeometry | None,
    candidate_zips: tuple[str, ...],
    api_key: str,
    min_overlap: float = 0.01,
) -> tuple[SexAgeCounts, dict[str, float], dict[str, int]]:
    """
    Return population (total + age breakdown) for the area covered by iso_polygon
    using proportional ZIP area weighting.

    For each candidate ZIP:
      - Fetch its ZCTA boundary polygon from Census TIGERweb (cached).
      - Compute overlap_fraction = intersection_area / zcta_area.
      - Scale all age-group counts by that fraction.
      - Sum across all ZIPs.

    ZIPs with overlap < min_overlap (default 1%) are excluded to avoid noise
    from ZIPs that barely touch the boundary.

    Falls back to an empty SexAgeCounts on any error.
    """
    _empty: SexAgeCounts = {"M": {}, "F": {}, "Total": 0}
    if not candidate_zips or iso_polygon is None:
        return _empty, {}, {}

    zcta_geoms = _fetch_zcta_geometries(candidate_zips)
    if not zcta_geoms:
        return _empty, {}, {}

    # Compute overlap fractions — done in geographic degrees (EPSG:4326).
    # Area ratios are accurate enough for population weighting at this scale.
    overlap_fractions: dict[str, float] = {}
    for zcta, geom in zcta_geoms.items():
        zcta_area = geom.area
        if zcta_area <= 0:
            continue
        intersection = iso_polygon.intersection(geom)
        fraction = intersection.area / zcta_area
        if fraction >= min_overlap:
            overlap_fractions[zcta] = min(fraction, 1.0)

    if not overlap_fractions:
        return _empty, {}, {}

    relevant_zips = tuple(sorted(overlap_fractions))
    zip_demo = get_zip_demographics(relevant_zips, api_key)

    combined: SexAgeCounts | None = None
    zip_scaled_populations: dict[str, int] = {}
    for zcta, demo in zip_demo.items():
        fraction = overlap_fractions.get(zcta, 1.0)
        scaled: SexAgeCounts = {
            "M": {k: round(v * fraction) for k, v in demo["M"].items()},
            "F": {k: round(v * fraction) for k, v in demo["F"].items()},
            "Total": round(demo["Total"] * fraction),
        }
        zip_scaled_populations[zcta] = scaled["Total"]
        combined = scaled if combined is None else combine_demographics(combined, scaled)

    return (combined if combined is not None else _empty), overlap_fractions, zip_scaled_populations
