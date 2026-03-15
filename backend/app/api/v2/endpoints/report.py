import asyncio
import logging
import uuid
from functools import reduce

import pandas as pd
from fastapi import APIRouter, Request
from fastapi.responses import Response
from geopy.distance import geodesic

# from weasyprint import HTML as WeasyHTML  # noqa: N811  # TODO: install pango via brew
from app.core.config import settings
from app.core.types import SexAgeCounts
from app.schemas.provider_request import ProviderRequest
from app.services.alphasophia import get_hcp_data
from app.services.census import combine_demographics, get_zip_demographics
from app.services.fee_schedule import get_medicare_rate
from app.services.html_imputers.baseline_imputer import replace_data_block
from app.types.alphasophia import CPT, Provider
from app.types.baseline_report_template import CptRow, ProviderProfile, ReportTemplateData, Upgrade
from app.utils.common import get_anchor_cpt_codes, get_provider_density, get_taxonomy_codes

router = APIRouter()

# ---------------------------------------------------------------------------
# Revenue source toggle
# True  → use Medicare RVU rate × totalServices  (preferred: totalCharges is
#         often blank in AlphaSophia data)
# False → use raw totalCharges from AlphaSophia  (switch back when data improves)
# ---------------------------------------------------------------------------
USE_RVU_REVENUE = True


def _cpt_revenue(services: int, medicare_rate: float | None, charges: float) -> float:
    """Return the best available revenue figure for a CPT code.

    When USE_RVU_REVENUE is True and a Medicare rate exists, revenue is
    estimated as  rate × services.  Otherwise falls back to raw charges.
    """
    if USE_RVU_REVENUE and medicare_rate is not None and services > 0:
        return medicare_rate * services
    return charges


@router.get("/specialties")
async def list_specialties(request: Request):
    """
    Return all specialties that have provider density data (non-empty states map).
    """
    specialty_lookup: dict = request.app.state.specialty_lookup
    return [
        {"id": specialty_id, "description": data["description"]}
        for specialty_id, data in specialty_lookup.items()
        if data.get("states")
    ]


@router.get("/search-providers")
async def search_providers(
    zip_code: str,
    specialty_name: str,
    request: Request,
):
    """
    Search for providers by ZIP code and specialty name.
    Returns a list of providers suitable for populating a dropdown.
    """
    taxonomy_codes = get_taxonomy_codes(request.app.state.specialty_lookup, specialty_name)
    if len(taxonomy_codes) == 0:
        logging.warning(f"No taxonomy codes found for specialty for {specialty_name}")
        return []
    providers: list[Provider] = []
    try:
        providers = await get_hcp_data(
            zip_codes_list=[zip_code],
            taxonomy_codes_list=taxonomy_codes,
            cpt_codes_list=[],
            npi_list=[],
            page_size=200,
        )
    except Exception as exc:
        logging.error("Failed to fetch providers from AlphaSophia: %s", exc)
        providers = []
    return [provider.model_dump() for provider in providers if isinstance(provider, Provider)]


@router.post("/generate")
async def generate_report(
    payload: ProviderRequest,
    request: Request,
):
    """
    Generate a market analysis report for the given provider location and specialty.
    Returns a PDF document.
    """
    # 0. Get all CPT codes for the given specialty name
    relevant_cpt_codes_list = get_anchor_cpt_codes(request.app.state.anchor_cpt_lookup, payload.specialty_name)

    # 1. Find all taxonomy codes for the given specialty name
    taxonomy_codes = get_taxonomy_codes(request.app.state.specialty_lookup, payload.specialty_name)

    # 2. Get the address line 1, 2 & zip code for the provider
    await payload.client_provider.update_address_and_zip()

    # 3. Geocode client provider
    await payload.client_provider.update_lat_long()

    # 4. Fetch client CPT codes profile
    await payload.client_provider.fetch_cpt_profiles(relevant_cpt_codes_list)

    # 5. Find ZIPs within 2× radius (expanded search to ensure no provider is left out)
    zip_centroids_df = request.app.state.zip_centroids_df.copy()
    zip_centroids_df["distance_from_source_miles"] = zip_centroids_df.apply(
        lambda row: geodesic(
            (payload.client_provider.latitude, payload.client_provider.longitude), (row["lat"], row["lon"])
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

    # 6. Fetch providers from AlphaSophia within expanded radius
    expanded_providers_list: list[Provider]
    try:
        expanded_providers_list = await get_hcp_data(
            zip_codes_list=expanded_zips_df["zip"].dropna().astype(str).tolist(),
            taxonomy_codes_list=taxonomy_codes,
            npi_list=[],
            cpt_codes_list=relevant_cpt_codes_list,
            page_size=100,
        )
        # Exclude client provider from competitor list
        expanded_providers_list = [
            p for p in expanded_providers_list if isinstance(p, Provider) and p.id != payload.client_provider.id
        ]
        logging.info(f"Fetched {len(expanded_providers_list)} providers from AlphaSophia on 2x radius")
    except Exception as exc:
        logging.error("Failed to fetch providers from AlphaSophia: %s", exc)
        expanded_providers_list = []

    # 7. Since Alphasophia does not provide address line 1, 2 & zip.
    # Update the provider object to add address line 1, 2 & zip
    # Also geocode the providers

    async def _enrich_provider(p: Provider) -> None:
        await p.update_address_and_zip()
        await p.update_lat_long()

    await asyncio.gather(*[_enrich_provider(p) for p in expanded_providers_list])

    # 8. Filter to providers within radius
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

    logging.info(f"Fetched {len(providers_in_radius)} providers within actual radius")

    # 9. Add CPT list to each provider

    # TODO: CPT_CODES list should be specialty-specific once a mapping is available

    await asyncio.gather(*[p.fetch_cpt_profiles(relevant_cpt_codes_list) for p in providers_in_radius])

    # 10. Aggregate competitor CPT data and resolve per-CPT Medicare rates

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

    # 11. Build CPT rows — sorted by client provider's totalServices descending
    n_providers = max(len(providers_in_radius), 1)

    # Collect (agg_cpt, client_cpt, medicare_rate) and sort before rendering
    cpt_triples = []
    for agg_cpt in agg_cpt_list:
        client_cpt = payload.client_provider.get_cpt_profile(str(agg_cpt.code)) or CPT(
            code=agg_cpt.code, totalServices=0, totalCharges=0.0
        )
        medicare_rate = get_medicare_rate(
            str(agg_cpt.code),
            provider_state,
            request.app.state.rvu_table,
            request.app.state.gpci_table,
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

    # 11. Get Demographics for zip codes within radius
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

    # 12. Get relevant population count
    # TODO: Yet to be implemented
    relevant_pop, population_label = 0, "All ages"

    # --- 9. Assemble ReportTemplateData ---
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
        targetDensity=round(expected_providers, 1),  # absolute expected providers in radius area
        providerGap=round(provider_gap, 1),
        cptRows=cpt_rows,
        cptTotalVisits=cpt_total_visits,
        cptTotalRevenue=cpt_total_revenue,
        utilizationPct=0,  # TODO: requires capacity model
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

    # --- 10. Populate HTML template in-memory ---
    template_html = (settings.TEMPLATES_DIR / "MREC_Report_TEMPLATE.html").read_text(encoding="utf-8")
    populated_html = replace_data_block(template_html, report_template_data)

    # --- 11. Return HTML directly (PDF via WeasyPrint disabled until pango is installed) ---
    # pdf_bytes = WeasyHTML(string=populated_html).write_pdf()
    # return Response(
    #     content=pdf_bytes,
    #     media_type="application/pdf",
    #     headers={"Content-Disposition": f'attachment; filename="report-{report_id}.pdf"'},
    # )
    return Response(content=populated_html, media_type="text/html")
