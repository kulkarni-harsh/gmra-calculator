"""
Tier 0 report generator.

Generates the V3 market baseline report from an address + specialty alone.
No provider NPI lookup — market-level aggregate only.
"""

import asyncio
import base64
import logging
from functools import reduce
from io import BytesIO

import pandas as pd
import ulid
from geopy.distance import geodesic

from app.core.config import settings
from app.core.types import SexAgeCounts
from app.schemas.address_report_request import AddressReportRequest
from app.services.alphasophia import get_hcp_data
from app.services.bedrock_llm import MarketAnalysisInput, generate_market_analysis
from app.services.census import combine_demographics, get_zip_demographics
from app.services.fee_schedule import get_medicare_rate
from app.services.geocoder import geocode_address
from app.services.html_imputers.v3_imputer import replace_data_block_v3
from app.services.mapbox import generate_map, stamp_provider_drive_times
from app.services.report_generator import ReportState
from app.services.s3 import upload_debug_excel
from app.types.alphasophia import CPT, Provider
from app.types.baseline_report_template import CptRowV2, ProviderProfileV2, ReportTemplateDataV2, Upgrade
from app.utils.common import (
    generate_tags,
    get_anchor_cpt_codes,
    get_anchor_cpt_patient_type_map,
    get_geriatric_population,
    get_pediatric_population,
    get_provider_density,
    get_source_tabs,
    get_taxonomy_codes,
)

# ── Drive-time fetch constants ────────────────────────────────────────────────
# Max drive-time option is 60 min. At ~50 mph average, 60 min ≈ 50 miles.
# Always fetch providers within this fixed radius; drive-time filter happens after stamping.
_DRIVE_TIME_FETCH_MILES: float = 50.0
# Approximate miles per minute (50 mph average) — used to scale census ZIP radius.
_APPROX_MILES_PER_MINUTE: float = 50.0 / 60.0


async def run_t0_report(
    payload: AddressReportRequest,
    state: ReportState,
    job_id: str = "",
) -> tuple[str, bytes | None]:
    """Generate the Tier 0 V3 HTML report from an address. Returns (html, debug_excel_bytes)."""
    log = logging.getLogger(__name__)

    log.info("[1/10] Resolving CPT codes and taxonomy for specialty '%s'", payload.specialty_name)
    relevant_cpt_codes_list = get_anchor_cpt_codes(state.anchor_cpt_lookup, payload.specialty_name)
    cpt_patient_type_map = get_anchor_cpt_patient_type_map(state.anchor_cpt_lookup)
    taxonomy_codes = get_taxonomy_codes(state.specialty_lookup, payload.specialty_name)
    source_tabs = get_source_tabs(state.specialty_lookup, payload.specialty_name)
    provider_state = payload.state

    log.info("[2/10] Geocoding address: '%s %s, %s %s'",
             payload.address_line_1, payload.city, payload.state, payload.zip_code)
    address_str = (
        f"{payload.address_line_1} "
        f"{payload.address_line_2 + ' ' if payload.address_line_2 else ''}"
        f"{payload.city}, {payload.state} {payload.zip_code}"
    ).strip()

    coords = await geocode_address(address_str, settings.MAPBOX_API_KEY)
    if coords is None:
        # Fall back to ZIP centroid
        zip_row = state.zip_centroids_df[state.zip_centroids_df["zip"].astype(str) == payload.zip_code]
        if zip_row.empty:
            raise ValueError(f"Could not geocode address and no ZIP centroid found for {payload.zip_code}")
        source_lat = float(zip_row.iloc[0]["lat"])
        source_lon = float(zip_row.iloc[0]["lon"])
        log.warning("[2/10] Geocoding failed — fell back to ZIP centroid (%.4f, %.4f)", source_lat, source_lon)
    else:
        source_lat, source_lon = coords
        log.info("[2/10] Geocoded to lat=%.4f, lon=%.4f", source_lat, source_lon)

    log.info("[3/10] Computing ZIP distances from geocoded location")
    zip_centroids_df = state.zip_centroids_df.copy()
    zip_centroids_df["distance_from_source_miles"] = zip_centroids_df.apply(
        lambda row: geodesic((source_lat, source_lon), (row["lat"], row["lon"])).miles,
        axis=1,
    )

    expanded_zips_df = zip_centroids_df[zip_centroids_df["distance_from_source_miles"] <= _DRIVE_TIME_FETCH_MILES]
    if expanded_zips_df.empty:
        expanded_zips_df = pd.DataFrame({
            "zip": [payload.zip_code],
            "lat": [source_lat],
            "lon": [source_lon],
            "distance_from_source_miles": [0.0],
        })
    log.info("[3/10] Done — %d ZIP codes within %.0f-mile fetch radius", len(expanded_zips_df), _DRIVE_TIME_FETCH_MILES)

    log.info("[4/10] Fetching providers from AlphaSophia across %d ZIP codes", len(expanded_zips_df))
    providers_list: list[Provider] = []
    try:
        providers_list = await get_hcp_data(
            zip_codes_list=expanded_zips_df["zip"].dropna().astype(str).tolist(),
            taxonomy_codes_list=taxonomy_codes,
            npi_list=[],
            cpt_codes_list=relevant_cpt_codes_list,
            page_size=100,
        )
        log.info("[4/10] Done — fetched %d providers from AlphaSophia", len(providers_list))
    except Exception as exc:
        log.error("[4/10] AlphaSophia fetch failed: %s", exc)

    log.info("[5/10] Enriching %d provider addresses and coordinates", len(providers_list))

    async def _enrich(p: Provider) -> None:
        await p.update_address_and_zip()
        await p.update_lat_long()

    await asyncio.gather(*[_enrich(p) for p in providers_list])
    log.info("[5/10] Done — addresses resolved")

    log.info("[5.5/10] Stamping drive times from source to %d enriched providers", len(providers_list))
    try:
        await asyncio.to_thread(
            stamp_provider_drive_times,
            source_lat,
            source_lon,
            providers_list,
            settings.MAPBOX_API_KEY,
        )
        log.info("[5.5/10] Done — drive times stamped")
    except Exception as exc:
        log.warning("[5.5/10] Drive time stamping failed — drive-time filter will exclude all providers: %s", exc)

    log.info("[6/10] Filtering providers to drive time <= %d min", payload.drive_time_minutes)
    providers_in_radius: list[Provider] = []
    for p in providers_list:
        if p.latitude is None or p.longitude is None:
            continue
        p.distance_from_source_miles = geodesic(
            (p.latitude, p.longitude), (source_lat, source_lon)
        ).miles
        if p.drive_time_minutes is not None and p.drive_time_minutes <= payload.drive_time_minutes:
            providers_in_radius.append(p)
    log.info("[6/10] Done — %d providers within %d min drive", len(providers_in_radius), payload.drive_time_minutes)

    log.info("[7/10] Generating map image")
    map_image_src: str | None = None
    try:
        map_bytes = await asyncio.to_thread(
            generate_map,
            token=settings.MAPBOX_API_KEY,
            source_lat=source_lat,
            source_lon=source_lon,
            providers=providers_in_radius,
        )
        map_image_src = f"data:image/png;base64,{base64.b64encode(map_bytes).decode()}"
        log.info("[7/10] Map image generated (%d bytes)", len(map_bytes))
    except Exception as exc:
        log.warning("[7/10] Map generation failed — report will render without map: %s", exc)

    log.info("[8/10] Fetching CPT profiles for %d in-radius providers", len(providers_in_radius))
    await asyncio.gather(*[p.fetch_cpt_profiles(relevant_cpt_codes_list) for p in providers_in_radius])
    log.info("[8/10] Done — CPT profiles fetched")

    # ── Debug dump ────────────────────────────────────────────────────────────
    debug_excel_bytes: bytes | None = None
    if job_id:
        try:
            def _row(p: Provider) -> dict:
                row = {
                    "npi": p.npi, "name": p.name,
                    "lat": p.latitude, "lon": p.longitude,
                    "distance_mi": round(p.distance_from_source_miles, 2) if p.distance_from_source_miles else None,
                }
                for code in relevant_cpt_codes_list:
                    cpt = p.get_cpt_profile(code)
                    row[f"cpt_{code}"] = cpt.totalServices if cpt else None
                return row

            buf = BytesIO()
            pd.DataFrame([_row(p) for p in providers_list]).to_excel(buf, index=False, engine="openpyxl")
            debug_excel_bytes = buf.getvalue()
            upload_debug_excel(job_id, debug_excel_bytes)
        except Exception as exc:
            log.warning("[debug] Failed to upload Excel: %s", exc)
    # ── end debug dump ────────────────────────────────────────────────────────

    log.info("[9/10] Aggregating CPT data across %d providers", len(providers_in_radius))
    peer_providers_count = max(len(providers_in_radius), 1)

    # Provider share distribution (all peers, no client)
    provider_raw_totals: list[int] = []
    for p in providers_in_radius:
        total = sum(
            (p.get_cpt_profile(code).totalServices or 0)
            for code in relevant_cpt_codes_list
            if p.get_cpt_profile(code)
        )
        p.cpt_total_services = total
        provider_raw_totals.append(total)

    _share_denom = sum(provider_raw_totals) or 1
    provider_shares: list[int] = sorted(
        [round(t / _share_denom * 100) for t in provider_raw_totals],
        reverse=True,
    )

    # Aggregate CPT totals
    agg_cpt_list: list[CPT] = []
    for code in relevant_cpt_codes_list:
        agg = CPT(code=code, totalServices=0, totalCharges=0.0)
        for p in providers_in_radius:
            cp = p.get_cpt_profile(code)
            if cp:
                agg.totalServices += cp.totalServices if cp.totalServices > 0 else 0
                agg.totalCharges += cp.totalCharges if cp.totalCharges > 0 else 0
                agg.description = cp.description
                agg.codeType = cp.codeType
        agg_cpt_list.append(agg)

    agg_cpt_list.sort(key=lambda c: c.totalServices, reverse=True)

    cpt_rows: list[CptRowV2] = []
    total_market_services = 0
    for agg_cpt in agg_cpt_list:
        vol = agg_cpt.totalServices if agg_cpt.totalServices > 0 else 0
        total_market_services += vol
        medicare_rate = get_medicare_rate(
            str(agg_cpt.code), provider_state, state.rvu_table, state.gpci_table
        )
        cpt_rows.append(
            CptRowV2(
                code=str(agg_cpt.code),
                desc=agg_cpt.description,
                patientType=cpt_patient_type_map.get(str(agg_cpt.code)),
                medicareRate=f"${medicare_rate:,.2f}" if medicare_rate is not None else None,
                totalVolume=f"{vol:,}" if vol > 0 else None,
            )
        )
    log.info("[9/10] Done — %d CPT rows, market total: %d", len(cpt_rows), total_market_services)

    log.info("[10/10] Fetching census demographics + rendering report")
    _census_miles = payload.drive_time_minutes * _APPROX_MILES_PER_MINUTE
    actual_zips_df = zip_centroids_df[zip_centroids_df["distance_from_source_miles"] <= _census_miles]
    if actual_zips_df.empty:
        actual_zips_df = pd.DataFrame({
            "zip": [payload.zip_code], "lat": [source_lat], "lon": [source_lon],
            "distance_from_source_miles": [0.0],
        })

    total_population = 0
    try:
        zip_demo_dict = get_zip_demographics(
            tuple(actual_zips_df["zip"].astype(str).values),
            settings.CENSUS_API_KEY,
        )
        combined_demo: SexAgeCounts = reduce(combine_demographics, zip_demo_dict.values())
        total_population = combined_demo["Total"]
    except Exception as exc:
        log.error("[10/10] Census demographics failed: %s", exc)
        combined_demo = SexAgeCounts({"M": {}, "F": {}, "Total": 0})

    if "geriatric" in payload.specialty_name.lower():
        relevant_pop = get_geriatric_population(combined_demo)
        population_label = "Geriatric (60+)"
    elif "pediatric" in payload.specialty_name.lower():
        relevant_pop = get_pediatric_population(combined_demo)
        population_label = "Pediatric (0-24)"
    else:
        relevant_pop = total_population
        population_label = "General Population"

    target_density = get_provider_density(state.specialty_lookup, payload.specialty_name, provider_state)
    if target_density is not None and relevant_pop > 0:
        expected_providers = (relevant_pop / 100_000) * target_density
        provider_gap = expected_providers - peer_providers_count
    else:
        expected_providers = 0.0
        provider_gap = 0.0

    if target_density is None:
        verdict_type, verdict_value = "caution", "N/A"
        verdict_sub = "No state-level density data available for this specialty/state."
    elif provider_gap > 1:
        verdict_type, verdict_value = "opportunity", "GO"
        verdict_sub = f"Underserved — {provider_gap:.1f} provider-equivalent gap vs. state density baseline."
    elif provider_gap < -1:
        verdict_type, verdict_value = "avoid", "AVOID"
        verdict_sub = f"Saturated — {abs(provider_gap):.1f} providers above state density baseline."
    else:
        verdict_type, verdict_value = "caution", "CAUTION"
        verdict_sub = "Market is near state density baseline — limited opportunity."

    report_id = job_id or f"MERC-{ulid.ulid()}"

    density_line = (
        f"The 2023 state-level physician density for <strong>{payload.specialty_name}</strong> in "
        f"<strong>{provider_state}</strong> is "
        f"<strong>{target_density:.1f} providers per 100k residents</strong>, "
        f"implying <strong>{expected_providers:.1f} expected providers</strong> in this market. "
        f"There are currently <strong>{peer_providers_count} active providers</strong> "
        f"within {payload.drive_time_minutes} min drive, "
        f"leaving a gap of <strong>{provider_gap:+.1f} providers</strong>."
        if target_density is not None
        else f"No state-level density data is available for <strong>{payload.specialty_name}</strong>"
             f" in <strong>{provider_state}</strong>."
    )
    _fallback_analysis = (
        f"The {payload.city}, {payload.state} market has "
        f"<strong>{total_population:,} total residents</strong>."
        "<br><br>"
        f"{density_line}"
        "<br><br>"
        "Upgrade to the Strategic Code Report for complete market opportunity analysis."
    )

    _top_cpt_descs = [row.desc for row in cpt_rows[:5] if row.desc]

    # ── Geographic distribution of competitors (drive time) ───────────────
    # drive_time_minutes is set by generate_map() via the Matrix API; fall back
    # to None if the map step was skipped or a provider had no valid route.
    competitor_drive_times = sorted(
        p.drive_time_minutes
        for p in providers_in_radius
        if p.drive_time_minutes is not None
    )
    _nearest_competitor_drive_min: float | None = competitor_drive_times[0] if competitor_drive_times else None
    _median_competitor_drive_min: float | None = (
        competitor_drive_times[len(competitor_drive_times) // 2] if competitor_drive_times else None
    )
    _providers_within_10_min: int | None = (
        sum(1 for t in competitor_drive_times if t <= 10)
        if competitor_drive_times else None
    )

    _provider_drive_vol_pairs: list[tuple[float, int]] = sorted(
        [
            (p.drive_time_minutes, round(p.cpt_total_services / _share_denom * 100))
            for p in providers_in_radius
            if p.drive_time_minutes is not None
        ],
        key=lambda x: x[0],
    )

    analysis_text = await generate_market_analysis(
        data=MarketAnalysisInput(
            city=payload.city,
            state=payload.state,
            specialty=payload.specialty_name,
            drive_time_minutes=payload.drive_time_minutes,
            total_population=total_population,
            relevant_pop=relevant_pop,
            population_label=population_label,
            peer_providers_count=peer_providers_count,
            expected_providers=expected_providers,
            provider_gap=provider_gap,
            target_density=target_density,
            total_market_services=total_market_services,
            provider_shares=provider_shares,
            top_cpt_descriptions=_top_cpt_descs,
            verdict_type=verdict_type,
            nearest_competitor_drive_min=_nearest_competitor_drive_min,
            median_competitor_drive_min=_median_competitor_drive_min,
            providers_within_10_min=_providers_within_10_min,
            provider_drive_volume_pairs=_provider_drive_vol_pairs,
        ),
        fallback_text=_fallback_analysis,
    )

    show_relevant_population = relevant_pop != total_population

    report_data = ReportTemplateDataV2(
        reportId=report_id,
        dateIssued=pd.Timestamp.now().strftime("%m/%d/%Y"),
        specialty=payload.specialty_name,
        market=f"{payload.city}, {payload.state}",
        radius=f"{payload.drive_time_minutes} min drive",
        reportTier="Market Entry",
        address=f"{payload.address_line_1} {payload.address_line_2 if payload.address_line_2 else ''}",
        clientName="",  # no named client for T0
        tags=generate_tags(cpt_rows),
        verdictType=verdict_type,
        verdictValue=verdict_value,
        verdictSub=verdict_sub,
        totalPopulation=f"{total_population:,}" if total_population > 0 else "N/A",
        relevantPopulation=f"{relevant_pop:,}" if relevant_pop > 0 else "N/A",
        populationLabel=population_label,
        currentProviders=peer_providers_count,
        targetDensity=round(expected_providers, 1),
        providerGap=round(provider_gap, 1),
        cptRows=cpt_rows,
        cptTotalVisits=f"{total_market_services:,}",
        analysisText=analysis_text,
        upgrades=[
            Upgrade(
                price="$599",
                name="5-Code Strategic Report",
                desc=(
                    "Top 5 CPT codes by procedure volume analyzed against this specific market."
                    " Procedure-specific demand and visit-mix optimization."
                ),
            ),
            Upgrade(
                price="$799",
                name="10-Code Full Analysis + Add-On",
                desc=(
                    "Complete procedure mix, NP/PA competitive presence, payer mix,"
                    " infrastructure sizing, and lease term optimization."
                ),
            ),
        ],
        providerProfile=ProviderProfileV2(annualVisits=None),
        competitorCount=peer_providers_count,
        showRelevantPopulation=show_relevant_population,
        taxonomyCodes=taxonomy_codes,
        searchedZipCodes=actual_zips_df["zip"].astype(str).tolist(),
        sourceTabs=source_tabs,
        peerNpis=[p.npi for p in providers_in_radius if p.npi],
        providerShares=provider_shares,
        mapImageSrc=map_image_src,
    )

    template_html = (settings.TEMPLATES_DIR / "MREC_Report_TEMPLATE_T0.html").read_text(encoding="utf-8")
    html = replace_data_block_v3(template_html, report_data)
    log.info("[10/10] Done — T0 report '%s' rendered (%d bytes)", report_id, len(html))
    return html, debug_excel_bytes
