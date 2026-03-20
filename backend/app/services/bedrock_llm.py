"""
Bedrock LLM service — generates market analysis prose for T0 reports.

Uses langchain-aws ChatBedrockConverse.  Falls back to `fallback_text`
on any error so the report pipeline is never blocked by LLM failures.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage

from app.core.config import settings

log = logging.getLogger(__name__)

AI_DISCLAIMER = (
    "<em style='font-size:0.75rem;color:#6b7280;'>"
    "&#9432; This analysis was generated with the assistance of AI and is intended for "
    "informational purposes. Verify key figures against primary sources before making "
    "business decisions."
    "</em>"
)


@dataclass
class MarketAnalysisInput:
    city: str
    state: str
    specialty: str
    drive_time_minutes: int
    total_population: int
    relevant_pop: int
    population_label: str
    peer_providers_count: int
    expected_providers: float
    provider_gap: float
    target_density: float | None
    total_market_services: int
    # Sorted descending — e.g. [34, 22, 15, 10, 8, ...] (percent shares)
    provider_shares: list[int] = field(default_factory=list)
    # Top CPT procedure descriptions
    top_cpt_descriptions: list[str] = field(default_factory=list)
    verdict_type: str = "caution"  # "opportunity" | "avoid" | "caution"
    # Geographic distribution of competitors (drive time)
    nearest_competitor_drive_min: float | None = None
    median_competitor_drive_min: float | None = None
    providers_within_10_min: int | None = None
    # List of (drive_time_minutes, cpt_volume_share_pct) pairs, sorted by drive time ASC.
    # Enables LLM to reason about proximity risk vs. volume dominance together.
    provider_drive_volume_pairs: list[tuple[float, int]] = field(default_factory=list)


def _build_prompt(d: MarketAnalysisInput) -> str:
    # ── Provider density narrative ─────────────────────────────────────────
    if d.target_density is not None and d.expected_providers > 0:
        density_pct = round((d.peer_providers_count / d.expected_providers) * 100)
        density_context = (
            f"- State benchmark density: {d.target_density:.1f} providers per 100k residents\n"
            f"- Expected providers for this population: {d.expected_providers:.1f}\n"
            f"- Active providers in market: {d.peer_providers_count}\n"
            f"- Operating at {density_pct}% of benchmark\n"
            f"- Provider gap: {d.provider_gap:+.1f} (positive = underserved, negative = saturated)\n"
        )
    else:
        density_context = (
            f"- State benchmark density: Not available for this specialty/state\n"
            f"- Active providers in market: {d.peer_providers_count}\n"
        )

    # ── Market concentration ───────────────────────────────────────────────
    if d.provider_shares:
        top_share = d.provider_shares[0]
        top3_share = sum(d.provider_shares[:3]) if len(d.provider_shares) >= 3 else sum(d.provider_shares)
        concentration_context = (
            f"- Top provider CPT volume share: {top_share}%\n"
            f"- Top 3 providers combined share: {top3_share}%\n"
            f"- Total providers with volume data: {len(d.provider_shares)}\n"
        )
    else:
        concentration_context = "- Provider share data not available\n"

    # ── CPT procedure mix ─────────────────────────────────────────────────
    if d.top_cpt_descriptions:
        cpt_context = "Top procedures by volume in this market:\n" + "\n".join(
            f"  {i + 1}. {desc}" for i, desc in enumerate(d.top_cpt_descriptions[:10])
        )
    else:
        cpt_context = "Procedure mix data not available."

    # ── Geographic distribution of competitors (drive time) ──────────────
    if d.nearest_competitor_drive_min is not None:
        within_10_line = ""
        if d.providers_within_10_min is not None and d.peer_providers_count > 0:
            pct = round(d.providers_within_10_min / d.peer_providers_count * 100)
            within_10_line = (
                f"- {d.providers_within_10_min} of {d.peer_providers_count} providers "
                f"({pct}%) are within a 10-minute drive\n"
            )
        median_line = (
            f"- Median competitor drive time: {d.median_competitor_drive_min:.0f} min\n"
            if d.median_competitor_drive_min is not None
            else ""
        )
        geo_context = (
            f"- Nearest competitor: {d.nearest_competitor_drive_min:.0f} min drive from proposed location\n"
            f"{median_line}"
            f"{within_10_line}"
        )
    else:
        geo_context = "- Competitor drive-time data not available\n"

    # ── Competitor proximity vs CPT volume ──────────────────────────────────
    if d.provider_drive_volume_pairs:
        lines = "\n".join(
            f"  - {round(dt)} min drive · {share}% volume share" for dt, share in d.provider_drive_volume_pairs[:10]
        )
        proximity_volume_context = f"Competitors sorted by drive time (nearest first):\n{lines}\n"
    else:
        proximity_volume_context = "- Competitor proximity-volume data not available\n"

    # ── Relevant population note ──────────────────────────────────────────
    pop_note = ""
    if d.relevant_pop != d.total_population and d.total_population > 0:
        pop_note = (
            f"Note: This specialty primarily serves the {d.population_label} "
            f"sub-population ({d.relevant_pop:,} of {d.total_population:,} total residents).\n"
        )

    instructions = (
        "You are a healthcare real estate and market intelligence analyst writing "
        "the narrative analysis section of a paid competitive intelligence report "
        "for a medical practice considering entering or expanding in a market.\n\n"
        "Write a 3-paragraph market analysis in the style of a senior healthcare "
        "consultant. Be specific, use the numbers provided, and give a clear "
        "directional opinion. Do NOT use bullet points — write in flowing prose. "
        "Do NOT add headers. Keep the total length to 200–280 words.\n\n"
        "The three paragraphs must cover:\n"
        "1. Market Overview — Population size, total annual patient visits, and "
        "what this implies about raw demand in the market.\n"
        "2. Provider Density & Location Advantage — Compare active providers "
        "to the benchmark, state whether this market is underserved/saturated/neutral. "
        "Comment on drive-time competition and volume: if the nearest competitor is within "
        "5–10 minutes AND has high CPT volume share, note direct proximity+dominance risk; "
        "if nearby competitors have low volume share, note the opportunity despite proximity. "
        "If most high-volume competitors are 15+ minutes away, highlight the catchment advantage. "
        "Give a clear site-selection opinion.\n"
        "3. Market Concentration & Procedure Mix — How concentrated is provider "
        "volume (dominant players vs distributed market), and which procedure types "
        "dominate — what this means for a new entrant's positioning.\n\n"
        "End with one actionable recommendation sentence."
    )
    footer = (
        "Write only the analysis text. No headers, no bullet points, no markdown "
        "formatting. Plain flowing paragraphs separated by a blank line."
    )
    return (
        f"{instructions}\n\n"
        "---\n"
        "MARKET DATA:\n\n"
        f"Location: {d.city}, {d.state}\n"
        f"Specialty: {d.specialty}\n"
        f"Drive-time catchment: {d.drive_time_minutes} min\n"
        f"Total population: {d.total_population:,}\n"
        f"{pop_note}"
        f"Annual patient visits (CPT services across all providers): {d.total_market_services:,}\n"
        f"Market verdict: {d.verdict_type.upper()}\n\n"
        f"Provider Density:\n{density_context}\n"
        f"Competitor Geographic Distribution:\n{geo_context}\n"
        f"Competitor Proximity vs Volume:\n{proximity_volume_context}\n"
        f"Market Concentration:\n{concentration_context}\n"
        f"{cpt_context}\n"
        "---\n\n"
        f"{footer}"
    )


async def generate_market_analysis(
    data: MarketAnalysisInput,
    fallback_text: str,
) -> str:
    """
    Call Bedrock Claude to generate a market analysis narrative.

    Returns the LLM-generated text (with AI disclaimer appended) on success,
    or `fallback_text` if Bedrock is unavailable or returns an error.
    Never raises.
    """
    try:
        llm = ChatBedrockConverse(
            model=settings.BEDROCK_MODEL_ID,
            region_name=settings.AWS_DEFAULT_REGION or "us-east-1",
            endpoint_url=settings.BEDROCK_ENDPOINT_URL or None,
            temperature=0.4,
            max_tokens=500,
        )
        prompt = _build_prompt(data)

        # Run synchronous LangChain call in a thread pool to stay async-safe
        response = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: llm.invoke([HumanMessage(content=prompt)]),
        )
        # AIMessage.content can be str | list — coerce to plain string
        raw = response.content
        text = (
            raw
            if isinstance(raw, str)
            else " ".join(
                c if isinstance(c, str) else (c.get("text") or "")
                for c in raw  # type: ignore[union-attr]
            )
        )
        # Replace \n\n before \n — order matters to preserve paragraph breaks
        html_text = text.replace("\n\n", "<br><br>").replace("\n", " ").strip()
        log.info("Bedrock market analysis generated (%d chars)", len(html_text))
        return f"{html_text}<br><br>{AI_DISCLAIMER}"
    except Exception as exc:
        log.warning("Bedrock market analysis failed — using fallback: %s", exc)
        return fallback_text
