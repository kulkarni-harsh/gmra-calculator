import pytest
from app.types.cpt import CPT
from app.types.google_maps import SiteOfCare


def _make_soc(cpt_services: dict[str, int]) -> SiteOfCare:
    cpt_list = [
        CPT(code=code, totalServices=services, totalCharges=0.0)
        for code, services in cpt_services.items()
    ]
    return SiteOfCare(place_id="test", is_locum=False, cpt_list=cpt_list)


def test_cpt_total_services_sums_list():
    soc = _make_soc({"99213": 100, "99214": 50})
    assert soc.cpt_total_services == 150


def test_cpt_total_services_empty():
    soc = _make_soc({})
    assert soc.cpt_total_services == 0


def test_get_cpt_profile_found():
    soc = _make_soc({"99213": 100, "99214": 50})
    cpt = soc.get_cpt_profile("99213")
    assert cpt is not None
    assert cpt.totalServices == 100


def test_get_cpt_profile_missing_returns_none():
    soc = _make_soc({"99213": 100})
    assert soc.get_cpt_profile("00000") is None
