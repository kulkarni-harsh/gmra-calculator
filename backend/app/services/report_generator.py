"""
Core report generation logic, decoupled from the HTTP request/response layer.

Both the HTTP endpoint (for future sync use) and the async worker call run_report().
State is loaded once at startup and passed in — no global singletons.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from functools import reduce
from io import BytesIO

import pandas as pd
from geopy.distance import geodesic

from app.core.config import settings
from app.core.types import SexAgeCounts
from app.schemas.provider_request import ProviderRequest
from app.services.alphasophia import get_hcp_data
from app.services.census import combine_demographics, get_zip_demographics
from app.services.fee_schedule import get_medicare_rate
from app.services.html_imputers.v2_imputer import replace_data_block_v2
from app.services.s3 import upload_debug_excel
from app.types.alphasophia import CPT, Provider
from app.types.baseline_report_template import CptRowV2, ProviderProfileV2, ReportTemplateDataV2, Upgrade
from app.utils.common import (
    generate_tags,
    get_anchor_cpt_codes,
    get_geriatric_population,
    get_pediatric_population,
    get_provider_density,
    get_source_tabs,
    get_taxonomy_codes,
    load_fee_schedule_tables,
)
from app.utils.validator import validate_speciality_master_df


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
    from opencage.geocoder import OpenCageGeocode  # noqa: F401 — imported for side-effects in alphasophia

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


async def run_report(payload: ProviderRequest, state: ReportState, job_id: str = "") -> tuple[str, bytes | None]:
    """Generate the HTML report and return it as a string."""

    log = logging.getLogger(__name__)

    log.info("[1/10] Resolving CPT codes and taxonomy for specialty '%s'", payload.specialty_name)

    # Get relevant CPT codes list, Taxonomy Codes & Source Tabs from where we got provider density info
    relevant_cpt_codes_list = get_anchor_cpt_codes(state.anchor_cpt_lookup, payload.specialty_name)
    taxonomy_codes = get_taxonomy_codes(state.specialty_lookup, payload.specialty_name)
    source_tabs = get_source_tabs(state.specialty_lookup, payload.specialty_name)
    provider_state = payload.client_provider.location.state or ""

    log.info(
        "[1/10] Done — %d CPT codes, %d taxonomy codes, %d source tabs",
        len(relevant_cpt_codes_list),
        len(taxonomy_codes),
        len(source_tabs),
    )

    log.info(
        "[2/10] Resolving client provider address, lat/long, and CPT profiles (NPI=%s)", payload.client_provider.id
    )
    # Get client provider address, lat/long
    await payload.client_provider.update_address_and_zip()
    await payload.client_provider.update_lat_long()
    log.info(
        "[2/10] Client provider geocoded — lat=%.4f, lon=%.4f",
        payload.client_provider.latitude or 0,
        payload.client_provider.longitude or 0,
    )
    # Fetch client provider's procedure count for relevant CPT codes
    await payload.client_provider.fetch_cpt_profiles(relevant_cpt_codes_list)
    log.info("[2/10] Done — client CPT profiles fetched")

    log.info("[3/10] Computing ZIP distances from client provider location")
    # Compute the distance between client provider and each ZIP
    zip_centroids_df = state.zip_centroids_df.copy()
    zip_centroids_df["distance_from_source_miles"] = zip_centroids_df.apply(
        lambda row: geodesic(
            (payload.client_provider.latitude, payload.client_provider.longitude),
            (row["lat"], row["lon"]),
        ).miles,
        axis=1,
    )

    # Find out providers within 2x radius, so we can geocode them later and get miles distance
    # 2x radius here is to avoid missing some providers that are outside of 1x ZIP search radius,
    # but are within the 1x distance based on the client and its coordinates
    expanded_zips_df = zip_centroids_df[zip_centroids_df["distance_from_source_miles"] <= 2 * payload.miles_radius]
    if expanded_zips_df.empty:
        log.warning(
            "[3/10] No ZIP codes found within 2× radius (%d mi). Falling back to input ZIP only.",
            2 * payload.miles_radius,
        )
        expanded_zips_df = pd.DataFrame(
            {
                "zip": [payload.client_provider.zip_code],
                "lat": [payload.client_provider.latitude],
                "lon": [payload.client_provider.longitude],
                "distance_from_source_miles": [0.0],
            }
        )
    log.info("[3/10] Done — %d ZIP codes in 2× search radius (%d mi)", len(expanded_zips_df), 2 * payload.miles_radius)

    log.info(
        "[4/10] Fetching providers from AlphaSophia across %d ZIP codes (next step: enrich addresses)",
        len(expanded_zips_df),
    )
    # Fetch all providers that are in ZIPs within 2x radius
    expanded_providers_list: list[Provider]
    try:
        expanded_providers_list = await get_hcp_data(
            zip_codes_list=expanded_zips_df["zip"].dropna().astype(str).tolist(),
            taxonomy_codes_list=taxonomy_codes,
            npi_list=[],
            cpt_codes_list=relevant_cpt_codes_list,
            page_size=100,
        )
        # Ensure we don't include the client provider, as its data is already included in payload
        expanded_providers_list = [
            p for p in expanded_providers_list if isinstance(p, Provider) and p.id != payload.client_provider.id
        ]
        log.info("[4/10] Done — fetched %d providers from AlphaSophia (2× radius)", len(expanded_providers_list))
    except Exception as exc:
        log.error("[4/10] Failed to fetch providers from AlphaSophia: %s", exc)
        expanded_providers_list = []

    log.info("[5/10] Enriching %d provider addresses and coordinates in parallel", len(expanded_providers_list))

    # Enrich provider addresses with Address 1 ,2, ZIP & coordinates
    async def _enrich_provider(p: Provider) -> None:
        await p.update_address_and_zip()
        await p.update_lat_long()

    await asyncio.gather(*[_enrich_provider(p) for p in expanded_providers_list])
    log.info("[5/10] Done — all provider addresses resolved")

    log.info("[6/10] Filtering providers to actual radius of %d mi", payload.miles_radius)
    # Filter providers within 1x radius
    # Skip providers that don't have coordinates
    providers_in_radius: list[Provider] = []
    skipped_no_coords = 0
    for _result in expanded_providers_list:
        if _result.latitude is None or _result.longitude is None:
            skipped_no_coords += 1
            continue
        _result.distance_from_source_miles = geodesic(
            (_result.latitude, _result.longitude),
            (payload.client_provider.latitude, payload.client_provider.longitude),
        ).miles
        if _result.distance_from_source_miles <= payload.miles_radius:
            providers_in_radius.append(_result)

    log.info(
        "[6/10] Done — %d providers within %d mi radius (skipped %d with no coords)",
        len(providers_in_radius),
        payload.miles_radius,
        skipped_no_coords,
    )

    log.info("[7/10] Fetching CPT profiles for %d in-radius competitors", len(providers_in_radius))
    # Fetch procedure count for relevant CPT codes in each in-radius provider
    await asyncio.gather(*[p.fetch_cpt_profiles(relevant_cpt_codes_list) for p in providers_in_radius])
    log.info("[7/10] Done — competitor CPT profiles fetched")

    # ── Debug dump: all expanded providers → S3 Excel ────────────────────────
    debug_excel_bytes: bytes | None = None
    if job_id:
        try:
            in_radius_ids = {p.id for p in providers_in_radius}

            def _provider_row(p: Provider) -> dict:
                if p.id == payload.client_provider.id:
                    in_radius_value: str | bool = "Source"
                else:
                    in_radius_value = p.id in in_radius_ids
                row = {
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
                    "in_radius": in_radius_value,
                }
                for cpt_code in relevant_cpt_codes_list:
                    cpt = p.get_cpt_profile(cpt_code)
                    row[f"cpt_{cpt_code}_services"] = cpt.totalServices if cpt else None
                return row

            rows = [_provider_row(payload.client_provider)]
            for p in expanded_providers_list:
                rows.append(_provider_row(p))

            debug_df = pd.DataFrame(rows)
            buf = BytesIO()
            debug_df.to_excel(buf, index=False, engine="openpyxl")
            debug_excel_bytes = buf.getvalue()
            upload_debug_excel(job_id, debug_excel_bytes)
            log.info("[debug] Provider Excel uploaded for job %s (%d rows)", job_id, len(rows))
        except Exception as _exc:
            log.warning("[debug] Failed to upload provider Excel: %s", _exc)
    # ── end debug dump ────────────────────────────────────────────────────────

    log.info("[8/10] Aggregating CPT data across %d providers", len(providers_in_radius))
    # Aggregate the count of relevant CPT codes for each compeititor provider
    agg_cpt_list: list[CPT] = []
    for _cpt in relevant_cpt_codes_list:
        agg_cpt = CPT(code=_cpt, totalServices=0, totalCharges=0.0)
        for _p in providers_in_radius:
            _p_cpt = _p.get_cpt_profile(_cpt)
            if _p_cpt:
                agg_cpt.totalServices += _p_cpt.totalServices if _p_cpt.totalServices > 0 else 0
                agg_cpt.totalCharges += _p_cpt.totalCharges if _p_cpt.totalCharges > 0 else 0
                agg_cpt.description = _p_cpt.description
                agg_cpt.codeType = _p_cpt.codeType
        agg_cpt_list.append(agg_cpt)

    # Get the count of providers in the market
    peer_providers_count = max(len(providers_in_radius), 1)

    # Create a triplet of [competitor CPT, client CPT, medicare rate for that CPT]
    cpt_triples: list[tuple[CPT, CPT, float | None]] = []
    for _agg_cpt in agg_cpt_list:
        client_cpt: CPT = payload.client_provider.get_cpt_profile(str(_agg_cpt.code)) or CPT(
            code=_agg_cpt.code, totalServices=0, totalCharges=0.0
        )
        medicare_rate: float | None = get_medicare_rate(
            str(_agg_cpt.code),
            provider_state,
            state.rvu_table,
            state.gpci_table,
        )
        cpt_triples.append((_agg_cpt, client_cpt, medicare_rate))

    # Sort the CPTs by number of services
    cpt_triples.sort(key=lambda t: t[1].totalServices, reverse=True)

    # Create a list of CPT rows
    cpt_rows: list[CptRowV2] = []
    (
        total_client_services,
        total_peer_services,  # exlcudes client
        total_market_services,  # Client + Peer
    ) = (0, 0, 0)
    # For each CPT, create a CPT row
    for agg_cpt, client_cpt, medicare_rate in cpt_triples:
        # Get the count of services for this CPT
        peer_services = agg_cpt.totalServices if agg_cpt.totalServices > 0 else 0
        client_services = client_cpt.totalServices if client_cpt.totalServices > 0 else 0
        peer_avg_services = peer_services / peer_providers_count

        # Keep trakc of total procedures count
        total_peer_services += peer_services
        total_client_services += client_services
        total_market_services += client_services + peer_services

        cpt_rows.append(
            # Store the code, description, medicare rate, client volume & peer avg volume
            CptRowV2(
                code=str(agg_cpt.code),
                desc=agg_cpt.description,
                medicareRate=f"${medicare_rate:,.2f}" if medicare_rate is not None else None,
                totalVolume=f"{(int(peer_services) + int(client_services)):,}"
                if (peer_services + client_services) > 0
                else None,
                clientVolume=f"{client_services:,}" if client_services else None,
                peerAvgVolume=f"{int(peer_avg_services):,}" if peer_avg_services else None,
                diffVolume=int(peer_avg_services) - int(client_services),
            )
        )
    # Keep track of total market services
    log.info("[8/10] Done — %d CPT rows built, market total: %d services", len(cpt_rows), total_market_services)

    # cpt_total_visits = f"{int(total_market_services):,} visits/yr"

    log.info(
        "[9/10] Fetching census demographics for %d ZIP codes in exact radius",
        len(zip_centroids_df[zip_centroids_df["distance_from_source_miles"] <= payload.miles_radius]),
    )
    actual_zips_df = zip_centroids_df[zip_centroids_df["distance_from_source_miles"] <= payload.miles_radius]
    if actual_zips_df.empty:
        log.warning("[9/10] No ZIPs in exact radius — falling back to client ZIP only")
        actual_zips_df = pd.DataFrame(
            {
                "zip": [str(payload.client_provider.location.zip_code)],
                "lat": [payload.client_provider.latitude],
                "lon": [payload.client_provider.longitude],
                "distance_from_source_miles": [0.0],
            }
        )

    combined_demo: SexAgeCounts
    total_population: int
    try:
        zip_demographic_dict = get_zip_demographics(
            tuple(actual_zips_df["zip"].astype(str).values),
            settings.CENSUS_API_KEY,
        )
        combined_demo = reduce(combine_demographics, zip_demographic_dict.values())
        total_population = combined_demo["Total"]
        log.info("[9/10] Done — total population across %d ZIPs: %d", len(actual_zips_df), total_population)
    except Exception as exc:
        log.error("[9/10] Failed to get demographics: %s", exc)
        combined_demo = SexAgeCounts({"M": {}, "F": {}, "Total": 0})
        total_population = 0

    # relevant_pop, population_label = total_population, "All ages"
    if "geriatric" in payload.specialty_name.lower():
        logging.info("[9/10] Checking for geriatric population")
        relevant_pop = get_geriatric_population(combined_demo)
        population_label = "Geriatric (60+)"
    elif "pediatric" in payload.specialty_name.lower():
        logging.info("[9/10] Checking for pediatric population")
        population_label = "Pediatric (0-24)"
        relevant_pop = get_pediatric_population(combined_demo)
    else:
        logging.info("[9/10] Checking for general population")
        population_label = "General Population"
        relevant_pop = total_population

    target_density = get_provider_density(state.specialty_lookup, payload.specialty_name, provider_state)

    if target_density is not None and relevant_pop > 0:
        expected_providers = (relevant_pop / 100_000) * target_density
        provider_gap = expected_providers - (peer_providers_count + 1)
    else:
        expected_providers = 0.0
        provider_gap = 0.0

    if target_density is None:
        verdict_type = "caution"
        verdict_value = "N/A"
        verdict_sub = "No state-level density data available for this specialty/state."
    elif provider_gap > 1:
        verdict_type = "green"
        verdict_value = "GO"
        verdict_sub = f"Underserved — {provider_gap:.1f} provider-equivalent gap vs. state density baseline."
    elif provider_gap < -1:
        verdict_type = "red"
        verdict_value = "AVOID"
        verdict_sub = f"Saturated — {abs(provider_gap):.1f} providers above state density baseline."
    else:
        verdict_type = "caution"
        verdict_value = "CAUTION"
        verdict_sub = "Market is near state density baseline — limited opportunity."

    log.info(
        "[9/10] Verdict: %s — density=%.2f/100k, expected=%.1f, current=%d, gap=%.1f",
        verdict_value,
        target_density or 0,
        expected_providers,
        peer_providers_count + 1,
        provider_gap,
    )

    log.info("[10/10] Rendering HTML report template (V2)")
    report_id = f"MERC-{pd.Timestamp.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    address_str = (
        f"{payload.client_provider.location.address_line_1 or ''} "
        f"{payload.client_provider.location.address_line_2 or ''}, "
        f"{payload.client_provider.location.city or ''} "
        f"{payload.client_provider.location.state or ''} "
        f"{payload.client_provider.location.zip_code or ''}"
    ).strip()

    density_line = (
        f"The 2023 state-level physician density for <strong>{payload.specialty_name}</strong> in "
        f"<strong>{provider_state}</strong> is "
        f"<strong>{target_density:.1f} providers per 100k residents</strong>, "
        f"implying <strong>{expected_providers:.1f} expected providers</strong> in this market. "
        f"There are currently <strong>{peer_providers_count + 1} active providers</strong> "
        f"(including this practice) within {payload.miles_radius} miles, "
        f"leaving a gap of <strong>{provider_gap:+.1f} providers</strong>."
        if target_density is not None
        else (
            f"No state-level density data is available for <strong>{payload.specialty_name}</strong>"
            f" in <strong>{provider_state}</strong>."
        )
    )
    analysis_text = (
        f"The {payload.client_provider.location.city}, {payload.client_provider.location.state} market has "
        f"<strong>{total_population:,} total residents</strong>."
        "<br><br>"
        f"{density_line}"
        "<br><br>"
        "Upgrade to the Strategic Code Report for complete market opportunity analysis."
    )

    show_relevant_population = relevant_pop != total_population

    report_template_data = ReportTemplateDataV2(
        reportId=report_id,
        dateIssued=pd.Timestamp.now().strftime("%m/%d/%Y"),
        specialty=payload.specialty_name,
        market=f"{payload.client_provider.location.city or ''}, {payload.client_provider.location.state or ''}",
        radius=f"{payload.miles_radius} mi",
        reportTier="Baseline",
        address=str(address_str),
        clientName=str(payload.client_provider.name),
        tags=generate_tags(cpt_rows),
        verdictType=verdict_type,
        verdictValue=verdict_value,
        verdictSub=verdict_sub,
        totalPopulation=f"{total_population:,}" if total_population > 0 else "N/A",
        relevantPopulation=f"{relevant_pop:,}" if relevant_pop > 0 else "N/A",
        populationLabel=population_label,
        currentProviders=peer_providers_count + 1,
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
        providerProfile=ProviderProfileV2(
            annualVisits=f"{total_client_services:,}",
        ),
        competitorCount=peer_providers_count,
        showRelevantPopulation=show_relevant_population,
        taxonomyCodes=taxonomy_codes,
        searchedZipCodes=actual_zips_df["zip"].astype(str).tolist(),
        sourceTabs=source_tabs,
        peerNpis=[p.npi for p in providers_in_radius if p.npi],
    )

    template_html = (settings.TEMPLATES_DIR / "MREC_Report_TEMPLATE_V2.html").read_text(encoding="utf-8")
    html = replace_data_block_v2(template_html, report_template_data)
    log.info("[10/10] Done — report '%s' rendered (%d bytes)", report_id, len(html))
    return html, debug_excel_bytes
