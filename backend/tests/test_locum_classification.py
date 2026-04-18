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
