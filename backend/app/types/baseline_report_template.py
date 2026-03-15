from dataclasses import dataclass


@dataclass(slots=True)
class Tag:
    text: str
    color: str


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
