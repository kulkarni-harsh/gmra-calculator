"""Tests for the active/locum provider split in ReportTemplateDataV2."""

import dataclasses
from typing import Any


def test_report_template_data_v2_has_active_providers_field():
    from app.types.baseline_report_template import ReportTemplateDataV2

    fields = {f.name for f in dataclasses.fields(ReportTemplateDataV2)}
    assert "activeProviders" in fields, "ReportTemplateDataV2 must have an 'activeProviders' field (non-locum count)"
    assert "currentProviders" not in fields, (
        "currentProviders has been replaced by activeProviders — remove the old field"
    )


def test_report_template_data_v2_locum_count_still_present():
    from app.types.baseline_report_template import ReportTemplateDataV2

    fields = {f.name for f in dataclasses.fields(ReportTemplateDataV2)}
    assert "locumCount" in fields, "locumCount must remain on ReportTemplateDataV2"


def test_report_template_data_v2_active_providers_is_int():
    from app.types.baseline_report_template import ReportTemplateDataV2

    hints = ReportTemplateDataV2.__dataclass_fields__
    assert hints["activeProviders"].type is int, "activeProviders must be typed as int"


def _minimal_v2(**overrides: object):
    """Build a minimal ReportTemplateDataV2 for snapshot tests."""
    from app.types.baseline_report_template import (
        CptRowV2,
        ProviderProfileV2,
        ReportTemplateDataV2,
        Tag,
    )

    defaults: dict[str, Any] = dict(
        reportId="TEST-001",
        dateIssued="04/25/2026",
        specialty="Family Medicine",
        market="75034 Frisco, TX",
        radius="20 min drive",
        reportTier="Market Entry",
        showSection03=False,
        address="5757 Warren Pkwy, Frisco TX 75034",
        clientName="",
        tags=[Tag(text="Test", color="green")],
        verdictType="opportunity",
        verdictValue="GO",
        verdictSub="Underserved",
        totalPopulation="503,447",
        relevantPopulation="503,447",
        populationLabel="All ages",
        activeProviders=36,
        targetDensity=55.2,
        providerGap=17.2,
        cptRows=[
            CptRowV2(
                code="99213",
                desc="Office visit",
                totalVolume="48,920",
                medicareRate="$115.28",
            )
        ],
        cptTotalVisits="48,920",
        analysisText="<p>Test analysis.</p>",
        upgrades=[],
        providerProfile=ProviderProfileV2(),
        competitorCount=36,
        showRelevantPopulation=False,
        taxonomyCodes=["207Q00000X"],
        searchedZipCodes=["75034"],
        sourceTabs=["Family Medicine"],
        peerNpis=["1234567890"],
        locumCount=2,
    )
    defaults.update(overrides)
    return ReportTemplateDataV2(**defaults)


def test_can_instantiate_with_active_and_locum():
    obj = _minimal_v2(activeProviders=36, locumCount=2)
    assert obj.activeProviders == 36
    assert obj.locumCount == 2


def test_active_providers_independent_of_locum_count():
    """activeProviders must not include locum — it is the ready-to-treat full-time count."""
    obj = _minimal_v2(activeProviders=10, locumCount=5)
    assert obj.activeProviders == 10
    assert obj.locumCount == 5
