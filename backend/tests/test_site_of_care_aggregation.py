"""Tests for SiteOfCare aggregation, locum classification, and CPT roll-ups."""

from app.services.google_maps import get_sites_of_care_list
from app.services.report_generator import _aggregate_cpt_data
from app.types.alphasophia import Provider
from app.types.cpt import CPT
from app.types.google_maps import GooglePlace, SiteOfCare


def _make_soc(cpt_services: dict[str, int]) -> SiteOfCare:
    cpt_list = [CPT(code=code, totalServices=services, totalCharges=0.0) for code, services in cpt_services.items()]
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


def test_aggregate_cpt_data_with_sites_of_care():
    soc_a = _make_soc({"99213": 200, "99214": 100})
    soc_b = _make_soc({"99213": 50})
    result = _aggregate_cpt_data(
        providers_in_radius=[soc_a, soc_b],
        cpt_codes=["99213", "99214"],
        cpt_patient_type_map={},
        provider_state="CA",
        rvu_table={},
        gpci_table={},
    )
    assert result.total_market_services == 350
    assert result.share_denom == 350
    assert len(result.cpt_rows) == 2
    assert result.cpt_rows[0].code == "99213"  # highest volume first


def test_aggregate_cpt_data_empty_list():
    result = _aggregate_cpt_data(
        providers_in_radius=[],
        cpt_codes=["99213"],
        cpt_patient_type_map={},
        provider_state="CA",
        rvu_table={},
        gpci_table={},
    )
    assert result.total_market_services == 0
    assert result.share_denom == 1  # divide-by-zero guard


# --- get_sites_of_care_list tests ---


def _make_provider(npi: str | None, place_id: str | None = "place_1") -> Provider:
    place = GooglePlace(place_id=place_id) if place_id else None
    return Provider(
        id=1,
        npi=npi,
        name="Test Provider",
        nearest_google_place=place,
        cpt_list=[CPT(code="99213", totalServices=10, totalCharges=0.0)],
    )


def test_get_sites_of_care_list_groups_by_place():
    p1 = _make_provider("1111111111", "place_1")
    p2 = _make_provider("2222222222", "place_1")
    result = get_sites_of_care_list([p1, p2])
    assert len(result) == 1
    assert set(result[0].npi_list) == {"1111111111", "2222222222"}
    assert result[0].cpt_total_services == 20  # CPT lists merged


def test_get_sites_of_care_list_none_npi_excluded():
    p1 = _make_provider(None, "place_1")
    p2 = _make_provider("2222222222", "place_1")
    result = get_sites_of_care_list([p1, p2])
    assert len(result) == 1
    assert result[0].npi_list == ["2222222222"]


def test_get_sites_of_care_list_all_none_npi():
    p1 = _make_provider(None, "place_1")
    result = get_sites_of_care_list([p1])
    assert len(result) == 1
    assert result[0].npi_list == []


def test_get_sites_of_care_list_locum_no_google_place():
    p = _make_provider("3333333333", place_id=None)
    result = get_sites_of_care_list([p])
    assert len(result) == 1
    assert result[0].is_locum is True
    assert result[0].npi_list == ["3333333333"]


def test_get_sites_of_care_list_locum_none_npi_no_google_place():
    p = _make_provider(None, place_id=None)
    result = get_sites_of_care_list([p])
    assert len(result) == 1
    assert result[0].is_locum is True
    assert result[0].npi_list == []


def test_get_sites_of_care_list_separate_sites():
    p1 = _make_provider("1111111111", "place_1")
    p2 = _make_provider("2222222222", "place_2")
    result = get_sites_of_care_list([p1, p2])
    assert len(result) == 2
