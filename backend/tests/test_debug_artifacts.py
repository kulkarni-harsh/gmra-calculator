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


def test_upload_debug_json_puts_correct_key():
    """upload_debug_json must write to debug/{job_id}/{stage}.json."""
    from unittest.mock import MagicMock, patch

    mock_client = MagicMock()
    with patch("app.services.s3._client", return_value=mock_client):
        from app.services.s3 import upload_debug_json
        result = upload_debug_json("job123", "01_providers_raw", [{"npi": "1"}])

    mock_client.put_object.assert_called_once()
    call_kwargs = mock_client.put_object.call_args.kwargs
    assert call_kwargs["Key"] == "debug/job123/01_providers_raw.json"
    assert call_kwargs["ContentType"] == "application/json"
    assert result == "debug/job123/01_providers_raw.json"


def test_upload_debug_json_returns_empty_string_on_error():
    """upload_debug_json must never raise — return '' on failure."""
    from unittest.mock import MagicMock, patch
    from botocore.exceptions import ClientError

    mock_client = MagicMock()
    mock_client.put_object.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "fail"}}, "PutObject"
    )
    with patch("app.services.s3._client", return_value=mock_client):
        from app.services.s3 import upload_debug_json
        result = upload_debug_json("job123", "01_providers_raw", [])

    assert result == ""


def test_find_nearby_google_places_returns_raw_and_deduped():
    """find_nearby_google_places must return GooglePlacesResult with .raw and .deduped."""
    from unittest.mock import patch

    fake_place = {
        "name": "Clinic A",
        "vicinity": "123 Main St",
        "geometry": {"location": {"lat": 37.0, "lng": -122.0}},
        "place_id": "abc123",
    }
    with (
        patch("app.services.google_maps._fetch_places_raw", return_value=[fake_place]),
        patch("app.services.google_maps.calculate_distance_miles", return_value=1.0),
    ):
        from app.services.google_maps import find_nearby_google_places
        result = find_nearby_google_places(
            source_longitude=-122.0,
            source_latitude=37.0,
            keywords=["family medicine"],
        )

    assert hasattr(result, "raw"), "result must have .raw"
    assert hasattr(result, "deduped"), "result must have .deduped"
    assert isinstance(result.raw, list)
    assert isinstance(result.deduped, list)
    assert len(result.raw) >= 1
    assert len(result.deduped) >= 1


def test_debug_upload_skips_when_no_job_id():
    """_debug_upload must be a no-op when job_id is None."""
    from unittest.mock import patch
    with patch("app.services.report_generator.upload_debug_json") as mock_upload:
        from app.services.report_generator import _debug_upload
        _debug_upload(None, "01_providers_raw", [{"npi": "1"}])
    mock_upload.assert_not_called()


def test_debug_upload_skips_when_flag_disabled():
    """_debug_upload must be a no-op when ENABLE_DEBUG_ARTIFACTS is False."""
    from unittest.mock import patch
    with (
        patch("app.services.report_generator.upload_debug_json") as mock_upload,
        patch("app.services.report_generator.settings") as mock_settings,
    ):
        mock_settings.ENABLE_DEBUG_ARTIFACTS = False
        from app.services.report_generator import _debug_upload
        _debug_upload("job123", "01_providers_raw", [{"npi": "1"}])
    mock_upload.assert_not_called()


def test_debug_upload_calls_s3_when_enabled():
    """_debug_upload must call upload_debug_json when job_id is set and flag is True."""
    from unittest.mock import patch
    with (
        patch("app.services.report_generator.upload_debug_json") as mock_upload,
        patch("app.services.report_generator.settings") as mock_settings,
    ):
        mock_settings.ENABLE_DEBUG_ARTIFACTS = True
        from app.services.report_generator import _debug_upload
        _debug_upload("job123", "01_providers_raw", [{"npi": "1"}])
    mock_upload.assert_called_once_with("job123", "01_providers_raw", [{"npi": "1"}])


def test_load_state_module_imports_json():
    """Importing load_state must not raise NameError for json."""
    import inspect
    from app.services.report_generator import load_state

    src = inspect.getsource(load_state)
    assert "json.load" in src

    import app.services.report_generator as rg
    assert hasattr(rg, "json")
