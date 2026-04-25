"""Unit tests for specialty lookup helpers in app/utils."""

from app.utils.common import (
    get_anchor_cpt_codes,
    get_anchor_cpt_patient_type_map,
    get_density_scope,
    get_provider_density,
    get_source_tabs,
    get_taxonomy_codes,
)
from app.utils.specialty import get_google_places_keywords

_FIXTURE_LOOKUP = {
    "fm": {
        "description": "Family Medicine",
        "taxonomy_codes": ["207Q00000X"],
        "google_places_keywords": ["family medicine", "primary care"],
        "source_tabs": ["FM Tab"],
        "states": {"US": 50.0, "CA": 60.0, "TX": 45.0},
    },
    "obgyn": {
        "description": "Obstetrics and Gynecology",
        "taxonomy_codes": ["207V00000X"],
        "google_places_keywords": [],
        "source_tabs": [],
        "states": {"US": 30.0},
    },
}

_FIXTURE_ANCHOR = {
    "through_the_door_cpt_codes": {
        "em_office_visits": {"codes": [{"code": "99213", "patient_type": "Established"}]},
        "preventive_visits": {"codes": [{"code": "99381", "patient_type": "New Patient"}]},
        "obgyn_specific": {"codes": [{"code": "99000", "patient_type": "New Patient"}]},
    }
}


def test_get_google_places_keywords_returns_list():
    out = get_google_places_keywords(_FIXTURE_LOOKUP, "Family Medicine")
    assert out == ["family medicine", "primary care"]


def test_get_google_places_keywords_falls_back_to_specialty_when_empty():
    out = get_google_places_keywords(_FIXTURE_LOOKUP, "Obstetrics and Gynecology")
    assert out == ["Obstetrics and Gynecology"]


def test_get_google_places_keywords_unknown_specialty_falls_back():
    out = get_google_places_keywords(_FIXTURE_LOOKUP, "Made Up Specialty")
    assert out == ["Made Up Specialty"]


def test_get_google_places_keywords_case_insensitive():
    out = get_google_places_keywords(_FIXTURE_LOOKUP, "  family medicine  ")
    assert out == ["family medicine", "primary care"]


def test_get_provider_density_state_match():
    assert get_provider_density(_FIXTURE_LOOKUP, "Family Medicine", "CA") == 60.0


def test_get_provider_density_falls_back_to_us():
    assert get_provider_density(_FIXTURE_LOOKUP, "Family Medicine", "ZZ") == 50.0


def test_get_provider_density_unknown_specialty_returns_none():
    assert get_provider_density(_FIXTURE_LOOKUP, "Unknown", "CA") is None


def test_get_density_scope_state():
    assert get_density_scope(_FIXTURE_LOOKUP, "Family Medicine", "CA") == "State"


def test_get_density_scope_national():
    assert get_density_scope(_FIXTURE_LOOKUP, "Family Medicine", "ZZ") == "National (US Avg.)"


def test_get_taxonomy_codes_match():
    assert get_taxonomy_codes(_FIXTURE_LOOKUP, "Family Medicine") == ["207Q00000X"]


def test_get_taxonomy_codes_unknown_returns_empty():
    assert get_taxonomy_codes(_FIXTURE_LOOKUP, "Unknown") == []


def test_get_source_tabs_match():
    assert get_source_tabs(_FIXTURE_LOOKUP, "Family Medicine") == ["FM Tab"]


def test_get_source_tabs_unknown_returns_empty():
    assert get_source_tabs(_FIXTURE_LOOKUP, "Unknown") == []


def test_get_anchor_cpt_codes_default():
    codes = get_anchor_cpt_codes(_FIXTURE_ANCHOR, "Family Medicine")
    assert "99213" in codes
    assert "99381" in codes
    assert "99000" not in codes  # not OBGYN


def test_get_anchor_cpt_codes_obgyn_includes_extra():
    codes = get_anchor_cpt_codes(_FIXTURE_ANCHOR, "Gynecology")
    assert "99000" in codes


def test_get_anchor_cpt_patient_type_map():
    out = get_anchor_cpt_patient_type_map(_FIXTURE_ANCHOR)
    assert out["99213"] == "Established"
    assert out["99381"] == "New Patient"
