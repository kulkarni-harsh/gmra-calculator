"""Unit tests for distance/normalization helpers in app.services.geocoding."""

import pandas as pd

from app.services.geocoding import (
    calculate_distance_miles,
    normalize_street,
    zips_within_radius_geopy,
)

# ── normalize_street ──────────────────────────────────────────────────────────


def test_normalize_street_returns_none_for_non_string():
    assert normalize_street(None) is None
    assert normalize_street(123) is None


def test_normalize_street_strips_suite():
    assert normalize_street("123 Main St Suite 400") == "123 Main St"


def test_normalize_street_strips_apartment():
    assert normalize_street("456 Oak Ave Apt 12") == "456 Oak Ave"


def test_normalize_street_strips_floor():
    assert normalize_street("789 Elm Rd Floor 3") == "789 Elm Rd"


def test_normalize_street_handles_no_suffix():
    assert normalize_street("123 Main St") == "123 Main St"


# ── calculate_distance_miles ─────────────────────────────────────────────────


def test_calculate_distance_miles_zero_for_same_point():
    assert calculate_distance_miles(37.0, -122.0, 37.0, -122.0) == 0.0


def test_calculate_distance_miles_returns_float():
    d = calculate_distance_miles(37.7749, -122.4194, 34.0522, -118.2437)  # SF → LA
    assert d is not None
    assert 340 < d < 400  # ~347 miles


def test_calculate_distance_miles_returns_none_on_null_input():
    assert calculate_distance_miles(None, -122.0, 37.0, -122.0) is None
    assert calculate_distance_miles(37.0, None, 37.0, -122.0) is None


# ── zips_within_radius_geopy ─────────────────────────────────────────────────


def test_zips_within_radius_returns_only_close_ones():
    centroids = pd.DataFrame(
        {
            "zip": ["94101", "94102", "10001"],
            "lat": [37.7749, 37.7849, 40.7128],
            "lon": [-122.4194, -122.4194, -74.0060],
        }
    )
    result = zips_within_radius_geopy(
        lat=37.7749, lon=-122.4194, radius_miles=5.0, centroids_df=centroids
    )
    assert "94101" in result
    assert "94102" in result
    assert "10001" not in result  # NYC is way outside 5 miles


def test_zips_within_radius_distances_are_positive_floats():
    centroids = pd.DataFrame(
        {"zip": ["94101"], "lat": [37.7749], "lon": [-122.4194]}
    )
    result = zips_within_radius_geopy(
        lat=37.7849, lon=-122.4194, radius_miles=10.0, centroids_df=centroids
    )
    assert result["94101"] > 0
