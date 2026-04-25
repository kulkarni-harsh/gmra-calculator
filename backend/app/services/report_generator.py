"""
Tier 1 / Tier 2 report generator.

Generates market-level reports from an address + specialty.
T1 (Market Entry) uses specialty-derived CPT codes.
T2 (Through-the-Door Codes) uses caller-provided CPT codes (custom_cpt_codes param).
No provider NPI lookup — market-level aggregate only.
"""

import asyncio
import base64
import json
import logging
from dataclasses import dataclass
from io import BytesIO

import pandas as pd
import ulid
from geopy.distance import geodesic
from shapely.geometry import Point, shape

from app.core.config import settings
from app.core.types import SexAgeCounts
from app.schemas.address_report_request import AddressReportRequest
from app.services import mapbox
from app.services.alphasophia import get_hcp_data
from app.services.bedrock_llm import MarketAnalysisInput, generate_market_analysis
from app.services.census import get_population_in_polygon
from app.services.fee_schedule import get_medicare_rate
from app.services.geocoder import geocode_address
from app.services.google_maps import find_nearby_google_places, get_sites_of_care_list
from app.services.html_imputers import render_report
from app.services.mapbox import fetch_isochrones, generate_map, stamp_provider_drive_times_by_isochrone
from app.services.payment import T2_DISPLAY_PRICE, T3_DISPLAY_PRICE
from app.services.s3 import upload_debug_excel
from app.types.alphasophia import CPT, Provider
from app.types.baseline_report_template import (
    CptRowV2,
    ProviderProfileV2,
    ProviderShareEntry,
    ReportTemplateDataV2,
    Upgrade,
)
from app.types.google_maps import SiteOfCare
from app.utils.common import (
    generate_tags,
    get_anchor_cpt_codes,
    get_anchor_cpt_patient_type_map,
    get_density_scope,
    get_geriatric_population,
    get_pediatric_population,
    get_provider_density,
    get_source_tabs,
    get_taxonomy_codes,
    load_fee_schedule_tables,
)
from app.utils.specialty import get_google_places_keywords
from app.utils.validator import validate_speciality_master_df

# Max drive-time option is 60 min. At ~50 mph average, 60 min ≈ 50 miles.
# Fetch providers within this fixed radius; drive-time filter happens after stamping.
_DRIVE_TIME_FETCH_MILES: float = 50.0


# ── Shared state (loaded once at worker startup, passed into every report run) ─


@dataclass
class ReportState:
    specialty_lookup: dict
    anchor_cpt_lookup: dict
    zip_centroids_df: pd.DataFrame
    cpt_lookup_df: pd.DataFrame
    specialty_master_df: pd.DataFrame
    rvu_table: dict
    gpci_table: dict


def load_state() -> ReportState:
    """Load all lookup data from disk. Call once at startup."""
    from opencage.geocoder import OpenCageGeocode  # noqa: F401 — side-effect import required by alphasophia

    specialty_lookup = json.load(open(settings.LOOKUP_DIR / "specialty_lookup.json"))
    anchor_cpt_lookup = json.load(open(settings.LOOKUP_DIR / "anchor_cpt_lookup.json"))
    zip_centroids_df = pd.read_csv(settings.LOOKUP_DIR / "zip_centroids.csv")
    cpt_lookup_df = pd.read_csv(settings.LOOKUP_DIR / "cpt_lookup.csv")
    specialty_master_df = pd.read_excel(settings.LOOKUP_DIR / "Specialty Master Sheet.xlsx")
    validate_speciality_master_df(specialty_master_df)
    rvu_table, gpci_table = load_fee_schedule_tables()
    logging.info("ReportState loaded successfully.")
    return ReportState(
        specialty_lookup=specialty_lookup,
        anchor_cpt_lookup=anchor_cpt_lookup,
        zip_centroids_df=zip_centroids_df,
        cpt_lookup_df=cpt_lookup_df,
        specialty_master_df=specialty_master_df,
        rvu_table=rvu_table,
        gpci_table=gpci_table,
    )


# ── Return-type containers ────────────────────────────────────────────────────


@dataclass
class _SpecialtyMeta:
    cpt_codes: list[str]
    cpt_patient_type_map: dict[str, str]
    taxonomy_codes: list[str]
    source_tabs: list[str]


@dataclass
class _CptAggregation:
    cpt_rows: list[CptRowV2]
    total_market_services: int
    provider_shares: list[ProviderShareEntry]
    share_denom: int  # sum of all provider CPT totals (denominator for share %)


@dataclass
class _PopulationData:
    total_population: int
    relevant_pop: int
    population_label: str
    combined_demo: SexAgeCounts
    zip_overlap_fractions: dict[str, float]
    zip_scaled_populations: dict[str, int]
    actual_zips_df: pd.DataFrame


@dataclass
class _Verdict:
    verdict_type: str
    verdict_value: str
    verdict_sub: str


# ── Private helpers ───────────────────────────────────────────────────────────


def _resolve_specialty_meta(state: ReportState, specialty_name: str) -> _SpecialtyMeta:
    return _SpecialtyMeta(
        cpt_codes=get_anchor_cpt_codes(state.anchor_cpt_lookup, specialty_name),
        cpt_patient_type_map=get_anchor_cpt_patient_type_map(state.anchor_cpt_lookup),
        taxonomy_codes=get_taxonomy_codes(state.specialty_lookup, specialty_name),
        source_tabs=get_source_tabs(state.specialty_lookup, specialty_name),
    )


async def _geocode_with_fallback(
    payload: AddressReportRequest,
    zip_centroids_df: pd.DataFrame,
) -> tuple[float, float]:
    """Return (lat, lon) for the request address, falling back to ZIP centroid."""
    log = logging.getLogger(__name__)
    address_str = (
        f"{payload.address_line_1} "
        f"{payload.address_line_2 + ' ' if payload.address_line_2 else ''}"
        f"{payload.city}, {payload.state} {payload.zip_code}"
    ).strip()

    coords = await geocode_address(address_str, settings.MAPBOX_API_KEY)
    if coords is not None:
        log.info("Geocoded to lat=%.4f, lon=%.4f", *coords)
        return coords

    zip_row = zip_centroids_df[zip_centroids_df["zip"].astype(str) == payload.zip_code]
    if zip_row.empty:
        raise ValueError(f"Could not geocode address and no ZIP centroid found for {payload.zip_code}")
    lat, lon = float(zip_row.iloc[0]["lat"]), float(zip_row.iloc[0]["lon"])
    log.warning("Geocoding failed — fell back to ZIP centroid (%.4f, %.4f)", lat, lon)
    return lat, lon


def _compute_candidate_zips(
    zip_centroids_df: pd.DataFrame,
    source_lat: float,
    source_lon: float,
    fallback_zip: str,
) -> pd.DataFrame:
    """Return ZIP centroids within the fixed provider-fetch radius."""
    df = zip_centroids_df.copy()
    df["distance_from_source_miles"] = df.apply(
        lambda row: geodesic((source_lat, source_lon), (row["lat"], row["lon"])).miles,
        axis=1,
    )
    nearby = df[df["distance_from_source_miles"] <= _DRIVE_TIME_FETCH_MILES]
    if not nearby.empty:
        return nearby
    return pd.DataFrame(
        {"zip": [fallback_zip], "lat": [source_lat], "lon": [source_lon], "distance_from_source_miles": [0.0]}
    )


async def _fetch_and_enrich_providers(
    expanded_zips_df: pd.DataFrame,
    taxonomy_codes: list[str],
    cpt_codes: list[str],
) -> list[Provider]:
    """Fetch providers from AlphaSophia and enrich their addresses + coordinates."""
    log = logging.getLogger(__name__)
    providers: list[Provider] = []
    try:
        providers = await get_hcp_data(
            zip_codes_list=expanded_zips_df["zip"].dropna().astype(str).tolist(),
            taxonomy_codes_list=taxonomy_codes,
            npi_list=[],
            cpt_codes_list=cpt_codes,
            page_size=100,
        )
        log.info("Fetched %d providers from AlphaSophia", len(providers))
    except Exception as exc:
        log.error("AlphaSophia fetch failed: %s", exc)

    async def _enrich(p: Provider) -> None:
        await p.update_address_and_zip()
        await p.update_lat_long()

    await asyncio.gather(*[_enrich(p) for p in providers])
    return providers


async def _stamp_and_filter_providers(
    providers: list[Provider],
    source_lat: float,
    source_lon: float,
    drive_time_limit: int,
) -> tuple[list[Provider], dict]:
    """Stamp drive times, filter to limit, then re-stamp the surviving subset.

    Two-pass stamping guarantees the isochrone band selection (which drops bands
    with no unique providers) uses exactly the same provider list as generate_map.
    Raw Mapbox polygons are cached, so the second pass costs no extra API calls.
    """
    log = logging.getLogger(__name__)
    iso_features: dict = {}

    # Pass 1 — stamp all enriched providers.
    try:
        iso_features = await asyncio.to_thread(
            stamp_provider_drive_times_by_isochrone,
            source_lat,
            source_lon,
            providers,
            settings.MAPBOX_API_KEY,
            drive_time_limit,
        )
    except Exception as exc:
        log.warning("Drive time stamping failed — filter will exclude all providers: %s", exc)

    # Stamp geodesic distance on every provider that has valid coordinates —
    # not just the in-radius subset — so the debug Excel contains accurate
    # distances for all fetched providers, not only those that made the cut.
    for p in providers:
        if p.latitude is not None and p.longitude is not None:
            p.distance_from_source_miles = geodesic((p.latitude, p.longitude), (source_lat, source_lon)).miles

    in_radius = [
        p
        for p in providers
        if p.latitude is not None
        and p.longitude is not None
        and p.drive_time_minutes is not None
        and p.drive_time_minutes <= drive_time_limit
    ]
    log.info("%d providers within %d-min drive after pass 1", len(in_radius), drive_time_limit)

    # Pass 2 — re-stamp the in-radius subset only.
    if in_radius:
        try:
            iso_features = await asyncio.to_thread(
                stamp_provider_drive_times_by_isochrone,
                source_lat,
                source_lon,
                in_radius,
                settings.MAPBOX_API_KEY,
                drive_time_limit,
            )
            in_radius = [
                p for p in in_radius if p.drive_time_minutes is not None and p.drive_time_minutes <= drive_time_limit
            ]
            log.info("%d providers after re-stamp reconciliation", len(in_radius))
        except Exception as exc:
            log.warning("Re-stamp failed — using pass-1 values: %s", exc)

    return in_radius, iso_features


async def _generate_map_image(
    providers_in_radius: list[Provider],
    source_lat: float,
    source_lon: float,
    iso_features: dict,
) -> tuple[str | None, dict, list[Provider]]:
    """Generate the map PNG and sync provider drive-time zones with map colouring.

    Returns (map_image_src, iso_features, providers_in_radius) where drive_time_minutes
    on each provider has been overwritten with the exact zone value used to colour its dot.
    """
    log = logging.getLogger(__name__)
    try:
        provider_coords = [
            (p.latitude, p.longitude) for p in providers_in_radius if p.latitude is not None and p.longitude is not None
        ]
        result = await asyncio.to_thread(
            generate_map,
            token=settings.MAPBOX_API_KEY,
            source_lat=source_lat,
            source_lon=source_lon,
            providers=provider_coords,
            isochrones=list(mapbox._MAP_ISOCHRONES),
        )
        map_image_src = f"data:image/png;base64,{base64.b64encode(result['map_bytes']).decode()}"
        provider_zones: dict = result.get("provider_zones", {})
        for p in providers_in_radius:
            if p.latitude is not None and p.longitude is not None:
                zone = provider_zones.get((p.latitude, p.longitude))
                if zone is not None:
                    p.drive_time_minutes = zone
        iso_features = result.get("isochrones", iso_features)
        log.info("Map image generated (%d bytes)", len(result["map_bytes"]))
        return map_image_src, iso_features, providers_in_radius
    except Exception as exc:
        log.warning("Map generation failed — report will render without map: %s", exc)
        return None, iso_features, providers_in_radius


def _aggregate_cpt_data(
    providers_in_radius: list[Provider | SiteOfCare],
    cpt_codes: list[str],
    cpt_patient_type_map: dict[str, str],
    provider_state: str,
    rvu_table: dict,
    gpci_table: dict,
) -> _CptAggregation:
    """Aggregate CPT volume across all in-radius peers and build display rows."""

    # Guard against divide-by-zero when no providers have any recorded services.
    share_denom = sum(p.cpt_total_services for p in providers_in_radius) or 1

    # Pass 2 — classify locum and build share list
    # Set is_locum on all providers
    if providers_in_radius and type(providers_in_radius[0]) is Provider:
        for p in providers_in_radius:
            p.set_is_locum(share_denom)

    # SiteOfCare already has is_locum set appropriately,
    # so we can skip that step for the SiteOfCare list if that's what we're processing here.

    provider_shares = sorted(
        [
            ProviderShareEntry(
                share=round(p.cpt_total_services / share_denom * 100),
                taxonomy=p.taxonomy.description or "Unknown",
                drive_time_minutes=p.drive_time_minutes,
                is_locum=p.is_locum,
            )
            for p in providers_in_radius
        ],
        key=lambda e: e.share,
        reverse=True,
    )

    # Market-wide CPT aggregates
    agg_map: dict[str, CPT] = {code: CPT(code=code, totalServices=0, totalCharges=0.0) for code in cpt_codes}
    for p in providers_in_radius:
        for code in cpt_codes:
            cp = p.get_cpt_profile(code)
            if cp:
                agg_map[code].totalServices += max(cp.totalServices, 0)
                agg_map[code].totalCharges += max(cp.totalCharges, 0)
                agg_map[code].description = cp.description
                agg_map[code].codeType = cp.codeType

    sorted_agg = sorted(agg_map.values(), key=lambda c: c.totalServices, reverse=True)
    cpt_rows: list[CptRowV2] = []
    total_market_services = 0
    for agg in sorted_agg:
        vol = max(agg.totalServices, 0)
        total_market_services += vol
        rate = get_medicare_rate(str(agg.code), provider_state, rvu_table, gpci_table)
        cpt_rows.append(
            CptRowV2(
                code=str(agg.code),
                desc=agg.description,
                patientType=cpt_patient_type_map.get(str(agg.code)),
                medicareRate=f"${rate:,.2f}" if rate is not None else None,
                totalVolume=f"{vol:,}" if vol > 0 else None,
            )
        )

    return _CptAggregation(
        cpt_rows=cpt_rows,
        total_market_services=total_market_services,
        provider_shares=provider_shares,
        share_denom=share_denom,
    )


def _fetch_population_data(
    expanded_zips_df: pd.DataFrame,
    source_lat: float,
    source_lon: float,
    drive_time_minutes: int,
    providers_in_radius: list[Provider | SiteOfCare],
    specialty_name: str,
    fallback_zip: str,
) -> _PopulationData:
    """Fetch census demographics and compute relevant population for the specialty."""
    log = logging.getLogger(__name__)

    # Use a provider-independent isochrone so population is stable across runs.
    # Raw Mapbox polygon is already cached — no extra API call.
    snapped = min(round(drive_time_minutes / 5) * 5, 60)
    iso_polygon = None
    try:
        pop_iso = fetch_isochrones(
            lat=source_lat,
            lon=source_lon,
            token=settings.MAPBOX_API_KEY,
            minutes=[snapped],
            providers=(),
        )
        if snapped in pop_iso:
            iso_polygon = shape(pop_iso[snapped]["geometry"])
        elif pop_iso:
            iso_polygon = shape(pop_iso[max(pop_iso)]["geometry"])
    except Exception as exc:
        log.warning("Population isochrone fetch failed — centroid fallback in use: %s", exc)

    # Proportional ZIP area weighting: each ZIP contributes
    # (intersection_area / zcta_area) × its population.
    total_population = 0
    combined_demo: SexAgeCounts = {"M": {}, "F": {}, "Total": 0}
    zip_overlap_fractions: dict[str, float] = {}
    zip_scaled_populations: dict[str, int] = {}
    try:
        combined_demo, zip_overlap_fractions, zip_scaled_populations = get_population_in_polygon(
            iso_polygon=iso_polygon,
            candidate_zips=tuple(expanded_zips_df["zip"].astype(str).values),
            api_key=settings.CENSUS_API_KEY,
        )
        total_population = combined_demo["Total"]
        log.info("Population: %d across %d ZIPs", total_population, len(zip_overlap_fractions))
    except Exception as exc:
        log.error("Census demographics failed: %s", exc)

    # Searched-ZIPs list for the report footer (centroid-in-polygon, display only).
    if iso_polygon is not None:
        actual_zips_df = expanded_zips_df[
            expanded_zips_df.apply(lambda row: iso_polygon.contains(Point(row["lon"], row["lat"])), axis=1)
        ]
    else:
        in_radius_zips = {str(p.location.zip_code) for p in providers_in_radius}
        actual_zips_df = expanded_zips_df[expanded_zips_df["zip"].astype(str).isin(in_radius_zips)]

    if actual_zips_df.empty:
        actual_zips_df = pd.DataFrame(
            {"zip": [fallback_zip], "lat": [source_lat], "lon": [source_lon], "distance_from_source_miles": [0.0]}
        )

    # Specialty-specific population slice
    name_lower = specialty_name.lower()
    if "geriatric" in name_lower:
        relevant_pop = get_geriatric_population(combined_demo)
        population_label = "Geriatric (60+)"
    elif "pediatric" in name_lower:
        relevant_pop = get_pediatric_population(combined_demo)
        population_label = "Pediatric (0-24)"
    else:
        relevant_pop = total_population
        population_label = "General Population"

    return _PopulationData(
        total_population=total_population,
        relevant_pop=relevant_pop,
        population_label=population_label,
        combined_demo=combined_demo,
        zip_overlap_fractions=zip_overlap_fractions,
        zip_scaled_populations=zip_scaled_populations,
        actual_zips_df=actual_zips_df,
    )


def _compute_verdict(
    target_density: float | None,
    provider_gap: float,
    density_scope: str,
) -> _Verdict:
    """Map a provider gap to a GO / CAUTION / AVOID verdict.

    Thresholds: gap > +1 → opportunity (market underserved by more than one FTE),
    gap < -1 → avoid (market oversupplied by more than one FTE).
    The ±1 buffer treats near-parity as caution rather than a hard boundary,
    since density benchmarks themselves carry ~5–10 % margin of error.
    """
    if target_density is None:
        return _Verdict("caution", "N/A", "No density data available for this specialty/state.")
    if provider_gap > 1:
        return _Verdict(
            "opportunity",
            "GO",
            f"Underserved — {provider_gap:.1f} provider-equivalent gap vs. {density_scope.lower()} density baseline.",
        )
    if provider_gap < -1:
        return _Verdict(
            "avoid",
            "AVOID",
            f"Saturated — {abs(provider_gap):.1f} providers above {density_scope.lower()} density baseline.",
        )
    return _Verdict(
        "caution",
        "CAUTION",
        f"Market is near {density_scope.lower()} density baseline — limited opportunity.",
    )


def _build_debug_excel(
    providers_list: list[Provider],
    providers_in_radius: list[Provider],
    source_lat: float,
    source_lon: float,
    cpt_codes: list[str],
    job_id: str,
    sites_of_care: list | None = None,
) -> bytes | None:
    """Upload a debug Excel to S3 and return the raw bytes, or None on failure."""
    log = logging.getLogger(__name__)
    in_radius_ids = {p.id for p in providers_in_radius}

    def _provider_row(p: Provider) -> dict:
        row: dict = {
            "npi": p.npi,
            "name": p.name,
            "id": p.id,
            "address_line_1": p.location.address_line_1,
            "address_line_2": p.location.address_line_2,
            "city": p.location.city,
            "state": p.location.state,
            "zip_code": p.location.zip_code,
            "taxonomy_code": p.taxonomy.code,
            "taxonomy_description": p.taxonomy.description,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "distance_from_center_miles": round(p.distance_from_source_miles, 2)
            if p.distance_from_source_miles is not None
            else None,
            "drive_time_minutes": p.drive_time_minutes,
            "in_radius": p.id in in_radius_ids,
        }
        for code in cpt_codes:
            cpt = p.get_cpt_profile(code)
            row[f"cpt_{code}"] = cpt.totalServices if cpt else None
        return row

    def _soc_row(s) -> dict:
        row: dict = {
            "place_id": s.place_id,
            "name": s.name,
            "vicinity": s.vicinity,
            "phone": s.phone,
            "city": s.location.city,
            "state": s.location.state,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "taxonomy_code": s.taxonomy.code,
            "taxonomy_description": s.taxonomy.description,
            "is_locum": s.is_locum,
            "distance_from_center_miles": round(s.distance_from_source_miles, 2)
            if s.distance_from_source_miles is not None
            else None,
            "drive_time_minutes": s.drive_time_minutes,
            "npi_list": ", ".join(s.npi_list) if s.npi_list else None,
        }
        cpt_by_code = {c.code: c for c in s.cpt_list}
        for code in cpt_codes:
            cpt = cpt_by_code.get(code)
            row[f"cpt_{code}"] = cpt.totalServices if cpt else None
        return row

    try:
        buf = BytesIO()
        providers_df = pd.DataFrame(
            [{"npi": "source", "latitude": source_lat, "longitude": source_lon, "distance_from_center_miles": 0}]
            + [_provider_row(p) for p in providers_list]
        )
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            providers_df.to_excel(writer, sheet_name="Providers", index=False)
            if sites_of_care:
                pd.DataFrame([_soc_row(s) for s in sites_of_care]).to_excel(
                    writer, sheet_name="Sites of Care", index=False
                )
        excel_bytes = buf.getvalue()
        upload_debug_excel(job_id, excel_bytes)
        return excel_bytes
    except Exception as exc:
        log.warning("Failed to upload debug Excel: %s", exc)
        return None


# ── Public entry point ────────────────────────────────────────────────────────


async def run_html_report(
    payload: AddressReportRequest,
    state: ReportState,
    job_id: str = "",
    custom_cpt_codes: list[str] | None = None,
) -> tuple[str, bytes | None]:
    """Generate the Tier 0 HTML report from an address. Returns (html, debug_excel_bytes)."""
    # Manual set-up for backward compatibility
    use_site_of_care = True  # When True, group providers by site of care for all peer calculations

    log = logging.getLogger(__name__)

    # 1. Specialty metadata
    log.info("[1] Resolving specialty meta for '%s'", payload.specialty_name)
    meta = _resolve_specialty_meta(state, payload.specialty_name)
    # T2: override specialty CPT codes with caller-provided list
    effective_cpt_codes = custom_cpt_codes if custom_cpt_codes else meta.cpt_codes
    provider_state = payload.state

    # 2. Geocode
    log.info("[2] Geocoding address")
    source_lat, source_lon = await _geocode_with_fallback(payload, state.zip_centroids_df)

    # 3. Candidate ZIPs
    log.info("[3] Computing candidate ZIPs within %.0f-mile fetch radius", _DRIVE_TIME_FETCH_MILES)
    expanded_zips_df = _compute_candidate_zips(state.zip_centroids_df, source_lat, source_lon, payload.zip_code)
    log.info("[3] %d candidate ZIPs", len(expanded_zips_df))

    # 4+5. Fetch providers from AlphaSophia and enrich addresses/coords
    log.info("[4] Fetching and enriching providers across %d ZIPs", len(expanded_zips_df))
    providers_list = await _fetch_and_enrich_providers(expanded_zips_df, meta.taxonomy_codes, effective_cpt_codes)

    # 5.5 + 6. Stamp drive times and filter to radius (two-pass)
    log.info("[5] Stamping drive times and filtering to %d-min radius", payload.drive_time_minutes)
    providers_in_radius, iso_features = await _stamp_and_filter_providers(
        providers_list, source_lat, source_lon, payload.drive_time_minutes
    )

    # 7. Generate map
    log.info("[6] Generating map image")
    # iso_features is updated here with the canonical map isochrones and returned
    # for potential future use (e.g. passing GeoJSON directly into the report).
    map_image_src, iso_features, providers_in_radius = await _generate_map_image(
        providers_in_radius, source_lat, source_lon, iso_features
    )

    # 8. CPT profiles + debug dump
    log.info("[7] Fetching CPT profiles for %d in-radius providers", len(providers_in_radius))
    await asyncio.gather(*[p.fetch_cpt_profiles(effective_cpt_codes) for p in providers_in_radius])

    # Save debug as JSON for debugging.
    with open("providers.json", "w") as f:
        f.write(json.dumps([p.model_dump() for p in providers_in_radius], indent=2))

    _google_places_keywords = get_google_places_keywords(state.specialty_lookup, payload.specialty_name)
    _nearby_google_places = find_nearby_google_places(
        source_latitude=source_lat,
        source_longitude=source_lon,
        keywords=_google_places_keywords,
        # Google Places uses a straight-line radius, so we can be more generous here than the drive-time fetch radius.
        radius_miles=_DRIVE_TIME_FETCH_MILES * 1.5,
    )
    # Stamp Nearest Google Place on each Provider in Radius
    for p in providers_in_radius:
        p.stamp_nearest_google_place(_nearby_google_places)

    # Group providers by physical site; used as `peers` when use_site_of_care=True.
    _sites_of_care_list = get_sites_of_care_list(providers_in_radius)
    peers: list[Provider | SiteOfCare] = _sites_of_care_list if use_site_of_care else providers_in_radius
    # with open("_debug_nearby_google_places.json", "w") as f:
    #     f.write(json.dumps([p.model_dump() for p in _nearby_google_places], indent=2))

    # with open("_debug_sites_of_care.json", "w") as f:
    #     f.write(json.dumps([p.model_dump() for p in _sites_of_care_list], indent=2))

    debug_excel_bytes: bytes | None = None
    if job_id:
        debug_excel_bytes = _build_debug_excel(
            providers_list, providers_in_radius, source_lat, source_lon, effective_cpt_codes, job_id,
            sites_of_care=_sites_of_care_list,
        )

    # 9. Aggregate CPT data
    log.info("[8] Aggregating CPT data across %d peers", len(peers))
    cpt_agg = _aggregate_cpt_data(
        peers,
        effective_cpt_codes,
        meta.cpt_patient_type_map,
        provider_state,
        state.rvu_table,
        state.gpci_table,
    )
    locum_count = sum(1 for p in peers if p.is_locum)
    log.info("[8] %d CPT rows, market total: %d", len(cpt_agg.cpt_rows), cpt_agg.total_market_services)

    # 10. Population + demographics
    log.info("[9] Fetching census demographics")
    pop = _fetch_population_data(
        expanded_zips_df,
        source_lat,
        source_lon,
        payload.drive_time_minutes,
        peers,
        payload.specialty_name,
        payload.zip_code,
    )

    # 11. Verdict + density gap (locum providers excluded — they don't represent permanent market capacity)
    peer_providers_count = max(sum(1 for p in peers if not p.is_locum), 0)
    density_scope = get_density_scope(state.specialty_lookup, payload.specialty_name, provider_state)
    target_density = get_provider_density(state.specialty_lookup, payload.specialty_name, provider_state)
    if target_density is not None and pop.relevant_pop > 0:
        expected_providers = (pop.relevant_pop / 100_000) * target_density
        provider_gap = expected_providers - peer_providers_count
    else:
        expected_providers, provider_gap = 0.0, 0.0

    verdict = _compute_verdict(target_density, provider_gap, density_scope)

    # 12. LLM market analysis
    density_line = (
        f"The 2023 {density_scope.lower()} physician density for <strong>{payload.specialty_name}</strong> in "
        f"<strong>{provider_state}</strong> is "
        f"<strong>{target_density:.1f} providers per 100k residents</strong>, "
        f"implying <strong>{expected_providers:.1f} expected providers</strong> in this market. "
        f"There are currently <strong>{peer_providers_count} active providers</strong> "
        f"within {payload.drive_time_minutes} min drive, "
        f"leaving a gap of <strong>{provider_gap:+.1f} providers</strong>."
        if target_density is not None
        else f"No density data is available for <strong>{payload.specialty_name}</strong>"
        f" in <strong>{provider_state}</strong>."
    )
    fallback_analysis = (
        f"The {payload.city}, {payload.state} market has "
        f"<strong>{pop.total_population:,} total residents</strong>.<br><br>"
        f"{density_line}<br><br>"
        "Upgrade to the Strategic Code Report for complete market opportunity analysis."
    )

    competitor_drive_times = sorted(
        p.drive_time_minutes for p in peers if p.drive_time_minutes is not None
    )
    analysis_text = await generate_market_analysis(
        data=MarketAnalysisInput(
            city=payload.city,
            state=payload.state,
            specialty=payload.specialty_name,
            drive_time_minutes=payload.drive_time_minutes,
            total_population=pop.total_population,
            relevant_pop=pop.relevant_pop,
            population_label=pop.population_label,
            peer_providers_count=peer_providers_count,
            expected_providers=expected_providers,
            provider_gap=provider_gap,
            target_density=target_density,
            total_market_services=cpt_agg.total_market_services,
            provider_shares=cpt_agg.provider_shares,
            top_cpt_descriptions=[r.desc for r in cpt_agg.cpt_rows[:5] if r.desc],
            verdict_type=verdict.verdict_type,
            nearest_competitor_drive_min=competitor_drive_times[0] if competitor_drive_times else None,
            median_competitor_drive_min=competitor_drive_times[len(competitor_drive_times) // 2]
            if competitor_drive_times
            else None,
            providers_within_10_min=sum(1 for t in competitor_drive_times if t <= 10)
            if competitor_drive_times
            else None,
            provider_drive_volume_pairs=sorted(
                [
                    (p.drive_time_minutes, round(p.cpt_total_services / cpt_agg.share_denom * 100))
                    for p in peers
                    if p.drive_time_minutes is not None
                ],
                key=lambda x: x[0],
            ),
        ),
        fallback_text=fallback_analysis,
    )

    # 13. Assemble and render report
    report_id = job_id or f"MERC-{ulid.ulid()}"

    # Upgrades: T2 only shows the tier above it; T1 shows both upper tiers
    if custom_cpt_codes:
        upgrades = [
            Upgrade(
                price=T3_DISPLAY_PRICE,
                name="10-Code Full Analysis + Add-On",
                desc=(
                    "Complete procedure mix, NP/PA competitive presence, payer mix,"
                    " infrastructure sizing, and lease term optimization."
                ),
            ),
        ]
    else:
        upgrades = [
            Upgrade(
                price=T2_DISPLAY_PRICE,
                name="Through-the-Door Codes Report",
                desc=(
                    "Your 5 custom CPT codes benchmarked against every competitor within your drive time."
                    " Procedure-specific demand and visit-mix optimization."
                ),
            ),
            Upgrade(
                price=T3_DISPLAY_PRICE,
                name="10-Code Full Analysis + Add-On",
                desc=(
                    "Complete procedure mix, NP/PA competitive presence, payer mix,"
                    " infrastructure sizing, and lease term optimization."
                ),
            ),
        ]

    report_data = ReportTemplateDataV2(
        reportId=report_id,
        dateIssued=pd.Timestamp.now().strftime("%m/%d/%Y"),
        specialty=payload.specialty_name,
        market=f"{payload.zip_code} {payload.city}, {payload.state}",
        radius=f"{payload.drive_time_minutes} min drive",
        reportTier="Market Entry",
        address=f"{payload.address_line_1} {payload.address_line_2 if payload.address_line_2 else ''}",
        clientName="",
        tags=generate_tags(cpt_agg.cpt_rows),
        verdictType=verdict.verdict_type,
        verdictValue=verdict.verdict_value,
        verdictSub=verdict.verdict_sub,
        totalPopulation=f"{pop.total_population:,}" if pop.total_population > 0 else "N/A",
        relevantPopulation=f"{pop.relevant_pop:,}" if pop.relevant_pop > 0 else "N/A",
        populationLabel=pop.population_label,
        currentProviders=peer_providers_count,
        targetDensity=round(expected_providers, 1),
        providerGap=round(provider_gap, 1),
        cptRows=cpt_agg.cpt_rows,
        cptTotalVisits=f"{cpt_agg.total_market_services:,}",
        analysisText=analysis_text,
        upgrades=upgrades,
        providerProfile=ProviderProfileV2(annualVisits=None),
        competitorCount=peer_providers_count,
        locumCount=locum_count,
        showRelevantPopulation=pop.relevant_pop != pop.total_population,
        taxonomyCodes=meta.taxonomy_codes,
        searchedZipCodes=[
            f"{z} ({round(pop.zip_overlap_fractions[z] * 100)}% · {pop.zip_scaled_populations.get(z, 0):,} pop)"
            if z in pop.zip_overlap_fractions
            else z
            for z in sorted(pop.zip_overlap_fractions) or pop.actual_zips_df["zip"].astype(str).tolist()
        ],
        sourceTabs=meta.source_tabs,
        peerNpis=(
            [npi for s in peers for npi in s.npi_list]  # type: ignore[union-attr]
            if use_site_of_care
            else [p.npi for p in peers if p.npi]  # type: ignore[union-attr]
        ),
        providerShares=cpt_agg.provider_shares,
        mapImageSrc=map_image_src,
        densityScope=density_scope,
    )

    html = render_report("T1", report_data)
    log.info("[10] Done — T1 report '%s' rendered (%d bytes)", report_id, len(html))
    return html, debug_excel_bytes
