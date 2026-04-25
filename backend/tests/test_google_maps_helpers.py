"""Unit tests for private helpers in app.services.google_maps."""

from app.services.google_maps import (
    _dedup_google_places,
    _generate_tile_centers,
    _normalize_phone,
)
from app.types.google_maps import GooglePlace

# ── _normalize_phone ─────────────────────────────────────────────────────────


def test_normalize_phone_strips_format_and_keeps_last_10():
    assert _normalize_phone("+1 (415) 555-1234") == "4155551234"


def test_normalize_phone_returns_empty_for_short_number():
    assert _normalize_phone("123") == ""


def test_normalize_phone_returns_empty_for_no_digits():
    assert _normalize_phone("no-number-here") == ""


def test_normalize_phone_handles_country_code_only_keeps_10_digits():
    assert _normalize_phone("+44 20 7946 0958") == "2079460958"


# ── _dedup_google_places ─────────────────────────────────────────────────────


def _place(place_id: str, lat: float, lon: float) -> GooglePlace:
    return GooglePlace(place_id=place_id, latitude=lat, longitude=lon)


def test_dedup_keeps_far_apart_places():
    a = _place("a", 37.7749, -122.4194)
    b = _place("b", 40.7128, -74.0060)  # NYC
    out = _dedup_google_places([a, b], threshold_miles=0.05)
    assert len(out) == 2


def test_dedup_collapses_close_places():
    a = _place("a", 37.7749, -122.4194)
    b = _place("b", 37.77491, -122.41941)  # ~10 ft away
    out = _dedup_google_places([a, b], threshold_miles=0.05)
    assert len(out) == 1
    assert out[0].place_id == "a"  # first one wins


def test_dedup_keeps_places_with_missing_coords_separate():
    a = _place("a", 37.7749, -122.4194)
    b = GooglePlace(place_id="b", latitude=None, longitude=None)
    out = _dedup_google_places([a, b], threshold_miles=0.05)
    assert len(out) == 2


# ── _generate_tile_centers ───────────────────────────────────────────────────


def test_generate_tile_centers_returns_at_least_one_point():
    centers = _generate_tile_centers(
        center_lat=37.0, center_lon=-122.0, total_radius_miles=20.0, tile_radius_miles=10.0
    )
    assert len(centers) >= 1
    # First entry should be near the center
    lat, lon = centers[0]
    assert abs(lat - 37.0) < 1.0
    assert abs(lon - (-122.0)) < 1.0


def test_generate_tile_centers_grid_grows_with_radius():
    small = _generate_tile_centers(37.0, -122.0, total_radius_miles=10.0, tile_radius_miles=10.0)
    big = _generate_tile_centers(37.0, -122.0, total_radius_miles=100.0, tile_radius_miles=10.0)
    assert len(big) > len(small)
