from dataclasses import dataclass


@dataclass(slots=True)
class Tag:
    text: str
    color: str


# ── V1 types (kept for backward compatibility) ────────────────────────────────


@dataclass(slots=True)
class CptRow:
    code: str
    desc: str | None
    type: str | None
    volume: str
    revenue: str
    # Optional: client/peer comparison inputs for Section 02 in HTML.
    clientVolume: str | int | float | None = None
    clientRevenue: str | int | float | None = None
    peerAvgVolume: str | int | float | None = None
    peerAvgRevenue: str | int | float | None = None
    medicareRate: str | None = None  # Medicare allowed amount per service (state-adjusted, non-facility)


@dataclass(slots=True)
class ProviderProfile:
    # Optional top-level practice snapshot used by "Practice Position Snapshot" cards.
    annualVisits: str | int | float | None = None
    annualRevenue: str | int | float | None = None


@dataclass(slots=True)
class Upgrade:
    price: str
    name: str
    desc: str


@dataclass(slots=True)
class ReportTemplateData:
    reportId: str
    dateIssued: str
    specialty: str
    market: str
    radius: str
    reportTier: str
    address: str
    clientName: str
    tags: list[Tag]
    verdictType: str
    verdictValue: str
    verdictSub: str
    totalPopulation: str
    relevantPopulation: str
    populationLabel: str
    currentProviders: int
    targetDensity: float
    providerGap: float
    cptRows: list[CptRow]
    cptTotalVisits: str
    cptTotalRevenue: str
    utilizationPct: int
    analysisText: str
    upgrades: list[Upgrade]
    providerProfile: ProviderProfile | None = None
    competitorCount: int | None = None


# ── V2 types (MREC_Report_TEMPLATE_T1) ────────────────────────────────────────
# Revenue fields have been removed. All sections (New vs Established split,
# Code Concentration, Fair Share, Visit Mix) are derived client-side from
# CPT volume data — no revenue fields required.


@dataclass(slots=True)
class CptRowV2:
    code: str
    desc: str | None = None
    patientType: str | None = None  # "New Patient" | "Established" — used by V3 template
    clientVolume: str | None = None
    peerAvgVolume: str | None = None
    totalVolume: str | None = None  # totalVolume = clientVolume + peerVolume
    diffVolume: int | float | None = None
    medicareRate: str | None = None  # CMS 2026 PFS office-setting rate, state-adjusted


@dataclass(slots=True)
class ProviderProfileV2:
    annualVisits: str | None = None


@dataclass(slots=True)
class ReportTemplateDataV2:
    reportId: str
    dateIssued: str
    specialty: str
    market: str
    radius: str
    reportTier: str
    address: str
    clientName: str
    tags: list[Tag]
    verdictType: str
    verdictValue: str
    verdictSub: str
    totalPopulation: str
    relevantPopulation: str
    populationLabel: str
    currentProviders: int
    targetDensity: float
    providerGap: float
    cptRows: list[CptRowV2]
    cptTotalVisits: str  # displayed in S03 market pool
    analysisText: str
    upgrades: list[Upgrade]
    providerProfile: ProviderProfileV2
    competitorCount: int
    # False hides the Relevant Population card in S01 (use for general-population
    # specialties where relevant == total population, e.g. Family Med, Internal Med).
    showRelevantPopulation: bool
    # Appendix: methodology transparency
    taxonomyCodes: list[str]  # NPI taxonomy codes searched
    searchedZipCodes: list[str]  # ZIP codes within the exact radius
    sourceTabs: list[str]  # Dashboard tab names from specialty_lookup (density source)
    peerNpis: list[str]  # NPIs of peer providers within the exact radius
    # Sorted descending list of each provider's % share of total market CPT services (0–100).
    # Anonymous — no names or NPIs. For T1+ reports, the client provider is included as one entry.
    # For T0 (Market Entry) reports, only peer providers are included (no named client).
    providerShares: list[int] | None = None
