import pytest
from app.types.alphasophia import CPT, Provider


def _make_provider(id: int = 1, cpt_total: int = 0) -> Provider:
    p = Provider(id=id, npi=f"NPI{id}", name=f"Provider {id}")
    p.cpt_total_services = cpt_total
    return p


def test_set_is_locum_raises_when_cpt_not_fetched():
    p = _make_provider()
    with pytest.raises(ValueError, match="CPT profiles must be fetched"):
        p.set_is_locum(total_market_services=100)


def test_set_is_locum_true_at_2pct_boundary():
    p = _make_provider(cpt_total=2)
    object.__setattr__(p, "_cpt_fetched", True)
    p.set_is_locum(total_market_services=100)
    assert p.is_locum is True


def test_set_is_locum_true_below_2pct():
    p = _make_provider(cpt_total=1)
    object.__setattr__(p, "_cpt_fetched", True)
    p.set_is_locum(total_market_services=100)
    assert p.is_locum is True


def test_set_is_locum_false_above_2pct():
    p = _make_provider(cpt_total=3)
    object.__setattr__(p, "_cpt_fetched", True)
    p.set_is_locum(total_market_services=100)
    assert p.is_locum is False


def test_set_is_locum_true_when_total_zero():
    p = _make_provider(cpt_total=0)
    object.__setattr__(p, "_cpt_fetched", True)
    p.set_is_locum(total_market_services=0)
    # 0 <= 0.02 * 0 → 0 <= 0 → True
    assert p.is_locum is True


from app.types.baseline_report_template import ProviderShareEntry, ReportTemplateDataV2
import dataclasses


def test_provider_share_entry_has_is_locum():
    entry = ProviderShareEntry(share=1, taxonomy="Family Medicine", is_locum=True)
    assert entry.is_locum is True


def test_provider_share_entry_is_locum_defaults_false():
    entry = ProviderShareEntry(share=10, taxonomy="Family Medicine")
    assert entry.is_locum is False


def test_report_template_data_v2_has_locum_count():
    fields = {f.name: f for f in dataclasses.fields(ReportTemplateDataV2)}
    assert "locumCount" in fields
    assert fields["locumCount"].default == 0


from app.services.report_generator import _aggregate_cpt_data


def _make_provider_with_cpt(id: int, cpt_services: int) -> Provider:
    p = Provider(id=id, npi=f"NPI{id}", name=f"Provider {id}")
    object.__setattr__(p, "_cpt_fetched", True)
    cpt = CPT(code="99213", totalServices=cpt_services, totalCharges=0.0)
    p.cpt_list = [cpt]
    return p


def test_aggregate_cpt_data_sets_is_locum():
    """Providers with ≤ 2% of market volume are flagged as locum."""
    providers = [
        _make_provider_with_cpt(1, 980),  # 98% — not locum
        _make_provider_with_cpt(2, 10),   # 1%  — locum
        _make_provider_with_cpt(3, 10),   # 1%  — locum
    ]
    result = _aggregate_cpt_data(
        providers_in_radius=providers,
        cpt_codes=["99213"],
        cpt_patient_type_map={},
        provider_state="TX",
        rvu_table={},
        gpci_table={},
    )
    assert providers[0].is_locum is False
    assert providers[1].is_locum is True
    assert providers[2].is_locum is True
    non_locum = [e for e in result.provider_shares if not e.is_locum]
    locum = [e for e in result.provider_shares if e.is_locum]
    assert len(non_locum) == 1
    assert len(locum) == 2
