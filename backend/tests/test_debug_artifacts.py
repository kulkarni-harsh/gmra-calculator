import pytest


def test_enable_debug_artifacts_default_true():
    """ENABLE_DEBUG_ARTIFACTS must default to True."""
    from app.core.config import Settings
    s = Settings(
        PROJECT_NAME="test", VERSION="0", API_PREFIX="/api",
        CENSUS_API_KEY="x", MAPBOX_API_KEY="x",
        ALPHASOPHIA_API_KEY="x", GOOGLE_API_KEY="x",
    )
    assert s.ENABLE_DEBUG_ARTIFACTS is True


def test_enable_debug_artifacts_can_be_disabled():
    """ENABLE_DEBUG_ARTIFACTS can be explicitly set to False."""
    from app.core.config import Settings
    s = Settings(
        PROJECT_NAME="test", VERSION="0", API_PREFIX="/api",
        CENSUS_API_KEY="x", MAPBOX_API_KEY="x",
        ALPHASOPHIA_API_KEY="x", GOOGLE_API_KEY="x",
        ENABLE_DEBUG_ARTIFACTS=False,
    )
    assert s.ENABLE_DEBUG_ARTIFACTS is False
