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

import pandas as pd
from geopy.distance import geodesic

from app.core.config import settings
from app.core.types import SexAgeCounts
from app.schemas.provider_request import ProviderRequest
from app.services.alphasophia import get_hcp_data
from app.services.census import combine_demographics, get_zip_demographics
from app.services.fee_schedule import get_medicare_rate
from app.services.html_imputers.baseline_imputer import replace_data_block
from app.types.alphasophia import CPT, Provider
from app.types.baseline_report_template import CptRow, ProviderProfile, ReportTemplateData, Upgrade
from app.utils.common import get_anchor_cpt_codes, get_provider_density, get_taxonomy_codes, load_fee_schedule_tables
from app.utils.validator import validate_speciality_master_df

USE_RVU_REVENUE = True


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


def _cpt_revenue(services: int, medicare_rate: float | None, charges: float) -> float:
    if USE_RVU_REVENUE and medicare_rate is not None and services > 0:
        return medicare_rate * services
    return charges


async def run_report(payload: ProviderRequest, state: ReportState) -> str:
    """Generate the HTML report and return it as a string."""

    relevant_cpt_codes_list = get_anchor_cpt_codes(state.anchor_cpt_lookup, payload.specialty_name)
    taxonomy_codes = get_taxonomy_codes(state.specialty_lookup, payload.specialty_name)

    await payload.client_provider.update_address_and_zip()
    await payload.client_provider.update_lat_long()
    await payload.client_provider.fetch_cpt_profiles(relevant_cpt_codes_list)

    zip_centroids_df = state.zip_centroids_df.copy()
    zip_centroids_df["distance_from_source_miles"] = zip_centroids_df.apply(
        lambda row: geodesic(
            (payload.client_provider.latitude, payload.client_provider.longitude),
            (row["lat"], row["lon"]),
        ).miles,
        axis=1,
    )
    expanded_zips_df = zip_centroids_df[zip_centroids_df["distance_from_source_miles"] <= 2 * payload.miles_radius]
    if expanded_zips_df.empty:
        logging.warning("No ZIP codes found within 2× radius. Falling back to input ZIP only.")
        expanded_zips_df = pd.DataFrame(
            {
                "zip": [payload.client_provider.zip_code],
                "lat": [payload.client_provider.latitude],
                "lon": [payload.client_provider.longitude],
                "distance_from_source_miles": [0.0],
            }
        )

    expanded_providers_list: list[Provider]
    try:
        expanded_providers_list = await get_hcp_data(
            zip_codes_list=expanded_zips_df["zip"].dropna().astype(str).tolist(),
            taxonomy_codes_list=taxonomy_codes,
            npi_list=[],
            cpt_codes_list=relevant_cpt_codes_list,
            page_size=100,
        )
        expanded_providers_list = [
            p for p in expanded_providers_list if isinstance(p, Provider) and p.id != payload.client_provider.id
        ]
        logging.info("Fetched %d providers from AlphaSophia on 2x radius", len(expanded_providers_list))
    except Exception as exc:
        logging.error("Failed to fetch providers from AlphaSophia: %s", exc)
        expanded_providers_list = []

    async def _enrich_provider(p: Provider) -> None:
        await p.update_address_and_zip()
        await p.update_lat_long()

    await asyncio.gather(*[_enrich_provider(p) for p in expanded_providers_list])

    providers_in_radius: list[Provider] = []
    for result in expanded_providers_list:
        if result.latitude is None or result.longitude is None:
            continue
        dist = geodesic(
            (result.latitude, result.longitude),
            (payload.client_provider.latitude, payload.client_provider.longitude),
        ).miles
        if dist <= payload.miles_radius:
            providers_in_radius.append(result)

    logging.info("Fetched %d providers within actual radius", len(providers_in_radius))

    await asyncio.gather(*[p.fetch_cpt_profiles(relevant_cpt_codes_list) for p in providers_in_radius])

    provider_state = payload.client_provider.location.state or ""

    agg_cpt_list: list[CPT] = []
    for cpt in relevant_cpt_codes_list:
        agg_cpt = CPT(code=cpt, totalServices=0, totalCharges=0.0)
        for p in providers_in_radius:
            p_cpt = p.get_cpt_profile(cpt)
            if p_cpt:
                agg_cpt.totalServices += p_cpt.totalServices if p_cpt.totalServices > 0 else 0
                agg_cpt.totalCharges += p_cpt.totalCharges if p_cpt.totalCharges > 0 else 0
                agg_cpt.description = p_cpt.description
                agg_cpt.codeType = p_cpt.codeType
        agg_cpt_list.append(agg_cpt)

    n_providers = max(len(providers_in_radius), 1)

    cpt_triples = []
    for agg_cpt in agg_cpt_list:
        client_cpt = payload.client_provider.get_cpt_profile(str(agg_cpt.code)) or CPT(
            code=agg_cpt.code, totalServices=0, totalCharges=0.0
        )
        medicare_rate = get_medicare_rate(
            str(agg_cpt.code),
            provider_state,
            state.rvu_table,
            state.gpci_table,
        )
        cpt_triples.append((agg_cpt, client_cpt, medicare_rate))

    cpt_triples.sort(key=lambda t: t[1].totalServices, reverse=True)

    cpt_rows: list[CptRow] = []
    total_market_services = 0.0
    total_market_revenue = 0.0
    total_client_services = 0
    total_client_revenue = 0.0

    for agg_cpt, client_cpt, medicare_rate in cpt_triples:
        mkt_services = agg_cpt.totalServices if agg_cpt.totalServices > 0 else 0
        mkt_revenue = _cpt_revenue(mkt_services, medicare_rate, agg_cpt.totalCharges)
        cli_services = client_cpt.totalServices if client_cpt.totalServices > 0 else 0
        cli_revenue = _cpt_revenue(cli_services, medicare_rate, client_cpt.totalCharges)
        peer_avg_services = mkt_services / n_providers
        peer_avg_revenue = mkt_revenue / n_providers

        total_market_services += mkt_services
        total_market_revenue += mkt_revenue
        total_client_services += cli_services
        total_client_revenue += cli_revenue

        cpt_rows.append(
            CptRow(
                code=str(agg_cpt.code),
                desc=agg_cpt.description,
                type=agg_cpt.codeType,
                volume=f"{int(mkt_services):,}",
                revenue=f"${mkt_revenue:,.0f}",
                clientVolume=f"{cli_services:,}" if cli_services else None,
                clientRevenue=f"${cli_revenue:,.0f}" if cli_services else None,
                peerAvgVolume=f"{int(peer_avg_services):,}" if mkt_services else None,
                peerAvgRevenue=f"${peer_avg_revenue:,.0f}" if mkt_services else None,
                medicareRate=f"${medicare_rate:,.2f}" if medicare_rate is not None else None,
            )
        )

    cpt_total_visits = f"{int(total_market_services):,} visits/yr"
    cpt_total_revenue = f"${total_market_revenue:,.0f}"

    actual_zips_df = zip_centroids_df[zip_centroids_df["distance_from_source_miles"] <= payload.miles_radius]
    if actual_zips_df.empty:
        actual_zips_df = pd.DataFrame(
            {
                "zip": [str(payload.client_provider.location.zip_code)],
                "lat": [payload.client_provider.latitude],
                "lon": [payload.client_provider.longitude],
                "distance_from_source_miles": [0.0],
            }
        )

    try:
        zip_demographic_dict = get_zip_demographics(
            tuple(actual_zips_df["zip"].astype(str).values),
            settings.CENSUS_API_KEY,
        )
        combined_demo: SexAgeCounts = reduce(combine_demographics, zip_demographic_dict.values())
        total_population: int = combined_demo["Total"]
    except Exception as exc:
        logging.error("Failed to get demographics: %s", exc)
        combined_demo = {"M": {}, "F": {}, "Total": 0}
        total_population = 0

    relevant_pop, population_label = total_population, "All ages"

    target_density = get_provider_density(state.specialty_lookup, payload.specialty_name, provider_state)
    current_providers = len(providers_in_radius) + 1
    if target_density is not None and relevant_pop > 0:
        expected_providers = (relevant_pop / 100_000) * target_density
        provider_gap = expected_providers - current_providers
    else:
        expected_providers = 0.0
        provider_gap = 0.0

    if target_density is None:
        verdict_type = "caution"
        verdict_value = "N/A"
        verdict_sub = "No density benchmark available for this specialty/state."
    elif provider_gap > 1:
        verdict_type = "green"
        verdict_value = "GO"
        verdict_sub = f"Underserved — {provider_gap:.1f} provider-equivalent gap vs. benchmark."
    elif provider_gap < -1:
        verdict_type = "red"
        verdict_value = "AVOID"
        verdict_sub = f"Saturated — {abs(provider_gap):.1f} providers above benchmark density."
    else:
        verdict_type = "caution"
        verdict_value = "CAUTION"
        verdict_sub = "Market is near benchmark density — limited opportunity."

    report_id = f"MERC-{pd.Timestamp.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    address_str = (
        f"{payload.client_provider.location.address_line_1} {payload.client_provider.location.address_line_2}, "
        f"{payload.client_provider.location.city} {payload.client_provider.location.state} "
        f"{payload.client_provider.location.zip_code}"
    ).strip()

    density_line = (
        f"The national benchmark for <strong>{payload.specialty_name}</strong> in "
        f"<strong>{provider_state}</strong> is "
        f"<strong>{target_density:.1f} providers per 100k residents</strong>, "
        f"implying <strong>{expected_providers:.1f} expected providers</strong> in this market. "
        f"There are currently <strong>{current_providers} active providers</strong> "
        f"(including your practice) within {payload.miles_radius} miles, "
        f"leaving a gap of <strong>{provider_gap:+.1f} providers</strong>."
        if target_density is not None
        else f"No density benchmark is available for <strong>{payload.specialty_name}</strong> in <strong>{provider_state}</strong>."
    )
    analysis_text = (
        f"The {payload.client_provider.location.city}, {payload.client_provider.location.state} market has "
        f"<strong>{total_population:,} total residents</strong>."
        "<br><br>"
        f"{density_line}"
        "<br><br>"
        "Upgrade to the Strategic Code Report for complete market opportunity analysis."
    )

    report_template_data = ReportTemplateData(
        reportId=report_id,
        dateIssued=pd.Timestamp.now().strftime("%m/%d/%Y"),
        specialty=payload.specialty_name,
        market=f"{payload.client_provider.location.city}, {payload.client_provider.location.state}",
        radius=f"{payload.miles_radius} mi",
        reportTier="Baseline",
        address=str(address_str),
        clientName=str(payload.client_provider.name),
        tags=[],
        verdictType=verdict_type,
        verdictValue=verdict_value,
        verdictSub=verdict_sub,
        totalPopulation=f"{total_population:,}" if total_population > 0 else "N/A",
        relevantPopulation=f"{relevant_pop:,}" if relevant_pop > 0 else "N/A",
        populationLabel=population_label,
        currentProviders=current_providers,
        targetDensity=round(expected_providers, 1),
        providerGap=round(provider_gap, 1),
        cptRows=cpt_rows,
        cptTotalVisits=cpt_total_visits,
        cptTotalRevenue=cpt_total_revenue,
        utilizationPct=0,
        analysisText=analysis_text,
        upgrades=[
            Upgrade(
                price="$599",
                name="5-Code Strategic Report",
                desc=(
                    "Your 5 highest-revenue CPT codes analyzed against this specific market."
                    " Revenue forecast and procedure-specific demand."
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
        providerProfile=ProviderProfile(
            annualVisits=f"{total_client_services:,}",
            annualRevenue=f"${total_client_revenue:,.0f}",
        ),
        competitorCount=len(providers_in_radius),
    )

    template_html = (settings.TEMPLATES_DIR / "MREC_Report_TEMPLATE.html").read_text(encoding="utf-8")
    return replace_data_block(template_html, report_template_data)
