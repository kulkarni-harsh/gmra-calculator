"""Unit tests for Medicare PFS rate calculation."""

import pytest

from app.services.fee_schedule import get_medicare_rate

_RVU = {
    "99213": {"work": 1.30, "pe_nonfac": 1.40, "pe_fac": 0.70, "mp": 0.10, "cf": 33.5675},
    "99214": {"work": 1.92, "pe_nonfac": 2.05, "pe_fac": 1.05, "mp": 0.13, "cf": 33.5675},
}
_GPCI = {
    "CA": {"pw": 1.05, "pe": 1.10, "mp": 0.55},
    "TX": {"pw": 1.00, "pe": 0.95, "mp": 0.80},
}


def test_get_medicare_rate_non_facility_california():
    """Test non-facility rate calculation for CPT 99213 in California."""
    rate = get_medicare_rate("99213", "CA", _RVU, _GPCI)
    expected = (1.30 * 1.05 + 1.40 * 1.10 + 0.10 * 0.55) * 33.5675
    assert rate == round(expected, 2)


def test_get_medicare_rate_facility_uses_facility_pe():
    """Test facility rate uses facility PE RVU instead of non-facility."""
    rate = get_medicare_rate("99213", "CA", _RVU, _GPCI, facility=True)
    expected = (1.30 * 1.05 + 0.70 * 1.10 + 0.10 * 0.55) * 33.5675
    assert rate == round(expected, 2)


def test_get_medicare_rate_unknown_state_uses_neutral_gpci():
    """Falls back to {pw:1, pe:1, mp:1} on unknown state."""
    rate = get_medicare_rate("99213", "ZZ", _RVU, _GPCI)
    expected = (1.30 + 1.40 + 0.10) * 33.5675
    assert rate == round(expected, 2)


def test_get_medicare_rate_unknown_cpt_returns_none():
    """Returns None when CPT code not found."""
    assert get_medicare_rate("00000", "CA", _RVU, _GPCI) is None


def test_get_medicare_rate_strips_whitespace_in_inputs():
    """Strips whitespace from CPT code and state."""
    rate_clean = get_medicare_rate("99213", "CA", _RVU, _GPCI)
    rate_padded = get_medicare_rate(" 99213 ", " CA ", _RVU, _GPCI)
    assert rate_clean == rate_padded


def test_get_medicare_rate_case_insensitive_state():
    """State lookup is case-insensitive."""
    rate_upper = get_medicare_rate("99213", "CA", _RVU, _GPCI)
    rate_lower = get_medicare_rate("99213", "ca", _RVU, _GPCI)
    assert rate_upper == rate_lower


@pytest.mark.parametrize("cpt,state", [("99213", "TX"), ("99214", "CA")])
def test_get_medicare_rate_is_positive(cpt, state):
    """All rates are positive."""
    rate = get_medicare_rate(cpt, state, _RVU, _GPCI)
    assert rate is not None and rate > 0


def test_get_medicare_rate_facility_vs_nonfacility():
    """Facility rates use lower PE RVU when pe_fac < pe_nonfac."""
    rate_nonfac = get_medicare_rate("99213", "CA", _RVU, _GPCI, facility=False)
    rate_fac = get_medicare_rate("99213", "CA", _RVU, _GPCI, facility=True)
    # Since pe_fac (0.70) < pe_nonfac (1.40), facility should be lower
    assert rate_fac < rate_nonfac
